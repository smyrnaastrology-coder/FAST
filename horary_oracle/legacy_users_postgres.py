"""Durable legacy Horary users and credits; opt-in via HORARY_DATABASE_URL.

The first database row must be populated from an explicitly supplied backup.
Never silently initialize an empty database: that could reset paid credits.
No connection string or backup content is logged.
"""
import base64
import json
import os


class LegacyStorageError(RuntimeError):
    pass


def _connect():
    import psycopg2
    url = os.getenv('HORARY_DATABASE_URL', '').strip()
    if not url:
        raise LegacyStorageError('legacy database not configured')
    return psycopg2.connect(url, connect_timeout=10)


def _bootstrap_data():
    encoded = os.getenv('HORARY_USERS_BOOTSTRAP_B64', '').strip()
    if not encoded:
        raise LegacyStorageError('legacy backup required for first initialization')
    try:
        raw = base64.b64decode(encoded, validate=True)
        data = json.loads(raw.decode('utf-8'))
        if not isinstance(data, dict) or not all(isinstance(v, dict) for k, v in data.items() if not k.startswith('__')):
            raise ValueError('invalid backup structure')
        return data
    except (ValueError, UnicodeError, TypeError) as exc:
        raise LegacyStorageError('invalid legacy backup') from exc


def _ensure(cur):
    cur.execute('CREATE TABLE IF NOT EXISTS horary_legacy_users_store '
                '(id INTEGER PRIMARY KEY CHECK (id = 1), payload JSONB NOT NULL)')
    cur.execute('ALTER TABLE horary_legacy_users_store ENABLE ROW LEVEL SECURITY')
    cur.execute('REVOKE ALL ON TABLE horary_legacy_users_store FROM PUBLIC')
    cur.execute('SELECT payload FROM horary_legacy_users_store WHERE id = 1')
    if cur.fetchone() is None:
        data = _bootstrap_data()
        cur.execute('INSERT INTO horary_legacy_users_store (id, payload) '
                    'VALUES (1, %s::jsonb) ON CONFLICT (id) DO NOTHING',
                    (json.dumps(data, ensure_ascii=False),))


def _payload(row):
    if not row or not isinstance(row[0], dict):
        raise LegacyStorageError('legacy users database is missing or corrupt')
    return row[0]


def load():
    conn = _connect()
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            _ensure(cur)
            cur.execute('SELECT payload FROM horary_legacy_users_store WHERE id = 1')
            data = _payload(cur.fetchone())
        conn.commit()
        return data
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update(mutator):
    conn = _connect()
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            _ensure(cur)
            cur.execute('SELECT payload FROM horary_legacy_users_store WHERE id = 1 FOR UPDATE')
            data = _payload(cur.fetchone())
            result = mutator(data)
            cur.execute('UPDATE horary_legacy_users_store SET payload = %s::jsonb WHERE id = 1',
                        (json.dumps(data, ensure_ascii=False),))
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save(data):
    if not isinstance(data, dict):
        raise LegacyStorageError('invalid users data')
    def replace(current):
        current.clear()
        current.update(data)
    update(replace)
