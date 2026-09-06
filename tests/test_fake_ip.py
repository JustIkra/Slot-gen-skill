import os
import ssl
import unittest
from unittest.mock import patch

from slotgen_provider.http import _PinnedHTTPSConnection, public_addresses


class FakeIPTests(unittest.TestCase):
    def resolve(self, addresses, host='openrouter.ai', config=None):
        records = [(2, 1, 6, '', (address, 443)) for address in addresses]
        with patch.dict(os.environ, config or {}, clear=True), patch('socket.getaddrinfo', return_value=records):
            return public_addresses(host, 443)

    def policy(self):
        return {'SLOTGEN_FAKE_IP_HOSTS': 'openrouter.ai', 'SLOTGEN_FAKE_IP_CIDRS': '198.18.0.0/16'}

    def test_explicit_host_and_range_allow_fake_ip(self):
        try:
            result = self.resolve(['198.18.0.21'], config=self.policy())
        except ValueError as error:
            self.fail(f'Explicit trusted Fake-IP should resolve: {error}')
        self.assertEqual(result, ['198.18.0.21'])

    def test_disabled_or_partial_configuration_rejects_fake_ip(self):
        for config in ({}, {'SLOTGEN_FAKE_IP_HOSTS': 'openrouter.ai'}, {'SLOTGEN_FAKE_IP_CIDRS': '198.18.0.0/16'}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                self.resolve(['198.18.0.21'], config=config)

    def test_exception_does_not_cover_other_hosts_or_subdomains(self):
        for host in ('cdn.example', 'openrouter.ai.evil.example', 'sub.openrouter.ai'):
            with self.subTest(host=host), self.assertRaises(ValueError):
                self.resolve(['198.18.0.21'], host=host, config=self.policy())

    def test_private_mixed_and_outside_configured_range_remain_rejected(self):
        for addresses in (['127.0.0.1'], ['10.0.0.1'], ['169.254.169.254'], ['::1'], ['198.19.0.1'], ['198.18.0.21', '127.0.0.1']):
            with self.subTest(addresses=addresses), self.assertRaises(ValueError):
                self.resolve(addresses, config=self.policy())

    def test_exception_cannot_be_used_to_allow_arbitrary_private_ranges(self):
        for cidr in ('0.0.0.0/0', '127.0.0.0/8', '10.0.0.0/8', '::/0', 'invalid'):
            config = self.policy() | {'SLOTGEN_FAKE_IP_CIDRS': cidr}
            with self.subTest(cidr=cidr), self.assertRaises(ValueError):
                self.resolve(['198.18.0.21'], config=config)

    def test_public_dns_remains_supported(self):
        self.assertEqual(self.resolve(['1.1.1.1']), ['1.1.1.1'])

    def test_fake_ip_tls_keeps_original_server_name_and_verification(self):
        class Context:
            def wrap_socket(self, connection, *, server_hostname):
                if server_hostname != 'openrouter.ai':
                    raise AssertionError('TLS lost original provider hostname')
                raise ssl.SSLCertVerificationError('fixture untrusted certificate')

        class Socket:
            closed = False

            def close(self):
                self.closed = True

        raw = Socket()
        connection = _PinnedHTTPSConnection('openrouter.ai', context=ssl.create_default_context())
        self.assertTrue(connection._context.check_hostname)
        self.assertEqual(connection._context.verify_mode, ssl.CERT_REQUIRED)
        connection._context = Context()
        records = [(2, 1, 6, '', ('198.18.0.21', 443))]

        def connect(address, timeout):
            self.assertEqual(address, ('198.18.0.21', 443))
            return raw

        with patch.dict(os.environ, self.policy(), clear=True), patch('socket.getaddrinfo', return_value=records), patch('socket.create_connection', side_effect=connect):
            with self.assertRaises(ssl.SSLCertVerificationError):
                connection.connect()
        self.assertTrue(raw.closed)
