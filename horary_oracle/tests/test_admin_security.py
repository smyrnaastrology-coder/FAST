import asyncio

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import api


def test_admin_key_fails_closed_without_configuration(monkeypatch):
    monkeypatch.delenv('ADMIN_KEY', raising=False)
    with pytest.raises(HTTPException) as exc:
        api._require_admin_key(None)
    assert exc.value.status_code == 503


def test_admin_list_requires_configured_secret(monkeypatch):
    monkeypatch.setenv('ADMIN_KEY', 'test-random-secret')
    for key in (None, '', 'wrong', 'şifre'):
        with pytest.raises(HTTPException) as exc:
            api._require_admin_key(key)
        assert exc.value.status_code == 403
    api._require_admin_key('test-random-secret')
    with pytest.raises(HTTPException) as exc:
        asyncio.run(api.admin_list(key='', x_admin_key=None))
    assert exc.value.status_code == 403


def test_admin_routes_block_unauthenticated_http_requests(monkeypatch):
    monkeypatch.setenv('ADMIN_KEY', 'test-random-secret')
    client = TestClient(api.app)
    assert client.get('/admin/list').status_code == 403
    assert client.post('/admin/create', params={'email': 'test@example.invalid'}).status_code == 403
    assert client.get('/admin/users').status_code == 403
    for path in ['/admin/add_credits', '/admin/set_plan', '/admin/reset_devices']:
        assert client.post(path, json={}).status_code == 403


def test_admin_routes_fail_closed_if_secret_missing(monkeypatch):
    monkeypatch.delenv('ADMIN_KEY', raising=False)
    client = TestClient(api.app)
    assert client.get('/admin/list').status_code == 503
    assert client.get('/admin/users').status_code == 503


@pytest.mark.parametrize('name', ['admin_users', 'admin_add_credits', 'admin_set_plan', 'admin_reset_devices'])
def test_admin_operations_reject_bad_key(monkeypatch, name):
    monkeypatch.setenv('ADMIN_KEY', 'test-random-secret')
    fn = getattr(api, name)
    with pytest.raises(HTTPException) as exc:
        if name == 'admin_users':
            fn(x_admin_key='incorrect')
        else:
            fn({}, x_admin_key='incorrect')
    assert exc.value.status_code == 403
