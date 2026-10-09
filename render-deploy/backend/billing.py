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
CREDITS_FILE = DATA_DIR / "pdf_credits.json"
TXNS_FILE = DATA_DIR / "pdf_seen_txns.json"

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
_SCHEMA_READY = False


def _pg_connect():
    # Geç bağlan; her çağrıda yeni bağlantı (uygulama ömrü kısa, basit tut).
    import psycopg2
    conn = psycopg2.connect(_DATABASE_URL, connect_timeout=10)
    return conn


def _pg_retry(fn, *a, **kw):
    """PG işlemini 3 denemeyle dener. Başarılıysa değeri, kalıcı hatada None."""
    son = None
    for deneme in range(3):
        try:
            return fn(*a, **kw)
        except Exception as e:
            son = e
            print(f"[billing] PG deneme {deneme+1}/3 hata: {e}")
            time.sleep(1)
    print(f"[billing] PG KALICI HATA ({fn.__name__}): {son}")
    return None


def ensure_schema_ready(force: bool = False) -> bool:
    """Şemayı bir kez kurar. Hazırsa True, aksi halde False (fail-closed)."""
    global _SCHEMA_READY
    if not _use_pg():
        return True
    if _SCHEMA_READY and not force:
        return True
    if _pg_retry(_pg_ensure_schema) is None:
        print("[billing] POSTGRES KULLANILAMIYOR — haklar dosya deposuna yazilacak")
        return False
    _SCHEMA_READY = True
    print("[billing] postgres sema hazir")
    return True


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
                CREATE TABLE IF NOT EXISTS billing_pdf_credits (
                    uid TEXT PRIMARY KEY,
                    credits INTEGER NOT NULL DEFAULT 0,
                    updated DOUBLE PRECISION
                );
                CREATE TABLE IF NOT EXISTS billing_pdf_txns (
                    uid TEXT,
                    txn TEXT,
                    created DOUBLE PRECISION,
                    PRIMARY KEY (uid, txn)
                );
                CREATE TABLE IF NOT EXISTS analysis_sessions (
                    session_id TEXT PRIMARY KEY,
                    builder TEXT,
                    input JSONB,
                    created_at DOUBLE PRECISION
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
        return True
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
        return True
    finally:
        conn.close()

# — pdf_single kredileri (Model B: ilk ücretsiz hariç her kitap 1 kredi) —
def _pg_get_credits_row(uid: str):
    """Kredi satırı yoksa None, varsa int döner (yok/bilinmiyor ayrımı için)."""
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT credits FROM billing_pdf_credits WHERE uid=%s", (uid,))
            row = cur.fetchone()
        if not row:
            return None
        try:
            return max(0, int(row[0] or 0))
        except (TypeError, ValueError):
            return 0
    finally:
        conn.close()

def _pg_add_credits(uid: str, n: int) -> int:
    """Krediye n ekler (negatifte taban 0). Tek atomik ifade — çift uygulama yok."""
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO billing_pdf_credits (uid, credits, updated)
                VALUES (%s, GREATEST(0, %s), %s)
                ON CONFLICT (uid) DO UPDATE SET
                  credits = GREATEST(0, billing_pdf_credits.credits + %s),
                  updated = EXCLUDED.updated
            """, (uid, n, time.time(), n))
            cur.execute("SELECT credits FROM billing_pdf_credits WHERE uid=%s", (uid,))
            row = cur.fetchone()
        conn.commit()
        return max(0, int((row or [0])[0] or 0))
    finally:
        conn.close()

def _pg_txn_seen(uid: str, txn: str):
    """True/False; PG bilinmiyorsa None."""
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM billing_pdf_txns WHERE uid=%s AND txn=%s", (uid, txn))
            return bool(cur.fetchone())
    finally:
        conn.close()

def _pg_mark_txn(uid: str, txn: str):
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO billing_pdf_txns (uid, txn, created) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                        (uid, txn, time.time()))
        conn.commit()
        return True
    finally:
        conn.close()

def _pg_legacy_row(uid: str):
    """Eski kalıcı hak satırı: True/False; PG bilinmiyorsa None."""
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM billing_pdf_single WHERE uid=%s", (uid,))
            return bool(cur.fetchone())
    finally:
        conn.close()

def _pg_delete_legacy(uid: str):
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM billing_pdf_single WHERE uid=%s", (uid,))
        conn.commit()
        return True
    finally:
        conn.close()

# — pdf_single (legacy kalıcı bayrak — migrasyon sonrası okunmaz) —
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
        return True
    finally:
        conn.close()


# ─────────────────────────── Public API (main.py) ───────────────────────────
def storage_mode() -> str:
    """Hakların gerçekte nerede durduğunu bildirir (teşhis için)."""
    if not _use_pg():
        return "file"
    if _pg_retry(_pg_is_subscribed, "__probe__") is not None:
        return "postgres"
    return "postgres-disi"


def _file_has_free_used(uid: str, device_token: str = ""):
    """None = bilinmiyor (dosya hic yok), True/False = kesin durum."""
    if not FREE_FILE.exists():
        return None
    data = _load(FREE_FILE)
    if uid and data.get(f"uid:{uid}"):
        return True
    if device_token and data.get(f"dev:{_hash(device_token)}"):
        return True
    return False


def _file_mark_free_used(uid: str, device_token: str = "") -> bool:
    try:
        data = _load(FREE_FILE)
        if uid:
            data[f"uid:{uid}"] = int(time.time())
        if device_token:
            data[f"dev:{_hash(device_token)}"] = int(time.time())
        _save(FREE_FILE, data)
        return True
    except Exception as e:
        print(f"[billing] dosya yedegi yazilamadi: {e}")
        return False


# — pdf kredi sayacı (dosya modu) —
def _file_get_credits_row(uid: str):
    """Satır yoksa None, varsa int (yok/bilinmiyor ayrımı için)."""
    data = _load(CREDITS_FILE)
    if uid not in data:
        return None
    try:
        return max(0, int(data.get(uid) or 0))
    except (TypeError, ValueError):
        return 0

def _file_add_credits(uid: str, n: int) -> int:
    try:
        data = _load(CREDITS_FILE)
        cur = 0
        try:
            cur = max(0, int(data.get(uid) or 0))
        except (TypeError, ValueError):
            cur = 0
        new = max(0, cur + n)
        data[uid] = new
        _save(CREDITS_FILE, data)
        return new
    except Exception as e:
        print(f"[billing] kredi dosyasi yazilamadi: {e}")
        return max(0, n)

def _file_txn_seen(uid: str, txn: str) -> bool:
    data = _load(TXNS_FILE)
    return bool(data.get(f"{uid}|{txn}"))

def _file_mark_txn(uid: str, txn: str) -> bool:
    try:
        data = _load(TXNS_FILE)
        data[f"{uid}|{txn}"] = int(time.time())
        _save(TXNS_FILE, data)
        return True
    except Exception as e:
        print(f"[billing] islem defteri yazilamadi: {e}")
        return False

def _file_delete_legacy(uid: str):
    try:
        data = _load(PURCHASES_FILE)
        if uid in data:
            del data[uid]
            _save(PURCHASES_FILE, data)
    except Exception:
        pass


def is_subscribed(uid: str) -> bool:
    if not uid:
        return False
    if _use_pg():
        sonuc = _pg_retry(_pg_is_subscribed, uid)
        if sonuc is not None:
            return sonuc
        rec = _load(SUBS_FILE).get(uid)
        if rec:
            return rec.get("status") == "active" and (
                not rec.get("expiry") or rec.get("expiry", 0) >= time.time())
        return False
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
        if _pg_retry(_pg_upsert_subscription, uid, product_id, expiry, status, provider) is not None:
            return
        # PG yoksa en azindan dosyaya yaz (kalici degil ama calistikca hak korunur)
        print(f"[billing] upsert dosyaya yazildi uid={uid}")
    subs = _load(SUBS_FILE)
    subs[uid] = {"product_id": product_id, "expiry": expiry, "status": status, "provider": provider, "updated": time.time()}
    _save(SUBS_FILE, subs)

FREE_PROGRAM_DISABLED = True  # Örnek/ücretsiz PDF kaldırıldı: tüm kitaplar ödemeli.

def has_free_used(uid: str, device_token: str = "") -> bool:
    """True = ucretsiz hak kullanimda.

    KRITIK: Onceki surumde PG hatasi durumunda False donuyordu (fail-open).
    Bu, depolama hic yazilamadiginda herkese SINIRSIZ ucretsiz PDF veriyordu.
    Artik bilinmiyorsa guvenli tarafa dusulur.

    Model B+: ücretsiz program tamamen kapatıldı — her zaman True (hak yok).
    """
    if FREE_PROGRAM_DISABLED:
        return True
    if _use_pg():
        sonuc = _pg_retry(_pg_has_free_used, uid, device_token)
        if sonuc is not None:
            return sonuc
        # PG okunamadi -> dosyaya dus
        dosya = _file_has_free_used(uid, device_token)
        if dosya is not None:
            return dosya
        if os.getenv("BILLING_FAIL_CLOSED", "1").strip().lower() in ("0", "false", "no", "off"):
            print("[billing] UYARI: ucretsiz hak durumu belirlenemedi ve "
                  "BILLING_FAIL_CLOSED=0 -> indirmeye IZIN verildi (KACAK ACIK)")
            return False
        print("[billing] UYARI: ucretsiz hak durumu belirlenemedi -> "
              "indirme reddedildi (fail-closed)")
        return True
    dosya = _file_has_free_used(uid, device_token)
    return bool(dosya)

def mark_free_used(uid: str, device_token: str = ""):
    """Ucretsiz hakki tuket. Onceki surumde dosya yedegi YOKTU; PG hatasinda
    tuketim sessizce kayboluyor ve hak hiç bitmiyordu. Artik her zaman bir
    depoya yazilir.

    Model B+: program kapalı — no-op (imza uyumluluk için korundu).
    """
    if FREE_PROGRAM_DISABLED:
        return
    if _use_pg():
        if _pg_retry(_pg_mark_free_used, uid, device_token) is not None:
            return
        # onceki surumde burasi sessizce geciyordu -> hak kayboluyordu
        print(f"[billing] mark_free_used PG basarisiz, dosyaya yaziliyor uid={uid}")
    _file_mark_free_used(uid, device_token)

def get_status(uid: str) -> dict:
    return {
        "uid": uid,
        "is_subscribed": is_subscribed(uid),
        "has_free_used": has_free_used(uid),
        "free_remaining": not has_free_used(uid),
        "has_pdf_single": has_pdf_single(uid),
        "pdf_credits": get_pdf_credits(uid),
    }

def _migrate_legacy_pdf_single(uid: str):
    """Eski kalıcı hak (tek satın alma = ömür boyu) → Model B: 1 kredi.
    Her depo bağımsız taşınır (aynı uid iki depoda da hakka sahip olabilir —
    ikisi de gerçek satın almadır). Idempotent: legacy satır taşınınca silinir.
    """
    if not uid:
        return
    if _use_pg():
        leg = _pg_retry(_pg_legacy_row, uid)
        if leg:
            if _pg_retry(_pg_get_credits_row, uid) is None:
                _pg_retry(_pg_add_credits, uid, 1)
                print(f"[billing] legacy pdf_single -> 1 kredi (PG) uid={uid}")
            _pg_retry(_pg_delete_legacy, uid)
    data = _load(PURCHASES_FILE)
    if uid in data:
        if _file_get_credits_row(uid) is None:
            _file_add_credits(uid, 1)
            print(f"[billing] legacy pdf_single -> 1 kredi (dosya) uid={uid}")
        _file_delete_legacy(uid)

def get_pdf_credits(uid: str) -> int:
    """Kalan kitap kredisi (ilk ücretsiz hak hariç)."""
    if not uid:
        return 0
    _migrate_legacy_pdf_single(uid)
    if _use_pg():
        sonuc = _pg_retry(_pg_get_credits_row, uid)
        if sonuc is not None:
            return sonuc
    v = _file_get_credits_row(uid)
    return v if v is not None else 0

def add_pdf_credits(uid: str, n: int) -> int:
    if not uid:
        return 0
    if _use_pg():
        sonuc = _pg_retry(_pg_add_credits, uid, n)
        if sonuc is not None:
            return sonuc
        print(f"[billing] add_credits PG basarisiz, dosyaya yaziliyor uid={uid}")
    return _file_add_credits(uid, n)

def txn_granted(uid: str, txn: str) -> bool:
    """Bu satın alma işlemi daha önce krediye çevrildi mi? (çift-kredi koruması)"""
    if not uid or not txn:
        return False
    if _use_pg():
        sonuc = _pg_retry(_pg_txn_seen, uid, txn)
        if sonuc is not None:
            return sonuc
    return _file_txn_seen(uid, txn)

def mark_txn_granted(uid: str, txn: str):
    if not uid or not txn:
        return
    if _use_pg():
        if _pg_retry(_pg_mark_txn, uid, txn) is not None:
            return
    _file_mark_txn(uid, txn)

def has_pdf_single(uid: str) -> bool:
    # Model B: kalıcı bayrak yok; kredi > 0 ise hak var.
    return get_pdf_credits(uid) > 0

def grant_pdf_single(uid: str, expiry: float = 0):
    """Model B: her hak kazandıran olay +1 kredi (kalıcı bayrak yazılmaz).
    İmza korundu — webhook/sync çağıranları değişmedi."""
    if not uid:
        return
    add_pdf_credits(uid, 1)

def can_download_pdf(uid: str, device_token: str = "", tip: str = "") -> dict:
    # Model B+: ücretsiz dal YOK — abone, kredisi olan, ya da 402 (ödeme).
    if is_subscribed(uid):
        return {"allowed": True, "reason": "subscribed"}
    if has_pdf_single(uid):
        return {"allowed": True, "reason": "pdf_single"}
    return {"allowed": False, "reason": "no_right"}

def consume_pdf(uid: str, device_token: str = "", tip: str = "", reason: str = "free"):
    if reason == "free":
        mark_free_used(uid, device_token)
    elif reason == "pdf_single":
        # Model B: her kitap 1 kredi düşer (taban 0).
        add_pdf_credits(uid, -1)
    # subscribed için tüketim yok (abonelik sınırsız).