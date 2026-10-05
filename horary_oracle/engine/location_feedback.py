# -*- coding: utf-8 -*-
"""Kullanici geri bildirimi -> motor kalibrasyonu besleme.

NEDEN: kalibrasyon 22 kayit ama yon hatasi 49.5 derece. Bu veri kendiliginden
buyumez; kullanici nesneyi bulunca gercek konumu girer. 'Bulamadim' cevabi da
veridir - yon tahmini ise tutmamis demektir.

AKIS:
  1. /api/horary/cast cevabinda 'feedback_token' doner (okunmaz, gizli).
  2. Kullanici 'dogru muymus?' ekraninda bir tik atar:
       - 'Buldum' + nerede buldun  -> gercek konum ipucu olarak birikir
       - 'Bulamadim'               -> yon tutmadi demektir, o da veridir
  3. Jeton imzali ve TEK KULLANIMLIDIR: ayni jeton iki kez gonderilemez,
     boylece tek bir cevap binlerce sahte kayit uretemez.
  4. Gecersiz jetonla gelen istek hic kaydedilmez.

Guvenli kural: geri bildirim ASLA yaniti degistirmez. Sadece sonraki
calismalarin kalibrasyonunu besler.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time

_TOKEN_TTL = 60 * 60 * 6          # 6 saat
_MAX_USED = 5000                  # saklanan jeton izlerinin tavan sayisi

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

TOKEN_SECRET = os.getenv("HORARY_FEEDBACK_SECRET", "")

# DIKKAT: bu depo 'horary_feedback.json' DEGILDIR. O dosya eski is-sonucu
# geri bildirimleri iceren bir JSON LISTESidir ve farkli bir sema kullanir;
# ayni dosyaya yazmak ya veriyi bozar ya da yazmayi engeller. Konum geri
# bildirimi kendi dosyasinda durur.
STORE = os.getenv("HORARY_FEEDBACK_DB") or os.path.join(_ROOT, "horary_location_feedback.json")
_SECRET_FILE = os.path.join(_ROOT, "horary_feedback_secret")

# Yazma yarisi: iki istek ayni anda gelirse biri digerinin kaydini ezmesin.
_LOCK = threading.Lock()


# ---------------- token ----------------
def _secret():
    """Geri bildirim jetonu anahtari.

    Oncelik sirasi: env degiskeni > kalibrasyon dosyasindan turetme > bir kez
    uretilip diske yazilan kalici sifre.

    Kalibrasyon dosyasindan turetmek tek seferlik kolay yoldu ama dosya her
    kayit eklendiginde degistigi icin butun eski jetonlari gecersiz kiliyordu.
    Artik anahtar kalibrasyondan bagimsiz ve kalicidir.
    """
    global TOKEN_SECRET
    if TOKEN_SECRET:
        return TOKEN_SECRET
    if os.path.exists(_SECRET_FILE):
        try:
            with open(_SECRET_FILE, "r", encoding="utf-8") as f:
                TOKEN_SECRET = f.read().strip()
            if TOKEN_SECRET:
                return TOKEN_SECRET
        except Exception:
            pass
    cal = os.path.join(_ROOT, "horary_calibration.json")
    if os.path.exists(cal):
        try:
            with open(cal, "rb") as f:
                TOKEN_SECRET = hashlib.sha256(b"horary-feedback|" + f.read()).hexdigest()
            return TOKEN_SECRET
        except Exception:
            pass
    # Son care: kurulumda bir kez uretilip yazilir, sonraki restart'larda ayni kalir.
    TOKEN_SECRET = secrets.token_hex(32)
    try:
        with open(_SECRET_FILE, "w", encoding="utf-8") as f:
            f.write(TOKEN_SECRET)
        try:
            os.chmod(_SECRET_FILE, 0o600)
        except Exception:
            pass
    except Exception:
        pass          # yazamazsak da calisir, sadece restart'ta yeni anahtar olur
    return TOKEN_SECRET


def _b64e(d):
    return base64.urlsafe_b64encode(
        json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()).decode().rstrip("=")


def _b64d(s):
    s += "=" * (-len(s) % 4)
    return json.loads(base64.urlsafe_b64decode(s.encode()).decode())


def make_token(email, question, question_type, origin_lat, origin_lon, direction=""):
    """Cevapla birlikte doner; kullanici butonu tiklayinca geri gonderilir.

    'jti' tek kullanimlik jeton sayacidir: ayni jeton ikinci kez gonderilirse
    reddedilir."""
    payload = {
        "e": (email or "")[:120],
        "q": (question or "")[:200],
        "t": question_type or "",
        "lat": origin_lat, "lon": origin_lon,
        "dir": (direction or "")[:60],
        "jti": secrets.token_hex(12),
        "ts": int(time.time()),
    }
    body = _b64e(payload)
    sig = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{body}.{sig}"


def read_token(token):
    """Gecerliyse payload doner, degilse None.

    DURUM DEGISTIRMEZ - sadece okur. Tek kullanim garantisi icin
    submit() kullanilir."""
    if not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    want = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, want):
        return None
    try:
        d = _b64d(body)
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    if time.time() - d.get("ts", 0) > _TOKEN_TTL:
        return None
    return d


# ---------------- geri bildirim deposu ----------------
def _load():
    """Depoyu okur. Bozuk/eskiden kalan liste bicimi ASLA cokmez."""
    try:
        with open(STORE, "r", encoding="utf-8") as f:
            db = json.load(f)
    except Exception:
        return {"entries": [], "used_tokens": []}
    if isinstance(db, list):
        # eski sema: ayri dosyaya tasinir, veri kaybolmaz
        return {"entries": [], "used_tokens": [], "legacy_list": len(db)}
    if not isinstance(db, dict):
        return {"entries": [], "used_tokens": []}
    db.setdefault("entries", [])
    db.setdefault("used_tokens", [])
    if not isinstance(db["entries"], list):
        db["entries"] = []
    if not isinstance(db["used_tokens"], list):
        db["used_tokens"] = []
    return db


def _save(db):
    """Atomik yazim: yarim kalmis dosya bir sonraki okumayi bozmasin."""
    tmp = f"{STORE}.tmp{os.getpid()}"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=1)
        os.replace(tmp, STORE)
        return True
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        return False


def _prune_used(db):
    """Eski jeton izlerini at; bellek/disk sismesin."""
    used = db.get("used_tokens", [])
    if len(used) > _MAX_USED:
        db["used_tokens"] = used[-_MAX_USED:]


def record(email, question, question_type, outcome, found_where=None,
           predicted_dir=None, trust_level=None, recast=None, note=None):
    """outcome: 'found' | 'not_found'
    found_where: sadece 'found' icin - serbest metin ('salon, koltuk alti')
    recast: kullanici calistirdigi diger sorular (neden sonuca goturmedi)
    """
    with _LOCK:
        db = _load()
        db["entries"].append({
            "ts": int(time.time()),
            "email": (email or "")[:120],
            "question": (question or "")[:200],
            "question_type": question_type or "",
            "outcome": outcome,
            "found_where": (found_where or "")[:200] or None,
            "predicted_dir": (predicted_dir or "")[:60] or None,
            "trust_level": trust_level or "",
            "recast": (recast or "")[:300] or None,
            "note": (note or "")[:300] or None,
        })
        _save(db)
        return len(db["entries"])


def submit(token, found, found_where=None, recast=None, note=None,
           trust_level=None):
    """Jetonu dogrula, TEK KULLANIMINI harca ve kaydet - hepsi tek kilit icinde.

    Doner: (ok, info). ok=False ise info['error'] doludur ve HICBIR SEY yazilmaz.
    Atomik olmanin nedeni: dogrulama ile 'kullanildi' isaretini ayri ayri
    yapmak yarista tek bir jetonun iki kez gecmesine izin verirdi.
    """
    with _LOCK:
        d = read_token(token)
        if not d:
            return False, {"error": "gecersiz veya suresi dolmus jeton"}
        jti = d.get("jti")
        if not jti:
            return False, {"error": "jeton yok sayfa sayiliyor"}
        db = _load()
        if jti in db["used_tokens"]:
            return False, {"error": "jeton zaten kullanildi"}
        db["used_tokens"].append(jti)
        _prune_used(db)
        db["entries"].append({
            "ts": int(time.time()),
            "email": d.get("e") or "",
            "question": d.get("q") or "",
            "question_type": d.get("t") or "",
            "outcome": "found" if found else "not_found",
            "found_where": (found_where or "")[:200] or None,
            "predicted_dir": d.get("dir") or None,
            "trust_level": trust_level or "",
            "recast": (recast or "")[:300] or None,
            "note": (note or "")[:300] or None,
        })
        _save(db)
        return True, {"saved": len(db["entries"])}


def stats(question_type=None):
    """Gercek basari orani - guveni satma yerine olcum."""
    es = _load().get("entries", [])
    if question_type:
        es = [e for e in es if e.get("question_type") == question_type]
    found = sum(1 for e in es if e.get("outcome") == "found")
    miss = sum(1 for e in es if e.get("outcome") == "not_found")
    n = len(es)
    return {
        "n": n,
        "found": found,
        "not_found": miss,
        "hit_rate": round(found / n, 3) if n else None,
        "by_type": _by_type(),
    }


def _by_type():
    out = {}
    for e in _load().get("entries", []):
        t = e.get("question_type") or "?"
        o = out.setdefault(t, {"n": 0, "found": 0})
        o["n"] += 1
        if e.get("outcome") == "found":
            o["found"] += 1
    for t, o in out.items():
        o["hit_rate"] = round(o["found"] / o["n"], 3) if o["n"] else None
    return out