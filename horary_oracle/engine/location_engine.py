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
# Yersel enlem × ev tablosu
def uzaklik_simmontie(enlem_deg, house, kuzey=True):
    # güney için farklı sütun yok kitapta, kuzey tablosu kullanılıyor
    if house in (1,4,7,10): return 0 if kuzey else 0.2 # Sıfır/Yakın
    if house in (2,5,8,11):
        return 1.6 if kuzey else 5.0
    return 5.0 if kuzey else 111.1

def uzaklik_burc_katsayi(mod):
    return {"öncü":3.2,"değişken":0.8,"sabit":0.4}.get(mod,0.8)

# Yön 139-140
EV_YON = {1:"DOĞU",4:"KUZEY",7:"BATI",10:"GÜNEY",
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
# İki burç arası ise iki şey arasında/arkasında/sıkışmış/eşikte
def is_cusp(deg): return deg < 2 or deg > 28
# Ay insani (İkizler,Başak,Terazi,Kova) vs hayvani (Koç,Boğa,Aslan,Yay,Oğlak) vs diğer

# Eski API uyumu için alias
def distance_fixed(lat, degree, house, is_north=True):
    base = uzaklik_simmontie(0, house, is_north)
    # basit fallback
    val = degree * uzaklik_burc_katsayi(burc_mod("Koç"))
    return val, "km"
def distance_live(element, house): return uzaklik_burc_katsayi(element)
def distance_live_advanced(a,b,c): return (0,"")
def distance_house_cusp(a,b): return abs(a-b)%360
def distance_moon_first_major(a,b,c,d): return (None,None)
def house_location_meaning(h): return alan_tipi(h)
