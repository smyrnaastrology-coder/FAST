from concurrent.futures import ThreadPoolExecutor

import pytest

import auth


def test_concurrent_spending_never_exceeds_balance(monkeypatch, tmp_path):
    monkeypatch.delenv('HORARY_DATABASE_URL', raising=False)
    monkeypatch.setattr(auth, 'DB', str(tmp_path / 'users.json'))
    monkeypatch.setattr(auth, 'AUDIT', str(tmp_path / 'audit.jsonl'))
    auth.create_user('test@example.invalid', credits=3)
    with ThreadPoolExecutor(max_workers=12) as pool:
        outcomes = list(pool.map(lambda _: auth.spend_credit('test@example.invalid'), range(20)))
    assert sorted(x for x in outcomes if x is not None) == [0, 1, 2]
    assert auth.get_user('test@example.invalid')['credits'] == 0


@pytest.mark.parametrize('amount', [0, -1, True])
def test_invalid_credit_amount_rejected(amount):
    with pytest.raises(ValueError):
        auth.spend_credit('test@example.invalid', amount=amount)
