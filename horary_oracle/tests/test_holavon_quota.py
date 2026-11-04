from datetime import date, timedelta

import pytest

from engine.holavon_quota import QuotaState, consume_question, remaining_questions


def test_free_limit_does_not_reset_on_new_day():
    state = QuotaState()
    today = date(2026, 10, 31)
    for expected in (2, 1, 0):
        decision = consume_question(state, is_pro=False, today=today)
        assert decision.allowed and decision.remaining == expected
        state = decision.state
    blocked = consume_question(state, is_pro=False, today=today + timedelta(days=1))
    assert not blocked.allowed and blocked.state == state


def test_pro_resets_next_day_and_keeps_free_balance():
    today = date(2026, 10, 31)
    state = QuotaState(free_used=2)
    for expected in (2, 1, 0):
        decision = consume_question(state, is_pro=True, today=today)
        assert decision.allowed and decision.remaining == expected
        state = decision.state
    assert not consume_question(state, is_pro=True, today=today).allowed
    tomorrow = consume_question(state, is_pro=True, today=today + timedelta(days=1))
    assert tomorrow.allowed and tomorrow.remaining == 2
    assert tomorrow.state.free_used == 2


def test_expiry_and_same_day_renewal_do_not_reset_usage():
    today = date(2026, 10, 31)
    state = QuotaState(free_used=3, pro_day=today, pro_used=3)
    assert not consume_question(state, is_pro=False, today=today).allowed
    assert not consume_question(state, is_pro=True, today=today).allowed


def test_corrupt_negative_usage_fails_closed():
    with pytest.raises(ValueError):
        QuotaState(free_used=-1)
    with pytest.raises(ValueError):
        QuotaState(pro_used=-1)


def test_read_remaining_does_not_consume_questions():
    today = date(2026, 10, 31)
    state = QuotaState(free_used=2, pro_day=today, pro_used=3)
    assert remaining_questions(state, is_pro=False, today=today) == 1
    assert remaining_questions(state, is_pro=True, today=today) == 0
    assert remaining_questions(state, is_pro=True, today=today + timedelta(days=1)) == 3
    assert state.free_used == 2 and state.pro_used == 3


def test_free_allowance_spends_before_purchased_credits():
    today = date(2026, 10, 31)
    state = QuotaState(free_used=2, credits=2)
    decision = consume_question(state, is_pro=False, today=today)
    assert decision.allowed and decision.source == 'free'
    assert decision.remaining == 0 and decision.credits == 2
    paid = consume_question(decision.state, is_pro=False, today=today)
    assert paid.allowed and paid.source == 'credit'
    assert paid.remaining == 0 and paid.credits == 1


def test_pro_daily_allowance_spends_before_purchased_credits():
    today = date(2026, 10, 31)
    state = QuotaState(free_used=3, pro_day=today, pro_used=3, credits=1)
    decision = consume_question(state, is_pro=True, today=today)
    assert decision.allowed and decision.source == 'credit'
    assert decision.credits == 0
    blocked = consume_question(decision.state, is_pro=True, today=today)
    assert not blocked.allowed and blocked.credits == 0


def test_purchased_credits_do_not_expire_with_the_day():
    today = date(2026, 10, 31)
    state = QuotaState(free_used=3, credits=4)
    tomorrow = consume_question(state, is_pro=False, today=today + timedelta(days=1))
    assert tomorrow.allowed and tomorrow.source == 'credit'
    assert tomorrow.credits == 3


def test_corrupt_negative_credit_balance_fails_closed():
    with pytest.raises(ValueError):
        QuotaState(credits=-1)
