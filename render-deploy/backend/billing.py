"""Billing & entitlement storage — dual-mode (PostgreSQL | file-based).

- `DATABASE_URL` env varsa PostgreSQL kullanilir (production/kalici).
- Yoksa eski file-based mod calisir (local/test, geriye donuk uyumlu).

Dis arayuz (main.py'nin kullandigi fonksiyonlar) degismedi:
  is_subscribed, upsert_subscription, has_free_used, mark_free_used,
  get_status, has_pdf_single, grant_pdf_single, can_download_pdf, consume_pdf
"""
import os, json, hashlib, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SUBS_FILE = DATA_DIR / "subscriptions.json"
FREE_FILE = DATA_DIR / "free_pdf_used.json"
PURCHASES_FILE = DATA_DIR / "pdf_purchases.json"

_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


# ─────────────────────────── File store ───────────────────────────
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


# ─────────────────────────── Postgres store ───────────────────────────
def _pg_connect():
    # Geç bağlan; her çağrıda yeni bağlantı (uygulama ömrü kısa, basit tut).
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(_DATABASE_URL)
    return conn

def _pg_ensure_schema():
    """Tabloları yoksa oluştur (idempotent)."""
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS billing_subs (
                    uid TEXT PRIMARY KEY,
                    product_id TEXT,
                    expiry DOUBLE PRECISION,
                    status TEXT,
                    provider TEXT,
                    updated DOUBLE PRECISION
                );
                CREATE TABLE IF NOT EXISTS billing_free (
                    key TEXT PRIMARY KEY,
                    used_at DOUBLE PRECISION
                );
                CREATE TABLE IF NOT EXISTS billing_pdf_single (
                    uid TEXT PRIMARY KEY,
                    expiry DOUBLE PRECISION
                );
            """)
        conn.commit()
    finally:
        conn.close()

def _use_pg() -> bool:
    return bool(_DATABASE_URL)

# — subscriptions —
def _pg_is_subscribed(uid: str) -> bool:
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT status, expiry FROM billing_subs WHERE uid=%s", (uid,))
            row = cur.fetchone()
        if not row:
            return False
        status, exp = row
        if status != "active":
            return False
        if exp and exp < time.time():
            return False
        return True
    finally:
        conn.close()

def _pg_upsert_subscription(uid, product_id, expiry, status, provider):
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO billing_subs (uid, product_id, expiry, status, provider, updated)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (uid) DO UPDATE SET
                  product_id=EXCLUDED.product_id, expiry=EXCLUDED.expiry,
                  status=EXCLUDED.status, provider=EXCLUDED.provider,
                  updated=EXCLUDED.updated
            """, (uid, product_id, expiry, status, provider, time.time()))
        conn.commit()
    finally:
        conn.close()

# — free used —
def _pg_has_free_used(uid: str, device_token: str) -> bool:
    keys = []
    if uid:
        keys.append(f"uid:{uid}")
    if device_token:
        keys.append(f"dev:{_hash(device_token)}")
    if not keys:
        return False
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            for k in keys:
                cur.execute("SELECT 1 FROM billing_free WHERE key=%s", (k,))
                if cur.fetchone():
                    return True
        return False
    finally:
        conn.close()

def _pg_mark_free_used(uid: str, device_token: str):
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            if uid:
                cur.execute("INSERT INTO billing_free (key, used_at) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                            (f"uid:{uid}", time.time()))
            if device_token:
                cur.execute("INSERT INTO billing_free (key, used_at) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                            (f"dev:{_hash(device_token)}", time.time()))
        conn.commit()
    finally:
        conn.close()

# — pdf_single —
def _pg_has_pdf_single(uid: str) -> bool:
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT expiry FROM billing_pdf_single WHERE uid=%s", (uid,))
            row = cur.fetchone()
        if not row:
            return False
        exp = row[0]
        return (exp is None) or (exp == 0) or (exp > time.time())
    finally:
        conn.close()

def _pg_grant_pdf_single(uid: str, expiry: float):
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO billing_pdf_single (uid, expiry) VALUES (%s,%s)
                ON CONFLICT (uid) DO UPDATE SET expiry=EXCLUDED.expiry
            """, (uid, expiry))
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────── Public API (main.py) ───────────────────────────
def is_subscribed(uid: str) -> bool:
    if not uid:
        return False
    if _use_pg():
        return _pg_is_subscribed(uid)
    rec = _load(SUBS_FILE).get(uid)
    if not rec:
        return False
    if rec.get("status") != "active":
        return False
    exp = rec.get("expiry", 0)
    if exp and exp < time.time():
        return False
    return True

def upsert_subscription(uid: str, product_id: str, expiry: float = 0, status: str = "active", provider: str = "revenuecat"):
    if not uid:
        return
    if _use_pg():
        _pg_ensure_schema()
        _pg_upsert_subscription(uid, product_id, expiry, status, provider)
        return
    subs = _load(SUBS_FILE)
    subs[uid] = {"product_id": product_id, "expiry": expiry, "status": status, "provider": provider, "updated": time.time()}
    _save(SUBS_FILE, subs)

def has_free_used(uid: str, device_token: str = "") -> bool:
    if _use_pg():
        return _pg_has_free_used(uid, device_token)
    data = _load(FREE_FILE)
    if uid and data.get(f"uid:{uid}"):
        return True
    if device_token and data.get(f"dev:{_hash(device_token)}"):
        return True
    return False

def mark_free_used(uid: str, device_token: str = ""):
    if _use_pg():
        _pg_mark_free_used(uid, device_token)
        return
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

def has_pdf_single(uid: str) -> bool:
    if not uid:
        return False
    if _use_pg():
        return _pg_has_pdf_single(uid)
    data = _load(PURCHASES_FILE)
    val = data.get(uid)
    if val is None:
        return False
    try:
        exp = float(val)
        return exp == 0 or exp > time.time()
    except (TypeError, ValueError):
        return True

def grant_pdf_single(uid: str, expiry: float = 0):
    if not uid:
        return
    if _use_pg():
        _pg_ensure_schema()
        _pg_grant_pdf_single(uid, expiry)
        return
    data = _load(PURCHASES_FILE)
    data[uid] = str(expiry or 0)
    _save(PURCHASES_FILE, data)

def can_download_pdf(uid: str, device_token: str = "", tip: str = "") -> dict:
    if is_subscribed(uid):
        return {"allowed": True, "reason": "subscribed"}
    if has_pdf_single(uid):
        return {"allowed": True, "reason": "pdf_single"}
    if not has_free_used(uid, device_token):
        return {"allowed": True, "reason": "free"}
    return {"allowed": False, "reason": "no_right"}

def consume_pdf(uid: str, device_token: str = "", tip: str = "", reason: str = "free"):
    if reason == "free":
        mark_free_used(uid, device_token)
    # subscribed / pdf_single için ekstra tüketim yok (kalıcı).