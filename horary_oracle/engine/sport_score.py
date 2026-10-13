# -*- coding: utf-8 -*-
"""SPOR SKOR / TOPLAM GOL KALİBRASYONU.

NEDEN VAR: "kaç kaç biter" bir SKOR sorusudur. Horary'nin kesin skor satırı
tahmin yöntemi YOKTUR; uydurma bir "3-1" ürünün güven ilkesine aykırıdır.
Ölçülebilir tek şey TOPLAM GOL sayısıdır (ve ondan türeyen alt/üst bahsi).
Bu modül onu da gol-dakikası modeliyle AYNI felsefeyle kalibre eder:
haritadan bir sinyal çıkarılır, gerçek maç sonuçlarıyla ilişkisi ölçülür ve
YETERLİ VERİ + DÜŞÜK HATA yoksa SAYI VERİLMEZ.

SİNYAL (hipotez, ölçülüyor): "uygulayıcı major açı sayısı". Spor
astrolojisinde yaygın bir sezgi, gökyüzündeki ETKİN (applying) açıların
sayısının olay (gol) sayısıyla ilişkili olduğudur. Bunu 7 klasik gezegen
(Güneş..Satürn) arasındaki applying Ptolemaik açı sayısı olarak tanımlıyoruz.
Bu bir VARSAYIMDIR; fit onu gerçek skorlarla sınar, tutmuyorsa güven kapısı
zaten sayı göstermez.

MODEL: toplam_gol = round(c * sinyal + d), [0, MAX_TOTAL_GOALS] aralığına
kırpılır. (c, d) MAE'yi en küçükleyen değerlerdir.

Kayıt şeması: sport_calibration deposundaki her maç kaydında
  "scoring_index": int   (haritadan önceden hesaplanıp saklanır)
  "goal_minutes": [...]  (toplam gol = len) veya "total_goals": int

Öğrenilen parametreler horary_sport_score_params.json dosyasına yazılır.
Bu modül horary_engine'e BAĞIMLI DEĞİLDİR (döngüsel import olmasın diye
aspect/uygulama mantığı burada bağımsız ve deterministik tutulur).
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
SCORE_PARAMS_FILE = os.path.join(_HERE, "..", "horary_sport_score_params.json")

CLASSICAL = ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
MAJOR_ANGLES = (0, 60, 90, 120, 180)
# açı bazlı orb (derece) — uygulayıcı kabul eşiği
ORB = {0: 8.0, 60: 6.0, 90: 7.0, 120: 7.0, 180: 8.0}

MIN_FIT_MATCHES = 5          # altında fit denenmez (skor gürültülü bir hedef)
MIN_TRUST_STRONG = 8         # "guclu" için en az maç
MAE_STRONG = 1.0             # toplam gol: ortalama sapma ≤1 gol
MAE_MID = 1.6                # toplam gol: ortalama sapma ≤1.6 gol
MAX_TOTAL_GOALS = 9
DEFAULT_TOTAL = 2            # yalnız sentetik/varsayılan; güven kapısı geçilmeden gösterilmez


def _closest_major(diff):
    """0..180 açısal farkına en yakın major açı: (angle, dist)."""
    best = None
    for a in MAJOR_ANGLES:
        d = abs(diff - a)
        if best is None or d < best[1]:
            best = (a, d)
    return best


def scoring_index(planets, applying_only=True):
    """7 klasik gezegen arası applying major açı sayısı (0..21).

    planets: {name: {"lon": float, "speed": float, ...}} (cast_horary_chart çıktısı).
    applying_only=True: yalnız yakınlaşan (uygulayıcı) açılar sayılır.
    """
    names = [n for n in CLASSICAL if n in planets]
    idx = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = planets[names[i]]
            b = planets[names[j]]
            diff = abs((b["lon"] - a["lon"] + 180) % 360 - 180)
            ang, dist = _closest_major(diff)
            if dist > ORB.get(ang, 8.0):
                continue
            if applying_only:
                s1 = a.get("speed", 0.0)
                s2 = b.get("speed", 0.0)
                diff_next = abs((b["lon"] + s2 - (a["lon"] + s1) + 180) % 360 - 180)
                _, dist_next = _closest_major(diff_next)
                if dist_next >= dist:
                    continue
            idx += 1
    return idx


def total_goals(rec):
    """Kayıttan gerçek toplam gol. Açık 'total_goals' > len(goal_minutes)."""
    if rec.get("total_goals") is not None:
        return int(rec["total_goals"])
    gm = rec.get("goal_minutes")
    return len(gm) if gm else None


def _clamp(v):
    return max(0, min(MAX_TOTAL_GOALS, int(round(v))))


def fit_score_params(records, min_matches=MIN_FIT_MATCHES):
    """(c, d) öğren: toplam_gol = round(c*sinyal + d). Grid arama + inceltme.
    Döner: {fitted, c, d, mae, n, reason?}."""
    usable = []
    for r in records:
        x = r.get("scoring_index")
        y = total_goals(r)
        if x is None or y is None:
            continue
        usable.append((float(x), float(y)))
    if len(usable) < min_matches:
        return {"fitted": False, "c": None, "d": None, "mae": None,
                "n": len(usable), "reason": "en az %d maç gerek" % min_matches}

    def mae(c, d):
        errs = [abs(_clamp(c * x + d) - y) for x, y in usable]
        return sum(errs) / len(errs)

    best = None
    c = -0.6
    while c <= 0.6 + 1e-9:
        d = 0.0
        while d <= 6.0 + 1e-9:
            e = mae(c, d)
            if best is None or e < best[0]:
                best = (e, c, d)
            d += 0.25
        c += 0.02
    e0, c0, d0 = best
    for step_c, step_d in ((0.005, 0.1), (0.001, 0.02)):
        c = c0 - 2 * step_c
        while c <= c0 + 2 * step_c + 1e-12:
            d = d0 - 2 * step_d
            while d <= d0 + 2 * step_d + 1e-12:
                e = mae(c, d)
                if e < best[0]:
                    best = (e, c, d)
                d += step_d
            c += step_c
        e0, c0, d0 = best
    e, c, d = best
    return {"fitted": True, "c": round(c, 4), "d": round(d, 2),
            "mae": round(e, 2), "n": len(usable)}


def assess_score(records, params=None):
    """Güven raporu. Toplam gol vermek için yeterli maç + düşük hata gerekir."""
    params = params if params is not None else load_params()
    n = len([r for r in records
             if total_goals(r) is not None and r.get("scoring_index") is not None])
    mae = params.get("mae")
    fitted = bool(params.get("fitted"))
    if not fitted or mae is None:
        return {"level": "zayif", "n": n, "mae": None, "give_total": False,
                "reason": "skor modeli eğitilmedi (yeterli maç verisi yok)"}
    if n >= MIN_TRUST_STRONG and mae <= MAE_STRONG:
        level = "guclu"
    elif n >= MIN_FIT_MATCHES and mae <= MAE_MID:
        level = "orta"
    else:
        level = "zayif"
    return {
        "level": level, "n": n, "mae": round(mae, 2),
        "give_total": level in ("guclu", "orta"),
        "reason": "%d maç, ortalama sapma %.1f gol" % (n, mae),
    }


def forecast_score(planets, records=None, params=None):
    """Tek harita için toplam gol tahmini. Güven zayifsa SAYI DÖNMEZ.

    Kesin skor satırı (örn 3-1) bu modelden ÇIKMAZ; yalnız toplam gol ve
    alt/üst 2.5 eğilimi verilir."""
    from engine.sport_calibration import SportCalibration
    records = records if records is not None else SportCalibration().records
    params = params if params is not None else load_params()
    trust = assess_score(records, params)
    base = {
        "trust_level": trust["level"],
        "trust_reason": trust["reason"],
        "trust_mae": trust["mae"],
        "trust_n": trust["n"],
        "give_total": trust["give_total"],
    }
    if not trust["give_total"] or not planets:
        base["total_goals"] = None
        base["over_under"] = None
        base["text"] = ("Skor/toplam gol için kalibrasyon yetersiz — sayı "
                        "verilmiyor (uydurma yerine susmayı seç).")
        return base
    idx = scoring_index(planets)
    total = _clamp(params["c"] * idx + params["d"])
    base["scoring_index"] = idx
    base["total_goals"] = total
    base["over_under"] = "üst 2.5" if total >= 3 else "alt 2.5"
    base["text"] = "Toplam ~%d gol (alt/üst eğilim: %s)" % (total, base["over_under"])
    return base


def load_params(filename=None):
    path = filename or SCORE_PARAMS_FILE
    if not os.path.exists(path):
        return {"fitted": False, "c": None, "d": None, "mae": None}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"fitted": False, "c": None, "d": None, "mae": None}


def save_params(params, filename=None):
    path = filename or SCORE_PARAMS_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
