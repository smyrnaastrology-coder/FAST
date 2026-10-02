"""
Standart 36 puanlı Ashtakoot (Ashtakoot Guna Milan) motoru.

Tasarım notları
---------------
* Yalnızca **sidereal (Lahiri) Ay** kullanılır. Uygulamanın geri kalan tüm
  hesapları tropikal kalır; `FLG_SIDEREAL` verilmedikçe `calc_ut` sonuçları
  değişmez.
* Puanlama şeması **Kuzey Hindistan (North Indian) 36 puan** standardıdır.
  Her koota tablosu `VARYANTLAR` içinde ayrı bir sabit olarak tutulur, böylece
  Güney Hindistan / Başka varyantlar mantığa dokunmadan eklenebilir.
* `kendisi_ile()` (aynı kişiyle karşılaştırma) tanım gereği **28/36** ve
  **Nadi 0** vermelidir; bu, `test_ashtakoot_motoru.py` içinde sabitlenmiştir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    import swisseph as swe
except ImportError:  # pragma: no cover
    swe = None


# --------------------------------------------------------------------------
# Sabitler
# --------------------------------------------------------------------------

NAKSHATRA_ADI = 360.0 / 27.0          # 13°20'
PADA_ADI = NAKSHATRA_ADI / 4.0        # 3°20'

BURC_ADLARI = [
    "Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
    "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık",
]

#: 12 burcun İngilizce ve İspanyolca adları (indeks `BURC_ADLARI` ile aynı).
BURC_ADLARI_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

BURC_ADLARI_ES = [
    "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis",
]

BURC_LORDU = {
    "Koç": "Mars", "Boğa": "Venus", "İkizler": "Mercury", "Yengeç": "Moon",
    "Aslan": "Sun", "Başak": "Mercury", "Terazi": "Venus", "Akrep": "Mars",
    "Yay": "Jupiter", "Oğlak": "Saturn", "Kova": "Saturn", "Balık": "Jupiter",
}

#: Gezegen adlarının İngilizce/İspanyolca karşılıkları. Hesaplama `BURC_LORDU`
#: anahtarlarını kullanır; çeviri yalnızca ekranda gösterim içindir.
GEZEGEN_EN = {
    "Sun": "Sun", "Moon": "Moon", "Mars": "Mars", "Mercury": "Mercury",
    "Jupiter": "Jupiter", "Venus": "Venus", "Saturn": "Saturn",
    "Ketu": "Ketu", "Rahu": "Rahu",
}

GEZEGEN_ES = {
    "Sun": "Sol", "Moon": "Luna", "Mars": "Marte", "Mercury": "Mercurio",
    "Jupiter": "Júpiter", "Venus": "Venus", "Saturn": "Saturno",
    "Ketu": "Ketu", "Rahu": "Rahu",
}

#: Yoni hayvanlarının İngilizce/İspanyolca adları (`YONI_ANIMALS` anahtarları).
YONI_ANIMAL_EN = {
    "At": "Horse", "İnek": "Cow", "Boğa": "Ox", "Koyun": "Sheep",
    "Deve": "Camel", "Yılan": "Serpent", "Aslan": "Lion",
    "Sakal": "Man (bearded)", "Leopard": "Leopard", "Tavus": "Peacock",
    "Kaplan": "Tiger", "Geyik": "Deer", "Kartal": "Eagle", "Köpek": "Dog",
    "Balık": "Fish", "Boş halka": "Empty ring",
}

YONI_ANIMAL_ES = {
    "At": "Caballo", "İnek": "Vaca", "Boğa": "Buey", "Koyun": "Oveja",
    "Deve": "Camello", "Yılan": "Serpiente", "Aslan": "León",
    "Sakal": "Hombre (barba)", "Leopard": "Leopardo", "Tavus": "Pavo real",
    "Kaplan": "Tigre", "Geyik": "Ciervo", "Kartal": "Águila",
    "Köpek": "Perro", "Balık": "Pez", "Boş halka": "Anillo vacío",
}

BURC_UST_MARS = 4
BURC_UST_JUPITER = 9
BURC_UST_SATURN = 10
BURC_UST_KOVA = 10
BURC_UST_BALIK = 11

#: 27 nakṣatra: (TR ad, EN ad, ES ad, lord, tanrı, sembol)
#:
#: Nakṣatra adları Sanskrit kökenli özel adlardır; İspanyolca astroloji
#: kaynakları da aynı yazımı kullanır (Ashlesha, Chitra, Shravana ...), bu
#: yüzden 3. sütun çeviri değil aynen aktarımdır. Gösterilebilir alanların
#: (burç, gezegen, yoni hayvanı, varna, gana) çevirileri aşağıdaki
#: sözlüklerdedir; `AyBilgisi.adla()` hepsini dile göre döndürür.
NAKSHATRALAR: List[Tuple[str, str, str, str, str, str]] = [
    ("Asvini",       "Ashwini",       "Ashwini",       "Ketu",    "Aşvini",     "At"),
    ("Bharani",      "Bharani",      "Bharani",      "Venus",   "Yama",       "İnek"),
    ("Krittika",     "Krittika",     "Krittika",     "Sun",     "Agni",       "Koyun boynuzu"),
    ("Rohini",       "Rohini",       "Rohini",       "Moon",    "Brahma",     "Deve"),
    ("Mrigashira",   "Mrigashira",   "Mrigashira",   "Mars",    "Soma",       "Yılan"),
    ("Ardra",        "Ardra",        "Ardra",        "Rahu",    "Rudra",      "Aslan"),
    ("Punarvasu",    "Punarvasu",    "Punarvasu",    "Jupiter", "Aditi",      "Sakal"),
    ("Pushya",       "Pushya",       "Pushya",       "Saturn",  "Brihaspati", "Keçi / koyun"),
    ("Ashlesha",     "Ashlesha",     "Ashlesha",     "Mercury", "Nagas",      "Yılan"),
    ("Magha",        "Magha",        "Magha",        "Ketu",    "Pitrlar",    "Leopard"),
    ("Purva Phalguni", "Purva Phalguni", "Purva Phalguni", "Venus", "Bhaga",  "Balık teknesi"),
    ("Uttara Phalguni", "Uttara Phalguni", "Uttara Phalguni", "Sun", "Aryaman", "İnek"),
    ("Hasta",        "Hasta",        "Hasta",        "Moon",    "Savitar",    "El"),
    ("Chitra",       "Chitra",       "Chitra",       "Mars",    "Tvashtar",   "Tavus kuşu"),
    ("Swati",        "Swati",        "Swati",        "Rahu",    "Vayu",       "Mercan dalı"),
    ("Vishakha",     "Vishakha",     "Vishakha",     "Jupiter", "Indra",      "Kaplan"),
    ("Anuradha",     "Anuradha",     "Anuradha",     "Saturn",  "Mitra",      "Geyik"),
    ("Jyeshtha",     "Jyeshtha",     "Jyeshtha",     "Mercury", "Indra",      "Kartal / tavus"),
    ("Mula",         "Mula",         "Mula",         "Ketu",    "Nirriti",    "Köpek"),
    ("Purva Ashadha", "Purva Ashadha", "Purva Ashadha", "Venus",  "Apas",       "Fil dişi"),
    ("Uttara Ashadha", "Uttara Ashadha", "Uttara Ashadha", "Sun", "Vishvedev", "Deve"),
    ("Shravana",     "Shravana",     "Shravana",     "Moon",    "Vishnu",     "Külük"),
    ("Dhanishta",    "Dhanishta",    "Dhanishta",    "Mars",    "Vasus",      "Davul"),
    ("Shatabhisha",  "Shatabhisha",  "Shatabhisha",  "Rahu",    "Varuna",     "Boş halka"),
    ("Purva Bhadrapada", "Purva Bhadrapada", "Purva Bhadrapada", "Jupiter", "Aja", "Tazı / rüzgar"),
    ("Uttara Bhadrapada", "Uttara Bhadrapada", "Uttara Bhadrapada", "Saturn", "Ahirbudhya", "İnek sırtı"),
    ("Revati",       "Revati",       "Revati",       "Mercury", "Pushan",     "Balık"),
]

#: Nakṣatra -> yoni hayvanı (Yoni koota).
#:
#: Klasik Yastrijiyotish'te yoni, nakṣatranın **sembolü** değil **eşleşen
#: hayvanıdır**: Hasta'nın sembolü "El" olmakla birlikte yonisi "At"tır ve
#: Asvini ile eşleşir. Bu yüzden sözlük sembol sütunundan bağımsız
#: tutulur — aşağıdaki 14 hayvan çifti klasik eşleşmeyi verir.
#:
#: Çifti olmayan nakṣatralar (Vishakha, Uttara Bhadrapada, Revati) yalnızca
#: kendisiyle eşleşir; sembolleri `NAKSHATRALAR` 6. sütununda kalır.
YONI_ANIMALS: Dict[str, Optional[str]] = {
    "Asvini": "At",            "Hasta": "At",
    "Bharani": "İnek",         "Uttara Phalguni": "İnek",
    "Krittika": "Koyun",       "Pushya": "Koyun",
    "Mrigashira": "Yılan",     "Ashlesha": "Yılan",
    "Ardra": "Aslan",          "Purva Phalguni": "Aslan",
    "Punarvasu": "Sakal",      "Swati": "Sakal",
    "Magha": "Leopard",        "Purva Bhadrapada": "Leopard",
    "Chitra": "Tavus",         "Purva Ashadha": "Tavus",
    "Mula": "Köpek",           "Dhanishta": "Köpek",
    "Anuradha": "Geyik",       "Shravana": "Geyik",
    "Jyeshtha": "Kartal",      "Uttara Ashadha": "Kartal",
    # çifti olmayanlar / ayrı gruplar
    "Vishakha": "Kaplan",      "Uttara Bhadrapada": "Boğa", "Revati": "Balık",
    # sembolü hayvan olmayanlar — geleneksel karşılıklarıyla temsil edilir
    "Rohini": "Deve",          "Shatabhisha": "Boş halka",
}

#: Padaya göre kasta (Varna koota)
VARNA_PADALARI = ["Brahmin", "Kshatriya", "Vaishya", "Shudra"]

#: Padaya göre gana (Gana koota). Kolayca değiştirilebilir yapıda tutulur.
GANA_PADALARI = ["Deva", "Deva", "Manushya", "Rakshasa"]

#: Vashya grupları (Vashya koota).
#:
#: Bu bir varyant şemadır: klasik kaynaklarda Oğlak (Makara) ve Kova (Kumbha)
#: ayrı gruplar olarak da anılır; burada sadeleştirilmiş dört gruba toplanmıştır
#: ve 12 burcun tamamı kapsanır. "Kova" ve "Balık" yarımları padaya göre
#: ayrılır.
VASHYA_GRUPLARI = {
    "Chatura":      [BURC_UST_KOVA, 9],        # Kova, Oğlak
    "Chatushpada":  [0, 1, 4, 8],              # Koç, Boğa, Aslan, Yay
    "Manushya":     [2, 5, 6],                 # İkizler, Başak, Terazi
    "Khala":        [3, 7, 11],                # Yengeç, Akrep, Balık
}

#: Naisargika (doğal) gezegen dostlukları — karşılıklı.
PLANET_DOSTLUK = {
    frozenset(("Sun", "Moon")), frozenset(("Sun", "Jupiter")),
    frozenset(("Sun", "Mars")), frozenset(("Sun", "Mercury")),
    frozenset(("Moon", "Mercury")), frozenset(("Moon", "Jupiter")),
    frozenset(("Moon", "Venus")), frozenset(("Mars", "Jupiter")),
    frozenset(("Mars", "Saturn")), frozenset(("Mercury", "Saturn")),
    frozenset(("Jupiter", "Venus")), frozenset(("Jupiter", "Saturn")),
    frozenset(("Venus", "Mercury")), frozenset(("Venus", "Saturn")),
}

PLANET_NOTR = {
    frozenset(("Sun", "Venus")), frozenset(("Mars", "Mercury")),
    frozenset(("Jupiter", "Mercury")),
}


def vashya_grubu(burc_no: int, pada: int) -> str:
    """Burç + pada çiftinden vashya grubunu döndürür."""
    # Kova (10) ve Balık (11) yarımlara bölünür: 1-2. pada birinci yarı.
    if burc_no == BURC_UST_KOVA:
        return "Chatura" if pada >= 3 else "Manushya"
    if burc_no == 11:
        return "Chatura" if pada >= 3 else "Khala"
    for grup, burclar in VASHYA_GRUPLARI.items():
        if burc_no in burclar:
            return grup
    return "Khala"


def gezegen_iliskisi(a: str, b: str) -> str:
    """İki gezegen arasındaki doğal ilişkiyi verir: dost / notr / dusman."""
    if a == b:
        return "dost"
    if frozenset((a, b)) in PLANET_DOSTLUK:
        return "dost"
    if frozenset((a, b)) in PLANET_NOTR:
        return "notr"
    return "dusman"


# --------------------------------------------------------------------------
# Ay veri yapısı
# --------------------------------------------------------------------------

@dataclass
class AyBilgisi:
    """Tek bir kişinin sidereal Ay konumundan türetilen tüm alanlar."""

    lon: float                       # sidereal boylam (derece)
    burc_no: int                     # 0-11
    burc_adi: str
    nakshatra_no: int                # 1-27
    nakshatra_adi: str
    nakshatra_adi_en: str
    nakshatra_adi_es: str
    lord: str
    tanri: str
    sembol: str
    pada: int                        # 1-4
    varna: str
    gana: str
    yoni: Optional[str]
    cinsiyet: str                    # "erkek" / "kadin"
    nadi: str
    yaklasik: bool = False           # doğum saati bilinmiyorsa True

    @property
    def nakshatra_basi(self) -> float:
        return (self.nakshatra_no - 1) * NAKSHATRA_ADI

    @property
    def nakshatra_ici_derece(self) -> float:
        return self.lon - self.nakshatra_basi

    @property
    def burc_ici_derece(self) -> float:
        return self.lon % 30.0

    # -- yerelleştirme -------------------------------------------------
    # Aşağıdaki sözlükler modül seviyesinde tanımlıdır; burada sonradan
    # atanabilmeleri için geç çözülür (import sırası güvenliği).

    def nakshatra(self, lang: str = "tr") -> str:
        """Nakṣatra adı: tr / en / es."""
        return _lang_get(self.nakshatra_adi, self.nakshatra_adi_en,
                         self.nakshatra_adi_es, lang)

    def burc(self, lang: str = "tr") -> str:
        """Burç adı. Hesaplama `burc_adi` (Türkçe) üzerinden yapılır."""
        return _lang_get(self.burc_adi,
                         BURC_ADLARI_EN[self.burc_no],
                         BURC_ADLARI_ES[self.burc_no], lang)

    def lord_adi(self, lang: str = "tr") -> str:
        """Nakṣatra lordunun gezegen adı."""
        return _GEZEGEN.get(lang, _TR_KIMLIK).get(self.lord, self.lord)

    def tanri_adi(self, lang: str = "tr") -> str:
        """Nakṣatranın tanrısı/deity'si (tanrı adları tüm dillerde aynı)."""
        return self.tanri

    def yoni_adi(self, lang: str = "tr") -> Optional[str]:
        """Yoni hayvanının dile göre adı (`None` ise boş halka)."""
        if self.yoni is None:
            return None
        return _YONI.get(lang, _TR_KIMLIK).get(self.yoni, self.yoni)

    def varna_adi(self, lang: str = "tr") -> str:
        return _VARNA.get(lang, _TR_KIMLIK).get(self.varna, self.varna)

    def gana_adi(self, lang: str = "tr") -> str:
        return _GANA.get(lang, _TR_KIMLIK).get(self.gana, self.gana)

    def cinsiyet_adi(self, lang: str = "tr") -> str:
        return _CINSIYET.get(lang, _TR_KIMLIK).get(self.cinsiyet, self.cinsiyet)

    def ozet(self, lang: str = "tr") -> str:
        """`Nakṣatra N. pada · Burç` biçiminde tek satırlık etiket."""
        return f"{self.nakshatra(lang)} {self.pada}. · {self.burc(lang)}"


# --------------------------------------------------------------------------
# Yerelleştirme sözlükleri
# --------------------------------------------------------------------------

def _TR_KIMLIK(ad: str) -> str:
    """Kimlik dönüşümü: Türkçe metinlerde değişecek sözcük yok."""
    return ad


#: `_TR_KIMLIK` bir fonksiyon olduğu için sözlük arayüzü şart; boş sözlük
#: `dict.get(ad, ad)` ile aynı davranışı verir.
_TR_KIMLIK_BOŞ: Dict[str, str] = {}

_GEZEGEN = {"tr": _TR_KIMLIK_BOŞ, "en": GEZEGEN_EN, "es": GEZEGEN_ES}
_YONI = {"tr": _TR_KIMLIK_BOŞ, "en": YONI_ANIMAL_EN, "es": YONI_ANIMAL_ES}

#: Padaya göre kasta adları (İngilizce/Spanish karşılıkları).
_VARNA = {
    "tr": _TR_KIMLIK_BOŞ,
    "en": {"Brahmin": "Brahmin", "Kshatriya": "Kshatriya",
           "Vaishya": "Vaishya", "Shudra": "Shudra"},
    "es": {"Brahmin": "Brahmin", "Kshatriya": "Kshatriya",
           "Vaishya": "Vaishya", "Shudra": "Shudra"},
}

#: Padaya göre gana (temperament) adları.
_GANA = {
    "tr": _TR_KIMLIK_BOŞ,
    "en": {"Deva": "Deva", "Manushya": "Manushya", "Rakshasa": "Rakshasa"},
    "es": {"Deva": "Deva", "Manushya": "Humano", "Rakshasa": "Rakshasa"},
}

#: Yoni cinsiyeti.
_CINSIYET = {
    "tr": _TR_KIMLIK_BOŞ,
    "en": {"erkek": "male", "kadin": "female"},
    "es": {"erkek": "masculino", "kadin": "femenino"},
}


def _lang_get(tr: str, en: str, es: str, lang: str) -> str:
    """`lang` değerine göre üç metinden birini seçer; bilinmeyen dilde TR."""
    if lang == "en":
        return en or tr
    if lang == "es":
        return es or tr
    return tr


def _cinsiyet(pada: int) -> str:
    """Yoni koota için: tek padalar erkek, çift padalar kadın."""
    return "erkek" if pada % 2 == 1 else "kadin"


def ay_nakshatrasi_hesapla(lon_sidereal: float, yaklasik: bool = False) -> AyBilgisi:
    """Sidereal Ay boylamından nakṣatra/pada/burç türetir ve `AyBilgisi` döndürür."""
    lon = float(lon_sidereal) % 360.0

    n_idx = int(lon // NAKSHATRA_ADI) % 27
    kalan = lon - n_idx * NAKSHATRA_ADI
    pada = min(4, int(kalan // PADA_ADI) + 1)

    tr, en, es, lord, tanri, sembol = NAKSHATRALAR[n_idx]
    burc_no = int(lon // 30) % 12

    return AyBilgisi(
        lon=lon,
        burc_no=burc_no,
        burc_adi=BURC_ADLARI[burc_no],
        nakshatra_no=n_idx + 1,
        nakshatra_adi=tr,
        nakshatra_adi_en=en,
        nakshatra_adi_es=es,
        lord=lord,
        tanri=tanri,
        sembol=sembol,
        pada=pada,
        varna=VARNA_PADALARI[pada - 1],
        gana=GANA_PADALARI[pada - 1],
        yoni=YONI_ANIMALS.get(tr),
        cinsiyet=_cinsiyet(pada),
        nadi=("nadi_1" if pada in (1, 2) else
              "nadi_2" if pada == 3 else "nadi_3"),
        yaklasik=yaklasik,
    )


def _sid_mod_ayarla():
    """Lahiri modunu kurar.

    ÖNEMLİ — bu çağrı "bir kez yapılıp bayraklaanır" şeklinde KURULAMAZ.
    `pyswisseph` sidereal modu thread-local C durumu olarak tutar; `set_sid_mode`
    yalnızca onu çağıran thread'in durumunu değiştirir. FastAPI/uvicorn her
    isteği worker thread'de servis ettiği için, modu yalnızca ilk thread
    kuran bir bayrak şu sonucu veriyordu:

        ana thread        -> 359.235721
        worker thread     -> 358.352513     (0.8832° yanlış)

    0.8832° fark bir nakşatradan (13.33°) fazladır ve Ay'ın hangi nakşatra/
    pada düştüğünü değiştirerek 36 puanlık tabloyu bozuyor; üstelik sonuç
    isteği hangi thread'in karşıladığına bağlı olarak değişiyordu.

    Bu yüzden mod HER çağrıda, thread ne olursa olsun yeniden kurulur.
    `set_sid_mode` yalnızca `FLG_SIDEREAL` verilen çağrılarda etkili olduğu
    için uygulamanın tropikal hesapları bozulmaz.
    """
    if swe is not None:
        swe.set_sid_mode(swe.SIDM_LAHIRI)


def ay_konumu_utc(yil: int, ay: int, gun: int, saat_utc: float) -> float:
    """UTC verilen doğum anı için Lahiri sidereal Ay boylamını derece döndürür.

    NOT: `FLG_SIDEREAL` verildiği için Ay, tropikalayanamsa değil Lahiri
   ayanamsa ile düşürülür (fark ≈ 23.7°). Sadece bu fonksiyon bu bayrağı
kullanır; uygulamanın geri kalanı tropikal kalır.
    """
    if swe is None:  # pragma: no cover
        raise RuntimeError("pyswisseph kurulu degil")
    _sid_mod_ayarla()
    jd = swe.julday(yil, ay, gun, saat_utc)
    return swe.calc_ut(jd, swe.MOON, swe.FLG_MOSEPH | swe.FLG_SPEED |
                      swe.FLG_SIDEREAL)[0][0]


# --------------------------------------------------------------------------
# Koota puanlama
# --------------------------------------------------------------------------

@dataclass
class Koota:
    ad: str                    # anahtar, örn. "varna" (metin sözlükleri bununla eşleşir)
    ad_tr: str                 # görünen Türkçe ad, örn. "Varna"
    ad_en: str
    ad_es: str
    azami: int
    puan: int
    ayni: bool = False        # aynı kişiyle karşılaştırmada mı
    not_: str = ""
    detay: dict = field(default_factory=dict)


def _koota_varna(a: AyBilgisi, b: AyBilgisi) -> Tuple[int, bool, str, dict]:
    ayni = a.varna == b.varna
    return (1 if ayni else 0), ayni, ("" if ayni else "Kast farkı"), {
        "a": a.varna, "b": b.varna}


def _koota_vashya(a: AyBilgisi, b: AyBilgisi) -> Tuple[int, bool, str, dict]:
    ga = vashya_grubu(a.burc_no, a.pada)
    gb = vashya_grubu(b.burc_no, b.pada)
    lord_b = BURC_LORDU[b.burc_adi]
    gl_b = vashya_grubu(_lord_burc_no(lord_b), 2)

    if ga == gb:
        return 2, True, "", {"a": ga, "b": gb}
    if ga == gl_b:
        return 1, False, "Gezegen uyum aracılığıyla kısmi", {
            "a": ga, "b": gb, "lord": lord_b}
    return 0, False, "Vashya kategorileri uzak", {"a": ga, "b": gb}


def _lord_burc_no(lord: str) -> int:
    for no, ad in enumerate(BURC_ADLARI):
        if BURC_LORDU[ad] == lord:
            return no
    return 0


def _koota_tara(a: AyBilgisi, b: AyBilgisi) -> Tuple[int, bool, str, dict]:
    sira = ((a.nakshatra_no - b.nakshatra_no) % 9) + 1
    if sira <= 3:
        return 3, True, "", {"sira": sira}
    if sira <= 6:
        return 1, False, "Orta tara", {"sira": sira}
    return 0, False, "Düşük tara", {"sira": sira}


def _koota_yoni(a: AyBilgisi, b: AyBilgisi) -> Tuple[int, bool, str, dict]:
    if a.yoni != b.yoni:
        return 0, False, f"Farklı yoni: {a.yoni} / {b.yoni}", {"a": a.yoni, "b": b.yoni}
    if a.cinsiyet == b.cinsiyet:
        return 4, True, "", {"a": a.yoni, "b": b.yoni, "cinsiyet": a.cinsiyet}
    return 3, False, "Aynı yoni, zıt cinsiyet", {
        "a": a.yoni, "b": b.yoni, "cinsiyet": f"{a.cinsiyet}/{b.cinsiyet}"}


def _koota_graha_maitri(a: AyBilgisi, b: AyBilgisi) -> Tuple[int, bool, str, dict]:
    if a.burc_no == b.burc_no:
        return 5, True, "", {"a": a.burc_adi}
    la, lb = BURC_LORDU[a.burc_adi], BURC_LORDU[b.burc_adi]
    iliski = gezegen_iliskisi(la, lb)
    puan = {"dost": 4, "notr": 3, "dusman": 1}[iliski]
    return puan, False, f"{la} / {lb}: {iliski}", {"a": la, "b": lb, "iliski": iliski}


#: Gana koota tablosu. Klasik Kuzey Hindistan şeması **yönlüdür**: (A, B) ile
#: (B, A) farklı puan verebilir. Bu yüzden 9 kombinasyonun tamamı tanımlıdır.
GANA_TABLOSU = {
    ("Deva", "Deva"): 6, ("Deva", "Manushya"): 5, ("Deva", "Rakshasa"): 0,
    ("Manushya", "Deva"): 5, ("Manushya", "Manushya"): 6, ("Manushya", "Rakshasa"): 1,
    ("Rakshasa", "Deva"): 0, ("Rakshasa", "Manushya"): 0, ("Rakshasa", "Rakshasa"): 6,
}


def _koota_gana(a: AyBilgisi, b: AyBilgisi) -> Tuple[int, bool, str, dict]:
    ayni = a.gana == b.gana
    puan = GANA_TABLOSU[(a.gana, b.gana)]
    return puan, ayni, "" if ayni else f"{a.gana} / {b.gana}", {
        "a": a.gana, "b": b.gana}


def _koota_rasi(a: AyBilgisi, b: AyBilgisi) -> Tuple[int, bool, str, dict]:
    fark = (a.burc_no - b.burc_no) % 12
    if fark == 0:
        return 7, True, "", {"fark": 0}
    if fark in (1, 2, 3, 9, 10, 11):
        return 5, False, "2./4. dost veya 3./12. tarafta", {"fark": fark}
    if fark in (4, 8):
        return 3, False, "5. veya 9. taraf", {"fark": fark}
    if fark in (5, 7):
        return 1, False, "6. veya 8. taraf", {"fark": fark}
    return 0, False, "Karşı taraf (7.)", {"fark": fark}


def _koota_nadi(a: AyBilgisi, b: AyBilgisi) -> Tuple[int, bool, str, dict]:
    ayni = a.nadi == b.nadi
    return (0 if ayni else 8), ayni, ("Nadi eşleşti" if ayni else ""), {
        "a": a.nadi, "b": b.nadi}


# --------------------------------------------------------------------------
# Nadi Dosha: puan değişmez, ama bağlamı modellenir
# --------------------------------------------------------------------------
#
# Ashtakoot'un tek sıfır puanlı kalemi Nadi'dir ve bu sıfır **geleneksel olarak
# nihai sonuç değildir**. Brihat Samhita ve ona dayanan bölümler, Nadi eşleşmesini
# "bhanga" (kırılma/hafifletme) ve "taraka" (şiddetlendirme) koşullarıyla
# birlikte ele alır:
#
#   * Bhanga — dosha etkisini zayıflatan etkenler. En sık örneklenen ve en güçlü
#     kabul edileni, Ay burçlarının birbirine 2/4/6/8/12 mesafede olmasıdır.
#   * Taraka — doshayı ağırlaştıran etkenler. Ay burçlarının 3/5/9/10/11
#     mesafede olması bu grubun başında gelir.
#
# TASARIM KARARI — puan değiştirilmez
# ----------------------------------
# Bu blok `nadi` kootasının 0/8 puanına **dokunmaz**. Klasik literatürde
# "dosha varsa iptal edilir" diyen okullar olsa da hangi okulun hangi ağırlığı
# kullandığı tartışmalıdır; 36 puanlık tablo tek bir okulun sayısıdır ve
# değiştirmek tüm sonuçları kaydırırdı. Bunun yerine doshanın varlığı, şiddeti
# ve bağlamı ayrı bir blok olarak raporlanır; kullanıcı ham puanı görmeye
# devam eder, yorumu ise çeviri katmanından gelir.
#
# KAPSAM
# ------
# Bu motor yalnızca Ay konumu üzerinden çalışır; doğum anındaki diğer gezegen
# konumlarını hesaplamaz. Bu yüzden klasik kural setinin yalnızca Ay burçları ve
# pada bilgisinden türetilebilen kısmı uygulanır. Nadi lordlarının 2/4/6/8/12
# mesafede olması gibi gezegen konumu gerektiren alt kurallar **bilinçli olarak
# dışarıda bırakılmıştır**; kapsam dışı oldukları `kapsam_disi` altında
# bildirilir ki sessizce atlanmasınlar.

#: Nadi lordları (pada -> gezegen). Brihat Samhita'daki yaygın eşleme:
#: 1. pada Mars, 2. pada Ay, 3. pada Güneş, 4. pada Venüs.
NADI_LORDU: Dict[int, str] = {1: "Mars", 2: "Moon", 3: "Sun", 4: "Venus"}

#: Bhanga (hafifletme) koşulları — hepsi Ay verisinden türetilebilir.
_BHANGA_KURALLARI = {
    "rasi_kendra": (
        "Ay burçları 2/12, 4/10 veya 6/8 konumunda",
        "En sık örneklenen hafifleticidir. Dosha, Ay burçlarının bu konum "
        "çiftlerinde olmasıyla dengelenir.",
    ),
    "nadi_lord_ayni": (
        "Nadi lordları aynı gezegen",
        "İki tarafın da nadi'sini yöneten gezegen aynıysa doshanın aracısı "
        "ortaklaşır.",
    ),
    "ayni_gana": (
        "Aynı gana",
        "Ay'ın temel karakter sınıfı aynıysa dosha bağlamında zayıflar.",
    ),
    "ayni_varna": (
        "Aynı varna",
        "Ay'ın varna'sı aynıysa kasta katmanında örtüşme vardır.",
    ),
}

#: Taraka (şiddetlendirme) koşulları.
_TARAKA_KURALLARI = {
    "rasi_dusman": (
        "Ay burçları 3/11 veya 5/9 konumunda",
        "Dosha, bu konum çiftlerinde en ağır kabul edilir; hafifletici koşul "
        "yoksa dosha öne çıkar.",
    ),
}

#: Gezegen konumu gerektirdiği için uygulanmayan klasik alt kurallar.
#: Sessizce atlanmak yerine burada bildirilir.
KAPSAM_DISI_KURALLAR = {
    "nadi_lord_kendra": "Nadi lordlarının 2/12, 4/10 veya 6/8 konumunda olması",
    "rasi_lord_kendra": "Ay burçlarının lordlarının 2/12, 4/10 veya 6/8 olması",
    "nadi_lord_dusthana": "Her iki nadi lordunun da 6/8/12'de bulunması",
    "kendra_lagna": "Lagna'nın her iki Ay'a 2/12, 4/10 veya 6/8 olması",
}


def _burc_iliskisi(x: int, y: int) -> Tuple[int, str]:
    """İki burç arasındaki konum ilişkisini simetrik olarak çözer.

    Klasik metinler burçları birbirine göre konumlarıyla anmaz, **eşleşen
    ev çiftleriyle** anar: "2/12", "4/10", "6/8", "3/11", "5/9", "7". Bu
    yüzden mesafe iki yönden de bakılarak küçültülür; iki tarafın "hangi
    evde durduğu" önemsizdir, ilişkinin kendisi önemlidir.

    Döndürür: (mesafe, etiket). `mesafe` 0..6, `etiket` "1", "2/12",
    "3/11", "4/10", "5/9", "6/8", "7".
    """
    d = abs(int(x) - int(y)) % 12
    d = min(d, 12 - d)
    etiket = {0: "1", 1: "2/12", 2: "3/11", 3: "4/10",
              4: "5/9", 5: "6/8", 6: "7"}[d]
    return d, etiket


#: Bhanga için klasik burç ilişkileri: 2/12, 4/10, 6/8.
_BHANGA_BURC_MESAFELERI = (1, 3, 5)

#: Taraka için klasik burç ilişkileri: 3/11, 5/9.
_TARAKA_BURC_MESAFELERI = (2, 4)


def nadi_dosha_analizi(a: AyBilgisi, b: AyBilgisi) -> dict:
    """Nadi eşleşmesinin varlığını, şiddetini ve bağlamını çözer.

    Dilden bağımsız kod döndürür: `kosullar` içindeki `kod` alanları metin
    katmanında (`ashtakoot_metin.nadi_dosha_metin`) dile çevrilir.
    """
    mesafe, iliski = _burc_iliskisi(a.burc_no, b.burc_no)
    lord_a = NADI_LORDU.get(a.pada)
    lord_b = NADI_LORDU.get(b.pada)
    var = a.nadi == b.nadi

    bhanga: List[dict] = []
    taraka: List[dict] = []

    if var:
        aday = {
            "rasi_kendra": mesafe in _BHANGA_BURC_MESAFELERI,
            "nadi_lord_ayni": lord_a is not None and lord_a == lord_b,
            "ayni_gana": a.gana == b.gana,
            "ayni_varna": a.varna == b.varna,
        }
        for kod, gecerli in aday.items():
            if gecerli:
                baslik, detay = _BHANGA_KURALLARI[kod]
                bhanga.append({"kod": kod, "baslik": baslik, "detay": detay,
                               "iliski": iliski})

        if mesafe in _TARAKA_BURC_MESAFELERI:
            baslik, detay = _TARAKA_KURALLARI["rasi_dusman"]
            taraka.append({"kod": "rasi_dusman", "baslik": baslik, "detay": detay,
                           "iliski": iliski})

    if not var:
        seviye = "yok"
    elif not bhanga:
        seviye = "belirgin"
    elif len(bhanga) == 1:
        seviye = "hafif"
    else:
        seviye = "hafifletilmis"

    return {
        "var": var,
        "seviye": seviye,
        "mesafe": mesafe,
        "iliski": iliski,
        "nadi_a": a.nadi,
        "nadi_b": b.nadi,
        "pada_a": a.pada,
        "pada_b": b.pada,
        "nadi_lord_a": lord_a,
        "nadi_lord_b": lord_b,
        "bhanga_sayisi": len(bhanga),
        "taraka_sayisi": len(taraka),
        "kosullar": bhanga + taraka,
        "kapsam_disi": list(KAPSAM_DISI_KURALLAR.keys()),
    }


#: Sıralı kootalar: (anahtar, TR/EN/ES ad, azami puan, hesaplayıcı)
KOOTALAR = [
    ("varna",         "Varna",         "Varna",         "Varna",         1, _koota_varna),
    ("vashya",        "Vashya",        "Vashya",        "Vashya",        2, _koota_vashya),
    ("tara",          "Tara",          "Tara",          "Tara",          3, _koota_tara),
    ("yoni",          "Yoni",          "Yoni",          "Yoni",          4, _koota_yoni),
    ("graha_maitri",  "Graha Maitri",  "Graha Maitri",  "Graha Maitri",  5, _koota_graha_maitri),
    ("gana",          "Gana",          "Gana",          "Gana",          6, _koota_gana),
    ("rasi",          "Rasi",          "Rashi",         "Rashi",         7, _koota_rasi),
    ("nadi",          "Nadi",          "Nadi",          "Nadi",          8, _koota_nadi),
]

AZAMI_TOPLAM = sum(k[4] for k in KOOTALAR)   # 36

#: (A, B) ile (B, A) farklı puan verebilen kootalar. Klasik şemada **Tara**
#: (9'lu döngü), **Vashya** (gezin aracılığıyla kısmi puan) ve **Gana**
#: (yönlü tablo) yönlüdür; kalan beş koota simetriktir. UI metinleri bu
#: ayrımı kullanır.
YONLU_KOOTALAR = {"tara", "vashya", "gana"}


@dataclass
class AshtaKootSonuc:
    a: AyBilgisi
    b: AyBilgisi
    kootalar: List[Koota]
    toplam: int
    azami: int = AZAMI_TOPLAM
    kendisi_ile: bool = False
    uyari: List[str] = field(default_factory=list)
    nadi_dosha: Dict[str, object] = field(default_factory=dict)

    @property
    def yuzde(self) -> float:
        return (self.toplam / self.azami * 100.0) if self.azami else 0.0

    @property
    def seviye(self) -> str:
        """20-23 / 26-27 / 28-29 / 33-34 bantları.

        Azami 36 olsa da pratikte ulaşılabilir toplamlar 20-34 arasıdır
        (ölçüldü: 20, 21, 22, 23, 26, 27, 28, 29, 33, 34). Bu yüzden bantlar
        bu aralığa göre kurulur; aksi halde alt iki bant hiç dolmaz.
        """
        t = self.toplam
        if t <= 23:
            return "cok_dusuk"
        if t <= 27:
            return "dusuk"
        if t <= 29:
            return "orta"
        return "yuksek"

    def koota(self, anahtar: str) -> Optional[Koota]:
        for k in self.kootalar:
            if k.ad == anahtar:
                return k
        return None

    def tablo_sozlugu(self) -> Dict[str, dict]:
        """UI / PDF için düz sözlük."""
        return {
            "toplam": self.toplam, "azami": self.azami,
            "yuzde": round(self.yuzde, 1), "seviye": self.seviye,
            "kendisi_ile": self.kendisi_ile,
            "a": _kisalt(self.a), "b": _kisalt(self.b),
            "kootalar": [
                {"ad": k.ad, "ad_tr": k.ad_tr, "ad_en": k.ad_en, "ad_es": k.ad_es,
                 "azami": k.azami, "puan": k.puan, "not": k.not_, "detay": k.detay}
                for k in self.kootalar
            ],
            "uyari": list(self.uyari),
            "nadi_dosha": dict(self.nadi_dosha),
        }


def _kisalt(ay: AyBilgisi) -> dict:
    return {
        "lon": round(ay.lon, 4), "burc": ay.burc_adi,
        "burc_ici": round(ay.burc_ici_derece, 2),
        "nakshatra": ay.nakshatra_adi, "nakshatra_no": ay.nakshatra_no,
        "pada": ay.pada, "lord": ay.lord, "tanri": ay.tanri, "sembol": ay.sembol,
        "varna": ay.varna, "gana": ay.gana, "yoni": ay.yoni,
        "cinsiyet": ay.cinsiyet, "nadi": ay.nadi, "yaklasik": ay.yaklasik,
    }


def ashtakoot_hesapla(a: AyBilgisi, b: AyBilgisi) -> AshtaKootSonuc:
    """İki `AyBilgisi` arasında standart 36 puanlık Ashtakoot hesabı."""
    kootalar: List[Koota] = []
    uyari: List[str] = []
    toplam = 0

    for anahtar, ad, ad_en, ad_es, azami, hesaplayici in KOOTALAR:
        puan, ayni, not_, detay = hesaplayici(a, b)
        puan = max(0, min(azami, int(puan)))
        toplam += puan
        kootalar.append(Koota(ad=anahtar, ad_tr=ad, ad_en=ad_en, ad_es=ad_es,
                              azami=azami, puan=puan, ayni=ayni, not_=not_,
                              detay=detay))

    if a.yaklasik or b.yaklasik:
        uyari.append(
            "Doğum saati bilinmediği için Ay konumu yaklaşık hesaplandı. "
            "Nakṣatra sınırına yakın doğumlarda sonuç değişebilir.")

    return AshtaKootSonuc(a=a, b=b, kootalar=kootalar, toplam=toplam,
                          kendisi_ile=False, uyari=uyari,
                          nadi_dosha=nadi_dosha_analizi(a, b))


def kendisi_ile(ay: AyBilgisi) -> AshtaKootSonuc:
    """Aynı kişiyi kendisiyle karşılaştırır — tanım gereği 28/36, Nadi 0."""
    sonuc = ashtakoot_hesapla(ay, ay)
    sonuc.kendisi_ile = True
    sonuc.uyari = list(sonuc.uyari) + [
        "Bu, kişinin kendisine karşı yapılan referans karşılaştırmadır; "
        "Varna-Vashya-Tara-Yoni-Gana-Graha Maitri-Rasi boyunca ölçülen "
        "sistem içi tutarlılığı gösterir. Nadi 0 her zaman çıkar."]
    return sonuc


# --------------------------------------------------------------------------
# Tek kişi profili: Ay nakṣatra özeti + 27 nakṣatra uyum haritası
# --------------------------------------------------------------------------

def nakshatra_uyum_haritasi(ay: AyBilgisi) -> List[dict]:
    """Kişinin kendi Ay nakṣatrası ile 27 nakṣatranın uyum tablosu.

    Her satır: uyum puanı (0-8), toplam bandı ve iki taraflı açıklama anahtarı.
    """
    satirlar = []
    for i, (tr, en, es, lord, tanri, sembol) in enumerate(NAKSHATRALAR):
        diger = AyBilgisi(
            lon=i * NAKSHATRA_ADI + PADA_ADI,       # odağın ilk padası
            burc_no=int((i * NAKSHATRA_ADI) // 30) % 12,
            burc_adi=BURC_ADLARI[int((i * NAKSHATRA_ADI) // 30) % 12],
            nakshatra_no=i + 1, nakshatra_adi=tr, nakshatra_adi_en=en,
            nakshatra_adi_es=es, lord=lord, tanri=tanri, sembol=sembol,
            pada=1, varna=VARNA_PADALARI[0], gana=GANA_PADALARI[0],
            yoni=YONI_ANIMALS.get(tr), cinsiyet="erkek", nadi="nadi_1")
        sonuc = ashtakoot_hesapla(ay, diger)
        satirlar.append({
            "nakshatra_no": i + 1, "nakshatra": tr, "nakshatra_en": en,
            "nakshatra_es": es, "lord": lord, "tanri": tanri, "sembol": sembol,
            "burc": diger.burc_adi,
            "burc_en": BURC_ADLARI_EN[diger.burc_no],
            "burc_es": BURC_ADLARI_ES[diger.burc_no],
            "lord_en": GEZEGEN_EN.get(lord, lord),
            "lord_es": GEZEGEN_ES.get(lord, lord),
            "sembol_en": YONI_ANIMAL_EN.get(sembol, sembol),
            "sembol_es": YONI_ANIMAL_ES.get(sembol, sembol),
            "toplam": sonuc.toplam, "yuzde": round(sonuc.yuzde, 1),
            "seviye": sonuc.seviye,
            "kootalar": [{"ad": k.ad, "azami": k.azami, "puan": k.puan,
                          "not": k.not_} for k in sonuc.kootalar],
            "kendisi": (i + 1 == ay.nakshatra_no),
        })
    satirlar.sort(key=lambda s: (-s["toplam"], s["nakshatra_no"]))
    return satirlar


def nakshatra_profili(ay: AyBilgisi) -> dict:
    """Tek kişi için Ay nakṣatra özeti + en uyumlu / en uyumsuz 5 nakṣatra."""
    harita = nakshatra_uyum_haritasi(ay)
    en_iyi = [s for s in harita if not s["kendisi"]][:5]
    en_kotu = [s for s in reversed(harita) if not s["kendisi"]][-5:]
    en_kotu = list(reversed(en_kotu))
    return {
        "ay": _kisalt(ay),
        "lord": ay.lord,
        "tanri": ay.tanri,
        "sembol": ay.sembol,
        "pada_metni": f"{ay.nakshatra_adi} {ay.pada}. Pada",
        "harita": harita,
        "en_iyi": en_iyi,
        "en_kotu": en_kotu,
        "kendisi_ile": kendisi_ile(ay).tablo_sozlugu(),
    }
