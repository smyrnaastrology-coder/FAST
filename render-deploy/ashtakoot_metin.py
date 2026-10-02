# -*- coding: utf-8 -*-
"""
Ashtakoot metin katmanı — dil yönlendirici.

Kullanım:
    from ashtakoot_metin import metinler, metin_getir, mod_yorumu, toplam_metni

`ashtakoot_metinleri.py` (TR) kaynak modüldür; `..._EN.py` ve `..._ES.py`
modülleri onun yapısını birebir izler. Bu modül dili seçer ve TR sürümü
çağrıldığında özyinelemeyi önlemek için yalnızca kendi TR sözlüğünü döndürür.
"""

from typing import Dict, Optional

import ashtakoot_metinleri as _tr
import ashtakoot_metinleri_EN as _en
import ashtakoot_metinleri_ES as _es

DILLER: Dict[str, dict] = {
    "tr": {"modul": _tr, "ad": "Türkçe", "sembol": "TR"},
    "en": {"modul": _en, "ad": "English", "sembol": "EN"},
    "es": {"modul": _es, "ad": "Español", "sembol": "ES"},
}


def dogrula(lang: str) -> bool:
    """Verilen dilin 8 koota için de metin dözdüğünü doğrular."""
    m = DILLER.get(lang, {}).get("modul")
    if not m:
        return False
    kok = m.KOOTA_METIN_TR if lang == "tr" else m.KOOTA_METIN
    return all(k in kok and "bantlar" in kok[k] for k in
               ("varna", "vashya", "tara", "yoni", "graha_maitri", "gana", "rasi", "nadi"))


def metinler(lang: str = "tr") -> dict:
    """Dilin tüm koota metin sözlüğünü döndürür; bilinmeyen dilde TR'a düşer."""
    m = DILLER.get(lang, {}).get("modul")
    if not m:
        return _tr.KOOTA_METIN_TR
    return m.KOOTA_METIN_TR if lang == "tr" else m.KOOTA_METIN


def metin_getir(koota: str, puan: int, azami: int, lang: str = "tr") -> dict:
    """Koota için puan bandına ait metni seçer ve döndürür."""
    m = DILLER.get(lang, {}).get("modul")
    if not m:
        m = _tr
    if lang == "tr":
        return _tr.metin_getir(koota, puan, azami)
    return m.metin_getir(koota, puan, azami)


def mod_yorumu(koota: str, mod: str, lang: str = "tr") -> str:
    m = DILLER.get(lang, {}).get("modul")
    if lang == "tr" or m is None:
        return _tr.mod_yorumu(koota, mod)
    return m.mod_yorumu(koota, mod)


def toplam_metni(seviye: str, lang: str = "tr") -> dict:
    m = DILLER.get(lang, {}).get("modul")
    if lang == "tr" or m is None:
        return _tr.toplam_metni(seviye)
    return m.toplam_metni(seviye)


def kendisi_notu(lang: str = "tr") -> dict:
    m = DILLER.get(lang, {}).get("modul")
    if lang == "tr" or m is None:
        return _tr.KENDISI_NOTU
    return getattr(m, "KENDISI_NOTU", _tr.KENDISI_NOTU)


def nadi_dosha_metin(lang: str = "tr") -> dict:
    """Nadi Dosha metin sözlüğü; bilinmeyen dilde TR'a düşer."""
    m = DILLER.get(lang, {}).get("modul")
    if lang == "tr" or m is None:
        return _tr.NADI_DOSHA_METIN
    return getattr(m, "NADI_DOSHA_METIN", _tr.NADI_DOSHA_METIN)


def bant_bul(puan: int, azami: int, lang: str = "tr") -> str:
    m = DILLER.get(lang, {}).get("modul")
    if lang == "tr" or m is None:
        return _tr.bant_bul(puan, azami)
    return m.bant_bul(puan, azami)


def dil_secenekleri() -> list:
    """Streamlit selectbox için (kod, etiket) listesi."""
    return [(k, v["ad"]) for k, v in DILLER.items()]


#: Motor tarafındaki alan adlarının (burç, lord, tanrı, yoni ...) dil başına
#: karşılığı. Koota yorumları zaten `..._EN/ES` modüllerinde tam metin olarak
#: bulunur; burada yalnızca profil/harita başlıkları çevrilir.
ETIKET: Dict[str, dict] = {
    "tr": {
        "burc": "Burç", "lord": "Lord", "tanri": "Tanrı", "yoni": "Yoni",
        "gana": "Gana", "varna": "Varna", "vashya": "Vashya", "nadi": "Nadi",
        "pada": "pada", "nakshatra": "Nakṣatra", "puan": "Puan",
        "seviye": "Seviye", "kendi": "kendi", "yoni_bos": "—",
        "dogum_saat": "Doğum Saati", "kisi": "Kişi", "ipucu": "İpucu",
        "koota": "Koota", "kendisiyle": "Kendisiyle",
        "harita_baslik": "27 Nakṣatra Uyum Haritası",
        "harita_aciklama": (
            "Her satır, Ay nakṣatra'sınızın o nakṣatra ile karşılaştırılmasıdır. "
            "Puan 0–36 arasında; 36 pratikte mümkün değildir."),
    },
    "en": {
        "burc": "Sign", "lord": "Lord", "tanri": "Deity", "yoni": "Yoni",
        "gana": "Gana", "varna": "Varna", "vashya": "Vashya", "nadi": "Nadi",
        "pada": "pada", "nakshatra": "Nakshatra", "puan": "Score",
        "seviye": "Level", "kendi": "self", "yoni_bos": "—",
        "dogum_saat": "Birth Time", "kisi": "Person", "ipucu": "Hint",
        "koota": "Koota", "kendisiyle": "Self",
        "harita_baslik": "27 Nakshatra Compatibility Map",
        "harita_aciklama": (
            "Each row compares your Moon nakshatra with that nakshatra. "
            "The score runs 0–36; 36 is not attainable in practice."),
    },
    "es": {
        "burc": "Signo", "lord": "Señor", "tanri": "Deidad", "yoni": "Yoni",
        "gana": "Gana", "varna": "Varna", "vashya": "Vashya", "nadi": "Nadi",
        "pada": "pada", "nakshatra": "Nakshatra", "puan": "Puntuación",
        "seviye": "Nivel", "kendi": "propio", "yoni_bos": "—",
        "dogum_saat": "Hora de nacimiento", "kisi": "Persona", "ipucu": "Consejo",
        "koota": "Koota", "kendisiyle": "Propio",
        "harita_baslik": "Mapa de compatibilidad de los 27 nakshatras",
        "harita_aciklama": (
            "Cada fila compara tu nakshatra lunar con ese nakshatra. "
            "La puntuación va de 0 a 36; 36 no es alcanzable en la práctica."),
    },
}


def etiket(alan: str, lang: str = "tr") -> str:
    """Tek bir alan adının dil başına karşılığını döndürür."""
    return ETIKET.get(lang, ETIKET["tr"]).get(alan, alan)


#: Doğum saati alanının yardım metni.
SAAT_YARDIM = {
    "tr": ("Doğum saatini girin (12:00 veya 1430). Boş bırakırsanız 12:00 "
           "kabul edilir ve yaklaşık hesap uyarısı gösterilir."),
    "en": ("Enter the birth time (12:00 or 1430). Leave it empty to assume "
           "12:00; an approximation warning is then shown."),
    "es": ("Introduce la hora de nacimiento (12:00 o 1430). Déjalo vacío para "
           "asumir 12:00; se mostrará un aviso de cálculo aproximado."),
}

#: Saat boş bırakıldığında gösterilen uyarı. `{ad}`, `{derece}`, `{rozet}`.
SAAT_UYARI = {
    "tr": ("{ad} için doğum saati girilmedi. Ay {rozet} kabul edildi ve {derece} "
           "dereceye kadar hata olasılığı vardır; nakṣatra sınırına yakın "
           "doğumlarda sonuç değişebilir."),
    "en": ("No birth time entered for {ad}. The Moon is placed at {rozet} with "
           "up to {derece} degrees of error; the result can change for births "
           "near a nakshatra boundary."),
    "es": ("No se indicó la hora de nacimiento de {ad}. La Luna se sitúa a las "
           "{rozet} con hasta {derece} grados de error; el resultado puede "
           "cambiar en nacimientos cercanos a un límite de nakshatra."),
}

#: Koota detaylarındaki "İpucu" öneki.
IPUCU = {"tr": "İpucu", "en": "Hint", "es": "Consejo"}

#: PDF bölümündeki sabit görünür metinler.
#: `baslik` "&middot;" ayracı olmadan verilir; PDF modülü birleştirir.
PDF_METIN = {
    "tr": {
        "baslik": "36 PUANLI UYUM",
        "alt": "Standart sekiz koota, 36 puan",
        "not": ("Not: Tara, Vashya ve Gana yönlü kootalardır; A/B sırası "
                "değiştikçe puanlar değişebilir. Nadi aynı grup olduğunda "
                "puan verilmez."),
    },
    "en": {
        "baslik": "36-POINT COMPATIBILITY",
        "alt": "Standard eight kootas, 36 points",
        "not": ("Note: Tara, Vashya and Gana are directional kootas; scores "
                "may change when the A/B order is swapped. Nadi scores zero "
                "when both fall in the same group."),
    },
    "es": {
        "baslik": "COMPATIBILIDAD DE 36 PUNTOS",
        "alt": "Ocho kootas estándar, 36 puntos",
        "not": ("Nota: Tara, Vashya y Gana son kootas direccionales; las "
                "puntuaciones pueden cambiar al intercambiar el orden A/B. "
                "Nadi puntúa cero cuando ambos pertenecen al mismo grupo."),
    },
}


def pdf_metin(lang: str = "tr") -> dict:
    """PDF bölümünün sabit metinleri; bilinmeyen dilde TR'a düşer."""
    return PDF_METIN.get(lang, PDF_METIN["tr"])
