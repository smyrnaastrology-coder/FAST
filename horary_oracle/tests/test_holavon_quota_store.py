from datetime import datetime, timezone

import pytest

from engine.holavon_quota_store import PostgresQuotaStore

REQUEST_ID = '32280f23-219e-45cf-b18b-90c8a8367703'


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, args):
        self.conn.calls.append((sql, args))
        if self.conn.fail:
            raise RuntimeError('database unavailable')

    def fetchone(self):
        return self.conn.row if len(self.conn.calls) == 2 else self.conn.existing


class FakeConnection:
    def __init__(self, row=(0, None, 0), fail=False, existing=None):
        self.row = row
        self.fail = fail
        self.existing = existing
        self.calls = []
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.autocommit = True

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_free_claim_locks_and_updates():
    conn = FakeConnection(row=(2, None, 0))
    result = PostgresQuotaStore(lambda: conn).consume('verified-user', is_pro=False, request_id=REQUEST_ID)
    assert result.allowed and result.remaining == 0
    assert 'FOR UPDATE' in conn.calls[1][0]
    assert conn.calls[3][1] == (3, None, 0, 'verified-user')
    assert conn.calls[4][1][:3] == ('verified-user', REQUEST_ID, 'free')
    assert not conn.autocommit
    assert conn.committed and conn.closed and not conn.rolled_back


def test_blocked_pro_claim_does_not_update():
    today = datetime.now(timezone.utc).date()
    conn = FakeConnection(row=(0, today, 3))
    result = PostgresQuotaStore(lambda: conn).consume('verified-user', is_pro=True, request_id=REQUEST_ID)
    assert not result.allowed and result.remaining == 0
    assert len(conn.calls) == 3
    assert conn.committed and conn.closed


def test_database_failure_rolls_back_and_fails_closed():
    conn = FakeConnection(fail=True)
    with pytest.raises(RuntimeError):
        PostgresQuotaStore(lambda: conn).consume('verified-user', is_pro=False, request_id=REQUEST_ID)
    assert conn.rolled_back and conn.closed and not conn.committed


def test_missing_identity_and_invalid_entitlement_rejected():
    store = PostgresQuotaStore(lambda: pytest.fail('should not connect'))
    with pytest.raises(ValueError):
        store.consume('', is_pro=False, request_id=REQUEST_ID)
    with pytest.raises(TypeError):
        store.consume('verified-user', is_pro='true', request_id=REQUEST_ID)
    with pytest.raises(ValueError):
        store.consume('verified-user', is_pro=False, request_id='invalid')


def test_retry_does_not_spend_a_second_question():
    conn = FakeConnection(row=(1, None, 0), existing=(2,))
    result = PostgresQuotaStore(lambda: conn).consume('verified-user', is_pro=False, request_id=REQUEST_ID)
    assert result.allowed and result.duplicate and result.remaining == 2
    assert len(conn.calls) == 3
    assert conn.committed and conn.closed
