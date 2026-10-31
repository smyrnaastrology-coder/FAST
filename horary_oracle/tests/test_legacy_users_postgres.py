import base64
import copy
import json

import pytest

import auth
import legacy_users_postgres as store


class FakeDatabase:
    def __init__(self, payload=None):
        self.payload = payload

    def connect(self):
        return FakeConnection(self)


class FakeConnection:
    def __init__(self, db):
        self.db = db
        self.pending = copy.deepcopy(db.payload)
        self.autocommit = True

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.db.payload = copy.deepcopy(self.pending)

    def rollback(self):
        self.pending = copy.deepcopy(self.db.payload)

    def close(self):
        pass


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.row = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params=None):
        if sql.startswith('SELECT payload'):
            self.row = None if self.conn.pending is None else (copy.deepcopy(self.conn.pending),)
        elif sql.startswith('INSERT INTO'):
            if self.conn.pending is None:
                self.conn.pending = json.loads(params[0])
        elif sql.startswith('UPDATE'):
            self.conn.pending = json.loads(params[0])

    def fetchone(self):
        return self.row


def _backup(data):
    return base64.b64encode(json.dumps(data).encode()).decode()


def test_first_backup_preserves_credits_and_is_not_reapplied(monkeypatch):
    db = FakeDatabase()
    monkeypatch.setattr(store, '_connect', db.connect)
    monkeypatch.setenv('HORARY_USERS_BOOTSTRAP_B64', _backup({'one@example.invalid': {'credits': 7}}))
    assert store.load()['one@example.invalid']['credits'] == 7
    store.update(lambda d: d['one@example.invalid'].__setitem__('credits', 6))
    monkeypatch.setenv('HORARY_USERS_BOOTSTRAP_B64', _backup({'one@example.invalid': {'credits': 99}}))
    assert store.load()['one@example.invalid']['credits'] == 6


def test_missing_or_invalid_backup_fails_closed(monkeypatch):
    monkeypatch.setattr(store, '_connect', FakeDatabase().connect)
    monkeypatch.delenv('HORARY_USERS_BOOTSTRAP_B64', raising=False)
    with pytest.raises(store.LegacyStorageError):
        store.load()
    monkeypatch.setenv('HORARY_USERS_BOOTSTRAP_B64', 'not-valid-base64!')
    with pytest.raises(store.LegacyStorageError):
        store.load()


def test_mutation_error_rolls_back(monkeypatch):
    db = FakeDatabase({'one@example.invalid': {'credits': 7}})
    monkeypatch.setattr(store, '_connect', db.connect)
    def bad_mutation(data):
        data['one@example.invalid']['credits'] = 0
        raise RuntimeError('failure')
    with pytest.raises(RuntimeError):
        store.update(bad_mutation)
    assert db.payload['one@example.invalid']['credits'] == 7


def test_auth_uses_postgres_only_when_configured(monkeypatch):
    db = FakeDatabase({'one@example.invalid': {'credits': 7}})
    monkeypatch.setattr(store, '_connect', db.connect)
    monkeypatch.setenv('HORARY_DATABASE_URL', 'postgresql://not-used')
    assert auth.get_user('one@example.invalid')['credits'] == 7
    assert auth.spend_credit('one@example.invalid') == 6
    assert db.payload['one@example.invalid']['credits'] == 6


def test_existing_user_is_not_overwritten(monkeypatch):
    db = FakeDatabase({'one@example.invalid': {'credits': 7}})
    monkeypatch.setattr(store, '_connect', db.connect)
    monkeypatch.setenv('HORARY_DATABASE_URL', 'postgresql://not-used')
    with pytest.raises(ValueError):
        auth.create_user('one@example.invalid')
    assert db.payload['one@example.invalid']['credits'] == 7
