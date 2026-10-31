from fastapi.testclient import TestClient

import api
from engine.holavon_quota_store import QuotaReservation


REQUEST_ID = '32280f23-219e-45cf-b18b-90c8a8367703'


class FakeStore:
    def __init__(self, allowed=True, duplicate=False):
        self.allowed = allowed
        self.duplicate = duplicate
        self.calls = []

    def remaining(self, user_id, *, is_pro):
        self.calls.append(('remaining', user_id, is_pro))
        return 2

    def consume(self, user_id, *, is_pro, request_id):
        self.calls.append(('consume', user_id, is_pro, request_id))
        return QuotaReservation(self.allowed, 2 if self.allowed else 0, self.duplicate)

    def complete(self, user_id, request_id):
        self.calls.append(('complete', user_id, request_id))

    def release(self, user_id, request_id):
        self.calls.append(('release', user_id, request_id))
        return True


def _payload(question='Bu ise girecek miyim?'):
    return {'question': question, 'lat': 41, 'lon': 29, 'lang': 'en',
            'email': 'forged@example.invalid', 'request_id': REQUEST_ID}


def _configure(monkeypatch, store, pro=False):
    api._retry_cache.clear()
    monkeypatch.setattr(api, '_holavon_context', lambda authorization: {
        'user_id': 'verified-user', 'email': 'verified@example.invalid',
        'is_pro': pro, 'store': store,
    })
    monkeypatch.setattr(api, 'call_openai', lambda *_: 'test answer')


def test_status_uses_verified_identity_and_subscription(monkeypatch):
    store = FakeStore()
    _configure(monkeypatch, store, pro=True)
    r = TestClient(api.app).get('/api/holavon/quota')
    assert r.status_code == 200
    assert r.json() == {'remaining': 2, 'limit': 3, 'is_pro': True, 'reset_timezone': 'UTC'}
    assert store.calls == [('remaining', 'verified-user', True)]


def test_answer_consumes_only_verified_account_quota(monkeypatch):
    store = FakeStore()
    _configure(monkeypatch, store)
    r = TestClient(api.app).post('/api/holavon/cast', json=_payload())
    assert r.status_code == 200
    assert r.json()['answer'] == 'test answer'
    assert r.json()['remaining'] == 2
    assert store.calls == [('consume', 'verified-user', False, REQUEST_ID),
                           ('complete', 'verified-user', REQUEST_ID)]


def test_exhaustion_and_retry_do_not_run_model(monkeypatch):
    for store, expected in [(FakeStore(allowed=False), 200), (FakeStore(duplicate=True), 409)]:
        _configure(monkeypatch, store)
        def no_model(*_):
            raise AssertionError('model must not run')
        monkeypatch.setattr(api, 'call_openai', no_model)
        r = TestClient(api.app).post('/api/holavon/cast', json=_payload())
        assert r.status_code == expected
        if expected == 200:
            assert r.json()['verdict'] == 'NO_QUOTA'


def test_chat_is_free_and_request_id_is_required(monkeypatch):
    store = FakeStore()
    _configure(monkeypatch, store)
    client = TestClient(api.app)
    assert client.post('/api/holavon/cast', json=_payload('hello')).json()['verdict'] == 'CHAT'
    assert store.calls == []
    payload = _payload()
    payload.pop('request_id')
    assert client.post('/api/holavon/cast', json=payload).status_code == 400


def test_experimental_route_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv('HOLAVON_QUOTA_EXPERIMENTAL', raising=False)
    r = TestClient(api.app).get('/api/holavon/quota')
    assert r.status_code == 503


def test_untrusted_history_is_limited(monkeypatch):
    store = FakeStore()
    _configure(monkeypatch, store)
    client = TestClient(api.app)
    data = _payload('hello')
    data['history'] = [{'role': 'user', 'content': 'x'}] * 5
    assert client.post('/api/holavon/cast', json=data).status_code == 400
    data['history'] = [{'role': 'system', 'content': 'x'}]
    assert client.post('/api/holavon/cast', json=data).status_code == 400


def test_retry_recovers_answer_without_running_model_twice(monkeypatch):
    store = FakeStore()
    _configure(monkeypatch, store)
    called = []
    monkeypatch.setattr(api, 'call_openai', lambda *_: called.append(True) or 'test answer')
    client = TestClient(api.app)
    first = client.post('/api/holavon/cast', json=_payload())
    store.duplicate = True
    second = client.post('/api/holavon/cast', json=_payload())
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert len(called) == 1


def test_failed_answer_refunds_pending_reservation(monkeypatch):
    store = FakeStore()
    _configure(monkeypatch, store)
    def failing_model(*_):
        raise RuntimeError('synthetic failure')
    monkeypatch.setattr(api, 'call_openai', failing_model)
    client = TestClient(api.app, raise_server_exceptions=False)
    assert client.post('/api/holavon/cast', json=_payload()).status_code == 500
    assert ('release', 'verified-user', REQUEST_ID) in store.calls
