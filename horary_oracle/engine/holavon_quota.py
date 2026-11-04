"""Holavon question quota rules, independent of storage and authentication.

This module does not enforce the quota on its own. Callers must verify the
account and subscription on the server and persist state atomically.

Two independent balances exist:

* the daily/free allowance (3 free questions in total, 3 Pro questions per
  UTC day), and
* purchased credits, which never expire and are only spent after the
  allowance for the current day is exhausted.
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
    credits: int = 0

    def __post_init__(self):
        if self.free_used < 0 or self.pro_used < 0 or self.credits < 0:
            raise ValueError('quota usage cannot be negative')


@dataclass(frozen=True)
class QuotaDecision:
    allowed: bool
    remaining: int
    state: QuotaState
    # Which balance paid for this question: 'pro', 'free' or 'credit'.
    source: str = ''
    # Purchased credit balance after the decision.
    credits: int = 0

    @property
    def available(self) -> int:
        return self.remaining + self.credits


def remaining_questions(state: QuotaState, *, is_pro: bool, today: date) -> int:
    """Return the unused daily/free allowance, without purchased credits."""
    if is_pro:
        used = state.pro_used if state.pro_day == today else 0
        return max(0, PRO_DAILY_LIMIT - used)
    return max(0, FREE_TOTAL_LIMIT - state.free_used)


def available_questions(state: QuotaState, *, is_pro: bool, today: date) -> int:
    """Allowance plus purchased credits: everything the user may still ask."""
    return remaining_questions(state, is_pro=is_pro, today=today) + state.credits


def consume_question(state: QuotaState, *, is_pro: bool, today: date) -> QuotaDecision:
    """Consume one question. `today` must come from a trusted server clock.

    Pro and free counters are independent: after expiry the original free
    balance applies; renewing does not reset a previously used daily balance.
    Purchased credits are not tied to a day and are only touched once the
    current allowance is used up.

    The caller must run read/decision/write under a database row lock.
    """
    if is_pro:
        used = state.pro_used if state.pro_day == today else 0
        if used < PRO_DAILY_LIMIT:
            updated = QuotaState(state.free_used, today, used + 1, state.credits)
            return QuotaDecision(
                True, PRO_DAILY_LIMIT - updated.pro_used, updated,
                source='pro', credits=updated.credits,
            )
        if state.credits > 0:
            updated = QuotaState(state.free_used, state.pro_day, state.pro_used,
                                 state.credits - 1)
            return QuotaDecision(True, 0, updated, source='credit',
                                 credits=updated.credits)
        return QuotaDecision(False, 0, state)

    if state.free_used < FREE_TOTAL_LIMIT:
        updated = QuotaState(state.free_used + 1, state.pro_day, state.pro_used,
                             state.credits)
        return QuotaDecision(
            True, FREE_TOTAL_LIMIT - updated.free_used, updated,
            source='free', credits=updated.credits,
        )
    if state.credits > 0:
        updated = QuotaState(state.free_used, state.pro_day, state.pro_used,
                             state.credits - 1)
        return QuotaDecision(True, 0, updated, source='credit',
                             credits=updated.credits)
    return QuotaDecision(False, 0, state)
