"""Server-side Supabase identity and RevenueCat entitlement verification.

Used by the experimental Holavon endpoints. Client-provided email, user ID and
subscription flags must never be used as proof of entitlement.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote


class AuthenticationError(Exception):
    pass


class IdentityUnavailable(Exception):
    pass


@dataclass(frozen=True)
class VerifiedIdentity:
    user_id: str
    email: str


def verify_identity(authorization: str | None, *, supabase_url: str,
                    anon_key: str, http) -> VerifiedIdentity:
    if not supabase_url or not anon_key:
        raise IdentityUnavailable('identity service not configured')
    scheme, _, token = (authorization or '').partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        raise AuthenticationError('sign-in required')
    try:
        response = http.get(
            supabase_url.rstrip('/') + '/auth/v1/user',
            headers={'apikey': anon_key, 'Authorization': 'Bearer ' + token.strip()},
            timeout=10,
        )
    except Exception as exc:
        raise IdentityUnavailable('identity service unavailable') from exc
    if response.status_code in (401, 403):
        raise AuthenticationError('invalid session')
    if response.status_code != 200:
        raise IdentityUnavailable('identity verification failed')
    try:
        user = response.json()
        user_id = user.get('id')
        email = user.get('email') or ''
        if not isinstance(user_id, str) or not user_id.strip() or not isinstance(email, str):
            raise ValueError('invalid identity response')
    except (AttributeError, TypeError, ValueError) as exc:
        raise IdentityUnavailable('invalid identity response') from exc
    return VerifiedIdentity(user_id=user_id, email=email)


def verify_pro(user_id: str, *, api_secret: str,
               http, now: datetime | None = None) -> bool:
    """Check actual subscription products using RevenueCat REST API.

    A network/configuration error is not equivalent to a free account; callers
    must fail closed instead of consuming the wrong quota.
    """
    if not user_id or not api_secret:
        raise IdentityUnavailable('subscription service not configured')
    try:
        response = http.get(
            'https://api.revenuecat.com/v1/subscribers/' + quote(user_id, safe=''),
            headers={'Authorization': 'Bearer ' + api_secret}, timeout=15,
        )
    except Exception as exc:
        raise IdentityUnavailable('subscription service unavailable') from exc
    if response.status_code == 404:
        return False
    if response.status_code != 200:
        raise IdentityUnavailable('subscription verification failed')
    try:
        subscriber = response.json()['subscriber']
        subscriptions = subscriber['subscriptions']
        if not isinstance(subscriptions, dict):
            raise ValueError('invalid subscriptions')
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError('current time has no timezone')
        invalid = False
        for product, record in subscriptions.items():
            if not isinstance(product, str) or product.split(':', 1)[0] not in ('sub_daily', 'sub_daily_yearly'):
                continue
            if not isinstance(record, dict) or not record.get('expires_date'):
                invalid = True
                continue
            if record.get('refunded_at'):
                continue
            try:
                expires_at = datetime.fromisoformat(record['expires_date'].replace('Z', '+00:00'))
                if expires_at.tzinfo is None:
                    raise ValueError('expiry has no timezone')
                grace = record.get('grace_period_expires_date')
                if grace:
                    grace_at = datetime.fromisoformat(grace.replace('Z', '+00:00'))
                    if grace_at.tzinfo is None:
                        raise ValueError('grace expiry has no timezone')
                    expires_at = max(expires_at, grace_at)
                if expires_at > current:
                    return True
            except (AttributeError, TypeError, ValueError):
                invalid = True
        if invalid:
            raise ValueError('invalid subscription expiry')
        return False
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise IdentityUnavailable('invalid subscription response') from exc
