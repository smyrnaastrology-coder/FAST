# -*- coding: utf-8 -*-
"""HORARY UZAKLIK & YÖN MOTORU (Deneb Kaitos ekolü, öğrenen kalibrasyon).

Katmanlar:
  1. Kişiyi belirle        -> QUESTION_HOUSES / derived_houses (horary_questions.py)
  2. Significator          -> ev yöneticisi (klasik)
  3. YÖN motoru            -> ev + burç + gezegen  (başlangıç 0.50/0.30/0.20, veriden fit)
  4. MESAFE motoru         -> açısal fark × ev-katsayı × gezegen gücü × kalibrasyon
  5. Kalibrasyon           -> gerçek vakalardan ölçek; tip bazlı; hata istatistiği

PRENSIP: astrolojik formül önceden doğru KABUL EDILMEZ; gerçek vakalarla test
edilir ve katsayılar (ağırlıklar + ölçek) veriden öğrenilir. Gerçek konum,
tahmin oluşturulurken KULLANILMAZ (data-leak yasak); sadece doğrulama/kalibrasyon.
"""
import json
import math
import os
from datetime import datetime

_DEFAULT_CALIB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "horary_calibration.json")
_DEFAULT_WEIGHTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "horary_weights.json")
_DEFAULT_BIAS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "horary_bias.json")

DEFAULT_WEIGHTS = {"house": 0.50, "sign": 0.30, "planet": 0.20}
MIN_FIT_RECORDS = 4
# Yön fit'ine girmek için minimum gerçek mesafe (oda/ev içi kayıtlarda yön ölçülemez)
MIN_FIT_DIRECTION_KM = 1.0

# Mentör ölçek katmanları (km / (Δθ·M birimi)) — sabit tek k yerine MERDİVEN.
# Aynı horary haritası (ör. doktor) 12 km (şehir) VEYA 7890 km (kıtalararası) olabilir;
# doğru katmanı kalibrasyon kayıtları / kullanıcı geribildirimi seçer.
DEFAULT_SCALE_TIERS = {
    "oda içi": 0.0002,      # Eş örneği: 10.05 Δθ · 0.0002 ≈ 2 m
    "şehir içi": 2.0,       # Aslı örneği: 6 Δθ · 2 ≈ 12 km
    "ülke içi": 100.0,      # Yasin örneği: 5.73 Δθ · 100 ≈ 573 km
    "kıtalararası": 1300.0, # Şanghay örneği: 6 Δθ · 1300 ≈ 7800 km
}


class HoraryDistanceEngine:
    # Azimut: 0=K, 45=KD, 90=D, 135=GD, 180=G, 225=GB, 270=B, 315=KB
    HOUSE_DIRECTION = {
        1: 90, 2: 135, 3: 135, 4: 0, 5: 22.5, 6: 45,
        7: 270, 8: 292.5, 9: 315, 10: 180, 11: 202.5, 12: 225,
    }
    SIGN_DIRECTION_CORRECTION = {
        "Koç": 0, "Boğa": 10, "İkizler": 15, "Yengeç": -10, "Aslan": -5, "Başak": 5,
        "Terazi": 20, "Akrep": -15, "Yay": 0, "Oğlak": -10, "Kova": 10, "Balık": -15,
    }
    SIGN_DIRECTION_CORRECTION_EN = {
        "Aries": 0, "Taurus": 10, "Gemini": 15, "Cancer": -10, "Leo": -5, "Virgo": 5,
        "Libra": 20, "Scorpio": -15, "Sagittarius": 0, "Capricorn": -10, "Aquarius": 10, "Pisces": -15,
    }
    PLANET_DIRECTION_CORRECTION = {
        "Sun": 0, "Moon": 5, "Mercury": 10, "Venus": 15, "Mars": -10,
        "Jupiter": 5, "Saturn": -5, "Uranus": 10, "Neptune": -10, "Pluto": -5,
    }
    HOUSE_TYPE = {1: "angular", 2: "succedent", 3: "cadent", 4: "angular", 5: "succedent",
                  6: "cadent", 7: "angular", 8: "succedent", 9: "cadent", 10: "angular",
                  11: "succedent", 12: "cadent"}
    # Mentör formülü D = Δθ · M · k  (M: burcun modalite çarpanı, k: öğrenilen ölçek)
    MODALITY_MULT = {"cardinal": 1.0, "mutable": 10.0, "fixed": 100.0}
    DIRECTIONS16 = ["K", "KKD", "KD", "DKD", "D", "DGD", "GD", "GGD", "G", "GGB", "GB", "BGB", "B", "BKB", "KB", "KKB"]
    DIRECTION_LABEL = {
        "K": "Kuzey", "KKD": "Kuzey-Kuzeydoğu", "KD": "Kuzeydoğu", "DKD": "Doğu-Kuzeydoğu",
        "D": "Doğu", "DGD": "Doğu-Güneydoğu", "GD": "Güneydoğu", "GGD": "Güney-Güneydoğu",
        "G": "Güney", "GGB": "Güney-Güneybatı", "GB": "Güneybatı", "BGB": "Batı-Güneybatı",
        "B": "Batı", "BKB": "Batı-Kuzeybatı", "KB": "Kuzeybatı", "KKB": "Kuzey-Kuzeybatı",
    }

    def __init__(self, weights=None):
        self.weights = dict(DEFAULT_WEIGHTS)
        if weights:
            self.set_weights(weights)

    def set_weights(self, weights):
        w = dict(DEFAULT_WEIGHTS)
        w.update({k: max(0.0, min(1.0, float(v))) for k, v in (weights or {}).items() if k in DEFAULT_WEIGHTS})
        self.weights = w

    @staticmethod
    def normalize_angle(angle):
        return angle % 360

    @staticmethod
    def angular_distance(deg1, deg2):
        diff = abs(deg1 - deg2)
        if diff > 180:
            diff = 360 - diff
        return diff

    @staticmethod
    def angle_to_direction(angle):
        index = int((angle + 11.25) / 22.5) % 16
        return HoraryDistanceEngine.DIRECTIONS16[index]

    def house_direction(self, house):
        return self.HOUSE_DIRECTION.get(house, 0)

    def sign_correction(self, sign):
        if sign in self.SIGN_DIRECTION_CORRECTION:
            return self.SIGN_DIRECTION_CORRECTION[sign]
        return self.SIGN_DIRECTION_CORRECTION_EN.get(sign, 0)

    def planet_correction(self, planet):
        return self.PLANET_DIRECTION_CORRECTION.get(planet, 0)

    def calculate_direction(self, house, sign, planet, planet_longitude=None, querent_longitude=None, return_components=False):
        h = self.house_direction(house)
        s = self.sign_correction(sign)
        p = self.planet_correction(planet)
        ang = None
        if planet_longitude is not None and querent_longitude is not None:
            ang = self.angular_distance(planet_longitude, querent_longitude)
        ang_adj = ((ang - 90) / 90) * 15 if ang is not None else 0.0
        w = self.weights
        direction = w["house"] * h + w["sign"] * s + w["planet"] * p + ang_adj
        direction = self.normalize_angle(direction)
        res = {
            "azimut": round(direction, 2),
            "yon": self.angle_to_direction(direction),
            "yon_label": self.DIRECTION_LABEL[self.angle_to_direction(direction)],
        }
        if return_components:
            res["components"] = {"house": h, "sign_corr": s, "planet_corr": p, "ang_adj": round(ang_adj, 2), "angular": ang}
        return res

    MODALITY_OF_SIGN = {
        "Koç": "cardinal", "Boğa": "fixed", "İkizler": "mutable", "Yengeç": "cardinal",
        "Aslan": "fixed", "Başak": "mutable", "Terazi": "cardinal", "Akrep": "fixed",
        "Yay": "mutable", "Oğlak": "cardinal", "Kova": "fixed", "Balık": "mutable",
        "Aries": "cardinal", "Taurus": "fixed", "Gemini": "mutable", "Cancer": "cardinal",
        "Leo": "fixed", "Virgo": "mutable", "Libra": "cardinal", "Scorpio": "fixed",
        "Sagittarius": "mutable", "Capricorn": "cardinal", "Aquarius": "fixed", "Pisces": "mutable",
    }

    def estimate_distance(self, orb_deg, house, condition=1.0, sign_querent=None):
        """Mentör formülü: D_temel = Δθ · M · condition  (k yalnızca apply()'de kalibrasyon ölçeği).
        Δθ (orb) = gösterge derecelerinin BURÇ-İÇİ farkı (ör. 4°03' ile 9°47' -> 5.73°),
        M  = SORAN göstergesinin burcunun modalitesi: öncü(cardinal)=1 / değişken(mutable)=10 / sabit(fixed)=100.
        """
        house_type = self.HOUSE_TYPE.get(house, "succedent")
        modality = self.MODALITY_OF_SIGN.get(sign_querent, "cardinal")
        mult = self.MODALITY_MULT[modality]
        base_distance = max(orb_deg, 0.001) * mult * condition
        return {
            "mesafe_km": round(base_distance),
            "base_exact": round(base_distance, 4),
            "ev_tipi": house_type,
            "base_km": round(base_distance),
            "condition": round(condition, 3),
            "modality": modality,
            "modality_multiplier": mult,
            "formula": f"D = Δθ·M·k = {orb_deg:.2f}° · {mult} · kalibrasyon_olcegi",
        }

    def analyze(self, house, sign, planet, friend_longitude, querent_longitude, condition=1.0, return_components=False, sign_querent=None):
        angular = self.angular_distance(friend_longitude, querent_longitude)
        # mesafe için burç-içi orb: |gösterge derecesi%30 - soran derecesi%30|  (mentör yöntemi)
        orb = abs((friend_longitude % 30) - (querent_longitude % 30))
        direction = self.calculate_direction(house, sign, planet, friend_longitude, querent_longitude, return_components=return_components)
        distance = self.estimate_distance(orb, house, condition, sign_querent)
        res = {
            "house": house,
            "significator": planet,
            "sign": sign,
            "angular": round(angular, 2),
            "orb_deg": round(orb, 2),
            "azimut": direction["azimut"],
            "yon": direction["yon"],
            "yon_label": direction["yon_label"],
            "mesafe_km": distance["mesafe_km"],
            "base_km": distance["base_km"],
            "base_exact": distance["base_exact"],
            "condition": distance["condition"],
            "ev_tipi": distance["ev_tipi"],
            "modality": distance["modality"],
            "modality_multiplier": distance["modality_multiplier"],
            "formula": distance["formula"],
        }
        if return_components:
            res["components"] = direction["components"]
        return res

    # PDF madde B: ÇOKLU gösterge ağırlıklı mesafe skoru.
    # Tek gösterge Δθ'si yerine N gösterge (soran, sorulan, Ay, 4.ev yöneticisi,
    # POF...) her biri kendi burç-içi orb'u ile D_i = Δθ_i·M_i·cond_i üretir;
    # nihai base = ağırlıklı ortalama. Yön her zamanki ev+burç+gezegen (birincil
    # gösterge) korunur. Kalibrasyon geriye tam uyumlu: efektif Δθ̂ / M̂ / ĉ öyle
    # üretilir ki base = Δθ̂·M̂·ĉ -> _base_value() ve apply() hiç değişmeden çalışır.
    DEFAULT_MULTI_INDICATORS = {
        "quesited": 1.6,   # sorulanın göstergesi (en güçlü ağırlık)
        "moon": 1.0,       # Ay - soranın doğal ortak göstergesi (Lilly)
        "ruler4": 0.6,     # 4. ev yöneticisi - yerin/konumun yöneticisi
        "querent": 0.4,    # soran (ASC yöneticisi)
        "pof": 0.3,        # Part of Fortune
        "significator": 1.0,  # takma/fallback (Merkür, Venüs...) etiketi
    }

    def analyze_multi(self, querent_longitude, indicators, weights=None,
                      primary=None, house=1, sign=None, planet="Moon",
                      return_components=False):
        wi = dict(self.DEFAULT_MULTI_INDICATORS)
        if weights:
            wi.update({k: max(0.0, float(v)) for k, v in weights.items()})
        qdeg = (querent_longitude or 0.0) % 30
        ws, orbs, mms, dsi = [], [], [], []
        rows = []
        for ind in indicators:
            if ind.get("lon") is None:
                continue
            w = wi.get(ind.get("label"), 1.0)
            orb = abs((ind["lon"] % 30) - qdeg)
            sig = ind.get("sign")
            mod = self.MODALITY_OF_SIGN.get(sig, "cardinal")
            mm = self.MODALITY_MULT.get(mod, 1.0)
            cond = float(ind.get("condition", 1.0))
            d = max(orb, 0.001) * mm * cond
            ws.append(w); orbs.append(orb); mms.append(mm)
            dsi.append(d)
            rows.append({
                "label": ind.get("label"), "planet": ind.get("planet"),
                "sign": sig, "house": ind.get("house"),
                "orb_deg": round(orb, 3), "modality": mod,
                "modality_multiplier": mm, "condition": round(cond, 3),
                "D_km": round(d, 4), "weight": round(w, 3),
            })
        if not dsi:
            return self.analyze(house, sign or "Koç", planet, indicators[0]["lon"],
                                querent_longitude, condition=1.0,
                                return_components=return_components,
                                sign_querent=(indicators[0].get("sign") if indicators else None))
        W = sum(ws) or 1.0
        base = sum(w * d for w, d in zip(ws, dsi)) / W
        # efektif bileşenler: base = Δθ̂ · M̂ · ĉ
        dth = sum(w * o for w, o in zip(ws, orbs)) / W
        Mh = sum(w * m for w, m in zip(ws, mms)) / W
        denom = dth * Mh
        ch = (base / denom) if denom > 0 else 1.0
        # birincil gösterge (yön + ev tipi + angular için)
        pidx = 0
        if primary is not None:
            for i, r in enumerate(rows):
                if r.get("label") == primary:
                    pidx = i
                    break
        pri_lon = indicators[pidx]["lon"]
        angular = self.angular_distance(pri_lon, querent_longitude)
        direc = self.calculate_direction(house, sign, planet, pri_lon,
                                         querent_longitude, return_components=return_components)
        pri_house = indicators[pidx].get("house", house)
        res = {
            "house": house,
            "significator": planet,
            "sign": sign,
            "angular": round(angular, 2),
            "orb_deg": round(dth, 2),
            "azimut": direc["azimut"],
            "yon": direc["yon"],
            "yon_label": direc["yon_label"],
            "mesafe_km": round(base),
            "base_km": round(base),
            "base_exact": round(base, 4),
            "condition": round(ch, 3),
            "ev_tipi": self.HOUSE_TYPE.get(pri_house, "succedent"),
            "modality": rows[pidx].get("modality", "cardinal"),
            "modality_multiplier": round(Mh, 4),
            "formula": f"D = Σ(w_i·Δθ_i·M_i·k)/Σw_i ({len(rows)} gösterge, ağırlıklı ort)",
            "multi_indicator_n": len(rows),
            "multi_indicators": rows,
        }
        if return_components:
            res["components"] = direc["components"]
        return res


# ---------------- GEZEGEN GÜCÜ (F3/F4) ----------------
def condition_factor(significator, sign, lon=None, retro=False, sun_lon=None, sun_name_lon=None):
    """Asalet/retro/combust -> mesafe katsayısı. Önceden doğru değil, veriden öğrenilecek."""
    from core.ephemeris import DOMICILE_TRADITIONAL, EXALTATION, DETRIMENT, FALL
    f = 1.0
    labels = []
    if DOMICILE_TRADITIONAL.get(sign) == significator:
        f *= 1.00
        labels.append("domicile")
    elif EXALTATION.get(sign) == significator:
        f *= 1.05
        labels.append("exaltation")
    elif DETRIMENT.get(sign) == significator:
        f *= 0.90
        labels.append("detriment")
    elif FALL.get(sign) == significator:
        f *= 0.85
        labels.append("fall")
    else:
        labels.append("neutral")
    if retro and significator not in ("Sun", "Moon"):
        f *= 0.90
        labels.append("retrograde")
    if significator != "Sun" and lon is not None and sun_lon is not None:
        d = abs((lon - sun_lon + 180) % 360 - 180)
        if d < 8.5:
            f *= 0.85
            labels.append("combust")
    return {"factor": round(f, 3), "labels": labels}


# ---------------- KM KATEGORİ TABLOSU (iki aşama) ----------------
DISTANCE_BANDS_KM = [
    (0, 50, "çok yakın"),
    (50, 150, "yakın"),
    (150, 400, "orta"),
    (400, 750, "orta-uzak"),
    (750, 1500, "uzak"),
    (1500, math.inf, "çok uzak"),
]


def km_category(km):
    for lo, hi, label in DISTANCE_BANDS_KM:
        if lo <= km < hi:
            return {"altsınır": lo, "üstsınır": hi, "label": label}
    return {"altsınır": 1500, "üstsınır": math.inf, "label": "çok uzak"}


# ---------------- KALİBRASYON ----------------
class HoraryCalibration:
    def __init__(self, filename=None):
        self.filename = filename or _DEFAULT_CALIB_FILE
        self.records = []

    # kayıt şeması:
    # {"_id", "question_type", "origin","destination", "house", "significator","sign","degree",
    #  "querent_planet","querent_degree", "angular_difference", "components", "condition",
    #  "real_distance_km", "real_bearing", "ts"}
    def add_record(self, upsert=False, **kw):
        if upsert:
            for i, r in enumerate(self.records):
                same = (r.get("question_type") == kw.get("question_type")
                        and r.get("origin") == kw.get("origin")
                        and r.get("destination") == kw.get("destination"))
                if same:
                    rec = dict(kw)
                    rec["_id"] = r["_id"]
                    self.records[i] = rec
                    return rec
        rec = dict(kw)
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

    def _base_value(self, r):
        ang = float(r.get("angular_difference", 1))
        cond = float(r.get("condition", 1.0))
        mm = r.get("modality_multiplier")
        if not mm:
            mod = HoraryDistanceEngine.MODALITY_OF_SIGN.get(r.get("sign"), "cardinal")
            mm = HoraryDistanceEngine.MODALITY_MULT.get(mod, 1.0)
        base = max(ang, 0.001) * mm * cond
        return base if base > 0 else None

    def _base_preds(self, house_type=None):
        """(base_km, gerçek_km, kayıt) listesi — D_temel = Δθ · M · condition."""
        out = []
        for r in self.records:
            base = self._base_value(r)
            if base is not None:
                out.append((base, float(r["real_distance_km"]), r))
        return out

    def likely_tier(self, records=None):
        """Kalibrasyon kayıtlarından soru tipine en uygun ölçek katmanını seç.
        Her kayıtta k = gerçek/base; en yakın varsayılan katman çoğunlukla kazanır."""
        recs = records if records is not None else self.records
        votes = {}
        for r in recs:
            base = self._base_value(r)
            if not base:
                continue
            k = float(r["real_distance_km"]) / base
            tier = min(DEFAULT_SCALE_TIERS, key=lambda t: abs(math.log10(DEFAULT_SCALE_TIERS[t]) - math.log10(k)))
            votes[tier] = votes.get(tier, 0) + 1
        if not votes:
            return "şehir içi"
        return max(votes, key=votes.get)

    def direction_confidence(self, weights=None):
        """Yön modelinin gerçek isabet güveni: kalibrasyon kayıtlarındaki
        ortalama yön hatasına göre 'iyi'/'orta'/'düşük' etiketi."""
        w = weights if weights is not None else load_weights()
        usable = [r for r in self.records
                  if r.get("components") and r.get("real_bearing") is not None
                  and float(r.get("real_distance_km", 0)) >= MIN_FIT_DIRECTION_KM]
        if not usable:
            return {"label": "bilinmiyor", "mean_err_deg": None, "n": 0}
        errs = [_circular_diff(_direction_predict(r["components"], w), r["real_bearing"]) for r in usable]
        mean = sum(errs) / len(errs)
        if mean <= 22.5:
            label = "iyi"
        elif mean <= 45:
            label = "orta"
        else:
            label = "düşük"
        return {"label": label, "mean_err_deg": round(mean, 1), "n": len(usable)}

    # gerçek uzaklık (km) -> ölçek katmanı eşiği. Oda/şehir join'ini (ör.
    # coworker: İbrahim ~0m + Defne 2258km) ayrı katmanlara böler.
    _TIER_EDGES = (("oda içi", 0.2), ("şehir içi", 20.0), ("ülke içi", 1500.0))

    def _tier_of_real(self, real_km):
        for name, edge in self._TIER_EDGES:
            if real_km < edge:
                return name
        return "kıtalararası"

    def _scale_ladders(self, question_type=None):
        """Her uzaklık katmanı için ayrı k ölçeği: real/base medyanı (aykırı dayanıklı)."""
        groups = {name: [] for name in ("oda içi", "şehir içi", "ülke içi", "kıtalararası")}
        for base, real, r in self._base_preds():
            if question_type and r.get("question_type") != question_type:
                continue
            groups[self._tier_of_real(real)].append(real / base)
        ladders = {}
        for name, ks in groups.items():
            if ks:
                ks2 = sorted(ks)
                ladders[name] = ks2[len(ks2) // 2]
        return ladders

    def scale_for(self, house_type=None, question_type=None, tier=None):
        """k ölçeği: önce (istenirse) belirli katman, sonra uzaklık katmanı medyanı,
        sonra soru tipi bucket ortalaması, en son global / varsayılan katman."""
        ladders = self._scale_ladders(question_type)
        if tier and tier in ladders:
            return ladders[tier]
        if ladders:  # olası katmanların medyanı (collapse'u <-> uç dengesi)
            return sorted(ladders.values())[len(ladders) // 2]
        if question_type:
            bucket = [r for r in self._base_preds() if r[2].get("question_type") == question_type]
            if bucket:
                return sum(real / base for base, real, _ in bucket) / len(bucket)
        bucket = self._base_preds()
        if bucket:
            return sum(real / base for base, real, _ in bucket) / len(bucket)
        return DEFAULT_SCALE_TIERS[self.likely_tier()]

    def tier_ladder(self, base_exact):
        """Tüm ölçek katmanlarını döndür: aynı Δθ farklı ölçek anlamlarına gelebilir."""
        return {tier: round(base_exact * k, 4) for tier, k in DEFAULT_SCALE_TIERS.items()}

    def apply(self, geo_result, question_type=None, origin=(None, None)):
        ht = geo_result.get("ev_tipi", "succedent")
        base_exact = geo_result.get("base_exact", geo_result.get("base_km", geo_result["mesafe_km"]))
        ladders = self._scale_ladders(question_type)
        # hedef katman: ev tipi (angular->oda, succedent->şehir, cadent->ülke/kıta) öncelikli
        _tier_hint = {"angular": "oda içi", "succedent": "şehir içi", "cadent": "ülke içi"}.get(ht)
        if not (_tier_hint and _tier_hint in ladders):
            _tier_hint = self.likely_tier()
        scale = ladders.get(_tier_hint) if _tier_hint else self.scale_for(ht, question_type)
        if scale is None:
            scale = self.scale_for(ht, question_type)
        km = base_exact * scale
        cat_q = {"angular": "yakın (kısa mesafe)", "succedent": "orta", "cadent": "uzak"}.get(ht, "orta")
        cat_km = km_category(km)
        confidence = 0.68 + min(0.12, 0.04 * len(self.records))
        _dc = self.direction_confidence()
        geo_result["direction_confidence"] = _dc["label"]
        geo_result["direction_mean_err_deg"] = _dc["mean_err_deg"]
        geo_result["direction_n"] = _dc["n"]
        geo_result["mesafe_kalibre_km"] = round(km)
        # ölçek katmanı merdiveni: aynı yönde, 3 (4) farklı uzunluk okunun koordinatları
        _brg = geo_result.get("azimut", geo_result.get("bouy", 0.0))
        try:
            _brg = float(_brg)
        except Exception:
            _brg = 0.0
        _ladder_out = {}
        for _tname in ("oda içi", "şehir içi", "ülke içi", "kıtalararası"):
            _k = ladders.get(_tname)
            _tkm = round(base_exact * _k, 6) if _k is not None else None
            _dest = None
            if _tkm is not None and origin[0] is not None and origin[1] is not None:
                _dlat, _dlon = destination_point(origin[0], origin[1], _brg, _tkm)
                _dest = {"lat": round(_dlat, 5), "lon": round(_dlon, 5)}
            _ladder_out[_tname] = {"km": _tkm, "bearing": round(_brg, 1), "dest": _dest}
        geo_result["scale_ladder"] = _ladder_out
        geo_result["likely_tier"] = _tier_hint or self.likely_tier()
        geo_result["scale_ladder_km"] = {k: v["km"] for k, v in _ladder_out.items()}
        if km < 1:  # mikro ölçek (oda içi) — metreyi göster
            m = round(km * 1000)
            lo = max(0.5, round(m * 0.8 / 50) * 50)
            hi = max(lo + 50, round(m * 1.25 / 50) * 50)
            geo_result["band"] = f"~{int(lo)}–{int(hi)} m"
            geo_result["display"] = f"~{m} m (oda/ev içi seviyesi)"
            cat_q = "çok yakın (oda içi)"
        else:
            lo = max(5, int(round(km * 0.8 / 50) * 50))
            hi = max(lo + 50, int(round(km * 1.25 / 50) * 50))
            geo_result["band"] = f"~{lo}–{hi} km"
            geo_result["display"] = f"~{round(km)} km"
        geo_result["category"] = cat_q
        geo_result["km_category"] = cat_km["label"]
        geo_result["km_category_range"] = f"{cat_km['altsınır']}–{cat_km['üstsınır']} km"
        geo_result["confidence"] = round(confidence, 2)
        geo_result["calibration_scale"] = round(scale, 3)
        geo_result["calibration_n"] = len(self.records)
        apply_direction_bias(geo_result, question_type=question_type)
        if geo_result.get("formula") and "(k≈" not in geo_result.get("formula", ""):
            geo_result["formula"] = geo_result["formula"] + f"  (k≈{scale:.3f})"
        elif geo_result.get("formula"):
            geo_result["formula"] = next(
                (seg for seg in geo_result["formula"].split("  (") if not seg.startswith("k≈")),
                geo_result["formula"],
            ) + f"  (k≈{scale:.3f})"
        return geo_result

    def get_record(self, ident):
        for r in self.records:
            if r.get("_id") == ident:
                return r
        return None


# ---------------- AĞIRLIK ÖĞRENİMİ ----------------
def _circular_diff(a, b):
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


def _direction_predict(comp, weights):
    return (weights["house"] * comp["house"] + weights["sign"] * comp["sign_corr"]
            + weights["planet"] * comp["planet_corr"] + comp.get("ang_adj", 0)) % 360


def fit_direction_weights(records):
    """Veriden ev/burç/gezegen ağırlıklarını öğren (küçültme: ortalama dairesel hata).
    Kayıtlarda 'components' + 'real_bearing' gerekir; en az MIN_FIT_RECORDS vaka.
    Mikro-ölçek kayıtlar (gerçek mesafe <1 km: oda/oda içi) YÖN ölçümü yapamaz —
    yağın konumu bilinemeyeceği için fit'e dahil edilmez (eş 2m gibi).
    """
    usable = [r for r in records
              if r.get("components") and r.get("real_bearing") is not None
              and float(r.get("real_distance_km", 0)) >= MIN_FIT_DIRECTION_KM]
    if len(usable) < MIN_FIT_RECORDS:
        return {"weights": dict(DEFAULT_WEIGHTS), "n": len(usable), "fitted": False, "reason": f"en az {MIN_FIT_RECORDS} vaka gerek"}

    def mean_err(w1, w2):
        w = {"house": w1, "sign": w2, "planet": 1.0 - w1 - w2}
        errs = [_circular_diff(_direction_predict(r["components"], w), r["real_bearing"]) for r in usable]
        return sum(errs) / len(errs)

    best = None
    for step in (0.05, 0.01, 0.002):
        w1 = 0.0
        while w1 <= 1.0 + 1e-9:
            w2 = 0.0
            while w2 <= (1.0 - w1) + 1e-9:
                e = mean_err(w1, w2)
                if best is None or e < best[0]:
                    best = (e, w1, w2)
                w2 += step
            w1 += step
    e, w1, w2 = best
    w = {"house": round(w1, 3), "sign": round(w2, 3), "planet": round(1.0 - w1 - w2, 3)}
    return {"weights": w, "mean_err_deg": round(e, 1), "n": len(usable), "fitted": True}


def load_weights(filename=None):
    path = filename or _DEFAULT_WEIGHTS_FILE
    if not os.path.exists(path):
        return dict(DEFAULT_WEIGHTS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {k: float(v) for k, v in json.load(f).items() if k in DEFAULT_WEIGHTS}
    except Exception:
        return dict(DEFAULT_WEIGHTS)


def save_weights(weights, filename=None):
    path = filename or _DEFAULT_WEIGHTS_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump({k: round(v, 3) for k, v in weights.items()}, f, ensure_ascii=False, indent=2)


# ---------------- TİP BAZLI YÖN SAPMASI (BIAS) ----------------
def _circular_mean(deg_list):
    """Dairesel ortalama: 330° ve 30° -> 0° (360.cpp)."""
    if not deg_list:
        return None
    x = sum(math.cos(math.radians(d)) for d in deg_list) / len(deg_list)
    y = sum(math.sin(math.radians(d)) for d in deg_list) / len(deg_list)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def fit_direction_bias(records, min_records=MIN_FIT_RECORDS):
    """Tip bazlı sistematik yön sapmasını öğren: bias = dairesel_ort(gerçek - sembolik tahmin).

    Her soru tipi için: sembolik model (mevcut ağırlıklar) belirli yönlerde
    SİSTEMATİK kayıyor (ör. öğrenci sürekli KD söylüyor ama gerçek GD). Bu sapmayı
    tip bazında ortalayıp 'düzeltme' olarak saklarız. En az min_records vaka gerekir
    (tek kayıt 'ezber', genellenmez).
    """
    weights = load_weights()
    usable = [r for r in records
              if r.get("components") and r.get("real_bearing") is not None
              and float(r.get("real_distance_km", 0)) >= MIN_FIT_DIRECTION_KM]
    by_type = {}
    for r in usable:
        pred = _direction_predict(r["components"], weights)
        drift = (r["real_bearing"] - pred) % 360  # gerçek, sembolik tahminin ilerisinde mi?
        by_type.setdefault(r.get("question_type", "?"), []).append(drift)
    bias = {}
    for t, drifts in by_type.items():
        if len(drifts) >= min_records:
            bias[t] = {"bias_deg": round(_circular_mean(drifts), 2), "n": len(drifts)}
        else:
            bias[t] = {"bias_deg": None, "n": len(drifts), "yetersiz_veri": True}
    return {"bias": bias, "n": len(usable), "fitted": bool(bias)}


def load_direction_bias(filename=None):
    path = filename or _DEFAULT_BIAS_FILE
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_direction_bias(bias, filename=None):
    path = filename or _DEFAULT_BIAS_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bias, f, ensure_ascii=False, indent=2)


def apply_direction_bias(geo_result, question_type=None, bias_db=None):
    """Bias varsa azimut/yön etiketini düzelt. Dönen dict: düzeltilen geo_result."""
    if not question_type or not geo_result.get("azimut"):
        return geo_result
    db = bias_db if bias_db is not None else load_direction_bias()
    entry = db.get(question_type)
    if not entry:
        return geo_result
    if entry.get("bias_deg") is None:
        geo_result["direction_bias_n"] = entry.get("n", 0)
        geo_result["direction_bias_status"] = "yetersiz_veri"
        return geo_result
    new_az = (geo_result["azimut"] + entry["bias_deg"]) % 360
    geo_result["azimut"] = round(new_az, 2)
    geo_result["yon"] = HoraryDistanceEngine.angle_to_direction(new_az)
    geo_result["yon_label"] = HoraryDistanceEngine.DIRECTION_LABEL[geo_result["yon"]]
    geo_result["direction_bias_deg"] = entry["bias_deg"]
    geo_result["direction_bias_n"] = entry["n"]
    geo_result["direction_bias_status"] = "uygulandi"
    return geo_result


# ---------------- MODEL İSTATİSTİĞİ ----------------
def model_stats(records):
    """Yön (±22.5/±45) + mesafe (±50/100/200 km) doğruluğu, genel + tip bazlı."""
    weights = load_weights()

    def _stats(subset):
        if not subset:
            return None
        dir_errs = []
        km_errs = []
        for r in subset:
            if r.get("components") and r.get("real_bearing") is not None:
                pred_az = _direction_predict(r["components"], weights)
                dir_errs.append(_circular_diff(pred_az, r["real_bearing"]))
            if r.get("angular_difference") and r.get("real_distance_km") is not None:
                mm = r.get("modality_multiplier") or HoraryDistanceEngine.MODALITY_MULT.get(
                    HoraryDistanceEngine.MODALITY_OF_SIGN.get(r.get("sign"), "cardinal"), 1.0)
                base = max(float(r["angular_difference"]), 0.001) * mm * float(r.get("condition", 1.0))
                cal = HoraryCalibration()
                scale = cal.scale_for(None, r.get("question_type"))
                pred_km = base * scale
                km_errs.append(abs(pred_km - float(r["real_distance_km"])))
        out = {"n": len(subset)}
        if dir_errs:
            out["yon_err_ort"] = round(sum(dir_errs) / len(dir_errs), 1)
            out["yon_<=22.5"] = round(sum(1 for e in dir_errs if e <= 22.5) / len(dir_errs) * 100)
            out["yon_<=45"] = round(sum(1 for e in dir_errs if e <= 45) / len(dir_errs) * 100)
        if km_errs:
            out["km_err_ort"] = round(sum(km_errs) / len(km_errs), 1)
            out["km_<=50"] = round(sum(1 for e in km_errs if e <= 50) / len(km_errs) * 100)
            out["km_<=100"] = round(sum(1 for e in km_errs if e <= 100) / len(km_errs) * 100)
            out["km_<=200"] = round(sum(1 for e in km_errs if e <= 200) / len(km_errs) * 100)
        return out

    result = {"genel": _stats(records)}
    by_type = {}
    for r in records:
        by_type.setdefault(r.get("question_type", "?"), []).append(r)
    for t, sub in by_type.items():
        result[t] = _stats(sub)
    return result


# ---------------- DOĞRULAMA / VERIFICATION ----------------
def verify_prediction(predicted_azimut, predicted_km, origin_lat, origin_lon, real_lat, real_lon):
    """Gerçek konum (hint) TAHMİN ÜRETİMİNDE kullanılmaz; sadece karşılaştırma+kalibrasyon."""
    real_dm = round(geographic_distance(origin_lat, origin_lon, real_lat, real_lon), 1)
    real_bearing = round(geographic_bearing(origin_lat, origin_lon, real_lat, real_lon), 2)
    dir_err = _circular_diff(predicted_azimut, real_bearing)
    km_err = abs(predicted_km - real_dm) if predicted_km else None
    return {
        "real_distance_km": real_dm,
        "real_bearing": real_bearing,
        "direction_error_deg": round(dir_err, 1),
        "distance_error_km": round(km_err, 1) if km_err is not None else None,
        "direction_ok": dir_err <= 45,
        "band_ok": (km_err is not None and km_err <= predicted_km * 0.25) if predicted_km else None,
        "verdict_text": ("✅ Yön + mesafe uyumlu" if dir_err <= 45 and (km_err is not None and km_err <= predicted_km * 0.25)
                         else "⚠️ Kısmen uyumlu" if dir_err <= 90 else "❌ Uyuşmuyor"),
    }


# ---------------- GERÇEK COĞRAFİ HESAP (sadece doğrulama) ----------------
def geographic_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lat2, dlon = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def geographic_bearing(lat1, lon1, lat2, lon2):
    lat1, lat2, dlon = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def destination_point(lat, lon, bearing_deg, km):
    """İlerisini hesapla: origin + rota + uzaklık -> hedef koordinatı (3 ok / katman)."""
    R = 6371.0
    brg = math.radians(bearing_deg)
    lat1, lon1 = math.radians(lat), math.radians(lon)
    d = km / R
    lat2 = math.asin(math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(brg))
    lon2 = lon1 + math.atan2(math.sin(brg) * math.sin(d) * math.cos(lat1),
                             math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return (math.degrees(lat2), (math.degrees(lon2) + 540) % 360 - 180)


# PDF adım 7-8: Ay'ın aranan kişinin yöneticisine uygulayan/ayrılan açısı + retrogradlık.
# Uygulayan (applying) = Ay bu açıya yaklaşıyor (yakınlaşma/hareket); ayrılan (separating) = uzaklaşıyor.
_MAJOR_ASPECTS = (0, 60, 90, 120, 180)


def _closest_aspect(lon_a, lon_b, orbs=(0, 8, 6, 6, 8, 8)):
    """(açı, orb) — iki boylam arasındaki en yakın ana açı ve orb'u."""
    d = abs(lon_a - lon_b) % 360
    if d > 180:
        d = 360 - d
    m = min(_MAJOR_ASPECTS, key=lambda x: abs(x - d))
    return m, round(abs(m - d), 1)


def moon_movement(moon_lon, quesited_lon, moon_retro=False, quesited_retro=False,
                  aspect_orbs=(0, 8, 6, 6, 8, 8)):
    """Ay <-> sorulan gösterge arası katman: açı, uygulayan/ayrılan, retrogradlık.

    applying: Ay, göstergeye uygulayan ana açıya DOĞRU ilerliyor (yaklaşma/hareket).
    separating: Ay o açıdan UZAKLAŞIYOR (ayrılık/uzaklaşma). Retrograd, yön değiştirme
    /geri dönüş temasını güçlendirir (PDF).
    """
    asp, orb = _closest_aspect(float(moon_lon), float(quesited_lon))
    # Ay ileri (doğal) ise boylamı artar: açı küçülüyorsa uyguluyordur
    sep_natural = (quesited_lon - moon_lon) % 360
    if sep_natural > 180:
        sep_natural = 360 - sep_natural
    sense = 1.0 if not moon_retro else -1.0
    # Ay'ın hedefe (uygulanan açı noktasına) uzaklığı: hedef - Ay
    target = (moon_lon + asp * (1 if (quesited_lon - moon_lon) % 360 <= 180 else -1)) % 360
    dist_to_target = ((target - moon_lon) % 360) * sense
    applying = orb <= 8 and dist_to_target >= 0 and dist_to_target <= 4.0
    state = "uygulayan" if applying else ("ayrılan" if orb <= 8 else "dışında")
    retro = (moon_retro or quesited_retro)
    note = f"Ay {asp}° açısında (orb {orb}°) {'uyguluyor' if applying else 'ayrılıyor'}"
    if moon_retro:
        note += "; Ay retro"
    if quesited_retro:
        note += "; gösterge retro"
    return {"aspect": asp, "orb": orb, "state": state, "applying": applying,
            "retro": retro, "note": note}


CITY_COORDINATES = {
    "İzmir": (38.4237, 27.1428), "Kırıkkale": (39.8468, 33.5153), "Ankara": (39.9334, 32.8597),
    "İstanbul": (41.0082, 28.9784), "Aydın": (37.8560, 27.8416), "Manisa": (38.6191, 27.4289),
    "Bursa": (40.1950, 29.0600), "Antalya": (36.8969, 30.7133), "Konya": (37.8746, 32.4932),
    "Tokat": (40.3167, 36.5500), "Niksar": (40.5903, 36.9492), "Ayrancılar": (38.10, 27.25),
    "Samsun": (41.2867, 36.33), "Ereğli": (41.2417, 31.4256), "Katar": (25.3548, 51.1839), "Mersin": (36.8119, 34.6389), "Mekke": (21.3891, 39.8579), "Manavgat": (36.7870, 31.4431),
    "Şanghay": (31.2304, 121.4737), "Valencia": (39.4699, -0.3763), "Milano": (45.4642, 9.1900),
    "Halkapınar": (38.4237, 27.1428), "Özdere": (38.0560, 27.0980), "Tilburg": (51.5555, 5.0913),
    "Çerkezköy": (41.2860, 28.0120),
}