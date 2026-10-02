# -*- coding: utf-8 -*-
"""
Ashtakoot için otomatik UTC ofseti çözümü.

Kullanıcı UTC ofsetini bilmez ve bilmesi de gerekmez: doğum ŞEHRİ + doğum
TARİHİ yeterlidir. Bu modül şehir adını koordinata çözüp o koordinat ve
tarih için geçerli UTC ofsetini hesaplar.

NEDEN GEREKLİ
--------------
Ay'ın görünen coğrafi konumu yalnızca doğum ANINA bağlıdır; doğum yerine
bağlı değildir. Tek gereken, yerel saati UTC'ye çeviren ofsettir. Ancak bu
ofset SABİT DEĞİLDİR: Türkiye örneğinde 2016 öncesi kışın UTC+2, yazın
UTC+3'tü. Sabit bir "+3" varsayımı kışın doğan bir kişide Ay'ın boylamını
~15° kaydırır, nakṣatra ve pada değişir, dolayısıyla 36 puanlık tablo tamamen
farklı çıkar. Bu yüzden ofset hesabı TARİHE BAĞLIDIR.

ÇÖZÜM KADEMELERİ
----------------
1. **IANA tz veritabanı** (`timezonefinder` + `pytz`) — koordinattan timezone
   adı, sonra O TARİHE ait gerçek ofset. `requirements.txt`'te ikisi de kurulu
   olduğu için production daima bu yolu kullanır. Tarihsel DST geçişleri dahil
   her şey buradan gelir.
2. **Boylam tahmini** — yalnızca 1. adım çalışamazsa. `round(lon/15)` mantığıyla
   yarım saat yuvarlanır; maksimum hata ±30 dakikadır. Bu değer "kesin" değildir,
   bu yüzden dönen `yontem` alanı `boylam` olur ve endpoint kullanıcıya bunu
   bildirir.

Neden elle bölge tablosu YOK: önceki sürümde `timezonefinder`/`pytz` yoksa
diye yazılmış bir `BOLGESEL_UTC` tablosu vardı. Bu tablo gerçek tz veritabanıyla
karşılaştırıldığında %22,5 sapma gösteriyordu (Hindistan %100, Doğu Avrupa %100,
Rusya %100, Şili %46 yanlış) ve sınırlayıcı kutuları örtüştüğü için Hindistan
koordinatlarına Çin ofseti (+8) uygulanıyordu. 1 saatlik hata Ay boylamını ~15°
kaydırıp nakṣatra/pada değiştirdiğinden, hatalı bir "yedek" sessizce 36 puanlık
tabloyu bozmaktadır. Bu yüzden tablo tamamen kaldırıldı: ya doğru veritabanı
kullanılır, ya da hata payı en fazla yarım saat olan dürüst bir tahmin kullanılır.

`sehir_coz()` şehir adını önce yerel `cities_db.json`, sonra gerekirse
geopy/Nominatim ile koordinata çözer.
"""

from __future__ import annotations

import threading
import time
from datetime import date, datetime
from typing import Optional, Tuple

try:
    import pytz as _pytz
except ImportError:  # pragma: no cover
    _pytz = None

try:
    from timezonefinder import TimezoneFinder as _TimezoneFinder
except ImportError:  # pragma: no cover
    _TimezoneFinder = None

_TZF = _TimezoneFinder() if _TimezoneFinder is not None else None


# --------------------------------------------------------------------------
# Ofset çözümü — tek güvenilir kaynak: IANA tz veritabanı
# --------------------------------------------------------------------------

def _saati_parcala(saat: float) -> Tuple[int, int]:
    """Ondalık saati (örn. 14.5) -> (tam saat, dakika)."""
    tam_saat = int(saat)
    dakika = int(round((float(saat) - tam_saat) * 60))
    if dakika == 60:
        tam_saat += 1
        dakika = 0
    return tam_saat % 24, dakika


def tzdb_ofset(lat: float, lon: float, yil: int, ay: int, gun: int,
               tam_saat: int, dakika: int) -> Optional[dict]:
    """IANA tz veritabanından o koordinat ve tarih için GERÇEK UTC ofseti.

    Dönen sözlük: {'offset': float, 'tz': str, 'belirsiz': bool}.
    Kütüphane yoksa veya koordinat çözülemezse None döner.

    `belirsiz`, yerel saatin yaz saati geçişinde iki kez geçtiği ya da hiç
    geçmediği durumlarda True olur. Doğum saatleri nadiren bu aralıktadır ama
    olduğunda sonuç deterministik seçilir ve bilgi kaybı olmaması için işaretlenir.
    """
    if _TZF is None or _pytz is None:
        return None
    try:
        tz_ad = (_TZF.timezone_at(lat=lat, lng=lon)
                 or _TZF.closest_timezone_at(lat=lat, lng=lon))
    except Exception:
        return None
    if not tz_ad:
        return None

    try:
        tz = _pytz.timezone(tz_ad)
        naive = datetime(yil, ay, gun, tam_saat, dakika)
    except Exception:
        return None

    belirsiz = False
    try:
        yerel = tz.localize(naive)
    except Exception:
        belirsiz = True
        yerel = None
        for is_dst in (True, False):
            try:
                yerel = tz.localize(naive, is_dst=is_dst)
                break
            except Exception:
                continue
        if yerel is None:
            return None

    try:
        ofset = yerel.utcoffset().total_seconds() / 3600.0
    except Exception:
        return None

    return {"offset": round(ofset, 2), "tz": tz_ad, "belirsiz": belirsiz}


def boylam_tahmini(lon: float) -> float:
    """Boylamdan kaba UTC ofseti (yarım saat yuvarlamalı).

    Yalnızca tz veritabanı erişilemediğinde kullanılır. Maksimum hata ±30
    dakikadır ve sonuç kesin kabul edilmemelidir.
    """
    ham = float(lon) / 15.0
    return max(-12.0, min(12.0, round(ham * 2.0) / 2.0))


def otomatik_utc_offset(lat: float, lon: float, yil: int, ay: int, gun: int,
                        saat: float = 12.0) -> Tuple[float, str]:
    """(koordinat, tarih) -> (UTC ofseti, kullanılan yöntem).

    `yöntem` değerleri:
      * 'timezonefinder' — IANA tz veritabanından kesin (tercih edilen).
      * 'boylam'         — yaklaşık tahmin (±30 dk); endpoint uyarı göstermelidir.
    """
    tam_saat, dakika = _saati_parcala(saat)
    sonuc = tzdb_ofset(lat, lon, yil, ay, gun, tam_saat, dakika)
    if sonuc is not None:
        return sonuc["offset"], "timezonefinder"
    return boylam_tahmini(lon), "boylam"


def utc_ofset_detay(lat: float, lon: float, yil: int, ay: int, gun: int,
                     saat: float = 12.0) -> dict:
    """Şeffaflık için zengin çözüm: ofset + yöntem + timezone adı + belirsizlik."""
    tam_saat, dakika = _saati_parcala(saat)
    sonuc = tzdb_ofset(lat, lon, yil, ay, gun, tam_saat, dakika)
    if sonuc is not None:
        return {"offset": sonuc["offset"], "yontem": "timezonefinder",
                "tz": sonuc["tz"], "belirsiz": sonuc["belirsiz"]}
    return {"offset": boylam_tahmini(lon), "yontem": "boylam",
            "tz": None, "belirsiz": False}


def _normalize(metin: str) -> str:
    """Aksan ve büyük/küçük harf duyarsız karşılaştırma için sadeleştirir."""
    import unicodedata
    m = unicodedata.normalize("NFKD", metin or "")
    return "".join(c for c in m if not unicodedata.combining(c)).lower().strip()


def _sehir_bul_yerel(metin: str, ulke: Optional[str] = None):
    """Yerel cities_db.json'da TAM ad eşleşmesi. Ülke verilmişse filtreler."""
    try:
        from core.utils import sehir_veritabani_yukle
    except Exception:
        try:
            from utils import sehir_veritabani_yukle
        except Exception:
            return []
    try:
        db = sehir_veritabani_yukle()
    except Exception:
        return []

    q = _normalize(metin)
    u_q = _normalize(ulke) if ulke else None
    bulunan = []
    for u in db:
        if u_q and u_q not in _normalize(u):
            continue
        for s, koor in db[u].items():
            if _normalize(s) == q:
                lat = koor["lat"] if isinstance(koor, dict) else koor[0]
                lon = koor["lon"] if isinstance(koor, dict) else koor[1]
                bulunan.append({"lat": lat, "lon": lon, "sehir": s, "ulke": u,
                                "tam_ad": f"{s}, {u}", "kaynak": "yerel"})
    return bulunan


# Cevrimici cozum Nominatim'e gider ve Nominatim 1 istek/sn sinirina sahiptir.
# Ayni sehir 400 kez sorulursa her seferinde 10 sn zaman asimi + HTTP 429 olur.
# Bu yuzden sonucu kisa sure bellekte tutuyoruz. Anahtar, aksan ve buyuk/kucuk
# harf duyarsizlastirilmis sorgudur; degerde zaman damgasi vardir.
_ONBELLEK: dict = {}
_ONBELLEK_TT = 86400.0          # 24 saat: dogum yeri/ofseti degismez
_KILIT = threading.Lock()


def _onbellek_al(anahtar: str):
    with _KILIT:
        kayit = _ONBELLEK.get(anahtar)
        if not kayit:
            return None
        deger, zaman = kayit
        if time.time() - zaman > _ONBELLEK_TT:
            _ONBELLEK.pop(anahtar, None)
            return None
        return deger


def _onbellek_yaz(anahtar: str, deger) -> None:
    with _KILIT:
        _ONBELLEK[anahtar] = (deger, time.time())


def _sehir_bul_geopy(metin: str, ulke: Optional[str] = None) -> Optional[dict]:
    """geopy/Nominatim ile çevrimiçi çözüm. Nominatim önem şekilde sıralar."""
    try:
        from core.utils import _get_geolocator
    except Exception:
        try:
            from utils import _get_geolocator
        except Exception:
            return None
    sorgu = f"{metin}, {ulke}" if ulke else metin
    anahtar = _normalize(sorgu)
    onbellekteki = _onbellek_al(anahtar)
    if onbellekteki is not None:
        return onbellekteki or None      # None ise "bilinen basarisiz" demektir

    try:
        konum = _get_geolocator().geocode(sorgu, language="tr", exactly_one=True)
    except Exception:
        _onbellek_yaz(anahtar, None)
        return None
    if not konum:
        _onbellek_yaz(anahtar, None)
        return None
    adres = konum.raw.get("address", {})
    sehir = (adres.get("city") or adres.get("town") or adres.get("village")
             or adres.get("state") or metin)
    sonuc = {"lat": konum.latitude, "lon": konum.longitude, "sehir": sehir,
             "ulke": adres.get("country", ""), "tam_ad": konum.address,
             "kaynak": "geopy"}
    _onbellek_yaz(anahtar, sonuc)
    return sonuc


def sehir_coz(sehir_adi: str, ulke: Optional[str] = None) -> Optional[dict]:
    """Şehir (+ isteğe bağlı ülke) metnini koordinata çözer.

    Neden bu kadar katmanlı: `cities_db.json` tam adı birden çok ülkede bulunan
    şehirlerde yanlış ülkeyi dönebiliyor. Örnek: veritabanında Almanya'nın
    başkenti Berlin EKSİK; "Berlin" araması yalnızca Berlin, Connecticut
    (ABD) ile eşleşip -5 ofset veriyordu. Bu yüzden:

      * Ülke ipucu varsa yalnızca o ülkede aranır.
      * Tam eşleşme tek ülkedeyse ağa çıkılmaz (hızlı yol: Izmir).
      * Tam eşleşme birden çok ülkeye düşüyorsa belirsizlik vardır; Nominatim
        önem sıralamasıyla devreye girer (Berlin -> Almanya).
    """
    metin = str(sehir_adi or "").strip()
    if len(metin) < 2:
        return None

    # Kullanici tek alana "Berlin, Almanya" yazabilir. Ayirip ulkeyi filtre
    # olarak kullaniriz; boylece belirsiz adlar (Berlin) ulke yazilmadigi
    # surece sessizce yanlis kitaya dusmez.
    if not ulke and "," in metin:
        parcalar = [p.strip() for p in metin.split(",") if p.strip()]
        if len(parcalar) >= 2:
            metin, ulke = parcalar[0], ", ".join(parcalar[1:])

    yerel = _sehir_bul_yerel(metin, ulke)
    if len(yerel) == 1:
        return yerel[0]

    if ulke and len(yerel) > 1:
        return yerel[0]

    cevrimici = _sehir_bul_geopy(metin, ulke)
    if cevrimici:
        return cevrimici

    # Cevrimici cozum basarisiz oldu ve ayni ad BIRDEN FAZLA ÜLKEDE bulunuyor.
    # Burada ilk kaydi secmek sessiz ve kotu bir hatadir: kullanici "Berlin"
    # yazdiginda veritabaninda yalnizca Berlin/Connecticut (ABD) oldugu icin
    # -6 ofset uygulanirdi. Dogru davranis hata dondurup kullaniciya ulke
    # yazdirisini istemektir; yanlis ofsetle hesaplanan 36 puanlik tablo,
    # hic sonuc vermemekten kotudur.
    #
    # ONEMLI: karsilastirma ESLESME sayisi degil ULKE sayisi uzerinden yapilir.
    # Ayni ulkede birden fazla kayit bulunabilir ("Istanbul" ve "İstanbul" gibi
    # takma adlar) ve bunlar belirsizlik degildir.
    if len({m.get("ulke") for m in yerel}) > 1:
        return None
    return yerel[0] if yerel else None


def sehirden_utc_offset(sehir_adi: str, yil: int, ay: int, gun: int,
                        saat: float = 12.0,
                        ulke: Optional[str] = None) -> Tuple[Optional[float], dict]:
    """Doğum şehri + tarihten UTC ofseti çözer.

    Dönen sözlük: {'offset', 'yontem', 'sehir', 'ulke', 'lat', 'lon'}.
    Şehir çözülemezse `offset` None'dur ve çağıran elle girilen ofseti
    kullanmalıdır.
    """
    bilgi = {"offset": None, "yontem": "bulunamadi", "sehir": str(sehir_adi or "").strip(),
             "ulke": str(ulke or ""), "lat": None, "lon": None,
             "tz": None, "belirsiz": False}

    konum = sehir_coz(sehir_adi, ulke)
    if not konum:
        return None, bilgi

    bilgi["sehir"] = konum.get("sehir") or bilgi["sehir"]
    bilgi["ulke"] = konum.get("ulke") or bilgi["ulke"]
    bilgi["lat"] = konum.get("lat")
    bilgi["lon"] = konum.get("lon")

    detay = utc_ofset_detay(konum["lat"], konum["lon"], yil, ay, gun, saat)
    bilgi["offset"] = detay["offset"]
    bilgi["yontem"] = detay["yontem"]
    bilgi["tz"] = detay.get("tz")
    bilgi["belirsiz"] = detay.get("belirsiz", False)
    return detay["offset"], bilgi
