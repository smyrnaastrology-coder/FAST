"""Quota tests against a dedicated local PostgreSQL database, never production."""
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from uuid import uuid4

import pytest

psycopg2 = pytest.importorskip('psycopg2')
from engine.holavon_quota_store import PostgresQuotaStore


@pytest.fixture
def quota_store():
    url = os.getenv('HORARY_TEST_DATABASE_URL', '')
    parsed = urlparse(url)
    if (parsed.hostname, parsed.port, parsed.path) != (
        '127.0.0.1', 25487, '/horary_test_quota_v2_20261031',
    ):
        pytest.skip('dedicated local test database required')
    store = PostgresQuotaStore(lambda: psycopg2.connect(url, connect_timeout=10))
    store.ensure_schema(url)
    return store


def test_free_quota_blocks_concurrent_requests(quota_store):
    user = str(uuid4())
    ids = [str(uuid4()) for _ in range(20)]
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda rid: quota_store.consume(user, is_pro=False, request_id=rid), ids))
    assert sum(r.allowed for r in results) == 3
    assert sorted(r.remaining for r in results if r.allowed) == [0, 1, 2]
    assert quota_store.remaining(user, is_pro=False) == 0


def test_duplicate_request_only_reserves_once(quota_store):
    user, rid = str(uuid4()), str(uuid4())
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: quota_store.consume(user, is_pro=True, request_id=rid), range(10)))
    assert sum(r.allowed and not r.duplicate for r in results) == 1
    assert sum(r.duplicate for r in results) == 9
    assert quota_store.remaining(user, is_pro=True) == 2


def test_failed_reservation_can_be_refunded_but_completed_one_cannot(quota_store):
    user, failed, complete = str(uuid4()), str(uuid4()), str(uuid4())
    assert quota_store.consume(user, is_pro=False, request_id=failed).allowed
    assert quota_store.consume(user, is_pro=False, request_id=complete).allowed
    quota_store.complete(user, complete)
    assert quota_store.release(user, complete) is False
    assert quota_store.release(user, failed) is True
    assert quota_store.release(user, failed) is False
    assert quota_store.remaining(user, is_pro=False) == 2
