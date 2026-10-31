"""Local PostgreSQL + API quota integration, with external identity mocked."""
import os
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

psycopg2 = pytest.importorskip('psycopg2')

import api
from engine.holavon_quota_store import PostgresQuotaStore


@pytest.fixture
def setup_api(monkeypatch):
    url = os.getenv('HORARY_TEST_DATABASE_URL', '')
    parsed = urlparse(url)
    if (parsed.hostname, parsed.port, parsed.path) != (
        '127.0.0.1', 25487, '/horary_test_quota_v2_20261031',
    ):
        pytest.skip('dedicated local test database required')
    store = PostgresQuotaStore(lambda: psycopg2.connect(url, connect_timeout=10))
    store.ensure_schema(url)
    user_id = str(uuid4())
    context = {'user_id': user_id, 'email': 'test@example.invalid',
               'is_pro': False, 'store': store}
    monkeypatch.setattr(api, '_holavon_context', lambda _: dict(context))
    calls = []
    monkeypatch.setattr(api, 'call_openai', lambda *_: calls.append(True) or 'answer')
    return TestClient(api.app), context, calls


@pytest.mark.parametrize('is_pro', [False, True])
def test_three_questions_then_limit(setup_api, is_pro):
    client, context, calls = setup_api
    context['is_pro'] = is_pro
    assert client.get('/api/holavon/quota').json()['remaining'] == 3
    for expected in (2, 1, 0):
        response = client.post('/api/holavon/cast', json={
            'question': 'Bu işe girecek miyim?', 'lat': 41, 'lon': 29,
            'request_id': str(uuid4()),
        })
        assert response.status_code == 200
        assert response.json()['remaining'] == expected
    blocked = client.post('/api/holavon/cast', json={
        'question': 'Başka iş bulabilir miyim?', 'lat': 41, 'lon': 29,
        'request_id': str(uuid4()),
    })
    assert blocked.status_code == 200
    assert blocked.json()['verdict'] == 'NO_QUOTA'
    assert len(calls) == 3
