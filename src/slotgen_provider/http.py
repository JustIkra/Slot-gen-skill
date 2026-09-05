import http.client
import ipaddress
import json
import os
import socket
import ssl
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit


class ProviderHTTPError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f'Provider HTTP {status}')


class SubmissionUnknown(RuntimeError):
    pass


def _parts(url):
    if not isinstance(url, str) or any(ord(c) <= 32 for c in url) or '\\' in url:
        raise ValueError('Invalid provider URL')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise ValueError('Provider URL must be HTTPS without credentials or fragment')
    if parsed.port not in (None, 443):
        raise ValueError('Unexpected provider port')
    return parsed


def validate_api_url(url, allowed_origins):
    parsed = _parts(url)
    origin = f'https://{parsed.hostname.lower()}'
    if origin not in allowed_origins:
        raise ValueError('Untrusted provider API origin')
    return url


def public_addresses(host, port):
    addresses = list(dict.fromkeys(info[4][0] for info in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)))
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError('Provider address is not public')
    return addresses


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        address = public_addresses(self.host, self.port)[0]
        connection = socket.create_connection((address, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(connection, server_hostname=self.host)
        except BaseException:
            connection.close()
            raise


class _Response:
    def __init__(self, connection, response):
        self.connection, self.response = connection, response
        self.status = response.status
        self.headers = {k.lower(): v for k, v in response.getheaders()}

    def read(self, size=-1):
        return self.response.read(size)

    def close(self):
        self.response.close()
        self.connection.close()


def _open_once(method, url, headers, body, timeout):
    parsed = _parts(url)
    connection = _PinnedHTTPSConnection(parsed.hostname, 443, timeout=timeout, context=ssl.create_default_context())
    resource = (parsed.path or '/') + (('?' + parsed.query) if parsed.query else '')
    try:
        connection.request(method, resource, body=body, headers=headers)
        return _Response(connection, connection.getresponse())
    except BaseException:
        connection.close()
        raise


def _fetch(method, url, headers, body, timeout, validate):
    for _ in range(6):
        validate(url)
        response = _open_once(method, url, headers, body, timeout)
        if response.status not in (301, 302, 303, 307, 308):
            if not 200 <= response.status < 300:
                status = response.status
                response.close()
                raise ProviderHTTPError(status)
            return response
        next_url = response.headers.get('location')
        response.close()
        if method != 'GET' or not next_url:
            raise ValueError('Provider write redirects are not followed')
        url = urljoin(url, next_url)
    raise ValueError('Too many provider redirects')


def request_bytes(method, url, *, token, allowed_origins, body=None, timeout=120, user_agent='SlotGen/0.1'):
    method = method.upper()
    validate_api_url(url, allowed_origins)
    headers = {'Accept': '*/*', 'Content-Type': 'application/json', 'User-Agent': user_agent}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    encoded = None if body is None else json.dumps(body).encode()
    try:
        response = _fetch(method, url, headers, encoded, timeout, lambda u: validate_api_url(u, allowed_origins))
        try:
            payload = response.read(64 * 1024 * 1024 + 1)
            if len(payload) > 64 * 1024 * 1024:
                raise ValueError('Provider JSON exceeds size limit')
            return payload, response.headers
        finally:
            response.close()
    except (OSError, http.client.HTTPException) as error:
        if method == 'POST':
            raise SubmissionUnknown('submission_unknown: verify provider status before submitting again') from error
        raise


def request_json(method, url, **kwargs):
    payload, _headers = request_bytes(method, url, **kwargs)
    return json.loads(payload)


def download_artifact(url, target, *, allowed_hosts, max_bytes=256 * 1024 * 1024, timeout=120, user_agent='SlotGen/0.1'):
    def validate(value):
        parsed = _parts(value)
        if parsed.hostname.lower() not in allowed_hosts:
            raise ValueError('Untrusted artifact host')
    if not isinstance(max_bytes, int) or max_bytes <= 0:
        raise ValueError('max_bytes must be positive')
    validate(url)
    response = _fetch('GET', url, {'Accept': '*/*', 'User-Agent': user_agent}, None, timeout, validate)
    target = Path(target)
    temporary = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f'.{target.name}.', delete=False) as output:
            temporary = Path(output.name)
            total = 0
            while chunk := response.read(min(65536, max_bytes - total + 1)):
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError('Artifact exceeds size limit')
                output.write(chunk)
            if not total:
                raise ValueError('Empty provider artifact')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
        return str(target)
    finally:
        response.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)
