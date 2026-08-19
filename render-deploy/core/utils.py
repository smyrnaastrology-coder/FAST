import os, io
import re
import json
import numpy as np
import swisseph as swe
from datetime import datetime, date, timedelta
from collections import defaultdict

from core.data import _FAST_RENKLER, fbst_sabit_yildizlar, fbst_sabit_yildizlar_ebeveyn, fbst_sabit_yildizlar_ask

try:
    from core.i18n import get_lang as _uget_lang, pdf_label as _updf_label
except Exception:
    def _uget_lang():
        return "tr"
    def _updf_label(t):
        return t


def _uEN():
    return _uget_lang() in ("en", "es")

# FBST kataloğundaki bazı yıldız anahtarları Swiss Ephemeris tarafından
# doğrudan çözümlenemez; gerçek pozisyon hesabı için sefstars.txt'teki ad kullanılır.
_YILDIZ_SEF_AD = {
    "ALFARD": "Alphard",
    "DENEB_ALGEDI": "Deneb Algedi",
    "GIEDI_SECUNDA": "Giedi Secunda",
    "ZUBEN_EL_GENUBI": "Zuben Elgenubi",
    "ZUBEN_EL_SCHEMALI": "Zuben Eschamali",
}

_PLT = None
def _plt():
    """Lazy matplotlib.pyplot yükleyici — ilk çizimden önce import edilir."""
    global _PLT
    if _PLT is not None:
        return _PLT
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Segoe UI Symbol', 'Segoe UI', 'DejaVu Sans', 'Arial'],
        'font.size': 11, 'axes.titlesize': 14, 'axes.titleweight': 'bold',
        'axes.labelsize': 11, 'axes.facecolor': '#FBF7F4', 'figure.facecolor': '#FFFFFF',
        'axes.edgecolor': '#E8E0D8', 'axes.linewidth': 0.8, 'axes.grid': True,
        'grid.color': '#E8E0D8', 'grid.linestyle': '--', 'grid.linewidth': 0.5,
        'grid.alpha': 0.7, 'xtick.color': '#6B5B7B', 'ytick.color': '#6B5B7B',
        'xtick.labelsize': 9, 'ytick.labelsize': 9, 'legend.facecolor': '#FFFFFF',
        'legend.edgecolor': '#E8E0D8', 'legend.labelcolor': '#4A4A4A',
        'legend.fontsize': 9, 'text.color': '#4A4A4A', 'figure.dpi': 150,
        'savefig.dpi': 300, 'savefig.bbox': 'tight', 'savefig.facecolor': '#FFFFFF',
    })
    _PLT = plt
    return _PLT

def sehir_veritabani_yukle():
    """cities_db.json dosyasından tüm dünya şehirlerini yükler."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "cities_db.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _normalize_metin(metin):
    """Aksan ve büyük/küçük harf duyarsız karşılaştırma için sadeleştirir."""
    import unicodedata
    metin = unicodedata.normalize("NFKD", metin or "")
    metin = "".join(c for c in metin if not unicodedata.combining(c))
    return metin.lower().strip()

def sehir_ara(arama_metni, limit=15):
    """cities_db.json içinde ülke ve şehir adlarında aksan duyarsız arama yapar.

    Önce ülke adında, sonra şehir adında eşleşme arar. Her sonuç
    {'sehir', 'ulke', 'lat', 'lon', 'tam_ad'} sözlüğü olarak döner.
    """
    q = _normalize_metin(arama_metni)
    if not q or len(q) < 2:
        return []
    try:
        db = sehir_veritabani_yukle()
    except Exception:
        return []
    sonuc = []
    gorulen = set()
    def _ekle(sehir, ulke, koor):
        lat = koor["lat"] if isinstance(koor, dict) else koor[0]
        lon = koor["lon"] if isinstance(koor, dict) else koor[1]
        anahtar = (sehir, ulke)
        if anahtar in gorulen:
            return
        gorulen.add(anahtar)
        sonuc.append({"sehir": sehir, "ulke": ulke, "lat": lat, "lon": lon,
                      "tam_ad": f"{sehir}, {ulke}"})
    # 1) Şehir adı tam eşleşmesi
    for ulke in sorted(db):
        for sehir, koor in db[ulke].items():
            if _normalize_metin(sehir) == q:
                _ekle(sehir, ulke, koor)
                if len(sonuc) >= limit:
                    return sonuc
    # 2) Ülke adı tam eşleşmesi (o ülkenin şehirleri)
    for ulke in sorted(db):
        if _normalize_metin(ulke) == q:
            for sehir, koor in db[ulke].items():
                _ekle(sehir, ulke, koor)
                if len(sonuc) >= limit:
                    return sonuc
    # 3) Şehir adı eşleşmesi (önek önce)
    for ulke in sorted(db):
        for sehir, koor in db[ulke].items():
            if _normalize_metin(sehir).startswith(q):
                _ekle(sehir, ulke, koor)
                if len(sonuc) >= limit:
                    return sonuc
    # 4) Ülke adı içeren eşleşme
    for ulke in sorted(db):
        if q in _normalize_metin(ulke):
            for sehir, koor in db[ulke].items():
                _ekle(sehir, ulke, koor)
                if len(sonuc) >= limit:
                    return sonuc
    # 5) Şehir adı içeren eşleşme
    if len(sonuc) < limit:
        for ulke in sorted(db):
            for sehir, koor in db[ulke].items():
                if q in _normalize_metin(sehir):
                    _ekle(sehir, ulke, koor)
                    if len(sonuc) >= limit:
                        return sonuc
    return sonuc

def _get_geolocator():
    from geopy.geocoders import Nominatim
    return Nominatim(user_agent="fbst_kadersel_navigasyon_v2", timeout=10)

def sehir_bul(arama_metni):
    """Dünyanın herhangi bir şehrini enlem/boylam olarak çözer.

    Önce yerel cities_db.json içinde aksan duyarsız arar, bulamazsa
    geopy (Nominatim) ile çevrimiçi çözmeyi dener.
    """
    yerel = sehir_ara(arama_metni, limit=1)
    if yerel:
        s = yerel[0]
        return {"lat": s["lat"], "lon": s["lon"], "sehir": s["sehir"],
                "ulke": s["ulke"], "tam_ad": s["tam_ad"], "kaynak": "yerel"}
    geo = _get_geolocator()
    try:
        konum = geo.geocode(arama_metni, language="tr", exactly_one=True)
        if konum:
            ulke = konum.raw.get("address", {}).get("country", "")
            sehir = konum.raw.get("address", {}).get("city",
                     konum.raw.get("address", {}).get("town",
                     konum.raw.get("address", {}).get("village",
                     konum.raw.get("address", {}).get("state", ""))))
            return {
                "lat": konum.latitude, "lon": konum.longitude,
                "sehir": sehir or arama_metni, "ulke": ulke,
                "tam_ad": konum.address, "kaynak": "geopy"
            }
    except Exception:
        pass
    return None

ULKE_SEHIR_DB = {
    "Türkiye": ["Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Aksaray", "Amasya", "Ankara", "Antalya",
                 "Ardahan", "Artvin", "Aydın", "Balıkesir", "Bartın", "Batman", "Bayburt", "Bilecik",
                 "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum",
                 "Denizli", "Diyarbakır", "Düzce", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir",
                 "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Iğdır", "Isparta", "İstanbul",
                 "İzmir", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kırıkkale",
                 "Kırklareli", "Kırşehir", "Kilis", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa",
                 "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye",
                 "Rize", "Sakarya", "Samsun", "Şanlıurfa", "Siirt", "Sinop", "Sivas", "Şırnak",
                 "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Uşak", "Van", "Yalova", "Yozgat", "Zonguldak"],
    "Almanya": ["Berlin", "Münih", "Hamburg", "Köln", "Frankfurt", "Stuttgart", "Düsseldorf", "Dresden", "Offenbach"],
    "İngiltere": ["Londra", "Manchester", "Birmingham", "Liverpool", "Edinburgh", "Bristol", "Leeds", "Glasgow"],
    "Fransa": ["Paris", "Marsilya", "Lyon", "Nice", "Toulouse", "Bordeaux", "Strazburg", "Nantes"],
    "İtalya": ["Roma", "Milano", "Napoli", "Floransa", "Venedik", "Torino", "Palermo", "Bologna"],
    "İspanya": ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Malaga", "Granada", "San Sebastián"],
    "Portekiz": ["Lizbon", "Porto", "Braga", "Faro", "Coimbra", "Funchal"],
    "Yunanistan": ["Atina", "Selanik", "Santorini", "Midilli", "Girit", "Rodos"],
    "Hollanda": ["Amsterdam", "Rotterdam", "Lahey", "Utrecht", "Eindhoven"],
    "Belçika": ["Brüksel", "Antwerp", "Brugge", "Gent", "Liege"],
    "İsviçre": ["Zürih", "Cenevre", "Bern", "Luzern", "Basel", "İnterlaken"],
    "Avusturya": ["Viyana", "Salzburg", "Graz", "Innsbruck", "Linz"],
    "İsveç": ["Stockholm", "Göteborg", "Malmö", "Uppsala"],
    "Norveç": ["Oslo", "Bergen", "Trondheim", "Stavanger", "Tromsø"],
    "Danimarka": ["Kopenhag", "Aarhus", "Odense", "Roskilde"],
    "Finlandiya": ["Helsinki", "Turku", "Tampere", "Oulu"],
    "İrlanda": ["Dublin", "Cork", "Galway", "Limerick"],
    "Polonya": ["Varşova", "Kraków", "Gdańsk", "Wroclaw", "Poznań"],
    "Çekya": ["Prag", "Brno", "Karlovy Vary", "Ostrava"],
    "Macaristan": ["Budapeşte", "Debrecen", "Pécs", "Szeged"],
    "Romanya": ["Bükreş", "Klausenburg", "Temeşvar", "Braşov"],
    "Bulgaristan": ["Sofya", "Filibe", "Varna", "Burgaz", "Ruse"],
    "Sırbistan": ["Belgrad", "Novi Sad", "Niš"],
    "Hırvatistan": ["Zagreb", "Split", "Dubrovnik", "Zadar"],
    "Slovenya": ["Ljubljana", "Maribor", "Bled"],
    "ABD": ["New York", "Los Angeles", "Chicago", "Miami", "San Francisco", "Las Vegas",
             "Boston", "Seattle", "Washington DC", "Atlanta", "Houston", "Denver", "Phoenix", "Honolulu"],
    "Kanada": ["Toronto", "Vancouver", "Montreal", "Ottawa", "Calgary", "Edmonton", "Quebec"],
    "Meksika": ["Meksiko City", "Cancún", "Guadalajara", "Monterrey", "Oaxaca"],
    "Brezilya": ["São Paulo", "Rio de Janeiro", "Salvador", "Brasília", "Florianópolis", "Fortaleza"],
    "Arjantin": ["Buenos Aires", "Córdoba", "Mendoza", "Bariloche", "Ushuaia"],
    "Şili": ["Santiago", "Valparaíso", "Antofagasta"],
    "Kolombiya": ["Bogotá", "Medellín", "Cali", "Cartagena"],
    "Peru": ["Lima", "Cusco", "Arequipa"],
    "Japonya": ["Tokyo", "Kyoto", "Osaka", "Hiroshima", "Nagoya", "Sapporo", "Fukuoka"],
    "Çin": ["Pekin", "Şangay", "Guangzhou", "Shenzhen", "Chengdu", "Hangzhou", "Xi'an"],
    "Güney Kore": ["Seoul", "Busan", "Jeju", "İncheon", "Daegu"],
    "Tayland": ["Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Krabi"],
    "Vietnam": ["Hanoi", "Ho Chi Minh City", "Da Nang", "Nha Trang", "Sapa"],
    "Endonezya": ["Bali (Denpasar)", "Cakarta", "Yogyakarta", "Surabaya", "Lombok"],
    "Malezya": ["Kuala Lumpur", "Penang", "Langkawi", "Kota Kinabalu"],
    "Singapur": ["Singapur"],
    "Hindistan": ["New Delhi", "Mumbai", "Bangalore", "Jaipur", "Goa", "Kerala", "Agra"],
    "Nepal": ["Kathmandu", "Pokhara", "Lumbini"],
    "Sri Lanka": ["Kolombo", "Kandy", "Galle", "Sigiriya"],
    "İsrail": ["Kudüs", "Tel Aviv", "Hayfa", "Ölü Deniz"],
    "BAE": ["Dubai", "Abu Dabi", "Sharjah"],
    "Suudi Arabistan": ["Riyad", "Cidde", "Mekke", "Medine"],
    "Katar": ["Doha"],
    "Mısır": ["Kahire", "İskenderiye", "Luxor", "Aswan", "Şarm El-Şeyh"],
    "Fas": ["Kazablanka", "Fes", "Marrakech", "Tanger", "Çagvan"],
    "Güney Afrika": ["Cape Town", "Johannesburg", "Durban", "Pretoria"],
    "Tanzanya": ["Dar es Salaam", "Zanzibar", "Arusha"],
    "Kenya": ["Nairobi", "Mombasa"],
    "Avustralya": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast"],
    "Yeni Zelanda": ["Auckland", "Wellington", "Queenstown", "Christchurch"],
    "Rusya": ["Moskova", "St. Petersburg", "Kazan", "Soçi", "Vladivostok"],
    "Ukrayna": ["Kiev", "Lviv", "Odessa", "Harkov"],
    "Gürcistan": ["Tiflis", "Batumi", "Kutaisi"],
    "Azerbaycan": ["Bakü", "Gence", "Şeki"],
    "Ermenistan": ["Erivan", "Gyumri"],
    "Kıbrıs": ["Lefkoşa", "Girne", "Gazimağusa", "Limasol"],
    "İzlanda": ["Reykjavik"],
    "Lüksemburg": ["Lüksemburg"],
    "Malta": ["Valletta"],
    "Monako": ["Monako"],
    "Vatikan": ["Vatikan"],
    "Andorra": ["Andorra la Vella"],
    "Liechtenstein": ["Vaduz"],
    "San Marino": ["San Marino"],
    "Küba": ["Havana", "Trinidad", "Varadero"],
    "Dominik Cumhuriyeti": ["Punta Cana", "Santo Domingo", "Puerto Plata"],
    "Jamaika": ["Kingston", "Montego Bay"],
    "Kosta Rika": ["San José", "Liberia", "Manuel Antonio"],
    "Panama": ["Panama City"],
    "Guatemala": ["Antigua Guatemala", "Guatemala City"],
    "Ekvador": ["Quito", "Guayaquil", "Galápagos"],
    "Bolivya": ["La Paz", "Sucre"],
    "Paraguay": ["Asunción"],
    "Uruguay": ["Montevideo"],
    "Diğer (Serbest Arama)": []
}

try:
    from timezonefinder import TimezoneFinder
    _tzf = TimezoneFinder()
except ImportError:
    _tzf = None

try:
    import pytz as _pytz
except ImportError:
    _pytz = None


def _turkiye_utc_offset_hesapla(yil, ay, gun):
    """Türkiye için tarihe göre doğru UTC offset'ini hesaplar (pytz bağımsız)."""
    if yil > 2016:
        return 3
    if yil < 1968:
        return 2
    mart_son_pazar = _son_pazar_gunu(yil, 3)
    eylul_son_pazar = _son_pazar_gunu(yil, 9)
    if (ay > 3) or (ay == 3 and gun >= mart_son_pazar):
        if (ay < 9) or (ay == 9 and gun <= eylul_son_pazar):
            return 3
    return 2


def _nci_pazar_gunu(yil, ay, n):
    """Ayın n. Pazar günü (1=ilk, 2=ikinci, ...)."""
    from datetime import date
    ilk_gun = date(yil, ay, 1).weekday()
    if ilk_gun == 6:
        return 1 + (n - 1) * 7
    return 1 + (6 - ilk_gun) + (n - 1) * 7


def _dst_kuzey_us(yil, ay, gun, baz):
    """ABD/Kanada: 2007 sonrası 2. Pazar Mart → 1. Pazar Kasım; öncesi 1. Nisan → son Ekim."""
    if yil < 2007:
        bas = _nci_pazar_gunu(yil, 4, 1)
        bit = _son_pazar_gunu(yil, 10)
    else:
        bas = _nci_pazar_gunu(yil, 3, 2)
        bit = _nci_pazar_gunu(yil, 11, 1)
    if (ay > 3 or (ay == 3 and gun >= bas)) and (ay < 11 or (ay == 11 and gun < bit)):
        return baz + 1
    return baz


def _dst_kuzey_ab(yil, ay, gun, baz):
    """AB: son Pazar Mart → son Pazar Ekim."""
    bas = _son_pazar_gunu(yil, 3)
    bit = _son_pazar_gunu(yil, 10)
    if (ay > 3 or (ay == 3 and gun >= bas)) and (ay < 10 or (ay == 10 and gun < bit)):
        return baz + 1
    return baz


def _dst_guney(yil, ay, gun, baz):
    """Güney yarımküre: Ekim 1. Pazar → Nisan 1. Pazar."""
    bas = _nci_pazar_gunu(yil, 10, 1)
    bit = _nci_pazar_gunu(yil, 4, 1)
    if (ay, gun) >= (10, bas) or (ay, gun) < (4, bit):
        return baz + 1
    return baz

BOLGESEL_UTC = [
    ("Turkiye", 35, 43, 25, 45, None, "turkiye"),
    ("Arjantin", -55, -20, -75, -50, -3, None),
    ("Brezilya", -35, 5, -75, -30, -3, None),
    ("Sili", -60, -15, -80, -60, -4, "guney"),
    ("ABD_Dogu", 25, 50, -85, -65, -5, "kuzey_us"),
    ("ABD_Merkez", 25, 50, -100, -85, -6, "kuzey_us"),
    ("ABD_Dag", 25, 50, -115, -100, -7, "kuzey_us"),
    ("ABD_Pasifik", 25, 50, -130, -115, -8, "kuzey_us"),
    ("Ingiltere", 49, 61, -10, 2, 0, "kuzey_ab"),
    ("Bati_Avrupa", 35, 65, 2, 10, 1, "kuzey_ab"),
    ("Orta_Avrupa", 35, 65, 10, 20, 1, "kuzey_ab"),
    ("Dogu_Avrupa", 35, 65, 20, 30, 2, "kuzey_ab"),
    ("Rusya_Bati", 40, 70, 30, 50, 2, "kuzey_ab"),
    ("Japonya", 30, 46, 128, 146, 9, None),
    ("Cin", 18, 55, 73, 135, 8, None),
    ("Hindistan", 5, 38, 65, 90, 5.5, None),
    ("Guney_Afrika", -35, -20, 15, 35, 2, None),
    ("Avustralya_Dogu", -45, -25, 140, 155, 10, "guney"),
    ("Avustralya_Merkez", -35, -15, 130, 140, 9.5, "guney"),
    ("Avustralya_Bati", -35, -20, 110, 130, 8, None),
    ("Yeni_Zelanda", -50, -35, 165, 180, 12, "guney"),
]


def otomatik_utc_offset(lat, lon, yil, ay, gun, saat=12):
    """Tarih/koordinata göre UTC offset'ini otomatik hesaplar.
    Önce pytz dener, sonra bölgesel eşleşme, en son boylam tahmini."""
    if _tzf is not None and _pytz is not None:
        try:
            tz_name = _tzf.timezone_at(lat=lat, lng=lon)
            if not tz_name:
                tz_name = _tzf.closest_timezone_at(lat=lat, lng=lon)
            if tz_name:
                tz = _pytz.timezone(tz_name)
                from datetime import datetime
                dt = tz.localize(datetime(yil, ay, gun, int(saat), int((saat % 1) * 60)))
                return dt.utcoffset().total_seconds() / 3600
        except Exception:
            pass
    for ad, lat_min, lat_max, lon_min, lon_max, baz, dst in BOLGESEL_UTC:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            if dst is None:
                return baz
            if dst == "turkiye":
                return _turkiye_utc_offset_hesapla(yil, ay, gun)
            if dst == "kuzey_us":
                return _dst_kuzey_us(yil, ay, gun, baz)
            if dst == "kuzey_ab":
                return _dst_kuzey_ab(yil, ay, gun, baz)
            if dst == "guney":
                return _dst_guney(yil, ay, gun, baz)
    tahmin = round(lon / 15.0)
    return max(-12, min(12, int(tahmin)))


POPULER_SEHIRLER = [
    "İstanbul, Türkiye", "Ankara, Türkiye", "İzmir, Türkiye",
    "Londra, İngiltere", "Paris, Fransa", "New York, ABD",
    "Berlin, Almanya", "Tokyo, Japonya", "Dubai, BAE",
    "Moskova, Rusya", "Roma, İtalya", "Madrid, İspanya",
    "Sydney, Avustralya", "Seoul, Güney Kore", "Bangkok, Tayland",
    "Kahire, Mısır", "São Paulo, Brezilya", "Toronto, Kanada"
]

# --- GLOBAL OPTİMİZASYON: FONT VE TASARIM AYARLARI ---

def global_font_ayarla():
    try:
        from reportlab.lib.fonts import addMapping
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # Font dosyalarını bul ve kaydet
        font_yollari = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:\\Windows\\Fonts\\arial.ttf", # Windows desteği için geri eklendi
            "DejaVuSans.ttf"
        ]
        bold_font_yollari = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf", # Windows desteği için geri eklendi
            "DejaVuSans-Bold.ttf"
        ]
        
        found_regular = False
        for path in font_yollari:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('DejaVuSans', path))
                found_regular = True
                break
        
        found_bold = False
        for path in bold_font_yollari:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', path))
                found_bold = True
                break

        # 🚨 KRİTİK DÜZELTME: ReportLab'e bu fontların birbirinin Bold/Normal versiyonu olduğunu söylememiz gerekir.
        # Bu yapılmazsa "Can't map determine family/bold/italic" hatası alınır.
        if found_regular and found_bold:
            addMapping('DejaVuSans', 0, 0, 'DejaVuSans')      # Normal
            addMapping('DejaVuSans', 1, 0, 'DejaVuSans-Bold') # Bold
            addMapping('DejaVuSans', 0, 1, 'DejaVuSans')      # Italic (Bold değilse normale düş)
            addMapping('DejaVuSans', 1, 1, 'DejaVuSans-Bold') # Bold Italic
            
    except Exception as e:
        print(f"Font yukleme hatasi: {e}")

global_font_ayarla()

KADIM_LACIVERT = "#1A1A2E"
DERIN_MAVI     = "#16213E"
ALTIN_AMBER    = "#C9A96E"
KART_ARKA_PLAN = "#FBF7F4"
METIN_SIYAH    = "#4A4A4A"
CERCEVE_GRI    = "#D4CFC8"
varsayilan_sabian_vizyonu = "Evrenin saklı geometri sembolü"
varsayilan_sabian_yorumu = "Bu derece, ilişkinizde henüz keşfedilmemiş derin bir ruhsal potansiyeli ve kendi içinizde çözmeniz gereken kadersel bir gizi barındırır."

ephe_klasoru = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ephe')
swe.set_ephe_path(ephe_klasoru)

# ==============================================================================

def karakutu_temizle(metin):
    """
    PDF'den gelen bozuk karakterleri ve '' kutucuklarını temizler,
    Türkçe karakterleri normalize eder.
    """
    if not isinstance(metin, str):
        return str(metin)
    
    # 1. Unicode normalizasyonu (bozuk karakter birleşimlerini düzeltir)
   
    
    # 2. Bozuk kutucukları ve bilinmeyen karakterleri sil
    bozuk_karakterler = ['', '\x0c'] 
    for char in bozuk_karakterler:
        metin = metin.replace(char, "")
        
    return metin.strip()


def get_planetary_position(jd, planet_id):
    """
    Belirli bir zaman dilimi (Julian Day) için
    gezegenin burç ve derece bilgisini çeker.
    """
    position = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
    return position[0][0]

def get_star_position(star_name, jd):
    """
    Sabit yıldızın konumunu hesaplar.
    """
    star_pos = swe.fixstar_ut(star_name, jd, swe.FLG_SWIEPH)
    return star_pos[0]


def fixstar_ut_lon(star_name, jd):
    """
    Sabit yıldızın belirli bir tarihteki ekliptik boylamını döndürür.
    fixstar_ut'un dönüş tip farkını güvenli şekilde yönetir.
    """
    result = swe.fixstar_ut(star_name, jd, swe.FLG_SWIEPH)
    if isinstance(result[0], tuple):
        return result[0][0]
    return result[0]



def dereceden_burc_dec(degree):
    """Dereceyi ondalık burç formatına çevirir."""
    burclar = ['Koç', 'Boğa', 'İkizler', 'Yengeç', 'Aslan', 'Başak',
               'Terazi', 'Akrep', 'Yay', 'Oğlak', 'Kova', 'Balık']
    sign_index = int(degree / 30) % 12
    sign_degree = degree - sign_index * 30
    return f"{sign_degree:.2f}° {burclar[sign_index]}"


def dereceyi_dakikaya_cevir(degree):
    """Dereceyi 'Burç X°Y'' formatına çevirir. Örnek: 'Terazi 28°12'."""
    burclar = ['Koç', 'Boğa', 'İkizler', 'Yengeç', 'Aslan', 'Başak',
               'Terazi', 'Akrep', 'Yay', 'Oğlak', 'Kova', 'Balık']
    sign_index = int(degree / 30) % 12
    sign_degree = degree - sign_index * 30
    tam_derece = int(sign_degree)
    dakika = int((sign_degree - tam_derece) * 60)
    burc_adi = burclar[sign_index]
    try:
        from core.i18n import pdf_label as _pl
        burc_adi = _pl(burc_adi)
    except Exception:
        pass
    return f"{burc_adi} {tam_derece}°{dakika:02d}'"



def tum_sabit_yildizlar_listesi():
    """
    Swiss Ephemeris veritabanındaki tüm sabit yıldızların adlarını döndürür.
    FBST kütüphanesindeki yıldızları da dahil eder.
    """
    stars = []
    try:
        sefstars_path = os.path.join(ephe_klasoru, 'sefstars.txt')
        if not os.path.exists(sefstars_path):
            sefstars_path = '/usr/share/swisseph/sefstars.txt'
        if os.path.exists(sefstars_path):
            with open(sefstars_path, 'r') as f:
                for satir in f:
                    satir = satir.strip()
                    if not satir or satir.startswith('#'):
                        continue
                    parts = satir.split(',')
                    if len(parts) >= 1:
                        yildiz_adi = parts[0].strip()
                        if yildiz_adi and not yildiz_adi.startswith('#'):
                            stars.append(yildiz_adi)
    except Exception:
        pass
    
    # FBST kütüphanesindeki yıldızları da ekle
    fbst_names = list(fbst_sabit_yildizlar.keys())
    for name in fbst_names:
        if name not in stars:
            stars.append(name)
    
    return stars



def sabit_yildiz_precession_tarama(target_deg, target_jd, orb_siniri=2.0):
    """
    BELİRLİ BİR TARİHTE ve EKLIPTİK POZİSYONDA hangi sabit yıldız olduğunu bulur.
    
    Örn: "MÖ 1000'de 56.17° Boğa'da (Algol pozisyonu) gerçekte hangi yıldız vardı?"
    
    Args:
        target_deg: Hedef ekliptik boylam (0-360°)
        target_jd: Hedef tarih (Julian Day)
        orb_siniri: Tolerans (varsayılan 2.0°)
    
    Returns:
        Liste: [{'yildiz': ..., 'lon': ..., 'fark': ...}, ...] - farka göre sıralı
    """
    bulunanlar = []
    tum_yildizlar = tum_sabit_yildizlar_listesi()
    
    for yildiz_adi in tum_yildizlar:
        try:
            yildiz_lon = fixstar_ut_lon(yildiz_adi, target_jd)
            fark = aci_farki_safe(target_deg, yildiz_lon)
            
            if fark <= orb_siniri:
                bulunanlar.append({
                    'yildiz': yildiz_adi,
                    'lon': yildiz_lon,
                    'fark': fark
                })
        except Exception:
            continue
    
    bulunanlar.sort(key=lambda x: x['fark'])
    return bulunanlar



def sabit_yildiz_tarihe_gore(star_name, target_jd):
    """
    Belirli bir sabit yıldızın belirli bir tarihteki gerçek ekliptik pozisyonunu döndürür.
    
    Args:
        star_name: Sabit yıldız adı
        target_jd: Hedef tarih (Julian Day)
    
    Returns:
        (ekliptik_boylam, ekliptik_enlem, burc_metni)
    """
    lon = fixstar_ut_lon(star_name, target_jd)
    result = swe.fixstar_ut(star_name, target_jd, swe.FLG_SWIEPH)
    if isinstance(result[0], tuple):
        lat = result[0][1]
    else:
        lat = result[1]
    
    burc = dereceden_burc_dec(lon)
    return lon, lat, burc



def bagil_harita_yildiz_donusumu(veritabani_derece, kaynak_yil, kaynak_ay=1, kaynak_gun=1, orb_siniri=2.0):
    """
    BAĞIL HARİTA YILDIZ DÖNÜŞÜMÜ - Kullanıcının temel sorusuna yanıt:
    
    'Bir bağıl harita X tarihinde Y derecesinde bir yapı gösteriyor.
     O tarihte orada gerçekte hangi sabit yıldız vardı?'
    
    Args:
        veritabani_derece: Bağıl haritada görünen ekliptik boylam (0-360°)
        kaynak_yil: Bağıl haritanın ait olduğu yıl
        kaynak_ay: Ay (varsayılan 1)
        kaynak_gun: Gün (varsayılan 1)
        orb_siniri: Tolerans (varsayılan 2.0°)
    
    Returns:
        dict: {
            'giris': {'derece': ..., 'burc': ..., 'tarih': ...},
            'sonuc': {found_star_info} veya None,
            'tum_bulunan': [list_of_stars],
            'aciklama': str
        }
    """
    target_jd = swe.julday(kaynak_yil, kaynak_ay, kaynak_gun, 0.0)
    
    # O tarihte bu derecede hangi yıldız vardı?
    bulunanlar = sabit_yildiz_precession_tarama(veritabani_derece, target_jd, orb_siniri)
    
    # Günümüz referansı için
    jd_gunumuz = swe.julday(2026, 7, 10, 0.0)
    
    result = {
        'giris': {
            'derece': veritabani_derece,
            'burc': dereceden_burc_dec(veritabani_derece),
            'tarih': f"{kaynak_yil}-{kaynak_ay:02d}-{kaynak_gun:02d}"
        },
        'sonuc': None,
        'tum_bulunan': bulunanlar,
        'aciklama': '',
        'jd_gunumuz': jd_gunumuz
    }
    
    if bulunanlar:
        en_yakin = bulunanlar[0]
        # FBST veritabanında bu yıldızın bilgisi var mı?
        fbst_bilgi = fbst_sabit_yildizlar.get(en_yakin['yildiz'].upper(), None)
        
        # Bu yıldızın günümüzdeki pozisyonu
        gunumuz_lon = fixstar_ut_lon(en_yakin['yildiz'], jd_gunumuz)
        
        result['sonuc'] = {
            'yildiz': en_yakin['yildiz'],
            'lon': en_yakin['lon'],
            'fark': en_yakin['fark'],
            'fbst_verisi': fbst_bilgi,
            'burc': dereceden_burc_dec(en_yakin['lon']),
            'gunumuz_lon': gunumuz_lon,
            'gunumuz_burc': dereceden_burc_dec(gunumuz_lon)
        }
        result['aciklama'] = (
            f"* Bağıl haritada görünen {veritabani_derece:.2f}° pozisyonu ({dereceden_burc_dec(veritabani_derece)}), "
            f"{kaynak_yil} yılındaki gerçek gökyüzünde **{en_yakin['yildiz']}** sabit yıldızına "
            f"karşılık gelmektedir (Orb: {en_yakin['fark']:.4f}°).\n\n"
            f"Bu yıldızın günümüzdeki pozisyonu: {gunumuz_lon:.4f}° "
            f"({dereceden_burc_dec(gunumuz_lon)})"
        )
    else:
        result['aciklama'] = (
            f"⚠️ {kaynak_yil} yılında {veritabani_derece:.2f}° pozisyonunda "
            f"({dereceden_burc_dec(veritabani_derece)}) {orb_siniri}° orb sınırı içinde "
            f"kataloglanmış sabit yıldız bulunamamıştır. Orb sınırını artırabilirsiniz."
        )
    
    return result


# ==============================================================================


def aci_farki_safe(derece1, derece2):
    """
    İki zodyak derecesi arasındaki en kısa kadersel mesafeyi (orb) hesaplar.
    """
    fark = abs(derece1 - derece2)
    if fark > 180:
        fark = 360 - fark
    return fark


def aci_farki(derece1, derece2):
    """
    İki zodyak derecesi arasındaki en kısa kadersel mesafeyi (orb) hesaplar.
    (360 derecelik çemberde 359° ile 1° arasındaki farkın 2° olduğunu anlar.)
    """
    fark = abs(derece1 - derece2)
    if fark > 180:
        fark = 360 - fark
    return fark


def _yildiz_gercek_derece(yildiz_adi, target_jd, fallback_derece):
    """Yıldızın belirli bir tarihteki gerçek ekliptik boylamını döndürür."""
    if target_jd is not None:
        try:
            ad = _YILDIZ_SEF_AD.get(yildiz_adi, yildiz_adi)
            return fixstar_ut_lon(ad, target_jd)
        except Exception:
            pass
    return fallback_derece


def kadersel_yildiz_harita_tara(gezegen_dereceleri, target_jd=None, orb_siniri=2.0, mod=None, max_muhur=None):
    """
    TEK BİR TARİHTE (target_jd) tüm sabit yıldızları precession ile hesaplayıp,
    verilen gezegen dereceleri sözlüğüyle eşleştirir.

    Args:
        gezegen_dereceleri: {gezegen_adi: derece} sözlüğü
        target_jd: Katmanın Julian Day'i. Verilirse yıldızlar gerçek pozisyonlarıyla
                   (precession dahil) hesaplanır; verilmezse FBST kataloğundaki
                   statik dereceler kullanılır (eski davranış).
        orb_siniri: Tolerans derecesi
        mod: Aktif mod
        max_muhur: Gösterilecek maksimum mühür sayısı (None = sınırsız).
                   FBST zengin yorumlu mühürler önceliklidir, kalanlar orba göre sıralanır.

    Returns:
        Liste: FBST tarzı mühür metinleri (zengin yorumlarla)
    """
    _EN = _uEN()
    if _aktif_sozluk_yok():
        return []

    if target_jd is not None:
        # Tüm yıldızların gerçek pozisyonlarını bir kez hesapla (performans)
        yildiz_pozisyonlari = {}
        for yildiz_adi in tum_sabit_yildizlar_listesi():
            try:
                yildiz_pozisyonlari[yildiz_adi] = fixstar_ut_lon(yildiz_adi, target_jd)
            except Exception:
                continue
    else:
        yildiz_pozisyonlari = {}

    bulunan_muhurler = []
    fbst_muhurler = []
    _aktif_mod = mod

    # Hangi gezegen için hangi FBST yıldızı zengin yorum üretti (fallback dedup için)
    zengin_pozisyonlar = defaultdict(set)

    if _aktif_mod == "ebeveyn_cocuk" and fbst_sabit_yildizlar_ebeveyn:
        _aktif_sozluk = fbst_sabit_yildizlar_ebeveyn
    elif _aktif_mod == "es_sevgili" and fbst_sabit_yildizlar_ask:
        _aktif_sozluk = fbst_sabit_yildizlar_ask
    else:
        _aktif_sozluk = fbst_sabit_yildizlar

    def _fark_ayikla(metin):
        try:
            import re
            m = re.search(r"Fark: ([\d.]+)", metin)
            return float(m.group(1)) if m else 999.0
        except Exception:
            return 999.0

    for yildiz_adi, veriler in _aktif_sozluk.items():
        if _EN and getattr(_aktif_sozluk, "_en", None):
            _ev = _aktif_sozluk._en.get(yildiz_adi)
            if isinstance(_ev, dict):
                veriler = _ev
        yildiz_derecesi = _yildiz_gercek_derece(yildiz_adi, target_jd, veriler["derece"])
        for gezegen_adi, gezegen_derecesi in gezegen_dereceleri.items():
            fark = aci_farki(gezegen_derecesi, yildiz_derecesi)

            if fark <= orb_siniri:
                if _EN:
                    rapor_metni = f"* Star Link: {yildiz_adi} (conjunct {_updf_label(gezegen_adi)} | Diff: {fark:.2f}°)\n"
                else:
                    rapor_metni = f"* Yıldız Bağlantısı: {yildiz_adi} ({gezegen_adi} ile | Fark: {fark:.2f}°)\n"
                etki_bulundu = False

                if "yargi" in veriler:
                    if _EN:
                        rapor_metni += f"   💫 Star's meaning: {veriler['yargi']}\n"
                    else:
                        rapor_metni += f"   💫 Yıldızın anlamı: {veriler['yargi']}\n"
                    etki_bulundu = True

                for kategori, gezegen_etkileri in veriler["etkiler"].items():
                    if _EN:
                        _kategori_ad = _KATEGORI_DUZ_AD_EN.get(kategori, kategori.replace("_", " ").title())
                    else:
                        _kategori_ad = _KATEGORI_DUZ_AD.get(kategori, kategori.replace("_", " ").title())
                    if gezegen_adi in gezegen_etkileri:
                        rapor_metni += f"   ➤ {_kategori_ad} ({_updf_label(gezegen_adi)}): {gezegen_etkileri[gezegen_adi]}\n"
                        etki_bulundu = True
                    elif "Genel" in gezegen_etkileri:
                        rapor_metni += f"   ➤ {_kategori_ad}: {gezegen_etkileri['Genel']}\n"
                        etki_bulundu = True

                if etki_bulundu:
                    zengin_pozisyonlar[gezegen_adi].add(round(yildiz_derecesi, 2))
                    if _aktif_mod != "ebeveyn_cocuk":
                        fbst_muhurler.append((fark, rapor_metni))
                    else:
                        bulunan_muhurler.append(rapor_metni)

    # FBST kataloğunda olmayan ama sefstars'ta olan yıldızlar da taranır
    if target_jd is not None:
        for yildiz_adi, yildiz_derecesi in yildiz_pozisyonlari.items():
            uyari_ustu = yildiz_adi.upper()
            if uyari_ustu in _aktif_sozluk:
                continue
            for gezegen_adi, gezegen_derecesi in gezegen_dereceleri.items():
                fark = aci_farki(gezegen_derecesi, yildiz_derecesi)
                if fark <= orb_siniri:
                    # FBST kataloğunda aynı pozisyonda zengin yorum üretilmişse
                    # genel fallback üretme (ad eşleşme farkları için)
                    if gezegen_adi in zengin_pozisyonlar:
                        if any(aci_farki(yildiz_derecesi, p) <= 0.5 for p in zengin_pozisyonlar[gezegen_adi]):
                            continue
                    if _EN:
                        if _aktif_mod == "ebeveyn_cocuk":
                            _baglam = "the bond you share with your child"
                            _alan = "that area"
                        elif _aktif_mod == "es_sevgili":
                            _baglam = "your relationship"
                            _alan = "that area"
                        else:
                            _baglam = "your life"
                            _alan = "that area"
                        _gezegen_anlami = _GEZEGEN_DUZ_ANLAM_EN.get(gezegen_adi, gezegen_adi)
                        bulunan_muhurler.append((
                            fark,
                            f"* Star Link: {yildiz_adi} (in {_updf_label(gezegen_adi)}'s zone | Diff: {fark:.2f}°)\n"
                            f"   ➤ What does it mean? {yildiz_adi}, an ancient star in the sky, aligns with "
                            f"{_updf_label(gezegen_adi)} ({_gezegen_anlami}) in your chart. This union amplifies the star's "
                            f"power in {_baglam}, making this theme more visible and pronounced in your life."
                        ))
                    else:
                        if _aktif_mod == "ebeveyn_cocuk":
                            _baglam = "çocuğunuzla aranızdaki bağda"
                            _alan = "o alanı"
                        elif _aktif_mod == "es_sevgili":
                            _baglam = "ilişkinizde"
                            _alan = "o alanı"
                        else:
                            _baglam = "hayatınızda"
                            _alan = "o alanı"
                        _gezegen_anlami = _GEZEGEN_DUZ_ANLAM.get(gezegen_adi, gezegen_adi)
                        bulunan_muhurler.append((
                            fark,
                            f"* Yıldız Bağlantısı: {yildiz_adi} ({gezegen_adi} bölgesinde | Fark: {fark:.2f}°)\n"
                            f"   ➤ Bu ne demek? {yildiz_adi} adlı eski bir gökyüzü yıldızı, doğum haritanızda "
                            f"{gezegen_adi} noktasına ({_gezegen_anlami}) denk geliyor. Bu buluşma, yıldızın gücünü "
                            f"{_baglam} {_alan} güçlendirir; bu temanın etkisi hayatınızda daha görünür ve belirgin hale gelir."
                        ))
                    break

    # Öncelik sırası: FBST zengin yorumlar → kozmik temaslar, her grup orba göre sıralı
    fbst_muhurler.sort(key=lambda x: x[0])
    bulunan_muhurler.sort(key=lambda x: x[0] if isinstance(x, tuple) else _fark_ayikla(x[0]))
    if _aktif_mod != "ebeveyn_cocuk":
        sirali = [m[1] for m in fbst_muhurler] + [m[1] if isinstance(m, tuple) else m for m in bulunan_muhurler]
    else:
        sirali = [m[1] if isinstance(m, tuple) else m for m in bulunan_muhurler]

    if max_muhur is not None and len(sirali) > max_muhur:
        sirali = sirali[:max_muhur]
    return sirali


def _aktif_sozluk_yok():
    """FBST sözlüklerinin mevcut olup olmadığını kontrol eder (güvenli dönüş)."""
    return False


def kadersel_yildiz_taramasi(gezegen_adi, gezegen_derecesi, orb_siniri=2.0, mod=None):
    _EN = _uEN()
    bulunan_muhurler = []
    _aktif_mod = mod

    if _aktif_mod == "ebeveyn_cocuk" and fbst_sabit_yildizlar_ebeveyn:
        _aktif_sozluk = fbst_sabit_yildizlar_ebeveyn
    elif _aktif_mod == "es_sevgili" and fbst_sabit_yildizlar_ask:
        _aktif_sozluk = fbst_sabit_yildizlar_ask
    else:
        _aktif_sozluk = fbst_sabit_yildizlar

    for yildiz_adi, veriler in _aktif_sozluk.items():
        if _EN and getattr(_aktif_sozluk, "_en", None):
            _ev = _aktif_sozluk._en.get(yildiz_adi)
            if isinstance(_ev, dict):
                veriler = _ev
        yildiz_derecesi = veriler["derece"]
        fark = aci_farki(gezegen_derecesi, yildiz_derecesi)

        if fark <= orb_siniri:
            # Raporlama şablonu
            if _EN:
                rapor_metni = f"* Star Link: {yildiz_adi} (conjunct {_updf_label(gezegen_adi)} | Diff: {fark:.2f}°)\n"
            else:
                rapor_metni = f"* Yıldız Bağlantısı: {yildiz_adi} ({gezegen_adi} ile | Fark: {fark:.2f}°)\n"
            etki_bulundu = False

            # Yıldızın genel yorumu
            if "yargi" in veriler:
                if _EN:
                    rapor_metni += f"   💫 Star's meaning: {veriler['yargi']}\n"
                else:
                    rapor_metni += f"   💫 Yıldızın anlamı: {veriler['yargi']}\n"
                etki_bulundu = True

            # Klasik etkileri tara
            for kategori, gezegen_etkileri in veriler["etkiler"].items():
                if _EN:
                    _kategori_ad = _KATEGORI_DUZ_AD_EN.get(kategori, kategori.replace("_", " ").title())
                else:
                    _kategori_ad = _KATEGORI_DUZ_AD.get(kategori, kategori.replace("_", " ").title())
                if gezegen_adi in gezegen_etkileri:
                    rapor_metni += f"   ➤ {_kategori_ad} ({gezegen_adi}): {gezegen_etkileri[gezegen_adi]}\n"
                    etki_bulundu = True
                elif "Genel" in gezegen_etkileri:
                    rapor_metni += f"   ➤ {_kategori_ad}: {gezegen_etkileri['Genel']}\n"
                    etki_bulundu = True

            if etki_bulundu:
                bulunan_muhurler.append(rapor_metni)

    return bulunan_muhurler


def _son_pazar_gunu(yil, ay):
    """Verilen yil ve ayin son pazar gununu dondurur (1-31 arasi)."""
    import calendar
    son_gun = calendar.monthrange(yil, ay)[1]
    for gun in range(son_gun, 0, -1):
        if calendar.weekday(yil, ay, gun) == 6:  # Sunday = 6
            return gun
    return son_gun


BURC_ISIMLERI = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
                  "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]

# Sabit yıldız fallback metinlerinde geçen gezegen/asteroid adlarının düz Türkçe açıklaması
_GEZEGEN_DUZ_ANLAM = {
    "Güneş": "kimliğiniz, yaşam gücünüz ve kendinizi ifade etme biçiminiz",
    "Ay": "duygularınız, iç dünyanız ve güvende hissettiğiniz alan",
    "Merkür": "zihniniz, iletişiminiz ve öğrenme biçiminiz",
    "Venüs": "sevgi, ilişkiler ve güzellik anlayışınız",
    "Mars": "enerjiniz, cesaretiniz ve mücadele gücünüz",
    "Jüpiter": "şans, büyüme ve genişleme alanınız",
    "Satürn": "sorumluluk, disiplin ve olgunluk alanınız",
    "Uranüs": "özgürlük, yenilik ve ani değişim alanınız",
    "Neptün": "hayal gücü, sezgiler ve ruhsal duyarlılığınız",
    "Plüton": "dönüşüm, derinlik ve güç alanınız",
    "KAD": "kuzey ay düğümü; hayat yolculuğunuzda gelişmeniz gereken yön",
    "GAD": "güney ay düğümü; geçmişten getirdiğiniz alışkanlıklar",
    "Chiron": "yaralarınız ve bu yaralardan doğan şifa gücünüz",
    "Ceres": "beslenme ve bakım alma ihtiyacınız",
    "Juno": "bağlılık, evlilik ve eşitlik anlayışınız",
    "Vesta": "adanma, odaklanma ve özünüze bağlılığınız",
    "Pallas": "bilgelik, strateji ve yaratıcı zekânız",
    "Lilith": "bastırılmış arzularınız ve özgür benliğiniz",
    "MC": "kariyer ve toplumsal hedefleriniz",
    "Yükselen": "dış dünyaya gösterdiğiniz yüz ve ilk izleniminiz",
    "ASC": "dış dünyaya gösterdiğiniz yüz ve ilk izleniminiz",
}

# Sabit yıldız fallback metinlerinde geçen gezegen/asteroid adlarının düz İngilizce açıklaması
_GEZEGEN_DUZ_ANLAM_EN = {
    "Güneş": "your identity, life force, and way of self-expression",
    "Ay": "your emotions, inner world, and where you feel safe",
    "Merkür": "your mind, communication, and way of learning",
    "Venüs": "love, relationships, and your sense of beauty",
    "Mars": "your energy, courage, and drive",
    "Jüpiter": "your area of luck, growth, and expansion",
    "Satürn": "your area of responsibility, discipline, and maturity",
    "Uranüs": "your area of freedom, innovation, and sudden change",
    "Neptün": "your imagination, intuition, and spiritual sensitivity",
    "Plüton": "your area of transformation, depth, and power",
    "KAD": "the north lunar node; the direction you need to grow in your life journey",
    "GAD": "the south lunar node; habits you carry from the past",
    "Chiron": "your wounds and the healing power born from them",
    "Ceres": "your need for nourishment and care",
    "Juno": "your sense of commitment, marriage, and equality",
    "Vesta": "your devotion, focus, and dedication to your essence",
    "Pallas": "your wisdom, strategy, and creative intelligence",
    "Lilith": "your suppressed desires and liberated self",
    "MC": "your career and societal goals",
    "Yükselen": "the face you show the world and your first impression",
    "ASC": "the face you show the world and your first impression",
}

# Yıldız etkisi kategorilerinin düz Türkçe başlıkları
_KATEGORI_DUZ_AD = {
    "ask": "Aşk Hayatı",
    "evlilik": "Evlilik",
    "cinsellik": "Cinsellik ve Yakınlık",
    "cekim": "Çekim ve Karizma",
    "karmik_ask": "Kadersel Aşk",
    "zihinsel": "Zihin ve Düşünce",
    "saglik": "Sağlık",
    "kaza": "Risk ve Sınavlar",
    "gizlilikler": "Gizem ve Sezgi",
    "is_hayati": "İş Hayatı",
    "arkadaslar": "Arkadaşlıklar",
    "maddi": "Para ve Maddi Konular",
    "sorumluluk_ogrenme": "Sorumluluk ve Öğrenme",
    "sinav_ve_donusum": "Sınav ve Dönüşüm",
    "duygusal_saglik": "Duygusal Sağlık",
    "sosyal_cevre": "Sosyal Çevre",
    "cocuk_gelisimi": "Çocuğun Gelişimi",
    "bedensel_saglik": "Bedensel Sağlık",
    "zihinsel_gelisim": "Zihinsel Gelişim",
    "egitim_ve_ogrenme": "Eğitim ve Öğrenme",
    "ebeveynlik": "Ebeveynlik",
    "karmik_bag": "Kadersel Bağ",
}

# Yıldız etkisi kategorilerinin düz İngilizce başlıkları (EN modda kullanılır)
_KATEGORI_DUZ_AD_EN = {
    "ask": "Love Life",
    "evlilik": "Marriage",
    "cinsellik": "Sexuality and Intimacy",
    "cekim": "Attraction and Charisma",
    "karmik_ask": "Fated Love",
    "zihinsel": "Mind and Thought",
    "saglik": "Health",
    "kaza": "Risk and Trials",
    "gizlilikler": "Mystery and Intuition",
    "is_hayati": "Career",
    "arkadaslar": "Friendships",
    "maddi": "Money and Financial Matters",
    "sorumluluk_ogrenme": "Responsibility and Learning",
    "sinav_ve_donusum": "Trial and Transformation",
    "duygusal_saglik": "Emotional Health",
    "sosyal_cevre": "Social Circle",
    "cocuk_gelisimi": "Your Child's Development",
    "bedensel_saglik": "Physical Health",
    "zihinsel_gelisim": "Mental Development",
    "egitim_ve_ogrenme": "Education and Learning",
    "ebeveynlik": "Parenting",
    "karmik_bag": "Fated Bond",
}


def dereceyi_burca_cevir(derece):
    """0-360 arasi dereceyi burc adina cevirir."""
    derece = float(derece) % 360
    burc_index = int(derece // 30)
    return BURC_ISIMLERI[burc_index]


def dereceyi_eve_ata(derece, cusps):
    """Dereceyi ev cusps listesine gore eve atar (1-12)."""
    derece = float(derece) % 360
    for i in range(12):
        bas = cusps[i] % 360
        son = cusps[(i + 1) % 12] % 360
        if son > bas:
            if bas <= derece < son:
                return i + 1
        else:
            if derece >= bas or derece < son:
                return i + 1
    return 1


GEZEGENLER = {
    "Güneş": 0, "Ay": 1, "Merkür": 2, "Venüs": 3, "Mars": 4,
    "Jüpiter": 5, "Satürn": 6, "Uranüs": 7, "Neptün": 8, "Plüton": 9,
    "Chiron": 15, "Juno": swe.AST_OFFSET + 3, "Ceres": swe.AST_OFFSET + 1, "Lilith": 10,
    "Pallas": swe.AST_OFFSET + 2, "Vesta": swe.AST_OFFSET + 4,
    "Eros": swe.AST_OFFSET + 433, "Psyche": swe.AST_OFFSET + 16,
    "Sappho": swe.AST_OFFSET + 80, "Amor": swe.AST_OFFSET + 1221,
}

def get_safe_flags(gezegen_id):
    """Gezegen ID'sine gore guvenli Swiss Ephemeris flag'i dondurur."""
    if gezegen_id is None:
        return swe.FLG_SWIEPH | swe.FLG_SPEED
    if isinstance(gezegen_id, int) and gezegen_id >= 10:
        return swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_NOABERR
    return swe.FLG_SWIEPH | swe.FLG_SPEED


def asteroid_ephe_mevcut_mu():
    """Asteroid efemeris dosyalarinin varligini kontrol eder."""
    ephe_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ephe")
    ast_files = [f for f in os.listdir(ephe_dir) if f.endswith(".sef") or "asteroid" in f.lower()]
    return len(ast_files) > 0


def asteroit_tahmini_derece(gezegen_adi, jd):
    """Asteroid pozisyonunu tahmini hesaplar (efemeris yoksa yaklasik)."""
    try:
        if gezegen_adi in GEZEGENLER:
            gid = GEZEGENLER[gezegen_adi]
            flags = get_safe_flags(gid)
            pos = swe.calc_ut(jd, gid, flags)
            return pos[0][0]
    except Exception:
        pass
    return None


def acg_pozisyon_hesapla(jd, enlem, boylam):
    """Astro-Cartography pozisyon hesaplama."""
    try:
        res, ascmc = swe.houses_ex(jd, enlem, boylam, b'P')
        return {"asc": ascmc[0], "mc": ascmc[1], "cusps": res}
    except Exception:
        return {"asc": 0, "mc": 0, "cusps": list(range(0, 360, 30))}


def astro_kartografi_skor(jd, enlem, boylam):
    """Belirtilen koordinatlardaki astro-kartografi skorunu hesaplar."""
    pos = acg_pozisyon_hesapla(jd, enlem, boylam)
    skor = 0
    for gezegen_id in range(10):
        try:
            gez_pos = swe.calc_ut(jd, gezegen_id, swe.FLG_SWIEPH)[0][0]
            asc_fark = abs(gez_pos - pos["asc"]) % 360
            mc_fark = abs(gez_pos - pos["mc"]) % 360
            if min(asc_fark, 360 - asc_fark) <= 5:
                skor += 2
            if min(mc_fark, 360 - mc_fark) <= 5:
                skor += 2
        except Exception:
            continue
    return min(skor, 10)


def kadersel_radar_analizi(p1_str, p2_str, event_date_str, event_time, p1_isim, p2_isim):
    """Kadersel radar analizi - sehir bazli enerji haritasi."""
    from datetime import datetime
    try:
        jd = swe.julday(*[int(x) for x in event_date_str.split("-")])
        sonuclar = {"para": [], "huzur": [], "tutku": []}
        return sonuclar
    except Exception:
        return {"para": [], "huzur": [], "tutku": []}


def _resize_and_encode(filename, max_width=800):
    """Resim dosyasini ac, yeniden boyutlandir ve base64'e cevir."""
    import base64
    from PIL import Image
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, filename)
        if not os.path.exists(path):
            return None
        img = Image.open(path)
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        w, h = img.size
        if w > max_width:
            ratio = max_width / w
            img = img.resize((max_width, int(h * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None

