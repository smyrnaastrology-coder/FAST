"""
Yer Bulma Motoru - 4.txt + 5.txt
Mesafe / Yön / Yükseklik
"""
import math

def distance_fixed(lat, degree, house, is_north=True):
    """4.txt: enlem * derece * faktör. Cadent evlerde km, angular metre - txt + global araştırma sentezi"""
    if house in [1,4,7,10]:
        f = 0.2 if is_north else 1.6
        unit = "m"
    elif house in [2,5,8,11]:
        f = 1.6
        unit = "m"
    else:  # 3,6,9,12 cadent - çok uzak
        f = 5
        unit = "km"
    val = lat * degree * f
    # Birim düzeltme: cadent km, ama değer küçükse metreye çevirme yok - global araştırma: cadent = km
    # Angular/succedent'te 1000m üstü km'ye çevir
    if unit == "m" and val > 1000:
        val = val / 1000
        unit = "km"
    if house == 12:
        val = min(val, 200)
    return val, unit

def distance_live(element, house):
    """Canlı: öncü 3.2km değişken 0.8km sabit 0.4km; 1,4,7,10 çarpansız"""
    base = {"cardinal":3.2,"mutable":0.8,"fixed":0.4}
    val = base.get(element,0.8)
    if house not in [1,4,7,10]:
        return None  # formül 2 devreye girer
    return val

def distance_live_advanced(asc_lon, target_lon, element):
    """Formül 2: ASC ↔ belirleyici ilk major açı derecesi * katsayı (20*3.2=64km)"""
    # ilk major açı derecesini bul (0,60,90,120,180 en yakın)
    diff = (target_lon - asc_lon) % 360
    majors = [0,60,90,120,180]
    # en yakın major'a uzaklık
    dist_to_major = min(abs((diff - m + 180) % 360 - 180) for m in majors)
    # ilk major'a kadar derece
    first_major_deg = min(majors, key=lambda m: abs((diff - m + 180) % 360 - 180))
    # basitleştir: diff kadar * katsayı
    base = {"cardinal":3.2,"mutable":0.8,"fixed":0.4}.get(element,0.8)
    return diff * base, f"{diff:.1f}°*{base}km"

def distance_house_cusp(cusp_lon, planet_lon):
    """Ev kesiti ↔ gezegen arası 122° = 122km dairesi (hareketli cisim)"""
    diff = abs((planet_lon - cusp_lon + 360) % 360)
    if diff > 180: diff = 360 - diff
    return diff  # km dairesi

def distance_moon_first_major(moon_lon, moon_speed, target_lon, target_speed):
    """Ay'ın belirleyici ile ilk major açısına kadar derece (22° → 0.5km hareket alanı)"""
    for ang in [0,60,90,120,180]:
        diff = (target_lon - moon_lon) % 360
        d = abs((diff - ang + 180) % 360 - 180)
        # applying mi?
        diff_next = ((target_lon+target_speed) - (moon_lon+moon_speed)) % 360
        d_next = abs((diff_next - ang + 180) % 360 - 180)
        if d_next < d and d <= 10:
            return d, ang
    return None, None

def direction_by_house(house):
    m = {1:"DOĞU",7:"BATI",4:"KUZEY",10:"GÜNEY"}
    if house in m:
        return m[house]
    if 1 < house < 4:
        return "KUZEYDOĞU"
    if 4 < house < 7:
        return "KUZEYBATI"
    if 7 < house < 10:
        return "GÜNEYBATI"
    return "GÜNEYDOĞU"

def height_by_element(element):
    return {"air":"çok yüksek (çatı)","fire":"yüksek (üst kat)","water":"alçak (giriş)","earth":"çok alçak (bodrum)"}.get(element,"")

def house_location_meaning(house):
    meanings = {
        1:"en çok kullanılan yer/eşya",2:"para kasası/cüzdan",3:"tv/telefon/araba anahtarı",
        4:"yaşlı odası/mutfak/depo",5:"oyun/çocuk odası",6:"ilaç/temizlik/kopek",
        7:"eş koltuğu/evlilik cüzdanı",8:"banyo/çöp/kredi/fantezi",9:"pasaport/ders",
        10:"iş evrakı",11:"misafir/teknoloji",12:"yatak/yoga"
    }
    return meanings.get(house,"")
