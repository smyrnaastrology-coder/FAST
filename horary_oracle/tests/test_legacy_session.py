import pytest
import asyncio
from fastapi import HTTPException

from engine.legacy_session import SessionError, issue_session, verify_session
import api
import auth


def test_signed_session_verifies_and_normalizes_identity():
    token = issue_session(' USER@Example.Invalid ', secret='test-secret', now=1000)
    assert verify_session(token, secret='test-secret', now=1001) == 'user@example.invalid'


def test_expired_or_tampered_session_rejected():
    token = issue_session('user@example.invalid', secret='test-secret', now=1000)
    with pytest.raises(SessionError):
        verify_session(token, secret='test-secret', now=4600)
    with pytest.raises(SessionError):
        verify_session(token, secret='wrong-secret', now=1001)
    with pytest.raises(SessionError):
        verify_session(token + 'x', secret='test-secret', now=1001)


@pytest.mark.parametrize('token', ['', 'a.b.c', 'horary1.invalid.bad', 'x' * 5000])
def test_malformed_session_is_rejected(token):
    with pytest.raises(SessionError):
        verify_session(token, secret='test-secret', now=1001)


def test_missing_secret_fails_closed():
    with pytest.raises(SessionError):
        issue_session('user@example.invalid', secret='', now=1000)
    with pytest.raises(SessionError):
        verify_session('anything', secret='', now=1000)


def test_login_issues_token_after_password_verification(monkeypatch):
    monkeypatch.setenv('HORARY_SESSION_SECRET', 'test-secret')
    monkeypatch.setattr(auth, 'verify', lambda *_: (True, {'credits': 3}))
    req = api.AuthRequest(email='user@example.invalid', password='test-password')
    result = asyncio.run(api.auth_login(req))
    assert verify_session(result['session_token'], secret='test-secret') == 'user@example.invalid'


def test_enforced_cast_requires_session_and_ignores_forged_email(monkeypatch):
    monkeypatch.setenv('HORARY_SESSION_SECRET', 'test-secret')
    monkeypatch.setenv('HORARY_REQUIRE_LEGACY_SESSION', 'true')
    seen = []
    monkeypatch.setattr(api, '_require_account', lambda email: seen.append(email) or {})
    req = api.CastRequest(question='hello', lat=41, lon=29, email='forged@example.invalid')
    with pytest.raises(HTTPException) as exc:
        asyncio.run(api.cast(req, authorization=None))
    assert exc.value.status_code == 401
    token = issue_session('real@example.invalid', secret='test-secret')
    result = asyncio.run(api.cast(req, authorization='Bearer ' + token))
    assert result['verdict'] == 'CHAT'
    assert seen == ['real@example.invalid']


def test_enforcement_disables_hardcoded_password_bypass(monkeypatch, tmp_path):
    monkeypatch.setenv('HORARY_REQUIRE_LEGACY_SESSION', 'true')
    monkeypatch.delenv('HORARY_DATABASE_URL', raising=False)
    monkeypatch.setattr(auth, 'DB', str(tmp_path / 'users.json'))
    monkeypatch.setattr(auth, 'AUDIT', str(tmp_path / 'audit.jsonl'))
    monkeypatch.setattr(auth, 'HARDCODED', {'known@example.invalid': 'old-known-password'})
    auth.update(lambda d: d.__setitem__('known@example.invalid', {
        'pwd': auth.hash_pass('new-password'), 'expiry': '2099-01-01T00:00:00',
        'credits': 3,
    }))
    assert not auth.verify('known@example.invalid', 'old-known-password')[0]
    assert auth.verify('known@example.invalid', 'new-password')[0]
