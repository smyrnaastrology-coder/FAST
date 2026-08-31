# -*- coding: utf-8 -*-
"""LOUIS/LILLY KONUM MOTORU — kayıp eşya/kişi yön, yükseklik ve mesafe katmanları.

Kaynak: Anthony Louis, "Horary Astrology Plain & Simple" (Bölüm 12: Finding Lost Items;
Table 16-19) + Appleby "Horary Astrology" Bölüm 9/15.

Bu modül mevcut horary_distance motoruna EK bir klasik-tici katmandır:
  - Table 16: Burç -> Yön (8 yel, azimut derece cinsinden)
  - Table 17: Ev -> Yön (16 yel'e yakın, azimut derece cinsinden)
  - Lilly'nin 8 göstergesi -> çoğunluk testiyle YÖN + belirsizlik
  - Element -> yer yüksekliği ; Modalite -> yer yüksekliği
  - Appleby aynı-çeyrek mesafe bandı (soran-sorulan açısal farkına göre)
"""

# ---------------- Table 16: BURÇ -> YÖN (Louis, Appleby ile birebir uyumlu) ----------------
# 0=K, 45=KD, 90=D, 135=GD, 180=G, 225=GB, 270=B, 315=KB
SIGN_DIRECTION = {
    "Koç": 90,        # East
    "Boğa": 135,      # South by East
    "İkizler": 225,   # West by South
    "Yengeç": 0,      # North
    "Aslan": 45,      # East by North
    "Başak": 225,     # South by West
    "Terazi": 270,    # West
    "Akrep": 45,      # North by East
    "Yay": 135,       # East by South
    "Oğlak": 180,     # South
    "Kova": 315,      # West by North
    "Balık": 315,     # North by West
}
SIGN_DIRECTION_EN = {
    "Aries": 90, "Taurus": 135, "Gemini": 225, "Cancer": 0,
    "Leo": 45, "Virgo": 225, "Libra": 270, "Scorpio": 45,
    "Sagittarius": 135, "Capricorn": 180, "Aquarius": 315, "Pisces": 315,
}

# ---------------- Table 17: EV -> YÖN (Louis) ----------------
# 16-yel kompası: 0=K, 22.5=KKD, 45=KD, 67.5=DKD, 90=D, 112.5=DGD, 135=GD, ...
HOUSE_DIRECTION_LOUIS = {
    1: 90.0,       # East
    2: 67.5,       # East Northeast
    3: 22.5,       # North Northeast
    4: 0.0,        # North
    5: 337.5,      # North Northwest
    6: 292.5,      # West Northwest
    7: 270.0,      # West
    8: 225.0,      # Southwest
    9: 202.5,      # South Southwest
    10: 180.0,     # South
    11: 135.0,     # Southeast
    12: 112.5,     # East Southeast
}
HOUSE_DIRECTION_LOUIS_8 = {
    1: 90, 2: 67.5, 3: 22.5, 4: 0, 5: 337.5, 6: 292.5,
    7: 270, 8: 225, 9: 202.5, 10: 180, 11: 135, 12: 112.5,
}

_DIRECTIONS16 = ["K", "KKD", "KD", "DKD", "D", "DGD", "GD", "GGD", "G", "GGB", "GB", "BGB", "B", "BKB", "KB", "KKB"]
_DIRECTION_LABEL = {
    "K": "Kuzey", "KKD": "Kuzey-Kuzeydoğu", "KD": "Kuzeydoğu", "DKD": "Doğu-Kuzeydoğu",
    "D": "Doğu", "DGD": "Doğu-Güneydoğu", "GD": "Güneydoğu", "GGD": "Güney-Güneydoğu",
    "G": "Güney", "GGB": "Güney-Güneybatı", "GB": "Güneybatı", "BGB": "Batı-Güneybatı",
    "B": "Batı", "BKB": "Batı-Kuzeybatı", "KB": "Kuzeybatı", "KKB": "Kuzey-Kuzeybatı",
}


def angle_to_dir(angle):
    idx = int((angle % 360 + 11.25) / 22.5) % 16
    return _DIRECTIONS16[idx]


def angle_to_dir_label(angle):
    return _DIRECTION_LABEL[angle_to_dir(angle)]


def sign_direction(sign):
    """Burç -> azimut (Table 16). TR veya EN karışık girişe çalışır."""
    if sign in SIGN_DIRECTION:
        return SIGN_DIRECTION[sign]
    return SIGN_DIRECTION_EN.get(sign, None)


def house_direction(house):
    """Ev -> azimut (Table 17)."""
    return HOUSE_DIRECTION_LOUIS.get(house)


# ---------------- ELEMENT -> YER YÜKSEKLİĞİ (Louis Bölüm 12) ----------------
SIGN_ELEMENT = {
    "Koç": "ateş", "Aslan": "ateş", "Yay": "ateş",
    "İkizler": "hava", "Terazi": "hava", "Kova": "hava",
    "Yengeç": "su", "Akrep": "su", "Balık": "su",
    "Boğa": "toprak", "Başak": "toprak", "Oğlak": "toprak",
    "Aries": "ateş", "Leo": "ateş", "Sagittarius": "ateş",
    "Gemini": "hava", "Libra": "hava", "Aquarius": "hava",
    "Cancer": "su", "Scorpio": "su", "Pisces": "su",
    "Taurus": "toprak", "Virgo": "toprak", "Capricorn": "toprak",
}

ELEMENT_HEIGHT = {
    "ateş": {
        "height": "orta yükseklikte",
        "place": "sıcak yerde, duvara/şömineye/sobaya yakın, demir/çelik eşya yanında, oda ortası yüksekliği",
        "direction": 90,
    },
    "hava": {
        "height": "yüksek / üst kat",
        "place": "üst kat, çatı, yüksek raf, tavan yakını, pencere/veranda/teras, açık temiz hava yeri",
        "direction": 270,
    },
    "toprak": {
        "height": "alçak / zeminde",
        "place": "yere yakın, zemin, bodrum, kiler, bahçe, gömülü, ilk kat, taş/çimento/çamur duvar yanı",
        "direction": 180,
    },
    "su": {
        "height": "alçak / su seviyesi",
        "place": "suya yakın, lavabo/mutfak/banyo altı, boru/tesisat yanı, nemli alçak yer (Yengeç temiz su, Akrep kirli/oil, Balık durgun su)",
        "direction": 0,
    },
}


def element_of_sign(sign):
    return SIGN_ELEMENT.get(sign)


def element_height(sign):
    """Burç -> element -> yükseklik + yer tarifi (Louis)."""
    el = element_of_sign(sign)
    return ELEMENT_HEIGHT.get(el)


# ---------------- MODALİTE -> YER YÜKSEKLİĞİ (Louis) ----------------
SIGN_MODALITY = {
    "Koç": "öncü", "Yengeç": "öncü", "Terazi": "öncü", "Oğlak": "öncü",
    "İkizler": "değişken", "Başak": "değişken", "Yay": "değişken", "Balık": "değişken",
    "Boğa": "sabit", "Aslan": "sabit", "Akrep": "sabit", "Kova": "sabit",
    "Aries": "öncü", "Cancer": "öncü", "Libra": "öncü", "Capricorn": "öncü",
    "Gemini": "değişken", "Virgo": "değişken", "Sagittarius": "değişken", "Pisces": "değişken",
    "Taurus": "sabit", "Leo": "sabit", "Scorpio": "sabit", "Aquarius": "sabit",
}

MODALITY_HEIGHT = {
    "öncü": "yüksek yer (çatı, tavan, tepe), yeni inşaat; dışarıda tepe/taze kazılmış zemin",
    "sabit": "gizli/saklı, zemine yakın/alçak; dışarıda düz kaliteli arazi",
    "değişken": "ev içinde; dışarıda sulu yer, hendek, çukur",
}


def modality_of_sign(sign):
    return SIGN_MODALITY.get(sign)


def modality_height(sign_or_mod):
    """Burç veya modalite -> yer yüksekliği (Louis)."""
    mod = sign_or_mod if sign_or_mod in MODALITY_HEIGHT else modality_of_sign(sign_or_mod)
    if mod is None:
        return {"modality": None, "height": ""}
    return {"modality": mod, "height": MODALITY_HEIGHT[mod]}


# ---------------- LILLY'NİN 8 GÖSTERGESİ -> ÇOĞUNLUK YÖN TESTİ ----------------
# Table 19: Lilly'nin kayıp eşyada kullandığı 8 konum göstergesi:
#   1. Yükselen (Asc) burcu
#   2. Asc yönetici gezegeninin burcu
#   3. 4. ev cusp burcu
#   4. 4. ev yönetici gezegeninin burcu
#   5. Ay'ın burcu
#   6. 2. ev cusp burcu
#   7. 2. ev yönetici gezegeninin burcu
#   8. Fortuna (POF) burcu
LILLY_INDICATOR_NAMES = [
    "asc_sign", "asc_ruler_sign", "cusp4_sign", "ruler4_sign",
    "moon_sign", "cusp2_sign", "ruler2_sign", "pof_sign",
]


def lilly_eight_indicators(**signs):
    """Lilly'nin 8 göstergesinden çoğunluk yön testimoniesi.

    Her gösterge bir burç adı; ona karşılık yön azimutu (Table 16). En çok geçen
    'yel' (8 veya 16 parça) kazanır. Lilly 'çoğunluk témoignages' kuralı: eşitlik
    yoksa en çok tekrar eden yön baskındır.

    Döndürür:
      n, majority_azimut, majority_dir, counts, individuals, clear
    - clear=True ise tek bir yel açık çoğunluk; False ise dağınık/belirsiz.
    """
    names = LILLY_INDICATOR_NAMES
    rows = []
    for k in names:
        s = signs.get(k)
        az = sign_direction(s) if s else None
        rows.append({"key": k, "sign": s, "azimut": az})
    valid = [r for r in rows if r["azimut"] is not None]
    # 8 yel'e yuvarlayarak oy say (16 yel çok dağınık, klasikte 8 yel kullanılır)
    wind8 = {r["key"]: int((r["azimut"] + 22.5) // 45) % 8 for r in valid}
    counts = {}
    for w in wind8.values():
        counts[w] = counts.get(w, 0) + 1
    if not counts:
        return {"n": 0, "clear": False, "counts": {}, "individuals": rows, "majority_azimut": None}
    best = max(counts, key=lambda w: (counts[w], -w))
    total = len(valid)
    clear = counts[best] > total / 2
    best_az = best * 45
    return {
        "n": total,
        "clear": clear,
        "counts": {int(w): c for w, c in counts.items()},
        "individuals": rows,
        "majority_azimut": round(best_az, 1),
        "majority_dir": angle_to_dir(best_az),
        "majority_dir_label": angle_to_dir_label(best_az),
    }


# ---------------- APPLEBY AYNI-ÇEYREK MESAFE BANDI ----------------
# Bölüm 15: soran ile sorulanın göstergeleri arası toplam açısal fark
#   <=30°  -> evde / çok yakın
#   30-70° -> aynı mahalle/çevre
#   >70°   -> uzakta / çok uzak
def angular_quadrant_band(angular_deg):
    """Açısal fark derecesine göre mesafe bandı (Appleby)."""
    a = abs(angular_deg)
    if a <= 30:
        return {"band": "evde / çok yakın", "range_km": "oda-metre seviyesi"}
    if a <= 70:
        return {"band": "aynı çevrede / yakın", "range_km": "yüzlerce metre-sehir içi"}
    if a <= 150:
        return {"band": "uzakta", "range_km": "ülke içi / yüzlerce km"}
    return {"band": "çok uzakta", "range_km": "kıtalararası / binlerce km"}
