"""Billing & entitlement — file-based MVP (Render free tier).
Production'da Postgres/Supabase'e taşınmalı; arayüz aynı kalır.
"""
import os, json, hashlib, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SUBS_FILE = DATA_DIR / "subscriptions.json"
FREE_FILE = DATA_DIR / "free_pdf_used.json"
PURCHASES_FILE = DATA_DIR / "pdf_purchases.json"

def _load(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:24]

# ── Subscriptions ──
def is_subscribed(uid: str) -> bool:
    if not uid:
        return False
    subs = _load(SUBS_FILE)
    rec = subs.get(uid)
    if not rec:
        return False
    # status active + expiry future
    if rec.get("status") != "active":
        return False
    exp = rec.get("expiry", 0)
    if exp and exp < time.time():
        return False
    return True

def upsert_subscription(uid: str, product_id: str, expiry: float = 0, status: str = "active", provider: str = "revenuecat"):
    subs = _load(SUBS_FILE)
    subs[uid] = {"product_id": product_id, "expiry": expiry, "status": status, "provider": provider, "updated": time.time()}
    _save(SUBS_FILE, subs)

def has_free_used(uid: str, device_token: str = "") -> bool:
    data = _load(FREE_FILE)
    if uid and data.get(f"uid:{uid}"):
        return True
    if device_token and data.get(f"dev:{_hash(device_token)}"):
        return True
    return False

def mark_free_used(uid: str, device_token: str = ""):
    data = _load(FREE_FILE)
    if uid:
        data[f"uid:{uid}"] = int(time.time())
    if device_token:
        data[f"dev:{_hash(device_token)}"] = int(time.time())
    _save(FREE_FILE, data)

def get_status(uid: str) -> dict:
    return {
        "uid": uid,
        "is_subscribed": is_subscribed(uid),
        "has_free_used": has_free_used(uid),
        "free_remaining": not has_free_used(uid),
    }

# ── pdf_single (one-time managed product) ──
# Tek seferlik PDF satın alımı: bu hakkı olan kullanıcı bir rapor PDF'ini
# kalıcı olarak indirebilir (abonelik değil; bir kez satın alınan hak).
# uid -> "1" veya son kullanma zamanı.
def has_pdf_single(uid: str) -> bool:
    if not uid:
        return False
    data = _load(PURCHASES_FILE)
    val = data.get(uid)
    if val is None:
        return False
    try:
        exp = float(val)
        return exp == 0 or exp > time.time()
    except (TypeError, ValueError):
        # "1" gibi geçersiz ise yine de hak say (kalıcı)
        return True

def grant_pdf_single(uid: str, expiry: float = 0):
    if not uid:
        return
    data = _load(PURCHASES_FILE)
    data[uid] = str(expiry or 0)
    _save(PURCHASES_FILE, data)

def can_download_pdf(uid: str, device_token: str = "", tip: str = "") -> dict:
    """PDF indirme hakkı kararı.
    Return: {"allowed": bool, "reason": str}
    reason: subscribed | pdf_single | free | no_right
    """
    # Abonelik: sınırsız
    if is_subscribed(uid):
        return {"allowed": True, "reason": "subscribed"}
    # pdf_single: tek seferlik satın alım hakkı (herhangi bir tip)
    if has_pdf_single(uid):
        return {"allowed": True, "reason": "pdf_single"}
    # Ücretsiz ilk PDF
    if not has_free_used(uid, device_token):
        return {"allowed": True, "reason": "free"}
    return {"allowed": False, "reason": "no_right"}

def consume_pdf(uid: str, device_token: str = "", tip: str = "", reason: str = "free"):
    """PDF hakkını kullan. free ise ücretsiz hakkı tüketir."""
    if reason == "free":
        mark_free_used(uid, device_token)
    # subscribed / pdf_single için ekstra tüketim yok (kalıcı).
