# -*- coding: utf-8 -*-
"""Kullanici geri bildirimi -> motor kalibrasyonu besleme.

NEDEN: kalibrasyon 22 kayit ama yon hatasi 49.5 derece. Bu veri kendiliginden
buyumez; kullanici nesneyi bulunca gercek konumu girer. 'Bulamadim' cevabi da
veridir - yon tahmini ise tutmamis demektir.

AKIS:
  1. /api/horary/cast cevabinda 'feedback_token' doner (okunmaz, gizli).
  2. Kullanici 'dogru muymus?' ekraninda bir tik atar:
       - 'Buldum' + gercek konum -> kalibrasyona KAYIT eklenir (olcek gelir)
       - 'Bulamadim'              -> yon hatasi kaydedilir, kalani veri olarak
                                     birikir (noktasal konum yok)
  3. Token gecerli degilse geri bildirim alinmaz: kimse rastgele veri
     enjekte edip motoru bozamaz.

Guvenli kural: geri bildirim ASLA yaniti degistirmez. Sadece sonraki
calismalarin kalibrasyonunu besler.
"""
import base64
import hashlib
import hmac
import json
import os
import time

TOKEN_SECRET = os.getenv("HORARY_FEEDBACK_SECRET", "")
_TOKEN_TTL = 60 * 60 * 6          # 6 saat

STORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "horary_feedback.json")


# ---------------- token ----------------
def _secret():
    """Geri bildirim token anahtarı. Ortamda yoksa kalibrasyon dosyasından
    turetilir (böylece anahtar kodda gezmez)."""
    global TOKEN_SECRET
    if not TOKEN_SECRET:
        cal = os.path.join(os.path.dirname(STORE), "horary_calibration.json")
        try:
            with open(cal, "rb") as f:
                TOKEN_SECRET = hashlib.sha256(f.read()).hexdigest()
        except Exception:
            TOKEN_SECRET = "feedback-local-dev"
    return TOKEN_SECRET


def _b64e(d):
    return base64.urlsafe_b64encode(
        json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()).decode().rstrip("=")


def _b64d(s):
    s += "=" * (-len(s) % 4)
    return json.loads(base64.urlsafe_b64decode(s.encode()).decode())


def make_token(email, question, question_type, origin_lat, origin_lon, direction=""):
    """Cevapla birlikte doner; kullanici butonu tiklayinca geri gonderilir."""
    payload = {
        "e": (email or "")[:120],
        "q": (question or "")[:200],
        "t": question_type or "",
        "lat": origin_lat, "lon": origin_lon,
        "dir": (direction or "")[:60],
        "ts": int(time.time()),
    }
    body = _b64e(payload)
    sig = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{body}.{sig}"


def read_token(token):
    """Gecerliyse payload doner, degilse None. Tek kullaniliktir."""
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
    if time.time() - d.get("ts", 0) > _TOKEN_TTL:
        return None
    return d


# ---------------- geri bildirim deposu ----------------
def _load():
    try:
        with open(STORE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"entries": []}


def _save(db):
    try:
        with open(STORE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=1)
        return True
    except Exception:
        return False


def record(email, question, question_type, outcome, found_where=None,
           predicted_dir=None, trust_level=None, recast=None, note=None):
    """outcome: 'found' | 'not_found'
    found_where: sadece 'found' icin - serbest metin ('salon, koltuk alti')
    recast: kullanici calistirdigi diger sorular (neden sonuca goturmedi)
    """
    db = _load()
    db.setdefault("entries", []).append({
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