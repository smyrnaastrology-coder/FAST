"""Short-lived signed sessions for the standalone Horary applications.

A server-only random secret must be configured. The legacy endpoint requires
these sessions only after the explicit rollout flag has been enabled.
"""
import base64
import hashlib
import hmac
import json
import re
import time


class SessionError(ValueError):
    pass


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def _unb64(value: str) -> bytes:
    if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise SessionError('invalid session')
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def issue_session(email: str, *, secret: str, now: int | None = None) -> str:
    normalized = (email or '').strip().lower()
    if not normalized or not secret:
        raise SessionError('session unavailable')
    current = int(time.time()) if now is None else now
    payload = _b64(json.dumps({'email': normalized, 'exp': current + 3600},
                              separators=(',', ':')).encode('utf-8'))
    content = 'horary1.' + payload
    signature = _b64(hmac.new(secret.encode('utf-8'), content.encode('ascii'),
                              hashlib.sha256).digest())
    return content + '.' + signature


def verify_session(token: str, *, secret: str, now: int | None = None) -> str:
    if not token or not secret or len(token) > 4096:
        raise SessionError('invalid session')
    parts = token.split('.')
    if len(parts) != 3 or parts[0] != 'horary1':
        raise SessionError('invalid session')
    try:
        content = parts[0] + '.' + parts[1]
        actual = _unb64(parts[2])
        expected = hmac.new(secret.encode('utf-8'), content.encode('ascii'), hashlib.sha256).digest()
        if not hmac.compare_digest(actual, expected):
            raise SessionError('invalid session')
        payload = json.loads(_unb64(parts[1]).decode('utf-8'))
        email, expiry = payload['email'], payload['exp']
        if not isinstance(email, str) or not email.strip() or type(expiry) is not int:
            raise SessionError('invalid session')
        current = int(time.time()) if now is None else now
        if expiry <= current:
            raise SessionError('session expired')
        return email
    except (KeyError, TypeError, UnicodeError, ValueError) as exc:
        raise SessionError('invalid session') from exc
