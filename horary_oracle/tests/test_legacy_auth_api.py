from fastapi.testclient import TestClient

import api
import auth


def test_enforced_standalone_session_uses_verified_not_claimed_email(monkeypatch):
    monkeypatch.setenv('HORARY_REQUIRE_LEGACY_SESSION', 'true')
    monkeypatch.setenv('HORARY_SESSION_SECRET', 'random-test-secret')
    monkeypatch.setattr(auth, 'verify', lambda email, password, device: (
        password == 'correct-test-password', {'plan': 'basic', 'credits': 5},
    ))

    async def fake_cast(req, *, holavon=None):
        return {'email': req.email}

    monkeypatch.setattr(api, '_cast', fake_cast)
    client = TestClient(api.app)
    login = client.post('/api/auth/login', json={
        'email': 'owner@example.invalid', 'password': 'correct-test-password',
    })
    assert login.status_code == 200
    token = login.json()['session_token']
    data = {'question': 'Will it work?', 'lat': 41, 'lon': 29,
            'email': 'forged@example.invalid'}
    assert client.post('/api/horary/cast', json=data).status_code == 401
    assert client.post('/api/horary/cast', json=data, headers={'Authorization': 'Bearer invalid'}).status_code == 401
    result = client.post('/api/horary/cast', json=data, headers={'Authorization': f'Bearer {token}'})
    assert result.status_code == 200
    assert result.json()['email'] == 'owner@example.invalid'


def test_missing_session_secret_fails_closed(monkeypatch):
    monkeypatch.setenv('HORARY_REQUIRE_LEGACY_SESSION', 'true')
    monkeypatch.delenv('HORARY_SESSION_SECRET', raising=False)
    client = TestClient(api.app)
    response = client.post('/api/horary/cast', json={'question': 'Test?', 'lat': 41, 'lon': 29})
    assert response.status_code == 503
