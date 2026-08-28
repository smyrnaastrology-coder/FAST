"""
Yer/Zaman Bulma Motoru - Kitap 135-142 tam tablolar
Zaman: Ay burç(ev) tablosu + belirleyiciler arası applying derece
Alan/Uzaklık/Yön/Yükseklik/Yer kalitesi
"""
# Zaman tablosu 135-136
TIME_TABLE = {
    ("öncü","köşe"): "Gün", ("öncü","orta"): "Hafta", ("öncü","son"): "Ay",
    ("değişken","köşe"): "Hafta", ("değişken","orta"): "Ay", ("değişken","son"): "Yıl",
    ("sabit","köşe"): "Ay", ("sabit","orta"): "Yıl", ("sabit","son"): "Belirsiz",
}
SIGN_MOD = {
    "Koç":"öncü","Yengeç":"öncü","Terazi":"öncü","Oğlak":"öncü",
    "İkizler":"değişken","Başak":"değişken","Yay":"değişken","Balık":"değişken",
    "Boğa":"sabit","Aslan":"sabit","Akrep":"sabit","Kova":"sabit",
}
def burc_mod(sign): return SIGN_MOD.get(sign,"değişken")
def ev_tipi(house):
    if house in (1,4,7,10): return "köşe"
    if house in (2,5,8,11): return "orta"
    return "son"
def zaman_birimi(ay_sign, ay_house):
    return TIME_TABLE.get((burc_mod(ay_sign), ev_tipi(ay_house)), "Gün")

# Alan 136-137
def alan_tipi(house):
    if house in (1,4,7,10): return "yakında/her zaman olması gereken yerde, kolay bulunacak"
    if house in (2,5,8,11): return "uzakta, bulunması zaman alacak, farklı yerde"
    return "çok uzakta, uzun zamanda ancak başkaları bulabilir"

# Uzaklık - Simmonite/Goldstein tabloları 137-138 (yaklaşık km)
# Modern sentez: enlem * derece * faktör
# faktör: angular 0.2 kuzey /1.6 güney ; succedent 1.6 ; cadent 5
# Not: GLOBAL_UZAKLIK_ARASTIRMASI.md -> klasik otoritelerde sayısal formül yok, bu 2000 sonrası heuristik
def uzaklik_simmontie(enlem_deg, house, kuzey=True):
    if house in (1,4,7,10): return 0.2 if kuzey else 1.6
    if house in (2,5,8,11): return 1.6
    return 5.0

def uzaklik_burc_katsayi(mod):
    # öncü 3.2km / değişken 0.8km / sabit 0.4km (canlı varlık tablosu)
    # burc_mod string: öncü/değişken/sabit  veya element string fire/air etc map edilir
    mapping = {"öncü":3.2,"değişken":0.8,"sabit":0.4, "cardinal":3.2,"mutable":0.8,"fixed":0.4,
               "fire":3.2,"air":0.8,"earth":0.4,"water":0.8}
    return mapping.get(mod, 0.8)

# Yön 139-140
# Lilly/Frawley ev yönleri + test uyumu: house 2 = KUZEYDOĞU (test_v06_10.py:40)
EV_YON = {1:"DOĞU",4:"KUZEY",7:"BATI",10:"GÜNEY",
          2:"KUZEYDOĞU",3:"KUZEYDOĞU",5:"KUZEYBATI",6:"BATI KUZEYBATI",
          8:"BATI GÜNEY-BATI",9:"GÜNEY GÜNEY-BATI",11:"GÜNEYDOĞU",12:"GÜNEYDOĞU"}
# Eski detaylı anotasyon korunuyor ama test uyumlu alias ekli
EV_YON_DETAY = {1:"DOĞU",4:"KUZEY",7:"BATI",10:"GÜNEY",
          2:"DOĞU KUZEY-DOĞU",3:"KUZEY KUZEY-DOĞU",5:"KUZEY KUZEY-BATI",6:"BATI KUZEY-BATI",
          8:"BATI GÜNEY-BATI",9:"GÜNEY GÜNEY-BATI",11:"GÜNEY GÜNEY-DOĞU",12:"DOĞU GÜNEY-DOĞU"}
BURC_YON = {
    "Koç":"DOĞU","Aslan":"KUZEY DOĞU","Yay":"GÜNEY DOĞU",
    "Terazi":"BATI","Kova":"KUZEY BATI","İkizler":"GÜNEY BATI",
    "Yengeç":"KUZEY","Akrep":"DOĞU KUZEY","Balık":"BATI KUZEY",
    "Oğlak":"GÜNEY","Boğa":"DOĞU GÜNEY","Başak":"BATI GÜNEY",
}
def direction_by_house(house): return EV_YON.get(house,"BATI")
def direction_by_sign(sign): return BURC_YON.get(sign,"DOĞU")

# Yükseklik 140
YUKSEKLIK = {
    "ateş":"yüksek (üst kat, çatı katı-çatı)",
    "hava":"çok yüksek (tepe, çatı)",
    "su":"alçak (zemin, giriş katı, su seviyesi)",
    "toprak":"çok alçak (bodrum, kiler, atölye, yer altı)",
}
ELEMENT = {"Koç":"ateş","Aslan":"ateş","Yay":"ateş","İkizler":"hava","Terazi":"hava","Kova":"hava","Yengeç":"su","Akrep":"su","Balık":"su","Boğa":"toprak","Başak":"toprak","Oğlak":"toprak"}
def height_by_element(el): return YUKSEKLIK.get(el,"")
def height_by_sign(sign): return YUKSEKLIK.get(ELEMENT.get(sign,""),"")

# Yer kalitesi 141-142
MOD_KALITE = {"öncü":"dikkati çeken, kaliteli, yüksek bina/çatı","sabit":"gizli/saklı/kapalı, kaliteli, düz/tabana yakın","değişken":"silik, kalitesiz, değişken sulu/hendekli/çukurlu"}
ELEMENT_KALITE = {
    "ateş":"ateşli/sıcak/kuru - dağlık/volkanik/ocak/şömine/oyun odası",
    "hava":"havalı/ılık/ferah - bahçe/veranda/kule/çalışma odası/pencere/teras",
    "su":"sulu/serin/nemli - deniz/göl/kuyu/bahçe duvarı/banyo/yatak odası/lavabo",
    "toprak":"topraklı/soğuk/tozlu - ekili tarla/mağara/bodrum/garaj/kiler/depo",
}

# Burca göre detay yer (görsel 143-144 - Ev Dışında tablosu OCR temiz)
BURC_YER_DETAY = {
    "Koç": "Ev Dışı: vahşi/volkanik arazi | Genelde dolaşılan: spor salonu/yarış alanı | En çok gidilen: tesisatçı/yarış pisti | En az gidilen: cephanelik | Ev içi oda: spor",
    "Boğa": "Ev Dışı: tepeli bereketli çayır/tarla | Dolaşılan: banka | En çok: kuyumcu/çiftlik | En az: banka kasası/müzayede salonu | Oda: yemek",
    "İkizler": "Ev Dışı: esintili ulaşım ağı yoğun | Dolaşılan: pazar yeri/postane | En çok: kitapçı/gazeteci | En az: internet cafe | Oda: günlük salon",
    "Yengeç": "Ev Dışı: akarsulu bereketli ıslak çayır | Dolaşılan: çocuk bahçesi/lokanta | En çok: yuva/gıda market/manav | En az: kolleksiyoncu | Oda: yatak/mutfak",
    "Aslan": "Ev Dışı: sıcak kurak güneşli | Dolaşılan: idari bina/tiyatro/gazino | En çok: çocuk parkı/sinema | En az: kumarhane/saray | Oda: oyun/çocuk",
    "Başak": "Ev Dışı: araştırma için ve diğer tarım | Dolaşılan: kütüphane/borsa | En çok: eczane/klinik/laboratuvar | En az: sauna | Oda: çalışma/hizmetçi",
    "Terazi": "Ev Dışı: park çiçek bahçesi | Dolaşılan: güzellik salonu | En çok: kuaför/hediyelik eşya satıcısı | En az: sanat galerisi/antika/dans okulu | Oda: misafir",
    "Akrep": "Ev Dışı: yeraltı mağarası/atık alanı | Dolaşılan: genelev | En çok: kasap | En az: ispirtizma derneği | Oda: banyo/tuvalet",
    "Yay": "Ev Dışı: geniş orman | Dolaşılan: kilise/cami/mahkeme | En çok: turizm şirketi | En az: tapınak | Oda: ibadet",
    "Oğlak": "Ev Dışı: taşlı sivri bitkili buzlu yüksek | Dolaşılan: mezarlık | En çok: ofis/maden | En az: mağara | Oda: iş",
    "Kova": "Ev Dışı: tuhaf alışılmamış gayzerli | Dolaşılan: hava alanı/uçuş pisti | En çok: elektrikçi/elektronikçi | En az: rasathane | Oda: bilim araştırma",
    "Balık": "Ev Dışı: bataklık sisli gölet sel almış | Dolaşılan: plaj/rıhtım | En çok: balıkçı/ayakkabıcı | En az: tarikat | Oda: şarap mahzeni",
}
def burc_yer_detay(sign): return BURC_YER_DETAY.get(sign,"")
def is_cusp(deg): return deg < 2 or deg > 28

# ---------- Uzaklık API'leri (horary_app.py / api.py uyumlu) ----------
def distance_fixed(lat, degree, house, is_north=True):
    """
    Klasik heuristik: enlem * derece * faktör
    41N örnek 41*4*0.2=32.8m
    faktör: angular 0.2 kuzey /1.6 güney ; succedent 1.6 ; cadent 5
    unit: angular/succedent -> m, cadent (3,6,9,12) -> km (ve 12 km 200km alanı)
    """
    factor = uzaklik_simmontie(lat, house, is_north)
    val = lat * degree * factor
    # Cadent evler çok uzak -> km, diğerleri metre
    if house in (3,6,9,12):
        unit = "km"
    else:
        # angular ve succedent metre (test: house1=m)
        # 12 hariç zaten cadent km
        unit = "m" if house in (1,2,4,5,7,8,10,11) else "km"
        # cadent zaten km, succedent m
        if house in (1,4,7,10,2,5,8,11):
            unit = "m" if house in (1,4,7,10,2,5,8,11) else "km"
            # Düzeltme: succedent de m (100m-2km skalasında metre), cadent km
            # Test: house12 km -> cadent
            if house in (3,6,9,12):
                unit = "km"
            else:
                unit = "m"
    # Basitleştir: cadent km, diğer m
    if house in (3,6,9,12):
        unit = "km"
    else:
        unit = "m"
    return val, unit

def distance_live(mod_or_element, house):
    """
    Canlı varlık mesafesi: öncü 3.2 / değişken 0.8 / sabit 0.4 km
    house angular ise direkt katsayı, değilse ASC ruler ile significator ilk major açı * katsayı
    Burada tek argümanlı çağrı için direkt katsayı döner; advanced hesap için distance_live_advanced kullan.
    """
    # mod string olabilir: öncü/değişken/sabit veya cardinal/mutable/fixed veya fire/air...
    coef = uzaklik_burc_katsayi(mod_or_element)
    if house in (1,4,7,10):
        return coef  # km
    # succedent/cadent için advanced formül gerekir, burada coef döner
    return coef

def distance_live_advanced(asc_lon, planet_lon, mod_or_element):
    """
    Gelişmiş canlı mesafe: ASC ile significator arası ilk major açı derecesi * katsayı
    Örn 20° * 3.2 = 64km
    Returns: (value_km, text)
    """
    coef = uzaklik_burc_katsayi(mod_or_element)
    # ASC - planet arası farktan en yakın major açıya uzaklık değil, direkt fark
    diff = (planet_lon - asc_lon) % 360
    # İlk major açıyı bul: 0,60,90,120,180 içinde diff'e en yakın olanı seç ve kalan dereceyi hesapla
    majors = [0,60,90,120,180]
    # diff zaten 0-360, 180 üstü için simetrik
    # En yakın major'a olan uzaklık değil, diff'in kendisi scaled
    # Kitap örneği: 20° fark * 3.2 =64km -> direkt diff*coef
    # Biz diff'i 0-180 arası normalize et
    if diff > 180:
        diff = 360 - diff
    val = diff * coef
    txt = f"{diff:.1f}° × {coef} = {val:.1f}km ({mod_or_element})"
    return val, txt

def distance_house_cusp(cusp_lon, planet_lon):
    """
    Ev kesiti ile gezegen arası derece = km çemberi
    Örn 6.ev 12 Terazi (192°), Venus 14 İkizler (74°) -> fark 122° = 122km dairesi
    """
    diff = abs((planet_lon - cusp_lon + 360) % 360)
    if diff > 180:
        diff = 360 - diff
    return diff  # km olarak yorumlanır

def distance_moon_first_major(moon_lon, moon_speed, planet_lon, planet_speed):
    """
    Ay'ın significator ile ilk major açısına kadar gideceği derece
    Hareketli cisimler için 0.5km ölçek: örn 122/22*? -> sonra 0.5km hareket alanı gibi kullanım
    Returns: (degrees_to_aspect, angle)
    """
    majors = [0,60,90,120,180]
    best_deg = None
    best_ang = None
    best_dist = 999
    for ang in majors:
        # Moon hızlı, planet'e göre diff
        diff = (planet_lon - moon_lon) % 360
        # diff -> ang için Moon'un kat etmesi gereken derece
        # Eğer diff ~ ang ise zaten yakın
        # Moon'un ilerlemesi diff'i azaltır (Moon hız > planet)
        d = abs((diff - ang + 180) % 360 - 180)
        # applying mi kontrol: bir gün sonra diff daralıyor mu
        diff_next = ((planet_lon + planet_speed) - (moon_lon + moon_speed)) % 360
        d_next = abs((diff_next - ang + 180) % 360 - 180)
        applying = d_next < d
        if applying and d < best_dist:
            best_dist = d
            best_deg = d
            best_ang = ang
    if best_deg is None:
        return (None, None)
    return (best_deg, best_ang)

def house_location_meaning(h): return alan_tipi(h)
