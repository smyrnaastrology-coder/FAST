"""Fast Koc — token auth (Faz 3).

- Supabase JWT (HS256) dogrulama: SUPABASE_JWT_SECRET varsa gercek kontrol.
- Dev token: FASTKOC_DEV_TOKEN eslesirse gecer (yerel/MVP).
- AUTH_ZORUNLU=false (varsayilan): Authorization yoksa anonim gecer, MVP kirilmaz.
  Uretimde AUTH_ZORUNLU=true yapin.

Kullanim: `kullanici: dict = Depends(mevcut_kullanici)` ve `rol_gerekli("koc")`.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)

ANONIM = {"sub": "anonim", "rol": "anonim", "email": ""}


def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def supabase_jwt_dogrula(token: str) -> Optional[dict]:
    secret = os.environ.get("SUPABASE_JWT_SECRET", "")
    if not secret:
        return None
    try:
        head_b64, body_b64, sig_b64 = token.split(".")
        imza = hmac.new(secret.encode(), f"{head_b64}.{body_b64}".encode(),
                        hashlib.sha256).digest()
        if not hmac.compare_digest(imza, _b64url_decode(sig_b64)):
            return None
        govde = json.loads(_b64url_decode(body_b64))
        if govde.get("exp") and govde["exp"] < time.time():
            return None
        return {"sub": govde.get("sub", ""), "rol": govde.get("role", "authenticated"),
                "email": govde.get("email", "")}
    except Exception:
        return None


def mevcut_kullanici(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if creds is None or not creds.credentials:
        if os.environ.get("AUTH_ZORUNLU", "false").lower() == "true":
            raise HTTPException(401, "token gerekli")
        return ANONIM
    token = creds.credentials
    claims = supabase_jwt_dogrula(token)
    if claims:
        return claims
    dev = os.environ.get("FASTKOC_DEV_TOKEN", "")
    if dev and hmac.compare_digest(token, dev):
        return {"sub": "dev", "rol": "admin", "email": "dev@fastkoc"}
    if os.environ.get("AUTH_ZORUNLU", "false").lower() == "true":
        raise HTTPException(401, "gecersiz token")
    return ANONIM


def rol_gerekli(*roller: str):
    def _kontrol(kullanici: dict = Depends(mevcut_kullanici)) -> dict:
        if kullanici.get("rol") in roller or kullanici.get("rol") == "admin":
            return kullanici
        if os.environ.get("AUTH_ZORUNLU", "false").lower() != "true" and kullanici == ANONIM:
            return kullanici  # MVP'de acik
        raise HTTPException(403, "yetki yok")
    return _kontrol
