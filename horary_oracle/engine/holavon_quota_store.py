"""Transactional Holavon quota storage for PostgreSQL.

Callers must validate the Supabase identity and subscription on the server.
This store must only be used by an authenticated server endpoint.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from threading import RLock
from typing import Callable
from uuid import UUID

from .holavon_quota import QuotaState, consume_question, remaining_questions

_schema_lock = RLock()
_ready_schemas = set()


@dataclass(frozen=True)
class QuotaReservation:
    allowed: bool
    remaining: int
    duplicate: bool = False


class PostgresQuotaStore:
    def __init__(self, connect: Callable):
        self._connect = connect

    def ensure_schema(self, database_url: str) -> None:
        """Apply only the quota tables; failures must stop request handling."""
        if not database_url:
            raise ValueError('database not configured')
        key = hashlib.sha256(database_url.encode('utf-8')).digest()
        with _schema_lock:
            if key in _ready_schemas:
                return
            sql = (Path(__file__).resolve().parent.parent / 'migrations' / '001_holavon_quota.sql').read_text(encoding='utf-8')
            conn = self._connect()
            try:
                conn.autocommit = False
                with conn.cursor() as cur:
                    cur.execute(sql)
                conn.commit()
                _ready_schemas.add(key)
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def remaining(self, user_id: str, *, is_pro: bool) -> int:
        if not user_id or not user_id.strip():
            raise ValueError('verified user ID required')
        if type(is_pro) is not bool:
            raise TypeError('verified subscription must be a boolean')
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT free_used, pro_day, pro_used FROM holavon_horary_quota '
                    'WHERE user_id = %s', (user_id,),
                )
                row = cur.fetchone()
                state = QuotaState(*row) if row else QuotaState()
                return remaining_questions(state, is_pro=is_pro,
                                           today=datetime.now(timezone.utc).date())
        finally:
            conn.close()

    def consume(self, user_id: str, *, is_pro: bool, request_id: str) -> QuotaReservation:
        """Reserve one question under a row lock using the server's UTC day.

        A duplicate request ID does not spend quota again. Callers MUST NOT
        run the LLM again on duplicates. The caller must never trust a
        client-supplied user ID or subscription flag.
        """
        if not user_id or not user_id.strip():
            raise ValueError('verified user ID required')
        if type(is_pro) is not bool:
            raise TypeError('verified subscription must be a boolean')
        try:
            request_id = str(UUID(request_id))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError('valid request ID required') from exc
        conn = self._connect()
        try:
            # Row locks must remain held across the read and update, even if
            # a connection factory happens to default to autocommit.
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO holavon_horary_quota (user_id) VALUES (%s) '
                    'ON CONFLICT (user_id) DO NOTHING', (user_id,),
                )
                cur.execute(
                    'SELECT free_used, pro_day, pro_used FROM holavon_horary_quota '
                    'WHERE user_id = %s FOR UPDATE', (user_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError('quota row unavailable')
                cur.execute(
                    'SELECT remaining FROM holavon_horary_reservations '
                    'WHERE user_id = %s AND request_id = %s',
                    (user_id, request_id),
                )
                existing = cur.fetchone()
                if existing is not None:
                    result = QuotaReservation(True, existing[0], duplicate=True)
                    conn.commit()
                    return result
                state = QuotaState(free_used=row[0], pro_day=row[1], pro_used=row[2])
                today = datetime.now(timezone.utc).date()
                decision = consume_question(
                    state, is_pro=is_pro, today=today,
                )
                if decision.allowed:
                    cur.execute(
                        'UPDATE holavon_horary_quota SET free_used = %s, '
                        'pro_day = %s, pro_used = %s WHERE user_id = %s',
                        (decision.state.free_used, decision.state.pro_day,
                         decision.state.pro_used, user_id),
                    )
                    cur.execute(
                        'INSERT INTO holavon_horary_reservations '
                        '(user_id, request_id, quota_type, quota_day, remaining) '
                        'VALUES (%s, %s, %s, %s, %s)',
                        (user_id, request_id, 'pro' if is_pro else 'free',
                         today, decision.remaining),
                    )
            conn.commit()
            return QuotaReservation(decision.allowed, decision.remaining)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def complete(self, user_id: str, request_id: str) -> None:
        conn = self._connect()
        try:
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE holavon_horary_reservations SET completed = TRUE '
                    'WHERE user_id = %s AND request_id = %s AND completed = FALSE',
                    (user_id, str(UUID(request_id))),
                )
                if cur.rowcount != 1:
                    raise RuntimeError('quota reservation unavailable')
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def release(self, user_id: str, request_id: str) -> bool:
        """Refund a pending reservation. Completed reservations are immutable."""
        conn = self._connect()
        try:
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute('SELECT free_used, pro_day, pro_used FROM holavon_horary_quota '
                            'WHERE user_id = %s FOR UPDATE', (user_id,))
                state = cur.fetchone()
                if state is None:
                    conn.commit()
                    return False
                cur.execute('SELECT quota_type, quota_day, completed FROM holavon_horary_reservations '
                            'WHERE user_id = %s AND request_id = %s FOR UPDATE',
                            (user_id, str(UUID(request_id))))
                reservation = cur.fetchone()
                if reservation is None or reservation[2]:
                    conn.commit()
                    return False
                free_used, pro_day, pro_used = state
                if reservation[0] == 'free':
                    free_used = max(0, free_used - 1)
                elif pro_day == reservation[1]:
                    pro_used = max(0, pro_used - 1)
                cur.execute('UPDATE holavon_horary_quota SET free_used = %s, '
                            'pro_used = %s WHERE user_id = %s', (free_used, pro_used, user_id))
                cur.execute('DELETE FROM holavon_horary_reservations WHERE user_id = %s '
                            'AND request_id = %s', (user_id, str(UUID(request_id))))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
