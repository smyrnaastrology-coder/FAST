from datetime import datetime, timezone

import pytest

from engine.holavon_identity import (
    AuthenticationError, IdentityUnavailable, verify_identity, verify_pro,
)


class Response:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body

    def json(self):
        return self.body


class Http:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_identity_comes_from_verified_server_response():
    http = Http(Response(200, {'id': 'verified-id', 'email': 'user@example.invalid'}))
    result = verify_identity('Bearer access-token', supabase_url='https://auth.invalid',
                             anon_key='public-key', http=http)
    assert result.user_id == 'verified-id'
    assert http.calls[0][1]['headers']['Authorization'] == 'Bearer access-token'


@pytest.mark.parametrize('authorization', [None, '', 'Basic token', 'Bearer '])
def test_identity_rejects_missing_or_wrong_authorization(authorization):
    with pytest.raises(AuthenticationError):
        verify_identity(authorization, supabase_url='https://auth.invalid',
                        anon_key='public-key', http=Http(Response(200, {})))


def test_invalid_identity_and_unavailable_service_are_not_free_accounts():
    for status, error in [(401, AuthenticationError), (500, IdentityUnavailable)]:
        with pytest.raises(error):
            verify_identity('Bearer token', supabase_url='https://auth.invalid',
                            anon_key='public-key', http=Http(Response(status, {})))


@pytest.mark.parametrize('expiry,expected', [
    ('2026-11-02T00:00:00Z', True),
    ('2026-10-30T00:00:00Z', False),
])
def test_verified_entitlement_expiration(expiry, expected):
    http = Http(Response(200, {'subscriber': {'subscriptions': {
        'sub_daily': {'expires_date': expiry},
    }}}))
    now = datetime(2026, 10, 31, tzinfo=timezone.utc)
    assert verify_pro('user/id', api_secret='secret',
                      http=http, now=now) is expected
    assert http.calls[0][0].endswith('user%2Fid')


def test_missing_entitlement_is_free_but_errors_fail_closed():
    empty = Http(Response(200, {'subscriber': {'subscriptions': {}}}))
    assert not verify_pro('user', api_secret='secret', http=empty)
    for response in (Response(500, {}), Response(200, {}),
                     Response(200, {'subscriber': {'subscriptions': {'sub_daily': {}}}}),
                     Response(200, {'subscriber': {'subscriptions': {'sub_daily': {
                         'expires_date': None,
                     }}}})):
        with pytest.raises(IdentityUnavailable):
            verify_pro('user', api_secret='secret', http=Http(response))


def test_pdf_purchase_is_not_a_subscription():
    http = Http(Response(200, {'subscriber': {'subscriptions': {}, 'entitlements': {
        'premium': {'expires_date': None, 'product_identifier': 'pdf_single'},
    }}}))
    assert not verify_pro('user', api_secret='secret', http=http)


def test_valid_subscription_survives_pdf_entitlement_and_honors_grace():
    now = datetime(2026, 10, 31, tzinfo=timezone.utc)
    http = Http(Response(200, {'subscriber': {
        'subscriptions': {'sub_daily:monthly': {
            'expires_date': '2026-10-30T00:00:00Z',
            'grace_period_expires_date': '2026-11-02T00:00:00Z',
        }},
        'entitlements': {'premium': {'product_identifier': 'pdf_single', 'expires_date': None}},
    }}))
    assert verify_pro('user', api_secret='secret', http=http, now=now)


def test_refunded_subscription_does_not_grant_pro():
    now = datetime(2026, 10, 31, tzinfo=timezone.utc)
    http = Http(Response(200, {'subscriber': {'subscriptions': {
        'sub_daily_yearly': {'expires_date': '2027-10-31T00:00:00Z',
                             'refunded_at': '2026-10-30T00:00:00Z'},
    }}}))
    assert not verify_pro('user', api_secret='secret', http=http, now=now)
