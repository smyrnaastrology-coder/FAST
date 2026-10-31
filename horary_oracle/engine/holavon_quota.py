"""Holavon question quota rules, independent of storage and authentication.

This module does not enforce the quota on its own. Callers must verify the
account and subscription on the server and persist state atomically.
"""
from dataclasses import dataclass
from datetime import date


FREE_TOTAL_LIMIT = 3
PRO_DAILY_LIMIT = 3


@dataclass(frozen=True)
class QuotaState:
    free_used: int = 0
    pro_day: date | None = None
    pro_used: int = 0

    def __post_init__(self):
        if self.free_used < 0 or self.pro_used < 0:
            raise ValueError('quota usage cannot be negative')


@dataclass(frozen=True)
class QuotaDecision:
    allowed: bool
    remaining: int
    state: QuotaState


def remaining_questions(state: QuotaState, *, is_pro: bool, today: date) -> int:
    if is_pro:
        used = state.pro_used if state.pro_day == today else 0
        return max(0, PRO_DAILY_LIMIT - used)
    return max(0, FREE_TOTAL_LIMIT - state.free_used)


def consume_question(state: QuotaState, *, is_pro: bool, today: date) -> QuotaDecision:
    """Consume one question. `today` must come from a trusted server clock.

    Pro and free counters are independent: after expiry the original free
    balance applies; renewing does not reset a previously used daily balance.
    The caller must run read/decision/write under a database row lock.
    """
    if is_pro:
        used = state.pro_used if state.pro_day == today else 0
        if used >= PRO_DAILY_LIMIT:
            return QuotaDecision(False, 0, state)
        updated = QuotaState(state.free_used, today, used + 1)
        return QuotaDecision(True, PRO_DAILY_LIMIT - updated.pro_used, updated)

    if state.free_used >= FREE_TOTAL_LIMIT:
        return QuotaDecision(False, 0, state)
    updated = QuotaState(state.free_used + 1, state.pro_day, state.pro_used)
    return QuotaDecision(True, FREE_TOTAL_LIMIT - updated.free_used, updated)
