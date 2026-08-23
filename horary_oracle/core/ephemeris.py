"""
Horary Oracle - Core Ephemeris
FBST app.py'den ayrıştırıldı, Regiomontanus zorunlu.
"""
import os
import swisseph as swe
from datetime import datetime

# swisseph ephe yolu - FBST ile aynı, Moshier internal kullan
# swe.set_ephe_path(...) çağrısı yoksa pyswisseph dahili Moshier kullanır (yeterli hassasiyet)
# İstersen horary_oracle/ephe klasörüne .se1 dosyaları koyup aktif edebilirsin
_EPHE_SET = False
for _p in [os.path.join(os.path.dirname(__file__), "..", "ephe"), os.path.join(os.path.dirname(__file__), "..", "..", "ephe")]:
    if os.path.isdir(_p):
        swe.set_ephe_path(os.path.abspath(_p))
        _EPHE_SET = True
        break

# Gezegen ID'leri
PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "NorthNode": swe.MEAN_NODE,
}

SIGNS_TR = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak","Terazi","Akrep","Yay","Oğlak","Kova","Balık"]
SIGNS_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

# Yöneticilik tablosu (karma: Akrep için Pluto öncelikli, sonra Mars - senin "Pluto sonra Mars" talimatın)
DOMICILE = {
    "Koç": "Mars", "Akrep": "Pluto",
    "Boğa": "Venus", "Terazi": "Venus",
    "İkizler": "Mercury", "Başak": "Mercury",
    "Yengeç": "Moon", "Aslan": "Sun",
    "Yay": "Jupiter", "Balık": "Jupiter",
    "Oğlak": "Saturn", "Kova": "Saturn",
}
DOMICILE_TRADITIONAL = {
    "Koç": "Mars", "Akrep": "Mars",
    "Boğa": "Venus", "Terazi": "Venus",
    "İkizler": "Mercury", "Başak": "Mercury",
    "Yengeç": "Moon", "Aslan": "Sun",
    "Yay": "Jupiter", "Balık": "Jupiter",
    "Oğlak": "Saturn", "Kova": "Saturn",
}
EXALTATION = {"Koç":"Sun","Boğa":"Moon","Oğlak":"Mars","Yengeç":"Jupiter","Terazi":"Saturn","Balık":"Venus","Başak":"Mercury"}
DETRIMENT = {"Koç":"Venus","Boğa":"Mars","İkizler":"Jupiter","Yengeç":"Saturn","Aslan":"Saturn","Başak":"Venus","Terazi":"Mars","Akrep":"Venus","Yay":"Mercury","Oğlak":"Moon","Kova":"Sun","Balık":"Mercury"}
FALL = {"Terazi":"Sun","Akrep":"Moon","Yengeç":"Mars","Oğlak":"Jupiter","Koç":"Saturn","Balık":"Mercury","Başak":"Venus"}

# Chaldean saat yöneticisi sırası
HOUR_SEQUENCE = ["Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"]  # en yavaştan en hızlıya

def sign_from_lon(lon: float) -> str:
    return SIGNS_TR[int(lon // 30) % 12]

def sign_en_from_lon(lon: float) -> str:
    return SIGNS_EN[int(lon // 30) % 12]

def deg_in_sign(lon: float) -> float:
    return lon % 30

def to_jd(year, month, day, hour_decimal, lat, lon) -> float:
    """UTC'ye çevrilmiş JD üretir. hour_decimal yerel saat -> UTC dönüşümü dışarıda yapılmalı."""
    # swe.julday gregorian
    jd = swe.julday(year, month, day, hour_decimal, swe.GREG_CAL)
    return jd

def planetary_positions(jd: float, flag=swe.FLG_MOSEPH | swe.FLG_SPEED):
    """Tüm gezegenlerin boy. + hızını döndürür."""
    out = {}
    for name, pid in PLANETS.items():
        # NorthNode için ayrı flag gerekebilir
        res, ret = swe.calc_ut(jd, pid, flag)
        lon = res[0] % 360
        lat = res[1]
        speed = res[3]  # günlük hız
        retro = speed < 0
        out[name] = {"lon": lon, "lat": lat, "speed": speed, "retro": retro, "sign": sign_from_lon(lon), "deg": deg_in_sign(lon)}
    return out

def houses_regiomontanus(jd: float, lat: float, lon: float):
    """
    Horary standardı: Regiomontanus.
    swe.houses_ex ile R sistemi.
    Returns: cusps[12], ascmc[10]  (asc = ascmc[0], mc = ascmc[1])
    """
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'R')
    asc_lon = ascmc[0] % 360
    mc_lon = ascmc[1] % 360
    return {"cusps": [c % 360 for c in cusps], "asc": asc_lon, "mc": mc_lon, "asc_sign": sign_from_lon(asc_lon), "mc_sign": sign_from_lon(mc_lon), "ascmc": ascmc}

def house_of_planet(planet_lon: float, cusps) -> int:
    """Gezegenin evini bul (1-12). Basit cusp arası kontrol."""
    # cusps: 12 eleman, cups[0]=1.ev girişi ... cusps[11]=12.ev girişi
    # Normalize: eğer gezegen ASC'den önceyse 12.ev vb. - basit segment search
    lon = planet_lon % 360
    for i in range(12):
        c1 = cusps[i] % 360
        c2 = cusps[(i+1) % 12] % 360
        # ev dilimi 0-360 sarmalı
        if c1 < c2:
            if c1 <= lon < c2:
                return i+1
        else:  # 360 geçişi (örn 300 -> 20)
            if lon >= c1 or lon < c2:
                return i+1
    return 12

def planetary_hour(jd: float, lat: float, lon: float, weekday: int = None):
    """
    Gezegen saat yöneticisi (Lilly). Günün gün doğumu/gün batımı hesabı gerekir.
    Basit yaklaşım: swe.rise_tran ile sunrise/sunset, sonra 12+12 böl.
    weekday: 0=Pazartesi ... 6=Pazar (Python). Lilly: 0=Pazar,1=Pazartesi...
    """
    # Günün başlangıcı için JD'nin tarihi
    # Bu fonksiyon basitleştirilmiş - tam doğruluk için sunrise/sunset gerekir
    # Şimdilik gezegen saatini saat dilimine göre kaba hesap
    # İleride swe.pheno + rise_trans ile düzeltilecek
    dt = swe.revjul(jd, swe.GREG_CAL)
    # dt: (year, month, day, hour_decimal)
    hour = dt[3]  # UTC hour
    # approximate planetary hour by dividing day into 24 planetary hours starting sunrise
    # Fallback: sequence by weekday ruler
    day_rulers = ["Moon","Mars","Mercury","Jupiter","Venus","Saturn","Sun"]  # Pazartesi->Pazar (modern Mon= Moon)
    # Lilly day rulers: Sunday=Sun, Monday=Moon ... Saturday=Saturn
    # Python weekday 0=Mon -> map
    lilly_day_map = {0:"Moon",1:"Mars",2:"Mercury",3:"Jupiter",4:"Venus",5:"Saturn",6:"Sun"}
    if weekday is not None:
        day_ruler = lilly_day_map[weekday]
    else:
        day_ruler = "Sun"
    # saat sırası day_ruler'dan başlar
    start_idx = HOUR_SEQUENCE.index(day_ruler) if day_ruler in HOUR_SEQUENCE else 0
    # gün doğumundan itibaren saat say
    # basitleştirme: gece/gündüz eşit 12 saat varsay
    hour_of_day = int(hour) % 24
    hour_ruler = HOUR_SEQUENCE[(start_idx + hour_of_day) % 7]
    return {"day_ruler": day_ruler, "hour_ruler": hour_ruler, "note": "approx - sunrise/sunset ile netleştirilecek"}

def essentials(lon: float, planet: str) -> dict:
    """Gezegenin bulunduğu burçtaki asalet/zarar durumu."""
    sign = sign_from_lon(lon)
    domicile_ruler = DOMICILE.get(sign)
    exalt_ruler = EXALTATION.get(sign)
    detriment_ruler = DETRIMENT.get(sign)
    fall_ruler = FALL.get(sign)
    return {
        "sign": sign,
        "domicile": planet == domicile_ruler,
        "exaltation": planet == exalt_ruler,
        "detriment": planet == detriment_ruler,
        "fall": planet == fall_ruler,
        "ruler": domicile_ruler,
        "exalt_ruler": exalt_ruler,
    }

def reception_score(planet_lon: float, planet: str, other_planet: str) -> int:
    """Reception puanı: planet, other_planet'in asaleti içinde mi? Lilly 5/4/3/2/1"""
    # Bu fonksiyon tek gezegen için - çift yönlü reception ayrıca hesaplanır
    # Şimdilik sadece domicile/exaltation
    e = essentials(planet_lon, other_planet)
    # Eğer planet, other_planet'in domicile burcundaysa -> other_planet planet'i seviyor (+5)
    # Yani reception: other_planet -> planet sevgisi
    # Kullanım: reception_score(mars_lon, "Mars", "Venus") -> Mars Venüs'ün burcunda mı?
    sign = e["sign"]
    if DOMICILE.get(sign) == other_planet:
        return 5
    if EXALTATION.get(sign) == other_planet:
        return 4
    # triplicity/term/face için tablo eklenebilir
    return 0
