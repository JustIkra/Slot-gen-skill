import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from slotgen_provider.http import download_artifact, request_json, validate_api_url


class Response:
    def __init__(self, status=200, headers=None, body=b'{}'):
        self.status, self.headers, self.body = status, headers or {}, io.BytesIO(body)

    def read(self, count=-1):
        return self.body.read(count)

    def close(self):
        pass


class HttpPolicyTests(unittest.TestCase):
    def test_rejects_untrusted_api_urls_before_transport(self):
        for url in ['https://openrouter.ai.evil.invalid/a', 'http://openrouter.ai/a',
                    'https://user@openrouter.ai/a', 'https://openrouter.ai:444/a',
                    '/relative', 'https://openrouter.ai\\@evil.invalid/a']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_api_url(url, {'https://openrouter.ai'})

    def test_cross_origin_redirect_never_receives_authorization(self):
        sent = []
        def send(method, url, headers, body, timeout):
            sent.append((url, headers))
            return Response(302, {'location': 'https://evil.invalid/collect'})
        with patch('slotgen_provider.http._open_once', side_effect=send):
            with self.assertRaises(ValueError):
                request_json('GET', 'https://openrouter.ai/a', token='fixture', allowed_origins={'https://openrouter.ai'})
        self.assertEqual([u for u, _ in sent], ['https://openrouter.ai/a'])

    def test_same_origin_read_redirect_is_allowed(self):
        replies = [Response(302, {'location': '/result'}), Response(body=b'{"ok":true}')]
        with patch('slotgen_provider.http._open_once', side_effect=replies):
            result = request_json('GET', 'https://openrouter.ai/a', token='fixture', allowed_origins={'https://openrouter.ai'})
        self.assertEqual(result, {'ok': True})

    def test_download_never_has_auth_and_preserves_existing_file_on_failure(self):
        seen = []
        def send(method, url, headers, body, timeout):
            seen.append(headers)
            return Response(body=b'too large')
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'artifact.bin'
            target.write_bytes(b'accepted')
            with patch('slotgen_provider.http._open_once', side_effect=send):
                with self.assertRaises(ValueError):
                    download_artifact('https://cdn.example/art', target, allowed_hosts={'cdn.example'}, max_bytes=2)
            self.assertEqual(target.read_bytes(), b'accepted')
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()), ['artifact.bin'])
        self.assertFalse(any('authorization' in {k.lower() for k in h} for h in seen))

    def test_private_and_mixed_dns_addresses_are_rejected(self):
        from slotgen_provider.http import public_addresses
        for address in ['127.0.0.1', '169.254.169.254', '::1', '10.0.0.1']:
            result = [(2, 1, 6, '', (address, 443))]
            with patch('socket.getaddrinfo', return_value=result), self.assertRaises(ValueError):
                public_addresses('cdn.example', 443)
