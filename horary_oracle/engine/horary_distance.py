# -*- coding: utf-8 -*-
"""HORARY UZAKLIK & YÖN MOTORU (Deneb Kaitos ekolü, kalibrasyon destekli).

Modüler model:
  EV   -> temel azimut          (%60 ağırlık)
  BURÇ -> yön düzeltmesi        (%25 ağırlık)
  GEZEGEN -> küçük yön düzeltmesi (%15 ağırlık)
  Jüpiter(querent) <-> significator ekliptik farkı -> yöne ±15° açısal düzeltme

Mesafe:
  base = sqrt(angular_distance) * 100
  mesafe = base * ev_tipi_çarpanı * kalibrasyon_ölçeği
  Kalibrasyon: gerçek vakalardan (gerçek_km / base) oranı öğrenilir.

Gerçek konum (haversine/bearing) tahmine KARIŞTIRILMAZ; sadece kalibrasyonda kullanılır.
"""
import json
import math
import os

_DEFAULT_CALIB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "horary_calibration.json")


class HoraryDistanceEngine:
    # Azimut: 0=K, 45=KD, 90=D, 135=GD, 180=G, 225=GB, 270=B, 315=KB
    HOUSE_DIRECTION = {
        1: 90, 2: 135, 3: 45, 4: 0, 5: 315, 6: 225,
        7: 270, 8: 315, 9: 45, 10: 180, 11: 45, 12: 315,
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
    DISTANCE_MULTIPLIER = {"angular": 0.75, "succedent": 1.00, "cadent": 1.35}
    DIRECTIONS16 = ["K", "KKD", "KD", "DKD", "D", "DGD", "GD", "GGD", "G", "GGB", "GB", "BGB", "B", "BKB", "KB", "KKB"]
    DIRECTION_LABEL = {
        "K": "Kuzey", "KKD": "Kuzey-Kuzeydoğu", "KD": "Kuzeydoğu", "DKD": "Doğu-Kuzeydoğu",
        "D": "Doğu", "DGD": "Doğu-Güneydoğu", "GD": "Güneydoğu", "GGD": "Güney-Güneydoğu",
        "G": "Güney", "GGB": "Güney-Güneybatı", "GB": "Güneybatı", "BGB": "Batı-Güneybatı",
        "B": "Batı", "BKB": "Batı-Kuzeybatı", "KB": "Kuzeybatı", "KKB": "Kuzey-Kuzeybatı",
    }

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

    def calculate_direction(self, house, sign, planet, planet_longitude=None, querent_longitude=None):
        direction = (
            self.house_direction(house)
            + self.sign_correction(sign) * 0.25
            + self.planet_correction(planet) * 0.15
        )
        if planet_longitude is not None and querent_longitude is not None:
            angular = self.angular_distance(planet_longitude, querent_longitude)
            direction += ((angular - 90) / 90) * 15
        direction = self.normalize_angle(direction)
        return {
            "azimut": round(direction, 2),
            "yon": self.angle_to_direction(direction),
            "yon_label": self.DIRECTION_LABEL[self.angle_to_direction(direction)],
        }

    def estimate_distance(self, angular_distance_value, house):
        house_type = self.HOUSE_TYPE.get(house, "succedent")
        multiplier = self.DISTANCE_MULTIPLIER[house_type]
        base_distance = math.sqrt(max(angular_distance_value, 0)) * 100
        return {"mesafe_km": round(base_distance * multiplier), "ev_tipi": house_type, "base_km": round(base_distance)}

    def analyze(self, house, sign, planet, friend_longitude, querent_longitude):
        angular = self.angular_distance(friend_longitude, querent_longitude)
        direction = self.calculate_direction(house, sign, planet, friend_longitude, querent_longitude)
        distance = self.estimate_distance(angular, house)
        return {
            "house": house,
            "significator": planet,
            "sign": sign,
            "angular": round(angular, 2),
            "azimut": direction["azimut"],
            "yon": direction["yon"],
            "yon_label": direction["yon_label"],
            "mesafe_km": distance["mesafe_km"],
            "base_km": distance["base_km"],
            "ev_tipi": distance["ev_tipi"],
        }


class HoraryCalibration:
    def __init__(self, filename=None):
        self.filename = filename or _DEFAULT_CALIB_FILE
        self.records = []

    def add_record(self, angular_distance, house_type, real_distance_km):
        self.records.append({"angular_distance": angular_distance, "house_type": house_type, "real_distance": real_distance_km})

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

    def scale_for(self, house_type):
        # öğrenilen oran: gerçek_km / (sqrt(angular)*multiplier)
        preds = []
        for r in self.records:
            if r.get("house_type") == house_type:
                mult = HoraryDistanceEngine.DISTANCE_MULTIPLIER.get(house_type, 1.0)
                base = math.sqrt(max(r["angular_distance"], 1)) * 100 * mult
                if base > 0:
                    preds.append(r["real_distance"] / base)
        return (sum(preds) / len(preds)) if preds else 1.0

    def global_scale(self):
        preds = []
        for r in self.records:
            mult = HoraryDistanceEngine.DISTANCE_MULTIPLIER.get(r.get("house_type"), 1.0)
            base = math.sqrt(max(r["angular_distance"], 1)) * 100 * mult
            if base > 0:
                preds.append(r["real_distance"] / base)
        return (sum(preds) / len(preds)) if preds else 1.0

    def apply(self, geo_result):
        """geo_result (HoraryDistanceEngine.analyze çıktısı) üzerine kalibrasyon + bant + kategori ekler."""
        ht = geo_result.get("ev_tipi", "succedent")
        scale = self.scale_for(ht)
        if scale == 1.0:
            scale = self.global_scale()
        km = geo_result["mesafe_km"] * scale
        lo = max(5, int(round(km * 0.8 / 50) * 50))
        hi = max(lo + 50, int(round(km * 1.25 / 50) * 50))
        cat = {"angular": "yakın (kısa mesafe)", "succedent": "orta", "cadent": "uzak"}.get(ht, "orta")
        confidence = 0.68 + min(0.12, 0.04 * len(self.records))
        geo_result["mesafe_kalibre_km"] = round(km)
        geo_result["band"] = f"~{lo}–{hi}"
        geo_result["category"] = cat
        geo_result["confidence"] = round(confidence, 2)
        geo_result["calibration_scale"] = round(scale, 3)
        return geo_result

    def average_error_pct(self):
        if not self.records:
            return None
        errs = []
        for r in self.records:
            mult = HoraryDistanceEngine.DISTANCE_MULTIPLIER.get(r.get("house_type"), 1.0)
            base = math.sqrt(max(r["angular_distance"], 1)) * 100 * mult
            scale = self.scale_for(r.get("house_type"))
            if base > 0:
                pred = base * scale
                errs.append(abs(pred - r["real_distance"]) / r["real_distance"] * 100)
        return round(sum(errs) / len(errs), 1) if errs else None


# ---------------- GERÇEK COĞRAFİ HESAP (sadece kalibrasyon için) ----------------
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


CITY_COORDINATES = {
    "İzmir": (38.4237, 27.1428), "Kırıkkale": (39.8468, 33.5153), "Ankara": (39.9334, 32.8597),
    "İstanbul": (41.0082, 28.9784), "Aydın": (37.8560, 27.8416), "Manisa": (38.6191, 27.4289),
    "Bursa": (40.1950, 29.0600), "Antalya": (36.8969, 30.7133), "Konya": (37.8746, 32.4932),
    "Tokat": (40.3167, 36.5500),
}