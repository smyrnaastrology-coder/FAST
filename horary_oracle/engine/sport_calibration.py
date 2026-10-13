# -*- coding: utf-8 -*-
"""SPOR GOL DAKİKASI KALİBRASYONU.

NEDEN VAR: horary_engine.sport_goal_minutes() bir "kullanıcı taktiği"dir:
1. gol = ASC derecesi, sonraki her gol = öncekinin üzerine sıradaki ev cusp'ının
derecesi eklenir. Bu formül HİÇ ölçülmemiştir; bir maçta 7 gol birden
öngörebiliyor. Ölçümsüz bir dakika rakamı göstermek ürünün güven ilkesine
aykırı. Bu modül o taktiği ÖLÇÜLEBİLİR hale getirir:

  - Her maç için taktik "derece işaretleri" (marks) üretir: ASC° ve kümülatif
    cusp toplamları. Bunlar DAKİKA değil, sadece artan derece sayılarıdır.
  - Gerçek gol dakikalarıyla bir doğrusal eşleme öğrenilir:
        dakika_k = a * mark_k + b
    (a, b) en küçük ortalama mutlak hatayı (MAE) veren değerlerdir.
  - Güven katmanı: yeterli maç VE düşük MAE yoksa DAKİKA VERİLMEZ. Bu, bir
    soru tipi için ölçüm olmadığında mesafe rakamı vermeyen location_trust ile
    aynı felsefedir.

Kayıt şeması (horary_sport_calibration.json, liste):
  {"_id", "match", "date", "kickoff_local", "lat", "lon",
   "cusps": [12 float], "goal_minutes": [int,...], "ts"}

Öğrenilen parametreler horary_sport_goal_params.json dosyasına yazılır.
"""
import json
import os
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(_HERE, "..", "horary_sport_calibration.json")
PARAMS_FILE = os.path.join(_HERE, "..", "horary_sport_goal_params.json")

MIN_FIT_MATCHES = 4          # altında hiç fit denenmez (ezber olur)
MIN_TRUST_STRONG = 6         # guclu icin en az mac
MAE_STRONG = 8.0             # dakika: bu ortalamanın altı "guclu"
MAE_MID = 20.0               # dakika: bu ortalamanın altı "orta"
MINUTE_MIN = 1               # gol 1. dakikadan önce olamaz
MINUTE_MAX = 95              # 90 + uzatma payı

# Öngörü için en fazla kaç gol dakikası gösterilsin (taktik 11 işaret üretir;
# bir futbol maçında 11 gol gerçekçi değil, kalibrasyondan medyan alınır).
DEFAULT_EXPECTED_GOALS = 2


def degree_marks(cusps):
    """Taktik çekirdeği: ASC° ve ardışık ev cusp derecelerinin kümülatif toplamı.
    Döner artan liste (dakika değil, derece işareti). 12 işaret."""
    if not cusps or len(cusps) < 12:
        return []
    marks = [cusps[0] % 30]
    cur = marks[0]
    for i in range(1, 12):
        cur += cusps[i] % 30
        marks.append(cur)
    return marks


def _predict_marks(marks, a, b):
    """marks -> clamp edilmiş dakika listesi."""
    out = []
    for m in marks:
        minute = a * m + b
        minute = max(MINUTE_MIN, min(MINUTE_MAX, minute))
        out.append(round(minute, 1))
    return out


def fit_goal_params(records, min_matches=MIN_FIT_MATCHES):
    """(a, b) öğren: dakika = a*mark + b. Her maçta i. öngörü i. gerçek golle
    eşleştirilir (taktik artan üretir). MAE'yi en küçükleyen (a, b) grid aramayla
    bulunur, sonra inceltilir. Döner: {fitted, a, b, mae, n, reason?}."""
    usable = []
    for r in records:
        marks = r.get("marks") or degree_marks(r.get("cusps") or [])
        goals = [float(x) for x in (r.get("goal_minutes") or [])]
        if len(marks) >= 2 and goals:
            usable.append((marks, sorted(goals)))
    if len(usable) < min_matches:
        return {"fitted": False, "a": None, "b": None, "mae": None,
                "n": len(usable), "reason": f"en az {min_matches} maç gerek"}

    def mae(a, b):
        errs = []
        for marks, goals in usable:
            preds = _predict_marks(marks, a, b)
            # i. öngörü i. gerçeğe: ilk min(len) golü karşılaştır
            for i in range(min(len(preds), len(goals))):
                errs.append(abs(preds[i] - goals[i]))
        return sum(errs) / len(errs) if errs else None

    best = None
    # kaba tarama
    a = 0.05
    while a <= 3.0 + 1e-9:
        b = -20.0
        while b <= 40.0 + 1e-9:
            e = mae(a, b)
            if e is not None and (best is None or e < best[0]):
                best = (e, a, b)
            b += 2.0
        a += 0.05
    if best is None:
        return {"fitted": False, "a": None, "b": None, "mae": None,
                "n": len(usable), "reason": "değerlendirilebilir çift yok"}

    # inceltme (kaba taramanın iki adımı kadar komşulukta)
    e0, a0, b0 = best
    for step_a, step_b in ((0.01, 0.5), (0.002, 0.1)):
        a = max(0.0, a0 - 2 * step_a)
        while a <= a0 + 2 * step_a + 1e-12:
            b = b0 - 2 * step_b
            while b <= b0 + 2 * step_b + 1e-12:
                e = mae(a, b)
                if e is not None and e < best[0]:
                    best = (e, a, b)
                b += step_b
            a += step_a
        e0, a0, b0 = best

    e, a, b = best
    return {"fitted": True, "a": round(a, 4), "b": round(b, 2),
            "mae": round(e, 2), "n": len(usable)}


def assess(records, params=None):
    """Güven raporu. Dakika vermek için yeterli maç + düşük hata gerekir."""
    params = params if params is not None else load_params()
    n = len([r for r in records if r.get("goal_minutes")])
    mae = params.get("mae")
    fitted = bool(params.get("fitted"))
    if not fitted or mae is None:
        return {"level": "zayif", "n": n, "mae": None, "give_minutes": False,
                "reason": "gol dakikası modeli eğitilmedi (yeterli maç verisi yok)"}
    if n >= MIN_TRUST_STRONG and mae <= MAE_STRONG:
        level = "guclu"
    elif n >= 3 and mae <= MAE_MID:
        level = "orta"
    else:
        level = "zayif"
    return {
        "level": level, "n": n, "mae": round(mae, 1),
        "give_minutes": level in ("guclu", "orta"),
        "reason": f"{n} maç, ortalama sapma {mae:.0f} dakika",
    }


def _expected_goals(records):
    counts = [len(r.get("goal_minutes") or []) for r in records if r.get("goal_minutes")]
    if not counts:
        return DEFAULT_EXPECTED_GOALS
    counts.sort()
    return counts[len(counts) // 2] or DEFAULT_EXPECTED_GOALS


def forecast(cusps, records=None, params=None):
    """Tek harita için gol dakikası tahmini. Güven zayifsa dakika DÖNMEZ."""
    records = records if records is not None else SportCalibration().records
    params = params if params is not None else load_params()
    trust = assess(records, params)
    marks = degree_marks(cusps)
    base = {
        "trust_level": trust["level"],
        "trust_reason": trust["reason"],
        "trust_mae": trust["mae"],
        "trust_n": trust["n"],
        "give_minutes": trust["give_minutes"],
    }
    if not trust["give_minutes"] or not marks:
        base["minutes"] = None
        base["text"] = ("Gol dakikası için kalibrasyon yetersiz — dakika tahmini "
                        "verilmiyor (uydurma yerine susmayı seç).")
        return base
    n_goals = min(_expected_goals(records), len(marks))
    preds = _predict_marks(marks, params["a"], params["b"])[:n_goals]
    preds = sorted(set(preds))
    base["minutes"] = preds
    base["text"] = f"~{n_goals} gol civarı; tahmini dakikalar: " + ", ".join(f"{m:.0f}'" for m in preds)
    base["expected_goals"] = n_goals
    return base


class SportCalibration:
    def __init__(self, filename=None):
        self.filename = filename or STORE
        self.records = []

    def add_record(self, **kw):
        rec = dict(kw)
        # cusps verilirse marks türet (fit hızı + tutarlılık için sakla)
        if rec.get("cusps") and not rec.get("marks"):
            rec["marks"] = degree_marks(rec["cusps"])
        rec["_id"] = (max([r.get("_id", 0) for r in self.records]) + 1) if self.records else 1
        rec.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
        self.records.append(rec)
        return rec

    def save(self, filename=None):
        with open(filename or self.filename, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def load(self, filename=None):
        path = filename or self.filename
        if not os.path.exists(path):
            self.records = []
            return
        with open(path, "r", encoding="utf-8") as f:
            self.records = json.load(f)


def load_params(filename=None):
    path = filename or PARAMS_FILE
    if not os.path.exists(path):
        return {"fitted": False, "a": None, "b": None, "mae": None}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"fitted": False, "a": None, "b": None, "mae": None}


def save_params(params, filename=None):
    path = filename or PARAMS_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
