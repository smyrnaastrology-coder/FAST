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

from .holavon_quota import (
    PRO_DAILY_LIMIT, FREE_TOTAL_LIMIT, QuotaState, consume_question,
    remaining_questions,
)

_schema_lock = RLock()
_ready_schemas = set()


@dataclass(frozen=True)
class QuotaReservation:
    allowed: bool
    remaining: int
    duplicate: bool = False
    source: str = ''
    credits: int = 0

    @property
    def available(self) -> int:
        return self.remaining + self.credits


@dataclass(frozen=True)
class CreditGrant:
    credits_added: int
    balance: int
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
            migrations = sorted(
                (Path(__file__).resolve().parent.parent / 'migrations').glob('*.sql')
            )
            conn = self._connect()
            try:
                conn.autocommit = False
                with conn.cursor() as cur:
                    for migration in migrations:
                        cur.execute(migration.read_text(encoding='utf-8'))
                conn.commit()
                _ready_schemas.add(key)
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def status(self, user_id: str, *, is_pro: bool) -> dict:
        """Return both balances without spending anything."""
        if not user_id or not user_id.strip():
            raise ValueError('verified user ID required')
        if type(is_pro) is not bool:
            raise TypeError('verified subscription must be a boolean')
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT free_used, pro_day, pro_used, credit_balance '
                    'FROM holavon_horary_quota WHERE user_id = %s', (user_id,),
                )
                row = cur.fetchone()
                state = QuotaState(*row) if row else QuotaState()
                today = datetime.now(timezone.utc).date()
                remaining = remaining_questions(state, is_pro=is_pro, today=today)
                return {
                    'remaining': remaining,
                    'limit': PRO_DAILY_LIMIT if is_pro else FREE_TOTAL_LIMIT,
                    'credits': state.credits,
                    'available': remaining + state.credits,
                    'is_pro': is_pro,
                }
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
                    'SELECT free_used, pro_day, pro_used, credit_balance '
                    'FROM holavon_horary_quota '
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
                state = QuotaState(free_used=row[0], pro_day=row[1],
                                   pro_used=row[2], credits=row[3])
                today = datetime.now(timezone.utc).date()
                decision = consume_question(
                    state, is_pro=is_pro, today=today,
                )
                if decision.allowed:
                    cur.execute(
                        'UPDATE holavon_horary_quota SET free_used = %s, '
                        'pro_day = %s, pro_used = %s, credit_balance = %s '
                        'WHERE user_id = %s',
                        (decision.state.free_used, decision.state.pro_day,
                         decision.state.pro_used, decision.state.credits,
                         user_id),
                    )
                    cur.execute(
                        'INSERT INTO holavon_horary_reservations '
                        '(user_id, request_id, quota_type, quota_day, remaining) '
                        'VALUES (%s, %s, %s, %s, %s)',
                        (user_id, request_id, decision.source,
                         today, decision.remaining),
                    )
            conn.commit()
            return QuotaReservation(decision.allowed, decision.remaining,
                                    source=decision.source,
                                    credits=decision.credits)
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
                cur.execute('SELECT free_used, pro_day, pro_used, credit_balance FROM holavon_horary_quota '
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
                free_used, pro_day, pro_used, credits = state
                if reservation[0] == 'free':
                    free_used = max(0, free_used - 1)
                elif reservation[0] == 'credit':
                    credits = credits + 1
                elif pro_day == reservation[1]:
                    pro_used = max(0, pro_used - 1)
                cur.execute('UPDATE holavon_horary_quota SET free_used = %s, '
                            'pro_used = %s, credit_balance = %s WHERE user_id = %s',
                            (free_used, pro_used, credits, user_id))
                cur.execute('DELETE FROM holavon_horary_reservations WHERE user_id = %s '
                            'AND request_id = %s', (user_id, str(UUID(request_id))))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def grant_credits(self, user_id: str, *, transaction_id: str,
                      product_id: str, credits: int,
                      source: str = 'revenuecat') -> CreditGrant:
        """Add purchased credits once per store transaction.

        transaction_id is the store's unique purchase ID. Replaying the same
        webhook/sync must return the existing balance and must not grant twice.
        """
        if not user_id or not user_id.strip():
            raise ValueError('verified user ID required')
        if not isinstance(transaction_id, str) or not transaction_id.strip():
            raise ValueError('transaction ID required')
        if len(transaction_id) > 200:
            raise ValueError('transaction ID too long')
        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError('product ID required')
        if type(credits) is not int or credits <= 0 or credits > 1000:
            raise ValueError('invalid credit amount')
        if not isinstance(source, str) or not source.strip():
            raise ValueError('credit source required')
        conn = self._connect()
        try:
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO holavon_horary_quota (user_id) VALUES (%s) '
                    'ON CONFLICT (user_id) DO NOTHING', (user_id,),
                )
                cur.execute(
                    'SELECT credit_balance FROM holavon_horary_quota '
                    'WHERE user_id = %s FOR UPDATE', (user_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError('credit wallet unavailable')
                cur.execute(
                    'INSERT INTO holavon_horary_credit_ledger '
                    '(transaction_id, user_id, product_id, credits, source) '
                    'VALUES (%s, %s, %s, %s, %s) '
                    'ON CONFLICT (transaction_id) DO NOTHING',
                    (transaction_id.strip(), user_id, product_id.strip(),
                     credits, source.strip()),
                )
                if cur.rowcount == 0:
                    conn.commit()
                    return CreditGrant(0, row[0], duplicate=True)
                cur.execute(
                    'UPDATE holavon_horary_quota '
                    'SET credit_balance = credit_balance + %s WHERE user_id = %s',
                    (credits, user_id),
                )
                cur.execute(
                    'SELECT credit_balance FROM holavon_horary_quota '
                    'WHERE user_id = %s', (user_id,),
                )
                balance = cur.fetchone()[0]
            conn.commit()
            return CreditGrant(credits, balance)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
