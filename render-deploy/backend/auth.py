"""Supabase Auth integration — token dogrulama, profil ve kayitli kisiler.

Bagimliliklar (env):
- SUPABASE_URL         (örn. https://xyz.supabase.co)
- SUPABASE_ANON_KEY    (anon/public key)
- DATABASE_URL         (mevcut billing PG baglantisi; tablolar ayni veritabaninda)

Depolama: billing.py ile ayni dual-mode mantigi kullanir.
- DATABASE_URL varsa PostgreSQL (idempotent tablolar: auth_profiles, auth_people).
- Yoksa dosya tabanli store (data/auth_profiles.json, data/auth_people.json)
  — local/test ve DATABASE_URL tanimlanmayan ortamlar icin. Boylece kisi kaydi
  her kosulda calisir.

Dis arayuz (main.py):
  get_profile(user_id), upsert_profile(...)
  list_people(user_id), create_person(...), update_person(...), delete_person(...)
"""
import os, json, time
from datetime import datetime
from pathlib import Path

import requests

_BASE = Path(__file__).resolve().parent.parent
_DATA_DIR = _BASE / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_FILE = _DATA_DIR / "auth_profiles.json"
PEOPLE_FILE = _DATA_DIR / "auth_people.json"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def _pg_connect():
    import psycopg2
    conn = psycopg2.connect(_DATABASE_URL)
    return conn


def _use_pg():
    return bool(_DATABASE_URL)


# ─────────────────────────── File store (billing deseni) ───────────────────────────
def _fread(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _fwrite(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def _file_profiles() -> dict:
    return _fread(PROFILES_FILE)

def _file_people() -> dict:
    return _fread(PEOPLE_FILE)


def _pg_ensure_schema():
    if not _use_pg():
        return
    conn = _pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS auth_profiles (
                    user_id TEXT PRIMARY KEY,
                    email TEXT,
                    display_name TEXT,
                    lang TEXT DEFAULT 'tr',
                    created_at DOUBLE PRECISION
                );
                CREATE TABLE IF NOT EXISTS auth_people (
                    id SERIAL PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    birth_date TEXT,
                    birth_time TEXT,
                    city TEXT,
                    country TEXT,
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    utc_offset TEXT,
                    folder TEXT,
                    created_at DOUBLE PRECISION,
                    updated_at DOUBLE PRECISION
                );
                CREATE INDEX IF NOT EXISTS idx_auth_people_owner ON auth_people(owner_id);
            """)
        conn.commit()
    finally:
        conn.close()


def supabase_enabled():
    return bool(SUPABASE_URL)


def verify_token(authorization: str) -> dict | None:
    """Supabase Auth access token'ini Google sunucusunda dogrular.

    Basariliysa {'id', 'email', ...} dondurur; degilse None.
    Eger SUPABASE_URL tanimli degilse (local/fallback) token'i dogrulamadan
    gecerli kabul etmez -> None (guvenli).
    """
    if not supabase_enabled():
        return None
    token = (authorization or "").replace("Bearer ", "").strip()
    if not token:
        return None
    try:
        headers = {
            "Authorization": f"Bearer {token}",
        }
        r = requests.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        uid = (data or {}).get("id") or (data or {}).get("sub")
        if not uid:
            return None
        return {
            "id": uid,
            "email": (data or {}).get("email", ""),
            "display_name": (data or {}).get("user_metadata", {}).get("full_name", "")
                            or (data or {}).get("user_metadata", {}).get("name", ""),
            "raw": data,
        }
    except Exception as e:
        print(f"[auth] verify_token hatasi: {e}")
        return None


# ─────────────────────────── Profil ───────────────────────────
def get_profile(user_id: str) -> dict:
    if not user_id:
        return {}
    _pg_ensure_schema()
    if _use_pg():
        try:
            conn = _pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT email, display_name, lang, created_at FROM auth_profiles WHERE user_id=%s", (user_id,))
                    row = cur.fetchone()
                if not row:
                    return {"user_id": user_id}
                email, display_name, lang, created_at = row
                return {"user_id": user_id, "email": email, "display_name": display_name, "lang": lang,
                        "created_at": created_at}
            finally:
                conn.close()
        except Exception as e:
            print(f"[auth] get_profile hatasi: {e}")
            return {"user_id": user_id}

    # file fallback
    profiles = _file_profiles()
    p = profiles.get(user_id) or {}
    return {"user_id": user_id, "email": p.get("email"),
            "display_name": p.get("display_name"), "lang": p.get("lang"), "created_at": p.get("created_at")}


def upsert_profile(user_id: str, email: str = "", display_name: str = "", lang: str = "tr"):
    if not user_id:
        return
    _pg_ensure_schema()
    if _use_pg():
        try:
            conn = _pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO auth_profiles (user_id, email, display_name, lang, created_at)
                        VALUES (%s,%s,%s,%s,%s)
                        ON CONFLICT (user_id) DO UPDATE SET
                          email=EXCLUDED.email, display_name=EXCLUDED.display_name, lang=EXCLUDED.lang
                    """, (user_id, email, display_name, lang, time.time()))
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            print(f"[auth] upsert_profile hatasi: {e}")
            return

    # file fallback
    profiles = _file_profiles()
    prev = profiles.get(user_id) or {}
    profiles[user_id] = {
        "user_id": user_id,
        "email": email or prev.get("email", ""),
        "display_name": display_name or prev.get("display_name", ""),
        "lang": lang or prev.get("lang", "tr"),
        "created_at": prev.get("created_at") or time.time(),
    }
    _fwrite(PROFILES_FILE, profiles)


# ─────────────────────────── Kayitli kisiler ───────────────────────────
def _person_row_to_dict(row) -> dict:
    (pid, owner_id, name, birth_date, birth_time, city, country,
     lat, lon, utc_offset, folder, created_at, updated_at) = row
    return {
        "id": pid,
        "owner_id": owner_id,
        "name": name,
        "birth_date": birth_date,
        "birth_time": birth_time,
        "city": city,
        "country": country,
        "lat": lat,
        "lon": lon,
        "utc_offset": utc_offset,
        "folder": folder,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def list_people(user_id: str) -> list:
    if not user_id:
        return []
    _pg_ensure_schema()
    if _use_pg():
        try:
            conn = _pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, owner_id, name, birth_date, birth_time, city, country, lat, lon, utc_offset, folder, created_at, updated_at "
                        "FROM auth_people WHERE owner_id=%s ORDER BY folder, name",
                        (user_id,))
                    rows = cur.fetchall()
                return [_person_row_to_dict(r) for r in rows]
            finally:
                conn.close()
        except Exception as e:
            print(f"[auth] list_people hatasi: {e}")
            return []

    # file fallback
    return _file_people().get(user_id, [])


def create_person(user_id: str, data: dict) -> dict | None:
    if not user_id or not data.get("name"):
        return None
    _pg_ensure_schema()
    if _use_pg():
        try:
            now = time.time()
            conn = _pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO auth_people (owner_id, name, birth_date, birth_time, city, country, lat, lon, utc_offset, folder, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id, owner_id, name, birth_date, birth_time, city, country, lat, lon, utc_offset, folder, created_at, updated_at
                    """, (user_id, data.get("name"), data.get("birth_date"), data.get("birth_time"),
                          data.get("city"), data.get("country"), data.get("lat"), data.get("lon"),
                          data.get("utc_offset"), data.get("folder", ""), now, now))
                    row = cur.fetchone()
                conn.commit()
                return _person_row_to_dict(row)
            finally:
                conn.close()
        except Exception as e:
            print(f"[auth] create_person hatasi: {e}")
            return None

    # file fallback
    now = time.time()
    people = _file_people()
    lst = people.setdefault(user_id, [])
    new_id = (max([p.get("id") or 0 for p in lst], default=0) + 1)
    row = {"id": new_id, "owner_id": user_id, "name": data.get("name"),
           "birth_date": data.get("birth_date"), "birth_time": data.get("birth_time"),
           "city": data.get("city"), "country": data.get("country"),
           "lat": data.get("lat"), "lon": data.get("lon"),
           "utc_offset": data.get("utc_offset"), "folder": data.get("folder", ""),
           "created_at": now, "updated_at": now}
    lst.append(row)
    _fwrite(PEOPLE_FILE, people)
    return row

def update_person(user_id: str, person_id: int, data: dict) -> dict | None:
    if not user_id:
        return None
    _pg_ensure_schema()
    if _use_pg():
        try:
            conn = _pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM auth_people WHERE id=%s AND owner_id=%s", (person_id, user_id))
                    if not cur.fetchone():
                        return None
                    cur.execute("""
                        UPDATE auth_people SET
                          name=COALESCE(%s, name),
                          birth_date=COALESCE(%s, birth_date),
                          birth_time=COALESCE(%s, birth_time),
                          city=COALESCE(%s, city),
                          country=COALESCE(%s, country),
                          lat=COALESCE(%s, lat),
                          lon=COALESCE(%s, lon),
                          utc_offset=COALESCE(%s, utc_offset),
                          folder=COALESCE(%s, folder),
                          updated_at=%s
                        WHERE id=%s AND owner_id=%s
                        RETURNING id, owner_id, name, birth_date, birth_time, city, country, lat, lon, utc_offset, folder, created_at, updated_at
                    """, (data.get("name"), data.get("birth_date"), data.get("birth_time"),
                          data.get("city"), data.get("country"), data.get("lat"), data.get("lon"),
                          data.get("utc_offset"), data.get("folder"), time.time(), person_id, user_id))
                    row = cur.fetchone()
                conn.commit()
                return _person_row_to_dict(row)
            finally:
                conn.close()
        except Exception as e:
            print(f"[auth] update_person hatasi: {e}")
            return None

    # file fallback
    people = _file_people()
    lst = people.get(user_id, [])
    for row in lst:
        if row.get("id") == person_id:
            row.update({k: data[k] for k in ("name", "birth_date", "birth_time", "city", "country",
                                             "lat", "lon", "utc_offset", "folder") if data.get(k) is not None})
            row["updated_at"] = time.time()
            _fwrite(PEOPLE_FILE, people)
            return row
    return None


def delete_person(user_id: str, person_id: int) -> bool:
    if not user_id:
        return False
    _pg_ensure_schema()
    if _use_pg():
        try:
            conn = _pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM auth_people WHERE id=%s AND owner_id=%s", (person_id, user_id))
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception as e:
            print(f"[auth] delete_person hatasi: {e}")
            return False

    # file fallback
    people = _file_people()
    lst = people.get(user_id, [])
    remaining = [row for row in lst if row.get("id") != person_id]
    if len(remaining) == len(lst):
        return False
    people[user_id] = remaining
    _fwrite(PEOPLE_FILE, people)
    return True


DEFAULT_FOLDERS = ["ailem", "arkadaslarim"]


def folder_labels(lang: str = "tr", user_id: str = "") -> dict:
    base = {"ailem", "arkadaslarim"}
    base_map = {k: k for k in base}
    if lang == "en":
        base_map = {"ailem": "My Family", "arkadaslarim": "My Friends"}
    elif lang == "es":
        base_map = {"ailem": "Mi Familia", "arkadaslarim": "Mis Amigos"}
    else:
        base_map = {"ailem": "Ailem", "arkadaslarim": "Arkadaşlarım"}
    # Kullanıcının dosya deposunda oluşturduğu özel klasörleri de ekle.
    if user_id:
        try:
            for p in _file_people().get(user_id, []):
                f = (p.get("folder") or "").strip()
                if f and f not in base_map:
                    base_map[f] = f
        except Exception:
            pass
    return base_map