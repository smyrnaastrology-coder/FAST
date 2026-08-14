import os
import time
import re
import json
import uuid
import base64
import numpy as np
import random
import matplotlib
matplotlib.use('Agg')

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

# Tutarlı renk paleti (tüm chart'lar için)
_FAST_RENKLER = {
    "birincil": "#B8A9C9",    # lavender
    "ikincil": "#8FB8CA",     # sage
    "vurgu": "#C9A96E",       # gold
    "rose": "#D4878F",        # rose
    "text": "#4A4A4A",        # dark gray
    "text_light": "#6B5B7B",  # muted purple
    "bg": "#FBF7F4",          # cream
    "border": "#E8E0D8",      # light border
}

import streamlit as st
import swisseph as swe
from datetime import datetime, date, timedelta
from collections import defaultdict

# Logo base64 yükleme (favicon ve sidebar için)
_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')
with open(_logo_path, 'rb') as _f:
    _logo_b64 = base64.b64encode(_f.read()).decode()

# Mod görselleri base64 yükleme
from PIL import Image
import io

def _resize_and_encode(filename, max_width=400):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    img = Image.open(path)
    ratio = max_width / img.width
    new_h = int(img.height * ratio)
    img = img.resize((max_width, new_h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

_cift_b64 = _resize_and_encode('cift.png')
_eb_b64 = _resize_and_encode('ebeveyn_cocuk.png')
_py_b64 = _resize_and_encode('potansıyel_yetenek.png')

@st.cache_data
def sehir_veritabani_yukle():
    """cities_db.json dosyasından tüm dünya şehirlerini yükler."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "cities_db.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_resource
def _get_geolocator():
    from geopy.geocoders import Nominatim
    return Nominatim(user_agent="fbst_kadersel_navigasyon_v2", timeout=10)

def sehir_bul(arama_metni):
    """Dünyanın herhangi bir şehrini enlem/boylam olarak çözer."""
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
                "tam_ad": konum.address
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
    "Portekiz": ["Lizbon", "Porto", "Braga", "Faro", "Coimbra"],
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

MD_VERITABANI_ADI = "ikili_iliskiler_simyasi_calismasi.md"

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

ephe_klasoru = os.path.join(os.path.dirname(__file__), 'ephe')
swe.set_ephe_path(ephe_klasoru)

# ==============================================================================
# 🌌 FBST KADERSEL KÜTÜPHANESİ (DOĞRUDAN APP.PY İÇİNE GÖMÜLÜ)
# ==============================================================================

# 1. PARÇACIK: GEZEGENLERİN OPERASYONEL VE RUHSAL MİSYONLARI


# 4. PARÇACIK: YÜKSELEN (ASC) - İLİŞKİNİN DÜNYEVİ VİTRİN ÜNİFORMASI
fbst_yukselenler = {
    "Koc": "Dış dünyaya inisiyatif alan, cesur ve öncü bir vitrinle çıkarsınız. Aşkın tutkusunu ve eylemsel guccunu dünyada fetihler yaparak somutlaştırırsınız.",
    "Boga": "Dış dünyaya sarsılmaz, huzur veren ve güven kokan bir vitrinle çıkarsınız. İlişkinin köklerini dünyada kalıcı bir maddi güvence ve sadakatle inşa edersiniz.",
    "Ikizler": "Dış dünyaya zihinsel olarak uyumlu, hareketli ve neşeli bir vitrinle çıkarsınız. Birbirinizin ufkunu açan o tatlı merakı, dünyada bilgi transferi ve iletişim ağı kurarak maddileştirirsiniz.",
    "Yengec": "Dış dünyaya korumacı, şefkatli ve birbirini saran bir vitrinle çıkarsınız. Aşkınızın o derin aidiyetini, dünyada sarsılmaz bir ruhsal yuva ve sıcak bir sığınak inşa ederek sergilersiniz.",
    "Aslan": "Dış dünyaya parlayan, cömert ve asil bir vitrinle çıkarsınız. Aşkınızın o ihtişamlı görkemini, dünyada yaratıcılık ve yönetme gücüyle taçlandırarak gösterirsiniz.",
    "Basak": "Dış dünyaya kusursuz işleyen, naif ve analitik bir vitrinle çıkarsınız. Birbirinize adadığınız iyileştirici şefkati, dünyada pratik bir düzen ve sıfır hatalı bir hizmetle maddileştirirsiniz.",
    "Terazi": "Dış dünyaya zarafetin ve uyumun vitriniyle çıkarsınız. Aşkın o masalsı dengesini, dünyada mutlak adalet, diplomasi ve kusursuz bir estetikle maddileştirirsiniz.",
    "Akrep": "Dış dünyaya son derece ketum, derin ve gizemli bir vitrinle çıkarsınız. Aşkınızın o hipnotik tutkusunu, dünyada yüzeysellikten uzak, dönüştürücü ve sarsılmaz bir güç merkezi kurarak yansıtırsınız.",
    "Yay": "Dış dünyaya maceracı, sınır tanımayan ve iyimser bir vitrinle çıkarsınız. Aşkın o coşkulu özgürlüğünü, dünyada uzak ufuklar keşfederek ve ortak bir vizyon inşa ederek maddileştirirsiniz.",
    "Oglak": "Dış dünyaya saygın, otoriter ve zamanın ötesinde bir vitrinle çıkarsınız. Fırtınaların sarsamayacağı o ebedi güveni, dünyada toplumsal statü ve yıkılmaz bir kale kurarak gösterirsiniz.",
    "Kova": "Dış dünyaya kuralları yıkan, ezber bozan ve elektrikli bir vitrinle çıkarsınız. Aşkınızın o isyankar doğasını, dünyada fütüristik idealler ve kolektif projeler üzerinden maddileştirirsiniz.",
    "Balik": "Dış dünyaya mistik, şefkatli ve adeta bu boyuta ait değilmiş gibi bir vitrinle çıkarsınız. Aşkınızın o koşulsuz teslimiyetini, dünyada ilahi bir şifa ve sanatsal bir üretimle maddileştirirsiniz."
}
# 5. PARÇACIK: RETRO (Rx) GEZEGENLERİN KARMİK VE RUHSAL ANLAMLARI
fbst_retrolar = {
    "Merkür": "📝 <b>[Karmik Retro Mührü]:</b> <i>Zihinsel içe dönüş! Geçmiş kadersel yaşamlardan kalma söylenmemiş sözleriniz var. Bu ilişkide iletişim dışa dönük olmaktan ziyade, telepatik ve derin bir içsel anlayışla çözülecektir.</i>",
    "Venüs": "📝 <b>[Karmik Retro Mührü]:</b> <i>Özdeğer sınavı! Sevgi enerjisi dış dünyadaki gösterişten çekilip, ruhun en derinlerine gizlenmiştir. Partnerinizle geçmişten gelen yarım kalmış bir aşk kontratınız var; şimdi onu şifalandırmaya geldiniz.</i>",
    "Mars": "📝 <b>[Karmik Retro Mührü]:</b> <i>Eylemin içselleştirilmesi! Öfke ve tutku dışarıya patlamak yerine içsel bir guca dönüşmüştür. Geçmişte yanlış kullanılmış güç veya pasif-agresif enerjileri bu ilişkide sevgiyle dönüştürme sınavındasınız.</i>",
    "Jüpiter": "📝 <b>[Karmik Retro Mührü]:</b> <i>İçsel bilgelik! Dış dünyanın ahlak ve inanç kurallarını reddedip, kendi ruhsal felsefenizi yaratma vaktidir. Bu ilişki, şansı dışarıda aramak yerine, bereketi kendi içinizde bulmanızı sağlayacaktır.</i>",
    "Satürn": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ağır Karmik Borç! Otorite figürleriyle ve geçmiş yaşamlardaki sorumluluklarla ilgili bitmemiş bir sınavınız var. İlişkinin kurallarını dış dünyanın dayatmalarına göre değil, kendi sarsılmaz iç otoritenizle kurmalısınız.</i>",
    "Uranüs": "📝 <b>[Karmik Retro Mührü]:</b> <i>İçsel devrim! İsyankar enerjiniz topluma karşı değil, kendi iç dünyanızdaki prangalara karşı çalışacak. İkiniz de bu bağın içinde birbirinizin ruhunu özgürleştirecek gizli birer anarşistsiniz.</i>",
    "Neptün": "📝 <b>[Karmik Retro Mührü]:</b> <i>Gizli illüzyonlar! Spiritüel algılarınız çok açık ancak kurban psikolojisine düşme tehlikeniz var. Rüyalarınız ve sezgileriniz size yol gösterecek; dış dünyanın gürültüsüne değil, içinizdeki ilahi sese güvenin.</i>",
    "Plüton": "📝 <b>[Karmik Retro Mührü]:</b> <i>Yeraltı simyası! Güç savaşları ve manipülasyon arzusu, en derine gömülmüş korkulardan beslenir. Bu ilişki sizi en büyük psikolojik zaaflarınızla yüzleştirip, kendi küllerinizden sessizce yeniden doğuracak.</i>",
    "Chiron": "📝 <b>[Karmik Retro Mührü]:</b> <i>Kadim yara! Şifa enerjisi dışarıdan önce kendi içinize yönelmelidir. Kendinizi iyileştirmeden partnerinizi iyileştiremezsiniz. Bu bağ, ruhun en saklı kalmış dehlizlerindeki acılara ayna tutarak merhem olacaktır.</i>",
    "Juno": "📝 <b>[Karmik Retro Mührü]:</b> <i>Karmik eş kontratı! Geçmiş yaşamlardan kalan tamamlanmamış bir evlilik veya sadakat sözleşmesi tekrar masada. Bağlılığın yüzeysel kurallarını yıkıp, ruhsal sadakati en derinden test edeceksiniz.</i>",
    "Ceres": "📝 <b>[Karmik Retro Mührü]:</b> <i>İçsel beslenme! Partnerinizden şefkat beklerken, aslında kendi kendinize yetmeyi ve kendi ruhunuzu beslemeyi öğrenmeniz gereken özel bir kadersel döngü.</i>",
    "Lilith": "📝 <b>[Karmik Retro Mührü]:</b> <i>Gölgenin inzivası! Bastırılmış tabular, cinsellik ve boyun eğmeyen vahşi enerji, yüzeysel olarak yaşanmak yerine ilişkideki en karanlık ve büyüleyici gizem olarak içselleşmiştir.</i>"
}



fbst_yukselenler_ebeveyn = {
    "Koc": "Dış dünyaya cesur ve koruyucu bir ebeveyn vitriniyle çıkarsınız. Ebeveynlikte inisiyatif alan, çocuğunu korumak için dünyaya meydan okuyan bir enerji sergilersiniz.",
    "Boga": "Dış dünyaya sarsılmaz, huzur veren ve güvenli bir ebeveyn vitriniyle çıkarsınız. Çocuğunuza maddi ve manevi güvence sağlayan, köklü bir yuva inşa edersiniz.",
    "Ikizler": "Dış dünyaya iletişim odaklı, neşeli ve meraklı bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzla bilgi paylaşan, her şeyi onunla birlikte keşfeden bir ebeveyn olursunuz.",
    "Yengec": "Dış dünyaya korumacı, şefkatli ve kucaklayıcı bir ebeveyn vitriniyle çıkarsınız. Çocuğunuz için sarsılmaz bir duygusal sığınak inşa edersiniz.",
    "Aslan": "Dış dünyaya parlayan, cömert ve gurur verici bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzun yeteneklerini sahneye koyan, onunla gurur duyan bir ebeveyn olursunuz.",
    "Basak": "Dış dünyaya kusursuz organize eden, pratik ve detaycı bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzun her ihtiyacını milimetrik karşılayan bir sistem kurarsınız.",
    "Terazi": "Dış dünyaya zarif, dengeli ve adaletli bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzla adil bir ilişki kuran, her zaman dengeyi arayan bir ebeveyn olursunuz.",
    "Akrep": "Dış dünyaya derin, gizemli ve koruyucu bir ebeveyn vitriniyle çıkarsınız. Çocuğunuz için her türlü tehlikeye karşı tetikte olan, okült bir ebeveynlik sergilersiniz.",
    "Yay": "Dış dünyaya maceracı, iyimser ve özgürlükçü bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzla birlikte hayatı keşfeden, ona geniş bir vizyon aşılayan bir ebeveyn olursunuz.",
    "Oglak": "Dış dünyaya saygın, disiplinli ve sorumluluk sahibi bir ebeveyn vitriniyle çıkarsınız. Çocuğunuza yapı ve disiplin veren, hayata hazırlayan bir ebeveyn olursunuz.",
    "Kova": "Dış dünyaya yenilikçi, özgürlükçü ve sıra dışı bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzu kalıplara sokmayan, bireyselliğine saygı duyan bir ebeveyn olursunuz.",
    "Balik": "Dış dünyaya mistik, şefkatli ve sezgisel bir ebeveyn vitriniyle çıkarsınız. Çocuğunuzla ruhsal bir bağ kuran, onun manevi gelişimine odaklanan bir ebeveyn olursunuz."
}

fbst_retrolar_ebeveyn = {
    "Merkür": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlikte iletişim içe yönelir! Çocuğunuzla aranızdaki bağ sözcüklerin ötesindedir; sezgisel ve telepatik bir anlayışla connected olmanız beklenir.</i>",
    "Venüs": "📝 <b>[Karmik Retro Mührü]:</b> <i>Özdeğer ve sevgi dilini yeniden öğrenme! Çocuğunuza sevginizi gösterme şekliniz, kendi çocukluk deneyimlerinizden derinden etkilenmiştir.</i>",
    "Mars": "📝 <b>[Karmik Retro Mührü]:</b> <i>Koruma içgüdüsünün içselleştirilmesi! Öfke ve sabır dengeniz test edilir; çocuğunuzla aranızdaki güç dinamiğinde içsel bir denge bulmanız gereken döngü.</i>",
    "Jüpiter": "📝 <b>[Karmik Retro Mührü]:</b> <i>Öğretme felsefesinin yeniden yapılması! Çocuğunuza aktardığınız değerler ve inançlar, kendi içinizde derin bir sorgulamadan geçmelidir.</i>",
    "Satürn": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlik disiplinindeki karmik borç! Sınır koyma ve otorite kurma konularında, kendi ebeveynlerinizden aldığınız mirası yeniden yapılandırmanız gereken sınav.</i>",
    "Uranüs": "📝 <b>[Karmik Retro Mührü]:</b> <i>İçsel ebeveynlik devrimi! Çocuğunuzun özgürlüğünü desteklerken, kendi içinizdeki bağımlılıkları ve korkuları yenmeniz gereken kadersel döngü.</i>",
    "Neptün": "📝 <b>[Karmik Retro Mührü]:</b> <i>İllüzyon ve ideal ebeveynlik! Mükemmel anne/baba olma hayaliniz, gerçekçi sınırlarla dengelenmelidir. Sezgileriniz güçlü ama netlik gerekli.</i>",
    "Plüton": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlik güç dönüşümü! Çocuğunuzun büyümesiyle birlikte kendi kimliğiniz de derinden değişir; kontrol bırakma ve yeniden doğuş sınavı.</i>",
    "Chiron": "📝 <b>[Karmik Retro Mührü]:</b> <i>Nesnel yara mirası! Kendi ebeveynlerinizden aldığınız yaraları şifalandırmadan, çocuğunuza tam anlamıyla şifa veremezsiniz. Nesnel şifa zincirinin bilinci.</i>",
    "Juno": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlik sadakat kontratı! Çocuğunuza verdiğiniz koşulsuz sadakat sözü, kendi iç çatışmalarınızla test edilir.</i>",
    "Ceres": "📝 <b>[Karmik Retro Mührü]:</b> <i>Besleme ve bırakma dengesi! Çocuğunuzu beslerken onu aynı anda bağımsız bırakmayı da öğrenmeniz gereken kadersel döngü.</i>",
    "Lilith": "📝 <b>[Karmik Retro Mührü]:</b> <i>Ebeveynlikte bastırılmış vahşilik! Toplumsal beklentilerin dışında, çocuğunuza en otantik ve sınırsız sevginizi gösterme korkunuzla yüzleşme zamanı.</i>"
}



# ══════════════════════════════════════════════════════════════════════════════
# KRİZ KÜTÜPHANESİ — EBEVEYN/ÇOCUK MODU
# ══════════════════════════════════════════════════════════════════════════════

KRIZ_KUTUPHANESI_EBEVEYN = [
    {
        "baslik": "İlk Uyanış: Vücudun Sırrı (0-6 Ay)",
        "yorum": "Doğumla birlikte hem siz hem de bebeğiniz devasa bir değişime uğradınız. Uykusuz geceler, beslenme düzeni ve ebeveyn kimliğinin ilk adımları bu dönemin temel sınavlarıdır. Bu kriz, sizi birey olmaktan anne/babaya dönüştüren ilk kapıdır."
    },
    {
        "baslik": "Kök Bağı: Ayrışmanın Tohumları (6 Ay - 2 Yıl)",
        "yorum": "Bebeğiniz yürümeye, konuşmaya ve mundo keşfetmeye başladıkça, onunla aranızdaki fiziksel bağın ötesinde güvenli bir bağlanma inşa etmenin zamanıdır. İlk 'hayır'ların ve ilk ayrılıkların evidir."
    },
    {
        "baslik": "Ben Merkezcilik Sınavı (2-4 Yaş)",
        "yorum": "'Hayır!' diyen, sınır denemeleri yapan, tuvalet eğitimiyle yüzleşen bir çocukla başa çıkmak, ebeveynlik sabrının ilk büyük testidir. Sınır koyma sanatı burada öğrenilir."
    },
    {
        "baslik": "Sosyal Aynada Yansıma (4-7 Yaş)",
        "yorum": "Çocuğunuz okula başlar, arkadaş edinir ve sizin dışınızdaki dünyanın kurallarını keşfeder. Onun sosyal yeteneklerini desteklerken kendi ebeveynlik kaygılarınızla yüzleşmenin zamanıdır."
    },
    {
        "baslik": "Bilgi Tapınağının Kapıları (7-12 Yaş)",
        "yorum": "Akademik baskı, yetenek keşfi ve karşılaştırma tuzağı bu dönemin sınavlarıdır. Çocuğunuzun kendi yolunu bulmasına izin verirken, toplumsal beklentilerle denge kurmanız gereken kritik dönem."
    },
    {
        "baslik": "Ergenlik Fırtınası: Kimlik Bunalımı (12-16 Yaş)",
        "yorum": "Hormonal değişiklikler, bağımsızlık savaşları ve kimlik arayışı bu dönemin temel yapiylaridir. Çocuğunuz artık bir birey olmak istiyor; siz ise hala korumak istiyorsunuz. Bu çatışma, ebeveyn-çocuk ilişkisinin en kritik sınavıdır."
    },
    {
        "baslik": "Ayrışma Protokolü (16-18 Yaş)",
        "yorum": "Üniversite, evden ayrılma ve bağımsız hayatın ilk adımları bu dönemde atılır. Yıllardır inşa ettiğiniz bağı gevşetip, bırakmanın zamanı gelmiştir."
    },
    {
        "baslik": "Yansıma: Kendini Görmek (18-21 Yaş)",
        "yorum": "Artık yetişkin olan çocuğunuz, sizi bir birey olarak görmeye başlar. Ebeveyn hatalarını fark etme, affetme ve ilişkide yeniden denge kurma sürecidir."
    },
    {
        "baslik": "Eşitlik Kapısı: Yetişkin Dostluğu (21+ Yaş)",
        "yorum": "Ebeveyn-çocuk ilişkisi artık hiyerarşik olmaktan çıkıp, iki yetişkin arasındaki saygı ve dostluğa dönüşür. Bu, ebeveynliğin en tatlı ödülünü toplama zamanıdır."
    }
]



print("[FAST] Ebeveyn-Çocuk yorum sözlükleri yüklendi.")
# ==============================================================================
# 6. PARÇACIK: SABİAN SEMBOLLERİ (ZODYAK'IN 360 DERECELİK RUHSAL DNA'SI)
# ==============================================================================
fbst_sabian = {
    "Koc": {
        1: ("Denizden yeni çıkmış, fok balığına sarılan bir kadın", "Yeni başlangıçlar, geçmişin sularından çıkarak bu ilişkide yepyeni bir formda doğma cesareti."),
        2: ("Gözlerden uzak bir vadide, yeteneklerini sergileyen bir komedyen", "Dış dünyanın onayına ihtiyaç duymadan, ilişkinin kendi içindeki neşeyi ve potansiyeli keşfetmesi."),
        3: ("Ülkesinin haritasını çıkaran bir adam", "İlişkinin kendi sınırlarını, potansiyelini ve gelecekteki ortak yaşam alanını belirleme çabası."),
        4: ("Gözlerden uzak, tenha bir yolda yürüyen iki aşık", "Dış dünyanın kalabalığından izole olup, ilişkinin kendi iç mahremiyetini ve kutsal yalnızlığını inşa etme gücü."),
        5: ("Kanatlı bir üçgen", "Ruh, beden ve zihin bütünlüğünün sağlanarak ilişkinin dünyevi sınırları aşıp ilahi bir boyuta (guce) yükselişi."),
        6: ("Bir kenarı parlak şekilde aydınlatılmış bir kare", "İlişkideki sağlam ve yapısal temellerin üzerine düşen evrensel ışık; odaklanılması gereken kadersel yönü gösteriyor."),
        7: ("Aynı anda iki farklı dünyada kendini ifade edebilen bir adam", "Hem maddi hem de manevi alemlerde denge kurarak, ilişkinin dualiteyi aşan kusursuz bir uyum yakalaması."),
        8: ("Doğu rüzgarında dalgalanan kurdeleli büyük bir kadın şapkası", "Evrensel değişim rüzgarlarına karşı sezgisel bir kalkan oluşturma ve ruhsal fırtınalara direnmeden uyumlanma."),
        9: ("Kristal küreye odaklanmış bir medyum", "Görünenin ötesine geçme, partnerin içsel dünyasındaki sessiz çağrıları ve yaraları telepatik olarak okuma yeteneği."),
        10: ("Geleneksel imgelere yeni formlar veren bir öğretmen", "Eski alışkanlıkları ve kalıplaşmış toksik ilişki yapiylarini yıkarak, bağınızı yepyeni bir vizyonla baştan yaratma."),
        11: ("Bir ülkenin yöneticisi", "İlişkinin kendi krallığını ilan etmesi, sorumluluk alma ve bu kadersel birliğin sarsılmaz otoritesini kurma vakti."),
        12: ("Üçgen şeklinde uçan yaban kazları sürüsü", "Ortak hedeflere doğru kusursuz bir kadersel senkronizasyon ve ilahi bir içgüdüyle, çabasızca yol alma gücü."),
        13: ("Patlamamış bir bomba; başarısız bir sosyal isyan", "İçinizde biriken öfke ve krizlerin, yıkıcı bir şekilde patlamak yerine sönümlenerek ruhsal bir bilgeliğe dönüşmesi ihtimali."),
        14: ("Bir adam ve kadının yakınında kıvrılan bir yılan", "Karmik bilgelik, köklü cinsel enerji (Kundalini) ve ilişkinin en derinlerinden uyanan gizemli, dönüştürücü çekim gücü."),
        15: ("Törensel bir battaniye dokuyan bir Kızılderili", "İlişkinin her bir anını, ince bir sabır ve emekle dokuyarak dışarıya karşı kutsal bir ruhsal zırh veya yuva haline getirme çabası."),
        16: ("Gün batımında çalışan doğa ruhları (periler)", "Günlük çabaların ötesinde, görünmez evrensel güçlerin (kadersel amortisörlerin) ilişkinizi onarmak ve desteklemek için devrede olması."),
        17: ("Sessizlik içinde onurlu bir şekilde oturan iki bekar kadın", "Yalnızlık korkusunu aşarak, sessizliğin ve ruhsal dinginliğin içinde birbirinize muazzam bir huzurla eşlik etme erdemi."),
        18: ("İki ağaç arasına gerilmiş boş bir hamak", "Aksiyon ve çabayı bırakıp, ilişkinin dinlenmeye, eylemsizliğe ve doğal akışa (rölantiye) teslim olmaya ihtiyaç duyduğu o kutsal an."),
        19: ("Sihirli bir halı", "Dünyevi kısıtlamaları ve mantığı reddeden, hayal gücü ve inançla sınırları aşarak ilişkinizi masalsı bir boyuta taşıma potansiyeli."),
        20: ("Kışın kuşları besleyen genç bir kız", "En zor, soğuk ve krizli anlarda bile; şefkat, merhamet ve koşulsuz sevgiyle birbirinizin ruhunu besleyebilme mucizesi."),
        21: ("Ringe giren bir boksör", "İlişkinin dışsal engellere, zorluklara veya içsel gölgelere karşı savaşmak üzere cesaretle ve eylemsel guce donanması."),
        22: ("Tüm arzuların gerçekleştiği bahçeye açılan kapı", "Ruhsal ve dünyevi tatminin zirvesine ulaşma vaadi; engellerin aşılıp kadersel ödüllerin, bolluğun kapısında durma hali."),
        23: ("Hafif bir yazlık elbise içinde hamile bir kadın", "İlişkinin kendi içinde büyüttüğü yeni bir vizyonun, yaratıcılığın, bereketin veya ruhsal bir meyvenin doğuma hazırlanması."),
        24: ("Açık bir pencereden içeri savrulan perdelerin bereket boynuzu şeklini alması", "Evrensel akışa tam teslim olunduğunda, kozmik şansın ve ruhsal bereketin beklenmedik bir şekilde ilişkinize dolması."),
        25: ("İnsanın iki farklı varlık seviyesinde deneyim kazanma ihtimali", "Aşkı hem en tutkulu fiziksel boyutta hem de en yüce ilahi boyutta aynı anda, ustalıkla yaşayabilme lütfu."),
        26: ("Taşıyabileceğinden daha fazla yeteneğe sahip olan bir adam", "İlişkinin potansiyelinin taşması; bu çok yoğun kadersel enerjiyi dağıtmadan odaklayıp doğru şekilde yönetme sınavı."),
        27: ("Hayal gücü sayesinde kaybedilmiş bir fırsatın yeniden kazanılması", "Geçmişte yapılmış hataların veya kaçırılan şansların, güçlü bir sevgi ve inançla onarılıp kadersel rotanın yeniden çizilmesi."),
        28: ("Hayal kırıklığına uğramış büyük bir izleyici kitlesiyle yüzleşen performans sanatçısı", "İlişkideki aşırı beklentilerin gerçeklikle çarpışması; maskelerin düşerek çıplak gerçeğin sevgiyle, olduğu gibi kabul edilmesi sınavı."),
        29: ("Göksel kürelerin (gezegenlerin) müziği", "Ruhlarınızın evrensel titresimla tam bir uyuma girdiği, kelimelere ihtiyaç duyulmayan o ilahi ve kozmik senkronizasyon noktası."),
        30: ("Bir ördek göleti ve yavruları", "Kadersel yolculuğun bu fazında sükunete erme; ait olma, huzurlu bir yuva kurma ve mutlak bir korunma alanının tamamlanması.")
    },
    "Boga": {
        1: ("Berrak bir dağ deresinin taşıdığı altın tozları", "İlişkinin doğal akışında saklı olan muazzam maddi ve manevi zenginliği fark etme ve bu bereketi sevgiyle kabul etme zamanı."),
        2: ("Elektrik fırtınası; doğanın karanlık gökyüzündeki muazzam gücü", "Krizlerin ve ani patlamaların aslında aranızdaki durgun enerjiyi temizleyen kozmik bir şifa ve uyanış olması."),
        3: ("Yoncalarla açan bir çimenliğe çıkan doğal basamaklar", "İlişkinin huzura, berekete ve köklenmeye giden yolda acele etmeden, adım adım ve organik bir şekilde büyümesi."),
        4: ("Gökkuşağının sonundaki altın küpü", "Fırtınalı süreçlerin ve sınavların ardından gelen o büyük kadersel ödül; birlikte ulaşılan ruhsal ve maddi tatmin."),
        5: ("Açık bir mezarın başında bekleyen dul bir kadın", "Geçmişin acılarına ve bitmiş karmik bağlara veda ederek, ruhsal bir arınmayla bu yeni ilişkiye tamamen yer açma sınavı."),
        6: ("Derin bir uçurumun üzerine kurulan asma köprü", "Aranızdaki en aşılmaz gibi görünen farklılıkları, sağlam ve güvenilir bir iletişim/sadakat köprüsüyle aşma gücü."),
        7: ("Kuyunun başındaki Samiriyeli kadın", "Eski önyargıları ve dünyevi tabuları yıkarak, partnerinizin ruhundaki en derin susuzluğu koşulsuz sevgiyle giderme erdemi."),
        8: ("Karsız bir zeminde duran kızak", "Gelecek için yapılan planlarda zamanlamanın önemini anlama; doğru kadersel şartlar oluşana kadar sabırla bekleme iradesi."),
        9: ("Tamamen süslenmiş bir Noel ağacı", "İlişkinin en karanlık veya soğuk günlerinde bile umudu canlı tutması ve birbirinize sunduğunuz içsel değerlerin kutlanması."),
        10: ("Bir Kızılhaç hemşiresi", "Koşulsuz şefkat, fedakarlık ve partnerin en zayıf, yaralı anında onun en büyük ruhsal şifacısı olma kontratı."),
        11: ("Bahçesindeki çiçekleri sulayan bir kadın", "Sevginin ancak günlük, istikrarlı ve pratik bir emekle beslendiğinde yıkılmaz ve kalıcı bir yuvaya dönüşeceği bilgeliği."),
        12: ("Vitrinlere bakan genç bir çift", "Ortak hayaller kurma, geleceği birlikte inşa etme ve ilişkinin dünyevi/maddi hedeflerini neşeyle belirleme fazı."),
        13: ("Ağır yükler taşıyan bir hamal", "İlişkinin maddi veya kadersel yüklerini cesaretle omuzlama; sadakatin ve sorumluluğun ağır bir sabir testine dönüşmesi."),
        14: ("Sahilde oynayan çocuklar ve suyun kenarındaki deniz kabukluları", "Doğal sınırlar içinde güvenle neşeyi yaşama; huzurlu bir yuva alanında çocuksu, korunaklı ve saf duygulara teslimiyet."),
        15: ("Kafasını kalın bir atkıyla sarmış adam", "Dış dünyanın gürültüsüne ve toksik müdahalelerine karşı ilişkinin mahremiyetini koruma; sadece birbirinizin iç sesini dinleme ihtiyacı."),
        16: ("Öğrencilerinin ilgisini çekemeyen yaşlı bir öğretmen", "İlişkide eski, işe yaramayan kalıpları bırakma vakti; inatlaşılan kurallar yerine yeni ve ilham verici bir ortak dil bulma zorunluluğu."),
        17: ("Kılıçlar ve meşaleler arasındaki sembolik savaş", "İlişkide zihinsel aydınlanma (meşale) ile yıkıcı eleştiri (kılıç) arasında seçim yapma; haklı olmayı değil şifayı seçme sınavı."),
        18: ("Eski bir çantayı açık pencereden havalandıran kadın", "Bilinçaltında birikmiş eski zehirleri, şüpheleri ve yükleri sevginin o taze ve şifalı rüzgarıyla temizleme arınması."),
        19: ("Okyanusun içinden yükselen yeni bir kıta", "Büyük krizlerin ve duygusal çalkantıların ardından ilişkinin yepyeni, sarsılmaz ve somut bir temel (kıta) yaratma mucizesi."),
        20: ("Gökyüzünde uçuşan kanat benzeri bulutlar", "Manevi bir ilhamın, evrensel korumanın ve hafifliğin ilişkiye sızması; aşırı maddiyatçılıktan sıyrılıp ilahi akışa güvenme."),
        21: ("Açık bir kitaptaki satırı gösteren parmak", "Kadersel kontratın size sunduğu çok net bir işareti, mesajı veya senkronizasyonu fark edip ona göre hizalanma anı."),
        22: ("Fırtınalı suların üzerinde uçan beyaz güvercin", "En büyük krizlerin, kavgaların ve korkuların ortasında bile; evrensel bir barışın, güvenin ve ilahi korumanın ilişkinin üzerinde süzülmesi."),
        23: ("Değerli taşlarla dolu bir mücevher dükkanı", "İlişkinin sahip olduğu o yüksek özdeğeri, nadir bulunan yetenekleri ve parlayan ortak zenginliği idrak etme zirvesi."),
        24: ("Belinde düşman kafa derileriyle at süren Kızılderili savaşçı", "Koruma içgüdüsünün veya sahiplenmenin yıkıcı bir kıskançlığa/kontrolcülüğe dönüşmesi riski; ilkel egoyu ehlileştirme sınavı."),
        25: ("Geniş ve muazzam bir halk parkı", "Kişisel sevginin sınırlarını aşıp, ilişkinin dış dünyaya da ilham veren kolektif bir huzur, bereket ve hoşgörü alanına dönüşmesi."),
        26: ("Sevgilisine serenat yapan İspanyol aşık", "Romantizmin, kur yapmanın ve sevgi dilini estetik bir şekilde, cesurca ifade etmenin ilişkinin manyetik guccunu yeniden alevlendirmesi."),
        27: ("Kabilesinin el sanatlarını satan yaşlı bir kadın", "Geleneklerin, köklerin ve geçmişin kadim bilgeliğini; ilişkinizin bugünkü maddi ve manevi inşasına faydalı olacak şekilde uyarlama."),
        28: ("Aşka yeniden uyanan olgun bir kadın", "Geçmişin tüm hayal kırıklıklarına rağmen kalbi cesurca yeniden açma; aşkın zamansız olduğunu ve ilişkinin her an yeniden filizlenebileceğini idrak etme."),
        29: ("Bir masada çalışan iki ayakkabı tamircisi", "Ortak bir amaç için omuz omuza, sıfır ego ile çalışma; vizyonları gerçeğe dönüştürmek için pratik, dengeli ve kusursuz bir işbirliği mühürü."),
        30: ("Eski bir kalenin terasında gösteriş yapan tavus kuşu", "Zamanın testlerinden geçmiş başarıların, asaletin ve ebedi güvenin haklı gururu; ilişkinin köklü bir imparatorluk üzerinde ihtişamla taçlanması.")
    },
    "Ikizler": {
        1: ("Cam tabanlı bir teknede okyanusun dibini izleyen insanlar", "Yüzeysel olanın ötesine geçip, zihinsel merakla birbirinizin en derin ruhsal sularını keşfetme arzusu."),
        2: ("Noel Baba'nın gizlice çorapları doldurması", "Beklenmedik anda gelen kadersel hediyeler ve aranızdaki saf, çocuksu masumiyetin görünmez bir el tarafından ödüllendirilmesi."),
        3: ("Paris'teki Tuileries Bahçeleri", "İletişimde zarafetin, zihinsel düzenin ve entelektüel uyumun kusursuz bir mimariyle (ortak bir dille) inşa edilmesi."),
        4: ("Çobanpüskülü ve ökse otu", "Nostaljinin, eski anıların ve köklü geleneklerin aranızdaki zihinsel bağı romantik bir köprüyle canlı tutması."),
        5: ("Eyleme çağıran radikal bir dergi", "Zihinsel isyan! İlişkideki sıradanlığı ve rutini kırarak, birbirinizin zihnini ateşleyecek yeni ve devrimsel fikirler üretme ihtiyacı."),
        6: ("Petrol sondajı yapan işçiler", "Günlük sohbetlerin ve yüzeysel iletişimin çok ötesine geçip, ilişkinin en derinindeki o zengin, gizli güç kaynağına (petrole) ulaşma çabası."),
        7: ("Eski moda bir su kuyusu", "Birbirinizin zihninden, tükenmeyen kadim bir bilgelik ve ilham kaynağı gibi faydalanma; ruhsal susuzluğu kelimelerle giderme."),
        8: ("Fabrikanın etrafında toplanmış öfkeli grevciler", "Fikir ayrılıklarının krize dönüşmesi; zihinsel adalet arayışı ve ilişkide eşit söz hakkı talep eden sarsıcı bir yüzleşme."),
        9: ("Oklarla dolu bir sadak", "Zihinsel keskinlik! Hedefe kilitlenmiş sözler; kelimeleri birbirinizi yaralamak için değil, ortak engelleri vurmak için kullanma sınavı."),
        10: ("Burun dalışı yapan bir uçak", "İletişimde tehlikeli manevralar; büyük zihinsel riskler alarak ilişkide korkulan o büyük yüzleşmeyi cesaretle gerçekleştirme."),
        11: ("Yeni açılmış topraklarda sunulan bakir deneyim alanları", "Zihnin sınırlarını genişletme; ilişkinin yepyeni ufuklara, ortak eğitimlere veya daha önce hiç konuşulmamış konulara yelken açması."),
        12: ("Siyahi bir köle kızın, hanımından haklarını talep etmesi", "İletişimdeki gizli dengesizliklerin patlaması; bir tarafın zihinsel tahakkümüne karşı diğerinin özgürlük ve saygı talebiyle ayaklanması."),
        13: ("Piyano konseri veren ünlü bir müzisyen", "Entelektüel yeteneklerin kusursuz sergilenişi; fikirlerinizle, vizyonunuzla ve iletişiminizle birbirinize ilham verip hayran bırakma hali."),
        14: ("Uzaklarda yaşayan iki insanın telepatik iletişimi", "Mekansal mesafelere veya sessizliklere rağmen, zihinlerin kuantum seviyesinde birbirine bağlanarak muazzam bir telepatik aktarım yapması."),
        15: ("Kendi aralarında konuşan iki Hollandalı çocuk", "Karmaşık felsefeleri bir kenara bırakıp, ilişkinin en saf, en neşeli ve sadece ikinizin anladığı o basit ortak dili kurabilme mucizesi."),
        16: ("Duygusal bir konuşma yapan kadın aktivist", "İnançlar ve ortak hedefler uğruna tutkulu bir savunma; ilişkinin zihinsel enerjisinin dış dünyaya karşı bir kalkana dönüşmesi."),
        17: ("Gürbüz bir gencin kafasının olgun bir düşünürün kafasına dönüşmesi", "İlişkinin zihinsel olarak seviye atlaması; çocuksu merakın ve fevriliğin, deneyimle harmanlanarak derin bir kadersel bilgeliğe evrilmesi."),
        18: ("Amerikan kalabalığı içinde kendi anadillerinde konuşan iki Çinli", "Dış dünyanın kalabalığı ve gürültüsü içinde, sadece ikinizin çözebildiği o gizli zihinsel titresim ve özel şifrelerle iletişim kurma."),
        19: ("Geleneksel bilgeliği ortaya çıkaran büyük arkaik bir cilt (kitap)", "İlişkinin köklerini, geçmişten veya kadim öğretilerden alınan büyük bir dersle, felsefi bir aydınlanmayla besleme anı."),
        20: ("Çok sayıda seçeneğin bulunduğu bir kafeterya", "Zihinsel dağınıklık veya kararsızlık sınavı; birçok fikir veya seçenek arasından ilişkinin kadersel rotasını ortak bir akılla seçebilme gücü."),
        21: ("Gürültülü bir işçi gösterisi", "Mantık ve duyguların, haklılık ve haksızlığın sert çatışması; ilişkide birikmiş zihinsel basıncın tahliye edilmesi gereken darboğaz."),
        22: ("Hasat festivalinde dans eden çiftler", "Zihinsel uyumun, üretken fikirlerin ve başarılı iletişimin meyvelerini toplama; ilişkinin neşeli ve coşkulu bir kutlamaya dönüşmesi."),
        23: ("Ağacın tepesindeki bir yuvada bulunan üç yavru kuş", "Zihinsel tohumların büyümesi; ortak fikirlerin, planların veya projelerin henüz kuluçka aşamasında olup şefkatle korunmaya ihtiyaç duyması."),
        24: ("Donmuş köy göletinde buz pateni yapan çocuklar", "Soğuk, krizli veya mesafeli dönemlerin üstesinden, iletişimdeki kıvrak bir zeka, neşe ve esneklikle gelebilme yeteneği."),
        25: ("Büyük palmiye ağaçlarını budayan bir bahçıvan", "İlişkinin zihinsel dallarını temizleme; gereksiz detayları, toksik düşünceleri ve geçmiş takıntıları budayarak ana hedefe (gövdeye) odaklanma."),
        26: ("Kış gökyüzüne karşı duran kırağı kaplı ağaçlar", "Duygusal mesafenin veya sessizliğin olduğu dönemlerde bile, aradaki o sağlam zihinsel bağın kristalize olmuş o eşsiz, asil güzelliği."),
        27: ("Kabilesinin kamp kurduğu ormandan çıkan bir çingene", "Zihinsel özgürlük arayışı; alışılmış düşünce kalıplarından ve ilişkinin konfor alanından çıkarak dışarıda yeni bir felsefe deneme cesareti."),
        28: ("İflas yoluyla toplumun yeniden başlama fırsatı vermesi", "Eski iletişim dilinin veya zihinsel yapıların tamamen çökmesi; bu yıkımın ardından sıfırdan, çok daha dürüst ve güçlü bir zihin inşası şansı."),
        29: ("İlkbaharın ilk bülbülü", "Yeniden doğuş, neşeli haberler ve taze fikirler; aradaki iletişimin kıştan çıkarak bahar coşkusuyla ve tatlı bir melodiyle canlanması."),
        30: ("Denize giren güzellerin geçit töreni", "Zihinsel ve estetik uyumun dışarıya cesurca sergilenmesi; ilişkinin sosyal vitrininde özgüvenle, parıldayarak boy gösterme enerjisi.")
    },
    "Yengec": {
        1: ("Aboard a ship sailors lower an old flag and raise a new one (Yelkenlide eski bayrağın inip yenisinin çekilmesi)", "Eski aidiyetlerin, ailevi bağların veya geçmişin sona erip, bu ilişkiyle yepyeni bir 'ortak yuva' kimliğine doğma cesareti."),
        2: ("Sihirli bir halı üzerinde geniş bir araziyi izleyen adam", "İlişkinin, günlük dünyevi dertlerden soyutlanıp, birbirinizin ruhuna üst bir perspektiften ve objektif bir şefkatle bakabilme yeteneği."),
        3: ("Kürklere bürünmüş bir adamın tüylü bir geyiği yönlendirmesi", "En soğuk, zor ve krizli zamanlarda bile, partnerinin o hassas ruhuna (geyiğe) sarsılmaz bir koruyucu kalkan (kürk) olma içgüdüsü."),
        4: ("Fareyle tartışan bir kedi", "Ortak yaşam alanında (yuvada) yaşanan ufak tefek güç savaşları; duygusal sınırların sevgiyle mi yoksa manipülasyonla mı test edileceğinin sınavı."),
        5: ("Tren yolunda trenin çarpıp parçaladığı bir otomobil", "Kaderin o durdurulamaz akışına (tren) karşı kişisel egoyla inatlaşmanın yıkıcılığı; bu ilişkide sisteme ve ilahi plana mutlak teslimiyetin şart olması."),
        6: ("Yuvalarını tüylendiren oyun kuşları", "Evliliğe, ortak yaşama ve yuvaya duygusal/maddi yatırım yapma vakti; birbirinizin kalbinde o en güvenli ve sıcak köşeyi inşa etme erdemi."),
        7: ("Ay ışığında dans eden iki doğa ruhu (peri)", "Mantığın bittiği yerde başlayan masalsı, çocuksu ve sihirli duygusal uyum; ilişkinin rasyonel dünyadan çıkıp rüya aleminde şifalanması."),
        8: ("İnsan kıyafetleri giymiş bir grup tavşanın geçit töreni", "Dış dünyanın, ailelerin veya toplumun ilişkiye dayattığı sahte formlara (kıyafetlere) bürünme tehlikesi; yapaylıktan kaçıp öze dönme uyarısı."),
        9: ("Gölette balık yakalamaya çalışan küçük, çıplak bir kız çocuğu", "İlişkinin en saf, en masum, en savunmasız anlarına geri dönerek o ilk günkü heyecanı (balığı) telaşsızca yakalama ve koruma çabası."),
        10: ("İlk kesim aşamasındaki büyük ve işlenmemiş bir elmas", "Ham ve ilkel sevginin zamanla, krizlerle ve sabırla işlenerek paha biçilmez, ebedi bir sadakat pırlantasına dönüşme süreci."),
        11: ("Ünlüleri taklit eden bir palyaço", "İlişkideki egoları, gerginlikleri ve çatışmaları muazzam bir mizahla, şefkatli bir alayla yumuşatarak yuvaya neşe katma yeteneği."),
        12: ("Aurasından reenkarne bir bilge olduğu anlaşılan bebeği emziren kadın", "Birbirinizin o naif, çocuksu yaralarını sararken aslında çok kadim ve kadersel bir ruhu beslediğinizin o büyük, kutsal farkındalığı."),
        13: ("İncelenmek üzere uzatılan, belirgin başparmaklı bir el", "İlişkide iradenin, karakterin ve somut eylemlerin (el) maskesiz bir şekilde dürüstçe masaya yatırılması ve yüzleşilmesi."),
        14: ("Kuzeydoğudaki karanlık ve dipsiz boşluğa bakan çok yaşlı bir adam", "Bilinmeyene, geleceğe ve yaşlılığa karşı birlikte geliştirilen sarsılmaz bir ruhsal bilgelik; ebediyete el ele yürüme cesareti."),
        15: ("Büyük bir ziyafet sonrası lüks bir yemek salonunda dinlenen konuklar", "İlişkinin zor günlerini atlatıp maddi/manevi tatminin, doygunluğun ve yuva huzurunun doruğuna ulaşma; o büyük ruhsal hasat anı."),
        16: ("Kadim bir kitap yardımıyla önündeki mandalayı inceleyen bir adam", "Aranızdaki bu derin ve karmaşık kadersel yapıyı (mandala), yüzeysel akılla değil, evrensel yasalar ve ruhsal bilgelikle çözme arzusu."),
        17: ("Bilgiye ve hayata dönüşen tohum", "Atılan ufacık bir sevgi ve şefkat tohumunun, köklenerek muazzam bir yaşam alanına (koca bir aileye) dönüşmesinin ilahi müjdesi."),
        18: ("Yavrularını beslemek için toprağı eşeleyen bir tavuk", "Aileyi, çocukları veya ilişkinin ortak geleceğini korumak için gösterilen o bitmek bilmeyen, fedakar ve kutsal anaç/ataç emek."),
        19: ("Evlilik töreni yöneten bir rahip", "İlişkinin kadersel bir akitle mühürlenmesi; sadakatin sadece dünyevi bir imza değil, ilahi bir onayla ve evrensel bir sözleşmeyle taçlanması."),
        20: ("Serenat yapan Venedik gondolcuları", "Duygusal dalgalanmaların, krizlerin ve suların üzerinde (gondol) muazzam bir zarafetle, romantizmle durarak aşkı kutlama gücü."),
        21: ("Operada hünerini sergileyen ünlü bir şarkıcı", "Birbirinize olan o derin sevginizin, fedakarlığınızın ve aidiyetinizin doruk noktasını yaşama ve bunu dünyada saygın bir duruşla sunma."),
        22: ("Yelkenliyi bekleyen genç kadın", "Kadersel partneri, beklenen ruhsal kurtarıcıyı veya ilişkinin gelecekteki o huzurlu günlerini sarsılmaz bir inanç, sadakat ve sabırla bekleme."),
        23: ("Bir edebiyat kulübünün toplantısı", "Sadece duygusal değil, ortak entelektüel değerlerin, kültürel köklerin ve paylaşılan ideallerin ilişkinin yatağını ve çatısını güçlendirmesi."),
        24: ("Güney denizlerinde küçük bir adada mahsur kalan kadın ve iki erkek", "İlişkide kadersel bir izolasyon, kıskançlık testleri veya aidiyetin, sadakatin sınırlarının en uç noktalarda, krizlerle sınanması."),
        25: ("İrade sahibi bir adamın üzerine inen üstün bir gücün gölgesi", "Kişisel egoların ve inatlaşmaların, ilişkinin ilahi kaderi (üstün güç) karşısında ezilmesi; evrene ve bu aşka tam teslimiyete zorlanma."),
        26: ("Lüks bir evin kütüphanesinde okuyan misafirler", "Zengin bir ruhsal ve zihinsel yuvada muazzam bir huzur bulma; tartışmaların yerini ortak bilgeliğin ve sessiz bir ahengin alması."),
        27: ("Lüks evlerin olduğu kanyonda şiddetli fırtına", "Konfor alanını ve yuvayı vuran kadersel kriz! İlişkinin sarsılmaz köklerinin, maddi ve manevi olarak dayaniklilik testinden geçmesi."),
        28: ("Beyaz sevgilisini kabilesiyle tanıştıran Kızılderili kız", "İki farklı kökün, ailenin, geleneğin veya geçmişin tek bir sevgi köprüsüyle birleştirilmesi; köklenmenin getirdiği o büyük uyum sınavı."),
        29: ("Yenidoğan ikizleri altın terazide tartan Yunan ilham perisi", "İçsel dualitenin (mantık ve duygu, sen ve ben) ilişki içinde kusursuz, ilahi ve yorulmaz bir dengeye oturtulduğu o altın mühür."),
        30: ("Amerikan Devrimi'nin kızı", "Köklere, geçmişe ve birbirinize duyulan o derin onur; ilişkinin dünyadaki gücünü ve devrimsel guccunu bu sarsılmaz aidiyetten alması.")
    },
    "Aslan": {
        1: ("Hırslarının dürtüsüyle hayati enerjisi harekete geçen bir adamın başına kan sıçraması", "İlişkide egonun ve tutkunun aniden alevlenmesi; ortak bir hedefe kilitlenip durdurulamaz bir güçle (guce) eyleme geçme uyanışı."),
        2: ("Bir kabakulak salgını", "İlişki içindeki bir krizin veya bulaşıcı bir karamsarlığın hızla yayılması tehlikesi; toksik enerjileri başkalarına bulaştırmadan izole etme sınavı."),
        3: ("Saçlarını omuzlarına dökmüş, gençlik kıyafetleri içindeki orta yaşlı bir kadın", "İlişkinin zamana ve yaşa meydan okuması; rutinin sıkıcılığından sıyrılıp, ilk günkü o taze, isyankar ve özgür ruhu yeniden kuşanma."),
        4: ("Av seferinden getirdiği ganimetlerin yanında duran resmi giyimli yaşlı adam", "Ego ve gurur sınavı! Geçmiş başarılarla veya ilişkinin sosyal statüsüyle övünme; partneri bir ganimet gibi değil, bir eş gibi görme uyarısı."),
        5: ("Derin bir kanyonun üzerinde yükselen heybetli kaya oluşumları", "Sarsılmazlık mühürü! İlişkinizin, etrafındaki tüm zamanın yıpratıcılığına ve derin krizlere rağmen dimdik, asil ve yıkılmaz bir kule gibi durması."),
        6: ("Eski moda, muhafazakar bir kadının, günümüzün modern bir kızıyla yüzleşmesi", "Geçmişin köklü değerleri ile geleceğin özgürleşme arzusunun çarpışması; ilişkide eski tabuları sevgiyle yıkarak modern bir ortak dil bulma."),
        7: ("Gece gökyüzünde ışıl ışıl parlayan takımyıldızlar", "Ruhlarınızın en karanlık zamanlarda bile evrensel bir rehberlikle (kadersel pusula) korunduğunu ve ilişkinizin ilahi bir plana hizmet ettiğini idrak etme."),
        8: ("Devrimci ideallerini yayan bir aktivist", "İlişkide bir şeyleri kökünden değiştirme ve yeniden inşa etme tutkusu; ancak bu isyanın partneri yıkmak için değil, bağı özgürleştirmek için yapılması gerekliliği."),
        9: ("Nefesleriyle parlayan cama şekil veren cam üfleyicileri", "Karmik simya! Birbirinizin ruhuna (nefes) dokunarak, başlangıçta ham olan bu bağı muazzam bir estetiğe ve kalıcı bir esere dönüştürme ustalığı."),
        10: ("Güneş ışığı tarlayı doldururken parlayan sabah çiy damlaları", "Karanlık bir dönemin ardından gelen taptaze bir ruhsal uyanış; ilişkinin her sabah yeniden, umutla ve ilahi bir iyimserlikle yıkanması."),
        11: ("Devasa bir meşe ağacının dallarından sarkan salıncakta sallanan çocuklar", "Çok köklü, korunaklı ve sarsılmaz bir güvenin (meşe ağacı) gölgesinde; ilişkinin en masum, eğlenceli ve çocuksu tarafını korkusuzca yaşama lütfu."),
        12: ("Süslü fenerlerle aydınlatılmış bir çimenlikte yetişkinlerin akşam partisi", "İlişkinin sosyal vitrininde parlama zamanı; gururla, estetikle ve dış dünyanın da onaylayıp hayran kalacağı bir uyumla sahneye çıkma."),
        13: ("Kulübesinin verandasında sallanan yaşlı bir deniz kaptanı", "Büyük fırtınaları, krizleri ve sabir testlerini atlatmış bir ilişkinin, artık deneyim ve bilgelikle geçmişe gülümseyerek baktığı o huzurlu demlenme anı."),
        14: ("Dışavurum fırsatları arayan bir insan ruhu", "Sadece kalplerde gizli kalan sevginin artık somut dünyada bir esere, bir evliliğe veya kalıcı bir ortak yaratıma dönüşme ihtiyacının patlaması."),
        15: ("Tezahürat yapan kalabalık bir caddede ilerleyen görkemli bir geçit töreni", "İlişkinin kendi krallığını ilan etmesi; gösterişli, cesur ve çevreden yüksek onay (alkış) alan asil bir kadersel zirve noktası."),
        16: ("Fırtına dindiğinde, doğanın parlak güneş ışığı altında sevinci", "Çok ağır bir krizin veya güç savaşının ardından gelen o muazzam rahatlama; gözyaşlarının yerini yıkanmış, tertemiz bir aşka bırakması."),
        17: ("Dini ilahiler söyleyen gönüllü bir kilise korosu", "Farklı seslerin (egoların) tek bir yüce amaç uğruna uyumlanması; ilişkinin dünyevi boyuttan çıkıp ruhsal bir adanmışlıkla bütünleşmesi."),
        18: ("Öğrencileri için deney yapan bir kimyager", "İlişkinin matematiğini ve kimyasını çözme zamanı! Formüllerin, elementlerin ve duyguların nasıl reaksiyon verdiğini deneyimleyerek ustalaşma."),
        19: ("Bir tekne partisi (yüzen ev)", "Bağlılığı bir pranga olarak değil, birlikte seyredilen eğlenceli ve özgür bir yolculuk olarak görme; ilişkinin sınırlarını esnetip neşeye odaklanma."),
        20: ("Güneş ritüeli yapan Zuni Kızılderilileri", "Varlığınızın ve bu muazzam aşkın kaynağına (Güneş'e/Yaradan'a) derin bir şükran duyma; egoyu sıfırlayıp ilahi güce saygıyla bağlanma."),
        21: ("Uçmaya çalışırken başları dönen ve kanat çırpan sarhoş tavuklar", "İlişkide kapasitenin ötesinde, gerçek dışı beklentilere veya abartılı egolara kapılma uyarısı; uçmaya çalışırken komik veya krizli durumlara düşme riski."),
        22: ("Görevini yerine getiren bir posta güvercini", "Sadakatin mührü! En zor şartlarda bile birbirinize verdiğiniz kadersel sözü tutma ve sevginin o kutsal mesajını hedefine ulaştırma erdemi."),
        23: ("Sirkte eyersiz ata binen bir binicinin heyecanlı kalabalığı büyülemesi", "İlişkinin tehlikeli, riskli ama bir o kadar da hipnotik durus gucu; engelleri ve kuralları hiçe sayarak cesaretle şov yapma ve başarma."),
        24: ("Fiziksel görünümünü tamamen ihmal edip ruhsal aydınlanmaya odaklanmış bir adam", "Dış dünyadaki gösterişin, egonun ve estetiğin anlamını yitirip; ilişkinin tamamen bilinçaltı, mistik ve yeraltı simyasına odaklanması."),
        25: ("Uçsuz bucaksız ve acımasız bir çölü geçen büyük bir deve", "Muazzam bir Dayaniklilik testi! İlişkinin kurak ve krizli süreçlerinde, içsel su (sevgi) rezervlerinizi kullanarak sabırla ve inatla hedefe yürüme."),
        26: ("Ağır bir fırtınanın ardından beliren gökkuşağı", "Kadersel bir söz! Çekilen acıların ve dökülen gözyaşlarının ardından evrenin ilişkinize sunduğu o ilahi umut, onarım ve şifa köprüsü."),
        27: ("Doğu gökyüzünde şafağın parıltısı", "Karanlık bir döngünün sonsuza dek kapanması; bu aşkla birlikte ruhun yeni bir bilince, umuda ve güneşe (uyanışa) gözlerini açması."),
        28: ("Büyük bir ağacın dalında cıvıldayan birçok küçük kuş", "Ortak çevrenin, dostlukların ve ufak neşelerin ilişkiyi beslemesi; ağır dramalardan uzaklaşıp basit, eğlenceli ve hareketli bir iletişime geçiş."),
        29: ("İnsan formunda yeniden doğmak üzere okyanus dalgalarından çıkan deniz kızı", "Büyük Simyasal Evrim! Bilinçsiz duyguların, kıskançlıkların (su) geride bırakılıp, ilişkinin tam idrak sahibi, olgun ve somut bir yapıya (insana) dönüşmesi."),
        30: ("Mührü açılmış (mühürsüz) bir mektup", "Mutlak şeffaflık! Sırların, maskelerin ve gizli ajandaların tamamen ortadan kalktığı; kalplerin birbirine dürüstçe, sansürsüzce okunmaya açıldığı son derece özgür bir faz.")
    },
    "Basak": {
        1: ("Bir adamın başındaki hayvan postu", "Kendi ilkel, hayvansal dürtülerini veya ham enerjini; disiplin, çalışma ve pratik zeka ile ehlileştirip üst bir formda kullanma yeteneği."),
        2: ("Geniş bir düzlükte yer alan, beyaz bir haç", "İlişkideki fedakarlığın ve hizmetin bir 'yük' değil, ilişkinin kalıcı huzurunu (kutsal yönünü) ayakta tutan temel sütun olduğunu fark etme."),
        3: ("İki melek yardıma hazır", "Birlikte en çok tıkandığınız, kusursuzlaştırmaya çalıştığınız kriz anlarında; evrenin size pratik bir çözümle, sezgisel bir yardımla kapı açması."),
        4: ("Genç bir adamın hayal gücü, gerçek bir boyuta dönüşüyor", "İlişkideki hayallerin ve uçuşan fikirlerin; çalışma, detaylara odaklanma ve pratik adımlarla somut bir esere (yuvaya/başarıya) dönüşmesi."),
        5: ("Bir adamın elinde rüya dolu bir peri masalı kitabı", "Gündelik hayatın pratikliğinde (Başak) kaybolurken, aşkın o masalsı ve ilahi kökenini (Peri masalı) unutmadan yaşama sanatı."),
        6: ("Süslemelerle dolu bir dans salonu", "Detaylarda estetik; ilişkinin gündelik düzenini kurarken, bu düzeni adeta bir sanat eseri veya bir dans gibi özenle, kusursuzca yönetme başarısı."),
        7: ("İki kadeh şarapla dolu bir masa", "Gündelik hayatın pratik koşturmacasında, durup birbirinize ayırdığınız o küçük ama nitelikli paylaşım anlarının kadersel değeri."),
        8: ("Bir kız, evcil kuşları besliyor", "İlişkideki küçük, savunmasız ve ilgiye muhtaç olan (çocuksu tarafınız, zayıf yanlarınız) parçaların şefkatle ve düzenle beslenip korunması."),
        9: ("Kendi kendini boyayan bir ressam", "İlişkiyi ve kendinizi dışarıdan bir gözle, adeta bir sanatçı titizliğiyle gözlemleyip; hataları anında revize ederek kusursuzluğa ulaşma çabası."),
        10: ("İki başlı bir adam, hayata bakıyor", "Mantık ve sezgiyi aynı anda kullanma; hem pratik işlere hem de ilişkinin gelecekteki ruhsal ihtiyaçlarına aynı anda odaklanabilme yetisi."),
        11: ("Yeni bir günün doğuşuyla parlayan, el değmemiş bir vadi", "İlişkideki eski krizlerin ve hataların, Başak'ın analitik temizliğiyle yok olması; her sabah taptaze bir başlangıç yapma temizliği."),
        12: ("Hazinesini arayan bir adam", "İlişkinin gündelik işleri (ev, iş, rutin) içinde, aslında aradığınız o büyük kadersel hazinenin (ruhsal olgunluk) saklı olduğunu fark etme."),
        13: ("Halkın önünde konuşan devlet adamı", "İlişkinin düzenini, kurallarını veya vizyonunu dış dünyaya karşı temsil etme; bir sistem/ekol gibi disiplinli ve saygın bir birliktelik."),
        14: ("Fotoğrafı çekilen bir aile albümü", "Zamanın akışına karşı duruş; ilişkinin her evresini, hatırasını ve dersini bir disiplinle kayda alıp geleceğe bir 'yaşanmışlık mirası' olarak taşıma."),
        15: ("Oyuncak bebeklerle oynayan bir kız çocuğu", "İlişkideki sorumlulukları, rolleri ve krizleri, bir oyun ciddiyetiyle; yargılamadan, suçlamadan, adeta bir simülasyon gibi deneyimleyerek çözme."),
        16: ("Volkanik patlamanın ardından oluşan verimli topraklar", "En büyük krizlerin (patlama), aslında Başak'ın analiz gücüyle işlendiğinde ilişkinizi gelecekte besleyecek en bereketli toprakları (tecrübe) oluşturması."),
        17: ("Halkı için dua eden bir din adamı", "İlişkideki gündelik hizmetin bir ibadete dönüşmesi; birbirinizin eksiklerini kapatmanın veya düzeni kurmanın, aslında birbirinizin ruhunu kutsamak olduğu bilinci."),
        18: ("Büyük bir kütüphanede çalışan araştırmacı", "İlişkinin kadersel kodlarını çözme arzusu; birbirinizin geçmişini, psikolojisini ve bu ilişkinin 'neden' var olduğunu bilimsel/analitik bir titizlikle araştırma."),
        19: ("Çiçek açmış bir nar ağacı", "Pratik ve sade görünümün altında, çok sayıda bereketli tohumun ve hayat enerjisinin saklı olduğu; ilişkinin potansiyelinin taşması."),
        20: ("Tarlasında hasat yapan bir köylü", "Emek verilen, planlanan ve ilmek ilmek işlenen her türlü kadersel çalışmanın, tam vaktinde ve bollukla karşılığını alma günü."),
        21: ("Kızlar basketbol takımı", "Ortak bir hedef uğruna koordineli çalışma; herkesin kendi rolünü kusursuz yaptığı, ego çatışması olmayan, tıkır tıkır işleyen bir ekip olma hali."),
        22: ("Kraliyet armasını taşıyan bir kraliyet muhafızı", "Sarsılmaz sadakat ve sistem koruyuculuğu; ilişkinin değerlerini, düzenini ve özel dünyasını dış tehlikelere karşı çelik bir disiplinle muhafaza etme."),
        23: ("Bir hayvanat bahçesinde kafes temizleyen bir adam", "İlişkideki vahşi, kontrolsüz veya hayvansal içgüdülerin; titiz bir temizlik ve disiplinle, sisteme zarar vermeyecek şekilde evcilleştirilmesi."),
        24: ("Büyük bir sarayın kapısında bekleyen gardiyan", "İlişkinin 'Kutsal Yuvaya' giriş ve çıkışlarını kontrol etme; kimlerin (veya hangi enerjilerin) bu alana dahil olup olmayacağına dair katı ve güvenli sınırlar."),
        25: ("Bahçesindeki otları temizleyen bir adam", "İlişkinin ruhsal topraklarını 'yabani otlardan' (toksik düşünceler, vesveseler) arındırma; bağı sadece saf ve işlevsel olanla besleme."),
        26: ("Bir ağaca asılı, henüz olgunlaşmamış meyveler", "İlişkinin planlarının veya hayallerinin henüz zamanının gelmediği; acele etmeden, sabırla ve düzenle olgunlaşmasını (hasadını) bekleme disiplini."),
        27: ("Güneş ışığıyla parlayan bir çaydanlık", "İlişkinin gündelik rutinini (çay/ritüel) kutsallaştırma; sıradan bir çay anını bile muazzam bir huzur ve şifa anına dönüştürme ustalığı."),
        28: ("Kel başını öne eğmiş bir keşiş", "İlişkide egonun tamamen geri çekilmesi; zihinsel kibrin yerini, sessiz bir hizmetin ve derin bir tevazunun alması."),
        29: ("Gizli bir kapıdan çıkan bir insan", "İlişkideki sorunları, krizleri ve tıkanıklıkları, kimsenin fark etmediği pratik, dahice ve gizli bir çıkış yoluyla (yöntemle) aşabilme."),
        30: ("Gökyüzünü süpüren bir yıldız süpürgesi", "İlişkinin kadersel arınması! Artık Başak'ın detaycı disiplini, gökyüzündeki kadersel tozları ve karmik tortuları bile temizleyerek, bağı kristal kadar berrak bir hale getirmiştir.")
    },
    "Terazi": {
        1: ("Bir kelebek kanadının üzerinde, üzerinde bir ok olan bir ok işareti", "İlişkideki duygusal veya zihinsel yönelimin (ok) belirlenmesi; aranızdaki etkileşimin hangi kadersel hedefe doğru uçtuğunu idrak etme."),
        2: ("Bir adamın elinde bulunan altı parıltılı ışık küresi", "İlişkinin yaşamın temel güçlerini (ışık kürelerini) dengede tutma ve bu güçleri ortak bir estetikle yönetebilme yetisi."),
        3: ("Şafak vakti ormanda yeni doğan bir gün", "Geçmişin tüm ağırlıklarını silen taze bir başlangıç; ilişkinin her yeni güne, temiz bir sayfayla ve umutla başlama disiplini."),
        4: ("Bir gruptan ayrılarak kendi yoluna giden bir adam", "İlişkide 'biz' olurken bireysel özgürlüğünü ve özgün karakterini koruyabilme; bağımlı değil, bağlı olma sanatı."),
        5: ("İçinde bir içki kadehi olan parlak bir halka", "Birlikteliğin getirdiği o kutsal, içsel bütünlük; birbirinizi 'tamamlanmış bir halka' gibi sarıp sarmalama ve bu bağın tadını çıkarma."),
        6: ("İçinde bir adamın figürü olan küçük bir heykel", "Birbirinizin hayatında kalıcı, asil ve estetik bir iz bırakma; ilişkinin dünyada somut bir sanat eseri gibi hatırlanması."),
        7: ("Fırtına öncesi sessizce duran bir gökyüzü", "Krizlerden önceki o kritik, sessiz ve dingin gözlem anı; yaklaşan kadersel değişimi, tartışmadan, sadece sezgisel olarak hissedip önlem alma."),
        8: ("Bir şöminenin başında ısınan bir grup insan", "En soğuk krizlerde bile ilişkinin iç sıcaklığını, güvenini ve yuva olma özelliğini, birbirinizin varlığıyla diri tutma yeteneği."),
        9: ("Üç usta sanatçı kendi atölyelerinde çalışıyor", "İlişkinin ortak vizyonu için her iki tarafın da kendi yeteneklerini, zekasını ve emeğini bağımsızca ama uyum içinde üretmesi."),
        10: ("Kano yapan bir grup insan", "İlişkinin akışında, herkesin aynı ritimle kürek çekmesi; çatışmaları dindirip, tek bir kadersel yöne doğru (hedefe) senkronize hareket etme."),
        11: ("Gözlerinde bir ışık olan bir adam", "İçsel aydınlanma! İlişkideki sorunları, karşıdakinin niyetini ve evrensel mesajı, görünür olandan çok daha derin bir vizyonla görme."),
        12: ("Madenden yeni çıkarılmış bir elmas", "İlişkinin ham ve işlenmemiş potansiyelinin, zorluklarla parlatılarak gerçek, paha biçilemez ve dayanıklı bir değer haline gelmesi."),
        13: ("Şapkasını çıkarmış, güneşin altında duran bir adam", "Egoların tamamen aradan çekilmesi; birbirinize ve kadersel rotanıza karşı o derin, maskesiz ve tevazulu teslimiyet."),
        14: ("Gökyüzünde birbirine doğru koşan iki melek", "İlişkinin ilahi bir el tarafından desteklendiği o anlar; krizlerin, tesadüf gibi görünen mucizevi yardımlarla çözüme kavuşması."),
        15: ("Bir yuvada toplanmış olan kuş yavruları", "İlişkinin en savunmasız, en çocuksu ve en korunmaya muhtaç olduğu o evre; birbirinizin içindeki 'çocuğu' sarmalayıp güvenle büyütme."),
        16: ("Bir adamın elinde tuttuğu bir pusula", "İlişkinin kadersel rotasını sapmadan, evrensel pusulaya (vicdan ve hakikat) uygun şekilde çizme becerisi."),
        17: ("Sık ağaçlıklı bir ormanda kaybolmuş bir adam", "İlişkide karmaşa ve belirsizlik dönemi! Dış dünyadan (başkalarının fikirleri) etkilenip kendi kadersel merkezinden sapma riski."),
        18: ("Eski bir kalenin surlarına asılı boş bir zırh", "Geçmişin savunma mekanizmalarının artık gereksizleşmesi; birbirinize karşı savunmasız (maskesiz) kalabilme cesareti."),
        19: ("Bir grup insan bir sanat eserini inceliyor", "İlişkinin dışarıya nasıl göründüğüne dair farkındalık; ilişkinin değerini, estetiğini ve başarısını objektif bir şekilde değerlendirme."),
        20: ("Tüm çiçeklerin açtığı bir mevsim", "İlişkide yaratıcılığın, aşkın ve paylaşımın zirvesi; her şeyin tıkır tıkır işlediği, güzelliklerin ve bereketin taşma noktası."),
        21: ("Bir fırtınanın ortasında dimdik duran bir çam ağacı", "En sarsıcı dış etkilerde bile, birbirinize olan bağınızın esnemesi ama asla kırılmaması; köklerinizin sarsılmaz gücü."),
        22: ("Bir tepenin zirvesinde yanan kutsal bir ateş", "İlişkinin kadersel amacının, herkesin görebileceği kadar net ve yüksek olması; ortak bir inançla dünyayı ısıtma gücü."),
        23: ("Bir aynada kendini izleyen bir kedi", "İlişkideki 'ben' ve 'sen' ayrımının netleşmesi; partnerinizin gözlerinde kendi kusurlarınızı ve güzelliklerinizi görebilme farkındalığı."),
        24: ("Bir adamın elinde bulunan eski bir anahtar", "İlişkinin kilitli olan tüm kadersel kapılarını açacak o çok özel, kadim bilgeliğe veya yönteme erişme (FBST'nin kendi anahtarı)."),
        25: ("Gökyüzünde süzülen bir kartal", "İlişkinin dünyevi dertlerin çok üzerine çıkması; perspektif, uzak görüşlülük ve kadersel bütünlüğü yukarıdan bir tanrısal bakışla görme."),
        26: ("Bir kartalın pençelerinde bir yılan", "Krizin, manipülasyonun veya korkunun (yılan), ilişkinin en yüksek vizyonu (kartal) tarafından etkisiz hale getirilip şifaya dönüştürülmesi."),
        27: ("Bir bahçede oynayan çocukların kahkahaları", "Ciddiyetin ve sorumlulukların arasında, ilişkinin o en saf, en neşeli ve çocuksu neşesini koruma zorunluluğu; mutluluk bir seçimdir."),
        28: ("Bir adamın büyük bir titizlikle kütüphane raflarını düzenlemesi", "İlişkinin geçmişini, anılarını ve öğrendiği dersleri zihinsel bir düzene oturtma; hatıraların birikim (bilgelik) olarak tutulması."),
        29: ("Güneşin batışında yanan ufuk çizgisi", "Bir devrin kapanışı! Artık ilişkinin bir aşamasının bitip, yeni ve bambaşka bir seviyeye geçmeden önceki o büyüleyici geçiş aralığı."),
        30: ("Dünya sahnesinde rolünü oynayan bir oyuncu", "İlişkinin evrensel tiyatrodaki kadersel görevi; herkesin bir rolü olduğu gibi, sizin ilişkinizin de dünyada 'temsil ettiği' o ilahi mesajı dürüstçe oynama.")
    },
    "Akrep": {
        1: ("Gece yarısı gökyüzünde parlayan, gözetleyen bir göz", "İlişkinin her anının evrensel bir gözlem altında olduğu; sadakatin ve niyetin en derin katmanlarda test edildiği o uyanık duruş."),
        2: ("Kırık bir şişeden sızan esansın kokusu", "Geçmişten gelen bir acının veya bastırılmış bir duygunun serbest kalarak ilişkinin havasını tamamen değiştirmesi; şifalanma sürecinin başlangıcı."),
        3: ("Evcilleştirilmeye çalışılan vahşi bir ev kedisi", "İlişkideki asi, kontrol edilemez ve özgür ruhlu yanların; şefkatle ve sabırla yuvaya/sisteme dahil edilme sınavı."),
        4: ("Bir mum ışığında elindeki kağıtları okuyan genç bir adam", "İlişkinin kadersel kontratlarını, gizli niyetlerini ve birbirinizin ruhsal haritasını, o karanlıkta bile net bir şekilde okuma/anlama yeteneği."),
        5: ("Kendi kendine yeten, izole bir kaya üzerindeki denizanası", "Kriz anlarında bile dışarıdan destek almadan, ilişkinin kendi içsel dayanıklılığıyla ve kendi kendine yetebilme gücüyle ayakta kalması."),
        6: ("Altın bir madeninde çalışan işçiler", "İlişkinin zorluklarını (toprağı) kazarak, birbirinizin karakterindeki o saklı, paha biçilemez ve asil hazineleri (altınları) gün yüzüne çıkarma çabası."),
        7: ("Derin gölün üzerindeki bir dalgıç", "Duyguların o karanlık ve tekinsiz derinliklerine korkusuzca dalıp, orada saklanan kadersel gizemleri (veya yaraları) birbiriniz için gün yüzüne çıkarma."),
        8: ("Ay'ın ışığını yansıtan bir göl", "İlişkinin, doğrudan güneşin parlaklığıyla değil, geceye özgü o yumuşak, mistik ve sezgisel bir bilgelikle aydınlanması; ruhların gece konuşması."),
        9: ("Kendi yansımasını hayranlıkla izleyen bir zürafa", "İlişkideki 'ben' ve 'biz' arasındaki o ince çizgi; partnerinizin gözlerinde kendi ruhunuzun güzelliğini değil, kendi eksikliklerinizi de görebilme cesareti."),
        10: ("Büyük bir kaza sonrasında kurtarılan bir grup insan", "Büyük kadersel krizlerden sağ çıkma mucizesi; ilişkinin yıkılacak gibi olduğu en karanlık anlarda bile ilahi bir elle kurtarılma."),
        11: ("Bir fırtına sonrasında ağacın dalında bekleyen bir kuş", "Krizli ve fırtınalı süreçlerden sonra gelen o mutlak sessizlik; korkunun yerini alan, artık güvende olduğunuz o huzurlu bekleme anı."),
        12: ("Büyük bir kütüphanede yasaklı kitapları arayan bir öğrenci", "İlişkinin tabu olan, konuşulmayan veya derinlerde saklanan o 'yasak' duygularını cesaretle ortaya çıkarıp yüzleşme arzusu."),
        13: ("Fırtınada limana sığınan dev bir gemi", "Dış dünyanın krizleri ve toplumsal baskılar karşısında, ilişkinin kendi içindeki o sarsılmaz ve güvenli limana (birbirinize) sığınıp korunma gücü."),
        14: ("Bir insanın içindeki derin tutku ormanları", "İlişkinin o tarif edilemez, kontrol edilemez ve vahşi tutku enerjisi; bu ateşi birbirinizi yakmak yerine birlikte dünyayı fethetmek için kullanma."),
        15: ("Yeniden doğuşu kutlayan bir kabile", "Büyük bir yıkımın veya ayrılık korkusunun ardından, ilişkinin küllerinden çok daha güçlü, bilge ve mühürlü bir şekilde yeniden doğması."),
        16: ("Bir çayırda kendi başına dans eden bir kız", "İlişkide, partnerinizin dünyasından bağımsız olarak kendi ruhsal neşenizi koruyabilme; aşkta bağımsız ama birleşik kalabilme becerisi."),
        17: ("Kendi kendini arayan bir sanatçı", "İlişkide partneri bir ayna olarak kullanıp, aslında kendi ruhunuzdaki eksik parçaları tamamlayarak 'bütünleşme' (individuasyon) yolculuğu."),
        18: ("Sessizce akan bir nehrin üzerindeki köprü", "Duygusal geçişler! Krizli sulardan, sarsılmaz bir mantık ve diplomasi köprüsü kurarak birbirinize ulaşabilme."),
        19: ("Kendi gölgesiyle konuşan bir adam", "İlişkide partnerinizin size yansıttığı 'karanlık' yanları yargılamadan, onları kendi gölgenizle barışmanın bir aracı olarak kullanma."),
        20: ("Törenle yakılan eski bir tapınak", "Eski inançların, bitmiş bir yaşantının veya geçmiş bir kadersel döngünün, ilişkinin selameti için büyük bir ritüelle ateşe verilip küle dönüştürülmesi."),
        21: ("Kendi iç dünyasında dev bir şehir kuran bir mimar", "İlişkinin dışarıya değil, birbirinizin ruhunun o uçsuz bucaksız, devasa ve zengin dünyasına kurduğunuz o görkemli ortak yuva."),
        22: ("Alevlerin içinden çıkan anka kuşu", "Mutlak yıkım ve diriliş! İlişkinin tamamen bitti denilen noktasında, bir mucizeyle tüm acıların şifaya dönüşüp çok daha yüce bir formda canlanması."),
        23: ("Bir tarlada yatan ölü bir karga", "Artık işlevi bitmiş olan korkuların, şüphelerin veya eski 'kara' düşüncelerin (karga) ilişkinizden sonsuza dek uzaklaşması, arınma."),
        24: ("Bir adamın elinde tuttuğu, parıldayan kutsal bir kadeh", "İlişkinin o en zorlu krizlerinden süzülüp elde edilen ruhsal iksir; mutlak sadakat ve aşkla içilen o kadersel yaşam şifası."),
        25: ("İki kutup arasında gidip gelen bir el feneri", "Duygusal uç noktalarda (sevgi ve öfke) gidip gelme; ancak her ne olursa olsun, bir el feneri gibi birbirinizin yolunu aydınlatma gayesi."),
        26: ("Bir uçurumun kenarında dimdik duran bir dağcı", "İlişkinin en uç, en tehlikeli ve en krizli noktasında bile, düşmeden, sapmadan, o asil ve sarsılmaz dengede durabilme ustalığı."),
        27: ("Gecenin karanlığını yırtan bir şimşek", "İlişkideki o çok gizli, çok saklı kalmış kadersel bir gerçeğin; beklenmedik, sarsıcı ve aydınlatıcı bir olayla tüm berraklığıyla ortaya çıkması."),
        28: ("Bir nehirde kendi kendine kaynayan sular", "İlişkinin derinlerinde biriken öfkenin veya tutkunun, dışarıdan fark edilmeden içeride fokur fokur kaynaması; patlamadan önce şifalandırma ihtiyacı."),
        29: ("Güneşin doğuşunu bekleyen bir grup insan", "En karanlık kadersel döngünün sonuna gelindiği; birbirinize olan inançla, yeni ve aydınlık bir dönemin başlamasını sabırla bekleme."),
        30: ("Mükemmel bir şekilde dengelenmiş bir terazinin iki kefesi", "Akrep'in o uçsuz bucaksız krizli derinliğinden, artık mutlak bir ruhsal dengeye ve hakikate ulaşıldığı o son kadersel durak.")
    },
    "Yay": {
        1: ("Gece gökyüzünde parlayan sönük bir yıldızın aniden patlayarak nova'ya dönüşmesi", "İlişkide uzun süredir durgun olan bir potansiyelin veya vizyonun, aniden patlayarak tüm hayatınızı aydınlatan kadersel bir rehbere dönüşmesi."),
        2: ("Sıcak bir ocağın başında, elleriyle yüzünü ısıtan bir beyaz rahibe", "İlişkinin en krizli, soğuk ve belirsiz anlarında bile; sarsılmaz bir inançla, kendi ruhsal ısınızı birbirinizin varlığında bulma mucizesi."),
        3: ("İki insan, yeni bir ülkeye ilk adımı atıyor", "İlişkide keşfedilmemiş yepyeni bir boyuta geçiş; ezberlerin bozulup, sınırların aşıldığı o ilk, cesur kadersel keşif adımı."),
        4: ("Uzak bir ülkede, kendi geleneklerini sürdüren bir göçmen", "İlişkinin dış çevreye, topluma veya standartlara uyum sağlamaya çalışırken, aslında kendi köklerine ve özgün felsefesine tutunma çabası."),
        5: ("Kendi içsel ışığını takip eden bir bilge", "Dış dünyanın ne dediğine bakmadan, ilişkinin kadersel rotasını sadece aranızdaki o ortak, ilahi rehberliğe (inanca) güvenerek çizme."),
        6: ("Eski bir kilisenin kapısında dilenen bir adam", "İlişkideki inanç ve şükür sınavı; elinizde olanın değerini bilmeyip sürekli eksikliklere odaklanma tuzağından kurtulma ihtiyacı."),
        7: ("Deniz kıyısında, devasa okyanusa bakan bir adam", "İlişkinin sahip olduğu o devasa, uçsuz bucaksız kadersel potansiyeli idrak etme; küçük sorunları, okyanusun büyüklüğü içinde eritme."),
        8: ("Bir taşın üzerine oyulmuş, silinmeye yüz tutmuş bir yazı", "Geçmişten gelen bir kadersel uyarının veya kadim bir öğretinin, ilişkinizin rotasını değiştirecek bir mesajla tekrar hatırlanması."),
        9: ("Dünyayı gezen bir grup öğrenci", "İlişkinin hayatı bir 'öğrenim alanı' olarak görmesi; birlikte dünyayı gezmek, kitaplar okumak veya felsefi bir yolculuğa çıkmak en büyük ortak bağınızdır."),
        10: ("Eski bir tiyatro sahnesinde prova yapan oyuncular", "İlişkinin yaşam sahnesinde sürekli bir gelişim ve prova halinde olması; hataları dert etmeden, hayatı bir neşe ve ustalıkla sahneleme."),
        11: ("Işıklı bir fenerin, denizde yol gösterdiği bir gemi", "Karanlık, belirsiz ve fırtınalı kadersel süreçlerde, birbirinizin vizyonuyla yolunuzu bulma; aşkın bir pusula gibi netleşmesi."),
        12: ("Bayrağın üzerinde parlayan altın bir güneş", "İlişkinin başarısının ve gücünün, tamamen o ortak inanca ve ilahi vizyona adanmışlıktan gelmesi; ışıkla mühürlenmiş zafer."),
        13: ("Huzur içinde uyuyan bir aslanın başını okşayan bir çocuk", "İlişkideki en güçlü, vahşi ve kontrolsüz tarafların (Aslan), şefkatle (çocuk) ehlileştirilip sevgiyle terbiye edilmesi."),
        14: ("Gökyüzünde asılı kalmış, devasa bir piramit", "İlişkinin ilahi bir düzene, kadim bir geometriye sahip olması; tesadüflerin ötesinde, planlı ve kadersel bir yapı üzerine kurulu oluşu."),
        15: ("Toprağa tohum eken bir çiftçi", "Şu an ilişkinin gördüğü zorlukların aslında gelecekteki büyük hasadın (huzurun/başarının) hazırlığı olduğu bilinci; sabırla ekmek."),
        16: ("Denizlerin üzerinde yükselen, ışık saçan bir şehir", "İlişkinin gerçeklikten kopuk, hayali ve idealist bir ütopya kurma çabası; bu hayalleri yere indirip nasıl yaşanabilir kılacağınızın sınavı."),
        17: ("Kendi içinde dönüp duran bir derviş", "İlişkinin dış dünyadaki kargaşadan sıyrılıp, sadece kendi iç ritmi ve ortak meditasyonları ile huzur bulma; aşkın bir ibadete dönüşmesi."),
        18: ("Savaş meydanında, kılıcını bırakıp dua eden bir şövalye", "Haklı olma savaşını bırakma! İlişkinin en şiddetli krizlerinde bile, silahları (egoyu/eleştiriyi) yere bırakıp birliğe dönme bilgeliği."),
        19: ("Yüksek bir dağın zirvesinden dünyayı izlemek", "İlişkinin günlük sorunlara, basit tartışmalara ve kıskançlıklara, sanki bir dağ zirvesinden bakıyormuş gibi mesafeli, bilge ve huzurlu bir bakış atması."),
        20: ("Gökyüzüne yükselen bir füze", "İlişkinin dünyevi kısıtlamalardan tamamen kurtulup, hızla ve buyuk bir ivmeyle, hayalleri gerçekleştirmek üzere yüksek bir kadersel boyuta sıçraması."),
        21: ("Kendi kendine yeten bir keşiş", "İlişkide bağımlılıktan kurtulup, herkesin kendi manevi merkezini koruduğu; ancak birbirinin ruhunu zenginleştirdiği o asil beraberlik."),
        22: ("Bir çayırda oynayan bebekler", "İlişkinin en saf, en çıkarsız, en neşeli ve sadece 'var olmanın' tadını çıkaran o ilk kadersel evresi; sevginin en yalın hali."),
        23: ("Bir gölün üzerinde süzülen bir kuğu", "Zarafetin, asaletin ve sevginin duru güzelliği; krizli anlarda bile, ilişkinin kendi asil duruşunu ve estetiğini asla bozmaması."),
        24: ("Büyük bir kütüphanede tozlu rafları karıştıran bir adam", "İlişkinin eksik kalan kadersel bilgilerini, geçmişin tozlu hatıralarında veya kadim bir öğretide arayıp bulma zorunluluğu."),
        25: ("Yükseklerden düşen bir yıldız", "Beklenmedik bir ilahi müdahale; ilişkinin gidişatını tek bir anda değiştiren, mucizevi ve kaderi yeniden yazan o göksel işaret."),
        26: ("Bir fırtınada bayrağını dik tutan bir asker", "Kriz ne kadar büyük olursa olsun, ilişkinin ana hedefine, değerlerine ve birbirinize olan bağlılığa sadık kalma yemini."),
        27: ("Bir sanatçının kendi eserini beğenmeyip parçalaması", "Mükemmeliyetçilik sınavı! İlişkideki bazı şeyleri veya bazı yönlerinizi, daha iyisini kurmak için tamamen yıkıp sıfırdan yapma cesareti."),
        28: ("Bir bahçede açan, kışın bile solmayan kırmızı güller", "İlişkinin en imkansız şartlarda, en krizli mevsimlerde bile o 'kırmızı' (tutku ve aşk) rengini koruyup yaşamaya devam etmesi."),
        29: ("Ufukta batarken denizi yutan güneş", "Bir kadersel evrenin kapanışı; ilişkinin bildiğiniz tüm formlarının, yeni ve çok daha parlak bir şafak öncesi karanlığa gömülmesi."),
        30: ("Gökyüzünde el ele tutuşan, melek gibi iki insan", "Kadersel Mühür! İki ruhun, dünyevi rollerini bitirip, artık tamamen ilahi bir kontratla, zamansız ve mekan dışı bir aşkla ebediyen birleşmesi.")
    },
    "Oglak": {
        1: ("Hintli bir şef, kendi kabilesini yönetiyor", "İlişkinin kendi içinde hiyerarşik bir düzen kurması; ortak yaşamın sorumluluklarını, rollerini ve sınırlarını asil bir otoriteyle yönetme becerisi."),
        2: ("Üç gül penceresi, biri parçalanmış", "İlişkinin mükemmeliyetçi yapısında bir çatlak veya noksanlık! Bu kusurun, ilişkinin daha fazla 'dışarıya ışık sızdırmasına' (yeni bakış açılarına) izin vermesi."),
        3: ("İnsan ruhunun, yeni deneyimler için fiziksel bedenini terk etmesi", "İlişkinin dünyevi kısıtlamalardan, maddi yüklerden ve katı sorumluluklardan sıyrılıp, sadece ruhun yüce amaçları için birleştiği o yükselmiş faz."),
        4: ("Grup kutlaması içinde, kendi dünyasında dans eden bir adam", "İlişkide sosyal sorumlulukları (toplum/aile) yerine getirirken, aslında ruhsal olarak kendi kadersel merkezine ve partnerine sadık kalabilme."),
        5: ("Kano yapan yerliler", "Hayatın o sert ve hızlı akan krizli sularında, ilişkinin ritmini kaybetmeden, birbirinize olan güvenle (aynı ritim) hedefe doğru ilerleme."),
        6: ("Kara bir kuş, beyaz bir kuşa dönüşüyor", "Kadersel simya! İlişkideki karanlık, şüpheci veya korku dolu enerjilerin; sarsılmaz bir sadakat ve disiplinle arınıp saf, beyaz bir şifaya dönüşmesi."),
        7: ("Bir kütüphanede çalışan, çok yaşlı bir adam", "İlişkinin geçmişteki tüm tecrübeleri, yaşanmışlıkları ve kadersel dersleri; geleceğin 'imparatorluğunu' kurmak için birer bilgelik kaynağı olarak kullanma."),
        8: ("Evinde, güneşin doğuşunu izleyen bir kadın", "Her gün, her krizden sonra ilişkinin potansiyeline ve yeni bir şafağın getirdiği o temiz, düzenli, disiplinli huzura olan inancı diri tutma."),
        9: ("Cirit atan bir Kızılderili savaşçı", "İlişkideki hedeflerin, hayallerin ve ortak projelerin; keskin bir odaklanma, tam bir kararlilik ve disiplinli bir çabayla (cirit) hedefe fırlatılması."),
        10: ("Eskimiş bir elmas, yeni bir yüzeye yerleştiriliyor", "İlişkinin yıllanmış, tecrübeli ve köklü değerinin; bugünün dünyasında yeni bir statüyle, yeni bir formla tekrar parlatılarak sunulması."),
        11: ("Büyük bir sarayda, hükümdarı bekleyen bir grup insan", "İlişkinin kendi içinde kurduğu o yüksek standartlar ve otorite; dış dünyanın (veya krizlerin) bu sarsılmaz otoriteye saygı duyması."),
        12: ("Bir kuş, kendi yuvasını inşa ediyor", "En temel sorumluluk! İlişkinin her bir çöpünü, her bir detayını; sarsılmaz bir güven, emek ve uzun vadeli bir planla (yuva) örme."),
        13: ("Şarkı söyleyen bir grup insan", "İlişkinin kurallarının ve sorumluluklarının sadece bir görev değil, bir neşe ve uyum içinde (şarkı) yerine getirilmesi; disiplinin sanata dönüşmesi."),
        14: ("Büyük bir kayanın üzerinde duran bir balık", "İlişkinin, duygusal (balık) doğasını; toprağın ve disiplinin o sarsılmaz (kaya) gücüyle birleştirip, duyguları somut bir başarıya dökme."),
        15: ("Yeniden doğuşunu bekleyen bir tohum", "İlişkide kış (kriz) dönemi; her şeyin donduğu, sessizleştiği bu dönemde aslında köklerin o gizli, güçlü ve derin hazırlığı."),
        16: ("Masa başında çalışan bir muhasebeci", "İlişkinin gerçekçi muhasebesi; kim ne veriyor, kim ne alıyor, kadersel borçlar neler? Dürüst bir yüzleşme ve rasyonel düzenleme."),
        17: ("Uzak bir tepede yanan bir fener", "İlişkinin çevresine, diğer insanlara veya birbirinize; kriz anlarında sarsılmaz bir yön, güven ve istikrar (fener) olma görevi."),
        18: ("Eski bir kalenin içinden dışarıyı izleyen bir nöbetçi", "İlişkinin değerlerini ve mahremiyetini; dışarıdan gelebilecek (dedikodu, müdahale) her türlü tehlikeye karşı 7/24 koruma disiplini."),
        19: ("Kendi kendine yeten, asil bir duruş", "Partnerinize muhtaç olduğunuz için değil, birbirinizi seçtiğiniz için birliktesiniz. Ego bağımlılığından özgür, asil bir beraberlik."),
        20: ("Tüm kış boyunca yetecek erzakın depolandığı bir ambar", "İlişkinin gelecek (kriz) planlaması; birbirinize olan güvenin ve kaynakların, zor günlerde birbirinizi ayakta tutacak kadar sağlam olması."),
        21: ("Tırmanılan devasa, karlı bir dağ", "İlişkinin o en zirve, en görkemli, en zorlu kadersel hedefi; o tepeye çıkarken birbirinizin elini bırakmadan, zorluklara göğüs germe."),
        22: ("Bir fırtınada bayrağını dik tutan bir asker", "Sadakat mühürü! Kriz ne kadar büyük olursa olsun, ilişkinin ana hedefine, değerlerine ve birbirinize olan bağlılığa sadık kalma yemini."),
        23: ("Bir kütüphanede tozlu rafları karıştıran bir adam", "İlişkinin eksik kalan kadersel bilgilerini, geçmişin tozlu hatıralarında veya kadim bir öğretide arayıp bulma zorunluluğu."),
        24: ("Kutsal bir sunakta yanan sürekli ateş", "İlişkideki emeğin sürekliliği; bir günlük aşk değil, bir ömür boyu yanan o kutsal hizmet ve adanmışlık ateşi."),
        25: ("Gökyüzünde el ele tutuşan, melek gibi iki insan", "Kadersel Mühür! İki ruhun, dünyevi rollerini bitirip, artık tamamen ilahi bir kontratla, zamansız ve mekan dışı bir aşkla ebediyen birleşmesi."),
        26: ("Kendi eliyle inşa ettiği bir kulübede huzur bulan adam", "İlişkinin dış dünyadan, karmaşadan ve statü hırsından uzaklaşıp, sadece birbirinizin inşa ettiği o basit ve dürüst yuvada bulduğu huzur."),
        27: ("Bir dağın zirvesinde, elindeki meşaleyle dünyayı aydınlatan bir adam", "İlişkinin ulaştığı o bilgelik seviyesi; kendi huzurunu bulup, aynı zamanda diğer çiftlere de kadersel bir rehber/örnek olma."),
        28: ("Bir nehirde kendi kendine kaynayan sular", "Dışarıdan durgun, içeriden derin; ilişkinin o en derin kadersel tortularının, sessizce ama çok güçlü bir şekilde arınma ve dönüşüm süreci."),
        29: ("Güneşin batışında yanan ufuk çizgisi", "Bir devrin kapanışı! Artık ilişkinin bir aşamasının bitip, yeni ve bambaşka bir statüye (imparatorluğa) geçmeden önceki o geçiş aralığı."),
        30: ("Mükemmel bir şekilde dengelenmiş bir terazinin iki kefesi", "Oğlak'ın o katı, disiplinli ve dünyevi yapısından; artık mutlak bir ruhsal dengeye ve ilahi adalete ulaşıldığı son durak.")
    },
    "Kova": {
        1: ("Eski bir misyon şefinin, kabile halkına yeni vizyonlar anlatması", "İlişkide rutinin dışına çıkma; partnerinle birlikte geleceğe dair radikal, özgürlükçü ve sınırları zorlayan yeni bir ortak yaşam vizyonu oluşturma."),
        2: ("Fırtınadan sığınmış bir şemsiye; altındaki iki kişi", "Dünyanın kaosu (fırtına) dışarıdayken, ilişkinin o kendine has, bağımsız ve entelektüel sığınağında birbirinize duyduğunuz o sarsılmaz zihinsel güven."),
        3: ("Taze bir şelalenin, vadideki göle dökülmesi", "Duyguların durgunlaşmasına izin vermeyen, sürekli yenilenen, tazeleyen ve zihni diri tutan o elektrikli tutku akışı."),
        4: ("Bir rahibin, kutsal ritüel için ateş yakması", "İlişkinin günlük sıradanlığını, bir ritüele dönüştürme; aşkı sadece fiziksel değil, evrensel bir bilgi ve hizmet aracı olarak kullanma."),
        5: ("Kendi içsel sesini takip eden bir adam", "İlişkide başkalarının ne dediğine, toplumsal kalıplara değil; sadece aranızdaki o benzersiz, sıra dışı kadersel sese (içgüdüye) güvenme."),
        6: ("Beyaz bir maske takmış, sahnede rol yapan bir oyuncu", "İlişkinin sosyal maskelerle değil, tamamen dürüst bir 'benlik' ile yaşanması; rollerin bitip hakikatin konuşulmaya başlandığı faz."),
        7: ("Deniz kıyısındaki kayalıklarda güneşlenen çocuk", "Zorlukların (kayalık) içinde bile neşeyi, özgürlüğü ve o çocuksu yaratıcılığı koruyabilme; krizlerin içinde huzuru bulma yetisi."),
        8: ("Güzelce düzenlenmiş bir bahçede oturan, kıyafetleri tozlu bir adam", "İçsel zenginliğin dış görünüme veya statüye ihtiyaç duymaması; ilişkinin özünün, dışarıdan nasıl göründüğünden çok daha kıymetli olduğunun farkına varma."),
        9: ("Kuş sürüsünün, fırtınaya karşı uçması", "Engeller ne kadar büyük olursa olsun; ilişkinin o bağımsız, grup bilinciyle hareket eden ve sınırları reddeden özgür ruhuyla fırtınaya meydan okuması."),
        10: ("Gözleri bağlı bir şekilde, denge üzerinde yürüyen adam", "İlişkideki sarsılmaz güven! Partnerinizin yönettiği bir dünyada, gözleriniz kapalı bile olsa (tam teslimiyetle) o denge üzerinde yürüme kararlılığı."),
        11: ("İlham perilerinin dans ettiği bir stüdyo", "İlişkinin sadece bir birliktelik değil, ortak bir 'yaratım merkezi' olması; birlikte üreterek, yazarak veya çizerek dünyayı güzelleştirme."),
        12: ("Tüm kitapların yandığı bir kütüphaneden kurtulan tek bir sayfa", "Eski öğretilerin, geleneksel aşk kalıplarının veya yaşanmışlıkların çöküşü; arta kalan o tek, saf ve gerçek 'aşk hakikati' ile yola devam."),
        13: ("Teleskopla yıldızları izleyen bir bilim insanı", "İlişkinin dünyevi dertlerin ötesine geçip, birbirinizin hayat amacını ve kadersel rotanızı en uzak galaksilere kadar (makro vizyon) okuma arzusu."),
        14: ("Gökyüzünde süzülen renkli bir uçurtma", "İlişkinin her türlü zorlukta bile yükselme, hafifleme ve esnek kalma gücü; bağlarınızın, sizi dünyaya çivilemek yerine özgürleştirmesi."),
        15: ("Yüksek bir dağın tepesinde dikilen fener", "İlişkinin hem kendi yolunu aydınlatması hem de çevresindeki diğer çiftlere (topluma) bir özgürlük/sevgi rehberi olması."),
        16: ("İki farklı dilden şarkı söyleyen bir koro", "İlişkinin uyumu! Farklılıklardan gelen o eşsiz sesin, tek bir kadersel melodide buluşarak ortaya çıkardığı o sıra dışı zenginlik."),
        17: ("Kendi kendini eğiten bir köpek yavrusu", "İlişkide hatalardan ders çıkarma disiplini; kimsenin dışarıdan müdahalesine gerek kalmadan, kendi krizlerini kendi kendine çözen o bağımsız yapı."),
        18: ("Eski bir saatin iç çarklarını temizleyen saatçi", "Zamanın ve kadersel döngülerin kusursuz işlemesi için, ilişkinin mekanik/zihinsel aksaklıklarını büyük bir titizlikle onarma."),
        19: ("Kendi içindeki okyanusu keşfeden bir kaşif", "İlişkinin sadece fiziksel bir birliktelik değil; birbirinizin bilinçaltındaki o uçsuz bucaksız, bilinmez ve gizemli okyanusları keşfetme yolculuğu."),
        20: ("Tüm sınırları yıkan bir vizyoner", "İlişkinin, toplumun size dayattığı 'oğlan-kız', 'eş-karı' veya 'aşk' kalıplarını tamamen reddedip, kendinize has kadersel bir 'birlikte var olma' modeli kurma."),
        21: ("Kendi kendine yeten ve konuşan bir heykel", "Dış dünyanın onayına muhtaç olmayan; kendi güzelliğini, kendi değerini ve kendi sessizliğini yaratabilen asil, bireysel birliktelik."),
        22: ("Işık saçan dev bir bulut", "İlişkinin bir formdan başka bir forma geçişi; artık somut ve katı sorumluluklardan sıyrılıp, sadece saf bir enerji ve ilham alanına dönüşme."),
        23: ("Bir göletin üzerinde yansıyan dolunay", "İlişkinin dünyadaki yansımasının, gökyüzündeki kadersel planla (ay) kusursuz bir uyum içinde olması; niyet ve eylemin birleşmesi."),
        24: ("Kendi elleriyle yaptığı bir müzik aletiyle çalan müzisyen", "İlişkinin müziğinin (uyumunun) başka kimseden değil, tamamen kendi el emeğinizle, kendi kurallarınızla ve kendi enstrümanlarınızla üretilmesi."),
        25: ("Eski bir tapınağın kalıntıları arasında açan orkideler", "İlişkideki eski krizlerin ve yıkılmışlıkların, artık hayatın neşesiyle ve nadide bir güzellikle (orkide) kaplanıp iyileştirilmesi."),
        26: ("Bir adamın gözlerinde parlayan merak", "Sorgulamanın ve keşfetmenin hiç bitmemesi; ilişkinin her gün, sanki partnerinizi ilk kez görüyormuş gibi bir heyecanla keşfedilme zorunluluğu."),
        27: ("Yağmurun altında ıslanan bir çiçek", "Duygusal arınma; ilişkinin o en yoğun ve bazen sert (yağmurlu) süreçlerinde, aslında birbirinizi temizleyip ruhsal olarak daha da canlı kıldığınız gerçeği."),
        28: ("Uçsuz bucaksız bir karda, sadece kendi ayak izleri olan bir adam", "İlişkide açılan o yepyeni, kimsenin yürümediği kadersel bir yol; tamamen size ait, tamamen özgün, tamamen keşfedilmemiş bir gelecek."),
        29: ("Gökyüzünde dans eden renkli ışıklar (Kuzey ışıkları)", "İlişkinin spiritüel bir olgunluğa ermesi; aradaki bağın artık dünyevi kelimelerin ötesine geçip, adeta bir enerji şölenine dönüşmesi."),
        30: ("Dünya sahnesinde, kendine has bir yöntemle yürüyen bir adam", "İlişkinin bir 'ekol' olması; hiçbir kurala, hiçbir modaya veya hiçbir toplumsal baskıya uymadan, kendi kadersel ritminizle dünyada var olma."),
    },
    "Balik": {
        1: ("Halka açık bir pazarda sergilenen kamuya ait ticaret alanı", "İlişkinin bireysel sırlar yerine, birbirinize karşı tam bir şeffaflık ve 'ortak yaşam' alanında dürüstçe var olma sınavı."),
        2: ("Sincapların bir ağaçta birbiriyle oyun oynaması", "İlişkideki o ilk, saf ve masum neşeyi; hiçbir kadersel yük altına girmeden, sadece birbirinizin varlığından keyif alarak yaşama erdemi."),
        3: ("Taşlaşmış bir ağaç gövdesi", "İlişkinin zamanın yıkıcılığına karşı gösterdiği sarsılmaz direniş; birbirinize olan bağlılığınızın artık tarihe kazınmış kadar kalıcı bir form alması."),
        4: ("Küçük bir adada, güneşli bir gün", "İlişkinin dış dünyadan, karmaşadan ve krizlerden yalıtılmış; sadece ikinizin huzur ve ışıkla dolu o kadersel sığınağı."),
        5: ("Kendi içsel dünyasında yaşayan, gizemli bir rahip", "Partnerinizi asla tamamen 'çözemeyeceğinizi' kabul etme; birbirinizin ruhundaki o gizemli ve dokunulmaz kutsal alanlara saygı duyma."),
        6: ("Sihirli bir değneğe sahip bir büyücü", "İlişkideki krizleri veya tıkanıklıkları, rasyonel yollarla değil; ancak birbirinize olan o büyük, ilahi 'aşk büyüsüyle' (şefkatle) çözme ustalığı."),
        7: ("Deniz kıyısında, ağlarını onaran balıkçılar", "İlişkinin duygusal yorgunluklarını (ağları) dürüstçe tamir etme; birbirinizi hırpalamak yerine, yara alan kısımları sevgiyle dikip onarma."),
        8: ("İki aşığın, gün batımında sessizce oturduğu bir bank", "Hiçbir kelimeye, hiçbir eyleme ihtiyaç duymadan; sadece yan yana var olmanın verdiği o mutlak huzur ve ruhsal bütünlük."),
        9: ("Kendi ışığıyla parlayan bir denizanası", "Karanlık ve krizli kadersel süreçlerde bile; ilişkinin kendi içindeki o saf, mistik ışığı yakarak birbirinize yol gösterme yetisi."),
        10: ("Yıldızların altında dua eden bir çocuk", "İlişkinin tüm kaderini, geleceğini ve birbirinizi evrenin o sonsuz şefkatine (Yaradan'a) bırakıp, ilahi akışa mutlak güven."),
        11: ("Işık saçan, mistik bir tapınağın kapısı", "İlişkinin artık bir çift olmanın ötesinde, ilahi bir hizmete veya ortak bir ruhsal amaca hizmet eden bir mabede dönüşmesi."),
        12: ("Denizlerin üzerinde süzülen bir martı", "En büyük krizlerde bile özgürlüğü koruma; ilişkiyi bir hapishane değil, birbirinizin ruhunu gökyüzüne taşıyan bir kanat yapma."),
        13: ("Eski bir tablonun temizlenmesi", "Geçmişin (ilişkinin önceki evrelerinin) üzerine birikmiş tozları ve hayal kırıklıklarını, şefkatle temizleyip o ilk günkü canlılığına döndürme."),
        14: ("Yıldızları gözlemleyen bir astronom", "İlişkinin kadersel rotasını, gündelik dertlere değil; yıldızların (evrensel yasaların) o muazzam ve değişmez rehberliğine göre çizme."),
        15: ("Bir grup insan, bir nehirde yıkanıyor", "Duygusal arınma! İlişkinin tüm ağırlığını, öfkesini ve geçmiş tortusunu, birbirinizin şefkatli sularında (sevgi) tamamen yıkıp arındırma."),
        16: ("Bir çayırda kendi başına dans eden bir kız", "İlişkinin içinde bile, kendi ruhsal neşenizi ve bağımsızlığınızı koruyarak, aşkı bir zorunluluk değil, bir neşe kaynağı yapma."),
        17: ("Kendi gölgesiyle konuşan bilge", "İlişkide partnerinizde gördüğünüz her şeyi, aslında kendi gölgenizin bir yansıması olarak kabul edip, bu aynalıkla bütünleşme."),
        18: ("Sessizce akan nehrin üzerindeki köprü", "Duygusal geçişler; krizli sulardan, sarsılmaz bir mantık ve şefkat köprüsü kurarak birbirinize ulaşabilme."),
        19: ("Kendi iç dünyasında dev bir şehir kuran mimar", "İlişkinin dış dünyadan çok, birbirinizin ruhunun o uçsuz bucaksız, zengin ve huzurlu dünyasında var olması."),
        20: ("Alevlerin içinden çıkan anka kuşu", "Mutlak yıkım ve diriliş! İlişkinin bittiği denilen noktasında, bir mucizeyle tüm acıların şifaya dönüşüp çok daha yüce bir formda canlanması."),
        21: ("Kendi eliyle yaptığı müzik aletiyle çalan müzisyen", "İlişkinin uyumunun başka kimseden değil, tamamen kendi içinizden gelen o özel titresimta, özgün bir şekilde üretilmesi."),
        22: ("Eski bir tapınağın kalıntıları arasında açan orkideler", "İlişkideki eski krizlerin ve yıkılmışlıkların, artık nadide bir güzellikle iyileştirilmesi."),
        23: ("Bir adamın gözlerinde parlayan merak", "Sorgulamanın ve keşfetmenin hiç bitmemesi; partnerinizi her gün yeniden keşfetme arzusu."),
        24: ("Yağmurun altında ıslanan bir çiçek", "İlişkinin o en yoğun ve bazen sert (yağmurlu) süreçlerinde, aslında birbirinizi temizleyip ruhsal olarak daha da canlı kıldığınız gerçeği."),
        25: ("Uçsuz bucaksız karda kendi ayak izleri", "İlişkide kimsenin yürümediği o özgün kadersel yol; tamamen size ait, tamamen keşfedilmemiş bir gelecek."),
        26: ("Gökyüzünde dans eden renkli ışıklar", "İlişkinin artık dünyevi kelimelerin ötesine geçip, bir enerji ve ışık şölenine dönüşmesi."),
        27: ("Dünya sahnesinde kendine has bir yöntemle yürüyen adam", "İlişkinin bir 'ekol' olması; hiçbir kurala uymadan, kendi kadersel ritminizle dünyada var olma."),
        28: ("Bir nehirde kendi kendine kaynayan sular", "Derinlerdeki duygusal fokurdama; öfkenin veya tutkunun sessiz ama güçlü bir şekilde şifaya dönüşümü."),
        29: ("Güneşin batışında yanan ufuk çizgisi", "Bir devrin kapanışı! Artık ilişkinin bildiğiniz tüm formlarının, çok daha parlak bir şafak öncesi karanlığa gömülmesi."),
        30: ("Gökyüzünde el ele tutuşan, melek gibi iki insan", "Kadersel Mühür! İki ruhun, dünyevi rollerini bitirip, artık tamamen ilahi bir kontratla, zamansız ve mekan dışı bir aşkla ebediyen birleşmesi.")
    },
}

# ==============================================================================
# 🎓 EBEVEYN-ÇOCUK SİMYASI SÖZLÜKLERİ (Dış dosyalardan yüklenir)
# ==============================================================================
import importlib.util as _iu

def _load_ext_dict(filename):
    """Dış Python dosyasından tek bir dict değişkeni yükler."""
    _dir = os.path.dirname(os.path.abspath(__file__))
    _path = os.path.join(_dir, filename)
    if not os.path.exists(_path):
        return {}
    _spec = _iu.spec_from_file_location("_mod_" + filename, _path)
    _mod = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    for _k, _v in vars(_mod).items():
        if isinstance(_v, dict) and not _k.startswith("_"):
            return _v
    return {}

fbst_sabian_ebeveyn = _load_ext_dict("fbst_sabian_ebeveyn.py")
fbst_sabit_yildizlar_ebeveyn = _load_ext_dict("fbst_sabit_yildizlar_ebeveyn.py")
ASTEROID_SINASTRI_YORUMLARI_EBEVEYN = _load_ext_dict("ASTEROID_SINASTRI_YORUMLARI_EBEVEYN.py")
FBST_GEZEGEN_EV_COCUK = _load_ext_dict("FBST_GEZEGEN_EV_COCUK.py")
FBST_GEZEGEN_EV_EBEVEYN = _load_ext_dict("FBST_GEZEGEN_EV_EBEVEYN.py")
FBST_YORUMLAR_EBEVEYN = _load_ext_dict("FBST_YORUMLAR_EBEVEYN.py")
FBST_GELISIM_DONEMleri_EBEVEYN = _load_ext_dict("FBST_GELISIM_DONEMleri_EBEVEYN.py")
FBST_POTANSIYEL_EBEVEYN = _load_ext_dict("FBST_POTANSIYEL_EBEVEYN.py")
FBST_MESLEK_EBEVEYN = _load_ext_dict("FBST_MESLEK_EBEVEYN.py")
FBST_YORUMLAR_BURC = _load_ext_dict("FBST_YORUMLAR_BURC.py")
FBST_YORUMLAR_EV = _load_ext_dict("FBST_YORUMLAR_EV.py")
FBST_SINASTRI_OZEL = _load_ext_dict("FBST_SINASTRI_OZEL.py")

def _load_all_ext_dicts(filename):
    """Dış Python dosyasındaki TÜM dict değişkenlerini tek bir dict olarak yükler."""
    _dir = os.path.dirname(os.path.abspath(__file__))
    _path = os.path.join(_dir, filename)
    if not os.path.exists(_path):
        return {}
    _spec = _iu.spec_from_file_location("_mod_" + filename, _path)
    _mod = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    result = {}
    for _k, _v in vars(_mod).items():
        if isinstance(_v, dict) and not _k.startswith("_"):
            result[_k] = _v
    return result

ARAP_EBEVEYN = _load_all_ext_dicts("ARAP_EBEVEYN_DICTS.py")

# ==============================================================================
# 🌟 FBST SABİT YILDIZLAR İLİŞKİ VE KADER VERİTABANI
# Kapsam: Aşk, Evlilik, Cinsellik, Maddi Durumlar
# ==============================================================================

fbst_sabit_yildizlar = {
    "ACRAB": {
        "derece": 242.48,  # 2°29' Yay
        "yargi": "Kadersel mimarinizde 'Yıkılan Kule' etkisini taşıyan bu sarsıcı mühür, büyük maddi kazançlar ve derin ezoterik sırlar vaat ederken, ihtirasın getirebileceği krizlere karşı kesin bir uyarıdır. Elde edilen dünyevi statü ve servet, kibre dönüştüğü an kadersel bir sarsıntıyla yıkılabilir; ancak krizleri sabırla yöneten bir irade, bu enkazdan muazzam bir ruhsal ve maddi zenginlik inşa edecektir.",

        "etkiler": {
            "evlilik": {
                "Satürn": "Evlilik yoluyla elde edilen kazanç.",
                "Uranüs": "Evlilik yoluyla gelen kazanç, ancak içsel zorlukları ve yasal sorunları aşmak gerekir."
            },
            "maddi": {
                "Mars": "Para konularında olumlu ancak abartılı borçlanma riski.",
                "Merkür": "Maddi hediyeler ve sürpriz destekler.",
                "Ay": "Materyalist eğilimler, servet edinme ancak terfiler nedeniyle gelebilecek krizler."
            },
            "saglik": {
                "Genel": "Bulaşıcı hastalıklara yatkınlık veya bağışıklık testleri.",
                "Güneş": "Kötü sağlık, canlılıkta dönemsel düşüşler."
            },
            "kaza": {
                "Neptün": "Orta yaş döneminde kazalara açıklık.",
                "Uranüs": "Elektrik ve yangın risklerine karşı görünmez kadersel sorumluluk."
            },
            "zihinsel": {
                "Mars": "Son derece aktif, stratejik ve delici bir zihin.",
                "Merkür": "Donuk zihin veya iletişim/ifade kusurlarında kadersel zorlanma."
            },
            "gizlilikler": {
                "Genel": "Özellikle gizemli doğa araştırma yeteneği, derin sörf yapabilme kapasitesi."
            }
        }
    },
    
    "ALDEBARAN": {
        "derece": 69.08,  # 9°05' İkizler

        "yargi":"Zihinsel ve ahlaki dürüstlüğün kozmik mührüdür. İlişkinizde dürüstlükten ve ilkelerinizden taviz vermediğiniz sürece size eşsiz bir kadersel sağlamlık ve uyum bahşeder.",

        "etkiler": {
            "ask": {
                "Venüs": "Aşk hayatında sıra dışı anormallikler, sürprizli ve tutkulu durumlar."
            },
            "evlilik": {
                "Ay": "Son derece uyumlu, kadersel koruma kalkanına sahip evlilik.",
                "Neptün": "İçsel mutluluğun önünde görünmez engeller.",
                "Satürn": "Evlilik içinde kalıcı içsel başarı, sarsılmaz taahhüt."
            },
            "is_hayati": {
                "Ay": "İş ve ticaret konularına yüksek elverişlilik.",
                "Neptün": "Büyük şirket yöneticiliği, gizli finansal kaynaklar ve danışmanlıkta zirve.",
                "Uranüs": "İş hayatında ani ve beklenmedik değişimler, kadersel yeniden yapılanmalar."
            },
            "saglik": {
                "Genel": "Bedensel olarak enfeksiyonlara ve hastalıklara genel bir hassasiyet.",
                "Mars": "Ateşli hastalıklar ve ani iltihaplar."
            },
            "kaza": {
                "Mars": "Kesici aletler veya ateşle ilgili kaza riskleri."
            },
            "zihinsel": {
                "Genel": "Akıllı, keskin ve pratik bir bilinç.",
                "Satürn": "Geçmişi asla unutmayan, son derece güçlü bir bellek."
            }
        }
    },
    
    "ALCYONE": {
        "derece": 59.76,  # 29° Boğa
        "yargi":"Alcyone, kolektif bilincin ve ruhsal arayışın mührüdür. Eğer bu mühür aktifse, ilişkinizdeki bireysel egoların çatışması yerini, daha yüksek bir vizyona hizmet eden 'ortak bir hayale' bırakmalıdır. Yargısı şudur: Alcyone size, kişisel hırslarınızın ilişkinizi zayıflattığını, ancak bir bütünün parçası olarak hareket ettiğinizde durdurulamaz bir güç haline geleceğinizi hatırlatır. Bu mühür, 'biz' olabilmenin, bireysel ışığın kolektif bir güce dönüşmesinin mührüdür; bu süreçte yaşadığınız krizler, sizi birbirinize değil, ortak bir hakikate bağlamak içindir.",

        "etkiler": {

            "ask": {
                "Genel": "Karşı cins ile genel olarak olumsuz, yıpratıcı kadersel sınavlar."
            },
            "evlilik": {
                "Neptün": "Eşin sağlığı ile ilgili kadersel hassasiyetler ve endişeler.",
                "Uranüs": "Evlilik ortağının beklenmedik şekilde farklı bir boyut keşfetmesi."
            },
            "cinsellik": {
                "Yükselen": "Şiddetli şehvet ve bastırılması zor, tehlikeli cinsel eğilimler.",
                "Venüs": "Cinsel konularda yoğun tutku ve dönüştürücü enerjiler."
            },
            "is_hayati": {
                "Genel": "Denizaşırı bağlantılar veya büyük ticaret vasıtasıyla başarılar.",
                "Merkür": "Ticari yazışmalarda veya anlaşmalarda başarısızlık riski."
            },
            "saglik": {
                "Satürn": "Kronik rahatsızlıklar veya tümörel oluşumlara karşı risk.",
                "Güneş": "Katarakt, kafa ve boğaz bölgesi rahatsızlıkları."
            },
            "kaza": {
                "Mars": "Kafa bölgesinde kazalar.",
                "Neptün": "Sinsi ve ciddi kaza potansiyelleri."
            },
            "arkadaslar": {
                "Neptün": "Arkadaşlardan ve kolektiften gelen gizli/kadersel yardımlar."
            },
            "zihinsel": {
                "Uranüs": "Son derece aktif, isyankar ve elektrikli bir zihin yapısı."
            }
        }
    },
    
    "ALFARD": {
        "derece": 147.17,  # 27° Aslan
        "yargi":"Alfard, arzunun karanlık derinliklerini ve bu derinliklerde kaybolma riskini temsil eden bir mühürdür. Eğer bu mühür aktifse, ilişkinizdeki tutkular birer kurtarıcı değil, zaman zaman sizi kendinize yabancılaştıran birer 'duygusal bataklık' gibi hissettirebilir. Yargısı şudur: Alfard size, sevginin sadece 'sahip olmak' olmadığını, gerçek sevginin bağımlılıklardan arınmış bir özgürlük olduğunu öğretmek için gelir. İlişkinizdeki acılar birer ceza değil, ruhunuzun o tutkulu ama dar kalıbından çıkması için gereken birer 'duygusal temizlik' evresidir; bu süreci şuurla geçtiğinizde, sevginin en saf haline ulaşırsınız." ,

        "etkiler": {
            "ask": {
                "Jüpiter": "İlişkilerde geç kalmışlık, dulluk veya derin bir yalnızlık teması.",
                "Merkür": "Kişinin hayatının seyrini tamamen değiştirecek acılı ve tehlikeli tutkular.",
                "Venüs": "Yakın çevreyle uyumsuz olan, gizli ve sıra dışı ilişkilere çekilme."
            },
            "evlilik": {
                "Merkür": "İletişim kopukluğuna dayalı uyumsuz evlilik.",
                "Ay": "Eşin veya annenin sağlığıyla ilgili kadersel krizler ve sınavlar."
            },
            "cinsellik": {
                "Genel": "Cinsellikte aşırı duygusallık ve sınır deneme potansiyeli."
            },
            "saglik": {
                "Mars": "Kadersel kayıplar (Düşük, ani ve ölümcül sağlık krizleri)."
            },
            "kaza": {
                "Mars": "Çok ciddi ve geri dönülemez kaza ihtimalleri."
            },
            "gizlilikler": {
                "Satürn": "Kısa süreli, gizli ve sonunda keder getiren yasak aşklar."
            }
        }
    },

    "AGENA": {
        "derece": 233.80,  # 23° Akrep
        "yargi":"Agena, kadersel bir 'hizmet' sınavının mührüdür. Eğer bu mühür aktifse, ilişkinizdeki veya yaşamınızdaki başarılarınız sadece kişisel tatmin için değil, çevrenize yayacağınız şifa ve bilgelik için tasarlanmıştır. Yargısı şudur: Otoriteyi bir baskı aracı olarak değil, bir sorumluluk bilinciyle kullandığınızda, kadersel rotanızdaki engeller kendiliğinden açılacaktır. Kendinizi kolektif bir iyiliğin parçası olarak gördüğünüzde, Agena size fiziksel güçle ruhsal derinliği birleştiren sarsılmaz bir başarı vadeder." ,

        "etkiler": {
            "evlilik": {
                "Satürn": "Kıskançlık yüzünden iç uyumun tamamen bozulması riski.",
                "Uranüs": "İç uyumsuzluk ve ani kopuş titresimları."
            },
            "ask": {
                "Genel": "Tutkuların yönlendirdiği, kadersel derinliği olan etkileşimler."
            },
            "cinsellik": {
                "Genel": "Cinsellikte yoğun enerji ve deneyim arayışı.",
                "Venüs": "Duygusallığın cinsellikte sesle ve yoğun bir tutkuyla ifadesi."
            },
            "maddi": {
                "Merkür": "Maddi kazanç ve zihinsel projelerden gelen kadersel ödüller.",
                "Güneş": "Toplumsal başarı ve parlama."
            },
            "is_hayati": {
                "Neptün": "Yetersiz yöneticilik veya başarıda görünmez engellerle karşılaşma."
            },
            "saglik": {
                "Genel": "Zehirlenmelere karşı hassasiyet.",
                "Mars": "Büyük fiziksel güç ve dayanıklılık potansiyeli."
            },
            "kaza": {
                "Neptün": "Dikkatsizlik veya dalgınlık sonucu gelen kazalar."
            },
            "zihinsel": {
                "Jüpiter": "Aydın, vizyoner ve bilge bir zihin.",
                "Mars": "Büyük zihinsel güçler, stratejik düşünme."
            },
            "arkadaslar": {
                "Genel": "Geniş ve etkili bir çevre, arkadaşlardan gelen dönemsel faydalar."
            }
        }
    },
    "SPICA": {
        "derece": 204.00,  # 24°00' Terazi
        "yargi":"Zodyak'ın en şanslı dokunuşlarından biridir. Bu mühür, ilahi bilginin, zarafetin ve sanatsal yeteneğin size sınırsız bir kadersel bereket ve ruhsal bütünleşme getireceğini simgeler." ,

        "etkiler": {
            "maddi": {
                "Genel": "Zenginlik, başarı ve çok konforlu bir çevrede yaşama lütfu.",
                "Neptün": "Her zaman tatmin edici ve akışı kesilmeyen kazanç."
            },
            "evlilik": {
                "Neptün": "Uyumlu, ruh eşi hissi veren kadersel evlilik.",
                "Uranüs": "Evlilik yoluyla aniden elde edilen kazanç ve sınıf atlama."
            },
            "zihinsel": {
                "Merkür": "Müthiş zeki, yetenekli ve sanatsal olarak marifetli bir akıl."
            },
            "saglik": {
                "Satürn": "İyi, kalıcı ve sağlam bir fiziksel temel."
            }
        }
    },

    "VEGA": {
        "derece": 285.26,  # 15° Oğlak
        "yargi":"Vega, kadersel rotanızda 'sanatsal deha'nın ve ruhsal zarafetin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki her türlü zorluğun üstesinden sadece mantıkla değil, estetik bir zekayla ve ruhsal bir incelikle gelebilirsiniz. Yargısı şudur: Vega, size dünyevi olanın ötesine geçme yeteneği sunar. Maddi kazanımlarınızın kalıcı olması, ilişkinizdeki sanatın ve estetiğin korunmasına bağlıdır. Bu mühür, 'saf ışığın' temsilcisidir; bu nedenle ruhunuzdaki ışığı karartacak her türlü hesaplı ve kirli oyun, ilişkinizdeki kadersel korumayı anında geri çeker." ,

        "etkiler": {
            "evlilik": {
                "Neptün": "Evliliğin veya evin ikiye bölünmesi tehlikesi.",
                "Satürn": "Gecikmiş içsel sorunlar ve soğukluk.",
                "Uranüs": "Beklenmedik içsel kederler ve kopuşlar."
            },
            "maddi": {
                "Jüpiter": "Maddi kazanca elverişlilik, ancak kibrin getirebileceği servet kaybı.",
                "Ay": "Rant, gayrimenkul veya emeklilik yoluyla düzenli kazanç.",
                "Uranüs": "Çok hızlı para kazanıp aynı hızda kaybetme (Materyalist aşırılık)."
            },
            "cinsellik": {
                "Genel": "Genellikle gizli ve yoğun şehvetlilik."
            }
        }
    },

"ANTARES": {
        "derece": 249.76,  # 9°46' Yay
        "yargi":"İlişkinizde ve hayatınızda büyük güç savaşlarını, stratejik dönemeçleri temsil eder. Yıkıcı rekabeti bırakıp gücünüzü inşaya yönlendirirseniz, kadersel bir zafer kazanırsınız." ,

        "etkiler": {
            "maddi": {
                "Genel": "Stratejik davranıldığında büyük servet, komutanlık ve ticari onur.",
                "Uranüs": "Beklenmedik finansal krizler ve spekülasyon zararları."
            },
            "ask": {
                "Ay": "İlişki dinamiğinde nüfuzlu, güçlü ve kadersel arkadaşların desteği."
            },
            "evlilik": {
                "Genel": "İlişkide kibir ve güç savaşları dengelenmezse, en yüksekten ani düşüş ve yıkım riski."
            },
            "is_hayati": {
                "Ay": "İş konularında elverişlilik ve dayanıklılık."
            },
            "arkadaslar": {
                "Ay": "Çok güçlü ve etkin çevrenin koruyucu kalkanı."
            }
        }
    },

    "REGULUS": {
        "derece": 149.83,  # 29°50' Aslan
        "yargi":"Kadersel mimaride kraliyet tacını temsil eder. Bu mühür size büyük bir itibar ve koruma vadeder; ancak intikamdan ve kibirden uzak durduğunuz sürece bu tahtta kalabilirsiniz." ,

        "etkiler": {
            "maddi": {
                "Genel": "KRALİYET YILDIZI; muazzam bir servet, yüksek itibar ve görünürlük.",
                "Satürn": "Sorumluluk bilinciyle korunduğu takdirde kalıcı, köklü zenginlik."
            },
            "ask": {
                "Venüs": "Şiddet içeren, yoğun tutkulu bağlılıklar veya krizli, büyük aşk maceraları."
            },
            "evlilik": {
                "Genel": "Güçlü, nüfuzlu çevrelerin ve kadersel dostların koruması altında, adeta 'kraliyet' tarzı bir birliktelik."
            },
            "arkadaslar": {
                "Güneş": "Arkadaşlar üzerinde büyük bir etki, liderlik ve komutanlık gücü.",
                "Uranüs": "İleri zamanda aniden düşman olan, rekabete giren eski arkadaşlar."
            }
        }
    },

    "SIRIUS": {
        "derece": 104.08,  # 14°05' Yengeç
        "yargi":"Evrensel şansın ve ilahi lütufların mührüdür. Bu hizalanma, attığınız adımların ardında büyük bir kadersel koruma ve bereket olduğunu, ruhsal bir sıçrama yaşayacağınızı müjdeler." ,

        "etkiler": {
            "maddi": {
                "Genel": "Kolektiften gelen devasa zenginlik, itibar ve kadersel lütuflar.",
                "Jüpiter": "Finansal genişleme, her zaman talihli ve bereketli bir akar hattı."
            },
            "cinsellik": {
                "Genel": "Çok güçlü bir cinsel şevk, bitmek bilmeyen yüksek yaşam enerjisi ve manyetik karizma."
            },
            "evlilik": {
                "Genel": "Toplumsal mevkisi yüksek, saygın ve koruyucu ortaklıklar kurma meyli."
            },
            "saglik": {
                "Ay": "Çok dayanıklı ve iyi bir sağlık genetiği."
            },
            "is_hayati": {
                "Neptün": "Kurumlarda, bankalarda ve büyük organizasyonlarda müthiş iş takibi ve başarı."
            }
        }
    },

    "ALGOL": {
        "derece": 56.17,  # 26°10' Boğa
        "yargi":"Kadersel navigasyonda en keskin virajlardan biridir. Kendi karanlığınızla veya dış dünyanın yıkıcı tutkularıyla yüzleştiğiniz bu evrede, öfkeyi bilgeliğe dönüştürmek en büyük sınavınızdır." ,

        "etkiler": {
            "ask": {
                "Genel": "Tutkuların kontrolden çıkmasıyla gelen ağır kadersel hayal kırıklıkları.",
                "Mars": "Karşı cinsle olan ilişkilerde yıkıcı krizler ve ani yol ayrımları."
            },
            "evlilik": {
                "Genel": "İlişki içinde ego krizlerinin, öfkenin ve inatçılığın evliliğin dengesini sarsma riski."
            },
            "maddi": {
                "Genel": "Büyük kazançlar elde etme hırsı ve gücü; ancak etik kurallar aşılırsa ani finansal kayıplar riski."
            }
        }
    },

    "SCHEAT": {
        "derece": 359.36,  # 29° Balık (yaklaşık)
        "yargi": "Scheat, kadersel rotanızda 'beklenmedik olanın' mührüdür. Eğer bu mühür aktifse, hayatınızda veya ilişkinizde kontrolünüz dışında gelişen ani olaylar, sizi konfor alanınızdan çıkarmak için tasarlanmış birer 'uyanış sarsıntısı'dır. Yargısı şudur: Scheat, sizi belirsizliğe hazırlar. Planlarınızın altüst olması bir başarısızlık değil, kadersel bir revizyondur. Bu türbülanslarda dik durmayı ve esnemeyi başardığınızda, normal bir rotada asla ulaşamayacağınız o derin bilgelik zirvesine ulaşacaksınız.",
        "etkiler": {
            "ask": {
                "Jüpiter": "Kadersel kayıplar ve hayal kırıklıklarıyla gelen ruhsal arınma.",
                "Ay": "Duygusal eleştiri krizleri ve partnerin beklentileriyle yüzleşme."
            },
            "evlilik": {
                "Genel": "Geçmişten gelen travmaların evliliğe yansıması, kadersel sınavlar."
            },
            "kaza": {
                "Mars": "Beklenmedik kazalar, dikkatsizlik kaynaklı olaylar.",
                "Merkür": "Özellikle su ve seyahatle ilgili, başta olmak üzere kadersel aksilikler."
            },
            "zihinsel": {
                "Uranüs": "Konsantrasyon düşüklüğü ancak anlık, parlak sezgiler."
            }
        }
    },

    "DENEB_ALGEDI": {
        "derece": 323.53,  # 23° Kova (yaklaşık)
        "yargi": "Deneb Algedi, gökyüzünün kadersel terazisinin kefesidir. Eğer bu mühür aktifse, ilişkinizdeki her eylem, söz ve niyet, evrensel bir kayıt sistemine işleniyor demektir. Yargısı şudur: Bu mühür size ne ceza ne de ödül verir; sadece 'adalet' getirir. İlişkinizde dürüstlük ve sadakat temelini inşa ettiyseniz, bu mühür size sarsılmaz bir yuva ve uzun ömürlü bir huzur bahşeder. Ancak sömürü, yalan veya haksızlık üzerine bir yapı kurduysanız, bu kadersel durak, ilişkinizdeki o yapının doğal bir sonuçla (hasatla) çözülmesini sağlar. Burada sınav, sorumluluk almanın onurudur.",
        "etkiler": {
            "ask": {
                "Jüpiter": "Beklentilerin gerçekle çarpışması, yüzeysel duygulardan arınma sınavı.",
                "Genel": "İlişkide ahlaki sorumluluk ve kadersel ciddiyet arayışı."
            },
            "evlilik": {
                "Genel": "Sadakat temelli köklü bir yuva inşası, karşılıklı sözleşmelere dayalı güven."
            },
            "maddi": {
                "Genel": "Hak edilenin (ne eksik ne fazla) alınacağı kadersel bir finansal döngü."
            }
        }
    },

    "UNUKALHAI": {
        "derece": 232.07,  # 22° Akrep (yaklaşık)
        "yargi": "Unukalhai, yılanın deri değiştirmesi gibi, kadersel bir arınmanın ve gölgelerle yüzleşmenin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki mevcut krizler veya zorlanmalar, eski ve artık işlevini yitirmiş kalıplarınızdan kurtulmanız için birer 'kabuk değiştirme' davetidir. Yargısı şudur: Gölgenizden kaçtığınız sürece krizler sizi kovalar; ancak gölgenizi (ilişkinizdeki bastırılmış korkuları) kabul edip şifalandırdığınızda, aradığınız o derin güç ve kozmik bütünleşmeye ulaşırsınız. Buradaki sınav, 'görünür olan' ile 'gölgede kalan' arasındaki dengedir.",
        "etkiler": {
            "evlilik": {
                "Uranüs": "Yıpratıcı ve ani değişimler getiren evlilikler.", 
                "Venüs": "İlişkide mülkiyetçilik, kıskançlık ve yoğun manipülasyon krizleri."
            },
            "ask": {
                "Neptün": "Kadersel karmaşalar, bulanık sınırlarla gelen ruhsal sınavlar.",
                "Genel": "İlişkide derin bir tutku arayışı, ancak bu tutkunun karanlık tarafıyla (tutku-takıntı dengesi) yüzleşme."
            },
            "cinsellik": {
                "Genel": "Sınırları zorlama, alışılmışın dışında, dönüşümsel cinsel enerjiler."
            },
            "maddi": {
                "Uranüs": "Lüks ortamlara çekilme ve bu ortamların getirdiği kadersel sorumluluklar."
            }
        }
    },


    "PROCYON": {
        "derece": 115.82,  # 25°49' Yengeç
        "yargi": "İlişkinizde bastırılamaz tutku ve iletişim krizleri arasında gidip gelen bir enerji hattı oluşuyor. Bu kadersel mühür, fevri kararlar yerine zihinsel bir diplomasi geliştirmeniz gerektiğinin kesin bir uyarısıdır." ,

        "etkiler": {
            "ask": {
                "Merkür": "Karşı cinsle zihinsel boyutta ve fikirsel anlamda yaşanan kadersel uyum sorunları."
            },
            "cinsellik": {
                "Yükselen": "Yoğun çekim gücü ve karşı tarafı derinden etkileyen manyetik bir enerji."
            },
            "saglik": {
                "Genel": "Sıvılardan, zehirlerden veya ani gelişen enfeksiyonlardan gelebilecek kadersel hassasiyetler."
            },
            "kaza": {
                "Genel": "Ani ve beklenmedik tehlikelere karşı fevri hareket etmekten doğan riskler."
            }
        }
    },

    "SABIK": {
        "derece": 257.97,  # 17°58' Yay
        "yargi":"Kadersel rotanızda aşk, gizli rekabetler ve geç gelen başarılarla sınanacağınız bir kavşaktasınız. Bu mühür, kalıcı zaferlerin ancak sabır ve ahlaki disiplinle kazanılabileceğini gösterir." ,

        "etkiler": {
            "ask": {
                "Mars": "Karşı cinsle olan ilişkilerde bitmek bilmeyen rekabet, sorunlar ve geçimsizlik.",
                "Neptün": "Karşı cinsle kadersel olarak çok olumlu, derin ve favori ilişkiler içine çekilme.",
                "Satürn": "Aşk hayatında kalıcı sorumluluklar, soğukluk, sorun ve hayal kırıklığı."
            },
            "cinsellik": {
                "Genel": "Tutkulu ve yoğun cinsel enerjiler, farklı deneyimlere açıklık."
            },
            "maddi": {
                "Jüpiter": "Yüksek ve kalıcı maddi başarı.",
                "Ay": "Mesleki olarak başarılı olmak ancak bunun zenginliğe dönüşmemesi.",
                "Neptün": "Maddi konularda sezgisel ve kadersel başarı.",
                "Satürn": "Başarı, itibar ve onurun ancak orta yaştan sonraki dönemlerde gelmesi."
            },
            "is_hayati": {
                "Merkür": "İş hayatında iletişim veya ticari hatalardan kaynaklanan zorlanmalar."
            },
            "arkadaslar": {
                "Merkür": "Arkadaşlardan gelecek küçük ama kritik yardımlar.",
                "Neptün": "Kolektif ve ruhsal idealleri paylaşan arkadaş çevreleri.",
                "Uranüs": "Arkadaş ve akrabalarla aniden gelişen, beklenmedik ayrılıklar."
            },
            "gizlilikler": {
                "Ay": "Bilinçaltında yatan veya çevreden gelen gizli rekabet enerjisi.",
                "Satürn": "Gizli yardımlar ve bunun yarattığı kadersel sorumluluklar."
            }
        }
    },

    "SADALSUUD": {
        "derece": 323.40,  # 23°24' Kova
        "yargi":"İlişkinizdeki enerji, klasik ilişki formüllerine sığmayacak kadar geniştir. Satürn'ün disiplini ile Uranüs'ün özgürlüğünü dengelediğiniz an, kadersel talih kapılarınız sonuna kadar açılacaktır." ,

        "etkiler": {
            "ask": {
                "Satürn": "Karşı cins üzerinde adeta hipnotik, büyüleyici ve otoriter bir etki kurabilme gücü.",
                "Uranüs": "Karşı cinsle ilişkilerde beklenmedik istikrarsızlık ve aniden kopan bağlar.",
                "Genel": "İlişkide sıra dışı, teknolojik veya entelektüel derinliği olan bir çekim alanı."
            },
            "cinsellik": {
                "Satürn": "Dürtüsel konularda aşırıya kaçma eğilimi ve gizli tutkular.",
                "Genel": "Fiziksel zevkten ziyade zihinsel ve ruhsal bir bütünleşmeyi arzulayan bir yapı."
            },
            "maddi": {
                "Jüpiter": "Çok güçlü kadersel maddi talih, spekülatif kazançlar ve şans odaklı zenginlik.",
                "Genel": "Kolektiften ve toplumsal projelerden gelen finansal bereket."
            },
            "evlilik": {
                "Uranüs": "Evlilikte özgürlükçü, geleneksel olmayan ve sıra dışı bir bağ kurma isteği.",
                "Genel": "Kadersel şansın yüksek olduğu, ancak bireysel alanın korunması gereken bir birliktelik."
            },
            "zihinsel": {
                "Genel": "Zamanının ötesinde, vizyoner, uzak görüşlü ve orijinal bir zeka yapısı."
            },
            "arkadaslar": {
                "Ay": "Sıradan olmayan, entelektüel açıdan besleyici ve saygılı arkadaşlıklar."
            }
        }
    },

"ARCTURUS": {
        "derece": 204.0,  # 24° Terazi (Konum verilerine göre hassas ayar gerektirebilir)
        "yargi":"İlişkinizdeki sırlar, dış dünyanın gürültüsünden uzakta ve 'sessiz bir koruma' altındadır. Bu mühür, dışarıdan gelen müdahalelere karşı ilişkinize doğal bir kalkan ve mahremiyet zırhı kazandırır." ,

        "etkiler": {
            "gizlilikler": {
                "Yükselen": "Sadık arkadaşlar ve kişisel yaşamdaki gizliliklerin sessizce korunması, özel hayatın mahremiyeti.",
                "Genel": "Sırları saklama konusunda mükemmel bir disiplin ve kadersel koruma."
            },
            "maddi": {
                "Genel": "Çalışarak elde edilen zenginlik, başarı ve toplum içinde saygınlık.",
                "Jüpiter": "Finansal konularda sürpriz fırsatlar ve şanslı girişimler."
            },
            "is_hayati": {
                "Genel": "Liderlik kapasitesi, iş hayatında güvenilir bir otorite figürü olma."
            },
            "ask": {
                "Genel": "Kişinin sadakati ile sınandığı, ancak sağlam temelli kadersel birliktelikler."
            }
        }
    },

"MERGA": {
        "derece": 204.0,  # 24° Terazi (Yaklaşık)
        "yargi": "Merga, dağınık enerjilerin tek bir kadersel hedefe odaklanması gerektiğinin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki veya yaşamınızdaki dağınıklık bir 'yol kaybı' değil, bir 'hasat hazırlığı'dır. Yargısı şudur: Enerjinizi sağa sola saçmayı bıraktığınızda, kadersel hasadınızın ne kadar bereketli olduğunu fark edeceksiniz. Merga, size zayıf taraflarınızı birleştirip bir 'kadersel değnek' gibi kullanarak, kendi kaderinizin efendisi olabileceğinizi fısıldar; bu, sorumluluk almanın en saf ve en ödüllendirici biçimidir.",
        "etkiler": {
            "maddi": {
                "Genel": "Odaklanmış çaba ile gelen hasat; uzun vadeli, sabırlı emeklerin meyve vermesi.",
                "Satürn": "Zamanın olgunlaştırdığı maddi kazanımlar."
            },
            "zihinsel": {
                "Genel": "Bilinçli odaklanma, dikkat dağınıklığının giderilmesi, hedefe kilitlenme yetisi.",
                "Merkür": "Düşünceleri eyleme dönüştürme konusunda yüksek stratejik yetenek."
            },
            "evlilik": {
                "Genel": "İlişkide ortak hedeflere yönelme, dağılmış bir bağı disiplinle yeniden inşa etme gücü."
            }
        }
    },

"FOMALHAUT": {
        "derece": 353.0,  # 3° 23' Balık
        "yargi":"Kadersel rotanızdaki yüksek idealleri temsil eder. Hayatınıza giren sırlar sizin sınavınızdır. Gizli düşmanlıklara karşı stratejik bir zırh kuşanmanız ve hayalperestlikten uzak durmanız gereken bir dönemdesiniz." ,

        "etkiler": {
            "gizlilikler": {
                "Jüpiter": "Gizli topluluklar veya ezoterik çevrelerle kadersel bağlar.",
                "Mars": "Arka planda yürütülen kadersel çatışmalar ve gizli gündemler.",
                "Merkür": "Sırlar içeren yazışmalar veya gizli bilgilerin açığa çıkması.",
                "Ay": "Büyük zorluklara ve karmaşık sorunlara yol açan gizli süreçler; ancak sabırla ulaşılan nihai kazançlar.",
                "Neptün": "Gizli operationalar veya görünmeyen güçlerle ilişkili kadersel süreçler.",
                "Venüs": "Gizli ve toplumdan saklanan aşk ilişkileri."
            },
            "maddi": {
                "Genel": "Uzun vadeli çabalarla elde edilen, çok zorlukla kazanılan ancak kalıcı olan kadersel servet.",
                "Uranüs": "İş hayatında ani ve sıra dışı değişimler, beklenmedik finansal kırılmalar."
            },
            "ask": {
                "Genel": "İlişkide idealist beklentiler ve gerçeklikten kopuş riski.",
                "Venüs": "Aşk hayatında kadersel sırlar ve ulaşılmaz olanın peşinde koşma."
            },
            "is_hayati": {
                "Genel": "Yaratıcı zeka gerektiren işlerde başarı, ancak gizli engellere karşı tetikte olma zorunluluğu."
            }
        }
    },
"RIGEL": {
        "derece": 76.5,  # 16°30' İkizler
        "yargi":"Bu mühür, zekanızın ve potansiyelinizin hızını artırır ancak duygusal rotanızda sarsıcı etkiler yaratabilir. Zekanızı dengeleyecek sabrı inşa etmezseniz, ani yükselişler aynı hızla sarsıntıya dönüşebilir." ,
        
        "etkiler": {
            "ask": {
                "Uranüs": "Aşk hayatında beklenmedik, şok edici ve erken yaşta gelen hayal kırıklıkları.",
                "Venüs": "Tutkulu ama sınırları zorlayan, gelenek dışı romantik deneyimler."
            },
            "zihinsel": {
                "Mars": "Dahi seviyesinde bir zeka, ancak bu zekanın getirdiği aşırı huzursuzluk ve sabırsızlık.",
                "Neptün": "Bilimsel keşiflere açık, aktif ve ilham dolu bir zihin yapısı."
            },
            "maddi": {
                "Genel": "Zeka ve yetenekle gelen hızlı yükseliş, ancak bu statüyü koruma sınavı.",
                "Jüpiter": "Sürpriz finansal kapıların açılması ve sosyal statü artışı."
            },
            "is_hayati": {
                "Genel": "İş hayatında üstün başarı, buluş yeteneği ve çevreyi yönetme becerisi."
            },
            "saglik": {
                "Genel": "Yüksek sinirsel enerji, zaman zaman gelen zihinsel tükenmişlik."
            }
        }
    },

"ZUBEN_EL_SCHEMALI": {
        "derece": 219.0,  # 19° Akrep
        "yargi":"Sistemin kadersel terazisinde dengeyi temsil eder. Eğer bu mühür aktifse, ilişkinizdeki stratejik hamleleriniz size 'akılcı bir yükseliş' olarak geri dönecektir." ,
        "etkiler": {
            "maddi": {
                "Genel": "Büyük zenginlik, onur ve entelektüel başarı. Başkalarından gelen kazançlar.",
                "Satürn": "Maddi konularda yavaş ama kalıcı ve sağlam bir yükseliş."
            },
            "ask": {
                "Genel": "İlişkilerde nezaket, diplomatik beceri ve uyum arayışı.",
                "Venüs": "Aşk hayatında entelektüel ve uyumlu bir atmosfer."
            },
            "evlilik": {
                "Genel": "Kadersel olarak dengeli, sosyal statüsü yüksek bir birliktelik."
            },
            "zihinsel": {
                "Merkür": "Bilimsel, felsefi ve yüksek düzeyde zihinsel yetenekler."
            }
        }
    },

    "ZUBEN_EL_GENUBI": {
        "derece": 215.0,  # 15° Akrep
        "yargi":"Terazinin bu kefesi, geçmiş karmik borçların ödendiği yerdir. İlişkinizdeki krizler bir 'ceza' değil, terazinin dengelenmesi için gereken bir kadersel hesaplaşmadır." ,

        
        "etkiler": {
            "maddi": {
                "Genel": "Zenginlik ancak bu zenginliğin getirdiği toplumsal bedeller ve kadersel riskler.",
                "Mars": "Dürtüsel harcamalar sonucu gelen kayıplar."
            },
            "ask": {
                "Genel": "Karşı cinsle ilişkilerde dikkatli olunması gereken, bazen manipülatif etkiler.",
                "Venüs": "Aşkta kadersel zorluklar ve yanlış anlaşılmalar."
            },
            "kaza": {
                "Genel": "İhmalkarlık ve dikkatsizlik sonucu oluşan fiziksel aksilikler."
            },
            "evlilik": {
                "Satürn": "Evlilikte zorlu imtihanlar, kadersel bir 'terazi' sınanması.",
                "Genel": "Evlilik ortaklığında güç ve denge unsurlarının çatışması."
            }
        }
    },
"THUBAN": {
        "derece": 167.0,  # Yaklaşık 17° Başak (FBST hassasiyetine göre ayarlanabilir)
        "yargi": "Zihniniz şu an kadim bir arşiv gibi çalışıyor. Çözemediğiniz krizlerin kökleri bugünde değil, geçmişin dosyalarında saklı. Stratejik dehanızı kullanarak bu karmik veriyi büyük bir kazanca dönüştürme vaktidir.",
        
        "etkiler": {
            "zihinsel": {
                "Genel": "Son derece delici, analizci ve gizli kalmış bilgileri ortaya çıkaran bir zihin yapısı.",
                "Satürn": "Zihinsel disiplin, tarihsel ve kadim konulara eğilim."
            },
            "is_hayati": {
                "Genel": "Borsa ve spekülatif piyasalarda kadersel başarı, gizli yatırımlarda öngörü.",
                "Uranüs": "Finansal piyasalarda ani stratejik hamleler."
            },
            "saglik": {
                "Genel": "Zehirlenme tehlikeleri ve kimyasal hassasiyetlere karşı kadersel uyarı."
            },
            "arkadaslar": {
                "Genel": "Bilgi paylaşımına dayalı, entelektüel derinliği olan arkadaşlıklar."
            },
            "gizlilikler": {
                "Genel": "Kökleri geçmişe dayanan sırlar, ailevi veya kadim bir mirasın korunması."
            }
        }
    },
"ALTAIR": {
        "derece": 300.9,  # 0° 54' Kova (FBST hassasiyetine göre ayarlanabilir)
        "yargi":"Yükselişiniz, bir kartalın kanat çırpışı kadar hızlı ve sarsıcı olacak. Ancak bu hız kıskançlık enerjilerini de çeker. Hızlı yükselmenin bedeli, rotada sabit kalabilme iradesidir." ,

        "etkiler": {
            "maddi": {
                "Genel": "Büyük, ani ancak kısa ömürlü zenginlik ve onur; şanslı girişimler.",
                "Mars": "Sosyal toplum ve iş ortaklıklarından gelen kadersel sınavlar sonrası büyük kazançlar."
            },
            "is_hayati": {
                "Merkür": "Ortaklıklar için kadersel olarak zorlu, dikkat gerektiren bir konum.",
                "Ay": "Şirket ve kamu işlerinde dönemsel sorunlar ve krizler."
            },
            "kaza": {
                "Satürn": "Çalışma hayatında veya genel yaşamda ömür boyu sürebilecek kaza tehlikesi veya yetersizlik hissi.",
                "Genel": "Ani ve büyük değişimlerin getirdiği kadersel sarsıntılar."
            },
            "arkadaslar": {
                "Güneş": "Çok sayıda arkadaş, ancak bunların bir kısmının kıskançlık ve yazışmalar yoluyla yarattığı problemler.",
                "Uranüs": "İkizler doğasında, entelektüel, edebiyatçı veya zeki arkadaş grupları."
            },
            "zihinsel": {
                "Genel": "Keskin, hızlı ve yönetici bir zeka; hızlı kavrayış."
            }
        }
    },

"MIRFAK": {
        "derece": 61.0,  # 1° İkizler
        "yargi": "Mirfak, kadersel bir yükselişin ve stratejik otoritenin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki veya yaşamınızdaki zorluklar, karakterinizi çelikleştirmek için tasarlanmış birer 'kadersel antrenman'dır. Yargısı şudur: Otoritenizi ve onurunuzu korumak için attığınız her akılcı adım, kadersel rotanızda sizi bir lider konumuna taşır. Ancak bu mühür, sadece kişisel hırsla değil, kolektife hizmet eden bir vizyonla yönetildiğinde gerçek gücünü ortaya çıkarır; aksi takdirde elde edilen statü, beraberinde yalnızlığı getirebilir.",
        "etkiler": {
            "maddi": {
                "Genel": "Liderlik becerisiyle gelen onur, prestij ve yüksek statü.",
                "Satürn": "Zamanla gelen kalıcı otorite."
            },
            "saglik": {
                "Genel": "Yüksek fiziksel dayanıklılık, ancak aşırı çalışmaya bağlı sinirsel yorgunluk."
            },
            "is_hayati": {
                "Genel": "Yönetici pozisyonları, kitleleri yönlendirme yetisi ve stratejik planlama başarısı."
            }
        }
    },
    
   "MARFIK": {
        "derece": 255.0,  # 15° Yay (yaklaşık)
        "yargi": "Marfik, gökyüzünün şifacı elini temsil eden, zehri panzehire dönüştürme kapasitesinin mührüdür. Eğer bu mühür aktifse, ilişkinizdeki çatışmalar ve zorlu süreçler aslında ruhsal tekamülünüz için gereken birer 'arınma töreni'dir. Yargısı şudur: Kendi hakikatinizi dışarıda değil, ilişkinizin derinliklerinde saklı olan 'gölge'lerde bulacaksınız. Zehri şifaya dönüştürmek, ancak kendi içsel karanlığınızla yüzleşip onu sevgiyle kucakladığınızda mümkündür; aksi takdirde krizler kısır bir döngü olarak tekrarlanacaktır.",
        "etkiler": {
            "zihinsel": {
                "Genel": "Kendi doğrularını savunma, felsefi ve ruhsal arayışlarda keskin bir zihin.",
                "Satürn": "Kadim bilgilere duyulan ilgi, ciddi ve disiplinli ruhsal araştırmalar."
            },
            "maddi": {
                "Genel": "Ruhsal veya ilahi olanın peşinden giderek elde edilen dünyevi bilgi ve manevi kazanç."
            },
            "evlilik": {
                "Genel": "Partnerle paylaşılan ortak inanç sistemleri, ruhsal hedefler ve kadersel bir yol arkadaşlığı."
            }
        }
    },
    
    "ANKA": { # Ankaa / Alpha Phoenicis
        "derece": 15.0,  # 15° Balık
        "yargi":"Bu mühür bir krizin veya yıkımın son olmadığını fısıldar. Yaşananlar ilişkinizin bitişi değil, geçmişin küllerinden çok daha güçlü ve asil bir şekilde yeniden doğuşunun habercisidir." ,

        "etkiler": {
            "maddi": {"Genel": "Küllerinden yeniden doğma gücü; büyük krizlerden finansal yükselişle çıkma."},
            "ask": {"Genel": "Derin bir duygusal dönüşüm ve bağ kurma arzusu."},
            "evlilik": {"Genel": "İlişkide yaşanan büyük değişim ve yenilenme süreçleri."}
        }
    },
    
    "ACRUX": {
        "derece": 221.0,  # 11° Akrep
        "yargi":"İlişkiniz kadersel bir ihtişam evresine giriyor. Bu mühür aktifken yaşananlar sadece dünyevi bir başarı değil, büyük bir prestij ve ruhsal otorite transferidir." ,

        "etkiler": {
            "maddi": {"Genel": "İhtişam, lüks, gösteriş ve sosyal prestij."},
            "is_hayati": {"Genel": "Yüksek onur, büyük başarı, kadersel bir yükseliş süreci."},
            "gizlilikler": {"Genel": "Ezoterik güçler ve saklı kalmış derin bilgilerin kullanımı."}
        }
    },

"RANA": {
        "derece": 58.0,  # 28° Boğa
        "yargi": "Rana, kadersel bir akışta belirsizliğin ve dalgalanmanın mührüdür. Bu yıldız aktifleştiğinde, hayatınızdaki en güvenli limanların bile sarsılabileceğini unutmamalısınız. Yargısı şudur: Kontrol etmeye çalıştığınız her şeyin akışa bırakılması gerektiğini öğretir; aksi takdirde 'boğulma' hissi veren duygusal veya fiziksel türbülanslarla yüzleşmek zorunda kalırsınız. Bu krizler, aslında sizi sahte güvenli alanlarınızdan çıkarıp gerçek kadersel rotanıza yönlendiren birer 'akıntı'dır.",
        "etkiler": {
            "kaza": {
                "Genel": "Sıvılarla, denizle veya seyahatlerde yaşanabilecek kadersel aksilikler/kazalar."
            },
            "saglik": {
                "Genel": "Solunum yolları hassasiyeti, sıvı dengesizliği veya ödem eğilimi."
            },
            "zihinsel": {
                "Genel": "Sezgisel derinlik ancak bu derinlikte kaybolma riski."
            }
        }
    },
    

    "CAPULUS": {
        "derece": 63.0,  # 3° İkizler
        "yargi": "Şu an haritanızda 'Dönüşüm Tutkusu' mühürleri aktif. Bu dönem, duygusal enerjilerinizin bir yıkım mı yoksa simyasal bir dönüşüm mü yaratacağını belirleyeceğiniz çok kritik bir kadersel kavşaktır." ,
        "etkiler": {
            "ask": {
                "Genel": "İlişkilerde yoğun duygusal dalgalanmalar ve tutku krizleri.",
                "Mars": "İlişkide yoğun tartışmalar ve kadersel olarak zorlu süreçler."
            },
            "maddi": {
                "Genel": "Riskli yatırımlardan gelen ani dalgalanmalar, dikkatli olunması gereken dönem."
            }
        }
    },

    "CASTOR": {
        "derece": 110.0,  # 20° Yengeç
        "yargi":"Castor, zihinsel dehanın ve edebi başarının ışığını taşırken, aynı zamanda bu parlaklığın getirdiği kadersel ağırlığı temsil eder. Bu mühür aktifse, ilişkiniz ani ve göz kamaştırıcı başarıların eşiğindedir; ancak elde edilen her zafer, beraberinde sürdürülebilirlik sınavını getirir. Zekayı manipülasyon için değil, ortak hakikati inşa etmek için kullanmadığınız takdirde, zirveden gelen hızlı düşüşler kaçınılmaz bir kadersel döngü haline gelir." ,

        "etkiler": {
            "maddi": {
                "Genel": "Ani ve büyük başarılar, ancak sonrasında gelen hızlı düşüş veya kayıplar.",
                "Jüpiter": "Finansal konularda şanslılık, ancak sürdürülebilirlik sınavı."
            },
            "zihinsel": {
                "Genel": "Zekayı yönetme gücü, edebi başarılar, ancak sinirsel aşırılıklar."
            },
            "kaza": {
                "Genel": "Göz rahatsızlıkları ve kaza potansiyeli."
            }
        }
    },

    "POLLUX": {
        "derece": 113.0,  # 23° Yengeç
        "yargi":"Şu an haritanızda 'Yıkıcı Tutku' mühürleri aktif. Bu dönem, duygusal tepkilerinizin bir yıkım mı yoksa simyasal bir dönüşüm mü yaratacağını belirleyeceğiniz çok kritik bir kadersel kavşaktır." ,

        "etkiler": {
            "cinsellik": {
                "Güneş": "Yoğun ve dönüştürücü cinsel enerjiler, tutkunun sınandığı derin deneyimler.",
                "Venüs": "Aşırı çekim gücü ve duygusal derinlikle şekillenen, sıra dışı cinsel deneyimler."
            },
            "ask": {
                "Genel": "Yıkıcı duygular, kadersel krizler ve ilişkideki manipülasyonlar."
            },
            "maddi": {
                "Genel": "Mücadeleyle gelen kazançlar, ancak güvenilmez çevre yüzünden riskler."
            }
        }
    },
}

# ============================================================
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
# ==============================================================================
# ⚙️ FBST MOTORU: GÖKSEL TAKİP VE EPHEMERIS HESAPLAMALARI
# ==============================================================================
@st.cache_data
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

# ==============================================================================
# 🌀 SABİT YILDIZ PRECESSION (EŞMERKEZLİ KAYMA) DÖNÜŞÜM SİSTEMİ
# ==============================================================================

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
    return f"{burclar[sign_index]} {tam_derece}°{dakika:02d}'"


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


def bağıl_harita_yildiz_donusumu(veritabani_derece, kaynak_yil, kaynak_ay=1, kaynak_gun=1, orb_siniri=2.0):
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
# 🎯 FBST KADERSEL YILDIZ TARAMA VE EŞLEŞTİRME ALGORİTMASI
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

def kadersel_yildiz_taramasi(gezegen_adi, gezegen_derecesi, orb_siniri=2.0):
    bulunan_muhurler = []
    _aktif_mod = st.session_state.get("sim_modu", "es_sevgili")

    if _aktif_mod == "ebeveyn_cocuk" and fbst_sabit_yildizlar_ebeveyn:
        _aktif_sozluk = fbst_sabit_yildizlar_ebeveyn
    else:
        _aktif_sozluk = fbst_sabit_yildizlar

    for yildiz_adi, veriler in _aktif_sozluk.items():
        yildiz_derecesi = veriler["derece"]
        fark = aci_farki(gezegen_derecesi, yildiz_derecesi)

        if fark <= orb_siniri:
            # Raporlama şablonu (Kadersel Mimari Dili)
            rapor_metni = f"* Yıldız Hizalanması: {yildiz_adi} ({gezegen_adi} ile Yakınlaşma | Fark: {fark:.2f}°)\n"
            etki_bulundu = False

            # ÖNCELİK: Yıldızın Fatih Bağıl Sentez doktrinine ait özel bir yargı analizi var mı?
            if "yargi" in veriler:
                rapor_metni += f"   ⚖️ Özel Yargı: {veriler['yargi']}\n"
                etki_bulundu = True

            # Klasik etkileri tara
            for kategori, gezegen_etkileri in veriler["etkiler"].items():
                if gezegen_adi in gezegen_etkileri:
                    rapor_metni += f"   ➤ {kategori.upper()} ({gezegen_adi}): {gezegen_etkileri[gezegen_adi]}\n"
                    etki_bulundu = True
                elif "Genel" in gezegen_etkileri:
                    rapor_metni += f"   ➤ {kategori.upper()} (Genel): {gezegen_etkileri['Genel']}\n"
                    etki_bulundu = True

            if etki_bulundu:
                bulunan_muhurler.append(rapor_metni)

    return bulunan_muhurler

    
varsayilan_sabian_vizyonu = "Evrenin saklı geometri sembolü"
varsayilan_sabian_yorumu = "Bu derece, ilişkinizde henüz keşfedilmemiş derin bir ruhsal potansiyeli ve kendi içinizde çözmeniz gereken kadersel bir gizi barındırır."
# Streamlit sayfası en başta yapılandırılmalı
st.set_page_config(page_title="FAST — Asartepe Sinastri Tekniği", page_icon="logo.png", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=DM+Sans:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500;1,600&display=swap');
    
    .stApp {
        background-color: #FBF7F4;
        color: #2D2D2D;
        font-family: 'DM Sans', sans-serif;
    }
    
    /* === BAŞLIK STİLLERİ — SANATSKİ FONTLAR === */
    .stApp h1, .stApp h2, .stApp h3 {
        font-family: 'Cormorant Garamond', serif;
        color: #3D2E50;
        letter-spacing: 0.5px;
    }
    h1 { 
        color: #3D2E50 !important; 
        font-family: 'Cormorant Garamond', serif; 
        font-weight: 700;
        font-size: 2.4rem !important;
        letter-spacing: 1px;
    }
    h2 { 
        color: #4A3F5C !important; 
        font-family: 'Playfair Display', serif; 
        font-weight: 600;
        font-size: 1.7rem !important;
        letter-spacing: 0.5px;
    }
    h3 { 
        color: #5C4E6B !important; 
        font-family: 'Playfair Display', serif; 
        font-weight: 500;
        font-size: 1.3rem !important;
    }
    h4 { 
        color: #6B5B7B !important;
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    h5, h6 {
        color: #7A6B8A !important;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
    }
    
    /* === YAZI TIPI & SATIR ARALIĞI === */
    .stMarkdown p { 
        color: #4A4A4A; 
        line-height: 1.8; 
        font-family: 'DM Sans', sans-serif;
        font-size: 0.95rem;
    }
    
    /* === BUTONLAR — YUMUŞAK GRADYAN === */
    div.stButton > button {
        background: linear-gradient(135deg, #C9A96E 0%, #D4B88C 50%, #C9A96E 100%);
        background-size: 200% 200%;
        color: #ffffff;
        font-weight: 600;
        border-radius: 14px;
        border: none;
        padding: 12px 32px;
        box-shadow: 0 4px 16px rgba(201,169,110,0.3);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        letter-spacing: 0.8px;
        font-family: 'DM Sans', sans-serif;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    div.stButton > button:hover {
        box-shadow: 0 6px 24px rgba(201,169,110,0.5);
        transform: translateY(-2px);
        background-position: 100% 0;
    }
    div.stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(201,169,110,0.3);
    }
    
    /* === KADERSEL KUTU === */
    .kadersel-kutu {
        background: linear-gradient(135deg, #FFFFFF 0%, #FBF7F4 100%);
        padding: 24px;
        border-radius: 18px;
        border-left: 4px solid #C9A96E;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        backdrop-filter: blur(10px);
    }
    
    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F5F0EB 0%, #EDE7E0 50%, #E8E0D8 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #3D2E50;
        font-family: 'Cormorant Garamond', serif;
    }
    
    /* === TABLAR === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 12px 24px;
        font-weight: 500;
        color: #8A7F96;
        font-family: 'DM Sans', sans-serif;
        letter-spacing: 0.3px;
        transition: all 0.3s ease;
        border-bottom: 3px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #5C4E6B;
        background: rgba(255,255,255,0.5);
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        border-bottom: 3px solid #C9A96E;
        color: #3D2E50;
        font-weight: 600;
    }
    
    /* === EXPANDER === */
    div[data-testid="stExpander"] {
        background: linear-gradient(135deg, #FFFFFF 0%, #FBF7F4 100%);
        border-radius: 14px;
        border: 1px solid #E8E0D8;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }
    div[data-testid="stExpander"]:hover {
        box-shadow: 0 4px 18px rgba(0,0,0,0.07);
        border-color: #D4CFC8;
    }
    div[data-testid="stExpander"] summary {
        color: #4A3F5C;
        font-weight: 600;
        font-family: 'DM Sans', sans-serif;
        letter-spacing: 0.3px;
    }
    
    /* === ALERT KUTULARI === */
    .stAlert > div {
        border-radius: 14px !important;
        font-family: 'DM Sans', sans-serif;
    }
    
    /* === DATAFRAME === */
    div[data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    }
    
    /* === METRİK KUTULARI === */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #FFFFFF 0%, #FBF7F4 100%);
        border-radius: 14px;
        padding: 16px;
        border: 1px solid #E8E0D8;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }
    div[data-testid="stMetric"] label {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        color: #6B5B7B;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: 'Cormorant Garamond', serif;
        font-weight: 700;
        color: #3D2E50;
    }
    
    /* === SELECTBOX & INPUT === */
    .stSelectbox, .stTextInput {
        font-family: 'DM Sans', sans-serif;
    }
    .stSelectbox > div > div {
        border-radius: 10px;
        border-color: #E8E0D8;
    }
    .stSelectbox > div > div:hover {
        border-color: #C9A96E;
    }
    
    /* === ÖZEL BAŞLIK DEKORASYONU === */
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #C9A96E, transparent);
        margin: 2rem 0;
        border: none;
    }
    
    /* === SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #F5F0EB;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #C9A96E, #D4B88C);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #B89960, #C9A96E);
    }
    
    /* === YAZI SEÇİMİ === */
    ::selection {
        background-color: rgba(201,169,110,0.3);
        color: #3D2E50;
    }
    
    /* === SİDEBAR MOD KARTLARI === */
    .mod-card {
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .mod-card:hover {
        transform: translateY(-3px) scale(1.01);
    }
    
    </style>
""", unsafe_allow_html=True)

# --- 1. KISIM: FBST MOTORU (ENGINE) ---
# --- ASTEROİD VE ÖZEL NOKTA KONTROLÜ ---
def get_safe_flags(gezegen_id):
    """Asteroidler (Juno, Ceres vb.) için doğru efemeris bayrağını döner."""
    if gezegen_id > 10000: # AST_OFFSET genellikle 10000'dir
        return swe.FLG_MOSEPH | swe.FLG_SPEED
    return swe.FLG_SWIEPH | swe.FLG_SPEED

# Asteroit efemeris dosyaları (.se1) yüklü mü kontrol et
_EPHE_TESTED = False
_EPHE_AVAILABLE = False

def asteroid_ephe_mevcut_mu():
    global _EPHE_TESTED, _EPHE_AVAILABLE
    if _EPHE_TESTED:
        return _EPHE_AVAILABLE
    _EPHE_TESTED = True
    try:
        jd = swe.julday(2000, 1, 1, 12.0)
        swe.calc_ut(jd, swe.AST_OFFSET + 3)
        _EPHE_AVAILABLE = True
    except Exception:
        _EPHE_AVAILABLE = False
    return _EPHE_AVAILABLE

# Asteroit mean longitude fallback (J2000 epoch, dakikadan yakın)
# Kaynak: JPL Small-Body Database mean elements
ASTEROIT_MEAN_ELEMENTS = {
    "Ceres":  {"L0": 95.0,  "L_rate": 91.3073,  "a": 2.7675},
    "Pallas": {"L0": 30.0,  "L_rate": 105.7416, "a": 2.7730},
    "Juno":   {"L0": 238.0, "L_rate": 100.8245, "a": 2.6683},
    "Vesta":  {"L0": 151.0, "L_rate": 96.3557,  "a": 2.3617},
    "Eros":   {"L0": 315.0, "L_rate": 108.4028, "a": 1.4573},
    "Psyche": {"L0": 236.0, "L_rate": 96.1047,  "a": 2.9218},
    "Sappho": {"L0": 269.0, "L_rate": 101.8295, "a": 2.5735},
    "Amor":   {"L0": 207.0, "L_rate": 107.9656, "a": 1.9204},
    "Hygiea":    {"L0": 270.0, "L_rate": 84.8477,  "a": 3.1390},
    "Euphrosyne":{"L0": 165.0, "L_rate": 78.8516,  "a": 3.1560},
    "Nemesis":   {"L0": 102.0, "L_rate": 93.0980,  "a": 2.7506},
}

def asteroit_tahmini_derece(gezegen_adi, jd):
    """Efemeris dosyası yoksa, asteroit yaklaşık boylamını hesaplar."""
    import math
    if gezegen_adi not in ASTEROIT_MEAN_ELEMENTS:
        return None
    el = ASTEROIT_MEAN_ELEMENTS[gezegen_adi]
    t = (jd - swe.julday(2000, 1, 1, 12.0)) / 365.25
    derece = (el["L0"] + el["L_rate"] * t) % 360.0
    return derece

GEZEGENLER = {
    "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS,
    "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN, "Uranüs": swe.URANUS,
    "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO, "Lilith": swe.MEAN_APOG,     
    "Chiron": swe.CHIRON, "KAD": swe.MEAN_NODE, "GAD": 999,
    "Juno": swe.AST_OFFSET + 3, "Ceres": swe.AST_OFFSET + 1,
    "Pallas": swe.AST_OFFSET + 2, "Vesta": swe.AST_OFFSET + 4,
    "Eros": swe.AST_OFFSET + 433, "Psyche": swe.AST_OFFSET + 16,
    "Sappho": swe.AST_OFFSET + 80, "Amor": swe.AST_OFFSET + 1221,
    "Hygiea": swe.AST_OFFSET + 10, "Euphrosyne": swe.AST_OFFSET + 31,
    "Nemesis": swe.AST_OFFSET + 128
}

ASTEROID_ISIMLERI = {
    "Juno": "Evlilik, ortaklık, karmik sözleşmeler",
    "Ceres": "Besleme, şefkat, anne-baba figürü, kayıp",
    "Pallas": "Yaratıcılık, stratejik zeka, dişil güç",
    "Vesta": "Adanmışlık, kutsal odak, iç ateş",
    "Eros": "Arzu, tutku, cinsel çekim, şehvet",
    "Psyche": "Ruh bağı, psikolojik derinlik, kırılganlık",
    "Sappho": "Romantik aşk, estetik, dişil çekim",
    "Amor": "Koşulsuz sevgi, fedakarlık, affedicilik",
    "Hygiea": "Sağlık, bakım, wellness, hijyen",
    "Euphrosyne": "Neşe, iyi eğlence, keyif, neşe",
    "Nemesis": "Karmik denge, intikam, nesiller arası döngüler"
}

ASTEROID_SINASTRI_YORUMLARI = {
    ("Juno", "Güneş"): "Karmik evlilik mührü! Bu eşleşme, ruhlarınızın önceki yaşamlardan beri sürdürdüğü sözleşmenin somut tezahürü. Juno'nun kutsal dişil enerjisi, Güneş'in eril öz-yönetimiyle birleşerek 'kaderin evliliğini' oluşturur.",
    ("Juno", "Ay"): "Duygusal karmik bağ — Ruhsal kökleriniz birbirine kenetlenmiş. Juno'nun adalet arayışı, Ay'ın duygusal dünyasıyla beslenerek derin bir 'ruh eşi' hissi yaratır. Ancak bu bağ, duygusal bağımlılığa da dönüşebilir.",
    ("Juno", "Venüs"): "Aşkın kutsal mührü! Venüs'ün güzellik ve uyum enerjisi, Juno'nun evlilik arzusuyla birleşerek 'peri masalı' benzeri bir romantik kader yaratır. Sanat, güzellik ve estetik bu ilişkinin dilidir.",
    ("Juno", "Mars"): "Tutkulu savaş ve tutkulu sevişme — Juno ve Mars arasındaki bu temas, hem yoğun cinsel çekimi hem de güç savaşlarını tetikler. Bu çift, birbirini hem en çok arzuladığı hem de en çok sinirlendirdiği yerde tanır.",
    ("Juno", "Jüpiter"): "Kutsal bolluk ve genişleme! Juno'nun sözleşmesi, Jüpiter'in bereket enerjisiyle beslenerek aile kurma, ortak yatırım ve ruhsal büyüme vaat eder. Bu birleşme, her iki taraf için de 'kutsal genişleme' kapısıdır.",
    ("Juno", "Satürn"): "Zorlu ama kalıcı kader — Juno ve Satürn'ün buluşması, uzun ömürlü ve yapısal bir evlilik yaratır. Ancak bu yapı, sorumluluk baskıları ve korkularla da gelir. Sınav nặng ama ödül büyük.",
    ("Juno", "Uranüs"): "Devrimci evlilik! Sıra dışı, beklenmedik ve sarsıcı bir birleşme. Juno'nun geleneksel evlilik anlayışı, Uranüs'ün devrim enerjisiyle çatışarak 'özgür birliktelik' modeli yaratır.",
    ("Juno", "Neptün"): "Mistik karmik rüya — Juno ve Neptün'ün birleşmesi, hem derin ruhsal connectedliği hem de hayal kırıklığı potansiyelini taşır. Bu çift, birbirini 'ilahi aşk' ile görebilir ama gerçeklik testi de sert olabilir.",
    ("Juno", "Plüton"): "Tartarus mührü! Juno'nun karmik adaleti, Plüton'un dönüştürücü gücüyle birleşerek yoğun güç savaşları ve derin krizler yaratır. Ancak bu krizlerden geçenler, ebedi bir birleşme elde eder.",
    ("Juno", "Merkür"): "Aklın karmik evliliği — Juno'nun sözleşmesi, Merkür'ün iletişim zekasıyla birleşerek zihinsel uyum ve planlı birliktelik yaratır. Ancak bu akılcılık, duygusal derinliği gölgeleyebilir.",
    ("Ceres", "Güneş"): "Besleyici ruh eşi — Ceres'in şefkat enerjisi, Güneş'in öz-neşesiyle birleşerek birbirini besleyen ve büyüten bir ilişki yaratır. Bu çift, birbirinin 'en iyi versiyonu' olmasını sağlar.",
    ("Ceres", "Ay"): "Anne çocuk gibi derin bir bağ — Ceres ve Ay'ın birleşmesi, koşulsuz annelik şefkati ve derin duygusal beslenme yaratır. Birbirinizin yaralarını sarmak için buradasınız.",
    ("Ceres", "Mars"): "Aktif beslenme ve koruma — Ceres'in şefkat enerjisi, Mars'ın koruyucu gücüyle birleşerek 'savaşçı şefkat' yaratır. Birbirinizi hem beslersiniz hem de korursunuz.",
    ("Pallas", "Güneş"): "Stratejik ruh eşi — Pallas'ın yaratıcı zekası, Güneş'in liderlik enerjisiyle birleşerek ortak bir vizyon ve strateji yaratır. Bu çift, hem akıllı hem de yaratıcıdır.",
    ("Pallas", "Venüs"): "Estetik uyum — Pallas'ın sanatsal zekası, Venüs'ün güzellik anlayışıyla birleşerek derin bir estetik ve yaratıcı uyum yaratır. Sanat ve güzellik bu ilişkinin ortak dilidir.",
    ("Vesta", "Güneş"): "Kutsal adanmışlık — Vesta'nın iç ateşi, Güneş'in öz-ifadesiyle birleşerek ortak bir davaya adanmış bir ilişki yaratır. Bu çift, bir ortak amaç için birlikte yanar.",
    ("Vesta", "Venüs"): "Kutsal tutku — Vesta'nın adanmışlığı, Venüs'ün aşk enerjisiyle birleşerek derin ve kutsal bir cinsel/duygusal birliktelik yaratır. Birbirinize hem ruhsal hem de bedensel olarak adanırsınız.",
    ("Eros", "Venüs"): "Tutkulu aşk döngüsü — Eros'un arzu enerjisi, Venüs'ün aşk anlayışıyla birleşerek yoğun bir romantik ve cinsel çekim yaratır. Bu çift, birbirini 'yanıp tutuşarak' sever.",
    ("Eros", "Mars"): "Ham tutku — Eros ve Mars'ın birleşmesi, en yoğun cinsel ve eylemsel enerjiyi yaratır. Bu birleşme, hem derin bir arzu hem de yıkıcı bir tutku potansiyeli taşır.",
    ("Psyche", "Güneş"): "Ruh-beden birleşmesi — Psyche'nin ruhsal derinliği, Güneş'in öz-bilinciyle birleşerek 'ruhun beden bulması' gibi derin bir bağlantı yaratır. Bu çift, birbirinin ruhunu tanır.",
    ("Psyche", "Venüs"): "Aşkın ruhu — Psyche ve Venüs'ün birleşmesi, hem estetik hem de psikolojik derinlik yaratır. Bu aşk, yüzeysel değil, ruhun en derin katmanlarına iner.",
    ("Psyche", "Plüton"): "Dönüşümsel ruh bağı — Psyche ve Plüton'ın birleşmesi, en yoğun psikolojik dönüşüm ve kriz enerjisini yaratır. Bu birleşme, ya en derin şifayı ya da en derin yarayı taşır.",
    ("Sappho", "Venüs"): "Romantik estetik aşkı — Sappho'nun romantik enerjisi, Venüs'ün güzellik anlayışıyla birleşerek derin bir romantik ve estetik aşk yaratır. Sanat, müzik ve güzellik bu ilişkinin temelidir.",
    ("Sappho", "Ay"): "Duygusal romantizm — Sappho ve Ay'ın birleşmesi, derin duygusal romantizm ve hassasiyet yaratır. Bu çift, birbirinin en hassas noktalarını bilir ve besler.",
    ("Amor", "Venüs"): "Koşulsuz sevgi mührü — Amor'un fedakarlık enerjisi, Venüs'ün aşk anlayışıyla birleşerek koşulsuz ve affedici bir aşk yaratır. Bu birleşme, fedakarlığın en yüce formudur.",
    ("Amor", "Güneş"): "Kendini adayan ruh — Amor ve Güneş'in birleşmesi, hem öz-neşeyi hem de fedakarlığı bir arada yaşatır. Bu çift, hem kendini hem de partnerini sever.",
    ("Chiron", "Güneş"): "İyileştirici ruh eşi — Chiron'un yaralı şifacısı, Güneş'in öz-bilinciyle birleşerek hem kendi yaralarınızı hem de partnerinizin yaralarını iyileştirme potansiyeli yaratır.",
    ("Chiron", "Ay"): "Duygusal iyileşme — Chiron ve Ay'ın birleşmesi, derin duygusal yaraların şifasını taşır. Bu çift, birbirinin en karanlık duygusal yaralarını bile sarabilir.",
    ("Chiron", "Venüs"): "Aşk yarası ve şifası — Chiron ve Venüs'ün birleşmesi, hem aşk acısını hem de aşk şifasını bir arada yaşatır. Bu ilişkinin temeli, yaralı kalplerin birbirini onarmasıdır.",
}

# ==============================================================================
# 🌙 ARAP NOKTALARI - İLİŞKİ VE EVLİLİK ANALİZİ
# ==============================================================================
# Arap Noktaları, astrolojide kadersel noktaları temsil eder.
# Formül: Gündüz = ASC + Nokta1 - Nokta2 / Gece = ASC + Nokta2 - Nokta1

ARAP_NOKTALARI_ILISKI = {
    "Evlilik Noktası": {"nokta1": "7HC", "nokta2": "Venüs", "kisa": "EVN", "aciklama": "Evlilik ve uzun süreli birliktelik kadersel kapısı"},
    "Aşk Noktası":     {"nokta1": "Venüs", "nokta2": "Ay", "kisa": "ASK", "aciklama": "Romantik aşk ve duygusal çekim merkezi"},
    "Tutku Noktası":   {"nokta1": "Mars", "nokta2": "Ay", "kisa": "TUT", "aciklama": "Cinsel tutku ve eylemsel arzu odağı"},
    "Ortaklık Noktası": {"nokta1": "7HC", "nokta2": "Güneş", "kisa": "ORT", "aciklama": "Eşit güçte ortaklık ve ittifak çizgisi"},
    "Sadakat Noktası":  {"nokta1": "Venüs", "nokta2": "Satürn", "kisa": "SDK", "aciklama": "Uzun vadeli bağlılık ve sadakat sözleşmesi"},
    "Cinsellik Noktası": {"nokta1": "Mars", "nokta2": "Venüs", "kisa": "CNS", "aciklama": "Cinsel çekim ve fiziksel uyum haritası"},
    "Evlilik Mutluluğu": {"nokta1": "Venüs", "nokta2": "Jüpiter", "kisa": "EVM", "aciklama": "Evlilikte bolluk, bereket ve ruhsal genişleme"},
    "Boşanma Noktası":  {"nokta1": "2HC", "nokta2": "7HC", "kisa": "BSN", "aciklama": "Ayrılık ve kopma enerjisi eşiği (farkındalık için)"},
}

ARAP_NOKTA_BURC_YORUMLARI = {
    ("Evlilik Noktası", "Koç"): "Evlilik kaderselliğiniz aceleci ve bağımsız bir ruhla harmanlanmış. Erken yaşlarda veya ani kararlarla evlilik kapısı açılabilir. Cesaret ve öncülük bu birlikteliğin temel taşıdır.",
    ("Evlilik Noktası", "Boğa"): "Evlilik kaderselliğiniz toprak, güzellik ve kalıcılık üzerine kuruludur. Sabırlı bir aşk, maddi güvenlik ve duyusal zevkler bu evliliğin temel direkleridir. Toprakla beslenen bir bağ.",
    ("Evlilik Noktası", "İkizler"): "Evlilik kaderselliğiniz iletişim, zihinsel uyum ve çok yönlülük üzerine inşa edilmiş. Konuşarak, öğrenerek ve paylaşarak büyüyen bir evlilik. Tek düzelik bu bağda zehir gibidir.",
    ("Evlilik Noktası", "Yengeç"): "Evlilik kaderselliğiniz derin duygusal beslenme, koruma ve aile kurma arzusuyla yoğrulmuş. Anne-çocuk bağı kadar derin bir ruhsal sığınak. Duygusal güvenlik en temel ihtiyacınızdır.",
    ("Evlilik Noktası", "Aslan"): "Evlilik kaderselliğiniz görkem, yaratıcılık ve öz-neşe üzerine kuruludur. Gösterişli, tutkulu ve onurlu bir birliktelik. Partneriniz hem sevgiliniz hem de sahnenizin en parlak yıldızıdır.",
    ("Evlilik Noktası", "Başak"): "Evlilik kaderselliğiniz hizmet, mükemmellik arayışı ve pratik düzen üzerine inşa edilmiş. Detaycı, titiz ve sadık bir birliktelik. Birbirinizi iyileştirmek ve geliştirmek için buradasınız.",
    ("Evlilik Noktası", "Terazi"): "Evlilik kaderselliğiniz uyum, estetik ve denge üzerine kuruludur. Adalet arayışı, sanatsal duyarlılık ve diplomatik iletişim bu evliliğin ruhudur. Eşitlik en kutsal değerinizi.",
    ("Evlilik Noktası", "Akrep"): "Evlilik kaderselliğiniz derin dönüşüm, tutku ve gizem üzerine yoğrulmuş. Yoğun power struggle'lar, cinsel çekim ve ruhsal yeniden doğuş. Bu evlilik ya sizi tamamen dönüştürür ya da yıkar.",
    ("Evlilik Noktası", "Yay"): "Evlilik kaderselliğiniz özgürlük, genişleme ve felsefi derinlik üzerine kuruludur. Farklı kültürler, uzun seyahatler ve ortak maceralar bu evliliğin besin kaynağıdır. Dar kalıplar bu bağı boğar.",
    ("Evlilik Noktası", "Oğlak"): "Evlilik kaderselliğiniz yapı, sorumluluk ve uzun vadeli planlar üzerine inşa edilmiş. Zorlu sınavlar, gecikmeli ödüller ve toplumsal statü bu evliliğin gölgesidir. Sabır en büyük erdemini.",
    ("Evlilik Noktası", "Kova"): "Evlilik kaderselliğiniz sıra dışı, özgür ve devrimci bir ruhla harmanlanmış. Geleneksel kalıpların dışındaki birliktelikler, arkadaşlık temelli aşk ve insani değerler. Özgürlük bu bağda kutsaldır.",
    ("Evlilik Noktası", "Balık"): "Evlilik kaderselliğiniz maneviyat, fedakarlık ve koşulsuz sevgi üzerine kuruludur. Ruh eşi hissi, mistik bağlantı ve hayal gücü. Ancak sınırlar bu bağda en kritik sınavını verir.",

    ("Aşk Noktası", "Koç"): "Aşk kaderselliğiniz ani, tutkulu ve cesur bir şekilde kapınızı çalar. İlk bakışta aşk, hızlı gelişen duygular ve fiziksel çekim bu aşkın dilidir. Sabırsızlık hem ateşleyici hem de yıkıcıdır.",
    ("Aşk Noktası", "Boğa"): "Aşk kaderselliğiniz yavaş gelişen, duyusal ve kalıcı bir şekilde olgunlaşır. Dokunma, koku ve güzellik bu aşkın besin kaynağıdır. Sahiplenici tutumlar bu güzel bağı zehirleyebilir.",
    ("Aşk Noktası", "İkizler"): "Aşk kaderselliğiniz zihinsel uyum, flört ve iletişim üzerine kuruludur. Konuşarak aşık olur, paylaşarak büyürsünüz. Ancak yüzeysellik riski her zaman kapınızda bekler.",
    ("Aşk Noktası", "Yengeç"): "Aşk kaderselliğiniz derin duygusal beslenme ve koruma içgüdüsüyle yoğrulmuş. Anne şefkati kadar derin bir romantizm. Geçmiş yaralar bu aşkı hem besler hem de zehirler.",
    ("Aşk Noktası", "Aslan"): "Aşk kaderselliğiniz görkemli, tutkulu ve gösterişli bir sahneyle gelir. Hayranlık, yaratıcılık ve cömertlik bu aşkın dilidir. Ego çatışmaları bu parlak aşkı karartabilir.",
    ("Aşk Noktası", "Başak"): "Aşk kaderselliğiniz pratik hizmet, titizlik ve mükemmellik arayışıyla beslenir. Küçük jestler, düzenli ilgi ve zihinsel analiz bu aşkın temelidir. Mükemmeliyetçilik bu bağı yorabilir.",
    ("Aşk Noktası", "Terazi"): "Aşk kaderselliğiniz estetik, uyum ve romantizm üzerine inşa edilmiş. Sanat, güzellik ve denge bu aşkın ruhudur. Kararsızlık ve yüzeysellik bu derin bağın düşmanıdır.",
    ("Aşk Noktası", "Akrep"): "Aşk kaderselliğiniz derin, tutkulu ve dönüştürücü bir enerjiyle gelir. Cinsel çekim, gizem ve ruhsal derinlik bu aşkın temel direkleri. Kontrol ve kıskançlık bu bağı zehirleyebilir.",
    ("Aşk Noktası", "Yay"): "Aşk kaderselliğiniz özgürlük, macera ve felsefi derinlik üzerine kuruludur. Farklı kültürler, uzun sohbetler ve ortak keşifler bu aşkın besin kaynağıdır. Dar kalıplar bu bağı boğar.",
    ("Aşk Noktası", "Oğlak"): "Aşk kaderselliğiniz yavaş gelişen, ciddi ve yapısal bir şekilde olgunlaşır. Güvenilirlik, sadakat ve uzun vadeli planlar bu aşkın temelidir. Mesafeli tutumlar bu bağı soğutabilir.",
    ("Aşk Noktası", "Kova"): "Aşk kaderselliğiniz sıra dışı, özgür ve insani değerler üzerine kuruludur. Arkadaşlık temelli aşk, entelektüel uyum ve toplumsal duyarlılık bu aşkın ruhudur. Duygusal kopukluk riski her zaman vardır.",
    ("Aşk Noktası", "Balık"): "Aşk kaderselliğiniz maneviyat, fedakarlık ve koşulsuz sevgi üzerine yoğrulmuş. Ruh eşi hissi, mistik bağlantı ve hayal gücü bu aşkın besin kaynağıdır. Sınırlar bu bağda en kritik sınavını verir.",

    ("Tutku Noktası", "Koç"): "Tutku kaderselliğiniz ham, cesur ve eylemsel bir enerjiyle yoğrulmuş. Fiziksel çekim, rekabet ve öncülük bu tutkunun dilidir. Sabırsızlık ve öfke bu güçlü ateşi yıkabilir.",
    ("Tutku Noktası", "Boğa"): "Tutku kaderselliğiniz duyusal, yavaş ve derin bir şekilde olgunlaşır. Dokunma, koku ve zevk bu tutkunun besin kaynağıdır. Sahiplenici tutumlar bu güzel bağı zehirleyebilir.",
    ("Tutku Noktası", "İkizler"): "Tutku kaderselliğiniz zihinsel uyum, flört ve iletişim üzerine kuruludur. Konuşarak tutkulanır, paylaşarak coşarsınız. Ancak yüzeysellik riski her zaman kapınızda bekler.",
    ("Tutku Noktası", "Yengeç"): "Tutku kaderselliğiniz derin duygusal beslenme ve koruma içgüdüsüyle yoğrulmuş. Anne şefkati kadar derin bir tutku. Geçmiş yaralar bu ateşi hem besler hem de zehirler.",
    ("Tutku Noktası", "Aslan"): "Tutku kaderselliğiniz görkemli, tutkulu ve gösterişli bir sahneyle gelir. Hayranlık, yaratıcılık ve cömertlik bu tutkunun dilidir. Ego çatışmaları bu parlak ateşi karartabilir.",
    ("Tutku Noktası", "Başak"): "Tutku kaderselliğiniz pratik hizmet, titizlik ve mükemmellik arayışıyla beslenir. Detaycı, düzenli ve sadık bir tutku. Mükemmeliyetçilik bu bağı yorabilir.",
    ("Tutku Noktası", "Terazi"): "Tutku kaderselliğiniz estetik, uyum ve romantizm üzerine inşa edilmiş. Sanat, güzellik ve denge bu tutkunun ruhudur. Kararsızlık bu derin bağın düşmanıdır.",
    ("Tutku Noktası", "Akrep"): "Tutku kaderselliğiniz derin, yoğun ve dönüştürücü bir enerjiyle gelir. Cinsel çekim, gizem ve ruhsal derinlik bu tutkunun temel direkleri. Kontrol ve kıskançlık bu bağı zehirleyebilir.",
    ("Tutku Noktası", "Yay"): "Tutku kaderselliğiniz özgürlük, macera ve felsefi derinlik üzerine kuruludur. Farklı kültürler, uzun seyahatler ve ortak keşifler bu tutkunun besin kaynağıdır.",
    ("Tutku Noktası", "Oğlak"): "Tutku kaderselliğiniz yavaş gelişen, ciddi ve yapısal bir şekilde olgunlaşır. Güvenilirlik, sadakat ve uzun vadeli planlar bu tutkunun temelidir. Mesafeli tutumlar bu bağı soğutabilir.",
    ("Tutku Noktası", "Kova"): "Tutku kaderselliğiniz sıra dışı, özgür ve devrimci bir ruhla harmanlanmış. Geleneksel kalıpların dışındaki tutkular ve insani değerler. Özgürlük bu bağda kutsaldır.",
    ("Tutku Noktası", "Balık"): "Tutku kaderselliğiniz maneviyat, fedakarlık ve koşulsuz sevgi üzerine kuruludur. Ruh eşi hissi, mistik bağlantı ve hayal gücü bu tutkunun besin kaynağıdır.",

    ("Ortaklık Noktası", "Koç"): "Ortaklık kaderselliğiniz cesur, bağımsız ve öncülük eden bir ruhla harmanlanmış. Eşit güçte, rekabetçi ama destekleyici bir birliktelik. Liderlik struggle'ları bu bağın sınavıdır.",
    ("Ortaklık Noktası", "Boğa"): "Ortaklık kaderselliğiniz toprak, güvenirlik ve kalıcılık üzerine kuruludur. Maddi güvenlik, duyusal zevkler ve sabırlı büyüme bu ortaklığın temel direkleridir.",
    ("Ortaklık Noktası", "İkizler"): "Ortaklık kaderselliğiniz iletişim, zihinsel uyum ve çok yönlülük üzerine inşa edilmiş. Konuşarak, öğrenerek ve paylaşarak büyüyen bir ortaklık.",
    ("Ortaklık Noktası", "Yengeç"): "Ortaklık kaderselliğiniz derin duygusal beslenme, koruma ve aile kurma arzusuyla yoğrulmuş. Duygusal güvenlik en temel ihtiyacınızdır.",
    ("Ortaklık Noktası", "Aslan"): "Ortaklık kaderselliğiniz görkem, yaratıcılık ve öz-neşe üzerine kuruludur. Gösterişli, tutkulu ve onurlu bir ortaklık.",
    ("Ortaklık Noktası", "Başak"): "Ortaklık kaderselliğiniz hizmet, mükemmellik arayışı ve pratik düzen üzerine inşa edilmiş. Detaycı, titiz ve sadık bir ortaklık.",
    ("Ortaklık Noktası", "Terazi"): "Ortaklık kaderselliğiniz uyum, estetik ve denge üzerine kuruludur. Eşitlik en kutsal değerinizi oluşturur.",
    ("Ortaklık Noktası", "Akrep"): "Ortaklık kaderselliğiniz derin dönüşüm, tutku ve gizem üzerine yoğrulmuş. Yoğun power struggle'lar ve ruhsal yeniden doğuş.",
    ("Ortaklık Noktası", "Yay"): "Ortaklık kaderselliğiniz özgürlük, genişleme ve felsefi derinlik üzerine kuruludur. Ortak maceralar bu ortaklığın besin kaynağıdır.",
    ("Ortaklık Noktası", "Oğlak"): "Ortaklık kaderselliğiniz yapı, sorumluluk ve uzun vadeli planlar üzerine inşa edilmiş. Sabır en büyük erdemini.",
    ("Ortaklık Noktası", "Kova"): "Ortaklık kaderselliğiniz sıra dışı, özgür ve devrimci bir ruhla harmanlanmış. Arkadaşlık temelli ortaklık ve insani değerler.",
    ("Ortaklık Noktası", "Balık"): "Ortaklık kaderselliğiniz maneviyat, fedakarlık ve koşulsuz sevgi üzerine kuruludur. Ruh eşi hissi ve mistik bağlantı.",

    ("Sadakat Noktası", "Koç"): "Sadakat kaderselliğiniz cesur, bağımsız ve öncülük eden bir ruhla harmanlanmış. Özgürlüğüne düşkün ama sözünün eri bir sadakat. Bağımsızlık bu bağda kutsaldır.",
    ("Sadakat Noktası", "Boğa"): "Sadakat kaderselliğiniz toprak, güvenirlik ve kalıcılık üzerine kuruludur. Fiziksel sadakat, maddi destek ve duyusal bağlılık bu sadakatın temel direkleridir.",
    ("Sadakat Noktası", "İkizler"): "Sadakat kaderselliğiniz iletişim, zihinsel uyum ve çok yönlülük üzerine inşa edilmiş. Konuşarak, öğrenerek ve paylaşarak büyüyen bir sadakat.",
    ("Sadakat Noktası", "Yengeç"): "Sadakat kaderselliğiniz derin duygusal beslenme, koruma ve aile kurma arzusuyla yoğrulmuş. Aile sadakati ve duygusal bağlılık en temel değeri.",
    ("Sadakat Noktası", "Aslan"): "Sadakat kaderselliğiniz görkem, yaratıcılık ve öz-neşe üzerine kuruludur. Onurlu, tutkulu ve gösterişli bir sadakat.",
    ("Sadakat Noktası", "Başak"): "Sadakat kaderselliğiniz hizmet, mükemmellik arayışı ve pratik düzen üzerine inşa edilmiş. Detaycı, titiz ve sadık bir bağlılık.",
    ("Sadakat Noktası", "Terazi"): "Sadakat kaderselliğiniz uyum, estetik ve denge üzerine kuruludur. Eşitlik ve adalet bu sadakatın temel direkleridir.",
    ("Sadakat Noktası", "Akrep"): "Sadakat kaderselliğiniz derin dönüşüm, tutku ve gizem üzerine yoğrulmuş. Koşulsuz, derin ve dönüştürücü bir sadakat.",
    ("Sadakat Noktası", "Yay"): "Sadakat kaderselliğiniz özgürlük, genişleme ve felsefi derinlik üzerine kuruludur. Farklı kültürler ve ortak keşifler bu sadakatın besin kaynağıdır.",
    ("Sadakat Noktası", "Oğlak"): "Sadakat kaderselliğiniz yapı, sorumluluk ve uzun vadeli planlar üzerine inşa edilmiş. Güvenilirlik ve disiplinli sadakat bu bağın temelidir.",
    ("Sadakat Noktası", "Kova"): "Sadakat kaderselliğiniz sıra dışı, özgür ve devrimci bir ruhla harmanlanmış. Arkadaşlık temelli sadakat ve insani değerler.",
    ("Sadakat Noktası", "Balık"): "Sadakat kaderselliğiniz maneviyat, fedakarlık ve koşulsuz sevgi üzerine kuruludur. Manevi bağlılık ve ruhsal sadakat bu bağın ruhudur.",

    ("Cinsellik Noktası", "Koç"): "Cinsel çekim kaderselliğiniz ham, cesur ve eylemsel bir enerjiyle yoğrulmuş. İlk bakışta fiziksel çekim ve yoğun arzu bu cinselliğin dilidir.",
    ("Cinsellik Noktası", "Boğa"): "Cinsel çekim kaderselliğiniz duyusal, yavaş ve derin bir şekilde olgunlaşır. Dokunma, koku ve zevk bu cinselliğin besin kaynağıdır.",
    ("Cinsellik Noktası", "İkizler"): "Cinsel çekim kaderselliğiniz zihinsel uyum, flört ve iletişim üzerine kuruludur. Konuşarak çekim, paylaşarak coşku yaratır.",
    ("Cinsellik Noktası", "Yengeç"): "Cinsel çekim kaderselliğiniz derin duygusal beslenme ve koruma içgüdüsüyle yoğrulmuş. Güvenlik ve şefkat bu cinselliğin temelidir.",
    ("Cinsellik Noktası", "Aslan"): "Cinsel çekim kaderselliğiniz görkemli, tutkulu ve gösterişli bir sahneyle gelir. Hayranlık, yaratıcılık ve cömertlik bu cinselliğin dilidir.",
    ("Cinsellik Noktası", "Başak"): "Cinsel çekim kaderselliğiniz pratik, titiz ve mükemmellik arayışıyla beslenir. Detaycı, düzenli ve sadık bir cinsellik.",
    ("Cinsellik Noktası", "Terazi"): "Cinsel çekim kaderselliğiniz estetik, uyum ve romantizm üzerine inşa edilmiş. Sanat, güzellik ve denge bu cinselliğin ruhudur.",
    ("Cinsellik Noktası", "Akrep"): "Cinsel çekim kaderselliğiniz derin, yoğun ve dönüştürücü bir enerjiyle gelir. En derin cinsel çekim ve ruhsal dönüşüm bu noktada düğümlenir.",
    ("Cinsellik Noktası", "Yay"): "Cinsel çekim kaderselliğiniz özgürlük, macera ve felsefi derinlik üzerine kuruludur. Farklı deneyimler ve ortak keşifler bu cinselliğin besin kaynağıdır.",
    ("Cinsellik Noktası", "Oğlak"): "Cinsel çekim kaderselliğiniz yavaş gelişen, ciddi ve yapısal bir şekilde olgunlaşır. Güvenilirlik ve disiplin bu cinselliğin temelidir.",
    ("Cinsellik Noktası", "Kova"): "Cinsel çekim kaderselliğiniz sıra dışı, özgür ve devrimci bir ruhla harmanlanmış. Geleneksel kalıpların dışındaki cinsellik ve insani değerler.",
    ("Cinsellik Noktası", "Balık"): "Cinsel çekim kaderselliğiniz maneviyat, fedakarlık ve koşulsuz sevgi üzerine kuruludur. Ruh eşi hissi, mistik bağlantı ve hayal gücü bu cinselliğin besin kaynağıdır.",

    ("Evlilik Mutluluğu", "Koç"): "Evlilik mutluluğu kaderselliğiniz cesur, bağımsız ve öncülük eden bir ruhla harmanlanmış. Macera ve heyecan bu evliliğin neşesidir.",
    ("Evlilik Mutluluğu", "Boğa"): "Evlilik mutluluğu kaderselliğiniz toprak, güvenirlik ve kalıcılık üzerine kuruludur. Maddi bolluk, duyusal zevkler ve sabırlı büyüme bu mutluluğun temelidir.",
    ("Evlilik Mutluluğu", "İkizler"): "Evlilik mutluluğu kaderselliğiniz iletişim, zihinsel uyum ve çok yönlülük üzerine inşa edilmiş. Konuşarak, öğrenerek ve paylaşarak büyüyen bir mutluluk.",
    ("Evlilik Mutluluğu", "Yengeç"): "Evlilik mutluluğu kaderselliğiniz derin duygusal beslenme, koruma ve aile kurma arzusuyla yoğrulmuş. Aile içi neşe ve duygusal güvenlik bu mutluluğun ruhudur.",
    ("Evlilik Mutluluğu", "Aslan"): "Evlilik mutluluğu kaderselliğiniz görkem, yaratıcılık ve öz-neşe üzerine kuruludur. Gösterişli, tutkulu ve onurlu bir neşe.",
    ("Evlilik Mutluluğu", "Başak"): "Evlilik mutluluğu kaderselliğiniz hizmet, mükemmellik arayışı ve pratik düzen üzerine inşa edilmiş. Küçük jestler ve düzenli ilgi bu mutluluğun temelidir.",
    ("Evlilik Mutluluğu", "Terazi"): "Evlilik mutluluğu kaderselliğiniz uyum, estetik ve denge üzerine kuruludur. Sanat, güzellik ve romantizm bu mutluluğun ruhudur.",
    ("Evlilik Mutluluğu", "Akrep"): "Evlilik mutluluğu kaderselliğiniz derin dönüşüm, tutku ve gizem üzerine yoğrulmuş. Yoğun derinlik ve ruhsal yeniden doğuş bu mutluluğun temelidir.",
    ("Evlilik Mutluluğu", "Yay"): "Evlilik mutluluğu kaderselliğiniz özgürlük, genişleme ve felsefi derinlik üzerine kuruludur. Farklı kültürler, uzun seyahatler ve ortak maceralar bu mutluluğun besin kaynağıdır.",
    ("Evlilik Mutluluğu", "Oğlak"): "Evlilik mutluluğu kaderselliğiniz yapı, sorumluluk ve uzun vadeli planlar üzerine inşa edilmiş. Gecikmeli ödüller ve sabırlı büyüme bu mutluluğun temelidir.",
    ("Evlilik Mutluluğu", "Kova"): "Evlilik mutluluğu kaderselliğiniz sıra dışı, özgür ve devrimci bir ruhla harmanlanmış. Arkadaşlık temelli mutluluk ve insani değerler.",
    ("Evlilik Mutluluğu", "Balık"): "Evlilik mutluluğu kaderselliğiniz maneviyat, fedakarlık ve koşulsuz sevgi üzerine kuruludur. Ruh eşi hissi ve mistik mutluluk bu bağın ruhudur.",

    ("Boşanma Noktası", "Koç"): "Ayrılık enerjisi kaderselliğiniz aceleci ve bağımsız bir ruhla yoğrulmuş. ani kararlar, öfke anları ve bağımsızlık arzusu bu noktada düğümlenir. Farkındalık bu enerjiyi dönüştürebilir.",
    ("Boşanma Noktası", "Boğa"): "Ayrılık enerjisi kaderselliğiniz toprak, inatçılık ve maddi bağlarla yoğrulmuş. Maddi güvence endişesi ve sahiplenicilik bu noktada yoğunlaşır. Değişime direnç bu enerjinin temelidir.",
    ("Boşanma Noktası", "İkizler"): "Ayrılık enerjisi kaderselliğiniz iletişim kopukluğu, yüzeysellik ve kararsızlıkla yoğrulmuş. Konuşmadan dinleme ve anlama eksikliği bu noktada kritikleşir.",
    ("Boşanma Noktası", "Yengeç"): "Ayrılık enerjisi kaderselliğiniz duygusal duvarlar, geçmiş yaralar ve korunma içgüdüsüyle yoğrulmuş. Duygusal kopukluk ve güvensizlik bu noktada yoğunlaşır.",
    ("Boşanma Noktası", "Aslan"): "Ayrılık enerjisi kaderselliğiniz ego çatışmaları, gurur ve gösterişmerkezcilikle yoğrulmuş. Dikkat ve hayranlık eksikliği bu noktada kritikleşir.",
    ("Boşanma Noktası", "Başak"): "Ayrılık enerjisi kaderselliğiniz mükemmeliyetçilik, eleştiri ve detaylara takılma ile yoğrulmuş. Pratik düzen ve hizmet eksikliği bu noktada yoğunlaşır.",
    ("Boşanma Noktası", "Terazi"): "Ayrılık enerjisi kaderselliğiniz uyumsuzluk, adaletsizlik ve kararsızlıkla yoğrulmuş. Denge eksikliği ve ilişkide eşitsizlik bu noktada kritikleşir.",
    ("Boşanma Noktası", "Akrep"): "Ayrılık enerjisi kaderselliğiniz yoğun kıskançlık, kontrol ihtiyacı ve gizlilikle yoğrulmuş. Güven eksikliği ve yoğun power struggle'lar bu noktada yoğunlaşır.",
    ("Boşanma Noktası", "Yay"): "Ayrılık enerjisi kaderselliğiniz özgürlük ihtiyacı, farklılık ve macera arayışıyla yoğrulmuş. Dar kalıplara sığamama ve farklı yollar bu noktada kritikleşir.",
    ("Boşanma Noktası", "Oğlak"): "Ayrılık enerjisi kaderselliğiniz soğukluk, mesafe ve sorumluluk baskılarıyla yoğrulmuş. Duygusal kopukluk ve yapısal baskılar bu noktada yoğunlaşır.",
    ("Boşanma Noktası", "Kova"): "Ayrılık enerjisi kaderselliğiniz kopukluk, özgürleşme ihtiyacı ve sıra dışı beklentilerle yoğrulmuş. Duygusal mesafe ve farklı değerler bu noktada kritikleşir.",
    ("Boşanma Noktası", "Balık"): "Ayrılık enerjisi kaderselliğiniz hayal kırıklığı, kaçış ve kurban zihniyetiyle yoğrulmuş. Sınırsız fedakarlık ve reality kaybı bu noktada yoğunlaşır.",
}

ARAP_NOKTA_EV_YORUMLARI = {
    ("Evlilik Noktası", 1): "Evlilik kaderselliğiniz kimliğinizle doğrudan bağlantılı. Kendinizi partneriniz aracılığıyla yeniden keşfedersiniz. Evlilik hayatınızın merkezinde.",
    ("Evlilik Noktası", 2): "Evlilik kaderselliğiniz maddi değerler, güvenlik ve kaynaklarla yoğrulmuş. Ortak finansal planlar ve duyusal zevkler bu evliliğin temelidir.",
    ("Evlilik Noktası", 3): "Evlilik kaderselliğiniz iletişim, kardeşler ve çevreyle bağlantılı. Konuşarak büyüyen, kısa seyahatler ve öğrenmeyle beslenen bir evlilik.",
    ("Evlilik Noktası", 4): "Evlilik kaderselliğiniz aile kökleri, ev ve iç dünyayle derin bir bağa sahip. Evlilik, sığınak ve anne-baba olma arzusuyla beslenir.",
    ("Evlilik Noktası", 5): "Evlilik kaderselliğiniz yaratıcılık, çocuklar ve romantik aşkla yoğrulmuş. Eğlence, sanat ve çocuk sahibi olma bu evliliğin neşesidir.",
    ("Evlilik Noktası", 6): "Evlilik kaderselliğiniz hizmet, rutin ve sağlıkla bağlantılı. Birbirini besleyen, düzenli ve pratik bir evlilik. Sağlık konuları gündemde olabilir.",
    ("Evlilik Noktası", 7): "Evlilik kaderselliğiniz en güçlü noktada — 7. evin kendi evidir. Eş seçimi, ortaklık ve açık ittifaklar bu evliliğin temel direğidir.",
    ("Evlilik Noktası", 8): "Evlilik kaderselliğiniz derin dönüşüm, krizler ve ortak kaynaklarla yoğrulmuş. Yoğun güç savaşları, cinsel derinlik ve ruhsal yeniden doğuş.",
    ("Evlilik Noktası", 9): "Evlilik kaderselliğiniz felsefe, yüksek öğrenim ve farklı kültürlerle beslenir. Uzun seyahatler, ortak inançlar ve ruhsal genişleme bu evliliğin ruhudur.",
    ("Evlilik Noktası", 10): "Evlilik kaderselliğiniz kariyer, toplumsal statü ve mirasla bağlantılı. Toplumsal baskılar ve kariyer hedefleri bu evliliğin gölgesidir.",
    ("Evlilik Noktası", 11): "Evlilik kaderselliğiniz arkadaşlık, gruplar ve insani değerlerle yoğrulmuş. Arkadaşlık temelli aşk ve toplumsal duyarlılık bu evliliğin besin kaynağıdır.",
    ("Evlilik Noktası", 12): "Evlilik kaderselliğiniz gizli yaralar, maneviyat ve fedakarlıkla yoğrulmuş. Ruh eşi hissi, mistik bağlantı ve bilinçdışı kalıplar bu evliliğin derin katmanlarıdır.",

    ("Aşk Noktası", 1): "Aşk kaderselliğiniz kimliğinizle doğrudan bağlantılı. Kendinizi bu aşkta yeniden keşfedersiniz. Aşk hayatınızın merkezinde.",
    ("Aşk Noktası", 2): "Aşk kaderselliğiniz maddi değerler, güvenlik ve kaynaklarla yoğrulmuş. Duyusal zevkler ve fiziksel çekim bu aşkın temelidir.",
    ("Aşk Noktası", 3): "Aşk kaderselliğiniz iletişim, kardeşler ve çevreyle bağlantılı. Konuşarak büyüyen bir aşk. Kısa seyahatler ve öğrenmeyle beslenir.",
    ("Aşk Noktası", 4): "Aşk kaderselliğiniz aile kökleri, ev ve iç dünyayle derin bir bağa sahip. Evlilik, sığınak ve anne-baba olma arzusuyla beslenir.",
    ("Aşk Noktası", 5): "Aşk kaderselliğiniz yaratıcılık, çocuklar ve romantik aşkla yoğrulmuş. Eğlence, sanat ve çocuk sahibi olma bu aşkın neşesidir.",
    ("Aşk Noktası", 6): "Aşk kaderselliğiniz hizmet, rutin ve sağlıkla bağlantılı. Birbirini besleyen, düzenli ve pratik bir aşk.",
    ("Aşk Noktası", 7): "Aşk kaderselliğiniz en güçlü noktada — 7. evin kendi evidir. Eş seçimi ve açık ittifaklar bu aşkın temel direğidir.",
    ("Aşk Noktası", 8): "Aşk kaderselliğiniz derin dönüşüm, krizler ve ortak kaynaklarla yoğrulmuş. Yoğun güç savaşları ve ruhsal yeniden doğuş.",
    ("Aşk Noktası", 9): "Aşk kaderselliğiniz felsefe, yüksek öğrenim ve farklı kültürlerle beslenir. Uzun seyahatler ve ruhsal genişleme bu aşkın ruhudur.",
    ("Aşk Noktası", 10): "Aşk kaderselliğiniz kariyer, toplumsal statü ve mirasla bağlantılı. Toplumsal baskılar bu aşkın gölgesidir.",
    ("Aşk Noktası", 11): "Aşk kaderselliğiniz arkadaşlık, gruplar ve insani değerlerle yoğrulmuş. Arkadaşlık temelli aşk bu evliliğin besin kaynağıdır.",
    ("Aşk Noktası", 12): "Aşk kaderselliğiniz gizli yaralar, maneviyat ve fedakarlıkla yoğrulmuş. Ruh eşi hissi ve bilinçdışı kalıplar bu aşkın derin katmanlarıdır.",
}

# Kısaltılmış ev yorumları (diğer noktalar için de kullanılır)
ARAP_EV_KISAYORUMLARI = {
    1: "Kendi kimliğinizle, bedeninizle ve öz-bilincinizle yoğrulmuş.", 2: "Maddi değerler, güvenlik ve kaynaklarla beslenir.",
    3: "İletişim, çevre ve kısa seyahatlerle bağlantılı.", 4: "Aile kökleri, ev ve iç dünyayla derin bağı var.",
    5: "Yaratıcılık, çocuklar ve romantik aşkla yoğrulmuş.", 6: "Hizmet, rutin ve sağlıkla bağlantılı.",
    7: "Eş seçimi ve açık ittifakların merkezi.", 8: "Derin dönüşüm, krizler ve ortak kaynaklarla beslenir.",
    9: "Felsefe, yüksek öğrenim ve farklı kültürlerle genişler.", 10: "Kariyer, toplumsal statü ve mirasla bağlantılı.",
    11: "Arkadaşlık, gruplar ve insani değerlerle yoğrulmuş.", 12: "Gizli yaralar, maneviyat ve bilinçdışıyla derinleşir.",
}

# ==============================================================================
# 🌍 ASTROKARTOGRAFİ MOTORU (Bilimsel Lokasyon Analizi)
# ==============================================================================
# Bir olay/tanışma tarihinde dünyanın herhangi bir noktasında hangi gezegenin
# hangi açısal pozisyonda (Yükselen, Alçalan, MC, IC) olduğunu hesaplar.
# Bu, profesyonel astrokartografi yazılımlarının temel mantığıdır.

GEZEGEN_ACG = {
    "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY,
    "Venüs": swe.VENUS, "Mars": swe.MARS, "Jüpiter": swe.JUPITER,
    "Satürn": swe.SATURN, "Uranüs": swe.URANUS, "Neptün": swe.NEPTUNE,
    "Plüton": swe.PLUTO
}

GEZEGEN_ANLAMLARI = {
    "Güneş": {"parlaklik": "Liderlik, otorite, kariyer parlamasi", "para": 15, "prestij": 20, "tutku": 5, "huzur": 0},
    "Ay": {"parlaklik": "Duygusal guvenlik, yuva, annelik", "para": 0, "prestij": 0, "tutku": 5, "huzur": 20},
    "Merkür": {"parlaklik": "Iletisim, ticaret, zekа, esnaflik", "para": 15, "prestij": 5, "tutku": 0, "huzur": 5},
    "Venüs": {"parlaklik": "Ask, guzellik, sanat, lüks, uyum", "para": 10, "prestij": 5, "tutku": 20, "huzur": 15},
    "Mars": {"parlaklik": "Enerji, cesaret, rekabet, tutku", "para": 5, "prestij": 5, "tutku": 20, "huzur": -10},
    "Jüpiter": {"parlaklik": "Bolluk, genisleme, sartinlik, eгitim", "para": 20, "prestij": 15, "tutku": 5, "huzur": 15},
    "Satürn": {"parlaklik": "Disiplin, yapı, sinav, olgunluk", "para": 10, "prestij": 10, "tutku": -5, "huzur": -10},
    "Uranüs": {"parlaklik": "Devrim, ozgurluk, icat, ani degisim", "para": 5, "prestij": 5, "tutku": 10, "huzur": -5},
    "Neptün": {"parlaklik": "Rüya, sanat, spiritüellik, bulaniklik", "para": -5, "prestij": 0, "tutku": 10, "huzur": 15},
    "Plüton": {"parlaklik": "Donusum, guc, derinlik, yikim-yeniden-dogus", "para": 5, "prestij": 10, "tutku": 15, "huzur": -10}
}

def dereceyi_burca_cevir(derece):
    """Dereceyi burç adına çevirir."""
    burclar = ['Koç', 'Boğa', 'İkizler', 'Yengeç', 'Aslan', 'Başak',
               'Terazi', 'Akrep', 'Yay', 'Oğlak', 'Kova', 'Balık']
    return burclar[int(derece / 30) % 12]

def dereceyi_eve_ata(derece, cusps):
    """Derecenin hangi evde olduğunu bulur."""
    for idx in range(12):
        h_start = cusps[idx]
        h_end = cusps[(idx + 1) % 12]
        if h_start < h_end:
            if h_start <= derece < h_end: return idx + 1
        else:
            if derece >= h_start or derece < h_end: return idx + 1
    return 1

# Arap Noktası Sinastri Yorumları (Nokta <-> Nokta)
ARAP_NOKTA_SINASTRI_YORUMLARI = {
    ("Evlilik Noktası", "Evlilik Noktası"): "Kaderin evlilik noktaları çakışması! Her iki ruh da aynı evlilik titresimında titreşiyor. Bu eşleşme, kozmik bir evlilik sözleşmesinin en güçlü göstergesidir. Aynı anda hem çekim hem de uyum yaratır.",
    ("Evlilik Noktası", "Aşk Noktası"): "Evlilik ve aşk noktalarının karmik buluşması! Evlilik sözleşmesi aşk ateşiyle besleniyor. Bu birleşme, hem resmi birlikteliği hem de derin romantizmi vaat eder. Kaderin en tatlı tuzağı.",
    ("Evlilik Noktası", "Tutku Noktası"): "Evlilik ve tutku noktalarının çapraz etkileşimi! Evlilik sözleşmesi cinsel tutkuyla yoğrulmuş. Bu birleşme, hem derin bağlılığı hem de yoğun fiziksel çekimi vaat eder. Ateş ve taşın erimesi.",
    ("Evlilik Noktası", "Ortaklık Noktası"): "Evlilik ve ortaklık noktalarının güçlü ittifakı! Eşit güçte, dengeli ve stratejik bir birliktelik. Her iki ruh da ortak bir vizyon için bir araya gelmiş.",
    ("Evlilik Noktası", "Sadakat Noktası"): "Evlilik ve sadakat noktalarının kutsal sözleşmesi! Uzun vadeli, kalıcı ve güvenilir bir evlilik. Zorlu sınavlar bu birlikteliği sadece daha güçlü yapar.",
    ("Evlilik Noktası", "Cinsellik Noktası"): "Evlilik ve cinsellik noktalarının tutkulu dansı! Fiziksel uyum ve cinsel çekim evlilik sözleşmesini besliyor. Bu birleşme, hem ruhsal hem de bedensel tatmini vaat eder.",
    ("Evlilik Noktası", "Evlilik Mutluluğu"): "Evlilik ve mutluluk noktalarının bolluk bereketi! Evlilikte derin neşe, ruhsal genişleme ve kozmik bolluk. Bu birleşme, cennetin yeryüzündeki yansımasıdır.",
    ("Aşk Noktası", "Tutku Noktası"): "Aşk ve tutku noktalarının ateşi! Duygusal derinlik ve fiziksel çekim mükemmel uyum içinde. Bu birleşme, Romeo ve Juliet'in kozmik versiyonudur.",
    ("Aşk Noktası", "Ortaklık Noktası"): "Aşk ve ortaklık noktalarının dengesi! Romantik aşk, eşit güçte bir ortaklıkla besleniyor. Bu birleşme, hem duygusal hem de pratik tatmini vaat eder.",
    ("Aşk Noktası", "Sadakat Noktası"): "Aşk ve sadakat noktalarının kalıcı bağı! Duygusal aşk, uzun vadeli sadakatla taçlanmış. Bu birleşme, zamana meydan okuyan bir aşk yaratır.",
    ("Aşk Noktası", "Cinsellik Noktası"): "Aşk ve cinsellik noktalarının ruhsal bedeni! Duygusal derinlik ve fiziksel çekim mükemmel bir dans yapıyor. Bu birleşme, ruh-beden birleşmesinin en saf formudur.",
    ("Aşk Noktası", "Evlilik Mutluluğu"): "Aşk ve mutluluk noktalarının neşesi! Romantik aşk, derin mutluluk ve ruhsal genişlemeyle besleniyor. Bu birleşme, cennet bahçesinin kapılarını açar.",
    ("Tutku Noktası", "Ortaklık Noktası"): "Tutku ve ortaklık noktalarının dengesi! Yoğun fiziksel çekim, eşit güçte bir ortaklıkla dengeleniyor. Bu birleşme, hem tutkulu hem de yapısal bir birliktelik yaratır.",
    ("Tutku Noktası", "Sadakat Noktası"): "Tutku ve sadakat noktalarının kalıcı ateşi! Yoğun cinsel çekim, uzun vadeli sadakatla besleniyor. Bu birleşme, zamana meydan okuyan bir tutku yaratır.",
    ("Tutku Noktası", "Cinsellik Noktası"): "Tutku ve cinsellik noktalarının en yoğun birleşmesi! Fiziksel çekim ve cinsel enerji zirve noktasında. Bu birleşme, en yoğun arzu ve en derin tatmini vaat eder.",
    ("Ortaklık Noktası", "Sadakat Noktası"): "Ortaklık ve sadakat noktalarının güvenilir bağı! Eşit güçte, kalıcı ve güvenilir bir birliktelik. Zorlu sınavlar bu birlikteliği sadece daha güçlü yapar.",
    ("Ortaklık Noktası", "Cinsellik Noktası"): "Ortaklık ve cinsellik noktalarının dengeli ateşi! Fiziksel uyum, eşit güçte bir ortaklıkla besleniyor. Bu birleşme, hem tatlı hem de güçlü bir bağ yaratır.",
    ("Sadakat Noktası", "Cinsellik Noktası"): "Sadakat ve cinsellik noktalarının derin bağı! Uzun vadeli bağlılık, fiziksel çekimle taçlanmış. Bu birleşme, hem güvenilir hem de tutkulu bir birliktelik yaratır.",
}

# Arap Noktası <-> Gezegen Sinastri Yorumları
ARAP_NOKTA_GEZEGEN_SINASTRI = {
    # --- EVLILIK NOKTASI ---
    ("Evlilik Noktası", "Güneş"): "Evlilik kaderselliğiniz partnerinizin öz-bilinciyle derin bir uyum içinde. Evlilik, her iki tarafın da en parlak versiyonunu ortaya çıkarır. Kaderin evlilik ateşi yanıyor.",
    ("Evlilik Noktası", "Ay"): "Evlilik kaderselliğiniz partnerinizin duygusal dünyasıyla derin bir uyum içinde. Evlilik, duygusal beslenme ve koruma hissi yaratır. Ruh eşi bağının en saf formu.",
    ("Evlilik Noktası", "Merkür"): "Evlilik kaderselliğiniz partnerinizin iletişim zekasıyla uyum içinde. Evlilik, zihinsel uyum ve planlı birliktelik yaratır. Konuşarak büyüyen bir bağ.",
    ("Evlilik Noktası", "Venüs"): "Evlilik kaderselliğiniz partnerinizin aşk dilinde mükemmel uyum yaratır. Estetik, güzellik ve romantizm bu evliliğin temel direkleri. Kozmik aşk mührü.",
    ("Evlilik Noktası", "Mars"): "Evlilik kaderselliğiniz partnerinizin tutkusuyla derin bir uyum içinde. Fiziksel çekim, eylem ve koruma enerjisi bu evliliği besler. Ateş ve taşın erimesi.",
    ("Evlilik Noktası", "Jüpiter"): "Evlilik kaderselliğiniz partnerinizin bolluk enerjisiyle besleniyor. Evlilikte bereket, genişleme ve ruhsal büyüme. Kaderin en cömert armağanı.",
    ("Evlilik Noktası", "Satürn"): "Evlilik kaderselliğiniz partnerinizin yapısal enerjisiyle derin bir uyum içinde. Evlilik, sorumluluk ve uzun vadeli planlarla beslenir. Zorlu ama kalıcı bir bağ.",
    ("Evlilik Noktası", "Uranüs"): "Evlilik kaderselliğiniz partnerinizin devrimci enerjisiyle çatışma yaratıyor. Sıra dışı, beklenmedik ve sarsıcı bir evlilik. Özgürlük bu bağda kutsaldır.",
    ("Evlilik Noktası", "Neptün"): "Evlilik kaderselliğiniz partnerinizin mistik enerjisiyle yoğrulmuş. Ruh eşi hissi, hayal gücü ve maneviyat bu evliliğin besin kaynağıdır. Sınırlar bu bağda kritikleşir.",
    ("Evlilik Noktası", "Plüton"): "Evlilik kaderselliğiniz partnerinin dönüştürücü gücüyle derin bir uyum içinde. Yoğun güç savaşları, krizler ve ruhsal yeniden doğuş. Bu evlilik ya yıkar ya da yeniden inşa eder.",

    # --- ASK NOKTASI ---
    ("Aşk Noktası", "Güneş"): "Aşk kaderselliğiniz partnerinizin öz-bilinciyle derin bir uyum içinde. Bu aşk, her iki tarafın da en parlak versiyonunu ortaya çıkarır. Kozmik aşk ateşi.",
    ("Aşk Noktası", "Ay"): "Aşk kaderselliğiniz partnerinizin duygusal dünyasıyla mükemmel bir dans yapıyor. Duygusal beslenme, koruma ve ruhsal sığınak bu aşkın temelidir.",
    ("Aşk Noktası", "Merkür"): "Aşk kaderselliğiniz partnerinizin zihinsel dünyasıyla dans ediyor. Kelimeler, fikirler ve zihinsel uyum bu aşkın dilidir. Zekayla büyüyen bir tutku.",
    ("Aşk Noktası", "Venüs"): "Aşk kaderselliğiniz partnerinizin aşk dilinde en saf uyumu yaratır. Estetik, güzellik ve romantizm bu aşkın ruhudur. Kozmik aşk mührü.",
    ("Aşk Noktası", "Mars"): "Aşk kaderselliğiniz partnerinizin tutkusuyla derin bir uyum içinde. Fiziksel çekim, eylem ve koruma enerjisi bu aşkı besler. Ateş ve tutkunun dansı.",
    ("Aşk Noktası", "Jüpiter"): "Aşk kaderselliğiniz partnerinizin bolluk ve genişleme enerjisiyle besleniyor. Bu aşk, umut, neşe ve ruhsal büyüme taşır. Kaderin gülümseyen yüzü.",
    ("Aşk Noktası", "Satürn"): "Aşk kaderselliğiniz partnerinizin yapısal enerjisiyle derin bir uyum içinde. Sabır, disiplin ve uzun vadeli bağlılık bu aşkın iskeletini oluşturur. Zamanla olgunlaşan şarap.",
    ("Aşk Noktası", "Uranüs"): "Aşk kaderselliğiniz partnerinizin devrimci enerjisiyle çatışıyor. Beklenmedik tanışma, sıra dışı çekim ve ani kopuşlar. Bu aşk bir yıldırım gibi çakar.",
    ("Aşk Noktası", "Neptün"): "Aşk kaderselliğiniz partnerinizin mistik enerjisiyle yoğrulmuş. Maneviyat, hayal gücü ve koşulsuz sevgi bu aşkın besin kaynağıdır. Hayal kırıklığı riski yüksek ama ödülü de öyle.",
    ("Aşk Noktası", "Plüton"): "Aşk kaderselliğiniz partnerinizin dönüştürücü gücüyle derin bir uyum içinde. Bu aşk sizi her yönünüzden değiştirir. Yoğunluk, tutku ve ruhsal yeniden doğum.",

    # --- TUTKU NOKTASI ---
    ("Tutku Noktası", "Güneş"): "Tutku kaderselliğiniz partnerinizin öz-gücüyle besleniyor. Bu tutku, egonun dansı, iki Güneş'in bir araya gelişi. Parıltılı ama dengeli bir ateş gerekir.",
    ("Tutku Noktası", "Ay"): "Tutku kaderselliğiniz partnerinizin duygusal derinliğiyle besleniyor. Arzu ve duygusal beslenme iç içe. Bu tutku, ruhsal kucaklama ile fiziksel arzunun erimesi.",
    ("Tutku Noktası", "Merkür"): "Tutku kaderselliğiniz partnerinizin zihinsel çevikliğiyle besleniyor. Zihinsel oyunlar, flört ve entelektüel çekim bu tutkunun motoru. Kelimelerle tahrik eden bir bağ.",
    ("Tutku Noktası", "Mars"): "Tutku kaderselliğiniz partnerinizin eylemsel enerjisiyle mükemmel bir uyum içinde. Fiziksel çekim, cesaret ve koruma enerjisi bu tutkuyu besler. En yoğun arzu mührü.",
    ("Tutku Noktası", "Venüs"): "Tutku kaderselliğiniz partnerinizin aşk dilinde derin bir uyum yaratır. Fiziksel çekim ve duygusal derinlik bu tutkunun temel direkleridir.",
    ("Tutku Noktası", "Jüpiter"): "Tutku kaderselliğiniz partnerinizin bolluk enerjisiyle besleniyor. Tutkunun genişlemesi, coşku ve cömertlik. Bu tutku sınır tanımaz.",
    ("Tutku Noktası", "Satürn"): "Tutku kaderselliğiniz partnerinizin yapısal enerjisiyle derin bir uyum içinde. Tutkunun kontrolü, disiplin ve derinleşme. Kısıtlı gibi görünse de en derin tatmin burada.",
    ("Tutku Noktası", "Plüton"): "Tutku kaderselliğiniz partnerinizin dönüştürücü gücüyle derin bir uyum içinde. Yoğun güç savaşları, cinsel derinlik ve ruhsal yeniden doğuş. Bu tutku ya yıkar ya da yeniden inşa eder.",

    # --- ORTAKLIK NOKTASI ---
    ("Ortaklık Noktası", "Güneş"): "Ortaklık kaderselliğiniz partnerinizin öz-bilinciyle uyum içinde. Birlikte parlayan, birbirinin güçlü yönlerini ortaya çıkaran kozmik bir işbirliği.",
    ("Ortaklık Noktası", "Ay"): "Ortaklık kaderselliğiniz partnerinizin duygusal dünyasıyla uyum içinde. Duygusal beslenme, koruma ve ev ortamında huzur bu birliğin temel taşları.",
    ("Ortaklık Noktası", "Merkür"): "Ortaklık kaderselliğiniz partnerinizin iletişim zekasıyla uyum içinde. Planlama, sözleşme ve zihinsel uyum bu işbirliğinin motoru.",
    ("Ortaklık Noktası", "Venüs"): "Ortaklık kaderselliğiniz partnerinizin estetik ve sevgi diliyle uyum içinde. Güzel olanı birlikte yaratma, sanatsal uyum ve romantik denge.",
    ("Ortaklık Noktası", "Mars"): "Ortaklık kaderselliğiniz partnerinizin eylem enerjisiyle uyum içinde. Birlikte savaşan, birlikte büyüyen aktif ve yapi bir ortaklık.",
    ("Ortaklık Noktası", "Jüpiter"): "Ortaklık kaderselliğiniz partnerinizin bolluk enerjisiyle besleniyor. Birlikte genişleme, öğrenme ve ruhsal büyüme. Kaderin en bereketli işbirliği.",
    ("Ortaklık Noktası", "Satürn"): "Ortaklık kaderselliğiniz partnerinizin yapısal enerjisiyle uyum içinde. Uzun vadeli planlar, sorumluluk paylaşımı ve kalıcı yapılar. Zorlu ama ölümsüz bir ortaklık.",
    ("Ortaklık Noktası", "Uranüs"): "Ortaklık kaderselliğiniz partnerinizin devrimci enerjisiyle beklenmedik bir şekilde şekilleniyor. Sıra dışı, özgürlükçü ve yenilikçi bir işbirliği. Bağlılık ama bağımsızlık da şart.",
    ("Ortaklık Noktası", "Neptün"): "Ortaklık kaderselliğiniz partnerinizin manevi enerjisiyle yoğrulmuş. Maneviyat, sanat ve koşulsuz hizmet bu birliğin besin kaynağı. Sınırlar belirsizleşebilir.",
    ("Ortaklık Noktası", "Plüton"): "Ortaklık kaderselliğiniz partnerinizin dönüştürücü gücüyle derin bir uyum içinde. Bu ortaklık sizi her yönünüzden değiştirir. Güç, denge ve yeniden doğum.",

    # --- SADAKAT NOKTASI ---
    ("Sadakat Noktası", "Güneş"): "Sadakat kaderselliğiniz partnerinizin öz-bilinciyle uyum içinde. Güneş gibi parlak ve gözükmeyen bir sadakat. İkisinin de aynı yöne bakması kaderin hediyesi.",
    ("Sadakat Noktası", "Ay"): "Sadakat kaderselliğiniz partnerinizin duygusal dünyasıyla uyum içinde. Duygusal beslenme ve koruma hissi bu sadakatın temelidir. Ay gibi döngüsel ama sarsılmaz bir bağlılık.",
    ("Sadakat Noktası", "Merkür"): "Sadakat kaderselliğiniz partnerinizin iletişim zekasıyla uyum içinde. Zihinsel uyum ve sözlerin gücü bu sadakatı besler. Konuşarak büyüyen güven.",
    ("Sadakat Noktası", "Venüs"): "Sadakat kaderselliğiniz partnerinizin aşk dilinde derin bir uyum yaratır. Duygusal bağlılık, estetik ve romantizm bu sadakatın temelidir.",
    ("Sadakat Noktası", "Mars"): "Sadakat kaderselliğiniz partnerinizin eylem enerjisiyle uyum içinde. Aktif koruma, cesaret ve fedakarlık. Bu sadakat için savaşır, bu sadakat için yaşar.",
    ("Sadakat Noktası", "Jüpiter"): "Sadakat kaderselliğiniz partnerinizin bolluk enerjisiyle besleniyor. Genişleyen güven, derinleşen bağlılık ve ruhsal sadakat. Kaderin en cömert yemini.",
    ("Sadakat Noktası", "Satürn"): "Sadakat kaderselliğiniz partnerinizin yapısal enerjisiyle mükemmel bir uyum içinde. Uzun vadeli, kalıcı ve güvenilir bir bağ. Zorlu sınavlar bu birlikteliği sadece daha güçlü yapar.",
    ("Sadakat Noktası", "Uranüs"): "Sadakat kaderselliğiniz partnerinizin devrimci enerjisiyle çatışıyor. Özgürlük arzusu ve bağlılık arasındaki gerilim. Sıra dışı sadakat formatları.",
    ("Sadakat Noktası", "Neptün"): "Sadakat kaderselliğiniz partnerinizin manevi enerjisiyle yoğrulmuş. Manevi sadakat, koşulsuz sevgi ve ruhsal bağlılık. Fiziksel sınırların ötesinde bir yemin.",
    ("Sadakat Noktası", "Plüton"): "Sadakat kaderselliğiniz partnerinizin dönüştürücü gücüyle derin bir uyum içinde. Mutlak sadakat, yoğunluk ve ruhsal yeniden doğum. Bu bağlılık ne ölü ne de ölümsüz.",

    # --- CINSELLIK NOKTASI ---
    ("Cinsellik Noktası", "Güneş"): "Cinsel çekim kaderselliğiniz partnerinizin öz-gücüyle besleniyor. Öz-bilinç ve arzu iç içe. Bu cinsellikte ego dansı ve karşılıklı tapınma var.",
    ("Cinsellik Noktası", "Ay"): "Cinsel çekim kaderselliğiniz partnerinizin duygusal derinliğiyle besleniyor. Duygusal beslenme ve fiziksel arzu iç içe. Ay ışığında büyüyen bir cinsellik.",
    ("Cinsellik Noktası", "Merkür"): "Cinsel çekim kaderselliğiniz partnerinizin zihinsel çevikliğiyle besleniyor. Zihinsel oyunlar, fısıltı ve entelektüel çekim bu cinselliğin motoru. Kelimelerle tahrik eden bir bağ.",
    ("Cinsellik Noktası", "Mars"): "Cinsel çekim kaderselliğiniz partnerinizin eylemsel enerjisiyle mükemmel bir uyum içinde. Fiziksel çekim, cesaret ve koruma enerjisi bu cinselliği besler. En yoğun arzu mührü.",
    ("Cinsellik Noktası", "Venüs"): "Cinsel çekim kaderselliğiniz partnerinizin aşk dilinde derin bir uyum yaratır. Fiziksel çekim ve duygusal derinlik bu cinselliğin temel direkleridir.",
    ("Cinsellik Noktası", "Jüpiter"): "Cinsel çekim kaderselliğiniz partnerinizin bolluk enerjisiyle besleniyor. Cinsel tatmin, bolluk ve neşe. Bu cinsellikte coşku ve cömertlik var.",
    ("Cinsellik Noktası", "Satürn"): "Cinsel çekim kaderselliğiniz partnerinizin yapısal enerjisiyle derin bir uyum içinde. Cinsel disiplin, derinleşme ve kontrol. Kısıtlı gibi görünse de en derin tatmin burada.",
    ("Cinsellik Noktası", "Uranüs"): "Cinsel çekim kaderselliğiniz partnerinizin devrimci enerjisiyle çatışıyor. Sıra dışı cinsellik, beklenmedik arzu ve ani kopuşlar. Bu cinsellik bir yıldırım gibi çakar.",
    ("Cinsellik Noktası", "Neptün"): "Cinsel çekim kaderselliğiniz partnerinizin mistik enerjisiyle yoğrulmuş. Maneviyat, hayal gücü ve koşulsuz sevgi bu cinselliğin besin kaynağıdır. Sınırsız ama dikkatli olmalı.",
    ("Cinsellik Noktası", "Plüton"): "Cinsel çekim kaderselliğiniz partnerinizin dönüştürücü gücüyle derin bir uyum içinde. Yoğun güç savaşları, cinsel derinlik ve ruhsal yeniden doğuş.",

    # --- EVLILIK MUTLULUGU ---
    ("Evlilik Mutluluğu", "Güneş"): "Evlilik mutluluğu kaderselliğiniz partnerinizin öz-bilinciyle uyum içinde. Birlikte parlayan, neşe ve gurur dolu bir evlilik. Kaderin gülümseyen yüzü.",
    ("Evlilik Mutluluğu", "Ay"): "Evlilik mutluluğu kaderselliğiniz partnerinizin duygusal dünyasıyla uyum içinde. Duygusal beslenme, koruma ve ev ortamında huzur bu mutluluğun temel taşları.",
    ("Evlilik Mutluluğu", "Merkür"): "Evlilik mutluluğu kaderselliğiniz partnerinizin iletişim zekasıyla uyum içinde. Konuşarak büyüyen, plan yapan ve birlikte öğrenen bir evlilik.",
    ("Evlilik Mutluluğu", "Venüs"): "Evlilik mutluluğu kaderselliğiniz partnerinizin aşk dilinde mükemmel uyum yaratır. Estetik, güzellik ve romantizm bu mutluluğun temel direkleri.",
    ("Evlilik Mutluluğu", "Mars"): "Evlilik mutluluğu kaderselliğiniz partnerinizin eylem enerjisiyle uyum içinde. Aktif, yapi ve tutkulu bir evlilik. Birlikte savaşan, birlikte gülen bir duo.",
    ("Evlilik Mutluluğu", "Satürn"): "Evlilik mutluluğu kaderselliğiniz partnerinizin yapısal enerjisiyle uyum içinde. Uzun vadeli planlar ve sorumluluk paylaşımı bu mutluluğun iskeletini oluşturur.",
    ("Evlilik Mutluluğu", "Uranüs"): "Evlilik mutluluğu kaderselliğiniz partnerinizin devrimci enerjisiyle beklenmedik bir şekilde şekilleniyor. Sıra dışı evlilik formatları, özgürlük ve yenilik.",
    ("Evlilik Mutluluğu", "Neptün"): "Evlilik mutluluğu kaderselliğiniz partnerinizin manevi enerjisiyle yoğrulmuş. Maneviyat, sanat ve koşulsuz hizmet bu mutluluğun besin kaynağı.",
    ("Evlilik Mutluluğu", "Plüton"): "Evlilik mutluluğu kaderselliğiniz partnerinizin dönüştürücü gücüyle derin bir uyum içinde. Bu evlilik sizi her yönünüzden değiştirir. Yoğunluk ve yeniden doğum.",

    # --- BOS (BOSANMA) NOKTASI ---
    ("Boş Noktası", "Güneş"): "Ayrılık enerjisi partnerinizin öz-bilinciyle çatışıyor. Ego çatışmaları ve özgürlük talepleri bu noktayı aktive eder. Ayrılık ya da öz-benliğin yeniden doğuşu.",
    ("Boş Noktası", "Ay"): "Ayrılık enerjisi partnerinizin duygusal dünyasıyla çatışıyor. Duygusal kopuş, beslenme eksikliği ve güvensizlik bu noktayı tetikler.",
    ("Boş Noktası", "Merkür"): "Ayrılık enerjisi partnerinizin iletişim tarzıyla çatışıyor. Yanlış anlama, iletişim kopukluğu ve zihinsel ayrışma.",
    ("Boş Noktası", "Venüs"): "Ayrılık enerjisi partnerinizin aşk diliyle çatışıyor. Değer farkları, estetik ayrışma ve romantik hayal kırıklığı.",
    ("Boş Noktası", "Mars"): "Ayrılık enerjisi partnerinizin eylem tarzıyla çatışıyor. Öfke, saldırganlık ve fiziksel ayrışma. Dikkatli olunması gereken bir enerji.",
    ("Boş Noktası", "Jüpiter"): "Ayrılık enerjisi partnerinizin bolluk anlayışıyla çatışıyor. Farklı inançlar, genişleme yolları ve ruhsal ayrışma.",
    ("Boş Noktası", "Satürn"): "Ayrılık enerjisi partnerinizin yapısal enerjisiyle çatışıyor. Sorumluluk yükleri, disiplin farkları ve uzun vadeliPlan çatışmaları.",
    ("Boş Noktası", "Uranüs"): "Ayrılık enerjisi partnerinizin devrimci enerjisiyle uyumsuzluk yaratıyor. Ani kopuşlar, beklenmedik ayrılıklar ve özgürlük krizleri.",
    ("Boş Noktası", "Neptün"): "Ayrılık enerjisi partnerinizin manevi enerjisiyle çatışıyor. Hayal kırıklığı, aldanma ve manevi kopuş.",
    ("Boş Noktası", "Plüton"): "Ayrılık enerjisi partnerinizin dönüştürücü gücüyle çatışıyor. Yoğun güç savaşları, kıskançlık ve zorunlu yeniden doğum.",
}

def acg_pozisyon_hesapla(jd, enlem, boylam):
    """
    Belirli bir Julian Day'de ve koordinatlarda gezegenlerin açısal pozisyonlarını hesaplar.
    Returns: dict of {gezegen_adi: {"ac": derece, "dc": derece, "mc": derece, "ic": derece, "burc": str}}
    """
    sonuclar = {}
    try:
        evre, ascs = swe.houses(jd, enlem, boylam, b'P')  # Placidus ev sistemi
        mc_derece = ascs[1]  # MC (Midheaven)
        ac_derece = ascs[0]  # AC (Ascendant)
    except Exception:
        return sonuclar

    for gezegen_adi, gezegen_id in GEZEGEN_ACG.items():
        try:
            konum = swe.calc_ut(jd, gezegen_id)
            gezegen_lon = konum[0][0]

            ac_fark = aci_farki_safe(gezegen_lon, ac_derece)
            mc_fark = aci_farki_safe(gezegen_lon, mc_derece)
            dc_fark = aci_farki_safe(gezegen_lon, (ac_derece + 180) % 360)
            ic_fark = aci_farki_safe(gezegen_lon, (mc_derece + 180) % 360)

            en_yakin_aci = min([
                ("AC", ac_fark), ("MC", mc_fark), ("DC", dc_fark), ("IC", ic_fark)
            ], key=lambda x: x[1])

            sonuclar[gezegen_adi] = {
                "lon": gezegen_lon,
                "en_yakin_aci": en_yakin_aci[0],
                "aci_farki": en_yakin_aci[1],
                "ac_orb": ac_fark, "mc_orb": mc_fark, "dc_orb": dc_fark, "ic_orb": ic_fark,
                "burc": dereceden_burc_dec(gezegen_lon)
            }
        except Exception:
            continue

    return sonuclar

def astro_kartografi_skor(jd, enlem, boylam):
    """
    Belirli bir koordinat için astrokartografi skoru hesaplar.
    Yakın zamandaki gezegenlerin açısal pozisyonlarına göre puan verir.
    """
    acg = acg_pozisyon_hesapla(jd, enlem, boylam)
    
    huzur, para, tutku, kriz = 50.0, 50.0, 50.0, 50.0
    etkiler = []
    orb_siniri = 5.0  # 5 derece yakınlık sınırı

    for gezegen_adi, veri in acg.items():
        fark = veri["aci_farki"]
        if fark > orb_siniri:
            continue

        aci = veri["en_yakin_aci"]
        deger = GEZEGEN_ANLAMLARI.get(gezegen_adi, {})
        
        # Yakınlık çarpımı: 0° = %100, 5° = %0
        carpan = max(0, 1.0 - (fark / orb_siniri))
        
        if aci == "AC":
            carpan *= 1.2  # Yükselen en güçlü etki
        elif aci == "MC":
            carpan *= 1.0
        elif aci == "DC":
            carpan *= 0.8
        elif aci == "IC":
            carpan *= 0.6

        para += deger.get("para", 0) * carpan
        tutku += deger.get("tutku", 0) * carpan
        huzur += deger.get("huzur", 0) * carpan
        kriz -= deger.get("huzur", 0) * carpan * 0.5

        aci_simge = {"AC": "↑ Yükselen", "DC": "↓ Alçalan", "MC": "⌃ MC", "IC": "⌄ IC"}
        etkiler.append(f"{gezegen_adi} {aci_simge.get(aci, aci)} ({fark:.1f}°) → {deger['parlaklik']}")

    # Satürn Plüto yakınlığı kriz skorunu artırır
    if "Satürn" in acg and "Plüton" in acg:
        sat_plu_fark = aci_farki_safe(acg["Satürn"]["lon"], acg["Plüton"]["lon"])
        if sat_plu_fark < 10:
            kriz += 20 * (1 - sat_plu_fark / 10)
            etkiler.append(f"⚠️ Satürn-Plüto kavuşumu ({sat_plu_fark:.1f}°) → Yapısal kriz potansiyeli")

    huzur = min(99, max(5, huzur))
    para = min(99, max(5, para))
    tutku = min(99, max(5, tutku))
    kriz = min(99, max(5, kriz))

    return {
        "huzur": round(huzur, 1), "para": round(para, 1),
        "tutku": round(tutku, 1), "kriz": round(kriz, 1),
        "etkiler": etkiler, "acg": acg
    }

@st.cache_data
def kadersel_radar_analizi(p1_str, p2_str, event_date_str, event_time, p1_isim, p2_isim):
    """Astrokartografi tabanlı küresel lokasyon taraması."""
    tarih = datetime.strptime(f"{event_date_str} {event_time}", "%Y-%m-%d %H:%M")
    jd_event = swe.julday(tarih.year, tarih.month, tarih.day, tarih.hour + tarih.minute / 60.0)

    global_yerler_db = sehir_veritabani_yukle()

    radar_sonuclari = []
    toplam_sehir = sum(len(s) for s in global_yerler_db.values())

    def _tek_sehir_hesapla(ulke, sehir, lat, lon):
        skor = astro_kartografi_skor(jd_event, lat, lon)
        return {
            "sehir": f"{sehir}, {ulke}",
            "lat": lat, "lon": lon,
            "huzur": skor["huzur"], "para": skor["para"],
            "tutku": skor["tutku"], "kriz": skor["kriz"],
            "etkiler": skor["etkiler"]
        }

    is_listesi = []
    for ulke, sehirler in global_yerler_db.items():
        for sehir, koordinat in sehirler.items():
            if isinstance(koordinat, dict):
                lat, lon = koordinat["lat"], koordinat["lon"]
            else:
                lat, lon = koordinat
            is_listesi.append((ulke, sehir, lat, lon))

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_tek_sehir_hesapla, u, s, la, lo): (u, s) for u, s, la, lo in is_listesi}
        for future in as_completed(futures):
            radar_sonuclari.append(future.result())

    return radar_sonuclari

def _son_pazar_gunu(yil, ay):
    """Verilen ayın son Pazar gününün gün numarasını döndürür."""
    import calendar
    # Ayın son gününü bul
    son_gun = calendar.monthrange(yil, ay)[1]
    # O günden geriye doğru tarayarak Pazar'ı bul (Pazar=6, Pazartesi=0)
    for gun in range(son_gun, 0, -1):
        from datetime import date
        if date(yil, ay, gun).weekday() == 6:  # Pazar
            return gun
    return son_gun  # Fallback

class FBST_Engine:

    
    def __init__(self, p1, p2, event_date, event_time="12:00", city="Ankara", country="Türkiye", lat=39.9334, lon=32.8597, p1_isim="", p2_isim="", mod="es_sevgili", ebeveyn_rolu="anne", utc_offset=None):
        
        self._session_id = uuid.uuid4().hex[:12]
        self.mod = mod
        self.ebeveyn_rolu = ebeveyn_rolu
        
        # 1. Metinleri tarihe çevir
        t1 = datetime.strptime(p1, "%Y-%m-%d")
        t2 = datetime.strptime(p2, "%Y-%m-%d")
        
        # 2. MUTLAK ZAMAN AYRIŞTIRMASI
        if t1 < t2:
            tarih_eski = t1  # Örn: 1986 (Doğum tarihi küçük / Yaşça büyük)
            isim_eski = p1_isim
            
            tarih_yeni = t2  # Örn: 1988 (Doğum tarihi büyük / Yaşça küçük)
            isim_yeni = p2_isim
        else:
            tarih_eski = t2  
            isim_eski = p2_isim
            
            tarih_yeni = t1  
            isim_yeni = p1_isim
        
        # 3. KESİN ÇÖZÜM: PDF'E GÖRE TERS ATAMA!
        # PDF motorun p1'i "M.S.", p2'yi "M.Ö." olarak ekrana basıyor.
        # Bu yüzden p1'e YENİ (1988) tarihi, p2'ye ESKİ (1986) tarihi veriyoruz.
        
        self.p1 = tarih_yeni   
        self.p1_isim = isim_yeni if isim_yeni else ("Çocuk" if self.mod == "ebeveyn_cocuk" else "Situa M.S.")
        
        self.p2 = tarih_eski   
        if self.mod == "bireysel_natal":
            self.p2_isim = ""
        else:
            self.p2_isim = isim_eski if isim_eski else ("Ebeveyn" if self.mod == "ebeveyn_cocuk" else "Situa M.Ö.")
        
        # 4. Geri Kalan Rutin Bilgiler
        self.event_date_str = event_date
        self.event_time_str = event_time
        self.event_date = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
        
        self.city = city
        self.country = country
        self.enlem = float(lat)
        self.boylam = float(lon)
        
        saat_dakika = event_time.split(":")
        self.saat_ondalik = int(saat_dakika[0]) + int(saat_dakika[1]) / 60.0
        
        # Gün farkı her ihtimale karşı mutlak değerde (abs)
        self.gun_farki = abs((self.p2 - self.p1).days)
        
        self.utc_offset = utc_offset

    @staticmethod
    def turkiye_utc_offset(yil, ay, gun):
        """
        Türkiye için tarihe göre doğru UTC offset'ini döndürür.
        - 2016 sonrası: UTC+3 (kalıcı yaz saati, DST yok)
        - 1985-2016 arası: UTC+3 (yaz) / UTC+2 (kış) — DST uygulanır
        - 1968-1985 arası: UTC+3 (yaz) / UTC+2 (kış) — DST uygulanır
        - 1968 öncesi: UTC+2 (sabit, DST yok)
        
        DST kuralları (uygulandığında):
        - Başlangıç: Mart ayının son Pazar günü (saatler 03:00'te 04:00'e geçer)
        - Bitiş: Eylül ayının son Pazar günü (saatler 04:00'te 03:00'e geri döner)
        
        NOT: Türkiye 2016'dan önce DST'yi eylül ayının sonunda bitiriyordu,
        ekim ayı zaten kış saati (UTC+2) dönemine giriyordu.
        """
        # 2016 sonrası: kalıcı UTC+3
        if yil > 2016:
            return 3
        
        # 1968 öncesi: sabit UTC+2
        if yil < 1968:
            return 2
        
        # 1968-2016 arası: DST uygulanır
        # Yaz saati başlangıcı: Mart ayının son Pazar günü
        # Yaz saati bitişi: Eylül ayının son Pazar günü (EKIM DEĞİL!)
        mart_son_pazar = _son_pazar_gunu(yil, 3)
        eylul_son_pazar = _son_pazar_gunu(yil, 9)
        
        # Yaz saati döneminde miyiz? (Mart son Pazar - Eylül son Pazar arası)
        if (ay > 3) or (ay == 3 and gun >= mart_son_pazar):
            if (ay < 9) or (ay == 9 and gun <= eylul_son_pazar):
                return 3  # Yaz saati (UTC+3)
        
        return 2  # Kış saati (UTC+2)

    def _get_utc_offset(self, yil, ay, gun):
        if self.utc_offset is not None:
            return self.utc_offset
        return otomatik_utc_offset(self.enlem, self.boylam, yil, ay, gun, int(self.saat_ondalik))

    def get_julian_dates(self):
        if hasattr(self, '_j_ileri'):
            return self._j_ileri, self._j_geri
        import swisseph as swe
        
        lmt_farki = self.boylam / 15.0
        utc_saat = self.saat_ondalik - lmt_farki
        
        jd_milat = swe.julday(1, 1, 1, utc_saat, swe.JUL_CAL)
        
        self._j_ileri = jd_milat + self.gun_farki
        self._j_geri  = jd_milat - self.gun_farki
        
        return self._j_ileri, self._j_geri
    
    def get_natal_julian_day(self, which="p1"):
        """
        Gerçek natal harita Julian günü — bağıl/Milat hesabı yok.
        which="p1" için self.p1, which="p2" için self.p2 kullanılır.
        """
        if which == "p1":
            d1 = self.p1
            tarih = d1 if isinstance(d1, date) else datetime.strptime(str(d1), "%Y-%m-%d").date()
        else:
            d1 = self.p2
            tarih = d1 if isinstance(d1, date) else datetime.strptime(str(d1), "%Y-%m-%d").date()
        uo = self._get_utc_offset(tarih.year, tarih.month, tarih.day)
        dogum_saat_utc = self.saat_ondalik - uo
        return swe.julday(tarih.year, tarih.month, tarih.day, dogum_saat_utc)

    def calculate_ks(self): 
        return self.gun_farki / 365.25

    def get_bagil_position(self, gezegen_adi, vektor):
        """Bağıl haritalar (Situa A/B) için gezegen pozisyonunu döndürür."""
        j_ileri, j_geri = self.get_julian_dates()
        jd = j_ileri if vektor == "ileri" else j_geri
        
        if gezegen_adi == "GAD":
            k_derece = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
            return (k_derece + 180.0) % 360.0
        
        gid = GEZEGENLER.get(gezegen_adi)
        if gid is not None:
            flags = get_safe_flags(gid)
            return swe.calc_ut(jd, gid, flags)[0][0]
        return None

    def zaman_vektoru_duzelt(self, tarih_a, tarih_b):
        """
        Doğum tarihlerini mutlak bir zaman doğrusuna yerleştirir.
        Küçük olan tarih (yaşı büyük olan) -> M.Ö. (situa_a)
        Büyük olan tarih (yaşı küçük olan) -> M.S. (situa_b)
        """
        # Python'da eski tarihler (<) yeni tarihlerden küçüktür.
        if tarih_a < tarih_b:
            situa_m_o = tarih_a  # Eski olan
            situa_m_s = tarih_b  # Yeni olan
        else:
            situa_m_o = tarih_b  # Eski olan
            situa_m_s = tarih_a  # Yeni olan
            
        return situa_m_o, situa_m_s


    # =====================================================================
    # SABIT YILDIZLAR ve MC ANALİZİ
    # =====================================================================

    SABIT_YILDIZLAR = {
        "Regulus": {"derece": 149.882, "kaynak": "Aslan"},
        "Spica": {"derece": 200.941, "kaynak": "Terazi"},
        "Vega": {"derece": 281.531, "kaynak": "Oğlak"},
        "Algol": {"derece": 261.593, "kaynak": "Boğa"},
        "Arcturus": {"derece": 198.960, "kaynak": "Terazi"},
        "Sirius": {"derece": 104.657, "kaynak": "Yengeç"},
        "Capella": {"derece": 280.994, "kaynak": "Oğlak"},
        "Rigel": {"derece": 208.399, "kaynak": "Terazi"},
        "Antares": {"derece": 248.970, "kaynak": "Akrep"},
        "Fomalhaut": {"derece": 339.560, "kaynak": "Balık"},
        "Aldebaran": {"derece": 69.478, "kaynak": "İkizler"},
        "Betelgeuse": {"derece": 274.833, "kaynak": "Oğlak"},
        "Castor": {"derece": 113.645, "kaynak": "Yengeç"},
        "Pollux": {"derece": 116.114, "kaynak": "Yengeç"},
        "Procyon": {"derece": 104.364, "kaynak": "Yengeç"},
        "Altair": {"derece": 297.695, "kaynak": "Oğlak"},
        "Deneb": {"derece": 49.624, "kaynak": "Koç"},
        "Bellatrix": {"derece": 205.863, "kaynak": "Terazi"},
        "Polaris": {"derece": 43.576, "kaynak": "Koç"},
        "Alcyone": {"derece": 58.056, "kaynak": "Boğa"},
        "Mira": {"derece": 53.565, "kaynak": "Boğa"},
        "Zubenelgenubi": {"derece": 209.061, "kaynak": "Terazi"},
        "Zubenelchemali": {"derece": 215.295, "kaynak": "Akrep"},
        "Scheat": {"derece": 14.470, "kaynak": "Koç"},
        "Markab": {"derece": 15.163, "kaynak": "Koç"},
        "Alphard": {"derece": 153.629, "kaynak": "Aslan"},
        "Dubhe": {"derece": 143.580, "kaynak": "Aslan"},
        "Merak": {"derece": 133.250, "kaynak": "Aslan"},
        "Phecda": {"derece": 142.560, "kaynak": "Aslan"},
        "Megrez": {"derece": 144.130, "kaynak": "Aslan"},
        "Alioth": {"derece": 154.940, "kaynak": "Başak"},
        "Mizar": {"derece": 159.550, "kaynak": "Başak"},
        "Alkaid": {"derece": 165.760, "kaynak": "Başak"},
    }

    # Sabit yıldız → meslek kategorisi eşleme (astrolojik anlamlar)
    # Bilgelik: bilimsel araştırma, analitik düşünce, akademik uzmanlık, psikoloji, felsefe
    # Maneviyat: ruhsallık, iyileştirme, metafizik, spiritüel rehberlik, sezgisel bilgelik
    SABIT_YILDIZ_MESLEK_MAP = {
        # ── KOÇ VE BOĞA BÖLGESİ ──
        "Regulus": { "Liderlik": 5, "Zihinsel Yetenek": 2 },
        "Spica": { "Sanatsal Yetenek": 5, "Bilgelik": 2 },
        "Arcturus": { "Liderlik": 4 },
        "Alpheratz": {"Sanatsal Yetenek": 4, "İletişim": 3},
        "Mirach": {"Sanatsal Yetenek": 5, "Maneviyat": 2},
        "Algol": { "Zihinsel Yetenek": 5 },
        "Alcyone": { "Sanatsal Yetenek": 4, "Bilgelik": 3 },
        "Mira": { "Zihinsel Yetenek": 4, "Zanaatkarlık": 3 },
        "Facies": { "Zihinsel Yetenek": 5, "Zanaatkarlık": 2 },
        "Alphard": { "Sağlık/Tıp": 5, "Zihinsel Yetenek": 4, "Maneviyat": 3 },
        "Hamal": { "Spor": 4, "Liderlik": 3 },
        "Kerb": { "Spor": 6, "Liderlik": 3 },
        "Sheratan": { "Zihinsel Yetenek": 4 },
        # ── İKİZLER VE YENGEÇ BÖLGESİ ──
        "Aldebaran": { "Liderlik": 5, "Zihinsel Yetenek": 3 },
        "Rigel": { "Bilgelik": 5, "Zihinsel Yetenek": 3 },
        "Bellatrix": { "Zihinsel Yetenek": 5, "Liderlik": 3 },
        "Capella": { "Bilgelik": 5, "İletişim": 3 },
        "Betelgeuse": { "Liderlik": 5, "Sanatsal Yetenek": 3 },
        "Sirius": { "Liderlik": 5, "Sanatsal Yetenek": 3 },
        "Menkar": {"İletişim": 4, "Yardımseverlik": 3},
        "Praesepe": { "Liderlik": 4, "Yardımseverlik": 3 },
        "Canopus": { "Bilgelik": 5, "Zihinsel Yetenek": 4 },
        "Enif": {"Sanatsal Yetenek": 4, "İletişim": 3},
        # ── ASLAN VE BAŞAK BÖLGESİ ──
        "Castor": { "İletişim": 5, "Zihinsel Yetenek": 3 },
        "Pollux": { "Spor": 5, "Zihinsel Yetenek": 3 },
        "Procyon": { "Sağlık/Tıp": 4, "Liderlik": 4, "Spor": 3 },
        "Zosma": {"Sağlık/Tıp": 5, "Yardımseverlik": 4, "Maneviyat": 3},
        "Denebola": { "Zihinsel Yetenek": 4, "Bilgelik": 3 },
        "Vindemiatrix": { "Sağlık/Tıp": 4, "Zanaatkarlık": 4, "Bilgelik": 3 },
        "Porrima": { "İletişim": 4, "Zihinsel Yetenek": 3 },
        # ── TERAZİ VE AKREP BÖLGESİ ──
        "Vega": {"Sanatsal Yetenek": 5, "İletişim": 3},
        "Zubenelgenubi": { "Yardımseverlik": 5, "Zihinsel Yetenek": 2 },
        "Zubenelchemali": { "Yardımseverlik": 4, "Liderlik": 3 },
        "Alphecca": {"Sanatsal Yetenek": 4, "Maneviyat": 3, "İletişim": 2},
        "Unukalhai": { "Zihinsel Yetenek": 4, "Yardımseverlik": 3 },
        "Sabik": { "Zihinsel Yetenek": 4, "Yardımseverlik": 3 },
        "Dabih": { "Zihinsel Yetenek": 4, "Maneviyat": 3 },
        # ── YAY VE OĞLAK BÖLGESİ ──
        "Antares": { "Zihinsel Yetenek": 5, "Liderlik": 4 },
        "Ras Alhague": {"Yardımseverlik": 4, "Maneviyat": 3},
        "Altair": { "Liderlik": 5 },
        "Deneb": { "Sanatsal Yetenek": 5, "Maneviyat": 3, "Bilgelik": 2 },
        "Alnilam": { "İletişim": 4, "Liderlik": 3 },
        "Alnitak": { "İletişim": 4, "Zihinsel Yetenek": 3 },
        "Terebellum": { "Liderlik": 4, "Zihinsel Yetenek": 3 },
        "Rukbat": { "Zanaatkarlık": 4, "Bilgelik": 3 },
        "Nashira": { "Zihinsel Yetenek": 4, "Bilgelik": 3 },
        "Zavijava": { "Zihinsel Yetenek": 4, "Zanaatkarlık": 3 },
        # ── KOVA VE BALIK BÖLGESİ ──
        "Fomalhaut": {"Maneviyat": 5, "Sanatsal Yetenek": 4},
        "Scheat": { "Zihinsel Yetenek": 4, "Zanaatkarlık": 3 },
        "Markab": { "Bilgelik": 4, "İletişim": 3 },
        "Deneb Algedi": { "Zihinsel Yetenek": 4, "Liderlik": 3 },
        "Achernar": { "Maneviyat": 4, "Bilgelik": 3 },
        "Sadalmelik": { "Zihinsel Yetenek": 5, "Bilgelik": 3 },
        "Sadalsuud": { "Zihinsel Yetenek": 5, "Bilgelik": 3 },
        "Skat": { "Zihinsel Yetenek": 4, "Maneviyat": 3 },
        "Polaris": { "Bilgelik": 5, "Zihinsel Yetenek": 3 },
        "Khambalia": { "Zihinsel Yetenek": 4 },
        # ── DİĞER ──
        "Dubhe": { "Bilgelik": 4, "Zihinsel Yetenek": 3 },
        "Merak": { "Bilgelik": 4, "Zanaatkarlık": 3 },
        "Phecda": { "Zanaatkarlık": 4, "Yardımseverlik": 3 },
        "Megrez": { "Bilgelik": 4, "Zihinsel Yetenek": 3 },
        "Alioth": { "Bilgelik": 4, "Zihinsel Yetenek": 3 },
        "Mizar": { "Bilgelik": 4, "İletişim": 3 },
        "Alkaid": { "Zihinsel Yetenek": 4, "Bilgelik": 3 },
        # ── ESTETİK VE ANALİTİK ──
        "Castra": { "Sanatsal Yetenek": 4, "Zanaatkarlık": 3 },
        "Acubens": { "Zihinsel Yetenek": 4, "Bilgelik": 3 },
        # ── ORTAKLIK VE DANISMANLIK ──
        "Diadem": {"Yardımseverlik": 4, "Sanatsal Yetenek": 3},
        "Sualocin": { "Sanatsal Yetenek": 4, "Liderlik": 3 },
        "Rotanev": { "Sanatsal Yetenek": 4, "Liderlik": 3 },
        "Sadatoni": {"İletişim": 4, "Yardımseverlik": 3},
        # ── VİZYON VE HEDEFE YÖNELİK ──
        "Kaus Australis": { "Zihinsel Yetenek": 5, "Liderlik": 3 },
        "Kaus Media": { "Zihinsel Yetenek": 4, "Liderlik": 3 },
        "Kaus Borealis": { "Zihinsel Yetenek": 4, "Liderlik": 3 },
        "Al Hecka": { "Zihinsel Yetenek": 4, "İletişim": 3 },
        "Alderamin": { "Liderlik": 5, "Zihinsel Yetenek": 3 },
        # ── ESTETİK VE TASARIM ──
        "Schedar": { "Sanatsal Yetenek": 5, "Liderlik": 3 },
        "Albireo": {"Sanatsal Yetenek": 5, "Maneviyat": 3},
        "Gienah": { "Sanatsal Yetenek": 5, "Zihinsel Yetenek": 3 },
        # ── KORUMA VE TARİH ──
        "Thuban": { "Sağlık/Tıp": 4, "Zanaatkarlık": 4, "Bilgelik": 4 },
        "Coxa": { "Sağlık/Tıp": 5, "Zanaatkarlık": 3 },
        "Acamar": { "Bilgelik": 4, "Zihinsel Yetenek": 3 },
        # ── KİTLE İLETİŞİM ──
        "Nunki": { "İletişim": 5, "Liderlik": 3 },
        # ── ENERJİ VE FİZİKSEL EFOR ──
        "Mirfak": { "Spor": 5, "Liderlik": 3 },
        "Deneb Kaitos": { "Zihinsel Yetenek": 4 },
        # ── SEZGİ VE KUŞBAKISI ──
        "Seginus": { "Zihinsel Yetenek": 4, "İletişim": 3 },
        "Zaurak": { "Sanatsal Yetenek": 4, "Zihinsel Yetenek": 3 },
        # ── ZANAAT VE BEDEN SANATLARI ──
        "Almach": { "Sanatsal Yetenek": 5, "Liderlik": 3 },
        "Alhena": { "Sanatsal Yetenek": 4, "Zanaatkarlık": 4 },
        "Phact": { "Sanatsal Yetenek": 5, "Zihinsel Yetenek": 3 },
        # ── KORUMA VE KAPSAYICILIK ──
        "Alkes": { "Zanaatkarlık": 4, "Yardımseverlik": 3 },
        "Tejat Prior": { "Zanaatkarlık": 4, "Yardımseverlik": 3 },
        "Tejat Posterior": { "Zanaatkarlık": 4, "Yardımseverlik": 3 },
        # ── SİRÜEL SORUMLULUK ──
        "Gacrux": { "Maneviyat": 5, "Bilgelik": 3 },
        "Acrux": { "Maneviyat": 5, "Bilgelik": 3 },
        "Rasalgethi": {"Sağlık/Tıp": 4, "Yardımseverlik": 4, "Maneviyat": 4},
        "Bunda": { "Zihinsel Yetenek": 4, "Zanaatkarlık": 3 },
        # ── GÖRSEL ALGI VE ODAK ──
        "M31": { "Zihinsel Yetenek": 5, "Sanatsal Yetenek": 3 },
        "Menkalinan": { "Sanatsal Yetenek": 4, "Zihinsel Yetenek": 3 },
        "Copula": { "Zihinsel Yetenek": 4, "Sanatsal Yetenek": 3 },
        # ── YÖN VE KEŞİF ──
        "Kochab": { "Bilgelik": 5, "Zihinsel Yetenek": 3 },
        "Pelorus": { "Bilgelik": 4, "Liderlik": 3 },
        "Wazn": { "Zihinsel Yetenek": 4, "Liderlik": 3 },
        # ── SAĞLIK VE ŞIFA YILDIZLARI ──
        "Syrma": {"Sağlık/Tıp": 5, "Yardımseverlik": 3},
        "Aculeus": { "Sağlık/Tıp": 4, "Zihinsel Yetenek": 3 },
        "Acumen": {"Sağlık/Tıp": 4, "Maneviyat": 3},
        "Acrux": { "Sağlık/Tıp": 4, "Maneviyat": 5, "Bilgelik": 3 },
    }

    # Meslek Arap Noktası (Part of Spirit) burç → meslek kategorisi eşlemesi
    # Burç Kutupsallıkları:
    # Sanatsal: Aslan, İkizler, Terazi
    # Öğretici: Yay, Oğlak, Koç
    # Toplayıcı dünyevi: Boğa, Başak
    # Yönlendirici: Akrep, Kova, Balık
    MESLEK_ARAP_BURC_MAP = {
        "Koç":     { "Liderlik": 4, "Spor": 2, "Askeriye": 2 },
        "Boğa":    { "Zanaatkarlık": 4, "Sanatsal Yetenek": 2, "Sağlık/Tıp": 1 },
        "İkizler": { "İletişim": 4, "Zihinsel Yetenek": 2, "Hukuk/Politika": 1 },
        "Yengeç":  {"Yardımseverlik": 3, "Maneviyat": 3, "Sağlık/Tıp": 1},
        "Aslan":   { "Sanatsal Yetenek": 4, "Liderlik": 2, "Askeriye": 1 },
        "Başak":   { "Zihinsel Yetenek": 4, "Zanaatkarlık": 2, "Sağlık/Tıp": 2 },
        "Terazi":  {"Sanatsal Yetenek": 3, "İletişim": 3, "Hukuk/Politika": 2},
        "Akrep":   { "Zihinsel Yetenek": 4, "Askeriye": 2 },
        "Yay":     { "Bilgelik": 4, "Liderlik": 2 },
        "Oğlak":   { "Zanaatkarlık": 3, "Zihinsel Yetenek": 3, "Askeriye": 1 },
        "Kova":    { "Zihinsel Yetenek": 4, "Bilgelik": 2 },
        "Balık":   {"Maneviyat": 4, "Sanatsal Yetenek": 2, "Sağlık/Tıp": 1},
    }

    # Sabit yıldız parlaklık/sınıflarına göre orb genişlikleri
    # 1. magnitude (en parlak) → MC: 5°, Gezegen: 4°
    # 2. magnitude → MC: 4°, Gezegen: 3°
    # 3. magnitude → MC: 3°, Gezegen: 2°
    # 4. magnitude (en sönük) → MC: 2°, Gezegen: 1.5°
    YILDIZ_ORB_KATMANI = {
        "Regulus": 1, "Spica": 1, "Sirius": 1, "Vega": 1, "Capella": 1,
        "Arcturus": 1, "Aldebaran": 1, "Antares": 1, "Fomalhaut": 1,
        "Betelgeuse": 1, "Rigel": 1, "Procyon": 1, "Altair": 1, "Deneb": 1,
        "Achernar": 1, "Alpheratz": 1, "Acrux": 1, "M31": 1, "Canopus": 1,
        "Pollux": 2, "Castor": 2, "Bellatrix": 2, "Alphard": 2, "Dubhe": 2,
        "Markab": 2, "Scheat": 2, "Algol": 2, "Denebola": 2, "Alnitak": 2,
        "Alnilam": 2, "Alphecca": 2, "Ras Alhague": 2,
        "Hamal": 2, "Kaus Australis": 2, "Alderamin": 2,
        "Schedar": 2, "Nunki": 2, "Mirfak": 2,
        "Almach": 2, "Alhena": 2, "Gacrux": 2, "Menkalinan": 2, "Kochab": 2,
        "Mirach": 2, "Zosma": 2,
        "Merak": 3, "Megrez": 3, "Alioth": 3, "Mizar": 3, "Alkaid": 3,
        "Alcyone": 3, "Polaris": 3, "Zubenelgenubi": 3, "Phecda": 3, "Mira": 3,
        "Zubenelchemali": 3, "Deneb Algedi": 3, "Sadalmelik": 3, "Sadalsuud": 3,
        "Skat": 3, "Unukalhai": 3, "Vindemiatrix": 3, "Menkar": 3,
        "Sadatoni": 3, "Kaus Media": 3, "Sheratan": 3, "Nashira": 3,
        "Porrima": 3, "Dabih": 3, "Albireo": 3, "Gienah": 3,
        "Acamar": 3, "Deneb Kaitos": 3, "Sabik": 3, "Enif": 3,
        "Rasalgethi": 3, "Tejat Prior": 3, "Tejat Posterior": 3, "Pelorus": 3,
        "Facies": 4, "Praesepe": 4,
        "Zavijava": 4, "Kaus Borealis": 4, "Al Hecka": 4, "Diadem": 4,
        "Acubens": 4, "Rukbat": 4, "Terebellum": 4,
        "Thuban": 4, "Seginus": 4, "Zaurak": 4,
        "Phact": 4, "Alkes": 4, "Bunda": 4, "Copula": 4, "Wazn": 4,
        "Kerb": 2,
        "Castra": 5, "Sualocin": 5, "Rotanev": 5, "Khambalia": 5,
    }

    YILDIZ_MC_ORB = {1: 2.0, 2: 1.5, 3: 1.0, 4: 0.5}
    YILDIZ_GEZEGEN_ORB = {1: 2.0, 2: 1.5, 3: 1.0, 4: 0.5}

    # MC burç yöneticileri
    MC_YONETICI_MAP = {
        "Koç": "Mars", "Boğa": "Venüs", "İkizler": "Merkür", "Yengeç": "Ay",
        "Aslan": "Güneş", "Başak": "Merkür", "Terazi": "Venüs", "Akrep": "Mars",
        "Yay": "Jüpiter", "Oğlak": "Satürn", "Kova": "Uranüs", "Balık": "Neptün",
    }

    # Yönetici gezegenin burç dignity tablosu (ev strength)
    YONETICI_EV_GUCU = {
        "Koç": {"Mars": 10, "Güneş": 9, "Jüpiter": 6, "Satürn": 3, "Venüs": 5},
        "Boğa": {"Venüs": 10, "Ay": 9, "Satürn": 6, "Merkür": 3, "Mars": 2},
        "İkizler": {"Merkür": 10, "Jüpiter": 5, "Venüs": 6, "Satürn": 3},
        "Yengeç": {"Ay": 10, "Mars": 5, "Venüs": 6, "Satürn": 3},
        "Aslan": {"Güneş": 10, "Jüpiter": 9, "Mars": 6, "Satürn": 3},
        "Başak": {"Merkür": 10, "Venüs": 6, "Satürn": 5, "Mars": 3},
        "Terazi": {"Venüs": 10, "Satürn": 9, "Merkür": 5, "Mars": 3},
        "Akrep": {"Mars": 10, "Plüton": 9, "Venüs": 5, "Jüpiter": 3},
        "Yay": {"Jüpiter": 10, "Güneş": 9, "Mars": 6, "Satürn": 3},
        "Oğlak": {"Satürn": 10, "Venüs": 9, "Merkür": 5, "Mars": 3},
        "Kova": {"Uranüs": 10, "Satürn": 9, "Merkür": 5, "Venüs": 3},
        "Balık": {"Neptün": 10, "Jüpiter": 9, "Venüs": 6, "Mars": 3},
    }

    # ─── MERCÜR'ÜN ZEKA HARİTASI ───
    # Merkür'ün burcu zeka türünü, evi zekanın hangi alana odaklandığını gösterir
    MERCURY_BURC_ZEKA = {
        "Koç":    { "Spor": 2, "Liderlik": 2 },
        "Boğa":   { "Zanaatkarlık": 3, "Liderlik": 1 },
        "İkizler": { "İletişim": 4, "Zihinsel Yetenek": 1 },
        "Yengeç": {"tip": "Duygusal Zeka", "Yardımseverlik": 2, "Maneviyat": 2},
        "Aslan":  { "Sanatsal Yetenek": 3, "Liderlik": 2 },
        "Başak": { "Zihinsel Yetenek": 3, "Zanaatkarlık": 1 },
        "Terazi": {"tip": "Diplomatik/Sanatsal Zeka", "Sanatsal Yetenek": 2, "İletişim": 2},
        "Akrep":  { "Zihinsel Yetenek": 3, "Bilgelik": 1 },
        "Yay":    { "Bilgelik": 3, "İletişim": 1 },
        "Oğlak":  { "Zihinsel Yetenek": 3, "Zanaatkarlık": 1 },
        "Kova":   { "Zihinsel Yetenek": 3, "Bilgelik": 1 },
        "Balık":  {"tip": "Sezgisel/Yaratıcı Zeka", "Sanatsal Yetenek": 2, "Maneviyat": 2},
    }

    MERCURY_EV_ZEKA = {
        1:  { "İletişim": 2, "Liderlik": 1 },
        2:  { "Liderlik": 2, "Zanaatkarlık": 2 },
        3:  { "İletişim": 3, "Zihinsel Yetenek": 1 },
        4:  { "Yardımseverlik": 2, "Zanaatkarlık": 1 },
        5:  { "Sanatsal Yetenek": 3, "Liderlik": 1 },
        6:  { "Yardımseverlik": 2, "Zihinsel Yetenek": 2 },
        7:  {"oda": "Ortaklık/Diplomasi Zekası", "İletişim": 2, "Sanatsal Yetenek": 1},
        8:  { "Zihinsel Yetenek": 3, "Maneviyat": 1 },
        9:  { "Bilgelik": 3, "İletişim": 1 },
        10: { "Zihinsel Yetenek": 2, "Liderlik": 2 },
        11: { "Zihinsel Yetenek": 3, "İletişim": 1 },
        12: {"oda": "Gizli/Derin Zeka", "Maneviyat": 3, "Sanatsal Yetenek": 1},
    }

    # ─── 12 ZEKA TÜRÜ: ASTROLOJİK İMZA TABLOSU ───
    # Gardner'ın Çoklu Zeka Kuramı + Astroloji
    # Her gezegen-burç kombinasyonu ilgili zeka türlerine katkı verir
    GEZEGEN_BURC_ZEKA = {
        ("Güneş", "Aslan"): {"Liderlik_Z": 6, "Gorsel_Z": 2},
        ("Güneş", "Koç"): { "Liderlik_Z": 5, "Kinestetik_Z": 3, "Girişimcilik": 2 },
        ("Güneş", "Yay"): { "Felsefi_Z": 4, "Liderlik_Z": 3, "Girişimcilik": 2 },
        ("Güneş", "Oğlak"): {"Liderlik_Z": 4, "Stratejik_Z": 3},
        ("Güneş", "Boğa"): {"Doga_Z": 3, "Gorsel_Z": 2},
        ("Güneş", "Akrep"): { "Stratejik_Z": 4, "Liderlik_Z": 2, "Stratejik Zeka": 2 },
        ("Güneş", "İkizler"): {"Sozel_Z": 4, "Sosyal_Z": 2},
        ("Güneş", "Terazi"): {"Sosyal_Z": 4, "Gorsel_Z": 3},
        ("Güneş", "Kova"): { "Yenilikci_Z": 4, "Liderlik_Z": 2, "Yenilikçilik": 3 },
        ("Güneş", "Başak"): {"Mantiksal_Z": 3, "Doga_Z": 2},
        ("Güneş", "Yengeç"): {"Duygusal_Z": 3, "Liderlik_Z": 2},
        ("Güneş", "Balık"): {"Duygusal_Z": 3, "Muzikal_Z": 2},
        ("Ay", "Yengeç"): {"Duygusal_Z": 6, "Sosyal_Z": 2},
        ("Ay", "Akrep"): { "Stratejik_Z": 4, "Duygusal_Z": 4, "Stratejik Zeka": 2 },
        ("Ay", "Balık"): {"Duygusal_Z": 5, "Muzikal_Z": 3},
        ("Ay", "Boğa"): {"Doga_Z": 4, "Duygusal_Z": 3},
        ("Ay", "Aslan"): {"Liderlik_Z": 3, "Gorsel_Z": 3},
        ("Ay", "Başak"): {"Mantiksal_Z": 3, "Duygusal_Z": 3},
        ("Ay", "Koç"): {"Liderlik_Z": 3, "Kinestetik_Z": 2},
        ("Ay", "Terazi"): {"Sosyal_Z": 4, "Gorsel_Z": 3},
        ("Ay", "Yay"): {"Felsefi_Z": 3, "Duygusal_Z": 2},
        ("Ay", "Oğlak"): {"Stratejik_Z": 3, "Duygusal_Z": 2},
        ("Ay", "Kova"): {"Yenilikci_Z": 3, "Sosyal_Z": 2},
        ("Ay", "İkizler"): {"Sozel_Z": 4, "Duygusal_Z": 2},
        ("Merkür", "İkizler"): {"Sozel_Z": 6, "Mantiksal_Z": 2},
        ("Merkür", "Başak"): { "Mantiksal_Z": 6, "Sozel_Z": 2, "Akademik/Araştırma": 3 },
        ("Merkür", "Kova"): { "Yenilikci_Z": 5, "Mantiksal_Z": 3, "Yenilikçilik": 3 },
        ("Merkür", "Oğlak"): {"Stratejik_Z": 4, "Mantiksal_Z": 3},
        ("Merkür", "Akrep"): { "Stratejik_Z": 4, "Mantiksal_Z": 3, "Stratejik Zeka": 3 },
        ("Merkür", "Koç"): {"Liderlik_Z": 3, "Sozel_Z": 3},
        ("Merkür", "Boğa"): {"Doga_Z": 3, "Mantiksal_Z": 2},
        ("Merkür", "Yengeç"): {"Duygusal_Z": 3, "Sozel_Z": 3},
        ("Merkür", "Aslan"): {"Liderlik_Z": 3, "Gorsel_Z": 2},
        ("Merkür", "Terazi"): {"Sosyal_Z": 3, "Gorsel_Z": 2},
        ("Merkür", "Yay"): {"Felsefi_Z": 4, "Sozel_Z": 2},
        ("Merkür", "Balık"): {"Muzikal_Z": 3, "Duygusal_Z": 2},
        ("Venüs", "Boğa"): {"Gorsel_Z": 5, "Doga_Z": 3},
        ("Venüs", "Terazi"): {"Sosyal_Z": 5, "Gorsel_Z": 3},
        ("Venüs", "Balık"): {"Muzikal_Z": 5, "Duygusal_Z": 3},
        ("Venüs", "Aslan"): {"Gorsel_Z": 4, "Liderlik_Z": 3},
        ("Venüs", "Koç"): {"Kinestetik_Z": 3, "Gorsel_Z": 3},
        ("Venüs", "Akrep"): { "Stratejik_Z": 4, "Duygusal_Z": 3, "Stratejik Zeka": 2 },
        ("Venüs", "Yay"): {"Felsefi_Z": 3, "Gorsel_Z": 2},
        ("Venüs", "Oğlak"): {"Stratejik_Z": 3, "Doga_Z": 2},
        ("Venüs", "Kova"): { "Yenilikci_Z": 3, "Gorsel_Z": 2, "Yenilikçilik": 2 },
        ("Venüs", "İkizler"): {"Sozel_Z": 3, "Gorsel_Z": 2},
        ("Venüs", "Yengeç"): {"Duygusal_Z": 4, "Gorsel_Z": 2},
        ("Venüs", "Başak"): {"Mantiksal_Z": 3, "Doga_Z": 3},
        ("Mars", "Koç"): { "Kinestetik_Z": 6, "Liderlik_Z": 3, "Girişimcilik": 3 },
        ("Mars", "Akrep"): { "Stratejik_Z": 5, "Kinestetik_Z": 3, "Stratejik Zeka": 3 },
        ("Mars", "Oğlak"): {"Stratejik_Z": 4, "Kinestetik_Z": 3},
        ("Mars", "Aslan"): {"Liderlik_Z": 4, "Kinestetik_Z": 3},
        ("Mars", "Yay"): { "Felsefi_Z": 3, "Kinestetik_Z": 3, "Girişimcilik": 3 },
        ("Mars", "Boğa"): {"Doga_Z": 3, "Kinestetik_Z": 3},
        ("Mars", "Başak"): {"Mantiksal_Z": 3, "Kinestetik_Z": 2},
        ("Mars", "İkizler"): {"Sozel_Z": 3, "Kinestetik_Z": 2},
        ("Mars", "Terazi"): {"Sosyal_Z": 3, "Kinestetik_Z": 2},
        ("Mars", "Kova"): { "Yenilikci_Z": 3, "Kinestetik_Z": 2, "Yenilikçilik": 3 },
        ("Mars", "Yengeç"): {"Duygusal_Z": 3, "Kinestetik_Z": 2},
        ("Mars", "Balık"): {"Muzikal_Z": 2, "Kinestetik_Z": 2},
        ("Jüpiter", "Yay"): { "Felsefi_Z": 6, "Sosyal_Z": 3, "Girişimcilik": 3 },
        ("Jüpiter", "Balık"): {"Duygusal_Z": 5, "Muzikal_Z": 3},
        ("Jüpiter", "Koç"): { "Liderlik_Z": 4, "Kinestetik_Z": 2, "Girişimcilik": 3 },
        ("Jüpiter", "Aslan"): {"Liderlik_Z": 4, "Gorsel_Z": 2},
        ("Jüpiter", "Boğa"): { "Doga_Z": 4, "Sosyal_Z": 2, "Girişimcilik": 2 },
        ("Jüpiter", "İkizler"): {"Sozel_Z": 3, "Sosyal_Z": 3},
        ("Jüpiter", "Yengeç"): {"Duygusal_Z": 3, "Sosyal_Z": 3},
        ("Jüpiter", "Terazi"): {"Sosyal_Z": 5, "Gorsel_Z": 2},
        ("Jüpiter", "Akrep"): {"Stratejik_Z": 4, "Felsefi_Z": 3},
        ("Jüpiter", "Oğlak"): {"Stratejik_Z": 3, "Mantiksal_Z": 3},
        ("Jüpiter", "Kova"): {"Yenilikci_Z": 4, "Sosyal_Z": 3},
        ("Jüpiter", "Başak"): {"Mantiksal_Z": 3, "Doga_Z": 3},
        ("Satürn", "Oğlak"): { "Stratejik_Z": 6, "Mantiksal_Z": 3, "Akademik/Araştırma": 3 },
        ("Satürn", "Kova"): { "Yenilikci_Z": 5, "Stratejik_Z": 3, "Akademik/Araştırma": 2 },
        ("Satürn", "Terazi"): {"Sosyal_Z": 4, "Stratejik_Z": 3},
        ("Satürn", "İkizler"): {"Sozel_Z": 3, "Mantiksal_Z": 3},
        ("Satürn", "Boğa"): {"Doga_Z": 4, "Stratejik_Z": 2},
        ("Satürn", "Başak"): {"Mantiksal_Z": 5, "Doga_Z": 3},
        ("Satürn", "Akrep"): {"Stratejik_Z": 5, "Duygusal_Z": 2},
        ("Satürn", "Koç"): {"Liderlik_Z": 3, "Kinestetik_Z": 3},
        ("Satürn", "Aslan"): {"Liderlik_Z": 3, "Gorsel_Z": 2},
        ("Satürn", "Yay"): {"Felsefi_Z": 3, "Stratejik_Z": 2},
        ("Satürn", "Yengeç"): {"Duygusal_Z": 3, "Stratejik_Z": 2},
        ("Satürn", "Balık"): {"Duygusal_Z": 3, "Muzikal_Z": 2},
        ("Uranüs", "Kova"): { "Yenilikci_Z": 6, "Mantiksal_Z": 2, "Akademik/Araştırma": 3, "Yenilikçilik": 4 },
        ("Uranüs", "Koç"): { "Yenilikci_Z": 4, "Kinestetik_Z": 2, "Yenilikçilik": 3 },
        ("Uranüs", "Boğa"): { "Yenilikci_Z": 3, "Doga_Z": 2, "Yenilikçilik": 2 },
        ("Uranüs", "İkizler"): {"Yenilikci_Z": 4, "Sozel_Z": 2},
        ("Uranüs", "Yay"): {"Felsefi_Z": 4, "Yenilikci_Z": 3},
        ("Uranüs", "Akrep"): {"Stratejik_Z": 4, "Yenilikci_Z": 3},
        ("Uranüs", "Oğlak"): {"Stratejik_Z": 4, "Yenilikci_Z": 3},
        ("Uranüs", "Terazi"): {"Sosyal_Z": 3, "Yenilikci_Z": 3},
        ("Uranüs", "Aslan"): {"Liderlik_Z": 3, "Yenilikci_Z": 3},
        ("Uranüs", "Balık"): {"Duygusal_Z": 3, "Yenilikci_Z": 3},
        ("Uranüs", "Yengeç"): {"Duygusal_Z": 3, "Yenilikci_Z": 2},
        ("Uranüs", "Başak"): {"Mantiksal_Z": 3, "Yenilikci_Z": 3},
        ("Neptün", "Balık"): {"Muzikal_Z": 6, "Duygusal_Z": 4},
        ("Neptün", "Akrep"): { "Stratejik_Z": 4, "Duygusal_Z": 3, "Stratejik Zeka": 2 },
        ("Neptün", "Yengeç"): {"Duygusal_Z": 5, "Muzikal_Z": 3},
        ("Neptün", "Boğa"): {"Gorsel_Z": 3, "Doga_Z": 3},
        ("Neptün", "Aslan"): {"Gorsel_Z": 4, "Muzikal_Z": 3},
        ("Neptün", "Terazi"): {"Sosyal_Z": 3, "Gorsel_Z": 3},
        ("Neptün", "Yay"): {"Felsefi_Z": 4, "Muzikal_Z": 3},
        ("Neptün", "Koç"): {"Kinestetik_Z": 3, "Muzikal_Z": 2},
        ("Neptün", "İkizler"): {"Sozel_Z": 3, "Muzikal_Z": 3},
        ("Neptün", "Oğlak"): {"Stratejik_Z": 3, "Muzikal_Z": 2},
        ("Neptün", "Kova"): {"Yenilikci_Z": 3, "Muzikal_Z": 3},
        ("Neptün", "Başak"): {"Mantiksal_Z": 3, "Doga_Z": 2},
        ("Plüton", "Akrep"): { "Stratejik_Z": 6, "Duygusal_Z": 3, "Stratejik Zeka": 4 },
        ("Plüton", "Koç"): { "Liderlik_Z": 4, "Kinestetik_Z": 3, "Girişimcilik": 2 },
        ("Plüton", "Terazi"): {"Sosyal_Z": 4, "Stratejik_Z": 3},
        ("Plüton", "Oğlak"): {"Stratejik_Z": 5, "Mantiksal_Z": 2},
        ("Plüton", "Yay"): {"Felsefi_Z": 4, "Stratejik_Z": 3},
        ("Plüton", "Kova"): {"Yenilikci_Z": 4, "Stratejik_Z": 3},
        ("Plüton", "İkizler"): {"Sozel_Z": 3, "Stratejik_Z": 3},
        ("Plüton", "Boğa"): {"Doga_Z": 3, "Stratejik_Z": 3},
        ("Plüton", "Aslan"): {"Liderlik_Z": 4, "Gorsel_Z": 2},
        ("Plüton", "Yengeç"): {"Duygusal_Z": 4, "Stratejik_Z": 2},
        ("Plüton", "Başak"): {"Mantiksal_Z": 3, "Stratejik_Z": 3},
        ("Plüton", "Balık"): {"Duygusal_Z": 4, "Muzikal_Z": 2},
    }

    # Gezegenin bulunduğu ev, ilgili zeka türünü güçlendirir
    ZEKA_EVLERI = {
        ("Merkür", 3): {"Sozel_Z": 3, "Mantiksal_Z": 2},
        ("Merkür", 6): {"Mantiksal_Z": 3},
        ("Merkür", 10): {"Sozel_Z": 2, "Mantiksal_Z": 2},
        ("Merkür", 9): {"Felsefi_Z": 2, "Sozel_Z": 2},
        ("Uranüs", 11): {"Yenilikci_Z": 4},
        ("Uranüs", 3): {"Yenilikci_Z": 3},
        ("Uranüs", 10): {"Yenilikci_Z": 3},
        ("Mars", 1): {"Kinestetik_Z": 4},
        ("Mars", 5): {"Kinestetik_Z": 2},
        ("Mars", 10): {"Kinestetik_Z": 3, "Liderlik_Z": 2},
        ("Güneş", 1): {"Liderlik_Z": 4},
        ("Güneş", 10): {"Liderlik_Z": 5},
        ("Güneş", 5): {"Gorsel_Z": 2, "Liderlik_Z": 2},
        ("Jüpiter", 9): {"Felsefi_Z": 4, "Sosyal_Z": 2},
        ("Jüpiter", 11): {"Sosyal_Z": 3},
        ("Jüpiter", 2): {"Doga_Z": 2, "Sosyal_Z": 2},
        ("Venüs", 2): {"Gorsel_Z": 2, "Doga_Z": 2},
        ("Venüs", 5): {"Gorsel_Z": 3, "Muzikal_Z": 2},
        ("Venüs", 7): {"Sosyal_Z": 3},
        ("Satürn", 10): {"Stratejik_Z": 4},
        ("Satürn", 6): {"Mantiksal_Z": 3, "Doga_Z": 2},
        ("Satürn", 2): {"Doga_Z": 3},
        ("Neptün", 12): {"Muzikal_Z": 3, "Duygusal_Z": 3},
        ("Neptün", 5): {"Muzikal_Z": 3, "Gorsel_Z": 2},
        ("Plüton", 8): {"Stratejik_Z": 4, "Duygusal_Z": 2},
        ("Plüton", 10): {"Stratejik_Z": 3, "Liderlik_Z": 2},
        ("Ay", 4): {"Duygusal_Z": 3},
        ("Ay", 12): {"Duygusal_Z": 3, "Muzikal_Z": 2},
    }

    # Zeka türünden meslek kategorisine eşleme (ağırlıklar ile)
    ZEKA_MESLEK_ESLESTIRME = {
        "Sozel_Z": { "Hukuk/Politika": 0, "İletişim": 0, "Bilgelik": 0 },
        "Mantiksal_Z": { "Bilgelik": 0, "Zihinsel Yetenek": 0 },
        "Gorsel_Z": { "Sanatsal Yetenek": 0, "Zanaatkarlık": 0, "Zihinsel Yetenek": 0 },
        "Muzikal_Z": {"Sanatsal Yetenek": 0.7, "Maneviyat": 0.25},
        "Kinestetik_Z": { "Spor": 0, "Askeriye": 0, "Sağlık/Tıp": 0 },
        "Doga_Z": { "Zanaatkarlık": 0, "Sağlık/Tıp": 0, "Yardımseverlik": 0 },
        "Sosyal_Z": { "Liderlik": 0, "Hukuk/Politika": 0, "Yardımseverlik": 0 },
        "Duygusal_Z": {"Maneviyat": 0.65, "Yardımseverlik": 0.6, "Sanatsal Yetenek": 0.15},
        "Yenilikci_Z": { "Zihinsel Yetenek": 0, "Liderlik": 0 },
        "Stratejik_Z": { "Zihinsel Yetenek": 0, "Liderlik": 0, "Askeriye": 0 },
        "Felsefi_Z": { "Bilgelik": 0, "Maneviyat": 0 },
        "Liderlik_Z": { "Liderlik": 0, "Askeriye": 0 },
    }

    def zekeleri_hesapla(self, jd=None):
        """
        12 zeka türünü gezegen burç ve ev konumlarından hesaplar.
        Her gezegenin burcu → zeka türüne katkı verir.
        Her gezegenin evi → zeka türünü güçlendirir.
        MC kavuşumu → zeka katkısı ×1.5 ile çarpılır.
        """
        try:
            if self.mod == "ebeveyn_cocuk":
                d1 = self.event_date.date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            else:
                d1 = self.p1 if isinstance(self.p1, date) else datetime.strptime(str(self.p1), "%Y-%m-%d").date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            jd = swe.julday(d1.year, d1.month, d1.day, dogum_saat_utc)
        except Exception:
            return {}

        try:
            _, ascmc = swe.houses_ex(jd, self.enlem, self.boylam, b'P')
            mc_derece = ascmc[1]
        except Exception:
            mc_derece = 0

        burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
                    "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]

        gezegenler = {
            "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY,
            "Venüs": swe.VENUS, "Mars": swe.MARS, "Jüpiter": swe.JUPITER,
            "Satürn": swe.SATURN, "Uranüs": swe.URANUS, "Neptün": swe.NEPTUNE,
            "Plüton": swe.PLUTO
        }

        zeka = {k: 0 for k in [
            "Sozel_Z", "Mantiksal_Z", "Gorsel_Z", "Muzikal_Z",
            "Kinestetik_Z", "Doga_Z", "Sosyal_Z", "Duygusal_Z",
            "Yenilikci_Z", "Stratejik_Z", "Felsefi_Z", "Liderlik_Z"
        ]}

        try:
            res, _ = swe.houses_ex(jd, self.enlem, self.boylam, b'P')
        except Exception:
            return zeka

        for g_isim, g_id in gezegenler.items():
            try:
                pos = swe.calc_ut(jd, g_id)[0][0]
                burc = burclar[int(pos / 30) % 12]

                ev = 0
                for idx in range(12):
                    h_start = res[idx]
                    h_end = res[(idx + 1) % 12]
                    if h_start < h_end:
                        if h_start <= pos < h_end:
                            ev = idx + 1
                            break
                    else:
                        if pos >= h_start or pos < h_end:
                            ev = idx + 1
                            break

                burc_zeka = self.GEZEGEN_BURC_ZEKA.get((g_isim, burc), {})
                for z, p in burc_zeka.items():
                    if z in zeka:
                        zeka[z] += p

                ev_zeka = self.ZEKA_EVLERI.get((g_isim, ev), {})
                for z, p in ev_zeka.items():
                    if z in zeka:
                        zeka[z] += p

                mc_fark = abs(mc_derece - pos)
                if mc_fark > 180:
                    mc_fark = 360 - mc_fark
                if mc_fark <= 8:
                    for z, p in burc_zeka.items():
                        if z in zeka:
                            zeka[z] += int(p * 0.5)

            except Exception:
                continue

        return zeka

    def mc_analizi(self):
        """
        MC (Midheaven) analizi: MC burcu, yöneticisi, yöneticinin evi/burcu.
        Dönüşüm haritası içinMC + yöneticisi kariyer potansiyelini gösterir.
        """
        try:
            if self.mod == "ebeveyn_cocuk":
                d1 = self.event_date.date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            else:
                d1 = self.p1 if isinstance(self.p1, date) else datetime.strptime(str(self.p1), "%Y-%m-%d").date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            j1 = swe.julday(d1.year, d1.month, d1.day, dogum_saat_utc)
        except Exception:
            return {}

        try:
            _, ascmc = swe.houses_ex(j1, self.enlem, self.boylam, b'P')
            mc_derece = ascmc[1]
        except Exception:
            return {}

        mc_burc = dereceyi_burca_cevir(mc_derece)
        mc_derece_ic = mc_derece % 30
        mc_yonetici = self.MC_YONETICI_MAP.get(mc_burc, "")

        # Yöneticinin haritadaki konumu
        gezegen_id_haritasi = {
            "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS,
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN, "Uranüs": swe.URANUS,
            "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO, "Kronos": swe.KRONOS
        }

        yonetici_konum = {}
        if mc_yonetici in gezegen_id_haritasi:
            try:
                y_pos = get_planetary_position(j1, gezegen_id_haritasi[mc_yonetici])
                y_burc = dereceyi_burca_cevir(y_pos)
                y_ev = self.ev_konumu_bul(j1, gezegen_id_haritasi[mc_yonetici])
                y_derece_ic = y_pos % 30
                yonetici_konum = {
                    "burc": y_burc,
                    "ev": y_ev,
                    "derece_ic": round(y_derece_ic, 1),
                    "derece_tam": round(y_pos, 1),
                }
            except Exception:
                pass

        # Yöneticinin ev gücü
        ev_guc = 5  # varsayılan orta
        if mc_yonetici and mc_burc in self.YONETICI_EV_GUCU:
            ev_guc = self.YONETICI_EV_GUCU[mc_burc].get(mc_yonetici, 5)

        return {
            "mc_derece": round(mc_derece, 1),
            "mc_burc": mc_burc,
            "mc_derece_ic": round(mc_derece_ic, 1),
            "mc_yonetici": mc_yonetici,
            "yonetici_konum": yonetici_konum,
            "ev_guc": ev_guc,
            "jd": j1,
        }

    def sabit_yildiz_analizi(self):
        """
        Tüm gezegenler ve MC ile kavuşum yapan sabit yıldızları bulur.
        Yıldız parlaklık sınıfına göre değişen orb genişliği kullanılır:
          1. magnitüd (en parlak): MC 5°, gezegen 4°
          2. magnitüd: MC 4°, gezegen 3°
          3. magnitüd: MC 3°, gezegen 2°
          4. magnitüd (en sönük): MC 2°, gezegen 1.5°
        Pozisyonlar swe.fixstar_ut() ile natal JD'ye göre dinamik hesaplanır.
        """
        mc_bilgisi = self.mc_analizi()
        if not mc_bilgisi:
            return {"mc_yildizlari": [], "gezegen_yildizlari": [], "tum_yildizlar": []}

        j1 = mc_bilgisi["jd"]
        mc_derece = mc_bilgisi["mc_derece"]

        gezegen_id_haritasi = {
            "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS,
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN, "Uranüs": swe.URANUS,
            "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO, "Kronos": swe.KRONOS
        }

        gezegen_pozisyonlari = {}
        for g_isim, g_id in gezegen_id_haritasi.items():
            try:
                pos = get_planetary_position(j1, g_id)
                gezegen_pozisyonlari[g_isim] = pos
            except Exception:
                continue

        mc_yildizlari = []
        gezegen_yildizlari = []
        yonetici_yildizlari = []
        asc_yildizlari = []

        # MC yöneticisinin pozisyonunu al (kritik kariyer göstergesi)
        mc_yonetici = mc_bilgisi.get("mc_yonetici", "")
        yonetici_konum = mc_bilgisi.get("yonetici_konum", {})
        yonetici_derece = yonetici_konum.get("derece_tam", None)

        # Yükselen (ASC) derecesi — maske/kişisel sunum göstergesi
        try:
            ascmc = mc_bilgisi.get("ascmc", None)
            if ascmc is None:
                res, ascmc = swe.houses_ex(j1, self.enlem, self.boylam, b'P')
            asc_derece = ascmc[0] if ascmc else None
        except Exception:
            asc_derece = None

        for yildiz_adi in self.SABIT_YILDIZ_MESLEK_MAP.keys():
            try:
                yildiz_derece = fixstar_ut_lon(yildiz_adi, j1)
            except Exception:
                continue

            katman = self.YILDIZ_ORB_KATMANI.get(yildiz_adi, 4)
            mc_orb_max = self.YILDIZ_MC_ORB.get(katman, 2.0)
            gezegen_orb_max = self.YILDIZ_GEZEGEN_ORB.get(katman, 1.5)

            # MC kavuşumu
            mc_fark = abs(mc_derece - yildiz_derece)
            if mc_fark > 180:
                mc_fark = 360 - mc_fark
            if mc_fark <= mc_orb_max:
                meslek_etkileri = self.SABIT_YILDIZ_MESLEK_MAP.get(yildiz_adi, {})
                mc_yildizlari.append({
                    "yildiz": yildiz_adi,
                    "orb": round(mc_fark, 2),
                    "derece": round(yildiz_derece, 1),
                    "meslek_etkileri": meslek_etkileri,
                    "tip": "MC",
                })

            # MC yöneticisi kavuşumu (kritik kariyer göstergesi)
            if yonetici_derece is not None:
                yn_fark = abs(yonetici_derece - yildiz_derece)
                if yn_fark > 180:
                    yn_fark = 360 - yn_fark
                if yn_fark <= gezegen_orb_max:
                    meslek_etkileri = self.SABIT_YILDIZ_MESLEK_MAP.get(yildiz_adi, {})
                    yonetici_yildizlari.append({
                        "yildiz": yildiz_adi,
                        "gezegen": mc_yonetici,
                        "orb": round(yn_fark, 2),
                        "derece": round(yildiz_derece, 1),
                        "meslek_etkileri": meslek_etkileri,
                        "tip": "MC_YONETICI",
                    })

            # Yükselen (ASC) kavuşumu — maske/kişisel sunum göstergesi
            if asc_derece is not None:
                asc_fark = abs(asc_derece - yildiz_derece)
                if asc_fark > 180:
                    asc_fark = 360 - asc_fark
                asc_orb_max = min(mc_orb_max, 2.0)
                if asc_fark <= asc_orb_max:
                    meslek_etkileri = self.SABIT_YILDIZ_MESLEK_MAP.get(yildiz_adi, {})
                    asc_yildizlari.append({
                        "yildiz": yildiz_adi,
                        "orb": round(asc_fark, 2),
                        "derece": round(yildiz_derece, 1),
                        "meslek_etkileri": meslek_etkileri,
                        "tip": "YUKSELEN",
                    })

            # Gezegen kavuşumları
            for g_isim, g_pos in gezegen_pozisyonlari.items():
                g_fark = abs(g_pos - yildiz_derece)
                if g_fark > 180:
                    g_fark = 360 - g_fark
                if g_fark <= gezegen_orb_max:
                    meslek_etkileri = self.SABIT_YILDIZ_MESLEK_MAP.get(yildiz_adi, {})
                    gezegen_yildizlari.append({
                        "yildiz": yildiz_adi,
                        "gezegen": g_isim,
                        "orb": round(g_fark, 2),
                        "derece": round(yildiz_derece, 1),
                        "meslek_etkileri": meslek_etkileri,
                        "tip": "GEZEGEN",
                    })

        tum = mc_yildizlari + gezegen_yildizlari + yonetici_yildizlari + asc_yildizlari
        return {
            "mc_yildizlari": mc_yildizlari,
            "gezegen_yildizlari": gezegen_yildizlari,
            "yonetici_yildizlari": yonetici_yildizlari,
            "asc_yildizlari": asc_yildizlari,
            "tum_yildizlar": tum,
        }

    def mc_sabit_yildiz_puan(self):
        """
        MC + sabit yıldız combined scoring:
        - MC burcu → meslek kategorisi bonusu
        - MC yöneticisinin evi → bonus
        - MC sabit yıldız kavuşumu → bonus
        - Gezegen sabit yıldız kavuşumları → bonus

        Döndürür: {kategori: toplam_puan, ...}
        """
        kategori_puanlari = {}

        mc_bilgisi = self.mc_analizi()
        if not mc_bilgisi:
            return kategori_puanlari

        yildiz_bilgisi = self.sabit_yildiz_analizi()

        # 1. MC burcuna göre meslek kategorisi bonusu (burç kutupsallıkları)
        mc_burc_meslek_map = {
            "Koç": { "Liderlik": 6, "Spor": 5, "Askeriye": 4 },
            "Boğa": { "Zanaatkarlık": 6, "Sağlık/Tıp": 3, "Liderlik": 2 },
            "İkizler": { "İletişim": 6, "Zihinsel Yetenek": 3 },
            "Yengeç": {"Yardımseverlik": 6, "Maneviyat": 3, "Sağlık/Tıp": 3},
            "Aslan": { "Liderlik": 6, "Sanatsal Yetenek": 4, "Askeriye": 3 },
            "Başak": { "Zihinsel Yetenek": 6, "Zanaatkarlık": 3, "Sağlık/Tıp": 3 },
            "Terazi": {"Hukuk/Politika": 6, "Sanatsal Yetenek": 3, "İletişim": 3},
            "Akrep": { "Zihinsel Yetenek": 6, "Askeriye": 3, "Sağlık/Tıp": 2 },
            "Yay": { "Bilgelik": 6, "Liderlik": 3 },
            "Oğlak": { "Liderlik": 5, "Askeriye": 3, "Zanaatkarlık": 3 },
            "Kova": { "Zihinsel Yetenek": 6, "Bilgelik": 3, "Hukuk/Politika": 2 },
            "Balık": {"Maneviyat": 6, "Sanatsal Yetenek": 3, "Sağlık/Tıp": 3},
        }

        mc_burc = mc_bilgisi["mc_burc"]
        for kategori, puan in mc_burc_meslek_map.get(mc_burc, {}).items():
            kategori_puanlari[kategori] = kategori_puanlari.get(kategori, 0) + puan

        # 1b. Yükselen (ASC) elementi — maske/kişisel sunum kariyer yönü
        try:
            ascmc = mc_bilgisi.get("ascmc", None)
            if ascmc is None:
                jd = mc_bilgisi.get("jd")
                if jd:
                    res, ascmc = swe.houses_ex(jd, self.enlem, self.boylam, b'P')
            if ascmc:
                asc_derece = ascmc[0]
                asc_burc = self.dereceyi_burca_cevir(asc_derece)
                ASC_ELEMENT_MAP = {
                    "Koç": "Ateş", "Aslan": "Ateş", "Yay": "Ateş",
                    "Boğa": "Toprak", "Başak": "Toprak", "Oğlak": "Toprak",
                    "İkizler": "Hava", "Terazi": "Hava", "Kova": "Hava",
                    "Yengeç": "Su", "Akrep": "Su", "Balık": "Su",
                }
                ASC_ELEMENT_KATEGORI = {
                    "Ateş": { "Liderlik": 1, "Spor": 1, "Askeriye": 1 },
                    "Toprak": { "Zanaatkarlık": 1, "Sağlık/Tıp": 1, "Liderlik": 1 },
                    "Hava": { "İletişim": 1, "Zihinsel Yetenek": 1, "Hukuk/Politika": 1 },
                    "Su": {"Maneviyat": 1.5, "Sanatsal Yetenek": 1.0, "Yardımseverlik": 1.0},
                }
                asc_element = ASC_ELEMENT_MAP.get(asc_burc, "")
                for kategori, puan in ASC_ELEMENT_KATEGORI.get(asc_element, {}).items():
                    kategori_puanlari[kategori] = kategori_puanlari.get(kategori, 0) + puan
        except Exception:
            pass

        # 2. MC yöneticisinin evine göre bonus (açısal evlerde güçlendirme)
        yonetici = mc_bilgisi.get("yonetici_konum", {})
        if yonetici:
            yonetici_ev = yonetici.get("ev", 0)
            # Açısal evler (1,4,7,10) daha güçlü bonus verir
            ev_guc_carpani = {1: 1.5, 4: 1.3, 7: 1.2, 10: 1.5}
            ev_meslek_map = {
                1: { "Liderlik": 2, "Spor": 2, "Askeriye": 1 },
                2: { "Zanaatkarlık": 2, "Sanatsal Yetenek": 1, "Sağlık/Tıp": 1 },
                3: { "İletişim": 1, "Zihinsel Yetenek": 1, "Hukuk/Politika": 1 },
                4: {"Yardımseverlik": 2, "Maneviyat": 2, "Sağlık/Tıp": 1},
                5: { "Sanatsal Yetenek": 2, "Zihinsel Yetenek": 1 },
                6: { "Zanaatkarlık": 2, "Bilgelik": 1, "Sağlık/Tıp": 1 },
                7: { "İletişim": 2, "Liderlik": 1, "Hukuk/Politika": 1 },
                8: { "Zihinsel Yetenek": 2, "Maneviyat": 2, "Askeriye": 1 },
                9: { "Bilgelik": 2, "Liderlik": 1 },
                10: { "Liderlik": 2, "Zihinsel Yetenek": 2, "Askeriye": 1 },
                11: { "Zihinsel Yetenek": 2, "Bilgelik": 1 },
                12: {"Maneviyat": 2, "Sanatsal Yetenek": 1},
            }
            ev_puanlari = ev_meslek_map.get(yonetici_ev, {})
            carpan = ev_guc_carpani.get(yonetici_ev, 1.0)
            for kategori, puan in ev_puanlari.items():
                bonus = round(puan * carpan, 2)
                kategori_puanlari[kategori] = kategori_puanlari.get(kategori, 0) + bonus

            # Yöneticinin kendi burcuna göre bonus (burç kutupsallıkları)
            yonetici_burc = yonetici.get("burc", "")
            yonetici_burc_bonus = {
                "Koç": { "Liderlik": 2, "Spor": 1, "Askeriye": 1 },
                "Boğa": { "Zanaatkarlık": 2, "Sağlık/Tıp": 1 },
                "İkizler": {"İletişim": 2, "Hukuk/Politika": 1},
                "Yengeç": {"Yardımseverlik": 1, "Maneviyat": 1, "Sağlık/Tıp": 1},
                "Aslan": { "Liderlik": 2, "Sanatsal Yetenek": 1 },
                "Başak": { "Zihinsel Yetenek": 2, "Zanaatkarlık": 1, "Sağlık/Tıp": 1 },
                "Terazi": {"Hukuk/Politika": 2, "Sanatsal Yetenek": 1, "İletişim": 1},
                "Akrep": { "Zihinsel Yetenek": 2, "Askeriye": 1 },
                "Yay": { "Bilgelik": 2 },
                "Oğlak": { "Liderlik": 1, "Askeriye": 1, "Zanaatkarlık": 1 },
                "Kova": { "Zihinsel Yetenek": 2, "Hukuk/Politika": 1 },
                "Balık": {"Maneviyat": 2, "Sağlık/Tıp": 1},
            }
            for kategori, puan in yonetici_burc_bonus.get(yonetici_burc, {}).items():
                kategori_puanlari[kategori] = kategori_puanlari.get(kategori, 0) + puan

        # 2b. Orta seviye gezegen-burç konumu bonusu (3 puan ana, 1 puan yan)
        j1 = mc_bilgisi["jd"]
        gezegen_burc_meslek_map = {
            ("Mars", "Koç"): { "Spor": 6, "Liderlik": 2, "Askeriye": 3 },
            ("Mars", "Aslan"): { "Spor": 4, "Sanatsal Yetenek": 2, "Askeriye": 1 },
            ("Mars", "Yay"): { "Spor": 4, "Liderlik": 2, "Askeriye": 1 },
            ("Mars", "Boğa"): { "Spor": 3, "Zanaatkarlık": 2 },
            ("Mars", "Başak"): { "Spor": 3, "Zihinsel Yetenek": 2, "Sağlık/Tıp": 1 },
            ("Mars", "Oğlak"): { "Spor": 3, "Zihinsel Yetenek": 1, "Askeriye": 1 },
            ("Mars", "İkizler"): {"Spor": 2, "İletişim": 2},
            ("Mars", "Terazi"): {"Spor": 2, "Sanatsal Yetenek": 2, "Hukuk/Politika": 1},
            ("Mars", "Kova"): { "Spor": 3, "Zihinsel Yetenek": 2 },
            ("Mars", "Akrep"): { "Spor": 3, "Zihinsel Yetenek": 2, "Askeriye": 2 },
            ("Mars", "Balık"): {"Spor": 2, "Maneviyat": 2},
            ("Mars", "Yengeç"): {"Spor": 2, "Yardımseverlik": 2},
            ("Venüs", "Boğa"): { "Sanatsal Yetenek": 2, "Zanaatkarlık": 1 },
            ("Venüs", "Terazi"): {"Sanatsal Yetenek": 2, "İletişim": 1},
            ("Venüs", "Balık"): {"Sanatsal Yetenek": 2, "Maneviyat": 1},
            ("Venüs", "Aslan"): { "Sanatsal Yetenek": 2, "Liderlik": 1 },
            ("Venüs", "Koç"): { "Sanatsal Yetenek": 1, "Liderlik": 1 },
            ("Venüs", "Akrep"): { "Sanatsal Yetenek": 2, "Zihinsel Yetenek": 1 },
            ("Venüs", "Yay"): { "Sanatsal Yetenek": 1, "Bilgelik": 1 },
            ("Venüs", "Oğlak"): { "Sanatsal Yetenek": 1, "Zanaatkarlık": 1 },
            ("Venüs", "Kova"): { "Sanatsal Yetenek": 1, "Zihinsel Yetenek": 1 },
            ("Venüs", "İkizler"): {"Sanatsal Yetenek": 1, "İletişim": 1},
            ("Venüs", "Yengeç"): {"Sanatsal Yetenek": 2, "Yardımseverlik": 1},
            ("Venüs", "Başak"): { "Sanatsal Yetenek": 1, "Zihinsel Yetenek": 1 },
            ("Neptün", "Balık"): {"Sanatsal Yetenek": 2, "Maneviyat": 2},
            ("Neptün", "Akrep"): { "Sanatsal Yetenek": 2, "Zihinsel Yetenek": 1 },
            ("Neptün", "Yengeç"): {"Sanatsal Yetenek": 2, "Maneviyat": 1},
            ("Neptün", "Boğa"): { "Sanatsal Yetenek": 1, "Zanaatkarlık": 1 },
            ("Neptün", "Aslan"): { "Sanatsal Yetenek": 2, "Liderlik": 1 },
            ("Neptün", "Yay"): { "Sanatsal Yetenek": 1, "Bilgelik": 1 },
            ("Güneş", "Aslan"): { "Liderlik": 2, "Sanatsal Yetenek": 1 },
            ("Güneş", "Koç"): { "Liderlik": 2, "Spor": 1 },
            ("Güneş", "Yay"): { "Bilgelik": 2, "Liderlik": 1 },
            ("Güneş", "Kova"): { "Zihinsel Yetenek": 2 },
            ("Güneş", "Boğa"): { "Zanaatkarlık": 1, "Sanatsal Yetenek": 1 },
            ("Güneş", "Akrep"): { "Zihinsel Yetenek": 1, "Askeriye": 1 },
            ("Ay", "Koç"): { "İletişim": 2, "Spor": 2, "Zihinsel Yetenek": 1 },
            ("Ay", "Yengeç"): {"Yardımseverlik": 2, "Maneviyat": 1},
            ("Ay", "Balık"): {"Maneviyat": 2, "Sanatsal Yetenek": 1},
            ("Ay", "Akrep"): { "Sanatsal Yetenek": 2, "Zihinsel Yetenek": 1, "Maneviyat": 1 },
            ("Ay", "Aslan"): { "Liderlik": 1, "Sanatsal Yetenek": 1 },
            ("Ay", "Başak"): { "Zanaatkarlık": 2, "Zihinsel Yetenek": 1, "Hukuk/Politika": 1 },
            ("Ay", "Oğlak"): { "Hukuk/Politika": 2, "Zihinsel Yetenek": 1 },
            ("Merkür", "İkizler"): { "İletişim": 2, "Bilgelik": 1 },
            ("Merkür", "Başak"): { "Bilgelik": 2, "Zanaatkarlık": 1 },
            ("Merkür", "Kova"): { "Zihinsel Yetenek": 2, "Bilgelik": 1 },
            ("Merkür", "Akrep"): { "Zihinsel Yetenek": 1, "Hukuk/Politika": 1 },
            ("Jüpiter", "Yay"): { "Bilgelik": 2, "Liderlik": 1 },
            ("Jüpiter", "Balık"): {"Maneviyat": 2, "Yardımseverlik": 1},
            ("Jüpiter", "Koç"): { "Liderlik": 2, "Askeriye": 1 },
            ("Jüpiter", "Aslan"): { "Liderlik": 2, "Sanatsal Yetenek": 1 },
            ("Jüpiter", "Boğa"): { "Zanaatkarlık": 3, "Liderlik": 1 },
            ("Satürn", "Oğlak"): { "Zihinsel Yetenek": 2, "Zanaatkarlık": 1, "Askeriye": 1 },
            ("Satürn", "Kova"): { "Zihinsel Yetenek": 2, "Bilgelik": 1 },
            ("Satürn", "İkizler"): { "İletişim": 1, "Bilgelik": 1, "Hukuk/Politika": 1 },
            ("Uranüs", "Kova"): { "Zihinsel Yetenek": 2, "Bilgelik": 1 },
            ("Uranüs", "Koç"): { "Zihinsel Yetenek": 1, "Liderlik": 1 },
            ("Uranüs", "Boğa"): { "Zihinsel Yetenek": 1, "Zanaatkarlık": 1 },
            ("Plüton", "Akrep"): { "Zihinsel Yetenek": 2, "Maneviyat": 1, "Askeriye": 1 },
            ("Plüton", "Koç"): { "Liderlik": 2, "Askeriye": 1 },
            ("Kronos", "Oğlak"): { "Zihinsel Yetenek": 2, "Liderlik": 2, "Askeriye": 1, "Stratejik Zeka": 3 },
            ("Kronos", "Kova"): { "Zihinsel Yetenek": 2, "Bilgelik": 2, "Akademik/Araştırma": 3 },
            ("Kronos", "Akrep"): { "Zihinsel Yetenek": 2, "Askeriye": 2, "Stratejik Zeka": 3 },
            ("Kronos", "Koç"): { "Liderlik": 2, "Spor": 1, "Askeriye": 2 },
            ("Kronos", "Aslan"): { "Liderlik": 2, "Sanatsal Yetenek": 1 },
            ("Kronos", "Yay"): { "Bilgelik": 2, "Akademik/Araştırma": 2 },
            ("Kronos", "Boğa"): { "Zanaatkarlık": 2, "Sağlık/Tıp": 1 },
            ("Kronos", "Başak"): { "Sağlık/Tıp": 2, "Zihinsel Yetenek": 1 },
            ("Kronos", "Terazi"): {"Hukuk/Politika": 2, "Sanatsal Yetenek": 1},
            ("Kronos", "Yengeç"): {"Yardımseverlik": 2, "Sağlık/Tıp": 1},
            ("Kronos", "İkizler"): {"İletişim": 2, "Hukuk/Politika": 1},
            ("Kronos", "Balık"): {"Maneviyat": 2, "Sağlık/Tıp": 1},
        }
        gezegen_isimleri = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter", "Satürn", "Uranüs", "Neptün", "Plüton", "Kronos"]
        gezegen_swe_idleri = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO, swe.KRONOS]
        burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
        for i, (g_isim, g_id) in enumerate(zip(gezegen_isimleri, gezegen_swe_idleri)):
            try:
                pos = get_planetary_position(j1, g_id)
                burc_index = int(pos / 30) % 12
                burc = burclar[burc_index]
                ek_map = gezegen_burc_meslek_map.get((g_isim, burc), {})
                for kategori, puan in ek_map.items():
                    kategori_puanlari[kategori] = kategori_puanlari.get(kategori, 0) + puan
            except Exception:
                continue

        # 2c. MARS'A ÖZEL AÇISAL EV VE KAVUŞUM BONUSU (spor için kritik)
        try:
            j1 = mc_bilgisi["jd"]
            mars_pos = swe.calc_ut(j1, swe.MARS)[0][0]
            mars_ev = self.ev_konumu_bul(j1, swe.MARS)
            mc_derece = mc_bilgisi.get("mc_derece", 0)
            mc_burc_check = mc_bilgisi.get("mc_burc", "")
            mars_burc_index = int(mars_pos / 30) % 12
            mars_burc_ad = burclar[mars_burc_index] if mars_burc_index < len(burclar) else ""

            # Mars açısal ev bonusu: ateş/toprak burçta更强, su/hava burçta zayıf
            ates_burclari = {"Koç", "Aslan", "Yay"}
            toprak_burclari = {"Boğa", "Başak", "Oğlak"}
            hava_burclari = {"İkizler", "Terazi", "Kova"}
            su_burclari = {"Yengeç", "Akrep", "Balık"}

            # Ateş burçlarında MC = spor odaklı kariyer
            mc_ates = mc_burc_check in ates_burclari

            if mars_ev in [1, 10]:
                if mars_burc_ad in ates_burclari:
                    kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 3.0
                elif mars_burc_ad in toprak_burclari:
                    kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 2.0
                    kategori_puanlari["Zanaatkarlık"] = kategori_puanlari.get("Zanaatkarlık", 0) + 1.0
                elif mars_burc_ad in su_burclari:
                    kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 1.0
                    kategori_puanlari["Maneviyat"] = kategori_puanlari.get("Maneviyat", 0) + 1.0
                else:
                    kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 1.5
            elif mars_ev in [4, 7]:
                if mars_burc_ad in ates_burclari:
                    kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 2.0
                elif mars_burc_ad in toprak_burclari:
                    kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 1.0
                else:
                    kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 0.5

            # Mars-MC kavuşumu (career spor göstergesi)
            mc_fark = abs(mc_derece - mars_pos)
            if mc_fark > 180:
                mc_fark = 360 - mc_fark
            if mc_fark <= 5:
                kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 4
            elif mc_fark <= 10:
                kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 2
            elif mc_fark <= 15:
                kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 1

            # MC yöneticisi Mars ise → güçlü spor kariyeri
            yonetici = mc_bilgisi.get("mc_yonetici", "")
            if yonetici == "Mars":
                kategori_puanlari["Spor"] = kategori_puanlari.get("Spor", 0) + 3

            # Venüs-Neptün kavuşumu → sanatsal kariyer (MC'de veya yöneticisi)
            for g_isim2, g_id2 in [("Venüs", swe.VENUS), ("Neptün", swe.NEPTUNE)]:
                try:
                    g_pos2 = swe.calc_ut(j1, g_id2)[0][0]
                    g_fark = abs(mc_derece - g_pos2)
                    if g_fark > 180:
                        g_fark = 360 - g_fark
                    if g_fark <= 8 and g_isim2 == "Venüs":
                        kategori_puanlari["Sanatsal Yetenek"] = kategori_puanlari.get("Sanatsal Yetenek", 0) + 2
                    elif g_fark <= 8 and g_isim2 == "Neptün":
                        kategori_puanlari["Sanatsal Yetenek"] = kategori_puanlari.get("Sanatsal Yetenek", 0) + 1
                except:
                    pass

            # Güneş kavuşumu MC'de → liderlik/sanatsal
            try:
                sun_pos = swe.calc_ut(j1, swe.SUN)[0][0]
                sun_fark = abs(mc_derece - sun_pos)
                if sun_fark > 180:
                    sun_fark = 360 - sun_fark
                if sun_fark <= 8:
                    kategori_puanlari["Liderlik"] = kategori_puanlari.get("Liderlik", 0) + 2
            except:
                pass

            # ─── MERCÜR'ÜN ZEKA HARİTASI ───
            # Merkür'ün burcu → zeka türü, evi → zekanın odak alanı
            try:
                mercury_pos = swe.calc_ut(j1, swe.MERCURY)[0][0]
                mercury_burc_index = int(mercury_pos / 30) % 12
                mercury_burc = burclar[mercury_burc_index]
                mercury_ev = self.ev_konumu_bul(j1, swe.MERCURY)

                # Burç-zeka bonusu
                burc_zeka = self.MERCURY_BURC_ZEKA.get(mercury_burc, {})
                for kategori, puan in burc_zeka.items():
                    if kategori == "tip":
                        continue
                    kategori_puanlari[kategori] = kategori_puanlari.get(kategori, 0) + puan

                # Ev-zeka odağı bonusu
                ev_zeka = self.MERCURY_EV_ZEKA.get(mercury_ev, {})
                for kategori, puan in ev_zeka.items():
                    if kategori == "oda":
                        continue
                    kategori_puanlari[kategori] = kategori_puanlari.get(kategori, 0) + puan

                # Merkür-MC kavuşumu → kariyer zekası güçlenir
                merc_mc_fark = abs(mc_derece - mercury_pos)
                if merc_mc_fark > 180:
                    merc_mc_fark = 360 - merc_mc_fark
                if merc_mc_fark <= 8:
                    kategori_puanlari["İletişim"] = kategori_puanlari.get("İletişim", 0) + 2
                    kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 1
            except:
                pass

            # ─── SATÜRN'ÜN OTORİTE ANALİZİ ───
            # Satürn MC yöneticisiyse veya MC'deyse → otorite, disiplin, kariyer otoritesi
            try:
                saturn_pos = swe.calc_ut(j1, swe.SATURN)[0][0]
                saturn_ev = self.ev_konumu_bul(j1, swe.SATURN)
                saturn_burc_index = int(saturn_pos / 30) % 12
                saturn_burc = burclar[saturn_burc_index]

                # MC yöneticisi Satürn → otorite/disiplin bonusu
                if yonetici == "Satürn":
                    # Satürn 10. evde → güçlü kariyer otoritesi
                    if saturn_ev == 10:
                        kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 3
                        kategori_puanlari["Liderlik"] = kategori_puanlari.get("Liderlik", 0) + 2
                    # Satürn 1. evde → kendi kendine otorite
                    elif saturn_ev == 1:
                        kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 2
                        kategori_puanlari["Liderlik"] = kategori_puanlari.get("Liderlik", 0) + 2
                    # Satürn 10'dan açısal evde
                    elif saturn_ev in [4, 7]:
                        kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 2
                        kategori_puanlari["Liderlik"] = kategori_puanlari.get("Liderlik", 0) + 1
                    else:
                        kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 1

                    # Satürn dignity bonusu (Oğlak/Kova'da güçlü)
                    if saturn_burc in ["Oğlak", "Kova"]:
                        kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 1
                        kategori_puanlari["Zanaatkarlık"] = kategori_puanlari.get("Zanaatkarlık", 0) + 1

                # Satürn-MC kavuşumu → otorite/uzmanlık
                sat_mc_fark = abs(mc_derece - saturn_pos)
                if sat_mc_fark > 180:
                    sat_mc_fark = 360 - sat_mc_fark
                if sat_mc_fark <= 8:
                    kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 2
                    kategori_puanlari["Liderlik"] = kategori_puanlari.get("Liderlik", 0) + 1
            except:
                pass

            # ─── KRONOS ASTEROID ANALİZİ ───
            # Kronos: Otorite, ustalık, uzmanlık, disiplin, kariyer otoritesi
            try:
                kronos_pos = swe.calc_ut(j1, swe.KRONOS)[0][0]
                kronos_ev = self.ev_konumu_bul(j1, swe.KRONOS)
                kronos_burc_index = int(kronos_pos / 30) % 12
                kronos_burc = burclar[kronos_burc_index]

                # Kronos-MC kavuşumu → güçlü kariyer otoritesi
                kronos_mc_fark = abs(mc_derece - kronos_pos)
                if kronos_mc_fark > 180:
                    kronos_mc_fark = 360 - kronos_mc_fark
                if kronos_mc_fark <= 5:
                    kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 3
                    kategori_puanlari["Liderlik"] = kategori_puanlari.get("Liderlik", 0) + 2
                    kategori_puanlari["Askeriye"] = kategori_puanlari.get("Askeriye", 0) + 1
                elif kronos_mc_fark <= 10:
                    kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 2
                    kategori_puanlari["Liderlik"] = kategori_puanlari.get("Liderlik", 0) + 1
                elif kronos_mc_fark <= 15:
                    kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 1

                # Kronos açısal evlerde → güçlü ustalık/otorite
                if kronos_ev in [1, 10]:
                    kategori_puanlari["Liderlik"] = kategori_puanlari.get("Liderlik", 0) + 2
                    kategori_puanlari["Zihinsel Yetenek"] = kategori_puanlari.get("Zihinsel Yetenek", 0) + 1
                    # Kronos Oğlak/Kova'da → ustalık bonusu
                    if kronos_burc in ["Oğlak", "Kova"]:
                        kategori_puanlari["Zanaatkarlık"] = kategori_puanlari.get("Zanaatkarlık", 0) + 1
                        kategori_puanlari["Bilgelik"] = kategori_puanlari.get("Bilgelik", 0) + 1
                elif kronos_ev in [4, 7]:
                    kategori_puanlari["Liderlik"] = kategori_puanlari.get("Liderlik", 0) + 1
            except:
                pass

        except Exception:
            pass

        # 3. Ev gücü bonusu (daha güçlü ev = daha çok puan, ORTA SEVIYE)
        ev_guc = mc_bilgisi.get("ev_guc", 5)
        guc_carpan = 0.5 + (ev_guc / 20.0)  # 0.5 - 1.0 arası, daha dengeli
        for kategori in list(kategori_puanlari.keys()):
            kategori_puanlari[kategori] = round(kategori_puanlari[kategori] * guc_carpan, 2)

        # 4. Sabit yıldız bonusları — kişisel gezegenler çok daha etkilidir
        KISISEL_GEZEGENLER = {"Güneş", "Ay", "Merkür", "Venüs", "Mars"}
        for yildiz in yildiz_bilgisi.get("tum_yildizlar", []):
            meslek_etkileri = yildiz.get("meslek_etkileri", {})
            orb = yildiz.get("orb", 3.0)
            tip = yildiz.get("tip", "")

            # Orb çarpanı: 0-1° = 1.0, 1-2° = 0.8, 2-3° = 0.6
            if orb <= 1.0:
                orb_carpan = 1.0
            elif orb <= 2.0:
                orb_carpan = 0.8
            else:
                orb_carpan = 0.6

            # Sabit yıldız tip ağırlıkları:
            # MC_YONETICI 3x → MC yöneticisi en güçlü kariyer göstergesi
            # MC 2.5x → MC doğrudan kariyer noktası
            # YUKSELEN 2x → yükselen kişisel sunum/first impression
            # Kişisel gezegen (Güneş-Mars) 2x → bireysel etki
            # Dış gezegen (Jüpiter-Plüton) 1.2x → nesilsel etki
            # Asteroid/diğer 1.0x
            if tip == "MC_YONETICI":
                tip_carpan = 3.0
            elif tip == "MC":
                tip_carpan = 2.5
            elif tip == "YUKSELEN":
                tip_carpan = 2.0
            elif tip == "GEZEGEN":
                gezegen_adi = yildiz.get("gezegen", "")
                if gezegen_adi in KISISEL_GEZEGENLER:
                    tip_carpan = 2.0
                else:
                    tip_carpan = 1.2
            else:
                tip_carpan = 1.0

            for kategori, taban_puan in meslek_etkileri.items():
                eklenen = round(taban_puan * orb_carpan * tip_carpan, 2)
                kategori_puanlari[kategori] = kategori_puanlari.get(kategori, 0) + eklenen

        return kategori_puanlari


    def ev_konumu_bul(self, j_time, planet_id):
        try:
            res, _ = swe.houses_ex(j_time, self.enlem, self.boylam, b'P')
            try:
                pos, _ = swe.calc_ut(j_time, planet_id)
                p_lon = pos[0]
            except Exception:
                isim = next((k for k, v in GEZEGENLER.items() if v == planet_id), None)
                p_lon = asteroit_tahmini_derece(isim, j_time)
                if p_lon is None:
                    return random.randint(1, 12)
            for idx in range(12):
                h_start = res[idx]
                h_end = res[(idx + 1) % 12]
                if h_start < h_end:
                    if h_start <= p_lon < h_end: return idx + 1
                else:
                    if p_lon >= h_start or p_lon < h_end: return idx + 1
            return 1
        except Exception:
            return random.randint(1, 12)

    def kadersel_cumle_kur(self, gezegen_ad, burc_ad, ev_no, rol=None):
        rx_mi = " (Rx)" in burc_ad
        temiz_burc = burc_ad.replace(" (Rx)", "")

        metin = None
        if self.mod == "ebeveyn_cocuk" and rol and FBST_GEZEGEN_EV_COCUK and FBST_GEZEGEN_EV_EBEVEYN:
            sozluk = FBST_GEZEGEN_EV_COCUK if rol == "cocuk" else FBST_GEZEGEN_EV_EBEVEYN
            metin = sozluk.get((gezegen_ad, ev_no))
        else:
            if FBST_YORUMLAR_BURC and (gezegen_ad, temiz_burc) in FBST_YORUMLAR_BURC:
                metin = FBST_YORUMLAR_BURC[(gezegen_ad, temiz_burc)]
            elif FBST_YORUMLAR_EV and (gezegen_ad, str(ev_no)) in FBST_YORUMLAR_EV:
                metin = FBST_YORUMLAR_EV[(gezegen_ad, str(ev_no))]

        if metin:
            cumle = f"<b>{gezegen_ad} {temiz_burc} {ev_no}. Ev:</b> {metin}"
        else:
            cumle = f"<b>{gezegen_ad} {temiz_burc} {ev_no}. Ev:</b> {gezegen_ad} burcu {temiz_burc} takımyıldızında yer alıyor ve {ev_no}. ev alanını etkiliyor."

        if rx_mi:
            retro_sozluk = fbst_retrolar_ebeveyn if self.mod == "ebeveyn_cocuk" else fbst_retrolar
            retro_metni = retro_sozluk.get(gezegen_ad)
            if retro_metni:
                cumle += f" <br/>{retro_metni}"

        return cumle
    
    def sabian_okuyucu(self, gezegen_isim, mutlak_derece):
        import math
        burclar_keys = ["Koc", "Boga", "Ikizler", "Yengec", "Aslan", "Basak", "Terazi", "Akrep", "Yay", "Oglak", "Kova", "Balik"]
        burc_indeks = int(mutlak_derece // 30)
        burc = burclar_keys[burc_indeks]
        
        # Astroloji kurallarına göre 0.01 derece 1. derecedir. (Örn: 14.2 = 15. derece)
        sabian_derece = math.floor(mutlak_derece % 30) + 1 
        
        # Gezegenin temel fıtratını yapi olarak belirliyoruz
        gez_fitrat_sozlugu = {
            "Güneş": "iradesi ve ego vitrini", "Ay": "duygusal aidiyet ihtiyacı",
            "Merkür": "zihinsel titresimı", "Venüs": "özdeğer algısı ve aşkı",
            "Mars": "eylemsel gucu ve tutkusu", "Jüpiter": "kadersel vizyonu",
            "Satürn": "sarsılmaz sadakati", "Uranüs": "isyankar özgürlüğü",
            "Neptün": "ilahi teslimiyeti", "Plüton": "yeraltı simyası",
            "Chiron": "kadersel yarası ve şifası", "Juno": "eş sözleşmesi",
            "Ceres": "ruhsal beslenme gücü", "Lilith": "gölge arzuları",
            "KAD": "tekamül rotası", "GAD": "karmik borcu"
        }
        gez_fitrat = gez_fitrat_sozlugu.get(gezegen_isim, "kadersel enerjisi")
        
        # Sabian Sembolünü ve Yorumunu Sözlükten Çek (mode'a göre)
        _aktif_mod = getattr(self, 'mod', 'es_sevgili')
        if _aktif_mod == "ebeveyn_cocuk" and fbst_sabian_ebeveyn:
            sabian_verisi = fbst_sabian_ebeveyn.get(burc, {}).get(sabian_derece, (varsayilan_sabian_vizyonu, varsayilan_sabian_yorumu))
        else:
            sabian_verisi = fbst_sabian.get(burc, {}).get(sabian_derece, (varsayilan_sabian_vizyonu, varsayilan_sabian_yorumu))
        sembol_vizyonu = sabian_verisi[0]
        sembol_yorumu = sabian_verisi[1]
        
        # ReportLab (PDF) uyumlu şık tipografi
        if _aktif_mod == "ebeveyn_cocuk":
            sentez = f"👁️‍🗨️ <b>Sabian Şifresi ({sabian_derece}°):</b> <i>\"{sembol_vizyonu}\"</i><br/>"
            sentez += f"<font color='#555555'><b>Mühür:</b> {gez_fitrat}, bu vizyonla mühürlenmiştir. {sembol_yorumu}</font>"
        elif _aktif_mod == "bireysel_natal":
            sentez = f"👁️‍🗨️ <b>Sabian Şifresi ({sabian_derece}°):</b> <i>\"{sembol_vizyonu}\"</i><br/>"
            sentez += f"<font color='#555555'><b>Mühür:</b> {gez_fitrat}, bu vizyonla mühürlenmiştir. {sembol_yorumu}</font>"
        else:
            sentez = f"👁️‍🗨️ <b>Sabian Şifresi ({sabian_derece}°):</b> <i>\"{sembol_vizyonu}\"</i><br/>"
            sentez += f"<font color='#555555'><b>Mühür:</b> Partnerinizin {gez_fitrat}, bu vizyonla mühürlenmiştir. {sembol_yorumu}</font>"
        
        return sentez
   
    def get_kadersel_durak(self):
        bugun = datetime.now()
        iliski_suresi = (bugun - self.event_date).days / 365.25
        
        if self.mod == "ebeveyn_cocuk":
            if iliski_suresi < 2: 
                return "🌱 Keşif ve Bağlanma Fazı (Yeni Doğan - 2 Yaş): Bu dönemde ebeveyn ve çocuk birbirlerinin enerjisini, ihtiyaçlarını ve iletişim dilini keşfeder. Bağlanma kalıpları oluşur, güven temeli atılır. Krizlerden ziyade, karşılıklı uyum ve sezgisel bağın güçlendirilmesi önceliklidir."
            elif 2 <= iliski_suresi < 7: 
                return "⚙️ Sınır ve Bağımsızlık Fazı (2 - 7 Yaş): Çocuğun kendi benliğini keşfetmeye başladığı, sınırların test edildiği bir dönem. 'Neden?' soruları artar, bağımsızlık ihtiyacı güçlenir. Ebeveynin sabır ve net sınırlarla yaklaşması, çocuğun kendine güveninin gelişmesinin temelini atar."
            else: 
                return "🏛️ Olgunlaşma ve Rehberlik Fazı (7 Yaş Üstü): Çocuk artık kendi kararlarını verebilecek olgunluğa ulaşır. Ebeveyn-çocuk ilişkisi yönlendirmeden rehberliğe, otoriteden danışmanlığa dönüşür. Birlikte öğrenme, paylaşma ve karşılıklı saygı bu dönemin en değerli kazanımlarıdır."
        else:
            if iliski_suresi < 2: 
                return "🌱 Çıraklık Aşaması (Kadersel Yeni Ay): İlişkiniz henüz kurulum fazında. Birbirinizin enerjisine, vektörel hızına ve dünyevi vitrinlerine uyumlanma sürecindesiniz. Bu dönemde krizlerden ziyade, birbirini keşfetmenin o büyüleyici ve illüzyonlu akışı devrededir."
            elif 2 <= iliski_suresi < 7: 
                return "⚙️ Kalfalık Aşaması (Sabir Testi): İlişkiniz artık başlangıçtaki o illüzyonlu 'Yeni Ay' fazından çıkmış ve gerçek bir motor gibi yük taşımaya başlamıştır. FAST tekniğinde 'Bağ Gücü', iliskinin yokus çıkabilme gücüdür. Bu dönemde yaşadığınız krizler, kavgalar veya ego çarpışmaları ilişkinin kötüye gittiğini değil; aksine 'vites kutusunun' test edildiğini gösterir. Göreviniz birbirinizle savaşmak değil, aranızdaki bu yüksek sürtünmeyi (krizi) kalıcı bir üretim ilerlemesine (çözüme) dönüştürmektir."
            else: 
                return "🏛️ Ustalık Aşaması (Fraktal Büyüme): İlişkiniz tüm ağır sabir testlerinden ve Satürn döngülerinden sağ çıkarak kendi sarsılmaz imparatorluğunu kurmuştur. Artık aranızdaki bağ, ufak krizlerle sarsılmayacak kadar köklenmiş ve Altın Oran'ın o çabasız, koruyucu titresimına yerleşmiştir."

    def calculate_bagil_tarihler(self):
        import swisseph as swe
        from datetime import datetime
        
        j_ileri, j_geri = self.get_julian_dates()
        
        # 4. GÖRSEL VE PDF İÇİN KUSURSUZ TARİH YAZDIRMA
        # Doğrudan kilitlenmiş astronomik JD üzerinden Jülyen tarihlerini çekiyoruz.
        y1, m1, d1, _ = swe.revjul(j_ileri, swe.JUL_CAL)
        y2, m2, d2, _ = swe.revjul(j_geri, swe.JUL_CAL)
        
        # Astronomik Yıldan Tarihsel Yıla Çevrim (0 = 1 M.Ö.)
        ileri_str = f"{int(d1):02d}.{int(m1):02d}.{abs(y1)+1:04d} M.Ö." if y1 <= 0 else f"{int(d1):02d}.{int(m1):02d}.{y1:04d} M.S."
        geri_str = f"{int(d2):02d}.{int(m2):02d}.{abs(y2)+1:04d} M.Ö." if y2 <= 0 else f"{int(d2):02d}.{int(m2):02d}.{y2:04d} M.S."
        
        # Arayüzdeki diğer fonksiyonlar çökmesin diye sahte obje gönderiyoruz
        dummy_date = datetime(1, 1, 1)
        return dummy_date, ileri_str, dummy_date, y2, geri_str

    def calculate_altin_oran_muhru(self):
        ks_yil = self.calculate_ks()
        phi = 1.618033988749895
        uyum_sapmasi = ks_yil % phi
        fibonacci_sayilari = [1, 2, 3, 5, 8, 13, 21, 34, 55]
        en_yakin_fib = min(fibonacci_sayilari, key=lambda x: abs(x - ks_yil))
        
        if self.mod == "ebeveyn_cocuk":
            if abs(ks_yil - en_yakin_fib) < 0.3: 
                return f"Ebeveyn ve çocuk arasındaki {ks_yil:.2f} yıllık zaman farkı, kozmik bir harmoni içinde. En ağır krizlerde bile bu bağ kendini otomatik olarak onarır. Birbirinden kopma neredeyse imkansız; evren bu bağı koruma altına almış."
            elif uyum_sapmasi < 0.2 or uyum_sapmasi > 1.4: 
                return f"{ks_yil:.2f} yıllık fark, doğal bir ritim ve uyum dalgasına sahip. Birçok sorun konuşulmadan, sezgisel bir şekilde çözülebilir. Arada sessiz bir telepati, bir akış var."
            else: 
                return f"{ks_yil:.2f} yıllık fark, doğal bir koruma kalkanı oluşturmamış. Bu bir eksiklik değil; tam tersine, ilişkide ne ekilirse aynısının biçileceği anlamına gelir. Evren kadersel bir torpille kurtarmaz ama haksız yere de cezalandırmaz. İlişkinin mimarisi tamamen size ait."
        else:
            if abs(ks_yil - en_yakin_fib) < 0.3: 
                return f"Aranizdaki {ks_yil:.2f} yillik vektorsel yas farki, kozmik bir harmoni icinde. En agir krizlerde bile bu bag kendini otomatik olarak onarir. Birbirinizden kopmaniz neredeyse imkansiz; evren bu iliskiyi koruma altina almis."
            elif uyum_sapmasi < 0.2 or uyum_sapmasi > 1.4: 
                return f"{ks_yil:.2f} yillik yas farkiniz, dogal bir ritim ve uyum dalgasina sahip. Bir cok sorunu konusmadan, sezgisel bir sekilde cozmeniz mumkun. Aranizda sessiz bir telepati, bir akis var."
            else: 
                return f"{ks_yil:.2f} yillik yas farkiniz, dogal bir koruma kalkani olusturmamis. Bu bir eksiklik degil; tam tersine, iliskinizde ne ekerseniz aynisini bieceginiz anlamina gelir. Evren sizi kadersel bir torpille kurtarmaz ama haksiz yere de cezalandirmaz. Iliskinin mimari tamamen size ait."

    def gezegen_konumu_bul(self, julian_gun, gezegen_id):
        try:
            # 1. STANDART BAYRAKLAR
            bayraklar = swe.FLG_SWIEPH | swe.FLG_SPEED
            
            # 2. ASTEROİD ZIRHI: Eğer ID 10000'den büyükse (Juno, Ceres vb.) analitik hesaba geç
            if gezegen_id > 10000:
                bayraklar = swe.FLG_MOSEPH | swe.FLG_SPEED

            # 3. GAD ÖZEL HESAPLAMASI
            if gezegen_id == 999:
                konum, _ = swe.calc_ut(julian_gun, swe.MEAN_NODE, bayraklar)
                derece = (konum[0] + 180) % 360
                hiz = konum[3] 
            else:
                konum, _ = swe.calc_ut(julian_gun, gezegen_id, bayraklar)
                derece = konum[0]
                hiz = konum[3]
                
            burclar = ["Koc", "Boga", "Ikizler", "Yengec", "Aslan", "Basak", "Terazi", "Akrep", "Yay", "Oglak", "Kova", "Balik"]
            burc = burclar[int(derece // 30)]
            
            if hiz < 0 and gezegen_id not in [swe.SUN, swe.MOON, 999]: 
                return f"{burc} (Rx)"
            else: 
                return burc
                
        except Exception as e: 
            print(f"⚠️ KADERSEL MOTOR UYARISI: ID {gezegen_id} hesaplanamadı! Hata: {e}")
            return None

    def yukselen_bul(self, julian_gun):
        try:
            cusps, ascmc = swe.houses(julian_gun, self.enlem, self.boylam, b'P')
            burclar = ["Koc", "Boga", "Ikizler", "Yengec", "Aslan", "Basak", "Terazi", "Akrep", "Yay", "Oglak", "Kova", "Balik"]
            return burclar[int(ascmc[0] // 30)]
        except Exception: return "Hesaplanamadi"

    def calculate_tork(self):
        v_b = self.calculate_ks()
        j1 = swe.julday(self.p1.year, self.p1.month, self.p1.day, 12.0)
        j2 = swe.julday(self.p2.year, self.p2.month, self.p2.day, 12.0)
        e_a = 1.0 
        for gezegen, gid in GEZEGENLER.items():
            if gid == 999: continue
            try:
                d1 = swe.calc_ut(j1, gid)[0][0]
                d2 = swe.calc_ut(j2, gid)[0][0]
                aci_farki = abs(d1 - d2)
                if aci_farki > 180: aci_farki = 360 - aci_farki
                if abs(aci_farki - 137.5) < 5 or abs(aci_farki - 222.5) < 5: e_a += 2.5 
                elif aci_farki < 10: e_a += 1.5 
                elif abs(aci_farki - 90) < 5: e_a += 2.0 
                elif abs(aci_farki - 180) < 10: e_a += 1.0 
            except Exception:
                pass
        k_i = (v_b * e_a) + 10.0
        tork_skoru = min(k_i * 3.141592653589793, 100.0) 
        if tork_skoru > 85: durum = "Iliskiniz kendi kendini besleyen, kendi enerjisini ureten nadir bir yapiya sahip. Dissa bagimlilik yok, kendi icinizden gelen guclu bir motor var."
        elif tork_skoru > 60: durum = "Iliskiniz dik yokuclari kolayca asan guclu bir arac gibi. Zorluklara karsi dayanikli, ilerlemeli ve kararli."
        elif tork_skoru > 35: durum = "Iliskiniz bir nehir gibi dogal akisinda ilerliyor. Huzurlu, dengeli ve kendi ritmini bulmus."
        else: durum = "Iliskiniz derin bir arinma ve ic donusum doneminde. Yavas ama anlamlı bir surecten geciyorsunuz."
        return f"Guc Skoru: {tork_skoru:.1f}/100 - {durum}"

    def sinastri_hesapla(self, sessiz=False):
        """
        İki harita arasındaki sinastri açılarını hesaplar ve yorumlar.
        """
        import swisseph as swe
        from datetime import datetime, date

        if not sessiz:
            print("MOTOR TESTİ: Sinastri Hesaplama Fonksiyonu Tetiklendi!")
        
        # 1. DÜZELTME: Doğum tarihlerinden Julian Date'leri kendimiz üretiyoruz
        try:
            d1 = self.p1 if isinstance(self.p1, date) else datetime.strptime(str(self.p1), "%Y-%m-%d").date()
            d2 = self.p2 if isinstance(self.p2, date) else datetime.strptime(str(self.p2), "%Y-%m-%d").date()
            j1 = swe.julday(d1.year, d1.month, d1.day, 12.0)
            j2 = swe.julday(d2.year, d2.month, d2.day, 12.0)
        except Exception:
            j1, j2 = swe.julday(2000, 1, 1, 12.0), swe.julday(2000, 1, 1, 12.0)

        gezegenler_listesi = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter", "Satürn", "Uranüs", "Neptün", "Plüton", "KAD", "Chiron", "Juno", "Ceres", "Pallas", "Vesta", "Eros", "Psyche", "Sappho", "Amor"]
        
        # 2. DÜZELTME: Eksik olan GEZEGENLER ID sözlüğünü lokal olarak ekledik
        gezegen_id_haritasi = {
            "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS, 
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN, "Uranüs": swe.URANUS, 
            "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO, "KAD": swe.MEAN_NODE, "Chiron": 15,
            "Juno": swe.AST_OFFSET + 3, "Ceres": swe.AST_OFFSET + 1,
            "Pallas": swe.AST_OFFSET + 2, "Vesta": swe.AST_OFFSET + 4,
            "Eros": swe.AST_OFFSET + 433, "Psyche": swe.AST_OFFSET + 16,
            "Sappho": swe.AST_OFFSET + 80, "Amor": swe.AST_OFFSET + 1221
        }

        sinastri_verileri = []
        receteler = []
        
        # Açı Tipleri ve Orb Değerleri
        aci_tipleri = {
            0: {"isim": "Kavuşum", "etki": "Güçlü Birleşme", "puan": 10},
            180: {"isim": "Karşıt", "etki": "Farkındalık/Gerilim", "puan": -5},
            90: {"isim": "Kare", "etki": "Mücadele/Dinamizm", "puan": -8},
            120: {"isim": "Üçgen", "etki": "Doğal Akış/Şans", "puan": 8},
            60: {"isim": "Sekstil", "etki": "Fırsat/Uyum", "puan": 5}
        }
        
        if self.mod == "ebeveyn_cocuk":
            GEZEGEN_ANLAMLARI = {
                "Güneş": "kimlik, benlik gelişimi ve hayati güç",
                "Ay": "duygusal dünya, beslenme ihtiyacı ve içgüdü",
                "Merkür": "iletişim, öğrenme süreci ve zihinsel gelişim",
                "Venüs": "değerler, sevgi dili ve estetik algı",
                "Mars": "eylem cesareti, bağımsızlık enerjisi ve öfke yönetimi",
                "Jüpiter": "genişleme, bolluk ve bilgelik arayışı",
                "Satürn": "yapı, sorumluluk ve disiplin ihtiyacı",
                "Uranüs": "özgürlük arzusu, yenilik ve isyan enerjisi",
                "Neptün": "hayal gücü, maneviyat ve kırılganlık",
                "Plüton": "dönüşüm, güç yapiylari ve yeniden doğum",
                "KAD": "kader misyonu, ruhsal yön ve hayat dersi",
                "GAD": "gerçek benlik, içsel rehberlik ve Potansiyel",
                "Chiron": "şifa, yara bilgeliği ve merhamet",
                "Juno": "bağlanma tarzı, taahhüt ve güven ihtiyacı",
                "Ceres": "beslenme, koruma içgüdüsü ve annelik enerjisi",
                "Pallas": "stratejik zeka, yaratıcı çözüm ve vizyon",
                "Vesta": "içsel odak, kutsal bağlılık ve kararlılık",
                "Eros": "tutku, arzu yoğunluğu ve eylem enerjisi",
                "Psyche": "ruhsal derinlik, kırılganlık ve bilinçdışı",
                "Sappho": "hassasiyet, estetik algı ve duygusal derinlik",
                "Amor": "koşulsuz sevgi, kabul ve kalp bağlanması",
            }
        else:
            GEZEGEN_ANLAMLARI = {
                "Güneş": "öz-bilinç, kimlik ve hayati güç",
                "Ay": "duygusal dünya, içgüdü ve beslenme",
                "Merkür": "iletişim, zihinsel alışveriş ve merak",
                "Venüs": "sevgi dili, estetik ve değerler",
                "Mars": "tutku, eylem cesareti ve fiziksel çekim",
                "Jüpiter": "genişleme, bolluk ve ruhsal büyüme",
                "Satürn": "yapı, sorumluluk ve kalıcı bağlılık",
                "Uranüs": "özgürlük, yenilik ve ani değişimler",
                "Neptün": "maneviyat, hayal gücü ve koşulsuz sevgi",
                "Plüton": "dönüşüm, güç ve ruhsal yeniden doğum",
                "KAD": "kader düğümü, ruhsal misyon ve karmik bağ",
                "GAD": "gerçek benlik, ruhsal rehberlik ve içsel ışık",
                "Chiron": "şifa, kırılganlık ve merhamet",
                "Juno": "evlilik sadakati, ortaklık ve taahhüt",
                "Ceres": "besleme, koruma ve annelik enerjisi",
                "Pallas": "stratejik zeka, yaratıcı çözüm ve vizyon",
                "Vesta": "adhara, kutsal odak ve içsel ateş",
                "Eros": "arfzunun derinliği, cinsel çekim ve tutku",
                "Psyche": "ruhsal derinlik, kırılganlık ve bilinçdışı bağ",
                "Sappho": "şiirsel hassasiyet, estetik tutku ve duygusal derinlik",
                "Amor": "koşulsuz sevgi, romantik kader ve kalp bağlanması",
            }
        
        if self.mod == "ebeveyn_cocuk":
            ACI_DINAMIKLERI = {
                0: {
                    "baslik": "Bu iki enerji birleşerek ortak bir gelişim alanı yaratıyor",
                    "aciklama": "Bu kavuşumda, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi aynı noktada birleşmiş. Bu birleşme, ebeveyn-çocuk bağında {konu} alanında güçlü bir etki yaratıyor. Birbirinizin bu alandaki güçlü ve zayıf yönlerini tamamlıyorsunuz.",
                    "konu_map": {
                        "Güneş": "kimlik ve benlik gelişimi", "Ay": "duygusal bağ ve beslenme",
                        "Merkür": "iletişim ve öğrenme", "Venüs": "değerler ve sevgi dili",
                        "Mars": "bağımsızlık ve eylem", "Jüpiter": "genişleme ve bilgelik",
                        "Satürn": "yapı ve disiplin", "Uranüs": "özgürlük ve yenilik",
                        "Neptün": "hayal gücü ve maneviyat", "Plüton": "dönüşüm ve güç",
                    }
                },
                180: {
                    "baslik": "Bu iki enerji zıt kutuplarda birbirini tamamlıyor",
                    "aciklama": "Bu karşıtlıkta, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi zıt kutuplarda duruyor. Bu zıtlık, ebeveyn-çocuk bağında {konu} alanında sürekli bir gerilim ve farkındalık yaratıyor. Zıt yönlerinizi kabul etmek, bu enerjiyi yapıcıya dönüştürmenin anahtarıdır.",
                    "konu_map": {
                        "Güneş": "kimlik ve benlik", "Ay": "duygusal ihtiyaçlar",
                        "Merkür": "iletişim ve düşünce tarzı", "Venüs": "değer algısı",
                        "Mars": "bağımsızlık ve eylem", "Jüpiter": "genişleme ve inanç",
                        "Satürn": "yapı ve sorumluluk", "Uranüs": "özgürlük ve değişim",
                        "Neptün": "gerçek ve hayal", "Plüton": "güç ve kontrol",
                    }
                },
                90: {
                    "baslik": "Bu iki enerji arasında yapıcı bir mücadele var",
                    "aciklama": "Bu kare açıda, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi arasında sürekli bir gerilim ve itme-çekme dinamiği var. Bu mücadele, ebeveyn-çocuk bağında {konu} alanında büyütücü bir baskı yaratıyor. Bu enerjiyi kanalize etmek için ortak bir hedef belirlemek en sağlıklı yoldur.",
                    "konu_map": {
                        "Güneş": "ego ve benlik", "Ay": "duygusal güvenlik",
                        "Merkür": "anlama ve anlaşma", "Venüs": "değer ve kabul",
                        "Mars": "bağımsızlık ve eylem", "Jüpiter": "inanç ve genişleme",
                        "Satürn": "sorumluluk ve yapı", "Uranüs": "özgürlük ve rutin",
                        "Neptün": "gerçeklik ve hayal", "Plüton": "güç ve kontrol",
                    }
                },
                120: {
                    "baslik": "Bu iki enerji arasında doğal bir uyum akışı var",
                    "aciklama": "Bu üçgende, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi arasında doğal bir uyum ve akış var. Bu trio, ebeveyn-çocuk bağında {konu} alanında şans ve kolaylık yaratıyor. Birbirinizin bu alandaki güçlü yönlerini destekliyorsunuz.",
                    "konu_map": {
                        "Güneş": "benlik ifadesi ve güç", "Ay": "duygusal akış ve beslenme",
                        "Merkür": "iletişim ve zihinsel uyum", "Venüs": "değerler ve estetik",
                        "Mars": "bağımsızlık ve eylem uyumu", "Jüpiter": "büyüme ve neşe",
                        "Satürn": "yapı ve destek", "Uranüs": "özgürlük ve yenilik",
                        "Neptün": "maneviyat ve ilham", "Plüton": "dönüşüm ve derinlik",
                    }
                },
                60: {
                    "baslik": "Bu iki enerji arasında yapıcı bir fırsat bağı var",
                    "aciklama": "Bu sekstilde, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi arasında yapıcı bir fırsat ve destek bağı var. Bu uyum, ebeveyn-çocuk bağında {konu} alanında yeni kapılar açıyor. Bu fırsatı değerlendirmek için birlikte adım atmanız yeterli.",
                    "konu_map": {
                        "Güneş": "benlik ve ifade", "Ay": "duygusal destek ve beslenme",
                        "Merkür": "iletişim ve öğrenme", "Venüs": "değerler ve güzellik",
                        "Mars": "bağımsızlık ve cesaret", "Jüpiter": "büyüme ve bolluk",
                        "Satürn": "yapı ve disiplin", "Uranüs": "yenilik ve özgürlük",
                        "Neptün": "ilham ve maneviyat", "Plüton": "dönüşüm ve güçlenme",
                    }
                },
            }
        else:
            ACI_DINAMIKLERI = {
                0: {
                    "baslik": "Bu iki enerji birleşerek ortak bir güç yaratıyor",
                    "aciklama": "Bu kavuşumda, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi aynı noktada birleşmiş. Bu birleşme, ilişkinizde {konu} alanında güçlü bir etki yaratıyor. Birbirinizin bu alandaki güçlü ve zayıf yönlerini tamamlıyorsunuz.",
                    "konu_map": {
                        "Güneş": "öz-bilinç ve ifade", "Ay": "duygusal bağ ve beslenme",
                        "Merkür": "iletişim ve anlama", "Venüs": "sevgi ve değerler",
                        "Mars": "tutku ve eylem", "Jüpiter": "büyüme ve bolluk",
                        "Satürn": "yapı ve taahhüt", "Uranüs": "özgürlük ve yenilik",
                        "Neptün": "maneviyat ve hayaller", "Plüton": "dönüşüm ve güç",
                    }
                },
                180: {
                    "baslik": "Bu iki enerji zıt kutuplarda birbirini tamamlıyor",
                    "aciklama": "Bu karşıtlıkta, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi zıt kutuplarda duruyor. Bu zıtlık, ilişkinizde {konu} alanında sürekli bir gerilim ve farkındalık yaratıyor. Zıt yönlerinizi kabul etmek, bu enerjiyi yapıcıya dönüştürmenin anahtarıdır.",
                    "konu_map": {
                        "Güneş": "öz-benlik ve ifade tarzı", "Ay": "duygusal ihtiyaçlar",
                        "Merkür": "iletişim ve düşünce tarzı", "Venüs": "sevgi ve değer algısı",
                        "Mars": "eylem ve tutku dili", "Jüpiter": "genişleme ve inanç",
                        "Satürn": "yapı ve sorumluluk", "Uranüs": "özgürlük ve değişim",
                        "Neptün": "gerçek ve hayal", "Plüton": "güç ve kontrol",
                    }
                },
                90: {
                    "baslik": "Bu iki enerji arasında yapıcı bir mücadele var",
                    "aciklama": "Bu kare açıda, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi arasında sürekli bir Gerilim ve itme-çekme dinamiği var. Bu mücadele, ilişkinizde {konu} alanında büyütücü bir baskı yaratıyor. Bu enerjiyi kanalize etmek için ortak bir hedef belirlemek en sağlıklı yoldur.",
                    "konu_map": {
                        "Güneş": "ego ve benlik", "Ay": "duygusal güvenlik",
                        "Merkür": "anlama ve anlaşma", "Venüs": "sevgi ve değer",
                        "Mars": "eylem ve tutku", "Jüpiter": "inanç ve genişleme",
                        "Satürn": "sorumluluk ve yapı", "Uranüs": "özgürlük ve rutin",
                        "Neptün": "gerçeklik ve hayal", "Plüton": "güç ve kontrol",
                    }
                },
                120: {
                    "baslik": "Bu iki enerji arasında doğal bir uyum akışı var",
                    "aciklama": "Bu üçgende, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi arasında doğal bir uyum ve akış var. Bu trio, ilişkinizde {konu} alanında şans ve kolaylık yaratıyor. Birbirinizin bu alandaki güçlü yönlerini destekliyorsunuz.",
                    "konu_map": {
                        "Güneş": "öz-ifade ve güç", "Ay": "duygusal akış ve beslenme",
                        "Merkür": "iletişim ve zihinsel uyum", "Venüs": "sevgi ve estetik",
                        "Mars": "tutku ve eylem uyumu", "Jüpiter": "büyüme ve neşe",
                        "Satürn": "yapı ve destek", "Uranüs": "özgürlük ve yenilik",
                        "Neptün": "maneviyat ve ilham", "Plüton": "dönüşüm ve derinlik",
                    }
                },
                60: {
                    "baslik": "Bu iki enerji arasında yapıcı bir fırsat bağı var",
                    "aciklama": "Bu sekstilde, {p1}'in {anlam1} enerjisi ile {p2}'in {anlam2} enerjisi arasında yapıcı bir fırsat ve destek bağı var. Bu uyum, ilişkinizde {konu} alanında yeni kapılar açıyor. Bu fırsatı değerlendirmek için birlikte adım atmanız yeterli.",
                    "konu_map": {
                        "Güneş": "öz-güç ve ifade", "Ay": "duygusal destek ve beslenme",
                        "Merkür": "iletişim ve öğrenme", "Venüs": "sevgi ve güzellik",
                        "Mars": "tutku ve cesaret", "Jüpiter": "büyüme ve bolluk",
                        "Satürn": "yapı ve disiplin", "Uranüs": "yenilik ve özgürlük",
                        "Neptün": "ilham ve maneviyat", "Plüton": "dönüşüm ve güçlenme",
                    }
                },
            }

        # Gezegen derecelerini önceden hesapla
        p1_pos = {}
        p2_pos = {}
        
        for g in gezegenler_listesi:
            try:
                gid = gezegen_id_haritasi.get(g)
                if gid is not None:
                    try:
                        flags = get_safe_flags(gid)
                        p1_pos[g] = swe.calc_ut(j1, gid, flags)[0][0]
                        p2_pos[g] = swe.calc_ut(j2, gid, flags)[0][0]
                    except Exception:
                        tahmini = asteroit_tahmini_derece(g, j1)
                        if tahmini is not None:
                            p1_pos[g] = tahmini
                            p2_pos[g] = asteroit_tahmini_derece(g, j2)
            except Exception as e:
                if not sessiz: print(f"UYARI: {g} hesaplanamadı ({e})")
                continue

        # Çapraz Açı Kontrolü
        for g1 in gezegenler_listesi:
            for g2 in gezegenler_listesi:
                if g1 not in p1_pos or g2 not in p2_pos: continue
                
                d1 = p1_pos[g1]
                d2 = p2_pos[g2]
                
                fark = abs(d1 - d2)
                if fark > 180: fark = 360 - fark
                
                for aci_deg, aci_info in aci_tipleri.items():
                    orb = abs(fark - aci_deg)
                    if orb <= 5.0: # 5 derece orb
                        burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
                        burc1 = burclar[int(d1 / 30) % 12]
                        burc2 = burclar[int(d2 / 30) % 12]
                        
                        # --- FBST SİNASTRİ YORUMLARI (dış dosyadan) ---
                        fbst_yorumlar = FBST_SINASTRI_OZEL if FBST_SINASTRI_OZEL else {}

                        g_key = f"{g1}-{g2}"
                        alt_key = f"{g2}-{g1}"

                        ozel_yorum = ""
                        if self.mod == "ebeveyn_cocuk" and FBST_YORUMLAR_EBEVEYN:
                            if g_key in FBST_YORUMLAR_EBEVEYN and aci_deg in FBST_YORUMLAR_EBEVEYN[g_key]:
                                ozel_yorum = FBST_YORUMLAR_EBEVEYN[g_key][aci_deg]
                            elif alt_key in FBST_YORUMLAR_EBEVEYN and aci_deg in FBST_YORUMLAR_EBEVEYN[alt_key]:
                                ozel_yorum = FBST_YORUMLAR_EBEVEYN[alt_key][aci_deg]
                        if not ozel_yorum:
                            if g_key in fbst_yorumlar and aci_deg in fbst_yorumlar[g_key]:
                                ozel_yorum = fbst_yorumlar[g_key][aci_deg]
                            elif alt_key in fbst_yorumlar and aci_deg in fbst_yorumlar[alt_key]:
                                ozel_yorum = fbst_yorumlar[alt_key][aci_deg]
                        
                        if ozel_yorum:
                            if self.mod == "ebeveyn_cocuk":
                                yorum = f"<b>{self.p1_isim} {g1} & {self.p2_isim} {g2} {aci_info['isim']} Dersi:</b> {ozel_yorum}"
                            else:
                                yorum = f"<b>{self.p1_isim} {g1} & {self.p2_isim} {g2} {aci_info['isim']} Mührü:</b> {ozel_yorum}"
                        else:
                            p1_anlam = GEZEGEN_ANLAMLARI.get(g1, "enerji")
                            p2_anlam = GEZEGEN_ANLAMLARI.get(g2, "enerji")
                            aci_yapi = ACI_DINAMIKLERI.get(aci_deg, ACI_DINAMIKLERI[0])
                            if self.mod == "ebeveyn_cocuk":
                                konu = aci_yapi["konu_map"].get(g1, aci_yapi["konu_map"].get(g2, "ebeveyn-çocuk bağının temel yapiylari"))
                            else:
                                konu = aci_yapi["konu_map"].get(g1, aci_yapi["konu_map"].get(g2, "ilişkinin temel yapiylari"))
                            zengin_yorum = aci_yapi["aciklama"].format(
                                p1=self.p1_isim, p2=self.p2_isim,
                                anlam1=p1_anlam, anlam2=p2_anlam, konu=konu
                            )
                            if self.mod == "ebeveyn_cocuk":
                                yorum = f"<b>{self.p1_isim} {g1} ({burc1}) & {self.p2_isim} {g2} ({burc2}) {aci_info['isim']} Dersi:</b> {zengin_yorum}"
                            else:
                                yorum = f"<b>{self.p1_isim} {g1} ({burc1}) & {self.p2_isim} {g2} ({burc2}) {aci_info['isim']} Teması:</b> {zengin_yorum}"
                        
                        sinastri_verileri.append(yorum)
                        
                        # --- GELİŞTİRİLMİŞ ŞİFA REÇETELERİ ---
                        fbst_receteler = {
                        "Güneş-Güneş-0": "Öneri: İkinizin de benzer enerji titresimlarında titreştiği bu kavuşumda, birlikte güneş doğumu meditasyonu yaparak ortak niyetlerinizi güçlendirin. Her sabah 10 dakika gözlerinizi kapatarak içsel ışığınızın birleşmesini hayal edin ve ardından ortak bir hedefinizi journal'a yazın. Bu ritüeli 21 gün boyunca her sabah tekrarlayarak birlikteliğinizin temel enerjisini yeniden kodlayın.",
                        "Güneş-Güneş-60": "Öneri: Benzer ama farklı yollarda yürüyen bu uyumlu enerjiyi korumak için haftada bir kez 'İçsel Işık Paylaşımı' seansı düzenleyin. Birbirinizin güçlü yönlerini yüksek sesle takdir ederek başlayın, ardından ortak bir yürüyüşe çıkın ve yürüyüş sırasında birbirinize ilham veren hikayeler anlatın. Bu pratik, doğal uyumunuzu bilinçli bir şekilde besleyerek ilişkinizin akışını koruyacaktır.",
                        "Güneş-Güneş-90": "Öneri: Birbirinizin egosunu zorlayan bu gerilimli açıyı çözmek için şu 3 adımı uygulayın: 1) Haftada iki kez 'Gölge Yansıtma' oturumu yapın ve birbirinizin davranışlarında hoşunuza gitmeyen yönleri kendi içinizde arayın.\n2) Güç mücadelesine dönüşen anlarda hemen durun ve sesli nefes egzersizi yapın.\n3) Ortak bir yaratıcı projeye yönelerek rekabet enerjisini işbirliğine dönüştürün.",
                        "Güneş-Güneş-120": "Öneri: Doğal akışı ve uyumu korumak için bu trine enerjisini bilinçli şekilde besleyin. Her ay birlikte yeni bir deneyim planlayın ve bu deneyim sırasında birbirinizin rehberliğine güvenme pratiği yapın. Birlikte doğada yürüyerek ve birbirinizin hikayelerini dinleyerek bu doğal bağınızı derinleştirin.",
                        "Güneş-Güneş-180": "Öneri: Zıtlıklarınızı dengelemek için ayna meditasyonu yapın: karşılıklı oturun ve 5 dakika boyunca birbirinizin gözlerinin içine bakarak nefes alın. Ardından birbirinizin en güçlü ve en zayıf yönlerini yüksek sesle kabul edin. Son olarak, ortak bir vizyon belgesi oluşturun ve zıt yönlerinizi bu vizyonun tamamlayıcı parçaları olarak yeniden tanımlayın.",
                        "Güneş-Ay-0": "Öneri: Güneş'in aktif enerjisi ile Ay'ın duygusal derinliğinin kavuştuğu bu noktada, birlikte ay döngüsü takibi yapın. Her yeni ayda ortak duygusal niyetler belirleyin ve dolunayda bu niyetleri serbest bırakma ritüeli düzenleyin. Ay'ın fazlarına göre meditasyon sürelerinizi ayarlayın ve birbirinizin duygusal ihtiyaçlarını bu ritüeller aracılığıyla daha iyi anlayın.",
                        "Güneş-Ay-60": "Öneri: Güneş'in ışığı ile Ay'ın yumuşaklığının uyumlu dansını korumak için akşam rutinleri oluşturun. Her akşam yemekten sonra birlikte çay içerek günün duygusal iniş çıkışlarını paylaşın. Birbirinize 'Bugün seni en çok ne etkiledi?' diye sorun ve dinlerken tamamen var olun. Bu sadelik, doğal uyumunuzu besleyerek duygusal bağınızı güçlendirecektir.",
                        "Güneş-Ay-90": "Öneri: Güneş'in egosu ile Ay'ın duygusal hassasiyeti arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal tetiklenme anında 'Durdur ve Hisset' tekniğini kullanın: 3 derin nefes alın ve duyguyu bedeninizde nerede hissettiğinizi fark edin.\n2) Birbirinizin duygusal dilini öğrenmek için haftada bir 'Duygu Haritası' paylaşımı yapın.\n3) Ortak bir şifa banyosu düzenleyin ve suyun arındırıcı enerjisinde birbirinizi affedin.",
                        "Güneş-Ay-120": "Öneri: Güneş'insıcakluğu ile Ay'ın besleyiciliğinin doğal uyumunu korumak için birlikte yemek pişirme ritüeli oluşturun. Her hafta birlikte yeni bir tarif deneyin ve pişirirken birbirinizin duygusal ihtiyaçlarını konuşun. Yemek yerken şükran pratiği yaparak bu doğal besleyici enerjiyi bilinçli şekilde besleyin.",
                        "Güneş-Ay-180": "Öneri: Güneş'in dışa dönüklüğü ile Ay'ın içe dönüklüğü arasındaki zıtlığı dengelemek için 'Değişim Günü' pratiği yapın. Bir gün Güneş'in enerjisini takip edin (dış mekanlarda aktif olun), ertesi gün Ay'ın enerjisini takip edin (içe dönük meditasyon ve duygusal çalışma yapın). Ardından bu deneyimleri paylaşarak zıt kutuplarınızın birbirini nasıl tamamladığını keşfedin.",
                        "Güneş-Merkür-0": "Öneri: Güneş'in güç enerjisi ile Merkür'ün iletişim becerilerinin kavuştuğu bu noktada, birlikte bilinçli iletişim pratiği yapın. Her sabah 5 dakika boyunca birbirinize günün niyetini yüksek sesle söyleyin ve ardından birlikte journal'a yazın. Bu ritüel, zihinsel netliğinizi ve iletişim kalitenizi artırarak ortak vizyonunuzu güçlendirecektir.",
                        "Güneş-Merkür-60": "Öneri: Güneş'in ışığı ile Merkür'ün zekasının uyumlu dansını korumak için haftada bir 'Bilgi Paylaşımı' oturumu düzenleyin. Birbirinize bu hafta öğrendiğiniz yeni bir şeyi anlatın ve ardından birlikte bu konuyu tartışın. Zihinsel alışverişlerinizi destekleyen bu pratik, doğal uyumunuzu besleyerek entelektüel bağınızı derinleştirin.",
                        "Güneş-Merkür-90": "Öneri: Güneş'in baskın enerjisi ile Merkür'ün hızlı zihni arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) İletişimde 'Dinleme Molası' verin: her konuştuğunuzda 3 saniye durupdoğruın sözünü bitirmesini bekleyin.\n2) Düşüncelerinizi journal'a yazarak zihinsel karmaşayı dağıtın.\n3) Birlikte sesli kitap okuyarak iletişim tarzlarınızı senkronize edin.",
                        "Güneş-Merkür-120": "Öneri: Güneş'insıcakluğu ile Merkür'ün netliğinin doğal akışını korumak için birlikte okuma saati düzenleyin. Her akşam 20 dakika boyunca aynı kitabı okuyun ve ardından birbirinize düşüncelerinizi paylaşın. Bu ortak entelektüel deneyim, zihinsel bağınızı güçlendirerek iletişiminizi derinleştirecektir.",
                        "Güneş-Merkür-180": "Öneri: Güneş'in dışa dönüklüğü ile Merkür'ün içe dönüklüğü arasındaki zıtlığı dengelemek için 'İletişim Dansı' pratiği yapın: bir gün sadece dinleyin, ertesi gün sadece anlatın. Ardından bu deneyimleri paylaşarak iletişim tarzlarınızdaki zıtlıkların aslında birbirinizi nasıl tamamladığını keşfedin. Bu pratik, zihinsel ve duygusal köprülerinizi güçlendirecektir.",
                        "Güneş-Venüs-0": "Öneri: Güneş'in güç enerjisi ile Venüs'ün sevgi enerjisinin kavuştuğu bu noktada, birlikte güzellik ve sevgi ritüelleri oluşturun. Her sabah birbirinize sevgi dolu bir mesaj yazın ve akşam birlikte güzel bir müzik dinleyerek dans edin. Bu ritüel, ilişkinizin sevgi titresimını yükselterek romantik bağınızı besleyecektir.",
                        "Güneş-Venüs-60": "Öneri: Güneş'in ışığı ile Venüs'ün zarafetinin uyumunu korumak için haftada bir 'Güzellik Günü' düzenleyin. Birlikte doğa yürüyüşüne çıkın ve güzelliklerini fotoğraf çekin, ardından birlikte yemek pişirin ve şık bir sofra kurun. Bu estetik deneyimler, doğal uyumunuzu besleyerek duyusal bağınızı derinleştirecektir.",
                        "Güneş-Venüs-90": "Öneri: Güneş'in baskın enerjisi ile Venüs'ün barışçıl doğası arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Çatışma anında 'Sevgi Nefesi' tekniğini kullanın: derin nefes alırken sevgihis edin, verirken baskisi serbest bırakın.\n2) Birbirinizin sevgi dilini öğrenmek için 'Beş Sevgi Dili' testini birlikte yapın.\n3) Ortak bir şifa sanatı pratiği (resim, müzik veya dans) yaparak yaratıcı enerjinizi birleştirin.",
                        "Güneş-Venüs-120": "Öneri: Güneş'insıcakluğu ile Venüs'ün sevgisinin doğal akışını korumak için birlikte romantik ritüeller oluşturun. Her ay birlikte yeni bir deneyim planlayın (müze ziyareti, doğa yürüyüşü, yemek kursu) ve bu deneyim sırasında birbirinize olan minnettarlığınızı ifade edin. Bu ritüel, sevgi enerjinizi canlı tutarak ilişkinizi besleyecektir.",
                        "Güneş-Venüs-180": "Öneri: Güneş'in bireyselliği ile Venüs'ün birleştiriciliği arasındaki zıtlığı dengelemek için 'Bireysel Birlik' pratiği yapın: her gün 30 dakika bireysel aktivite yapın, ardından birlikte zaman geçirerek bu deneyimleri paylaşın. Bu denge, hem bireysel kimliğinizi hem de ilişkinizi güçlendirecektir.",
                        "Güneş-Mars-0": "Öneri: Güneş'in güç enerjisi ile Mars'ın savaşçı enerjisinin kavuştuğu bu noktada, birlikte fiziksel aktivite ve macera ritüelleri oluşturun. Her hafta birlikte yeni bir spor deneyin veya doğa macerasına çıkın. Bu aktif enerji, ilişkinizin canlılığını ve tutkusunu koruyarak fiziksel bağınızı güçlendirecektir.",
                        "Güneş-Mars-60": "Öneri: Güneş'in ışığı ile Mars'ın cesaretinin uyumunu korumak için haftada bir 'Maceracı Çift' etkinliği planlayın. Birlikte yeni bir yer keşfedin, adrenal aktiviteler yapın veya birlikte bir hedefe ulaşmak için strateji geliştirin. Bu enerji paylaşımı, doğal uyumunuzu besleyerek cesaret ve macera ruhunuzu canlı tutacaktır.",
                        "Güneş-Mars-90": "Öneri: Güneş'in ego enerjisi ile Mars'ın öfke enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Öfke anında 'Savaşçı Meditasyonu' yapın: 5 dakika boyunca derin nefes alarak enerjinizi sakinleştirin.\n2) Fiziksel egzersiz birlikte yaparak saldırgan enerjiyi yapıcıya dönüştürün.\n3) Ortak bir hedef belirleyin ve rekabet enerjisini işbirliğine çevirin.",
                        "Güneş-Mars-120": "Öneri: Güneş'insıcakluğu ile Mars'ın cesaretinin doğal akışını korumak için birlikte aktif meditasyon pratiği yapın. Yoga, tai chi veya dans meditasyonu gibi fiziksel aktiviteleri meditasyonla birleştirin. Bu pratik, cesaret ve enerji akışınızı dengede tutarak hem bedensel hem de ruhsal bağınızı güçlendirecektir.",
                        "Güneş-Mars-180": "Öneri: Güneş'in bireyselliği ile Mars'ın savaşçılığı arasındaki zıtlığı dengelemek için 'Dengeli Savaşçı' pratiği yapın: bir gün pasif olun, ertesi gün aktif olun. Ardından bu deneyimleri paylaşarak zıt yönlerinizi nasıl dengeleyebileceğinizi keşfedin. Bu pratik, hem bireysel güç hem de ilişkisel denge sağlayacaktır.",
                        "Güneş-Jüpiter-0": "Öneri: Güneş'in güç enerjisi ile Jüpiter'in genişletici enerjisinin kavuştuğu bu noktada, birlikte büyüme ve bolluk ritüelleri oluşturun. Her sabah şükran journal'ı tutun ve birlikte büyük hayaller kurun. Bu enerji, bolluk bilincinizi ve ortak vizyonunuzu güçlendirecektir.",
                        "Güneş-Jüpiter-60": "Öneri: Güneş'in ışığı ile Jüpiter'in bereketinin uyumunu korumak için haftada bir 'Bereket Paylaşımı' oturumu düzenleyin. Birbirinize bu hafta yaşadığınız olumlu deneyimleri anlatın ve birlikte şükran meditasyonu yapın. Bu pratik, doğal bolluk akışınızı besleyerek ortak bereketinizi artıracaktır.",
                        "Güneş-Jüpiter-90": "Öneri: Güneş'in bireysel gücü ile Jüpiter'in aşırı genişleme enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Bolluk ve paylaşım dengesini korumak için ortak bir bütçe planı oluşturun.\n2) Fazla harcama veya aşırı iyimserlik anında durup gerçekçi bir değerlendirme yapın.\n3) Birlikte sosyal sorumluluk projelerine katılarak bolluk enerjisini paylaşıma dönüştürün.",
                        "Güneş-Jüpiter-120": "Öneri: Güneş'insıcakluğu ile Jüpiter'in bereketinin doğal akışını korumak için birlikte bolluk meditasyonu yapın. Her sabah 10 dakika boyunca bolluk ve refah imgeleri canlandırın ve ardından birlikte şükran duaları edin. Bu ritüel, bolluk bilincinizi ve bereket akışınızı sürekli canlı tutacaktır.",
                        "Güneş-Jüpiter-180": "Öneri: Güneş'in bireyselliği ile Jüpiter'in genişleticiliği arasındaki zıtlığı dengelemek için 'Ölçülü Büyüme' pratiği yapın: bireysel hedeflerinizi ve ortak hedeflerinizi dengeleyerek biroluşum planı oluşturun. Bu denge, hem bireysel gelişiminizi hem de ortak vizyonunuzu besleyecektir.",
                        "Güneş-Satürn-0": "Öneri: Güneş'in güç enerjisi ile Satürn'ün disiplin enerjisinin kavuştuğu bu noktada, birlikte yapı ve sorumluluk ritüelleri oluşturun. Haftalık bir planlama oturumu düzenleyin ve birbirinize hesap verin. Bu disiplin, ortak hedeflerinize ulaşmanızı sağlayarak ilişkinizin temelini güçlendirecektir.",
                        "Güneş-Satürn-60": "Öneri: Güneş'in ışığı ile Satürn'ün disiplininin uyumunu korumak için haftada bir 'Yapı ve Planlama' oturumu yapın. Birlikte hedeflerinizi belirleyin ve bunlara ulaşmak için somut adımlar planlayın. Bu pratik, doğal disiplininizi besleyerek ortak sorumluluk duygunuzu güçlendirecektir.",
                        "Güneş-Satürn-90": "Öneri: Güneş'in bireysel gücü ile Satürn'ün sınırlayıcı enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Sınırları kabul etmeyi ve aynı anda yaratıcı olmayı öğrenmek için birlikte Mindfulness pratiği yapın.\n2) Sorumlulukları adil bir şekilde paylaşmak için açık iletişim kurun.\n3) Ortak bir miras veya uzun vadeli proje oluşturarak kısıtlamaları yapısal güce dönüştürün.",
                        "Güneş-Satürn-120": "Öneri: Güneş'insıcakluğu ile Satürn'ün disiplininin doğal akışını korumak için birlikte uzun vadeli bir plan oluşturun ve bu plana sadık kalın. Her ay ilerlemenizi değerlendirin ve birbirinizi teşvik edin. Bu yapı, hedeflerinize ulaşmanızı sağlayarak ortak başarınızı ve güveninizi pekiştirecektir.",
                        "Güneş-Satürn-180": "Öneri: Güneş'in bireyselliği ile Satürn'ün kısıtlaması arasındaki zıtlığı dengelemek için 'Özgürlük ve Sorumluluk Dansı' pratiği yapın: bireysel alanlarınızın ve ortak sorumluluklarınızın dengesini bulun. Her hafta birbirinize alan tanıyın ve aynı zamanda ortak yükümlülüklerinizi yerine getirin. Bu denge, hem bireysel özgürlüğünüzü hem de ilişkisel güveninizi koruyacaktır.",
                        "Güneş-Uranüs-0": "Öneri: Güneş'in güç enerjisi ile Uranüs'ün devrim enerjisinin kavuştuğu bu noktada, birlikte yenilik ve değişim ritüelleri oluşturun. Her ay birlikte yeni bir şey deneyin (teknoloji, sanat, felsefe) ve bu deneyimleri tartışın. Bu enerji, ilişkize yeni soluklar getirerek yaratıcı ve devrimci bağınızı canlı tutacaktır.",
                        "Güneş-Uranüs-60": "Öneri: Güneş'in ışığı ile Uranüs'ün yenilikçiliğinin uyumunu korumak için haftada bir 'Yenilikçi Buluşma' düzenleyin. Birlikte farklı bir aktivite yapın veya farklı bir yer keşfedin. Bu deneyimler, doğal yaratıcılığınızı besleyerek ilişkize taze enerji katacaktır.",
                        "Güneş-Uranüs-90": "Öneri: Güneş'in bireysel gücü ile Uranüs'ün ani değişim enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Değişim anında 'Dur ve Al' tekniğini kullanın: ani bir karar almadan önce 24 saat bekleyin.\n2) Birbirinizin bağımsızlığına saygı duyun ve aynı anda bağlantıda kalın.\n3) Ortak bir vizyon oluşturarak bireysel özgürlüğü ve ilişkisel bağlılığı dengeleyin.",
                        "Güneş-Uranüs-120": "Öneri: Güneş'insıcakluğu ile Uranüs'ün devrim enerjisinin doğal akışını korumak için birlikte vizyoner bir proje oluşturun. Geleceğe yönelik yaratıcı planlar yapın ve bu planları somutlaştırmak için birlikte çalışın. Bu pratik, yaratıcı potansiyelinizi ve ortak vizyonunuzu güçlendirecektir.",
                        "Güneş-Uranüs-180": "Öneri: Güneş'in bireyselliği ile Uranüs'ün kolektif devrimi arasındaki zıtlığı dengelemek için 'Bireysel Devrim' pratiği yapın: hem bireysel değişim hem de ortak dönüşüm için zaman ayırın. Her hafta birlikte yeni bir perspektif keşfedin ve bu perspektifi ilişkinize nasıl uygulayacağınızı tartışın. Bu denge, hem bireysel özgürlüğünüzü hem de ilişkisel dönüşümünüzü destekleyecektir.",
                        "Güneş-Neptün-0": "Öneri: Güneş'in güç enerjisi ile Neptün'ün manevi enerjisinin kavuştuğu bu noktada, birlikte manevi ritüeller ve meditasyon pratiği oluşturun. Her sabah birlikte dua edin veya meditasyon yapın ve manevi vizyonlarınızı paylaşın. Bu enerji, ruhsal bağınızı derinleştirerek ilişkinizi manevi bir boyuta taşıyacaktır.",
                        "Güneş-Neptün-60": "Öneri: Güneş'in ışığı ile Neptün'ün manevi flöwsunun uyumunu korumak için haftada bir 'Manevi Paylaşım' oturumu düzenleyin. Birlikte müzik dinleyin, sanat eserlerini inceleyin veya doğada yürüyüş yaparak manevi deneyimlerinizi paylaşın. Bu pratik, manevi hassasiyetinizi ve yaratıcı ilhamınızı besleyecektir.",
                        "Güneş-Neptün-90": "Öneri: Güneş'in net gücü ile Neptün'ün bulanık enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Rüya günlüğü tutarak bilinçaltınızı keşfedin ve bu deneyimleri birbirinizle paylaşın.\n2) Manevi pratiğinizi somutlaştırarak illüzyonları ve gerçekleri dengeleyin.\n3) Birlikte gönüllülük yaparak manevi enerjinizi somut eylemlere dönüştürün.",
                        "Güneş-Neptün-120": "Öneri: Güneş'insıcakluğu ile Neptün'ün manevi akışının doğal uyumunu korumak için birlikte manevi bir yolculuk planlayın. Manevi mekanları ziyaret edin, meditasyon kamplarına katılın veya birlikte yaratıcı sanat pratiği yapın. Bu deneyim, manevi bilinçliliğinizi ve ruhsal bağınızı derinleştirecektir.",
                        "Güneş-Neptün-180": "Öneri: Güneş'in bireyselliği ile Neptün'ün evrenselliği arasındaki zıtlığı dengelemek için 'Bireysel Maneviyat' pratiği yapın: her biriniz kendi manevi yolunuzu takip edin, ardından bu deneyimleri birlikte paylaşarak ortak bir manevi vizyon oluşturun. Bu denge, hem bireysel ruhsal gelişimi hem de ortak manevi bağı besleyecektir.",
                        "Güneş-Plüton-0": "Öneri: Güneş'in güç enerjisi ile Plüton'un dönüştürücü enerjisinin kavuştuğu bu noktada, birlikte derin dönüşüm ve yeniden doğum ritüelleri oluşturun. Her ay birlikte eski alışkanlıklarınızı bırakın ve yeni başlangıçlar yapın. Bu enerji, derin dönüşümünüzü ve yeniden doğuşunuzu hızlandırarak ilişkinizi yeniden yapılandıracaktır.",
                        "Güneş-Plüton-60": "Öneri: Güneş'in ışığı ile Plüton'un derin transformasyonunun uyumunu korumak için haftada bir 'Dönüşüm Paylaşımı' oturumu düzenleyin. Birlikte eski yaralarınızı iyileştirin ve yeni bir kimlik oluşturun. Bu pratik, derin dönüşümünüzü destekleyerek ilişkinizi yeniden yapılandıracaktır.",
                        "Güneş-Plüton-90": "Öneri: Güneş'in ego enerjisi ile Plüton'un power struggle enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Güç mücadelelerini fark edin ve bunları derin birkendi analizine dönüştürün.\n2) Birbirinizin gölgelerini kabul edin ve bu gölgelerle birlikte çalışın.\n3) Ortak bir dönüşüm pratiği yaparak power struggle'ı ortak güce dönüştürün.",
                        "Güneş-Plüton-120": "Öneri: Güneş'insıcakluğu ile Plüton'un derin dönüşümünün doğal akışını korumak için birlikte derin bir şifa çalışması yapın. Psikolojik astroloji, enerji çalışması veya derin meditasyon pratiği yaparak içsel dönüşümlerinizi destekleyin. Bu pratik, derin dönüşümünüzü ve ruhsal yenilenmenizi hızlandıracaktır.",
                        "Güneş-Plüton-180": "Öneri: Güneş'in bireyselliği ile Plüton'un transformasyonu arasındaki zıtlığı dengelemek için 'Bireysel Dönüşüm' pratiği yapın: her biriniz kendi derin dönüşümünüzü takip edin, ardından bu dönüşümleri birlikte paylaşarak ortak bir yeniden doğum süreci geçirin. Bu denge, hem bireysel hem de ilişkisel dönüşümü destekleyecektir.",
                        "Güneş-KAD-0": "Öneri: Güneş'in güç enerjisi ile Kuzey Ay Düğümü'nün kadersel yolunun kavuştuğu bu noktada, birlikte kaderinizi bilinçli şekilde yönlendirme pratiği yapın. Her sabah kadersel niyetlerinizi yüksek sesle söyleyin ve birlikte kaderinizi şekillendiren adımlar atın. Bu enerji, kadersel yolunuzu ve ortak amacınızı güçlendirecektir.",
                        "Güneş-KAD-60": "Öneri: Güneş'in ışığı ile Kuzey Ay Düğümü'nün kadersel akışının uyumunu korumak için haftada bir 'Kader Paylaşımı' oturumu düzenleyin. Birbirinize kadersel deneyimlerinizi anlatın ve birlikte geleceğinizi planlayın. Bu pratik, kadersel yola bağlılığınızı ve ortak amacınızı besleyecektir.",
                        "Güneş-KAD-90": "Öneri: Güneş'in bireysel gücü ile Kuzey Ay Düğümü'nün kadersel zorlukları arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Kadersel engelleri fırsat olarak yeniden çerçeveleyin.\n2) Birbirinize hesap vererek kadersel yolunuzda ilerleyin.\n3) Ortak bir kader vizyonu oluşturarak zorlukları birlikte aşın.",
                        "Güneş-KAD-120": "Öneri: Güneş'insıcakluğu ile Kuzey Ay Düğümü'nün kadersel akışının doğal uyumunu korumak için birlikte kadersel bir proje başlatın. Bu proje, bireysel ve ortak kaderinizi birleştirecek şekilde tasarlanmalıdır. Bu pracık, kadersel potansiyelinizi ve ortak amacınızı gerçekleştirmenizi sağlayacaktır.",
                        "Güneş-KAD-180": "Öneri: Güneş'in bireyselliği ile Kuzey Ay Düğümü'nün kolektif kaderi arasındaki zıtlığı dengelemek için 'Bireysel Kader' pratiği yapın: her biriniz kendi kadersel yolunuzu keşfedin, ardından bu deneyimleri birlikte paylaşarak ortak bir kader vizyonu oluşturun. Bu denge, hem bireysel kadersel potansiyeli hem de ortak amacın gerçekleşmesini destekleyecektir.",
                        "Güneş-Chiron-0": "Öneri: Güneş'in güç enerjisi ile Chiron'un şifacı yarasının kavuştuğu bu noktada, birlikte derin şifa ve iyileşme ritüelleri oluşturun. Her sabah birlikte şifa meditasyonu yapın ve birbirinizin yaralarını şifalandırma niyetinde bulunun. Bu enerji, derin şifa sürecinizi ve birbirinize olan şifa kapasitenizi güçlendirecektir.",
                        "Güneş-Chiron-60": "Öneri: Güneş'in ışığı ile Chiron'un şifa enerjisinin uyumunu korumak için haftada bir 'Şifa Paylaşımı' oturumu düzenleyin. Birbirinize yaralarınızı anlatın ve birlikte şifa pratiği yapın. Bu pratik, şifa sürecinizi destekleyerek derin iyileşmenizi hızlandıracaktır.",
                        "Güneş-Chiron-90": "Öneri: Güneş'in ego enerjisi ile Chiron'un kırılgan enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Kırılganlık anında birbirinize alan tanıyın ve aynı anda destek olun.\n2) Yaralarınızı şifalandırmak için profesyonel destek alın.\n3) Birlikte şifa projeleri başlatarak yaralarınızı dönüştürücü güce dönüştürün.",
                        "Güneş-Chiron-120": "Öneri: Güneş'insıcakluğu ile Chiron'un şifa akışının doğal uyumunu korumak için birlikte şifa banyosu veya enerji çalışması yapın. Doğanın iyileştirici gücünden faydalanarak birlikte şifa deneyimleri yaşayın. Bu pratik, derin şifa sürecinizi ve ruhsal iyileşmenizi destekleyecektir.",
                        "Güneş-Chiron-180": "Öneri: Güneş'in bireyselliği ile Chiron'un evrensel şifası arasındaki zıtlığı dengelemek için 'Bireysel Şifa' pratiği yapın: her biriniz kendi şifa yolunuzu takip edin, ardından bu deneyimleri birlikte paylaşarak ortak bir şifa vizyonu oluşturun. Bu denge, hem bireysel şifayı hem de ortak iyileşmeyi destekleyecektir.",
                        "Ay-Ay-0": "Öneri: İkinizin de benzer duygusal titresimlarda titreştiği bu kavuşumda, birlikte duygusal ritim ritüelleri oluşturun. Her yeni ayda ortak duygusal niyetler belirleyin ve dolunayda bu niyetleri serbest bırakma pratiği yapın. Bu ritüel, duygusal senkronizasyonunuzu derinleştirerek ortak içsel dünyanızı besleyecektir.",
                        "Ay-Ay-60": "Öneri: Duygusal hassasiyetinizin doğal uyumunu korumak için haftada bir 'Duygu Paylaşımı' oturumu düzenleyin. Birbirinize duygusal deneyimlerinizi anlatın ve birlikte meditasyon yaparak duygusal berraklık elde edin. Bu pratik, duygusal bağınızı güçlendirerek derin bir anlayış oluşturacaktır.",
                        "Ay-Ay-90": "Öneri: Duygusal hassasiyetiniz arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal tetiklenme anında birbirinize alan tanıyın ve aynı anda destek olun.\n2) Duygusal ihtiyaçlarınızı açıkça ifade edin ve birbirinizin ihtiyaçlarını öğrenin.\n3) Birlikte duygusal şifa meditasyonu yaparak duygusal dengenizi yeniden kurun.",
                        "Ay-Ay-120": "Öneri: Duygusal hassasiyetinizin doğal akışını korumak için birlikte duygusal deneyimler planlayın. Birlikte doğa yürüyüşü yapın, müzik dinleyin veya sanat eserlerini inceleyerek duygusal deneyimlerinizi paylaşın. Bu pratik, duygusal derinliğinizi ve ortak duygusal dünyanızı besleyecektir.",
                        "Ay-Ay-180": "Öneri: Duygusal hassasiyetinizin zıtlıklarını dengelemek için 'Ayna Meditasyonu' yapın: karşılıklı oturun ve 5 dakika boyunca birbirinizin gözlerinin içine bakarak nefes alın. Ardından birbirinizin duygusal dilini yüksek sesle onaylayın. Bu pratik, duygusal zıtlıklarınızı birbirinizi tamamlayan güçlere dönüştürecektir.",
                        "Ay-Merkür-0": "Öneri: Ay'ın duygusal derinliği ile Merkür'ün iletişim becerilerinin kavuştuğu bu noktada, birlikte duygusal iletişim ritüelleri oluşturun. Her akşam birbirinize duygularınızı yüksek sesle ifade edin ve birlikte journal'a yazın. Bu ritüel, duygusal iletişiminizi derinleştirerek anlayış köprülerinizi güçlendirecektir.",
                        "Ay-Merkür-60": "Öneri: Ay'ın yumuşaklığı ile Merkür'ün zekasının uyumunu korumak için haftada bir 'Duygusal Zeka' oturumu düzenleyin. Birbirinize duygusal deneyimlerinizi anlatın ve birlikte bu deneyimleri analiz edin. Bu pratik, duygusal zekanızı ve iletişim kalitenizi artıracaktır.",
                        "Ay-Merkür-90": "Öneri: Ay'ın duygusal dalgalanmaları ile Merkür'ün hızlı zihni arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal konuşmalar sırasında zihinsel analizi bırakarak sadece duygulara odaklanın.\n2) Mantıksal tartışmalar sırasında duygusal hassasiyeti unutmayın.\n3) Birlikte hem duygusal hem de zihinsel denge pratiği yapın.",
                        "Ay-Merkür-120": "Öneri: Ay'ın duygusal akışı ile Merkür'ün netliğinin doğal uyumunu korumak için birlikte hikaye anlatımı pratiği yapın. Birbirinize duygusal hikayeler anlatın ve bu hikayeleri birlikte yazın. Bu pratik, duygusal ve zihinsel bağınızı derinleştirerek yaratıcı iletişiminizi besleyecektir.",
                        "Ay-Merkür-180": "Öneri: Ay'ın duygusallığı ile Merkür'ün rasyonelliği arasındaki zıtlığı dengelemek için 'Denge Konuşması' pratiği yapın: her konuşmada hem duygusal hem de mantıksal perspektifleri birleştirin. Bu denge, hem duygusal derinliğinizi hem de zihinsel netliğinizi koruyarak iletişiminizi güçlendirecektir.",
                        "Ay-Venüs-0": "Öneri: Ay'ın duygusal derinliği ile Venüs'ün sevgi enerjisinin kavuştuğu bu noktada, birlikte sevgi ve şefkat ritüelleri oluşturun. Her sabah birbirinize sevgi dolu dokunuşlar ve sözlerle yaklaşın ve birlikte güzellik deneyimleri yaşayın. Bu enerji, sevgi bağınızı derinleştirerek romantik ve duygusal ilişkinizi besleyecektir.",
                        "Ay-Venüs-60": "Öneri: Ay'ın yumuşaklığı ile Venüs'ün zarafetinin uyumunu korumak için haftada bir 'Güzellik ve Sevgi' oturumu düzenleyin. Birlikte sanat eserlerini inceleyin, doğa yürüyüşü yapın veya birlikte yemek pişirerek duygusal ve estetik deneyimlerinizi paylaşın. Bu pratik,gök uyumunuzu besleyerek duygusal ve duysal bağınızı derinleştirecektir.",
                        "Ay-Venüs-90": "Öneri: Ay'ın duygusal hassasiyeti ile Venüs'ün barışçıl doğası arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal çatışma anında 'Sevgi Nefesi' tekniğini kullanın: derin nefes alırken sevgihis edin, verirken baskisi serbest bırakın.\n2) Birbirinizin sevgi dilini öğrenmek için 'Beş Sevgi Dili' testini birlikte yapın.\n3) Ortak bir şifa sanatı pratiği yaparak yaratıcı enerjinizi birleştirin.",
                        "Ay-Venüs-120": "Öneri: Ay'ın duygusal akışı ile Venüs'ün sevgisinin doğal uyumunu korumak için birlikte romantik ritüeller oluşturun. Her ay birlikte yeni bir deneyim planlayın (müze ziyareti, doğa yürüyüşü, yemek kursu) ve bu deneyim sırasında birbirinize olan minnettarlığınızı ifade edin. Bu ritüel, sevgi enerjinizi canlı tutarak ilişkinizi besleyecektir.",
                        "Ay-Venüs-180": "Öneri: Ay'ın içe dönüklüğü ile Venüs'ün dışa dönüklüğü arasındaki zıtlığı dengelemek için 'İç Dış Dansı' pratiği yapın: bir gün içe dönük aktiviteler yapın (meditasyon, journal yazma), ertesi gün dışa dönük aktiviteler yapın (sosyal etkinlikler, sanat deneyimleri). Bu denge, hem içsel duygusal dünyanızı hem de dışsal sevgigösterimlerinizi besleyecektir.",
                        "Ay-Mars-0": "Öneri: Ay'ın duygusal derinliği ile Mars'ın savaşçı enerjisinin kavuştuğu bu noktada, birlikte duygusal güç ritüelleri oluşturun. Her sabah birlikte fiziksel aktivite yaparak duygusal enerjinizi serbest bırakın ve ardından birlikte meditasyon yaparak dengeyi bulun. Bu enerji, duygusal cesaretinizi ve fiziksel sağlığınızı güçlendirecektir.",
                        "Ay-Mars-60": "Öneri: Ay'ın yumuşaklığı ile Mars'ın cesaretinin uyumunu korumak için haftada bir 'Aktif Duygusal' etkinliği planlayın. Birlikte doğa yürüyüşüne çıkın, spor yapın veya adrenal aktiviteler yaparak duygusal ve fiziksel enerjinizi birleştirin. Bu pratik, doğal uyumunuzu besleyerek duygusal ve bedensel bağınızı derinleştirecektir.",
                        "Ay-Mars-90": "Öneri: Ay'ın duygusal hassasiyeti ile Mars'ın saldırgan enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Öfke anında 'Sakin Nefes' tekniğini kullanın: 10 kez derin nefes alarak duygusal dalgalanmaları sakinleştirin.\n2) Fiziksel egzersiz birlikte yaparak saldırgan enerjiyi yapıcıya dönüştürün.\n3) Birlikte duygusal şifa meditasyonu yaparak duygusal dengenizi yeniden kurun.",
                        "Ay-Mars-120": "Öneri: Ay'ın duygusal akışı ile Mars'ın cesaretinin doğal uyumunu korumak için birlikte aktif meditasyon pratiği yapın. Yoga, tai chi veya dans meditasyonu gibi fiziksel aktiviteleri meditasyonla birleştirin. Bu pratik, cesaret ve enerji akışınızı dengede tutarak hem bedensel hem de ruhsal bağınızı güçlendirecektir.",
                        "Ay-Mars-180": "Öneri: Ay'ın içe dönüklüğü ile Mars'ın dışa dönüklüğü arasındaki zıtlığı dengelemek için 'Dengeli Savaşçı' pratiği yapın: bir gün pasif ve duygusal olun, ertesi gün aktif ve savaşçı olun. Ardından bu deneyimleri paylaşarak zıt yönlerinizi nasıl dengeleyebileceğinizi keşfedin. Bu pratik, hem duygusal derinliğinizi hem de fiziksel cesaretinizi besleyecektir.",
                        "Ay-Jüpiter-0": "Öneri: Ay'ın duygusal derinliği ile Jüpiter'in genişletici enerjisinin kavuştuğu bu noktada, birlikte duygusal bolluk ve büyüme ritüelleri oluşturun. Her sabah şükran journal'ı tutun ve birlikte büyük duygusal hayaller kurun. Bu enerji, duygusal bolluk bilincinizi ve ortak vizyonunuzu güçlendirecektir.",
                        "Ay-Jüpiter-60": "Öneri: Ay'ın yumuşaklığı ile Jüpiter'in bereketinin uyumunu korumak için haftada bir 'Duygusal Bereket' oturumu düzenleyin. Birbirinize bu hafta yaşadığınız olumlu duygusal deneyimleri anlatın ve birlikte şükran meditasyonu yapın. Bu pratik, doğal duygusal akışınızı besleyerek ortak bereketinizi artıracaktır.",
                        "Ay-Jüpiter-90": "Öneri: Ay'ın duygusal hassasiyeti ile Jüpiter'in aşırı genişleme enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal aşırılıkları dengelemek için düzenli meditasyon pratiği yapın.\n2) Fazla iyimserlik veya aşırı duygusallık anında gerçekçi bir değerlendirme yapın.\n3) Birlikte sosyal sorumluluk projelerine katılarak duygusal enerjinizi paylaşıma dönüştürün.",
                        "Ay-Jüpiter-120": "Öneri: Ay'ın duygusal akışı ile Jüpiter'in bereketinin doğal uyumunu korumak için birlikte duygusal bolluk meditasyonu yapın. Her sabah 10 dakika boyunca duygusal bolluk ve refah imgeleri canlandırın ve ardından birlikte şükran duaları edin. Bu ritüel, duygusal bolluk bilincinizi ve bereket akışınızı sürekli canlı tutacaktır.",
                        "Ay-Jüpiter-180": "Öneri: Ay'ın içe dönüklüğü ile Jüpiter'in genişleticiliği arasındaki zıtlığı dengelemek için 'Ölçülü Duygusal Büyüme' pratiği yapın: bireysel duygusal ihtiyaçlarınızı ve ortak duygusal hedeflerinizi dengeleyerek biroluşum planı oluşturun. Bu denge, hem bireysel duygusal gelişiminizi hem de ortak duygusal vizyonunuzu besleyecektir.",
                        "Ay-Satürn-0": "Öneri: Ay'ın duygusal derinliği ile Satürn'ün disiplin enerjisinin kavuştuğu bu noktada, birlikte duygusal yapı ve sorumluluk ritüelleri oluşturun. Haftalık bir duygusal planlama oturumu düzenleyin ve birbirinize duygusal hesap verin. Bu disiplin, duygusal dengenizi koruyarak ilişkinizin temelini güçlendirecektir.",
                        "Ay-Satürn-60": "Öneri: Ay'ın yumuşaklığı ile Satürn'ün disiplininin uyumunu korumak için haftada bir 'Duygusal Yapı' oturumu yapın. Birlikte duygusal hedeflerinizi belirleyin ve bunlara ulaşmak için somut adımlar planlayın. Bu pratik, doğal disiplininizi besleyerek duygusal sorumluluk duygunuzu güçlendirecektir.",
                        "Ay-Satürn-90": "Öneri: Ay'ın duygusal dalgalanmaları ile Satürn'ün sınırlayıcı enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal sınırları kabul etmeyi ve aynı anda duygusal olmayı öğrenmek için birlikte Mindfulness pratiği yapın.\n2) Duygusal sorumlulukları adil bir şekilde paylaşmak için açık iletişim kurun.\n3) Ortak bir duygusal yapı oluşturarak duygusal dalgalanmaları yapısal güce dönüştürün.",
                        "Ay-Satürn-120": "Öneri: Ay'ın duygusal akışı ile Satürn'ün disiplininin doğal uyumunu korumak için birlikte uzun vadeli bir duygusal plan oluşturun ve bu plana sadık kalın. Her ay ilerlemenizi değerlendirin ve birbirinizi teşvik edin. Bu yapı, duygusal hedeflerinize ulaşmanızı sağlayarak ortak güveninizi ve derinliğinizi pekiştirecektir.",
                        "Ay-Satürn-180": "Öneri: Ay'ın içe dönüklüğü ile Satürn'ün kısıtlaması arasındaki zıtlığı dengelemek için 'Duygusal Özgürlük ve Sorumluluk Dansı' pratiği yapın: duygusal alanlarınızın ve ortak sorumluluklarınızın dengesini bulun. Her hafta birbirinize duygusal alan tanıyın ve aynı zamanda ortak duygusal yükümlülüklerinizi yerine getirin. Bu denge, hem duygusal özgürlüğünüzü hem de ilişkisel güveninizi koruyacaktır.",
                        "Ay-Uranüs-0": "Öneri: Ay'ın duygusal derinliği ile Uranüs'ün devrim enerjisinin kavuştuğu bu noktada, birlikte duygusal yenilik ve değişim ritüelleri oluşturun. Her ay birlikte yeni bir duygusal deneyim yaşayın ve bu deneyimleri tartışın. Bu enerji, ilişkize yeni duygusal soluklar getirerek yaratıcı ve devrimci duygusal bağınızı canlı tutacaktır.",
                        "Ay-Uranüs-60": "Öneri: Ay'ın yumuşaklığı ile Uranüs'ün yenilikçiliğinin uyumunu korumak için haftada bir 'Duygusal Yenilik' oturumu düzenleyin. Birlikte farklı bir duygusal aktivite yapın veya farklı bir duygusal deneyim yaşayın. Bu deneyimler, doğal duygusal yaratıcılığınızı besleyerek ilişkize taze duygusal enerji katacaktır.",
                        "Ay-Uranüs-90": "Öneri: Ay'ın duygusal hassasiyeti ile Uranüs'ün ani değişim enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal değişim anında 'Dur ve Hisset' tekniğini kullanın: ani bir duygusal tepki vermeden önce 24 saat bekleyin.\n2) Birbirinizin duygusal bağımsızlığına saygı duyun ve aynı anda bağlantıda kalın.\n3) Ortak bir duygusal vizyon oluşturarak bireysel duygusal özgürlüğü ve ilişkisel bağlılığı dengeleyin.",
                        "Ay-Uranüs-120": "Öneri: Ay'ın duygusal akışı ile Uranüs'ün devrim enerjisinin doğal uyumunu korumak için birlikte vizyoner bir duygusal proje oluşturun. Geleceğe yönelik yaratıcı duygusal planlar yapın ve bu planları somutlaştırmak için birlikte çalışın. Bu pratik, yaratıcı duygusal potansiyelinizi ve ortak duygusal vizyonunuzu güçlendirecektir.",
                        "Ay-Uranüs-180": "Öneri: Ay'ın içe dönüklüğü ile Uranüs'ün kolektif devrimi arasındaki zıtlığı dengelemek için 'Bireysel Duygusal Devrim' pratiği yapın: hem bireysel duygusal değişim hem de ortak duygusal dönüşüm için zaman ayırın. Her hafta birlikte yeni bir duygusal perspektif keşfedin ve bu perspektifi ilişkinize nasıl uygulayacağınızı tartışın. Bu denge, hem bireysel duygusal özgürlüğünüzü hem de ilişkisel duygusal dönüşümünüzü destekleyecektir.",
                        "Ay-Neptün-0": "Öneri: Ay'ın duygusal derinliği ile Neptün'ün manevi enerjisinin kavuştuğu bu noktada, birlikte manevi ve duygusal ritüeller oluşturun. Her sabah birlikte dua edin veya meditasyon yapın ve manevi ve duygusal vizyonlarınızı paylaşın. Bu enerji, ruhsal ve duygusal bağınızı derinleştirerek ilişkinizi manevi ve duygusal bir boyuta taşıyacaktır.",
                        "Ay-Neptün-60": "Öneri: Ay'ın yumuşaklığı ile Neptün'ün manevi flöwsunun uyumunu korumak için haftada bir 'Manevi ve Duygusal Paylaşım' oturumu düzenleyin. Birlikte müzik dinleyin, sanat eserlerini inceleyin veya doğada yürüyüş yaparak manevi ve duygusal deneyimlerinizi paylaşın. Bu pratik, manevi ve duygusal hassasiyetinizi ve yaratıcı ilhamınızı besleyecektir.",
                        "Ay-Neptün-90": "Öneri: Ay'ın duygusal dalgalanmaları ile Neptün'ün bulanık enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Rüya günlüğü tutarak bilinçaltınızı keşfedin ve bu deneyimleri birbirinizle paylaşın.\n2) Manevi pratiğinizi somutlaştırarak illüzyonları ve gerçekleri dengeleyin.\n3) Birlikte gönüllülük yaparak manevi ve duygusal enerjinizi somut eylemlere dönüştürün.",
                        "Ay-Neptün-120": "Öneri: Ay'ın duygusal akışı ile Neptün'ün manevi akışının doğal uyumunu korumak için birlikte manevi ve duygusal bir yolculuk planlayın. Manevi mekanları ziyaret edin, meditasyon kamplarına katılın veya birlikte yaratıcı sanat pratiği yapın. Bu deneyim, manevi ve duygusal bilinçliliğinizi ve ruhsal bağınızı derinleştirecektir.",
                        "Ay-Neptün-180": "Öneri: Ay'ın içe dönüklüğü ile Neptün'ün evrenselliği arasındaki zıtlığı dengelemek için 'Bireysel Manevi Duygusallık' pratiği yapın: her biriniz kendi manevi ve duygusal yolunuzu takip edin, ardından bu deneyimleri birlikte paylaşarak ortak bir manevi ve duygusal vizyon oluşturun. Bu denge, hem bireysel ruhsal ve duygusal gelişimi hem de ortak manevi ve duygusal bağı besleyecektir.",
                        "Ay-Plüton-0": "Öneri: Ay'ın duygusal derinliği ile Plüton'un dönüştürücü enerjisinin kavuştuğu bu noktada, birlikte derin duygusal dönüşüm ve yeniden doğum ritüelleri oluşturun. Her ay birlikte eski duygusal alışkanlıklarınızı bırakın ve yeni başlangıçlar yapın. Bu enerji, derin duygusal dönüşümünüzü ve yeniden doğuşunuzu hızlandırarak ilişkinizi yeniden yapılandıracaktır.",
                        "Ay-Plüton-60": "Öneri: Ay'ın yumuşaklığı ile Plüton'un derin transformasyonunun uyumunu korumak için haftada bir 'Duygusal Dönüşüm Paylaşımı' oturumu düzenleyin. Birlikte eski duygusal yaralarınızı iyileştirin ve yeni bir duygusal kimlik oluşturun. Bu pratik, derin duygusal dönüşümünüzü destekleyerek ilişkinizi yeniden yapılandıracaktır.",
                        "Ay-Plüton-90": "Öneri: Ay'ın duygusal hassasiyeti ile Plüton'un power struggle enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal güç mücadelelerini fark edin ve bunları derin bir duygusal analizine dönüştürün.\n2) Birbirinizin duygusal gölgelerini kabul edin ve bu gölgelerle birlikte çalışın.\n3) Ortak bir duygusal dönüşüm pratiği yaparak power struggle'ı ortak duygusal güce dönüştürün.",
                        "Ay-Plüton-120": "Öneri: Ay'ın duygusal akışı ile Plüton'un derin dönüşümünün doğal uyumunu korumak için birlikte derin bir duygusal şifa çalışması yapın. Psikolojik astroloji, enerji çalışması veya derin meditasyon pratiği yaparak içsel duygusal dönüşümlerinizi destekleyin. Bu pratik, derin duygusal dönüşümünüzü ve ruhsal yenilenmenizi hızlandıracaktır.",
                        "Ay-Plüton-180": "Öneri: Ay'ın içe dönüklüğü ile Plüton'un transformasyonu arasındaki zıtlığı dengelemek için 'Bireysel Duygusal Dönüşüm' pratiği yapın: her biriniz kendi derin duygusal dönüşümünüzü takip edin, ardından bu dönüşümleri birlikte paylaşarak ortak bir duygusal yeniden doğum süreci geçirin. Bu denge, hem bireysel hem de ilişkisel duygusal dönüşümü destekleyecektir.",
                        "Ay-KAD-0": "Öneri: Ay'ın duygusal derinliği ile Kuzey Ay Düğümü'nün kadersel yolunun kavuştuğu bu noktada, birlikte duygusal kaderinizi bilinçli şekilde yönlendirme pratiği yapın. Her sabah duygusal kadersel niyetlerinizi yüksek sesle söyleyin ve birlikte kaderinizi şekillendiren duygusal adımlar atın. Bu enerji, duygusal kadersel yolunuzu ve ortak amacınızı güçlendirecektir.",
                        "Ay-KAD-60": "Öneri: Ay'ın yumuşaklığı ile Kuzey Ay Düğümü'nün kadersel akışının uyumunu korumak için haftada bir 'Duygusal Kader Paylaşımı' oturumu düzenleyin. Birbirinize duygusal kadersel deneyimlerinizi anlatın ve birlikte duygusal geleceğinizi planlayın. Bu pratik, duygusal yola bağlılığınızı ve ortak amacınızı besleyecektir.",
                        "Ay-KAD-90": "Öneri: Ay'ın duygusal dalgalanmaları ile Kuzey Ay Düğümü'nün kadersel zorlukları arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal kadersel engelleri fırsat olarak yeniden çerçeveleyin.\n2) Birbirinize duygusal hesap vererek kadersel yolunuzda ilerleyin.\n3) Ortak bir duygusal kader vizyonu oluşturarak zorlukları birlikte aşın.",
                        "Ay-KAD-120": "Öneri: Ay'ın duygusal akışı ile Kuzey Ay Düğümü'nün kadersel akışının doğal uyumunu korumak için birlikte duygusal kadersel bir proje başlatın. Bu proje, bireysel ve ortak duygusal kaderinizi birleştirecek şekilde tasarlanmalıdır. Bu pratik, duygusal kadersel potansiyelinizi ve ortak amacınızı gerçekleştirmenizi sağlayacaktır.",
                        "Ay-KAD-180": "Öneri: Ay'ın içe dönüklüğü ile Kuzey Ay Düğümü'nün kolektif kaderi arasındaki zıtlığı dengelemek için 'Bireysel Duygusal Kader' pratiği yapın: her biriniz kendi duygusal kadersel yolunuzu keşfedin, ardından bu deneyimleri birlikte paylaşarak ortak bir duygusal kader vizyonu oluşturun. Bu denge, hem bireysel duygusal kadersel potansiyeli hem de ortak amacın gerçekleşmesini destekleyecektir.",
                        "Ay-Chiron-0": "Öneri: Ay'ın duygusal derinliği ile Chiron'un şifacı yarasının kavuştuğu bu noktada, birlikte derin duygusal şifa ve iyileşme ritüelleri oluşturun. Her sabah birlikte duygusal şifa meditasyonu yapın ve birbirinizin duygusal yaralarını şifalandırma niyetinde bulunun. Bu enerji, derin duygusal şifa sürecinizi ve birbirinize olan duygusal şifa kapasitenizi güçlendirecektir.",
                        "Ay-Chiron-60": "Öneri: Ay'ın yumuşaklığı ile Chiron'un şifa enerjisinin uyumunu korumak için haftada bir 'Duygusal Şifa Paylaşımı' oturumu düzenleyin. Birbirinize duygusal yaralarınızı anlatın ve birlikte duygusal şifa pratiği yapın. Bu pratik, duygusal şifa sürecinizi destekleyerek derin iyileşmenizi hızlandıracaktır.",
                        "Ay-Chiron-90": "Öneri: Ay'ın duygusal hassasiyeti ile Chiron'un kırılgan enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Duygusal kırılganlık anında birbirinize alan tanıyın ve aynı anda destek olun.\n2) Duygusal yaralarınızı şifalandırmak için profesyonel destek alın.\n3) Birlikte duygusal şifa projeleri başlatarak yaralarınızı dönüştürücü güce dönüştürün.",
                        "Ay-Chiron-120": "Öneri: Ay'ın duygusal akışı ile Chiron'un şifa akışının doğal uyumunu korumak için birlikte duygusal şifa banyosu veya enerji çalışması yapın. Doğanın iyileştirici gücünden faydalanarak birlikte duygusal şifa deneyimleri yaşayın. Bu pratik, derin duygusal şifa sürecinizi ve ruhsal iyileşmenizi destekleyecektir.",
                        "Ay-Chiron-180": "Öneri: Ay'ın içe dönüklüğü ile Chiron'un evrensel şifası arasındaki zıtlığı dengelemek için 'Bireysel Duygusal Şifa' pratiği yapın: her biriniz kendi duygusal şifa yolunuzu takip edin, ardından bu deneyimleri birlikte paylaşarak ortak bir duygusal şifa vizyonu oluşturun. Bu denge, hem bireysel duygusal şifayı hem de ortak iyileşmeyi destekleyecektir.",
                        "Merkür-Merkür-0": "Öneri: İkinizin de benzer zihinsel titresimlarda titreştiği bu kavuşumda, birlikte zihinsel senkronizasyon ritüelleri oluşturun. Her sabah birlikte journal'a yazın ve düşüncelerinizi yüksek sesle paylaşın. Bu ritüel, zihinsel senkronizasyonunuzu derinleştirerek ortak entelektüel dünyanızı besleyecektir.",
                        "Merkür-Merkür-60": "Öneri: Zihinsel uyumunuzu korumak için haftada bir 'Bilgi Paylaşımı' oturumu düzenleyin. Birbirinize bu hafta öğrendiğiniz yeni bir şeyi anlatın ve ardından birlikte bu konuyu tartışın. Zihinsel alışverişlerinizi destekleyen bu pratik, doğal uyumunuzu besleyerek entelektüel bağınızı derinleştirecektir.",
                        "Merkür-Merkür-90": "Öneri: Zihinsel iletişim tarzlarınız arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) İletişimde 'Dinleme Molası' verin: her konuştuğunuzda 3 saniye durupdoğruın sözünü bitirmesini bekleyin.\n2) Düşüncelerinizi journal'a yazarak zihinsel karmaşayı dağıtın.\n3) Birlikte sesli kitap okuyarak iletişim tarzlarınızı senkronize edin.",
                        "Merkür-Merkür-120": "Öneri: Zihinsel doğal akışınızı korumak için birlikte okuma saati düzenleyin. Her akşam 20 dakika boyunca aynı kitabı okuyun ve ardından birbirinize düşüncelerinizi paylaşın. Bu ortak entelektüel deneyim, zihinsel bağınızı güçlendirerek iletişiminizi derinleştirecektir.",
                        "Merkür-Merkür-180": "Öneri: Zihinsel iletişim tarzlarınızdaki zıtlıkları dengelemek için 'İletişim Dansı' pratiği yapın: bir gün sadece dinleyin, ertesi gün sadece anlatın. Ardından bu deneyimleri paylaşarak iletişim tarzlarınızdaki zıtlıkların aslında birbirinizi nasıl tamamladığını keşfedin. Bu pratik, zihinsel ve duygusal köprülerinizi güçlendirecektir.",
                        "Merkür-Venüs-0": "Öneri: Merkür'ün zekası ile Venüs'ün sevgi dilinin kavuştuğu bu noktada, birlikte sevgi dolu iletişim ritüelleri oluşturun. Her akşam birbirinize sevgi dolu sözlerle hitap edin ve birlikte güzel müzik dinleyerek duygusal ve zihinsel deneyimlerinizi paylaşın. Bu enerji, iletişim ve sevgi bağınızı derinleştirerek romantik ve entelektüel ilişkinizi besleyecektir.",
                        "Merkür-Venüs-60": "Öneri: Merkür'ün zekası ile Venüs'ün zarafetinin uyumunu korumak için haftada bir 'Güzel İletişim' oturumu düzenleyin. Birlikte şiir okuyun, şarkı sözleri analiz edin veya birlikte güzel bir mektup yazın. Bu pratik,gök uyumunuzu besleyerek zihinsel ve estetik bağınızı derinleştirecektir.",
                        "Merkür-Venüs-90": "Öneri: Merkür'ün rasyonelliği ile Venüs'ün duygusallığı arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Sevgi konuşmalarında mantıksal analizi bırakarak sadece duygulara odaklanın.\n2) Mantıksal tartışmalar sırasında sevgi dilini unutmayın.\n3) Birlikte hem duygusal hem de zihinsel denge pratiği yaparak iletişiminizi zenginleştirin.",
                        "Merkür-Venüs-120": "Öneri: Merkür'ün netliği ile Venüs'ün sevgisinin doğal uyumunu korumak için birlikte romantik yazma pratiği yapın. Birbirinize sevgi mektupları yazın veya birlikte romantik hikayeler oluşturun. Bu pratik, zihinsel ve duygusal bağınızı derinleştirerek yaratıcı iletişiminizi besleyecektir.",
                        "Merkür-Venüs-180": "Öneri: Merkür'ün rasyonelliği ile Venüs'ün duygusallığı arasındaki zıtlığı dengelemek için 'Denge Konuşması' pratiği yapın: her konuşmada hem mantıksal hem de duygusal perspektifleri birleştirin. Bu denge, hem zihinsel netliğinizi hem de duygusal derinliğinizi koruyarak iletişiminizi güçlendirecektir.",
                        "Merkür-Mars-0": "Öneri: Merkür'ün zekası ile Mars'ın savaşçı enerjisinin kavuştuğu bu noktada, birlikte tartışmalı ve aktif iletişim ritüelleri oluşturun. Her hafta birlikte güncel bir konuyu tartışın ve bu tartışmada zihinsel ve fiziksel enerjinizi birleştirin. Bu enerji, zihinsel cesaretinizi ve iletişim hızınızı güçlendirecektir.",
                        "Merkür-Mars-60": "Öneri: Merkür'ün zekası ile Mars'ın cesaretinin uyumunu korumak için haftada bir 'Aktif Zihin' etkinliği planlayın. Birlikte bulmaca çözün, strateji oyunları oynayın veya birlikte yeni bir konuda hızlı bir öğrenme pratiği yapın. Bu pratik, doğal uyumunuzu besleyerek zihinsel ve fiziksel bağınızı derinleştirecektir.",
                        "Merkür-Mars-90": "Öneri: Merkür'ün iletişim hızı ile Mars'ın saldırgan enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Tartışma anında 'Durdur ve Düşün' tekniğini kullanın: öfkeli bir cevap vermeden önce 10 saniye bekleyin.\n2) Fiziksel egzersiz birlikte yaparak saldırgan enerjiyi yapıcıya dönüştürün.\n3) Birlikte zihinsel şifa meditasyonu yaparak zihinsel dengenizi yeniden kurun.",
                        "Merkür-Mars-120": "Öneri: Merkür'ün netliği ile Mars'ın cesaretinin doğal uyumunu korumak için birlikte aktif zihinsel pratiği yapın. Hızlı okuma, zihinsel haritalama veya beyin fırtınası seansları yaparak zihinsel ve fiziksel enerjinizi birleştirin. Bu pratik, zihinsel cesaretinizi ve iletişim hızınızı besleyecektir.",
                        "Merkür-Mars-180": "Öneri: Merkür'ün içe dönüklüğü ile Mars'ın dışa dönüklüğü arasındaki zıtlığı dengelemek için 'Dengeli Zihin Savaşı' pratiği yapın: bir gün içe dönük zihinsel aktiviteler yapın (okuma, yazma), ertesi gün dışa dönük zihinsel aktiviteler yapın (tartışma, sunum). Bu denge, hem zihinsel derinliğinizi hem de iletişim cesaretinizi besleyecektir.",
                        "Merkür-Jüpiter-0": "Öneri: Merkür'ün zekası ile Jüpiter'in genişletici enerjisinin kavuştuğu bu noktada, birlikte bilgi ve bolluk ritüelleri oluşturun. Her sabah büyük düşüncelerinizi yüksek sesle paylaşın ve birlikte geniş vizyonlar geliştirin. Bu enerji, zihinsel bolluk bilincinizi ve ortak vizyonunuzu güçlendirecektir.",
                        "Merkür-Jüpiter-60": "Öneri: Merkür'ün zekası ile Jüpiter'in bereketinin uyumunu korumak için haftada bir 'Bilgi Bereketi' oturumu düzenleyin. Birbirinize bu hafta öğrendiğinizbereketli bilgileri anlatın ve birlikte şükran meditasyonu yapın. Bu pratik, doğal zihinsel bolluğunuzu besleyerek ortak bereketinizi artıracaktır.",
                        "Merkür-Jüpiter-90": "Öneri: Merkür'ün detaycılığı ile Jüpiter'in aşırı genişleme enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Fazla bilgi veya aşırı iyimserlik anında gerçekçi bir değerlendirme yapın.\n2) Detaylar ve geniş perspektifler arasında denge kurmak için strateji geliştirin.\n3) Birlikte sosyal sorumluluk projelerine katılarak zihinsel enerjinizi paylaşıma dönüştürün.",
                        "Merkür-Jüpiter-120": "Öneri: Merkür'ün netliği ile Jüpiter'in bereketinin doğal uyumunu korumak için birlikte bolluk meditasyonu yapın. Her sabah 10 dakika boyunca zihinsel bolluk ve refah imgeleri canlandırın ve ardından birlikte şükran duaları edin. Bu ritüel, zihinsel bolluk bilincinizi ve bereket akışınızı sürekli canlı tutacaktır.",
                        "Merkür-Jüpiter-180": "Öneri: Merkür'ün detaycılığı ile Jüpiter'in genişleticiliği arasındaki zıtlığı dengelemek için 'Ölçülü Bilgi Büyümesi' pratiği yapın: bireysel zihinsel hedeflerinizi ve ortak zihinsel hedeflerinizi dengeleyerek biroluşum planı oluşturun. Bu denge, hem bireysel zihinsel gelişiminizi hem de ortak zihinsel vizyonunuzu besleyecektir.",
                        "Merkür-Satürn-0": "Öneri: Merkür'ün zekası ile Satürn'ün disiplin enerjisinin kavuştuğu bu noktada, birlikte yapı ve öğrenme ritüelleri oluşturun. Haftalık bir çalışma planı oluşturun ve birbirinize hesap verin. Bu disiplin, zihinsel hedeflerinize ulaşmanızı sağlayarak ilişkinizin temelini güçlendirecektir.",
                        "Merkür-Satürn-60": "Öneri: Merkür'ün zekası ile Satürn'ün disiplininin uyumunu korumak için haftada bir 'Zihinsel Yapı' oturumu yapın. Birlikte zihinsel hedeflerinizi belirleyin ve bunlara ulaşmak için somut adımlar planlayın. Bu pratik, doğal disiplininizi besleyerek zihinsel sorumluluk duygunuzu güçlendirecektir.",
                        "Merkür-Satürn-90": "Öneri: Merkür'ün hızı ile Satürn'ün sınırlayıcı enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Zihinsel sınırları kabul etmeyi ve aynı anda yaratıcı olmayı öğrenmek için birlikte Mindfulness pratiği yapın.\n2) Zihinsel sorumlulukları adil bir şekilde paylaşmak için açık iletişim kurun.\n3) Ortak bir zihinsel yapı oluşturarak zihinsel karmaşayı yapısal güce dönüştürün.",
                        "Merkür-Satürn-120": "Öneri: Merkür'ün netliği ile Satürn'ün disiplininin doğal uyumunu korumak için birlikte uzun vadeli bir öğrenme planı oluşturun ve bu plana sadık kalın. Her ay ilerlemenizi değerlendirin ve birbirinizi teşvik edin. Bu yapı, zihinsel hedeflerinize ulaşmanızı sağlayarak ortak başarınızı ve güveninizi pekiştirecektir.",
                        "Merkür-Satürn-180": "Öneri: Merkür'ün hızı ile Satürn'ün kısıtlaması arasındaki zıtlığı dengelemek için 'Zihinsel Özgürlük ve Sorumluluk Dansı' pratiği yapın: zihinsel alanlarınızın ve ortak sorumluluklarınızın dengesini bulun. Her hafta birbirinize zihinsel alan tanıyın ve aynı zamanda ortak zihinsel yükümlülüklerinizi yerine getirin. Bu denge, hem zihinsel özgürlüğünüzü hem de ilişkisel güveninizi koruyacaktır.",
                        "Merkür-Uranüs-0": "Öneri: Merkür'ün zekası ile Uranüs'ün devrim enerjisinin kavuştuğu bu noktada, birlikte zihinsel yenilik ve değişim ritüelleri oluşturun. Her ay birlikte yeni bir teknoloji veya felsefi konu öğrenin ve bu deneyimleri tartışın. Bu enerji, ilişkize yeni zihinsel soluklar getirerek yaratıcı ve devrimci zihinsel bağınızı canlı tutacaktır.",
                        "Merkür-Uranüs-60": "Öneri: Merkür'ün zekası ile Uranüs'ün yenilikçiliğinin uyumunu korumak için haftada bir 'Zihinsel Yenilik' oturumu düzenleyin. Birlikte farklı bir konu hakkında araştırma yapın veya farklı bir zihinsel aktivite deneyin. Bu deneyimler, doğal yaratıcılığınızı besleyerek ilişkize taze zihinsel enerji katacaktır.",
                        "Merkür-Uranüs-90": "Öneri: Merkür'ün hızı ile Uranüs'ün ani değişim enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Zihinsel değişim anında 'Dur ve Al' tekniğini kullanın: ani bir fikir değişikliği yapmadan önce 24 saat bekleyin.\n2) Birbirinizin zihinsel bağımsızlığına saygı duyun ve aynı anda bağlantıda kalın.\n3) Ortak bir zihinsel vizyon oluşturarak bireysel zihinsel özgürlüğü ve ilişkisel bağlılığı dengeleyin.",
                        "Merkür-Uranüs-120": "Öneri: Merkür'ün netliği ile Uranüs'ün devrim enerjisinin doğal uyumunu korumak için birlikte vizyoner bir zihinsel proje oluşturun. Geleceğe yönelik yaratıcı zihinsel planlar yapın ve bu planları somutlaştırmak için birlikte çalışın. Bu pratik, yaratıcı zihinsel potansiyelinizi ve ortak vizyonunuzu güçlendirecektir.",
                        "Merkür-Uranüs-180": "Öneri: Merkür'ün içe dönüklüğü ile Uranüs'ün kolektif devrimi arasındaki zıtlığı dengelemek için 'Bireysel Zihinsel Devrim' pratiği yapın: hem bireysel zihinsel değişim hem de ortak zihinsel dönüşüm için zaman ayırın. Her hafta birlikte yeni bir zihinsel perspektif keşfedin ve bu perspektifi ilişkinize nasıl uygulayacağınızı tartışın. Bu denge, hem bireysel zihinsel özgürlüğünüzü hem de ilişkisel zihinsel dönüşümünüzü destekleyecektir.",
                        "Merkür-Neptün-0": "Öneri: Merkür'ün zekası ile Neptün'ün manevi enerjisinin kavuştuğu bu noktada, birlikte manevi ve zihinsel ritüeller oluşturun. Her sabah birlikte dua edin veya meditasyon yapın ve manevi ve zihinsel vizyonlarınızı paylaşın. Bu enerji, ruhsal ve zihinsel bağınızı derinleştirerek ilişkinizi manevi bir boyuta taşıyacaktır.",
                        "Merkür-Neptün-60": "Öneri: Merkür'ün zekası ile Neptün'ün manevi flöwsunun uyumunu korumak için haftada bir 'Manevi Zihin' oturumu düzenleyin. Birlikte müzik dinleyin, sanat eserlerini inceleyin veya doğada yürüyüş yaparak manevi ve zihinsel deneyimlerinizi paylaşın. Bu pratik, manevi ve zihinsel hassasiyetinizi ve yaratıcı ilhamınızı besleyecektir.",
                        "Merkür-Neptün-90": "Öneri: Merkür'ün netliği ile Neptün'ün bulanık enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Rüya günlüğü tutarak bilinçaltınızı keşfedin ve bu deneyimleri birbirinizle paylaşın.\n2) Manevi pratiğinizi somutlaştırarak illüzyonları ve gerçekleri dengeleyin.\n3) Birlikte gönüllülük yaparak manevi ve zihinsel enerjinizi somut eylemlere dönüştürün.",
                        "Merkür-Neptün-120": "Öneri: Merkür'ün netliği ile Neptün'ün manevi akışının doğal uyumunu korumak için birlikte manevi ve zihinsel bir yolculuk planlayın. Manevi mekanları ziyaret edin, meditasyon kamplarına katılın veya birlikte yaratıcı sanat pratiği yapın. Bu deneyim, manevi ve zihinsel bilinçliliğinizi ve ruhsal bağınızı derinleştirecektir.",
                        "Merkür-Neptün-180": "Öneri: Merkür'ün rasyonelliği ile Neptün'ün evrenselliği arasındaki zıtlığı dengelemek için 'Bireysel Manevi Zihin' pratiği yapın: her biriniz kendi manevi ve zihinsel yolunuzu takip edin, ardından bu deneyimleri birlikte paylaşarak ortak bir manevi ve zihinsel vizyon oluşturun. Bu denge, hem bireysel ruhsal ve zihinsel gelişimi hem de ortak manevi ve zihinsel bağı besleyecektir.",
                        "Merkür-Plüton-0": "Öneri: Merkür'ün zekası ile Plüton'un dönüştürücü enerjisinin kavuştuğu bu noktada, birlikte derin zihinsel dönüşüm ve yeniden doğum ritüelleri oluşturun. Her ay birlikte eski zihinsel kalıplarınızı bırakın ve yeni başlangıçlar yapın. Bu enerji, derin zihinsel dönüşümünüzü ve yeniden doğuşunuzu hızlandırarak ilişkinizi yeniden yapılandıracaktır.",
                        "Merkür-Plüton-60": "Öneri: Merkür'ün zekası ile Plüton'un derin transformasyonunun uyumunu korumak için haftada bir 'Zihinsel Dönüşüm Paylaşımı' oturumu düzenleyin. Birlikte eski zihinsel yaralarınızı iyileştirin ve yeni bir zihinsel kimlik oluşturun. Bu pratik, derin zihinsel dönüşümünüzü destekleyerek ilişkinizi yeniden yapılandıracaktır.",
                        "Merkür-Plüton-90": "Öneri: Merkür'ün hızı ile Plüton'un power struggle enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Zihinsel güç mücadelelerini fark edin ve bunları derin bir zihinsel analizine dönüştürün.\n2) Birbirinizin zihinsel gölgelerini kabul edin ve bu gölgelerle birlikte çalışın.\n3) Ortak bir zihinsel dönüşüm pratiği yaparak power struggle'ı ortak zihinsel güce dönüştürün.",
                        "Merkür-Plüton-120": "Öneri: Merkür'ün netliği ile Plüton'un derin dönüşümünün doğal uyumunu korumak için birlikte derin bir zihinsel şifa çalışması yapın. Psikolojik astroloji, enerji çalışması veya derin meditasyon pratiği yaparak içsel zihinsel dönüşümlerinizi destekleyin. Bu pratik, derin zihinsel dönüşümünüzü ve ruhsal yenilenmenizi hızlandıracaktır.",
                        "Merkür-Plüton-180": "Öneri: Merkür'ün rasyonelliği ile Plüton'un transformasyonu arasındaki zıtlığı dengelemek için 'Bireysel Zihinsel Dönüşüm' pratiği yapın: her biriniz kendi derin zihinsel dönüşümünüzü takip edin, ardından bu dönüşümleri birlikte paylaşarak ortak bir zihinsel yeniden doğum süreci geçirin. Bu denge, hem bireysel hem de ilişkisel zihinsel dönüşümü destekleyecektir.",
                        "Merkür-KAD-0": "Öneri: Merkür'ün zekası ile Kuzey Ay Düğümü'nün kadersel yolunun kavuştuğu bu noktada, birlikte zihinsel kaderinizi bilinçli şekilde yönlendirme pratiği yapın. Her sabah zihinsel kadersel niyetlerinizi yüksek sesle söyleyin ve birlikte kaderinizi şekillendiren zihinsel adımlar atın. Bu enerji, zihinsel kadersel yolunuzu ve ortak amacınızı güçlendirecektir.",
                        "Merkür-KAD-60": "Öneri: Merkür'ün zekası ile Kuzey Ay Düğümü'nün kadersel akışının uyumunu korumak için haftada bir 'Zihinsel Kader Paylaşımı' oturumu düzenleyin. Birbirinize zihinsel kadersel deneyimlerinizi anlatın ve birlikte zihinsel geleceğinizi planlayın. Bu pratik, zihinsel yola bağlılığınızı ve ortak amacınızı besleyecektir.",
                        "Merkür-KAD-90": "Öneri: Merkür'ün hızı ile Kuzey Ay Düğümü'nün kadersel zorlukları arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Zihinsel kadersel engelleri fırsat olarak yeniden çerçeveleyin.\n2) Birbirinize zihinsel hesap vererek kadersel yolunuzda ilerleyin.\n3) Ortak bir zihinsel kader vizyonu oluşturarak zorlukları birlikte aşın.",
                        "Merkür-KAD-120": "Öneri: Merkür'ün netliği ile Kuzey Ay Düğümü'nün kadersel akışının doğal uyumunu korumak için birlikte zihinsel kadersel bir proje başlatın. Bu proje, bireysel ve ortak zihinsel kaderinizi birleştirecek şekilde tasarlanmalıdır. Bu pratik, zihinsel kadersel potansiyelinizi ve ortak amacınızı gerçekleştirmenizi sağlayacaktır.",
                        "Merkür-KAD-180": "Öneri: Merkür'ün rasyonelliği ile Kuzey Ay Düğümü'nün kolektif kaderi arasındaki zıtlığı dengelemek için 'Bireysel Zihinsel Kader' pratiği yapın: her biriniz kendi zihinsel kadersel yolunuzu keşfedin, ardından bu deneyimleri birlikte paylaşarak ortak bir zihinsel kader vizyonu oluşturun. Bu denge, hem bireysel zihinsel kadersel potansiyeli hem de ortak amacın gerçekleşmesini destekleyecektir.",
                        "Merkür-Chiron-0": "Öneri: Merkür'ün zekası ile Chiron'un şifacı yarasının kavuştuğu bu noktada, birlikte derin zihinsel şifa ve iyileşme ritüelleri oluşturun. Her sabah birlikte zihinsel şifa meditasyonu yapın ve birbirinizin zihinsel yaralarını şifalandırma niyetinde bulunun. Bu enerji, derin zihinsel şifa sürecinizi ve birbirinize olan zihinsel şifa kapasitenizi güçlendirecektir.",
                        "Merkür-Chiron-60": "Öneri: Merkür'ün zekası ile Chiron'un şifa enerjisinin uyumunu korumak için haftada bir 'Zihinsel Şifa Paylaşımı' oturumu düzenleyin. Birbirinize zihinsel yaralarınızı anlatın ve birlikte zihinsel şifa pratiği yapın. Bu pratik, zihinsel şifa sürecinizi destekleyerek derin iyileşmenizi hızlandıracaktır.",
                        "Merkür-Chiron-90": "Öneri: Merkür'ün hızı ile Chiron'un kırılgan enerjisi arasındaki baskisi çözmek için şu 3 adımı uygulayın: 1) Zihinsel kırılganlık anında birbirinize alan tanıyın ve aynı anda destek olun.\n2) Zihinsel yaralarınızı şifalandırmak için profesyonel destek alın.\n3) Birlikte zihinsel şifa projeleri başlatarak yaralarınızı dönüştürücü güce dönüştürün.",
                        "Merkür-Chiron-120": "Öneri: Merkür'ün netliği ile Chiron'un şifa akışının doğal uyumunu korumak için birlikte zihinsel şifa banyosu veya enerji çalışması yapın. Doğanın iyileştirici gücünden faydalanarak birlikte zihinsel şifa deneyimleri yaşayın. Bu pratik, derin zihinsel şifa sürecinizi ve ruhsal iyileşmenizi destekleyecektir.",
                        "Merkür-Chiron-180": "Öneri: Merkür'ün rasyonelliği ile Chiron'un evrensel şifası arasındaki zıtlığı dengelemek için 'Bireysel Zihinsel Şifa' pratiği yapın: her biriniz kendi zihinsel şifa yolunuzu takip edin, ardından bu deneyimleri birlikte paylaşarak ortak bir zihinsel şifa vizyonu oluşturun. Bu denge, hem bireysel zihinsel şifayı hem de ortak iyileşmeyi destekleyecektir.",
                        "Venüs-Venüs-0": "Aşk dilinizdeki benzerlikleri kutlayın: 1. Aynı sevgi dilini keşfetmek için birlikte test yapın 2. Haftada bir minnettarlık günlüğü tutun 3. Birbirinize küçük hediyeler verme ritüeli oluşturun",
                        "Venüs-Venüs-60": "Uyumlu enerjinizi sanatsal projelere yönlendirin: 1. Birlikte resim, müzik veya dans aktivitesi planlayın 2. Aynı estetik zevklerinizi paylaşan bir alan yaratın 3. Ortak bir güzellik ritüeli geliştirin",
                        "Venüs-Venüs-90": "Değer çatışmalarını-dialogla aşın: 1. Para ve sevgi hakkındaki inançlarınızı birlikte yazın 2. Farklı zevkleri dengelemek için alternatif planlar yapın 3. Haftada bir duygusal ihtiyaçlarınızı paylaşın",
                        "Venüs-Venüs-120": "Aşkınızın bolluğunu başkalarıyla paylaşın: 1. Birlikte hayırseverlik projelerine katılın 2. Çevrenizdeki çiftlere ilham verin 3. Sevgi dolu bir ev atmosferi yaratmak için birlikte çalışın",
                        "Venüs-Venüs-180": "Zıt çekimlerinizi dengelemenin yollarını bulun: 1. Farklı sosyal ihtiyaçlarınızı kabul edin ve takvim oluşturun 2. Birbirinizin bağımsızlığına alan tanıyın 3. Ortak değerlerinizi güçlendirmek için meditasyon yapın",
                        "Venüs-Mars-0": "Tutku ve şefkati birleştirin: 1. Fiziksel yakınlığı duygusal bağla harmanlayan ritüeller geliştirin 2. Birlikte spor veya dans yapın 3. Romantik anları planlı oluşturun",
                        "Venüs-Mars-60": "Yaratıcı enerjinizi birlikte kanalize edin: 1. Ortak bir sanat projesi başlatın 2. Birlikte outdoor aktiviteler planlayın 3. Flörtöz enerjinizi oyunlara dönüştürün",
                        "Venüs-Mars-90": "Tutkuyu fiziksel aktivitelere yönlendirin: 1. Spor veya dans ile baskisi boşaltın 2. Tartışma anında 10 dakika mola verin 3. Ortak bir tutku projesi geliştirin",
                        "Venüs-Mars-120": "Aşk ve eylemi uyumlu hale getirin: 1. Birlikte hedefler belirleyin ve plan yapın 2. Romantik maceralar organize edin 3. Fiziksel ve duygusal yakınlığı dengeleyin",
                        "Venüs-Mars-180": "Çekim ve reddediş döngüsünü kırın: 1. İlişkideki oyunları fark edin ve iletişime geçin 2. Tutku ile bağımsızlık arasındaki dengeyi bulun 3. Birbirinize alan tanırken bağ kurun",
                        "Venüs-Jüpiter-0": "Bolluk ve sevgiyi birlikte genişletin: 1. Birlikte hayal kurun ve büyük planlar yapın 2. Şükran günlükleri tutun 3. Birlikte öğrenme ve büyüme fırsatları yaratın",
                        "Venüs-Jüpiter-60": "Sevginizi felsefi bir boyutla derinleştirin: 1. Birlikte kitap okuyun ve tartışın 2. Manevi pratikler geliştirin 3. Farklı kültürleri birlikte keşfedin",
                        "Venüs-Jüpiter-90": "Aşırılıkların farkında olun: 1. Harcama alışkanlıklarınızı birlikte gözden geçirin 2. Büyüme hevesinizi gerçekçi hedeflerle dengeleyin 3. Farklı beklentileri açıkça konuşun",
                        "Venüs-Jüpiter-120": "Sevgi ve bolluğu cömertçe paylaşın: 1. Birlikte hayırseverlik yapın 2. Misafirperverlik ritüelleri geliştirin 3. Birbirinizin büyümesini destekleyin",
                        "Venüs-Jüpiter-180": "Farklı değer sistemlerini uzlaştırın: 1. Para ve inanç konularında açık diyalog kurun 2. Birbirinizin felsefi perspektiflerine saygı gösterin 3. Ortak bir yaşam felsefesi oluşturun",
                        "Venüs-Satürn-0": "Sevgiye yapı ve sorumluluk katın: 1. İlişkiniz için net sınırlar belirleyin 2. Uzun vadeli hedefler için birlikte çalışın 3. Sadakatinizi somut eylemlerle gösterin",
                        "Venüs-Satürn-60": "Sevgi ve disiplini dengeleyin: 1. Düzenli ilişki bakımı ritüelleri oluşturun 2. Birbirinize karşı sabırlı olmayı öğrenin 3. Ortak sorumlulukları adaletle paylaşın",
                        "Venüs-Satürn-90": "Sevgideki sınırlamaları aşın: 1. İlişkideki korkularınızı birlikte yazın 2. Duygusal duvarları yıkmak için cesaret_pratikleri yapın 3. Güven inşası için küçük adımlar atın",
                        "Venüs-Satürn-120": "Sevgi ve olgunluğu harmanlayın: 1. Birlikte olgunluk yolculuğunu kutlayın 2. Uzun vadeli bağlılığınızı güçlendirin 3. Bilgelik ve şefkati ilişkiye taşıyın",
                        "Venüs-Satürn-180": "Sevgi ve kısıtlama arasındaki baskisi azaltın: 1. Özgürlük ve güvenlik ihtiyaçlarınızı dengeleyin 2. İlişkideki rolleri yeniden tanımlayın 3. Birbirinize alan tanırken sorumluluk alın",
                        "Venüs-Uranüs-0": "Sevgide yenilikçiliği kucaklayın: 1. İlişkinize spontane sürprizler ekleyin 2. Birbirinizin özgürlüğüne değer verin 3. Farklı ilişki modellerini keşfedin",
                        "Venüs-Uranüs-60": "Sevgi ve özgürlüğü uyumlu hale getirin: 1. Birlikte yeni deneyimler yaşayın 2. İlişkide esneklik ve yenilik geliştirin 3. Birbirinizin bireyselliğini kutlayın",
                        "Venüs-Uranüs-90": "Tutku ve bağımsızlık arasındaki baskisi yönetin: 1. Ani değişimlere karşı esnek olun 2. İlişkideki rutinleri kırın 3. Birbirinize alan tanırken bağ kurun",
                        "Venüs-Uranüs-120": "Sevgi ve devrimi birleştirin: 1. Toplumsal değişim için birlikte çalışın 2. İlişkinizi yenilikçi değerlerle besleyin 3. Birbirinizin vizyonunu destekleyin",
                        "Venüs-Uranüs-180": "Özgürlük ve yakınlık arasındaki dengeyi bulun: 1. Bağımsızlık ve birliktelik ihtiyaçlarınızı açıkça konuşun 2. İlişkide esnek sınırlar belirleyin 3. Birbirinize alan tanırken connected kalın",
                        "Venüs-Neptün-0": "Sevgiyi manevi boyutla derinleştirin: 1. Birlikte meditasyon veya dua yapın 2. Romantik hayallerinizi paylaşın 3. Sevginizi sanatsal ifadelerle besleyin",
                        "Venüs-Neptün-60": "Sevgi ve merhameti harmanlayın: 1. Birlikte hayırseverlik yapın 2. Birbirinize şefkatle bakın 3. Manevi bağlarınızı güçlendirmek için ritüeller geliştirin",
                        "Venüs-Neptün-90": "Illüzyon ve gerçeklik dengeleyin: 1. İlişkideki beklentilerinizi netleştirin 2. Duygusal bulanıklığı gidermek için iletişim kurun 3. Gerçekçi olmayan beklentileri bırakın",
                        "Venüs-Neptün-120": "Sevgiyi ilahi bir boyutta yaşayın: 1. Birlikte ruhani pratikler geliştirin 2. Sevginizi evrensel sevgiyle hizalayın 3. Birbirinizin ruhsal gelişimini destekleyin",
                        "Venüs-Neptün-180": "Sevgi ve kurbanlık arasındaki döngüyü kırın: 1. İlişkideki aldatma kalıplarını fark edin 2. Sınırlarınızı koruyarak sevgi verin 3. Kendinizi ve partnerinizi gerçekçi sevin",
                        "Venüs-Plüton-0": "Sevgiyi derinlemesine dönüştürün: 1. İlişkideki güç yapiylarini araştırın 2. Duygusal derinliklere inmek için güvenli alanlar yaratın 3. Birlikte gölge çalışmalar yapın",
                        "Venüs-Plüton-60": "Sevgi ve transformasyonu entegre edin: 1. Birlikte kişisel gelişim çalışın 2. İlişkideki eski kalıpları serbest bırakın 3. Yeniden doğuş ritüelleri geliştirin",
                        "Venüs-Plüton-90": "Tutku ve takıntı arasındaki çizgiyi belirleyin: 1. İlişkideki kontrol sorunlarını konuşun 2. Kıskançlık duygularınızı işleyin 3. Güven ve bağımsızlık dengeleyin",
                        "Venüs-Plüton-120": "Sevginin dönüştürücü gücünü kucaklayın: 1. Birlikte derin dönüşüm süreçlerinden geçin 2. İlişkinizi yeniden icat edin 3. Sevginizi güçlendirmek için.shadow work yapın",
                        "Venüs-Plüton-180": "Sevgi ve power mücadelelerini aşın: 1. İlişkideki manipulation fark edin 2. Güç dengesizliklerini düzeltmek için adımlar atın 3. Şeffaf ve dürüst iletişim kurun",
                        "Venüs-KAD-0": "Karmik derslerinizi sevgiyle öğrenin: 1. İlişkideki tekrar eden kalıpları analiz edin 2. Geçmiş yaşam inançlarınızı keşfedin 3. Karmik borçları affetme ritüelleriyle çözün",
                        "Venüs-KAD-60": "Sevgi ve karmik dengeyi uyumlu hale getirin: 1. Birlikte meditasyon yaparak karmik bağlantıları keşfedin 2. Affetme pratikleri geliştirin 3. Geçmiş derslerinizi sevgiyle entegre edin",
                        "Venüs-KAD-90": "Karmik derslerinizi sevgiyle aşın: 1. İlişkideki zorlukların karmik kökenlerini anlayın 2. Sabır ve kabul Pratikleri yapın 3. Döngüleri kırmak için bilinçli seçimler yapın",
                        "Venüs-KAD-120": "Karmik sevgi bağlarını kutlayın: 1. Birlikte karmik yolculuğunuzu kutlayın 2. Geçmiş derslerinizi minnetle karşılayın 3. Sevginizi karmik bilgelikle besleyin",
                        "Venüs-KAD-180": "Karmik çatışmaları sevgiyle dönüştürün: 1. İlişkideki karmik döngüleri tanıyın 2. Zıt karmik enerjileri dengelemek için çalışın 3. Affetme ve bırakma ritüelleri yapın",
                        "Venüs-Chiron-0": "Şifalı sevgi yaralarınızı birlikte iyileştirin: 1. İlişkideki hassas noktaları şefkatle ele alın 2. Birbirinizin yaralarını iyileştirmek için alan yaratın 3. Şifa meditasyonları yapın",
                        "Venüs-Chiron-60": "Sevgi ve şifayı doğal bir şekilde harmanlayın: 1. Birlikte şifa çalışmaları yapın 2. Birbirinize şefkatle dinleyin 3. İyileşme süreçlerinizi destekleyin",
                        "Venüs-Chiron-90": "Sevgideki yaraları şifaya dönüştürün: 1. İlişkideki acı verici tetikleyicileri belirleyin 2. Güvenli iletişim teknikleri öğrenin 3. Profesyonel destek almaktan çekinmeyin",
                        "Venüs-Chiron-120": "Sevgi ve şifa birleşimini kutlayın: 1. Birlikte şifa yolculuğunuzu kutlayın 2. İyileşme hikayelerinizi paylaşın 3. Şifalı sevgi pratiğinizi derinleştirin",
                        "Venüs-Chiron-180": "Sevgi ve yaralanma arasındaki baskisi azaltın: 1. İlişkideki yaraları inkar etmeyin 2. Şifa için sabırlı olun 3. Birbirinize destek olurken sınırlarınızı koruyun",
                        "Mars-Mars-0": "Enerjinizi birlikte kanalize edin: 1. Birlikte spor veya rekabetçi aktiviteler yapın 2. Ortak hedefler için birlikte çalışın 3. Enerji fazlalığını yaratıcı projelere yönlendirin",
                        "Mars-Mars-60": "Enerji ve aksiyonu uyumlu hale getirin: 1. Birlikte macera planları yapın 2. Ortak fiziksel hedefler belirleyin 3. Enerjinizi pozitif rekabetle besleyin",
                        "Mars-Mars-90": "Enerji çatışmalarını yapıcıya dönüştürün: 1. Rekabet duygularını fark edin ve yönetin 2. Birlikte spor yaparak baskisi boşaltın 3. Ortak bir hedef için birleşin",
                        "Mars-Mars-120": "Enerji ve aksiyonun gücünü birleştirin: 1. Birlikte büyük projeler başlatın 2. Fiziksel hedefler için birlikte çalışın 3. Enerjinizi toplumsal fayda için kullanın",
                        "Mars-Mars-180": "Zıt enerji yönlendirmelerini dengeleyin: 1. Farklı enerji seviyelerinizi kabul edin 2. Birbirinize alan tanırken birlikte çalışın 3. Enerji akışını iletişimle koordine edin",
                        "Mars-Jüpiter-0": "Enerjinizi büyük vizyonlara yönlendirin: 1. Birlikte cesur planlar yapın 2. Fiziksel ve zihinsel enerjinizi birleştirin 3. Macera ve büyüme için fırsatlar yaratın",
                        "Mars-Jüpiter-60": "Enerji ve bolluğu uyumlu hale getirin: 1. Birlikte yeni deneyimler yaşayın 2. Enerjinizi öğrenme ve keşif için kullanın 3. Fiziksel aktiviteleri manevi pratiklerle harmanlayın",
                        "Mars-Jüpiter-90": "Aşırılıkların ve inatçılığın farkında olun: 1. Enerji fazlalığını yapıcı kanallara yönlendirin 2. Büyüme hevesinizi sabırla dengeleyin 3. Farklı inançları saygıyla karşılayın",
                        "Mars-Jüpiter-120": "Enerji ve bolluğu cömertçe paylaşın: 1. Birlikte hayırseverlik yapın 2. Fiziksel enerjinizle topluma hizmet edin 3. Büyüme ve genişleme için birlikte çalışın",
                        "Mars-Jüpiter-180": "Enerji ve inanç arasındaki baskisi azaltın: 1. Fiziksel enerji ve ruhsal gelişimi dengeleyin 2. Farklı yaşam felsefelerini saygıyla karşılayın 3. Ortak bir vizyon oluşturmak için çalışın",
                        "Mars-Satürn-0": "Enerji ve disiplini birleştirin: 1. Hedeflerinizi netleştirin ve plan yapın 2. Sabırlı ve kararlı olun 3. Fiziksel enerjinizi yapılandırılmış aktivitelerle kullanın",
                        "Mars-Satürn-60": "Enerji ve olgunluğu dengeleyin: 1. Sabır ve kararlılığı birlikte pratiğe dökün 2. Uzun vadeli hedefler için çalışın 3. Enerjinizi sorumluluklarınızla harmanlayın",
                        "Mars-Satürn-90": "Enerji ve kısıtlama arasındaki baskisi yönetin: 1. Sabırsızlık duygularını fark edin 2. Enerji fazlalığını fiziksel aktivitelerle boşaltın 3. Sınırlamaları kabul ederken harekete geçin",
                        "Mars-Satürn-120": "Enerji ve yapıyı güçlü bir şekilde birleştirin: 1. Disiplinli bir egzersiz rutini oluşturun 2. Hedeflerinize sistemli bir şekilde ilerleyin 3. Enerjinizi uzun vadeli başarı için kullanın",
                        "Mars-Satürn-180": "Enerji ve kısıtlama arasındaki dengeyi bulun: 1. Fiziksel enerji ve yapısal sınırları dengeleyin 2. Farklı enerji seviyelerinizi kabul edin 3. Birlikte esnek bir plan oluşturun",
                        "Mars-Uranüs-0": "Enerjinizi devrimci enerji için kullanın: 1. Birlikte yenilikçi projeler başlatın 2. Spontane enerjiyi yapıcı kanallara yönlendirin 3. Özgürlüğünüzü birlikte kutlayın",
                        "Mars-Uranüs-60": "Enerji ve yeniliği uyumlu hale getirin: 1. Birlikte yeni deneyimler yaşayın 2. Enerjinizi yaratıcı projeler için kullanın 3. Değişime açık olun ve birbirinizi destekleyin",
                        "Mars-Uranüs-90": "Ani enerji değişimlerini yönetin: 1. Ani tepkiler vermekten kaçının 2. Enerji fazlığını fiziksel aktivitelerle boşaltın 3. Değişime esnek bir şekilde yaklaşın",
                        "Mars-Uranüs-120": "Enerji ve devrimi güçlü bir şekilde birleştirin: 1. Birlikte toplumsal değişim için çalışın 2. Enerjinizi yenilikçi projeler için kullanın 3. Birbirinizin vizyonunu destekleyin",
                        "Mars-Uranüs-180": "Enerji ve özgürlük arasındaki baskisi azaltın: 1. Fiziksel enerji ve bağımsızlık ihtiyaçlarını dengeleyin 2. Farklı enerji yönlendirmelerini kabul edin 3. Birlikte esnek bir plan oluşturun",
                        "Mars-Neptün-0": "Enerjinizi manevi amaçlar için kullanın: 1. Birlikte meditasyon veya dua yapın 2. Fiziksel enerjinizi ruhsal pratiklerle harmanlayın 3. Hayallerinizi eyleme dönüştürün",
                        "Mars-Neptün-60": "Enerji ve maneviyatı uyumlu hale getirin: 1. Birlikte şifa çalışmaları yapın 2. Fiziksel aktiviteleri ruhsal pratiklerle birleştirin 3. Hayallerinizi birlikte gerçekleştirin",
                        "Mars-Neptün-90": "Enerji ve belirsizlik arasındaki baskisi yönetin: 1. Enerji fazlığını yaratıcı aktivitelerle boşaltın 2. Net hedefler belirleyerek belirsizliği azaltın 3. Manevi rehberlik için meditasyon yapın",
                        "Mars-Neptün-120": "Enerji ve ilhamı güçlü bir şekilde birleştirin: 1. Birlikte sanatsal projeler geliştirin 2. Fiziksel enerjinizi ilham verici amaçlar için kullanın 3. Manevi vizyonunuzu eyleme dönüştürün",
                        "Mars-Neptün-180": "Enerji ve hayal kırıklığı arasındaki dengeyi bulun: 1. Gerçekçi hedefler belirleyin 2. Enerji fazlığını yapıcı kanallara yönlendirin 3. Manevi pratiklerle enerjinizi yenileyin",
                        "Mars-Plüton-0": "Enerjinizi derin transformasyon için kullanın: 1. Birlikte gölge çalışmalar yapın 2. Fiziksel enerjinizi dönüşüm projeleri için kullanın 3. Güç yapiylarini sağlıklı bir şekilde yönetin",
                        "Mars-Plüton-60": "Enerji ve gücü uyumlu hale getirin: 1. Birlikte güçlü projeler başlatın 2. Fiziksel enerjinizi kişisel gelişim için kullanın 3. Güçlü bir birliktelik oluşturun",
                        "Mars-Plüton-90": "Enerji ve power mücadelelerini yönetin: 1. Kontrol sorunlarını fark edin 2. Enerji fazlığını fiziksel aktivitelerle boşaltın 3. Güç dengesizliklerini iletişimle düzeltin",
                        "Mars-Plüton-120": "Enerji ve dönüştürücü gücü birleştirin: 1. Birlikte büyük değişimler için çalışın 2. Fiziksel enerjinizi toplumsal dönüşüm için kullanın 3. Güçlü bir vizyon oluşturun",
                        "Mars-Plüton-180": "Enerji ve yıkıcı güç arasındaki dengeyi bulun: 1. Enerji fazlını yapıcı kanallara yönlendirin 2. Güç mücadelelerini barışçıl diyalogla çözün 3. Transformasyon için sabırlı olun",
                        "Mars-KAD-0": "Karmik enerjilerinizi eyleme dönüştürün: 1. İlişkideki karmik döngüleri fark edin 2. Fiziksel enerjinizi karmik dersleri öğrenmek için kullanın 3. Geçmiş kalıplarını kırmak için harekete geçin",
                        "Mars-KAD-60": "Enerji ve karmik dengeyi uyumlu hale getirin: 1. Birlikte karmik meditasyonlar yapın 2. Fiziksel enerjinizi karmik denge için kullanın 3. Geçmiş derslerinizi eyleme dönüştürün",
                        "Mars-KAD-90": "Karmik enerjiler ve kısıtlamalar arasındaki baskisi yönetin: 1. Karmik döngüleri kırmak için sabırlı olun 2. Enerji fazlığını fiziksel aktivitelerle boşaltın 3. Karmik dersleri öğrenmek için çaba gösterin",
                        "Mars-KAD-120": "Karmik enerji ve eylemi güçlü bir şekilde birleştirin: 1. Birlikte karmik hedefler için çalışın 2. Fiziksel enerjinizi karmik denge için kullanın 3. Karmik derslerinizi uygulamaya dökün",
                        "Mars-KAD-180": "Karmik enerji ve kısıtlama arasındaki dengeyi bulun: 1. Karmik döngüleri kabul edin ve çalışın 2. Fiziksel enerji ve yapısal sınırları dengeleyin 3. Birlikte esnek bir karmik plan oluşturun",
                        "Mars-Chiron-0": "Enerjinizi şifa için kullanın: 1. Birlikte şifa çalışmaları yapın 2. Fiziksel enerjinizi iyileşme süreçleri için kullanın 3. Yaralarınızı birlikte şifaya dönüştürün",
                        "Mars-Chiron-60": "Enerji ve şifayı uyumlu hale getirin: 1. Birlikte şifa meditasyonları yapın 2. Fiziksel aktiviteleri şifa pratikleriyle birleştirin 3. Birbirinizi iyileşme süreçlerinde destekleyin",
                        "Mars-Chiron-90": "Enerji ve yaralanma arasındaki baskisi yönetin: 1. Enerji fazlığını fiziksel aktivitelerle boşaltın 2. Yaralarınızı şifaya dönüştürmek için çaba gösterin 3. Profesyonel destek almaktan çekinmeyin",
                        "Mars-Chiron-120": "Enerji ve şifa gücünü güçlü bir şekilde birleştirin: 1. Birlikte büyük şifa projeleri başlatın 2. Fiziksel enerjinizi toplumsal şifa için kullanın 3. Şifalı bir birliktelik oluşturun",
                        "Mars-Chiron-180": "Enerji ve yaralanma arasındaki dengeyi bulun: 1. Enerji fazlını yapıcı kanallara yönlendirin 2. Yaralarınızı şifaya dönüştürmek için sabırlı olun 3. Birlikte şifa yolculuğunda yürüyün",
                        "Jüpiter-Jüpiter-0": "Büyüme ve bolluğu birlikte genişletin: 1. Birlikte büyük hayaller kurun 2. Fırsatları birlikte değerlendirin 3. Genişleme ve öğrenme için birlikte çalışın",
                        "Jüpiter-Jüpiter-60": "Büyüme ve bolluğu uyumlu hale getirin: 1. Birlikte yeni öğrenme fırsatları keşfedin 2. Felsefi tartışmalar yapın 3. Manevi pratikler geliştirin",
                        "Jüpiter-Jüpiter-90": "Aşırılıklar ve farklı inançlar arasındaki baskisi yönetin: 1. Farklı bakış açılarını saygıyla karşılayın 2. Büyüme hevesinizi gerçekçi hedeflerle dengeleyin 3. Açık ve yapıcı iletişim kurun",
                        "Jüpiter-Jüpiter-120": "Büyüme ve bolluğu cömertçe paylaşın: 1. Birlikte hayırseverlik yapın 2. Öğrenme ve öğretme fırsatları yaratın 3. Toplumsal fayda için birlikte çalışın",
                        "Jüpiter-Jüpiter-180": "Farklı inanç ve değer sistemleri arasındaki dengeyi bulun: 1. Felsefi farklılıkları saygıyla karşılayın 2. Ortak değerlerinizi keşfedin 3. Birlikte kapsamlı bir dünya görüşü oluşturun",
                        "Jüpiter-Satürn-0": "Büyüme ve yapıyı dengeleyin: 1. Uzun vadeli hedefler belirleyin 2. Büyüme için yapılandırılmış planlar yapın 3. Sabırlı ve kararlı olun",
                        "Jüpiter-Satürn-60": "Büyüme ve disiplini uyumlu hale getirin: 1. Öğrenme için düzenli bir program oluşturun 2. Fırsatları gerçekçi bir şekilde değerlendirin 3. Büyüme ve yapıyı birlikte pratiğe dökün",
                        "Jüpiter-Satürn-90": "Büyüme ve kısıtlama arasındaki baskisi yönetin: 1. Büyük hayaller ve gerçekçi planlar arasında denge kurun 2. Sabırsızlık duygularını fark edin 3. Büyüme için sabırlı ve kararlı olun",
                        "Jüpiter-Satürn-120": "Büyüme ve yapıyı güçlü bir şekilde birleştirin: 1. Uzun vadeli başarı için yapılandırılmış planlar yapın 2. Bilgelik ve disiplini birlikte kullanın 3. Büyüme ve olgunluğu harmanlayın",
                        "Jüpiter-Satürn-180": "Büyüme ve kısıtlama arasındaki dengeyi bulun: 1. Farklı enerji seviyelerinizi kabul edin 2. Birlikte esnek bir plan oluşturun 3. Büyüme ve yapıyı dengelemek için iletişim kurun",
                        "Jüpiter-Uranüs-0": "Büyüme ve devrimi birlikte kucaklayın: 1. Birlikte yenilikçi projeler başlatın 2. Fırsatları spontane bir şekilde değerlendirin 3. Özgürlük ve genişleme için birlikte çalışın",
                        "Jüpiter-Uranüs-60": "Büyüme ve yeniliği uyumlu hale getirin: 1. Birlikte yeni deneyimler yaşayın 2. Fırsatları yaratıcı bir şekilde değerlendirin 3. Değişime açık ve maceracı olun",
                        "Jüpiter-Uranüs-90": "Büyüme ve ani değişimler arasındaki baskisi yönetin: 1. Ani fırsatlara karşı esnek olun 2. Büyüme hevesinizi gerçekçi hedeflerle dengeleyin 3. Değişime adaptasyon becerilerinizi geliştirin",
                        "Jüpiter-Uranüs-120": "Büyüme ve devrimi güçlü bir şekilde birleştirin: 1. Birlikte toplumsal değişim için çalışın 2. Fırsatları yenilikçi bir şekilde değerlendirin 3. Vizyoner projeler başlatın",
                        "Jüpiter-Uranüs-180": "Büyüme ve özgürlük arasındaki baskisi azaltın: 1. Farklı vizyonları saygıyla karşılayın 2. Ortak bir hedef için birleşin 3. Birlikte esnek bir plan oluşturun",
                        "Jüpiter-Neptün-0": "Büyüme ve maneviyatı derinleştirin: 1. Birlikte ruhani pratikler geliştirin 2. Fırsatları manevi değerlerinizle hizalayın 3. Hayallerinizi birlikte gerçekleştirin",
                        "Jüpiter-Neptün-60": "Büyüme ve ilhamı uyumlu hale getirin: 1. Birlikte sanatsal projeler geliştirin 2. Manevi fırsatları değerlendirin 3. Hayallerinizi eyleme dönüştürmek için çalışın",
                        "Jüpiter-Neptün-90": "Büyüme ve hayal kırıklığı arasındaki baskisi yönetin: 1. Gerçekçi hedefler belirleyerek hayal kırıklığını azaltın 2. Manevi rehberlik için meditasyon yapın 3. Fırsatları gerçekçi bir şekilde değerlendirin",
                        "Jüpiter-Neptün-120": "Büyüme ve ilhamı güçlü bir şekilde birleştirin: 1. Birlikte vizyoner projeler başlatın 2. Manevi fırsatları eyleme dönüştürün 3. Hayallerinizi gerçekleştirmek için birlikte çalışın",
                        "Jüpiter-Neptün-180": "Büyüme ve hayal kırıklığı arasındaki dengeyi bulun: 1. Farklı vizyonları saygıyla karşılayın 2. Gerçekçi ve manevi hedefler belirleyin 3. Birlikte dengeli bir plan oluşturun",
                        "Jüpiter-Plüton-0": "Büyüme ve dönüşümü derinleştirin: 1. Birlikte derin dönüşüm süreçlerinden geçin 2. Fırsatları dönüştürücü bir şekilde değerlendirin 3. Güçlü bir vizyon oluşturun",
                        "Jüpiter-Plüton-60": "Büyüme ve transformasyonu uyumlu hale getirin: 1. Birlikte güçlü projeler başlatın 2. Fırsatları kişisel gelişim için kullanın 3. Dönüşüm ve genişlemeyi harmanlayın",
                        "Jüpiter-Plüton-90": "Büyüme ve güç mücadeleleri arasındaki baskisi yönetin: 1. Kontrol sorunlarını fark edin 2. Fırsatları adil ve eşit bir şekilde değerlendirin 3. Güç dengesizliklerini iletişimle düzeltin",
                        "Jüpiter-Plüton-120": "Büyüme ve dönüştürücü gücü güçlü bir şekilde birleştirin: 1. Birlikte büyük değişimler için çalışın 2. Fırsatları toplumsal dönüşüm için kullanın 3. Güçlü bir vizyon oluşturun",
                        "Jüpiter-Plüton-180": "Büyüme ve yıkıcı güç arasındaki dengeyi bulun: 1. Fırsatları yapıcı kanallara yönlendirin 2. Güç mücadelelerini barışçıl diyalogla çözün 3. Dönüşüm için sabırlı olun",
                        "Jüpiter-KAD-0": "Karmik büyüme fırsatlarını değerlendirin: 1. İlişkideki karmik döngüleri fark edin 2. Büyüme için karmik dersleri öğrenin 3. Geçmiş kalıplarını kırmak için genişleme enerjisini kullanın",
                        "Jüpiter-KAD-60": "Büyüme ve karmik dengeyi uyumlu hale getirin: 1. Birlikte karmik meditasyonlar yapın 2. Büyüme fırsatlarını karmik denge için kullanın 3. Geçmiş derslerinizi genişleme enerjisiyle entegre edin",
                        "Jüpiter-KAD-90": "Karmik büyüme ve kısıtlamalar arasındaki baskisi yönetin: 1. Karmik döngüleri kırmak için sabırlı olun 2. Büyüme fırsatlarını gerçekçi bir şekilde değerlendirin 3. Karmik dersleri öğrenmek için çaba gösterin",
                        "Jüpiter-KAD-120": "Karmik büyüme ve genişlemeyi güçlü bir şekilde birleştirin: 1. Birlikte karmik hedefler için çalışın 2. Büyüme fırsatlarını karmik denge için kullanın 3. Karmik derslerinizi uygulamaya dökün",
                        "Jüpiter-KAD-180": "Karmik büyüme ve kısıtlama arasındaki dengeyi bulun: 1. Karmik döngüleri kabul edin ve çalışın 2. Büyüme ve yapısal sınırları dengeleyin 3. Birlikte esnek bir karmik plan oluşturun",
                        "Jüpiter-Chiron-0": "Büyüme ve şifayı derinleştirin: 1. Birlikte şifa çalışmaları yapın 2. Büyüme fırsatlarını iyileşme süreçleri için kullanın 3. Yaralarınızı birlikte şifaya dönüştürün",
                        "Jüpiter-Chiron-60": "Büyüme ve şifayı uyumlu hale getirin: 1. Birlikte şifa meditasyonları yapın 2. Büyüme fırsatlarını şifa pratikleriyle birleştirin 3. Birbirinizi iyileşme süreçlerinde destekleyin",
                        "Jüpiter-Chiron-90": "Büyüme ve yaralanma arasındaki baskisi yönetin: 1. Büyüme fırsatlarını yaralarınızı şifaya dönüştürmek için kullanın 2. Gerçekçi hedefler belirleyerek hayal kırıklığını azaltın 3. Profesyonel destek almaktan çekinmeyin",
                        "Jüpiter-Chiron-120": "Büyüme ve şifa gücünü güçlü bir şekilde birleştirin: 1. Birlikte büyük şifa projeleri başlatın 2. Büyüme fırsatlarını toplumsal şifa için kullanın 3. Şifalı bir genişleme yolculuğu oluşturun",
                        "Jüpiter-Chiron-180": "Büyüme ve yaralanma arasındaki dengeyi bulun: 1. Farklı vizyonları saygıyla karşılayın 2. Gerçekçi ve şifalı hedefler belirleyin 3. Birlikte dengeli bir şifa planı oluşturun",
                        "Satürn-Satürn-0": "Öneri: İkinizdeki disiplin ve sorumluluk enerjisini birleştirmek için ortak bir yaşam planı oluşturun. Her sabah birlikte kısa bir meditasyon yaparak günün yüklerini paylaşın. Birbirinizin sınırlarına saygı duyarak güçlü bir temel inşa edin.",
                        "Satürn-Satürn-60": "Öneri: Ortak sorumluluklarınızı yapıcı bir şekilde düzenleyin. Birlikte küçük hedefler koyarak adım adım ilerleyin. Haftalık kontrol noktaları belirleyin ve birbirinize destek olun.",
                        "Satürn-Satürn-90": "Öneri: Disiplin ve korku kalıplarını birlikte aşmak için bireysel terapiye başlayın. Birbirinize karşı sabırlı olmayı öğrenmek için iletişimi açık tutun. Ortak sorumlulukları adil bir şekilde paylaşarak baskisi azaltın.",
                        "Satürn-Satürn-120": "Öneri: Uyumlu disiplin enerjinizi birleştirerek uzun vadeli projeler geliştirin. Birlikte bir mentorluk programına katılın. Sorumluluk paylaşımı yaparak birbirinize destek olun.",
                        "Satürn-Satürn-180": "Öneri: Zıt disiplin anlayışlarınızı dengelemek için esnek kurallar koyun. Birinizin güçlü olduğu alanlarda diğerine destek olun. Kontrol ihtiyacı ve özgürlük isteği arasındaki dengeyi konuşarak bulun.",
                        "Satürn-Uranüs-0": "Öneri: Güvenlik ve değişim ihtiyacınızı birleştirmek için esnek bir yapı oluşturun. Her ay birlikte yeni bir deneyim yaşayın. Değişimi tehdit değil, büyüme fırsatı olarak görün.",
                        "Satürn-Uranüs-60": "Öneri: Yapıyı esneklikle dengelemek için birlikte yaratıcı projeler geliştirin. Geleneksel yöntemleri yenilikçi yaklaşımlarla harmanlayın. Değişimi desteklerken güvenli bir alan yaratın.",
                        "Satürn-Uranüs-90": "Öneri: Güvenlik ve özgürlük arasındaki baskisi çözmek için bireysel alan sınırlarını netleştirin. Her hafta birlikte yeni bir aktivite deneyerek değişime open olun. Kontrol ihtiyacınızı bırakarak birbirinize güvenmeyi öğrenin.",
                        "Satürn-Uranüs-120": "Öneri: Yapıyı yenilikle birleştirerek yaratıcı çözümler üretin. Birlikte gelecek planları yaparken esnek kalın. Değişimi yapı içinde nasıl entegre edeceğinizi birlikte öğrenin.",
                        "Satürn-Uranüs-180": "Öneri: Geleneksel ve devrimci yaklaşımlarınız arasındaki dengeyi bulun. Birbirinizin farklılıklarını kabul ederek ortak bir yol oluşturun. Özgürlük ve sorumluluk arasındaki dengeyi birlikte test edin.",
                        "Satürn-Neptün-0": "Öneri: Gerçekçilik ve idealizm enerjinizi birleştirmek için net sınırlar koyun. Birlikte manevi bir pratiğe başlayın ama günlük hayatı da ihmal etmeyin. Hayallerinizi somut adımlara dönüştürmek için bir plan yapın.",
                        "Satürn-Neptün-60": "Öneri: Disiplini sezgiyle harmanlayarak yaratıcı projeler geliştirin. Birlikte sanatsal aktivitelere katılın ama düzenli bir program da oluşturun. Manevi pratiğinizi günlük yaşamınıza entegre edin.",
                        "Satürn-Neptün-90": "Öneri: Korku ve hayal kırıklığı arasındaki baskisi çözmek için net iletişim kurun. Birbirinize karşı şeffaf olun ve gerçekçi beklentiler belirleyin. Hayalperestlik ve katı gerçekçilik arasındaki dengeyi bulun.",
                        "Satürn-Neptün-120": "Öneri: Yapıyı maneviyatla birleştirerek anlamlı bir yaşam oluşturun. Birlikte meditasyon veya yoga yaparak iç huzuru bulun. Hayallerinizi somut hedeflere dönüştürmek için adım adım ilerleyin.",
                        "Satürn-Neptün-180": "Öneri: Gerçekçilik ve idealizm arasındaki dengeyi bulmak için birbirinizi anlamaya çalışın. Birinizin güçlü olduğu alanlarda diğerine destek olun. Hayal kırıklıklarını birlikte aşmak için şefkatli iletişim kurun.",
                        "Satürn-Plüton-0": "Öneri: Güç ve kontrol enerjinizi birleştirmek için ortak bir misyon belirleyin. Birlikte derin bir dönüşüm pratiği yapın. Eski kalıpları kırmak için cesur adımlar atın ama destek sistemini de koruyun.",
                        "Satürn-Plüton-60": "Öneri: Disiplini güçlendirerek derin değişimler yaratın. Birlikte zorlu projeleri tamamlama konusunda birbirinize destek olun. Kontrolü bırakarak güvenli bir dönüşüm alanı yaratın.",
                        "Satürn-Plüton-90": "Öneri: Kontrol ve güç mücadelelerini çözmek için bireysel güç kaynaklarınızı keşfedin. Birbirinize karşı manipüle etmeden açık iletişim kurun. Güç dengesizliklerini kabul ederek ortak bir çözüm bulun.",
                        "Satürn-Plüton-120": "Öneri: Yapı ve dönüşüm enerjinizi birleştirerek güçlü bir ortaklık kurun. Birlikte uzun vadeli bir değişim planı yapın. Güçlü yanlarınızı birleştirerek ortak hedeflere ulaşın.",
                        "Satürn-Plüton-180": "Öneri: Kontrol ve güç arasındaki dengeyi bulmak için bireysel gölgelerinizi kabul edin. Birbirinizin güç kaynaklarını tanıyarak saygı gösterin. Güç mücadelelerini yapıcı diyaloğa dönüştürmek için çaba gösterin.",
                        "Satürn-KAD-0": "Öneri: Disiplininiz ve kadersel yolunuz birleşirken sorumluluklarınızı netleştirin. Birlikte gelecek planları yaparak somut hedefler belirleyin. Eski alışkanlıkları bırakarak yeni bir yaşam tarzı oluşturun.",
                        "Satürn-KAD-60": "Öneri: Yapınızı kadersel yönünüzle harmanlayarak anlamlı bir yolculuk başlatın. Birlikte bir mentorluk programına katılın. Sorumluluklarınızı yerine getirerek ruhsal gelişiminizi destekleyin.",
                        "Satürn-KAD-90": "Öneri: Korkularınız ve kadersel yolunuz arasındaki baskisi çözmek için cesaret toplayın. Birlikte zorlu deneyimlerden dersler çıkarın. Eski kalıpları kırmak için bireysel çalışma yapın.",
                        "Satürn-KAD-120": "Öneri: Disiplininiz ve kadersel yönünüz uyum içinde ilerlerken birlikte projeler geliştirin. Sorumluluklarınızı yerine getirerek ruhsal hedeflerinize ulaşın. Destekleyici bir ortam yaratın.",
                        "Satürn-KAD-180": "Öneri: Güvenlik ihtiyacınız ve kadersel yolunuz arasındaki dengeyi bulun. Birbirinizin farklı yollarını anlayarak destek olun. Korkularınızı aşarak cesur adımlar atın.",
                        "Satürn-Chiron-0": "Öneri: Disiplininiz ve yaralarınız birleşirken şifa sürecinizi yapılandırın. Birlikte bireysel terapiye katılın. Eski yaraları kabul ederek yeni bir başlangıç yapın.",
                        "Satürn-Chiron-60": "Öneri: Yapınızı şifa enerjisiyle harmanlayarak iyileşme süreçleri başlatın. Birlikte şifa pratiği yapın. Yaralarınızı kabul ederek başkalarına da yardım edin.",
                        "Satürn-Chiron-90": "Öneri: Korku ve acı arasındaki baskisi çözmek için şefkatli iletişim kurun. Birbirinize karşı sabırlı olun. Eski yaraları iyileştirmek için profesyonel destek alın.",
                        "Satürn-Chiron-120": "Öneri: Disiplininiz ve şifa enerjiniz uyum içinde çalışırken birlikte derin bir iyileşme pratiği yapın. Yaralarınızı kabul ederek güçlü bir şifacı olun. Destekleyici bir ortam yaratın.",
                        "Satürn-Chiron-180": "Öneri: Kontrol ihtiyacı ve acı arasındaki dengeyi bulmak için bireysel çalışmalara katılın. Birbirinizin yaralarını anlayarak şefkat gösterin. Güçlü ve kırılgan yanlarınızı birlikte kucaklayın.",
                        "Uranüs-Uranüs-0": "Öneri: Özgürlük ve yenilik enerjinizi birleştirmek için birlikte devrimci projeler başlatın. Değişimi kucaklayarak sınırları zorlayın. Birbirinize destek olarak yaratıcılığınızı besleyin.",
                        "Uranüs-Uranüs-60": "Öneri: Yenilikçiliğinizi birleştirerek yaratıcı çözümler üretin. Birlikte teknoloji veya sanat projeleri geliştirin. Özgünlüğünüzü destekleyerek ortak değerler oluşturun.",
                        "Uranüs-Uranüs-90": "Öneri: Özgürlük ve bağımsızlık arasındaki baskisi çözmek içinadet alan sınırlarını netleştirin. Birbirinize karşı şeffaf olun. Değişimi desteklerken ortak bir vizyon oluşturun.",
                        "Uranüs-Uranüs-120": "Öneri: Yenilik enerjiniz uyum içinde çalışırken birlikte gelecek planları yapın. Değişimi destekleyerek yaratıcı projeler geliştirin. Birbirinize ilham vererek büyümeye devam edin.",
                        "Uranüs-Uranüs-180": "Öneri: Farklı yenilikçi yaklaşımlarınızı dengelemek için açık iletişim kurun. Birbirinizin özgünlüğünü kabul ederek ortak bir yol bulun. Bağımsızlık ve bağlantı arasındaki dengeyi test edin.",
                        "Uranüs-Neptün-0": "Öneri: Devrim ve sezgi enerjinizi birleştirmek için yaratıcı projeler başlatın. Birlikte meditasyon veya sanat pratiği yapın. Değişimi manevi bir perspektiften kucaklayın.",
                        "Uranüs-Neptün-60": "Öneri: Yenilikçiliğinizi sezgiyle harmanlayarak ilham verici projeler geliştirin. Birlikte bilinç genişletme aktivitelerine katılın. Değişimi sezgisel olarak yönlendirin.",
                        "Uranüs-Neptün-90": "Öneri: Devrim ve hayalperestlik arasındaki baskisi çözmek için net sınırlar koyun. Birbirinize karşı gerçekçi olun. Değişimi somut adımlara dönüştürmek için plan yapın.",
                        "Uranüs-Neptün-120": "Öneri: Yenilik ve maneviyat enerjiniz uyum içinde çalışırken birlikte derin bir keşif yolculuğuna çıkın. Değişimi sezgisel olarak yönlendirin. Birbirinize ilham vererek yaratıcılığınızı besleyin.",
                        "Uranüs-Neptün-180": "Öneri: Devrim ve idealizm arasındaki dengeyi bulmak için bireysel vizyonlarınızı paylaşın. Birbirinizin farklılıklarını anlayarak ortak bir yol bulun. Özgürlük ve maneviyat arasındaki dengeyi test edin.",
                        "Uranüs-Plüton-0": "Öneri: Devrim ve dönüşüm enerjinizi birleştirmek için güçlü bir ortaklık kurun. Birlikte toplumsal değişim projeleri başlatın. Eski sistemleri kırmak için cesur adımlar atın.",
                        "Uranüs-Plüton-60": "Öneri: Yenilikçiliğinizi güçlendirerek derin değişimler yaratın. Birlikte yenilikçi projeleri tamamlama konusunda birbirinize destek olun. Değişimi destekleyerek toplumsal etki yaratın.",
                        "Uranüs-Plüton-90": "Öneri: Devrim ve güç arasındaki baskisi çözmek için bireysel güç kaynaklarınızı keşfedin. Birbirinize karşı manipüle etmeden açık iletişim kurun. Güç dengesizliklerini kabul ederek ortak bir çözüm bulun.",
                        "Uranüs-Plüton-120": "Öneri: Yenilik ve dönüşüm enerjiniz uyum içinde çalışırken birlikte güçlü projeler geliştirin. Değişimi destekleyerek toplumsal etki yaratın. Birbirinize ilham vererek büyümeye devam edin.",
                        "Uranüs-Plüton-180": "Öneri: Devrim ve güç arasındaki dengeyi bulmak için bireysel gölgelerinizi kabul edin. Birbirinizin güç kaynaklarını tanıyarak saygı gösterin. Güç mücadelelerini yapıcı diyaloğa dönüştürmek için çaba gösterin.",
                        "Uranüs-KAD-0": "Öneri: Özgürlük ve kadersel yolunuz birleşirken yenilikçi adımlar atın. Birlikte gelecek planları yaparak cesur hedefler belirleyin. Eski kalıpları bırakarak yeni bir yaşam tarzı oluşturun.",
                        "Uranüs-KAD-60": "Öneri: Yenilikçiliğinizi kadersel yönünüzle harmanlayarak anlamlı bir yolculuk başlatın. Birlikte yenilikçi projeler geliştirin. Değişimi destekleyerek ruhsal gelişiminizi hızlandırın.",
                        "Uranüs-KAD-90": "Öneri: Özgürlük ve kadersel yönünüz arasındaki baskisi çözmek için cesaret toplayın. Birlikte zorlu deneyimlerden dersler çıkarın. Eski kalıpları kırmak için bireysel çalışma yapın.",
                        "Uranüs-KAD-120": "Öneri: Yenilik ve kadersel yönünüz uyum içinde ilerlerken birlikte projeler geliştirin. Değişimi destekleyerek ruhsal hedeflerinize ulaşın. Destekleyici bir ortam yaratın.",
                        "Uranüs-KAD-180": "Öneri: Özgürlük ve kadersel yolunuz arasındaki dengeyi bulun. Birbirinizin farklı yollarını anlayarak destek olun. Korkularınızı aşarak cesur adımlar atın.",
                        "Uranüs-Chiron-0": "Öneri: Yenilik ve şifa enerjiniz birleşirken yaratıcı iyileşme süreçleri başlatın. Birlikte yenilikçi terapi yöntemleri deneyin. Eski yaraları kabul ederek yeni bir başlangıç yapın.",
                        "Uranüs-Chiron-60": "Öneri: Yenilikçiliğinizi şifa enerjisiyle harmanlayarak yaratıcı projeler geliştirin. Birlikte şifa pratiği yapın. Yaralarınızı kabul ederek başkalarına da yardım edin.",
                        "Uranüs-Chiron-90": "Öneri: Özgürlük ve acı arasındaki baskisi çözmek için şefkatli iletişim kurun. Birbirinize karşı sabırlı olun. Eski yaraları iyileştirmek için yenilikçi yöntemler deneyin.",
                        "Uranüs-Chiron-120": "Öneri: Yenilik ve şifa enerjiniz uyum içinde çalışırken birlikte derin bir iyileşme pratiği yapın. Yaralarınızı kabul ederek güçlü bir şifacı olun. Destekleyici bir ortam yaratın.",
                        "Uranüs-Chiron-180": "Öneri: Özgürlük ve acı arasındaki dengeyi bulmak için bireysel çalışmalara katılın. Birbirinizin yaralarını anlayarak şefkat gösterin. Güçlü ve kırılgan yanlarınızı birlikte kucaklayın.",
                        "Neptün-Neptün-0": "Öneri: Sezgi ve maneviyat enerjinizi birleştirmek için birlikte derin bir meditasyon pratiğine başlayın. Birbirinize ilham vererek yaratıcılığınızı besleyin. Hayallerinizi paylaşarak ortak bir vizyon oluşturun.",
                        "Neptün-Neptün-60": "Öneri: Sezgilerinizi birleştirerek yaratıcı projeler geliştirin. Birlikte sanatsal aktivitelere katılın. Manevi pratiğinizi birlikte derinleştirin.",
                        "Neptün-Neptün-90": "Öneri: Hayalperestlik ve gerçekçilik arasındaki baskisi çözmek için net sınırlar koyun. Birbirinize karşı şeffaf olun. Hayallerinizi somut adımlara dönüştürmek için plan yapın.",
                        "Neptün-Neptün-120": "Öneri: Sezgi ve maneviyat enerjiniz uyum içinde çalışırken birlikte derin bir ruhsal yolculuğa çıkın. Birbirinize ilham vererek yaratıcılığınızı besleyin. Hayallerinizi paylaşarak ortak bir vizyon oluşturun.",
                        "Neptün-Neptün-180": "Öneri: Farklı manevi yaklaşımlarınızı dengelemek için açık iletişim kurun. Birbirinizin sezgisel dilini anlayarak ortak bir yol bulun. Hayalperestlik ve gerçekçilik arasındaki dengeyi test edin.",
                        "Neptün-Plüton-0": "Öneri: Sezgi ve dönüşüm enerjinizi birleştirmek için derin bir ruhsal çalışma başlatın. Birlikte bilinç genişletme aktivitelerine katılın. Manevi güçlerinizi birleştirerek derin bir etki yaratın.",
                        "Neptün-Plüton-60": "Öneri: Sezgilerinizi güçlendirerek derin değişimler yaratın. Birlikte manevi projeleri tamamlama konusunda birbirinize destek olun. Değişimi sezgisel olarak yönlendirin.",
                        "Neptün-Plüton-90": "Öneri: Sezgi ve güç arasındaki baskisi çözmek için bireysel güç kaynaklarınızı keşfedin. Birbirinize karşı manipüle etmeden açık iletişim kurun. Manevi güç dengesizliklerini kabul ederek ortak bir çözüm bulun.",
                        "Neptün-Plüton-120": "Öneri: Sezgi ve dönüşüm enerjiniz uyum içinde çalışırken birlikte güçlü projeler geliştirin. Değişimi sezgisel olarak yönlendirin. Birbirinize ilham vererek ruhsal gelişiminizi derinleştirin.",
                        "Neptün-Plüton-180": "Öneri: Sezgi ve güç arasındaki dengeyi bulmak için bireysel gölgelerinizi kabul edin. Birbirinizin manevi güçlerini tanıyarak saygı gösterin. Manevi güç mücadelelerini yapıcı diyaloğa dönüştürmek için çaba gösterin.",
                        "Neptün-KAD-0": "Öneri: Sezgi ve kadersel yolunuz birleşirken manevi rehberliğinizi netleştirin. Birlikte meditasyon veya dua pratiği yapın. Eski kalıpları bırakarak yeni bir ruhsal yolculuk başlatın.",
                        "Neptün-KAD-60": "Öneri: Sezgilerinizi kadersel yönünüzle harmanlayarak anlamlı bir yolculuk başlatın. Birlikte manevi projeler geliştirin. Değişimi sezgisel olarak destekleyerek ruhsal gelişiminizi hızlandırın.",
                        "Neptün-KAD-90": "Öneri: Sezgi ve kadersel yönünüz arasındaki baskisi çözmek için cesaret toplayın. Birlikte zorlu deneyimlerden dersler çıkarın. Eski kalıpları kırmak için bireysel çalışma yapın.",
                        "Neptün-KAD-120": "Öneri: Sezgi ve kadersel yönünüz uyum içinde ilerlerken birlikte projeler geliştirin. Değişimi sezgisel olarak destekleyerek ruhsal hedeflerinize ulaşın. Destekleyici bir ortam yaratın.",
                        "Neptün-KAD-180": "Öneri: Sezgi ve kadersel yolunuz arasındaki dengeyi bulun. Birbirinizin farklı yollarını anlayarak destek olun. Korkularınızı aşarak sezgisel rehberliğinize güvenin.",
                        "Neptün-Chiron-0": "Öneri: Sezgi ve şifa enerjiniz birleşirken manevi iyileşme süreçleri başlatın. Birlikte meditasyon veya enerji iyileşmesi pratiği yapın. Eski yaraları kabul ederek yeni bir başlangıç yapın.",
                        "Neptün-Chiron-60": "Öneri: Sezgilerinizi şifa enerjisiyle harmanlayarak yaratıcı projeler geliştirin. Birlikte şifa pratiği yapın. Yaralarınızı kabul ederek başkalarına da yardım edin.",
                        "Neptün-Chiron-90": "Öneri: Sezgi ve acı arasındaki baskisi çözmek için şefkatli iletişim kurun. Birbirinize karşı sabırlı olun. Eski yaraları iyileştirmek için manevi yöntemler deneyin.",
                        "Neptün-Chiron-120": "Öneri: Sezgi ve şifa enerjiniz uyum içinde çalışırken birlikte derin bir iyileşme pratiği yapın. Yaralarınızı kabul ederek güçlü bir şifacı olun. Destekleyici bir ortam yaratın.",
                        "Neptün-Chiron-180": "Öneri: Sezgi ve acı arasındaki dengeyi bulmak için bireysel çalışmalara katılın. Birbirinizin yaralarını anlayarak şefkat gösterin. Güçlü ve kırılgan yanlarınızı birlikte kucaklayın.",
                        "Plüton-Plüton-0": "Öneri: Dönüşüm ve güç enerjinizi birleştirmek için güçlü bir ortaklık kurun. Birlikte derin bir değişim pratiği yapın. Eski güç yapılarını kırmak için cesur adımlar atın.",
                        "Plüton-Plüton-60": "Öneri: Dönüşüm enerjinizi birleştirerek derin değişimler yaratın. Birlikte güçlü projeleri tamamlama konusunda birbirinize destek olun. Değişimi destekleyerek derin bir etki yaratın.",
                        "Plüton-Plüton-90": "Öneri: Güç ve kontrol arasındaki baskisi çözmek için bireysel güç kaynaklarınızı keşfedin. Birbirinize karşı manipüle etmeden açık iletişim kurun. Güç dengesizliklerini kabul ederek ortak bir çözüm bulun.",
                        "Plüton-Plüton-120": "Öneri: Dönüşüm ve güç enerjiniz uyum içinde çalışırken birlikte güçlü projeler geliştirin. Değişimi destekleyerek derin bir etki yaratın. Birbirinize ilham vererek ruhsal gelişiminizi derinleştirin.",
                        "Plüton-Plüton-180": "Öneri: Farklı güç yaklaşımlarınızı dengelemek için açık iletişim kurun. Birbirinizin güç kaynaklarını tanıyarak saygı gösterin. Güç mücadelelerini yapıcı diyaloğa dönüştürmek için çaba gösterin.",
                        "Plüton-KAD-0": "Öneri: Dönüşüm ve kadersel yolunuz birleşirken derin bir değişim başlatın. Birlikte gelecek planları yaparak güçlü hedefler belirleyin. Eski kalıpları bırakarak yeni bir yaşam tarzı oluşturun.",
                        "Plüton-KAD-60": "Öneri: Dönüşüm enerjinizi kadersel yönünüzle harmanlayarak anlamlı bir yolculuk başlatın. Birlikte güçlü projeler geliştirin. Değişimi destekleyerek ruhsal gelişiminizi hızlandırın.",
                        "Plüton-KAD-90": "Öneri: Dönüşüm ve kadersel yönünüz arasındaki baskisi çözmek için cesaret toplayın. Birlikte zorlu deneyimlerden dersler çıkarın. Eski kalıpları kırmak için bireysel çalışma yapın.",
                        "Plüton-KAD-120": "Öneri: Dönüşüm ve kadersel yönünüz uyum içinde ilerlerken birlikte projeler geliştirin. Değişimi destekleyerek ruhsal hedeflerinize ulaşın. Destekleyici bir ortam yaratın.",
                        "Plüton-KAD-180": "Öneri: Dönüşüm ve kadersel yolunuz arasındaki dengeyi bulun. Birbirinizin farklı yollarını anlayarak destek olun. Korkularınızı aşarak cesur adımlar atın.",
                        "Plüton-Chiron-0": "Öneri: Dönüşüm ve şifa enerjiniz birleşirken derin iyileşme süreçleri başlatın. Birlikte derin terapi seansları yapın. Eski yaraları kabul ederek yeni bir başlangıç yapın.",
                        "Plüton-Chiron-60": "Öneri: Dönüşüm enerjinizi şifa enerjisiyle harmanlayarak yaratıcı projeler geliştirin. Birlikte şifa pratiği yapın. Yaralarınızı kabul ederek başkalarına da yardım edin.",
                        "Plüton-Chiron-90": "Öneri: Dönüşüm ve acı arasındaki baskisi çözmek için şefkatli iletişim kurun. Birbirinize karşı sabırlı olun. Eski yaraları iyileştirmek için derin çalışmalar yapın.",
                        "Plüton-Chiron-120": "Öneri: Dönüşüm ve şifa enerjiniz uyum içinde çalışırken birlikte derin bir iyileşme pratiği yapın. Yaralarınızı kabul ederek güçlü bir şifacı olun. Destekleyici bir ortam yaratın.",
                        "Plüton-Chiron-180": "Öneri: Dönüşüm ve acı arasındaki dengeyi bulmak için bireysel çalışmalara katılın. Birbirinizin yaralarını anlayarak şefkat gösterin. Güçlü ve kırılgan yanlarınızı birlikte kucaklayın.",
                        "KAD-Chiron-0": "Öneri: Kadersel yolunuz ve şifa enerjiniz birleşirken yaralarınızı şifaya dönüştürmek için çalışın. Birlikte derin bir şifa pratiği başlatın. Eski yaraları kabul ederek yeni bir başlangıç yapın.",
                        "KAD-Chiron-60": "Öneri: Kadersel yönünüzü şifa enerjisiyle harmanlayarak yaratıcı projeler geliştirin. Birlikte şifa pratiği yapın. Yaralarınızı kabul ederek başkalarına da yardım edin.",
                        "KAD-Chiron-90": "Öneri: Kadersel yolunuz ve acı arasındaki baskisi çözmek için şefkatli iletişim kurun. Birbirinize karşı sabırlı olun. Eski yaraları iyileştirmek için cesur adımlar atın.",
                        "KAD-Chiron-120": "Öneri: Kadersel yönünüz ve şifa enerjiniz uyum içinde çalışırken birlikte derin bir iyileşme pratiği yapın. Yaralarınızı kabul ederek güçlü bir şifacı olun. Destekleyici bir ortam yaratın.",
                        "KAD-Chiron-180": "Öneri: Kadersel yolunuz ve acı arasındaki dengeyi bulmak için bireysel çalışmalara katılın. Birbirinizin yaralarını anlayarak şefkat gösterin. Güçlü ve kırılgan yanlarınızı birlikte kucaklayın.",
                        }

                        r_key = f"{g1}-{g2}-{aci_deg}"
                        r_alt_key = f"{g2}-{g1}-{aci_deg}"
                        
                        if self.mod == "ebeveyn_cocuk":
                            fbst_receteler_ebeveyn = {
                                "Güneş-Güneş-0": "Pedagojik Protokol: Ebeveyn ve çocuk arasındaki benzer enerji titresimlarını güçlendirmek için birlikte sabah ritüelleri oluşturun. Her sabah 5 dakika boyunca birlikte niyet belirleyin ve günün hedefini konuşun. Bu ritüel, ortak vizyonunuzu ve birliktelik duygusunu güçlendirecektir.",
                                "Güneş-Güneş-60": "Pedagojik Protokol: Benzer ama farklı yeteneklerdeki bu uyumlu enerjiyi korumak için haftada bir 'Güçlü Yan Paylaşımı' oturumu düzenleyin. Birbirinizin güçlü yönlerini yüksek sesle takdir edin ve birlikte yeni beceriler keşfedin.",
                                "Güneş-Güneş-90": "Pedagojik Protokol: Ego çatışmalarını çözmek için şu adımları uygulayın: 1) Tartışma anında 'Dur ve Dinle' tekniğini kullanın. 2) Her iki taraf da kendi açısını yüksek sesle ifade etsin. 3) Ortak bir çözüm yolu birlikte belirlensin.",
                                "Güneş-Güneş-120": "Pedagojik Protokol: Doğal uyumu korumak için birlikte yeni deneyimler planlayın. Ayda bir yeni bir aktivite deneyin ve bu deneyim sırasında birbirinizin rehberliğine güvenme pratiği yapın.",
                                "Güneş-Güneş-180": "Pedagojik Protokol: Zıtlıkları dengelemek için ayna pratiği yapın: karşılıklı oturun ve birbirinizin güçlü ve zayıf yönlerini yüksek sesle kabul edin. Ardından bu zıtlıkların sizi nasıl tamamladığını tartışın.",
                                "Güneş-Ay-0": "Pedagojik Protokol: Ebeveynin bilinçli enerjisi ile çocuğun duygusal derinliğinin uyumu için birlikte ay döngüsü takibi yapın. Her yeni ayda ortak niyetler belirleyin ve duygusal ihtiyaçlarınızı paylaşın.",
                                "Güneş-Ay-60": "Pedagojik Protokol: Işık ve duygusallığın uyumunu korumak için akşam rutinleri oluşturun. Her akşam birlikte çay içerek günün duygusal iniş çıkışlarını paylaşın ve birbirinizi dinleyin.",
                                "Güneş-Ay-90": "Pedagojik Protokol: Ego ile duygusal hassasiyet arasındaki baskisi çözmek için: 1) Duygusal tetiklenme anında 'Durdur ve Hisset' tekniğini kullanın. 2) Birbirinizin duygusal dilini öğrenin. 3) Ortak bir şifa ritüeli oluşturun.",
                                "Güneş-Ay-120": "Pedagojik Protokol: Doğal besleyici uyumu korumak için birlikte yemek pişirme ritüeli oluşturun. Pişirirken birbirinizin duygusal ihtiyaçlarını konuşun.",
                                "Güneş-Ay-180": "Pedagojik Protokol: Dışa dönüklük ile içe dönüklük arasındaki dengeyi bulmak için 'Değişim Günü' pratiği yapın: bir gün aktif, ertesi gün sakin aktiviteler yapın.",
                                "Güneş-Merkür-0": "Pedagojik Protokol: Güç ve iletişimin kavuştuğu bu noktada, birlikte bilinçli iletişim pratiği yapın. Her sabah günün niyetini yüksek sesle paylaşın.",
                                "Güneş-Merkür-60": "Pedagojik Protokol: Işık ve zeka uyumunu korumak için haftada bir 'Bilgi Paylaşımı' oturumu düzenleyin. Birbirinize bu hafta öğrendiğiniz yeni bir şeyi anlatın.",
                                "Güneş-Merkür-90": "Pedagojik Protokol: İletişim baskisini çözmek için: 1) 'Dinleme Molası' verin: her konuştuğunuzda 3 saniye durup sözünü bitirmesini bekleyin. 2) Düşüncelerinizi yazarak paylaşın. 3) Birlikte sesli kitap okuyun.",
                                "Güneş-Merkür-120": "Pedagojik Protokol: Doğal iletişim akışını korumak için birlikte okuma saati düzenleyin. Aynı kitabı okuyup ardından düşüncelerinizi paylaşın.",
                                "Güneş-Venüs-0": "Pedagojik Protokol: Güç ve sevginin buluştuğu bu noktada, birlikte sevgi ritüelleri oluşturun. Her sabah birbirinize sevgi dolu bir mesaj yazın.",
                                "Güneş-Venüs-60": "Pedagojik Protokol: Işık ve zarafet uyumunu korumak için haftada bir 'Güzellik Günü' düzenleyin. Birlikte doğa yürüyüşü yapın veya sanatsal bir aktivite planlayın.",
                                "Güneş-Venüs-90": "Pedagojik Protokol: Enerji ile sevgi arasındaki baskisi çözmek için: 1) Çatışma anında 'Sevgi Nefesi' tekniğini kullanın. 2) Birbirinizin sevgi dilini öğrenin. 3) Ortak bir şifa sanatı pratiği yapın.",
                                "Güneş-Venüs-120": "Pedagojik Protokol: Doğal sevgi akışını korumak için birlikte romantik ritüeller oluşturun. Ayda bir yeni deneyim planlayın ve minnettarlığınızı ifade edin.",
                                "Güneş-Mars-0": "Pedagojik Protokol: Güç ve eylemin kavuştuğu bu noktada, birlikte fiziksel aktivite ritüelleri oluşturun. Her hafta birlikte yeni bir spor deneyin.",
                                "Güneş-Mars-60": "Pedagojik Protokol: Işık ve cesaret uyumunu korumak için haftada bir 'Maceracı Gün' planlayın. Birlikte yeni bir yer keşfedin.",
                                "Güneş-Mars-90": "Pedagojik Protokol: Ego ile saldırganlık arasındaki baskisi çözmek için: 1) Öfke anında derin nefes egzersizi yapın. 2) Fiziksel egzersiz birlikte yaparak enerjiyi yapıcıya dönüştürün. 3) Ortak bir hedef belirleyin.",
                                "Güneş-Mars-120": "Pedagojik Protokol: Doğal eylem akışını korumak için birlikte aktif meditasyon pratiği yapın. Yoga veya dans meditasyonu ile enerjinizi dengeleyin.",
                                "Güneş-Jüpiter-0": "Pedagojik Protokol: Güç ve genişlemenin kavuştuğu bu noktada, birlikte büyüme ritüelleri oluşturun. Her sabah şükran journal'ı tutun.",
                                "Güneş-Jüpiter-60": "Pedagojik Protokol: Işık ve bolluk uyumunu korumak için haftada bir 'Bereket Paylaşımı' oturumu düzenleyin.",
                                "Güneş-Jüpiter-90": "Pedagojik Protokol: Bireysel güç ile aşırı genişleme arasındaki baskisi çözmek için: 1) Gerçekçi hedefler belirleyin. 2) Fazla iyimserlik anında değerlendirme yapın. 3) Sosyal sorumluluk projelerine katılın.",
                                "Güneş-Jüpiter-120": "Pedagojik Protokol: Doğal bolluk akışını korumak için birlikte bolluk meditasyonu yapın.",
                                "Güneş-Satürn-0": "Pedagojik Protokol: Güç ve disiplinin kavuştuğu bu noktada, birlikte yapı ve sorumluluk ritüelleri oluşturun. Haftalık planlama oturumu düzenleyin.",
                                "Güneş-Satürn-60": "Pedagojik Protokol: Işık ve disiplin uyumunu korumak için haftada bir 'Yapı ve Planlama' oturumu yapın.",
                                "Güneş-Satürn-90": "Pedagojik Protokol: Bireysel güç ile sınırlayıcı enerji arasındaki baskisi çözmek için: 1) Mindfulness pratiği yapın. 2) Sorumlulukları adil paylaşın. 3) Uzun vadeli proje oluşturun.",
                                "Güneş-Satürn-120": "Pedagojik Protokol: Doğal disiplin akışını korumak için birlikte uzun vadeli bir plan oluşturun.",
                                "Güneş-Uranüs-0": "Pedagojik Protokol: Güç ve devrimin kavuştuğu bu noktada, birlikte yenilik ritüelleri oluşturun. Her ay yeni bir şey deneyin.",
                                "Güneş-Uranüs-60": "Pedagojik Protokol: Işık ve yenilikçilik uyumunu korumak için haftada bir 'Yenilikçi Buluşma' düzenleyin.",
                                "Güneş-Uranüs-90": "Pedagojik Protokol: Bireysel güç ile ani değişim arasındaki baskisi çözmek için: 1) Ani kararlar almadan önce 24 saat bekleyin. 2) Bağımsızlığa saygı gösterin. 3) Ortak bir vizyon oluşturun.",
                                "Güneş-Neptün-0": "Pedagojik Protokol: Güç ve maneviyatın kavuştuğu bu noktada, birlikte manevi ritüeller oluşturun. Meditasyon veya dua pratiği yapın.",
                                "Güneş-Neptün-60": "Pedagojik Protokol: Işık ve maneviyat uyumunu korumak için haftada bir 'Manevi Paylaşım' oturumu düzenleyin.",
                                "Güneş-Neptün-90": "Pedagojik Protokol: Net güç ile bulanık enerji arasındaki baskisi çözmek için: 1) Rüya günlüğü tutun. 2) Manevi pratiğinizi somutlaştırın. 3) Gönüllülük yapın.",
                                "Güneş-Plüton-0": "Pedagojik Protokol: Güç ve transformasyonun kavuştuğu bu noktada, birlikte derin dönüşüm ritüelleri oluşturun.",
                                "Güneş-Plüton-60": "Pedagojik Protokol: Işık ve derin dönüşüm uyumunu korumak için haftada bir 'Dönüşüm Paylaşımı' oturumu düzenleyin.",
                                "Güneş-Plüton-90": "Pedagojik Protokol: Ego ile güç mücadelesi arasındaki baskisi çözmek için: 1) Güç mücadelelerini fark edin. 2) Gölgeleri kabul edin. 3) Ortak dönüşüm pratiği yapın.",
                                "Güneş-KAD-0": "Pedagojik Protokol: Güç ve kadersel misyonun kavuştuğu bu noktada, birlikte kadersel niyetler belirleyin.",
                                "Güneş-KAD-60": "Pedagojik Protokol: Işık ve kadersel akış uyumunu korumak için haftada bir 'Kader Paylaşımı' oturumu düzenleyin.",
                                "Güneş-KAD-90": "Pedagojik Protokol: Bireysel güç ile kadersel zorluklar arasındaki baskisi çözmek için engelleri fırsat olarak yeniden çerçeveleyin.",
                                "Güneş-Chiron-0": "Pedagojik Protokol: Güç ve şifacı yaranın kavuştuğu bu noktada, birlikte derin şifa ritüelleri oluşturun. Birlikte şifa meditasyonu yapın.",
                                "Güneş-Chiron-60": "Pedagojik Protokol: Işık ve şifa enerjisi uyumunu korumak için haftada bir 'Şifa Paylaşımı' oturumu düzenleyin.",
                                "Güneş-Chiron-90": "Pedagojik Protokol: Ego ile kırılganlık arasındaki baskisi çözmek için: 1) Kırılganlık anında alan tanıyın. 2) Profesyonel destek alın. 3) Şifa projeleri başlatın.",
                                "Güneş-Chiron-120": "Pedagojik Protokol: Doğal şifa akışını korumak için birlikte doğada yürüyüş yapın ve şifa enerjisini hissedin.",
                                "Güneş-Chiron-180": "Pedagojik Protokol: Bireysel şifa ile evrensel şifa arasındaki dengeyi bulmak için her biriniz kendi şifa yolunuzu takip edin, ardından paylaşın.",
                                "Ay-Ay-0": "Pedagojik Protokol: Benzer duygusal titresimlar için birlikte ay döngüsü takibi yapın. Yeni ay ve dolunay ritüelleri oluşturun.",
                                "Ay-Ay-60": "Pedagojik Protokol: Duygusal uyumu korumak için haftada bir 'Duygu Paylaşımı' oturumu düzenleyin.",
                                "Ay-Ay-90": "Pedagojik Protokol: Duygusal hassasiyet arasındaki baskisi çözmek için: 1) Alan tanıyın. 2) İhtiyaçlarınızı açıkça ifade edin. 3) Duygusal şifa meditasyonu yapın.",
                                "Ay-Ay-120": "Pedagojik Protokol: Doğal duygusal akışı korumak için birlikte doğa yürüyüşü yapın ve müzik dinleyin.",
                                "Ay-Ay-180": "Pedagojik Protokol: Duygusal zıtlıkları dengelemek için ayna meditasyonu yapın.",
                                "Ay-Venüs-0": "Pedagojik Protokol: Duygusal derinlik ve sevginin kavuştuğu bu noktada, birlikte sevgi ve şefkat ritüelleri oluşturun.",
                                "Ay-Venüs-60": "Pedagojik Protokol: Yumuşaklık ve zarafet uyumunu korumak için haftada bir 'Güzellik ve Sevgi' oturumu düzenleyin.",
                                "Ay-Venüs-90": "Pedagojik Protokol: Duygusal hassasiyet ile barışçıl doğa arasındaki baskisi çözmek için 'Sevgi Nefesi' tekniğini kullanın.",
                                "Ay-Mars-0": "Pedagojik Protokol: Duygusal derinlik ve eylemin kavuştuğu bu noktada, birlikte fiziksel aktivite yaparak duygusal enerjinizi serbest bırakın.",
                                "Ay-Mars-60": "Pedagojik Protokol: Yumuşaklık ve cesaret uyumunu korumak için haftada bir 'Aktif Duygusal' etkinliği planlayın.",
                                "Ay-Mars-90": "Pedagojik Protokol: Duygusal hassasiyet ile saldırganlık arasındaki baskisi çözmek için 'Sakin Nefes' tekniğini kullanın.",
                                "Ay-Satürn-0": "Pedagojik Protokol: Duygusal derinlik ve disiplinin kavuştuğu bu noktada, birlikte duygusal yapı ritüelleri oluşturun.",
                                "Ay-Satürn-60": "Pedagojik Protokol: Yumuşaklık ve disiplin uyumunu korumak için haftada bir 'Duygusal Yapı' oturumu yapın.",
                                "Ay-Satürn-90": "Pedagojik Protokol: Duygusal dalgalanmalar ile sınırlayıcı enerji arasındaki baskisi çözmek için Mindfulness pratiği yapın.",
                                "Ay-Plüton-0": "Pedagojik Protokol: Duygusal derinlik ve transformasyonun kavuştuğu bu noktada, birlikte derin duygusal dönüşüm ritüelleri oluşturun.",
                                "Ay-Plüton-60": "Pedagojik Protokol: Yumuşaklık ve derin dönüşüm uyumunu korumak için haftada bir 'Duygusal Dönüşüm Paylaşımı' düzenleyin.",
                                "Ay-Plüton-90": "Pedagojik Protokol: Duygusal hassasiyet ile güç mücadelesi arasındaki baskisi çözmek için gölgeleri kabul edin.",
                                "Ay-Chiron-0": "Pedagojik Protokol: Duygusal derinlik ve şifacı yaranın kavuştuğu bu noktada, birlikte duygusal şifa ritüelleri oluşturun.",
                                "Ay-Chiron-60": "Pedagojik Protokol: Yumuşaklık ve şifa enerjisi uyumunu korumak için haftada bir 'Duygusal Şifa Paylaşımı' düzenleyin.",
                                "Ay-Chiron-90": "Pedagojik Protokol: Duygusal hassasiyet ile kırılganlık arasındaki baskisi çözmek için alan tanıyın ve destek olun.",
                                "Merkür-Merkür-0": "Pedagojik Protokol: Benzer zihinsel titresimlar için birlikte iletişim ritüelleri oluşturun. Her sabah journal'a yazın.",
                                "Merkür-Merkür-60": "Pedagojik Protokol: Zihinsel uyumu korumak için haftada bir 'Bilgi Paylaşımı' oturumu düzenleyin.",
                                "Merkür-Merkür-90": "Pedagojik Protokol: İletişim tarzlarındaki baskisi çözmek için 'Dinleme Molası' verin.",
                                "Merkür-Venüs-0": "Pedagojik Protokol: Zeka ve sevgi dilinin kavuştuğu bu noktada, birlikte sevgi dolu iletişim ritüelleri oluşturun.",
                                "Merkür-Venüs-60": "Pedagojik Protokol: Zeka ve zarafet uyumunu korumak için haftada bir 'Güzel İletişim' oturumu düzenleyin.",
                                "Merkür-Venüs-90": "Pedagojik Protokol: Rasyonellik ile duygusallık arasındaki baskisi çözmek için hem mantıksal hem duygusal perspektifleri birleştirin.",
                                "Merkür-Mars-0": "Pedagojik Protokol: Zeka ve eylemin kavuştuğu bu noktada, birlikte tartışmalı ve aktif iletişim ritüelleri oluşturun.",
                                "Merkür-Mars-60": "Pedagojik Protokol: Zeka ve cesaret uyumunu korumak için haftada bir 'Aktif Zihin' etkinliği planlayın.",
                                "Merkür-Mars-90": "Pedagojik Protokol: İletişim hızı ile saldırganlık arasındaki baskisi çözmek için 'Durdur ve Düşün' tekniğini kullanın.",
                                "Merkür-Satürn-0": "Pedagojik Protokol: Zeka ve disiplinin kavuştuğu bu noktada, birlikte yapı ve öğrenme ritüelleri oluşturun.",
                                "Merkür-Satürn-60": "Pedagojik Protokol: Zeka ve disiplin uyumunu korumak için haftada bir 'Zihinsel Yapı' oturumu yapın.",
                                "Merkür-Satürn-90": "Pedagojik Protokol: Hız ile sınırlayıcı enerji arasındaki baskisi çözmek için Mindfulness pratiği yapın.",
                                "Venüs-Venüs-0": "Pedagojik Protokol: Benzer sevgi dilleri için birlikte test yapın ve minnettarlık günlüğü tutun.",
                                "Venüs-Venüs-60": "Pedagojik Protokol: Uyumlu enerjinizi sanatsal projelere yönlendirin. Birlikte resim veya müzik aktivitesi planlayın.",
                                "Venüs-Venüs-90": "Pedagojik Protokol: Değer çatışmalarını dialogla aşın. Para ve sevgi hakkındaki inançlarınızı birlikte yazın.",
                                "Venüs-Mars-0": "Pedagojik Protokol: Tutku ve şefkati birleştirin. Fiziksel yakınlığı duygusal bağla harmanlayan ritüeller geliştirin.",
                                "Venüs-Mars-60": "Pedagojik Protokol: Yaratıcı enerjinizi birlikte kanalize edin. Ortak bir sanat projesi başlatın.",
                                "Venüs-Mars-90": "Pedagojik Protokol: Tutkuyu fiziksel aktivitelere yönlendirin. Spor veya dans ile baskisi boşaltın.",
                                "Venüs-Jüpiter-0": "Pedagojik Protokol: Bolluk ve sevgiyi birlikte genişletin. Birlikte hayal kurun ve büyük planlar yapın.",
                                "Venüs-Jüpiter-60": "Pedagojik Protokol: Sevginizi felsefi bir boyutla derinleştirin. Birlikte kitap okuyun ve tartışın.",
                                "Venüs-Satürn-0": "Pedagojik Protokol: Sevgiye yapı ve sorumluluk katın. Net sınırlar belirleyin.",
                                "Venüs-Satürn-60": "Pedagojik Protokol: Sevgi ve disiplini dengeleyin. Düzenli ilişki bakımı ritüelleri oluşturun.",
                                "Mars-Mars-0": "Pedagojik Protokol: Benzer eylem enerjileri için birlikte fiziksel aktivite planları yapın.",
                                "Mars-Mars-60": "Pedagojik Protokol: Enerji uyumunuzu korumak için birlikte outdoor aktiviteler planlayın.",
                                "Mars-Mars-90": "Pedagojik Protokol: Enerji çatışmalarını yapıcıya dönüştürmek için rekabetçi oyunlar oynayın.",
                                "Jüpiter-Jüpiter-0": "Pedagojik Protokol: Benzer büyüme enerjileri için birlikte öğrenme planları yapın.",
                                "Jüpiter-Satürn-0": "Pedagojik Protokol: Genişleme ve disiplin dengesini bulmak için uzun vadeli hedefler belirleyin.",
                                "Satürn-Satürn-0": "Pedagojik Protokol: Benzer yapı ve disiplin enerjileri için birlikte kurallar oluşturun.",
                                "Plüton-Plüton-0": "Pedagojik Protokol: Benzer dönüşüm enerjileri için birlikte derin çalışmalar yapın.",
                                "KAD-KAD-0": "Pedagojik Protokol: Benzer kadersel yollar için birlikte misyonunuzu keşfedin.",
                                "Chiron-Chiron-0": "Pedagojik Protokol: Benzer şifa enerjileri için birlikte şifa pratiği yapın.",
                            }
                            if r_key in fbst_receteler_ebeveyn:
                                receteler.append(f"<b>{g1}-{g2} {aci_info['isim']} Dersi:</b> {fbst_receteler_ebeveyn[r_key]}")
                            elif r_alt_key in fbst_receteler_ebeveyn:
                                receteler.append(f"<b>{g2}-{g1} {aci_info['isim']} Dersi:</b> {fbst_receteler_ebeveyn[r_alt_key]}")
                            elif aci_deg in [90, 180] and len(receteler) < 12:
                                receteler.append(f"<b>{g1}-{g2} {aci_info['isim']} Dersi:</b> Ortak bir aktivite belirleyin ve bu gerilimli enerjiyi yapıcı bir alana kanalize edin.")
                        else:
                            if r_key in fbst_receteler:
                                receteler.append(f"<b>{g1}-{g2} {aci_info['isim']} Şifası:</b> {fbst_receteler[r_key]}")
                            elif r_alt_key in fbst_receteler:
                                receteler.append(f"<b>{g2}-{g1} {aci_info['isim']} Şifası:</b> {fbst_receteler[r_alt_key]}")
                            elif aci_deg in [90, 180] and len(receteler) < 12:
                                receteler.append(f"<b>{g1}-{g2} {aci_info['isim']} Şifası:</b> Ortak bir hobi edinin ve bu gerilimli enerjiyi yapıcı bir alana kanalize edin.")

        if not sinastri_verileri:
            sinastri_verileri = ["Majör bir sinastri etkileşimi saptanmadı."]

        html_cikti = """<div style="background-color: #FBF7F4; padding: 15px; border-radius: 8px; border-left: 5px solid #B8A9C9; margin-bottom: 20px;">"""
        
        for madde in set(sinastri_verileri):
            html_cikti += f"<p style='font-size:13px; line-height:2.0; margin-bottom:14px; padding: 6px 0; border-bottom: 1px solid #E8E0D8;'>✨ {madde}</p>"
            
        html_cikti += """</div><div style="background-color: #FFF0ED; padding: 15px; border-radius: 8px; border-left: 5px solid #D4878F;">"""
        
        if self.mod == "ebeveyn_cocuk":
            html_cikti += """<h4 style="color: #C47A82; margin-top: 0;">💊 KADERSEL DERSLER VE ŞİFA ÖNERİLERİ</h4>"""
        else:
            html_cikti += """<h4 style="color: #C47A82; margin-top: 0;">💊 KADERSEL ŞİFA REÇETELERİ</h4>"""
        
        # Reçeteleri Bas
        if receteler:
            import re
            for rc in set(receteler):
                recete_html = re.sub(r'(\d+)\)\s*', r'<br/><b>\1)</b> ', rc)
                recete_html = re.sub(r'^<br/>', '', recete_html)
                html_cikti += f"<p style='font-size:13px; line-height:2.0; margin-bottom:14px; padding: 8px 0; border-bottom: 1px solid #E8DDD5;'>🌿 {recete_html}</p>"
        else:
            html_cikti += "<p style='font-size:13px;'>Mevcut kadersel temaslarınız akut bir şifa reçetesi gerektirmemektedir. Doğal akışınızda kalın.</p>"
            
        html_cikti += "</div>"
        
        return html_cikti

    def gelisim_donemleri_hesapla(self):
        """
        Çocuğun yaşına göre gelişim dönemlerini hesaplar + natal burç/ev bilgisi ekler.
        FBST_GELISIM_DONEMleri_EBEVEYN dict'inden uygun dönem metinlerini döndürür.
        """
        if not FBST_GELISIM_DONEMleri_EBEVEYN:
            return []

        if self.mod == "ebeveyn_cocuk":
            cocuk_tarih = self.event_date.date()
        else:
            cocuk_tarih = self.p1
        bugun = datetime.now().date()
        cocuk_ay = (bugun.year - cocuk_tarih.year) * 12 + (bugun.month - cocuk_tarih.month)

        # Çocuğun natal Julian Day'i (UTC dönüşümlü)
        try:
            dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(cocuk_tarih.year, cocuk_tarih.month, cocuk_tarih.day)
            jd_cocuk = swe.julday(cocuk_tarih.year, cocuk_tarih.month, cocuk_tarih.day, dogum_saat_utc)
        except Exception:
            jd_cocuk = None

        # 16 ana gezegen
        gezegenler = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter", "Satürn",
                       "Uranüs", "Neptün", "Plüton", "KAD", "Chiron", "Juno", "Ceres", "Pallas", "Vesta"]

        # Dönem eşikleri (ay cinsinden) ve karşılık gelen key'ler
        esikler = [
            (7, 0), (13, 7), (19, 13), (26, 19), (48, 26),
            (84, 4), (156, 70), (228, 140), (312, 210), (9999, 280)
        ]

        donem_key = 0
        for esik_ay, key in esikler:
            if cocuk_ay < esik_ay:
                donem_key = key
                break

        sonuclar = []
        for gezegen in gezegenler:
            arama_key = (gezegen, donem_key)
            if arama_key in FBST_GELISIM_DONEMleri_EBEVEYN:
                veri = FBST_GELISIM_DONEMleri_EBEVEYN[arama_key]

                # Natal burç ve ev bilgisi
                burc_adi = ""
                ev_no = ""
                if jd_cocuk and gezegen in GEZEGENLER:
                    try:
                        pos = get_planetary_position(jd_cocuk, GEZEGENLER[gezegen])
                        burc_adi = dereceyi_burca_cevir(pos)
                        ev_no = self.ev_konumu_bul(jd_cocuk, GEZEGENLER[gezegen])
                    except Exception:
                        pass

                sonuclar.append({
                    "gezegen": gezegen,
                    "donem": veri.get("donem", ""),
                    "metin": veri.get("metin", ""),
                    "burc": burc_adi,
                    "ev": ev_no
                })

        return sonuclar

    def potansiyel_hesapla(self):
        """
        Çocuğun potansiyel ve yetenek alanlarını COCUĞUN NATAL HARİTASI açılarından hesaplar.
        Sadece çocuğun kendi gezegenleri arasındaki açıları bulur (bağıl/sinastri değil).
        FBST_POTANSIYEL_EBEVEYN dict'inden uygun yorumları döndürür.
        """
        if not FBST_POTANSIYEL_EBEVEYN:
            return []

        try:
            if self.mod == "ebeveyn_cocuk":
                d1 = self.event_date.date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            else:
                d1 = self.p1 if isinstance(self.p1, date) else datetime.strptime(str(self.p1), "%Y-%m-%d").date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            j1 = swe.julday(d1.year, d1.month, d1.day, dogum_saat_utc)
        except Exception:
            return []

        gezegen_id_haritasi = {
            "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS,
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN, "Uranüs": swe.URANUS,
            "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO, "KAD": swe.MEAN_NODE, "Chiron": 15,
            "Ceres": swe.AST_OFFSET + 1, "Pallas": swe.AST_OFFSET + 2,
            "Juno": swe.AST_OFFSET + 3, "Vesta": swe.AST_OFFSET + 4
        }

        aci_tipleri = {0: "0", 60: "60", 90: "90", 120: "120", 180: "180"}

        # ÇOCUĞUN NATAL HARİTASI açılarını bul (sadece j1 kullanılır)
        cocuk_acilari = []
        gezegen_isimleri = list(gezegen_id_haritasi.keys())
        for i, g1 in enumerate(gezegen_isimleri):
            for j, g2 in enumerate(gezegen_isimleri):
                if j <= i:
                    continue
                try:
                    g1_id = gezegen_id_haritasi[g1]
                    g2_id = gezegen_id_haritasi[g2]
                    p1_pos = swe.calc_ut(j1, g1_id, get_safe_flags(g1_id))[0][0]
                    p2_pos = swe.calc_ut(j1, g2_id, get_safe_flags(g2_id))[0][0]
                    fark = abs(p1_pos - p2_pos)
                    if fark > 180:
                        fark = 360 - fark
                    for aci_deger, aci_str in aci_tipleri.items():
                        orb = abs(fark - aci_deger)
                        if orb <= 8:
                            aci_cift = f"{g1}-{g2}"
                            cocuk_acilari.append((aci_cift, aci_str, round(orb, 2)))
                except Exception:
                    continue

        # Potansiyel alanları tara — her alanda birden fazla açı topla
        sonuclar = []
        for (alan, aci_cift), metin in FBST_POTANSIYEL_EBEVEYN.items():
            for bulunan_cift, bulunan_aci, bulunan_orb in cocuk_acilari:
                ters_cift = f"{bulunan_cift.split('-')[1]}-{bulunan_cift.split('-')[0]}"
                if aci_cift == bulunan_cift or ters_cift == aci_cift:
                    sonuclar.append({
                        "alan": alan,
                        "aci": bulunan_cift,
                        "aci_turu": bulunan_aci,
                        "orb": bulunan_orb,
                        "metin": metin
                    })

        return sonuclar

    def asteroid_analizi(self):
        """
        90° kadran sistemi ile asteroit analizi.
        Kavuşum (0°) ve Zıtlık (180°) 90° kadranında aynı noktadır.
        Düğümler (Kuzey/Güney) de referans noktalarına eklenir.
        Kavuşum ağırlığı artırılmıştır.
        """
        try:
            jd = self.jdut
            bwhouse = self.bwhouse

            _, ascmc = swe.houses(jd, self.enlem, self.boylam, bwhouse)
            asc = ascmc[0]
            mc = ascmc[1]

            guenes = self.pb["gezegenler"].get("Güneş", {}).get("boylam", 0)
            ay = self.pb["gezegenler"].get("Ay", {}).get("boylam", 0)

            try:
                node_pos = swe.calc_ut(jd, swe.TRUE_NODE)
                kuzey_dugum = node_pos[0][0]
                guney_dugum = (kuzey_dugum + 180.0) % 360
            except:
                kuzey_dugum = 0
                guney_dugum = 180

            ASTEROITLER = {
                # === URANIAN TRANSNEPTUNIAN NOKTALARI (90° kadran ustası) ===
                40: { "b": 8 },
                41: { "b": 8 },
                42: { "b": 8 },
                43: { "b": 8 },
                44: { "b": 8 },
                45: { "b": 7 },
                46: { "b": 8 },
                47: { "b": 7 },

                # === CENTAURS & MAJOR (swe sabit constant'ları — AST_OFFSET kullanılmaz) ===
                15: { "b": 3 },
                16: { "b": 3 },
                17: {"swe_id": swe.CERES, "ad": "Ceres", "k": ["Yardımseverlik", "Sağlık/Tıp"], "b": 3.0},
                18: { "b": 4 },
                19: {"swe_id": swe.JUNO, "ad": "Juno", "k": ["Hukuk/Politika", "Yardımseverlik"], "b": 3.0},
                20: { "b": 3 },
                55: { "b": 4 },

                # === SAYILI ASTEROİTLER (AST_OFFSET ile) ===
                8: { "b": 2 },
                10: {"swe_id": swe.AST_OFFSET + 10, "ad": "Hygiea", "k": ["Sağlık/Tıp", "Yardımseverlik"], "b": 4.0},
                22: {"swe_id": swe.AST_OFFSET + 22, "ad": "Calliope", "k": ["İletişim", "Sanatsal Yetenek"], "b": 3.5},
                23: { "b": 3 },
                24: {"swe_id": swe.AST_OFFSET + 24, "ad": "Themis", "k": ["Hukuk/Politika", "Yardımseverlik"], "b": 4.0},
                27: {"swe_id": swe.AST_OFFSET + 27, "ad": "Euterpe", "k": ["Sanatsal Yetenek", "İletişim"], "b": 3.0},
                28: { "b": 3 },
                30: { "b": 3 },
                33: {"swe_id": swe.AST_OFFSET + 33, "ad": "Polyhymnia", "k": ["İletişim", "Maneviyat", "Sanatsal Yetenek"], "b": 3.0},
                34: {"swe_id": swe.AST_OFFSET + 34, "ad": "Circe", "k": ["Sanatsal Yetenek", "Maneviyat"], "b": 2.5},
                36: { "b": 3 },
                62: {"swe_id": swe.AST_OFFSET + 62, "ad": "Erato", "k": ["Sanatsal Yetenek", "İletişim"], "b": 3.0},
                80: {"swe_id": swe.AST_OFFSET + 80, "ad": "Sappho", "k": ["Sanatsal Yetenek", "İletişim"], "b": 4.0},
                93: { "b": 4 },
                100: {"swe_id": swe.AST_OFFSET + 100, "ad": "Hekate", "k": ["Maneviyat", "Yardımseverlik", "Sağlık/Tıp"], "b": 3.5},
                114: { "b": 3 },
                151: { "b": 3 },
                238: { "b": 3 },
                269: {"swe_id": swe.AST_OFFSET + 269, "ad": "Justitia", "k": ["Hukuk/Politika", "Yardımseverlik"], "b": 4.5},
                307: { "b": 4 },
                389: { "b": 3 },
                408: { "b": 3 },
                638: { "b": 3 },
                742: { "b": 4 },
                896: { "b": 3 },
                1048: {"swe_id": swe.AST_OFFSET + 1048, "ad": "Aesculapia", "k": ["Sağlık/Tıp", "Yardımseverlik"], "b": 4.5},
                1388: {"swe_id": swe.AST_OFFSET + 1388, "ad": "Aphrodite", "k": ["Sanatsal Yetenek", "Yardımseverlik"], "b": 3.5},
                1566: { "b": 3 },
                1813: { "b": 3 },
                1862: { "b": 4 },
                1981: { "b": 4 },
                2001: { "b": 4 },
                2063: { "b": 3 },
                2212: { "b": 4 },
                2598: { "b": 3 },
                2878: {"swe_id": swe.AST_OFFSET + 2878, "ad": "Panacea", "k": ["Sağlık/Tıp", "Yardımseverlik"], "b": 3.5},
                3361: {"swe_id": swe.AST_OFFSET + 3361, "ad": "Orpheus", "k": ["Sanatsal Yetenek", "Maneviyat", "İletişim"], "b": 3.5},
                3469: {"swe_id": swe.AST_OFFSET + 3469, "ad": "Bulgakov", "k": ["Sanatsal Yetenek", "İletişim"], "b": 3.0},
            }

            ORB = 6.0
            NOKTALAR = {
                "MC": mc, "ASC": asc, "Güneş": guenes, "Ay": ay,
                "KD": kuzey_dugum, "GD": guney_dugum,
            }
            NOKTA_AGIRLIK = {
                "MC": 6.0, "ASC": 0.8, "Güneş": 0.6, "Ay": 0.5,
                "KD": 0.5, "GD": 0.5,
            }

            ACILAR = [
                ("Kavuşum", 0.0, 1.5),
                ("Kare", 90.0, 0.7),
                ("Zıtlık", 180.0, 1.2),
                ("Trine", 120.0, 0.35),
                ("Sextil", 60.0, 0.25),
            ]

            sonuclar = {}
            for ast_key, bilgi in ASTEROITLER.items():
                try:
                    r = swe.calc_ut(jd, bilgi["swe_id"])
                    ast_lon = r[0][0]
                except:
                    continue

                for nokta_adi, nokta_lon in NOKTALAR.items():
                    raw_fark = abs(ast_lon - nokta_lon) % 360
                    if raw_fark > 180:
                        raw_fark = 360 - raw_fark

                    for aci_adi, aci_derece, aci_agirlik in ACILAR:
                        fark = abs(raw_fark - aci_derece)
                        if fark > 180:
                            fark = 360 - fark
                        if fark <= ORB:
                            n_agirlik = NOKTA_AGIRLIK[nokta_adi]
                            orb_factor = 1.0 - (fark / ORB) * 0.5
                            puan = bilgi["b"] * aci_agirlik * n_agirlik * orb_factor

                            for kat in bilgi["k"]:
                                if kat not in sonuclar:
                                    sonuclar[kat] = 0
                                sonuclar[kat] += round(puan, 2)

            return sonuclar
        except Exception:
            return {}

    def meslek_arap_noktasi_hesapla(self):
        """
        Meslek Arap Noktası (Part of Spirit) hesaplar.
        Gündüz: ASC + MC - Moon
        Gece:   ASC + Moon - MC
        Ruh Noktası'nın burcu ve evi meslek yorumunu derinleştirir.
        """
        try:
            if self.mod == "ebeveyn_cocuk":
                d1 = self.event_date.date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            else:
                d1 = self.p1 if isinstance(self.p1, date) else datetime.strptime(str(self.p1), "%Y-%m-%d").date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            j1 = swe.julday(d1.year, d1.month, d1.day, dogum_saat_utc)

            ascmc, _ = swe.houses_ex(j1, self.enlem, self.boylam, b'P')
            asc_derece = ascmc[0] % 360
            mc_derece = ascmc[1] % 360

            ay_pos = get_planetary_position(j1, swe.MOON) % 360
            gunes_pos = get_planetary_position(j1, swe.SUN) % 360

            fark = (gunes_pos - asc_derece) % 360
            Gunduz = fark < 180

            if Gunduz:
                ruh_noktasi = (asc_derece + mc_derece - ay_pos) % 360
            else:
                ruh_noktasi = (asc_derece + ay_pos - mc_derece) % 360

            ruh_burc = dereceyi_burca_cevir(ruh_noktasi)

            ruh_ev = 0
            for idx in range(12):
                h_start = ascmc[idx] % 360
                h_end = ascmc[(idx + 1) % 12] % 360
                if h_start < h_end:
                    if h_start <= ruh_noktasi < h_end:
                        ruh_ev = idx + 1
                        break
                else:
                    if ruh_noktasi >= h_start or ruh_noktasi < h_end:
                        ruh_ev = idx + 1
                        break

            return {
                "ruh_noktasi_derece": round(ruh_noktasi, 2),
                "ruh_burc": ruh_burc,
                "ruh_ev": ruh_ev,
                "gunduz": Gunduz,
                "asc": round(asc_derece, 2),
                "mc": round(mc_derece, 2),
                "ay": round(ay_pos, 2),
            }
        except Exception:
            return None

    def meslek_onerileri(self):
        """
        Hassas meslek yönlendirme puanlaması.
        Puan = (Açı Temel Puanı × Orb Çarpanı) + Çoklu Açı Bonusu + MC/Sabit Yıldız Bonusu

        Açı Temel Puanı: Kavuşum=5, Trigon=4, Sextile=3, Kare=2, Zıtlık=2
        Orb Çarpanı:     0-1°=1.0 | 1-2°=0.95 | 2-3°=0.88 | 3-4°=0.80
                         4-5°=0.70 | 5-6°=0.60 | 6-7°=0.50 | 7-8°=0.40
        Çoklu Bonus:     Her ek açı için +1.5 puan
        MC Bonus:        MC burcu + yöneticisi + sabit yıldızlar
        """
        if not FBST_POTANSIYEL_EBEVEYN or not FBST_MESLEK_EBEVEYN:
            return []

        potansiyeller = self.potansiyel_hesapla()
        if not potansiyeller:
            return []

        # ─── PAYLAŞILAN AÇI KATSAYISI (Shared Aspect Split) ───
        # Bir açı birden fazla kategoriyi besliyorsa, her kategori
        # puanın sadece 1/N'sini alır (N = o açının beslediği kategori sayısı).
        from collections import defaultdict
        aspect_cat_map = defaultdict(set)
        for (kat, aci) in FBST_POTANSIYEL_EBEVEYN:
            aspect_cat_map[aci].add(kat)

        # ─── GEZEGEN EV HESAPLAMA (Açısal ev güçlendirmesi için) ───
        aci_taban_puan = {"0": 5, "120": 4, "90": 3.5, "180": 3.5, "60": 2}

        def gezegen_ev_hesapla():
            """Her gezegenin hangi evde olduğunu hesaplar."""
            try:
                if self.mod == "ebeveyn_cocuk":
                    d1 = self.event_date.date()
                    dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
                else:
                    d1 = self.p1 if isinstance(self.p1, date) else datetime.strptime(str(self.p1), "%Y-%m-%d").date()
                    dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
                j1 = swe.julday(d1.year, d1.month, d1.day, dogum_saat_utc)
                res, _ = swe.houses_ex(j1, self.enlem, self.boylam, b'P')
                evler = {}
                for g_isim, g_id in [("Güneş", swe.SUN), ("Ay", swe.MOON), ("Merkür", swe.MERCURY),
                    ("Venüs", swe.VENUS), ("Mars", swe.MARS), ("Jüpiter", swe.JUPITER),
                    ("Satürn", swe.SATURN), ("Uranüs", swe.URANUS), ("Neptün", swe.NEPTUNE), ("Plüton", swe.PLUTO),
                    ("Chiron", swe.CHIRON), ("Ceres", swe.AST_OFFSET + 1),
                    ("Pallas", swe.AST_OFFSET + 2), ("Juno", swe.AST_OFFSET + 3),
                    ("Vesta", swe.AST_OFFSET + 4), ("Kronos", swe.KRONOS)]:
                    try:
                        pos = swe.calc_ut(j1, g_id, get_safe_flags(g_id))[0][0]
                        for idx in range(12):
                            h_start = res[idx]
                            h_end = res[(idx + 1) % 12]
                            if h_start < h_end:
                                if h_start <= pos < h_end:
                                    evler[g_isim] = idx + 1
                                    break
                            else:
                                if pos >= h_start or pos < h_end:
                                    evler[g_isim] = idx + 1
                                    break
                    except Exception:
                        continue
                return evler
            except Exception:
                return {}

        gezegen_evleri = gezegen_ev_hesapla()

        # Açısal ev çarpanı: Astrolojik kariyer analizine göre
        # 1,10 = kariyer/güç (yüksek), 6 = hizmet/günlük iş (orta), diğerleri düşük
        ACISAL_EVLER = {1: 1.8, 4: 1.3, 7: 1.2, 10: 1.8}
        UYUMLU_EVLER = {2: 1.0, 5: 1.1, 8: 1.0, 11: 1.0, 6: 1.05}
        DEGISIM_EVLER = {3: 0.85, 9: 0.85, 12: 0.8}

        def ev_carpan(gezegen_adi):
            """Gezegenin bulunduğu evin güç çarpanını döndürür."""
            ev = gezegen_evleri.get(gezegen_adi, 0)
            return ACISAL_EVLER.get(ev, UYUMLU_EVLER.get(ev, DEGISIM_EVLER.get(ev, 1.0)))

        def orb_carpan(orb):
            if orb <= 0.5:
                return 1.1   # Tight aspect
            elif orb <= 1:
                return 1.05  # Very tight
            elif orb <= 2:
                return 0.95
            elif orb <= 3:
                return 0.88
            elif orb <= 4:
                return 0.80
            elif orb <= 5:
                return 0.70
            elif orb <= 6:
                return 0.60
            elif orb <= 7:
                return 0.50
            else:
                return 0.40

        # ═══════════════════════════════════════════════════════════════════════
        # POZİSYON-BAZLI KARİYER PUANLAMA SİSTEMİ
        # 303 öğrenci anketi + 50 ünlü pozisyon verisinden türetilen kurallar:
        # Her gezegenin hangi burçta ve hangi evde olduğuna göre kategori puanı
        # ═══════════════════════════════════════════════════════════════════════

        mc_bilgisi = self.mc_analizi()
        yildiz_bilgisi = self.sabit_yildiz_analizi()
        arap_bilgisi = self.meslek_arap_noktasi_hesapla()
        ast_bilgileri = self.asteroid_analizi()

        tum_kategoriler = [
            "Sanatsal Yetenek", "Zihinsel Yetenek", "Liderlik",
            "Yardımseverlik", "Bilgelik", "İletişim", "Maneviyat",
            "Sağlık/Tıp", "Spor", "Zanaatkarlık",
            "Askeriye", "Hukuk/Politika",
            "Stratejik Zeka", "Girişimcilik", "Akademik/Araştırma", "Yenilikçilik",
        ]

        # ═══ KATEGORİ ETİKET SİSTEMİ (Modern meslek eşleştirmesi için) ═══
        # Her kategori birden fazla etiket taşır; FBST_MESLEK_EBEVEYN'de meslek→etiket eşleşmesi yapılır
        KATEGORI_ETIKETLERI = {
            "Sanatsal Yetenek":     ["Yaratıcı", "Estetik", "Görsel", "Performans", "Edebiyat", "Müzik", "Tasarım", "Film"],
            "Zihinsel Yetenek":     ["Analitik", "Planlama", "Matematik", "Mantık", "Veri", "Bilimsel", "İstatistik", "Mühendislik"],
            "Liderlik":             ["Yönetim", "Etki", "Kurumsal", "Karar Verme", "Liderlik"],
            "Yardımseverlik":       ["İnsan Odaklı", "Sosyal", "Destek", "Toplum", "Gönüllü", "Sivil Toplum", "Yardım"],
            "Bilgelik":             ["Akademik", "Öğretim", "Danışmanlık", "Felsefe", "Mentorluk"],
            "İletişim":             ["Medya", "Yazarlık", "Sunum", "İlişkiler", "Marka", "Halkla İlişkiler", "Dijital Medya"],
            "Maneviyat":            ["İnsan Odaklı", "Danışmanlık", "Terapi", "Koçluk", "Ruh Sağlığı", "Rehberlik", "Psikoloji"],
            "Sağlık/Tıp":           ["İnsan Odaklı", "Bilimsel", "Sağlık", "Bakım", "Tedavi", "Araştırma", "Cerrahi", "Hemşirelik", "Eczacılık"],
            "Spor":                 ["Fiziksel", "Performans", "Antrenman", "Sağlık", "Takım", "Spor Bilimi", "Fizyoterapi"],
            "Zanaatkarlık":         ["Teknik", "El Becerisi", "Üretim", "Uzmanlık", "İnşaat", "Teknoloji", "Mekatronik", "Otomasyon"],
            "Askeriye":             ["Disiplin", "Strateji", "Güvenlik", "Koruma", "Lojistik", "İstihbarat"],
            "Hukuk/Politika":       ["Yasal", "Düzenleme", "Kamu", "Etik", "Hakimiyet", "Mevzuat", "Diplomasi", "Kamu Yönetimi"],
            "Stratejik Zeka":       ["Strateji", "Analitik", "İstihbarat", "Araştırma", "Planlama", "Risk Yönetimi"],
            "Girişimcilik":         ["İş Geliştirme", "Risk", "Yaratıcı", "Teknoloji", "Modern", "Yatırım", "Pazarlama"],
            "Akademik/Araştırma":   ["Bilimsel", "Araştırma", "Veri", "Yayın", "Laboratuvar", "Bilim İletişimi", "Proje Yönetimi"],
            "Yenilikçilik":         ["Teknoloji", "Yenilik", "Modern", "Dijital", "İnovasyon", "Startup"],
        }

        # ═══ GEZEGEN BURÇ KURALLARI (303 öğrenci + 50 ünlü verisinden) ═══
        # Her (gezegen, burç) çifti ilgili kategorilere puan verir.
        # Puanlar empirik olarak belirlenmiştir.

        GEZEGEN_BURC_KURALLARI = {
            # ─── MERKÜR BURCU (303 ogrenci verisinden) ───
            ("Merkür", "Boğa"):   { "Zihinsel Yetenek": 3, "Zanaatkarlık": 3, "Sanatsal Yetenek": 2 },
            ("Merkür", "Başak"):  { "Sağlık/Tıp": 5, "Akademik/Araştırma": 3, "Bilgelik": 3, "Zihinsel Yetenek": 2 },
            ("Merkür", "Oğlak"):  { "Akademik/Araştırma": 3, "Zihinsel Yetenek": 2, "Maneviyat": 2 },
            ("Merkür", "Akrep"):  { "Stratejik Zeka": 3, "Bilgelik": 2, "Hukuk/Politika": 3 },
            ("Merkür", "Yengeç"): { "Maneviyat": 2, "Yardımseverlik": 3, "Sağlık/Tıp": 2, "Zihinsel Yetenek": 2 },
            ("Merkür", "Balık"):  { "Maneviyat": 3, "Sağlık/Tıp": 3, "Bilgelik": 2 },
            ("Merkür", "İkizler"):{ "İletişim": 6, "Zihinsel Yetenek": 3 },
            ("Merkür", "Terazi"): { "İletişim": 5, "Hukuk/Politika": 4, "Sanatsal Yetenek": 2 },
            ("Merkür", "Kova"):   { "Yenilikçilik": 3, "İletişim": 4, "Zihinsel Yetenek": 3, "Bilgelik": 3, "Akademik/Araştırma": 2 },
            ("Merkür", "Koç"):    { "Girişimcilik": 3, "Liderlik": 3, "Spor": 3, "Yardımseverlik": 2 },
            ("Merkür", "Aslan"):  { "Sanatsal Yetenek": 2, "Liderlik": 3, "İletişim": 2 },
            ("Merkür", "Yay"):    { "Akademik/Araştırma": 2, "Bilgelik": 2, "Liderlik": 3 },
            ("Merkür", "Yengeç"): { "İletişim": 3, "Bilgelik": 2, "Spor": 1, "Sağlık/Tıp": 2 },
            ("Merkür", "Boğa"):   { "Zanaatkarlık": 3, "Girişimcilik": 2, "Bilgelik": 2 },
            ("Merkür", "Başak"):  { "Sağlık/Tıp": 4, "Akademik/Araştırma": 3, "Zihinsel Yetenek": 2 },
            ("Merkür", "Oğlak"):  { "Stratejik Zeka": 3, "Bilgelik": 2, "Zihinsel Yetenek": 2 },
            ("Merkür", "Akrep"):  { "Stratejik Zeka": 3, "Bilgelik": 2, "Zihinsel Yetenek": 2 },

            # ─── GÜNEŞ BURCU (303 ogrenci verisinden) ───
            ("Güneş", "Terazi"):  { "Hukuk/Politika": 5, "İletişim": 4, "Zihinsel Yetenek": 2, "Askeriye": 1, "Girişimcilik": 2, "Stratejik Zeka": 2 },
            ("Güneş", "Kova"):    { "Yenilikçilik": 3, "Bilgelik": 2, "Zihinsel Yetenek": 2, "Akademik/Araştırma": 2 },
            ("Güneş", "İkizler"): { "İletişim": 5, "Girişimcilik": 2, "Zihinsel Yetenek": 2 },
            ("Güneş", "Koç"):     { "Girişimcilik": 3, "Liderlik": 3, "Spor": 4, "Askeriye": 3, "Zihinsel Yetenek": 3, "Stratejik Zeka": 3, "Hukuk/Politika": 2, "Yenilikçilik": 2 },
            ("Güneş", "Aslan"):   { "Sanatsal Yetenek": 2, "Liderlik": 3, "İletişim": 2, "Zihinsel Yetenek": 3 },
            ("Güneş", "Yay"):     { "Akademik/Araştırma": 2, "Bilgelik": 3, "Liderlik": 4, "Stratejik Zeka": 2 },
            ("Güneş", "Boğa"):    { "Zanaatkarlık": 4, "Girişimcilik": 3, "Liderlik": 3, "Stratejik Zeka": 2 },
            ("Güneş", "Başak"):   { "Sağlık/Tıp": 5, "Akademik/Araştırma": 3, "Bilgelik": 3, "Zihinsel Yetenek": 1, "Askeriye": 2, "Zanaatkarlık": 2 },
            ("Güneş", "Oğlak"):   { "Stratejik Zeka": 3, "Maneviyat": 3, "Bilgelik": 3, "Zihinsel Yetenek": 2, "Askeriye": 2, "Hukuk/Politika": 2, "Girişimcilik": 2, "Zanaatkarlık": 2 },
            ("Güneş", "Yengeç"):  { "Sağlık/Tıp": 4, "Spor": 4, "Maneviyat": 3, "Yardımseverlik": 2, "Zihinsel Yetenek": 2, "Akademik/Araştırma": 2 },
            ("Güneş", "Akrep"):   { "Stratejik Zeka": 3, "Askeriye": 3, "Bilgelik": 2, "Maneviyat": 2 },
            ("Güneş", "Balık"):   { "Maneviyat": 3, "Sanatsal Yetenek": 2, "Bilgelik": 4, "Yardımseverlik": 3 },

            # ─── AY BURCU ───
            ("Ay", "Koç"):      { "İletişim": 3, "Spor": 3, "Girişimcilik": 1, "Zihinsel Yetenek": 2, "Askeriye": 3 },
            ("Ay", "Boğa"):     { "Zanaatkarlık": 3, "Sanatsal Yetenek": 2, "Liderlik": 1, "Yardımseverlik": 2 },
            ("Ay", "İkizler"):  { "İletişim": 3, "Spor": 2, "Zihinsel Yetenek": 1, "Girişimcilik": 1 },
            ("Ay", "Yengeç"):   { "Maneviyat": 2, "Sağlık/Tıp": 3, "Yardımseverlik": 2, "Sanatsal Yetenek": 1 },
            ("Ay", "Aslan"):    { "Sanatsal Yetenek": 2, "Liderlik": 2, "İletişim": 1, "Zihinsel Yetenek": 2, "Maneviyat": 2 },
            ("Ay", "Başak"):    { "Sağlık/Tıp": 4, "Zanaatkarlık": 3, "Hukuk/Politika": 2, "Akademik/Araştırma": 1, "Bilgelik": 2 },
            ("Ay", "Terazi"):   { "Sanatsal Yetenek": 2, "Hukuk/Politika": 2, "İletişim": 2, "Stratejik Zeka": 2 },
            ("Ay", "Akrep"):    { "Sağlık/Tıp": 3, "Stratejik Zeka": 3, "Maneviyat": 2 },
            ("Ay", "Yay"):      { "Bilgelik": 3, "İletişim": 2, "Liderlik": 1, "Akademik/Araştırma": 3 },
            ("Ay", "Oğlak"):    { "Hukuk/Politika": 3, "Stratejik Zeka": 1, "Askeriye": 2 },
            ("Ay", "Kova"):     { "Yenilikçilik": 1, "İletişim": 2, "Bilgelik": 1 },
            ("Ay", "Balık"):    { "Maneviyat": 2, "Sanatsal Yetenek": 2, "Yardımseverlik": 2 },

            # ─── MARS BURCU ───
            ("Mars", "Koç"):      { "Spor": 10, "Girişimcilik": 4, "Askeriye": 3, "Stratejik Zeka": 3, "Zihinsel Yetenek": 2, "Hukuk/Politika": 2, "Liderlik": 3 },
            ("Mars", "Aslan"):    { "Spor": 7, "Sanatsal Yetenek": 4, "Liderlik": 4, "Zihinsel Yetenek": 2, "Askeriye": 2 },
            ("Mars", "Yay"):      { "Spor": 6, "Bilgelik": 2, "İletişim": 3, "Akademik/Araştırma": 3, "Stratejik Zeka": 2 },
            ("Mars", "Boğa"):     { "Zanaatkarlık": 5, "Sağlık/Tıp": 3, "Girişimcilik": 3, "Hukuk/Politika": 2, "Spor": 4 },
            ("Mars", "Başak"):    { "Sağlık/Tıp": 5, "Askeriye": 4, "Akademik/Araştırma": 2, "Zanaatkarlık": 3 },
            ("Mars", "Oğlak"):    { "Stratejik Zeka": 4, "Askeriye": 5, "Liderlik": 3, "Hukuk/Politika": 2, "Zanaatkarlık": 2, "Yenilikçilik": 2 },
            ("Mars", "İkizler"):  { "İletişim": 6, "Girişimcilik": 2, "Askeriye": 2 },
            ("Mars", "Terazi"):   { "Hukuk/Politika": 7, "İletişim": 4, "Sanatsal Yetenek": 1, "Askeriye": 3, "Girişimcilik": 2, "Stratejik Zeka": 3, "Spor": 2 },
            ("Mars", "Kova"):     { "Yenilikçilik": 4, "Bilgelik": 4, "İletişim": 3 },
            ("Mars", "Yengeç"):   { "Spor": 6, "Yardımseverlik": 4, "Sağlık/Tıp": 3, "Zihinsel Yetenek": 2 },
            ("Mars", "Akrep"):    { "Stratejik Zeka": 2, "Spor": 5, "Askeriye": 4, "Zanaatkarlık": 3 },
            ("Mars", "Balık"):    { "Sanatsal Yetenek": 3, "Maneviyat": 2, "Yardımseverlik": 3, "Zihinsel Yetenek": 2 },

            # ─── VENÜS BURCU ───
            ("Venüs", "Boğa"):    { "Sanatsal Yetenek": 4, "Zanaatkarlık": 3, "Liderlik": 2 },
            ("Venüs", "Terazi"):  { "Sanatsal Yetenek": 3, "Hukuk/Politika": 3, "İletişim": 2, "Stratejik Zeka": 2 },
            ("Venüs", "Balık"):   { "Sağlık/Tıp": 4, "Sanatsal Yetenek": 2, "Maneviyat": 2 },
            ("Venüs", "Aslan"):   { "Sanatsal Yetenek": 2, "İletişim": 3, "Liderlik": 1 },
            ("Venüs", "Akrep"):   { "Maneviyat": 3, "Stratejik Zeka": 3, "Sanatsal Yetenek": 1 },
            ("Venüs", "Koç"):     { "Liderlik": 2, "Spor": 2, "Hukuk/Politika": 2, "Zihinsel Yetenek": 2 },
            ("Venüs", "Yay"):     { "Bilgelik": 4, "İletişim": 3, "Akademik/Araştırma": 2 },
            ("Venüs", "Oğlak"):   { "Zanaatkarlık": 4, "Stratejik Zeka": 1, "Sanatsal Yetenek": 2 },
            ("Venüs", "Kova"):    { "Yenilikçilik": 2, "Zanaatkarlık": 2, "İletişim": 2 },
            ("Venüs", "İkizler"): { "İletişim": 5, "Hukuk/Politika": 3, "Zihinsel Yetenek": 2 },
            ("Venüs", "Yengeç"):  { "Sağlık/Tıp": 4, "Sanatsal Yetenek": 3, "Yardımseverlik": 4 },
            ("Venüs", "Başak"):   { "Sağlık/Tıp": 5, "Akademik/Araştırma": 2, "Sanatsal Yetenek": 1 },

            # ─── JÜPİTER BURCU ───
            ("Jüpiter", "Yay"):   { "Akademik/Araştırma": 3, "Bilgelik": 2, "Maneviyat": 3, "Liderlik": 2, "Zihinsel Yetenek": 2, "Stratejik Zeka": 2, "Askeriye": 2 },
            ("Jüpiter", "Balık"): { "Maneviyat": 2, "Sağlık/Tıp": 3, "Yardımseverlik": 4, "Sanatsal Yetenek": 1 },
            ("Jüpiter", "Koç"):   { "Spor": 4, "Girişimcilik": 3, "Askeriye": 3, "Liderlik": 2, "Hukuk/Politika": 2 },
            ("Jüpiter", "Aslan"): { "Sanatsal Yetenek": 3, "Liderlik": 3, "İletişim": 2, "Zihinsel Yetenek": 2 },
            ("Jüpiter", "Boğa"):  { "Zanaatkarlık": 5, "Girişimcilik": 2, "Liderlik": 2, "Sanatsal Yetenek": 1 },
            ("Jüpiter", "İkizler"):{ "İletişim": 5, "Girişimcilik": 2, "Yenilikçilik": 2, "Yardımseverlik": 2 },
            ("Jüpiter", "Yengeç"):{ "Yardımseverlik": 3, "Sağlık/Tıp": 3, "Maneviyat": 2, "Akademik/Araştırma": 2 },
            ("Jüpiter", "Başak"): { "Sağlık/Tıp": 5, "Akademik/Araştırma": 3, "Bilgelik": 3 },
            ("Jüpiter", "Terazi"):{ "Hukuk/Politika": 5, "İletişim": 3, "Sanatsal Yetenek": 1, "Stratejik Zeka": 3, "Girişimcilik": 3, "Askeriye": 2 },
            ("Jüpiter", "Akrep"): { "Stratejik Zeka": 3, "Maneviyat": 3, "Askeriye": 2, "Zihinsel Yetenek": 2 },
            ("Jüpiter", "Oğlak"): { "Spor": 5, "Askeriye": 3, "Liderlik": 2, "Stratejik Zeka": 2, "Hukuk/Politika": 2, "Girişimcilik": 2 },
            ("Jüpiter", "Kova"):  { "Yenilikçilik": 3, "Bilgelik": 2, "Maneviyat": 3, "Zihinsel Yetenek": 2, "Akademik/Araştırma": 2 },

            # ─── NEPTÜN BURCU ───
            ("Neptün", "Balık"):  { "Maneviyat": 2, "Sağlık/Tıp": 3, "Sanatsal Yetenek": 2, "Yardımseverlik": 2 },
            ("Neptün", "Akrep"):  { "Stratejik Zeka": 2, "Maneviyat": 3, "Sanatsal Yetenek": 1, "Zihinsel Yetenek": 1 },
            ("Neptün", "Yengeç"): { "Maneviyat": 3, "Sağlık/Tıp": 3, "Yardımseverlik": 4, "Sanatsal Yetenek": 1 },
            ("Neptün", "Yay"):    { "Spor": 4, "Bilgelik": 2, "Akademik/Araştırma": 2, "Stratejik Zeka": 2 },
            ("Neptün", "Oğlak"):  { "Spor": 4, "Zanaatkarlık": 3, "Askeriye": 2 },
            ("Neptün", "Başak"):  { "Sağlık/Tıp": 5, "Akademik/Araştırma": 2, "Zanaatkarlık": 2 },
            ("Neptün", "Terazi"): { "Sanatsal Yetenek": 2, "Hukuk/Politika": 2, "Yardımseverlik": 1, "Zihinsel Yetenek": 2 },
            ("Neptün", "Aslan"):  { "İletişim": 4, "Sanatsal Yetenek": 3, "Liderlik": 2 },
            ("Neptün", "Koç"):    { "Maneviyat": 4, "Spor": 2, "Girişimcilik": 1, "Zihinsel Yetenek": 2 },
            ("Neptün", "Boğa"):   { "Zanaatkarlık": 2, "Sanatsal Yetenek": 2 },
            ("Neptün", "İkizler"):{ "İletişim": 3, "Maneviyat": 2 },
            ("Neptün", "Kova"):   { "Yenilikçilik": 3, "Maneviyat": 2 },

            # ─── PLÜTON BURCU ───
            ("Plüton", "Akrep"):  { "Stratejik Zeka": 3, "Askeriye": 4, "Maneviyat": 2, "Sağlık/Tıp": 2 },
            ("Plüton", "Koç"):    { "Liderlik": 4, "Askeriye": 3, "Stratejik Zeka": 3, "Girişimcilik": 3, "Zihinsel Yetenek": 2, "Hukuk/Politika": 2 },
            ("Plüton", "Aslan"):  { "Sanatsal Yetenek": 2, "İletişim": 2, "Liderlik": 1, "Stratejik Zeka": 2 },
            ("Plüton", "Terazi"): { "Hukuk/Politika": 2, "Yardımseverlik": 2, "Sanatsal Yetenek": 1, "Stratejik Zeka": 2 },
            ("Plüton", "Yengeç"): { "Sağlık/Tıp": 4, "Yardımseverlik": 2, "İletişim": 2, "Maneviyat": 2 },
            ("Plüton", "İkizler"):{ "İletişim": 2, "Bilgelik": 2, "Zanaatkarlık": 2, "Zihinsel Yetenek": 3, "Yenilikçilik": 2 },
            ("Plüton", "Boğa"):   { "Zanaatkarlık": 2, "Sanatsal Yetenek": 2 },
            ("Plüton", "Başak"):  { "Sağlık/Tıp": 4, "Akademik/Araştırma": 2 },
            ("Plüton", "Oğlak"):  { "Stratejik Zeka": 3, "Askeriye": 2 },
            ("Plüton", "Kova"):   { "Yenilikçilik": 2, "Girişimcilik": 1 },
            ("Plüton", "Yay"):    { "Akademik/Araştırma": 2, "Bilgelik": 2, "Stratejik Zeka": 1 },
            ("Plüton", "Balık"):  { "Maneviyat": 3, "Sanatsal Yetenek": 2 },

            # ─── SATÜRN BURCU ───
            ("Satürn", "Oğlak"):  { "Stratejik Zeka": 3, "Akademik/Araştırma": 2, "Zanaatkarlık": 4, "Askeriye": 3, "Girişimcilik": 2 },
            ("Satürn", "Kova"):   { "Yenilikçilik": 3, "İletişim": 5, "Bilgelik": 3, "Zihinsel Yetenek": 2, "Askeriye": 2 },
            ("Satürn", "Yay"):    { "Spor": 4, "İletişim": 4, "Bilgelik": 3, "Akademik/Araştırma": 3, "Sanatsal Yetenek": 2, "Stratejik Zeka": 2 },
            ("Satürn", "Akrep"):  { "Stratejik Zeka": 3, "İletişim": 5, "Maneviyat": 3 },
            ("Satürn", "Aslan"):  { "Askeriye": 4, "Liderlik": 4, "Stratejik Zeka": 3, "Hukuk/Politika": 2 },
            ("Satürn", "Balık"):  { "Maneviyat": 3, "Liderlik": 3, "Yardımseverlik": 2 },
            ("Satürn", "Başak"):  { "Sağlık/Tıp": 5, "Akademik/Araştırma": 3, "Zanaatkarlık": 4 },
            ("Satürn", "Terazi"): { "Hukuk/Politika": 3, "Stratejik Zeka": 2 },

            # ─── URANÜS BURCU ───
            ("Uranüs", "Kova"):   { "Yenilikçilik": 5, "Bilgelik": 3, "İletişim": 3, "Zihinsel Yetenek": 2 },
            ("Uranüs", "Koç"):    { "Yenilikçilik": 4, "Spor": 3, "Girişimcilik": 3, "Liderlik": 2, "Stratejik Zeka": 3 },
            ("Uranüs", "Akrep"):  { "Yenilikçilik": 3, "Stratejik Zeka": 3, "Maneviyat": 2 },
            ("Uranüs", "Terazi"): { "Yenilikçilik": 2, "Hukuk/Politika": 3, "İletişim": 2, "Stratejik Zeka": 2 },
            ("Uranüs", "Boğa"):   { "Yenilikçilik": 3, "Zanaatkarlık": 3, "Liderlik": 2, "Zihinsel Yetenek": 2, "Girişimcilik": 2 },
            ("Uranüs", "Aslan"):  { "Yenilikçilik": 2, "Sanatsal Yetenek": 3, "Liderlik": 2, "Zihinsel Yetenek": 2 },
            ("Uranüs", "Başak"):  { "Sağlık/Tıp": 5, "Akademik/Araştırma": 2, "Yenilikçilik": 1, "Zihinsel Yetenek": 3 },
            ("Uranüs", "Yay"):    { "Yenilikçilik": 3, "Spor": 2, "Bilgelik": 2, "Akademik/Araştırma": 2 },
        }

        # ═══ EV BAZLI KATEGORİ BONUSU (50 ünlü pozisyon verisinden) ═══
        EV_KATEGORI = {
            1:  { "Liderlik": 2, "Spor": 4, "Askeriye": 3, "Girişimcilik": 3, "Stratejik Zeka": 2 },
            2:  { "Zanaatkarlık": 5, "Girişimcilik": 3, "Sağlık/Tıp": 3, "Yenilikçilik": 2 },
            3:  { "İletişim": 5, "Girişimcilik": 2, "Sanatsal Yetenek": 2, "Hukuk/Politika": 2 },
            4:  { "Yardımseverlik": 4, "Maneviyat": 3, "Sağlık/Tıp": 3, "Sanatsal Yetenek": 1 },
            5:  { "Sanatsal Yetenek": 3, "Girişimcilik": 2, "Yenilikçilik": 2, "Zanaatkarlık": 2 },
            6:  { "Zanaatkarlık": 4, "Sağlık/Tıp": 4, "Akademik/Araştırma": 4, "Bilgelik": 2 },
            7:  { "İletişim": 4, "Hukuk/Politika": 4, "Yardımseverlik": 2, "Liderlik": 1, "Stratejik Zeka": 2 },
            8:  { "Stratejik Zeka": 4, "Sağlık/Tıp": 4, "Maneviyat": 4, "Askeriye": 3 },
            9:  { "Bilgelik": 3, "Akademik/Araştırma": 5, "Liderlik": 1, "Yenilikçilik": 2, "İletişim": 2 },
            10: { "Liderlik": 3, "Stratejik Zeka": 4, "Askeriye": 4, "Girişimcilik": 3, "Hukuk/Politika": 2 },
            11: { "Yenilikçilik": 5, "Girişimcilik": 3, "İletişim": 2, "Zanaatkarlık": 2, "Akademik/Araştırma": 2 },
            12: { "Maneviyat": 5, "Yardımseverlik": 3, "Sanatsal Yetenek": 3, "Bilgelik": 2, "Akademik/Araştırma": 2 },
        }

        # ═══ MC BURÇ KURALLARI (50 ünlü pozisyon verisinden) ═══
        MC_BURC_KURALLARI = {
            "Koç":     { "Liderlik": 4, "Spor": 5, "Askeriye": 4, "Girişimcilik": 2 },
            "Boğa":    { "Zanaatkarlık": 5, "Girişimcilik": 2, "Sağlık/Tıp": 3 },
            "İkizler": { "İletişim": 5, "Girişimcilik": 2, "Hukuk/Politika": 1, "Liderlik": 2 },
            "Yengeç":  { "Sağlık/Tıp": 5, "Yardımseverlik": 4, "Maneviyat": 3 },
            "Aslan":   { "Sanatsal Yetenek": 3, "Liderlik": 2, "İletişim": 2, "Askeriye": 1 },
            "Başak":   { "Sağlık/Tıp": 5, "Akademik/Araştırma": 4, "Zanaatkarlık": 3, "Bilgelik": 2 },
            "Terazi":  { "Hukuk/Politika": 5, "Sanatsal Yetenek": 3, "İletişim": 3, "Stratejik Zeka": 2 },
            "Akrep":   { "Stratejik Zeka": 5, "Askeriye": 4, "Maneviyat": 2, "Hukuk/Politika": 1 },
            "Yay":     { "Akademik/Araştırma": 3, "Bilgelik": 5, "Liderlik": 2, "Yenilikçilik": 1 },
            "Oğlak":   { "Stratejik Zeka": 3, "Askeriye": 3, "Liderlik": 3, "Girişimcilik": 2, "Zanaatkarlık": 2 },
            "Kova":    { "Yenilikçilik": 4, "Maneviyat": 6, "Bilgelik": 3, "Akademik/Araştırma": 1, "Liderlik": 2 },
            "Balık":   { "Sağlık/Tıp": 5, "Maneviyat": 4, "Sanatsal Yetenek": 3, "Bilgelik": 2 },
        }

        # ═══ ASC BURÇ KURALLARI (empirik sağlık verisinden) ═══
        ASC_BURC_KURALLARI = {
            "Koç":     { "Spor": 3, "Askeriye": 3, "Liderlik": 2, "Girişimcilik": 1 },
            "Boğa":    { "Zanaatkarlık": 3, "Sağlık/Tıp": 2, "Girişimcilik": 1 },
            "İkizler": { "İletişim": 3, "Girişimcilik": 2, "Hukuk/Politika": 1 },
            "Yengeç":  { "Sağlık/Tıp": 3, "Yardımseverlik": 3, "Maneviyat": 1 },
            "Aslan":   { "Sanatsal Yetenek": 3, "Liderlik": 3, "Askeriye": 1 },
            "Başak":   { "Sağlık/Tıp": 3, "Akademik/Araştırma": 2, "Zanaatkarlık": 2, "Stratejik Zeka": 1 },
            "Terazi":  { "Hukuk/Politika": 3, "Sanatsal Yetenek": 2, "Stratejik Zeka": 1 },
            "Akrep":   { "Stratejik Zeka": 3, "Askeriye": 2, "Zihinsel Yetenek": 1, "Hukuk/Politika": 1 },
            "Yay":     { "Bilgelik": 3, "Akademik/Araştırma": 2, "Liderlik": 1 },
            "Oğlak":   { "Stratejik Zeka": 3, "Askeriye": 2, "Girişimcilik": 1, "Zanaatkarlık": 1 },
            "Kova":    { "Yenilikçilik": 3, "Girişimcilik": 2, "Akademik/Araştırma": 1, "Spor": 1 },
            "Balık":   { "Maneviyat": 3, "Sağlık/Tıp": 2, "Sanatsal Yetenek": 1 },
        }

        # ═══ GEZEGEN-EV KURALLARI (gezegenin hangi evde hangi kategorilere puan verdiği) ═══
        # Her ev kendi burcunun temasını taşır: 1=Koç, 2=Boğa, ..., 12=Balık
        # Gezegen evdeyken o evin temasını kendi filtresiyle ifade eder
        GEZEGEN_EV_KURALLARI = {
            # ── GÜNEŞ ──
            ("Güneş", 1):  { "Liderlik": 3, "Girişimcilik": 2 },
            ("Güneş", 2):  { "Zanaatkarlık": 2, "Girişimcilik": 2 },
            ("Güneş", 3):  { "İletişim": 2, "Zihinsel Yetenek": 2 },
            ("Güneş", 4):  { "Yardımseverlik": 2, "Maneviyat": 1 },
            ("Güneş", 5):  { "Sanatsal Yetenek": 3, "Girişimcilik": 2 },
            ("Güneş", 6):  { "Zanaatkarlık": 2, "Sağlık/Tıp": 2 },
            ("Güneş", 7):  { "Hukuk/Politika": 3, "İletişim": 2 },
            ("Güneş", 8):  { "Stratejik Zeka": 2, "Sağlık/Tıp": 2 },
            ("Güneş", 9):  { "Bilgelik": 3, "Akademik/Araştırma": 2 },
            ("Güneş", 10): { "Liderlik": 4, "Hukuk/Politika": 2, "Stratejik Zeka": 2 },
            ("Güneş", 11): { "Yenilikçilik": 3, "Girişimcilik": 2 },
            ("Güneş", 12): { "Maneviyat": 3, "Yardımseverlik": 2 },
            # ── AY ──
            ("Ay", 1):  { "Yardımseverlik": 2, "İletişim": 2 },
            ("Ay", 2):  { "Zanaatkarlık": 2, "Sanatsal Yetenek": 2 },
            ("Ay", 3):  { "İletişim": 3, "Zihinsel Yetenek": 2 },
            ("Ay", 4):  { "Yardımseverlik": 3, "Maneviyat": 2 },
            ("Ay", 5):  { "Sanatsal Yetenek": 3, "Maneviyat": 2 },
            ("Ay", 6):  { "Sağlık/Tıp": 3, "Yardımseverlik": 2 },
            ("Ay", 7):  { "İletişim": 3, "Yardımseverlik": 2 },
            ("Ay", 8):  { "Stratejik Zeka": 2, "Maneviyat": 2 },
            ("Ay", 9):  { "Bilgelik": 2, "Maneviyat": 3 },
            ("Ay", 10): { "Sağlık/Tıp": 2, "Yardımseverlik": 3 },
            ("Ay", 11): { "Yardımseverlik": 3, "İletişim": 2 },
            ("Ay", 12): { "Maneviyat": 4, "Yardımseverlik": 3 },
            # ── MERKÜR ──
            ("Merkür", 1):  { "İletişim": 3, "Zihinsel Yetenek": 2 },
            ("Merkür", 2):  { "Zanaatkarlık": 2, "Girişimcilik": 2 },
            ("Merkür", 3):  { "İletişim": 4, "Zihinsel Yetenek": 3 },
            ("Merkür", 4):  { "İletişim": 2, "Zihinsel Yetenek": 2 },
            ("Merkür", 5):  { "Sanatsal Yetenek": 2, "İletişim": 2 },
            ("Merkür", 6):  { "Zanaatkarlık": 3, "Akademik/Araştırma": 3 },
            ("Merkür", 7):  { "Hukuk/Politika": 3, "İletişim": 3 },
            ("Merkür", 8):  { "Stratejik Zeka": 3, "Zihinsel Yetenek": 3 },
            ("Merkür", 9):  { "Akademik/Araştırma": 4, "Bilgelik": 3 },
            ("Merkür", 10): { "İletişim": 3, "Hukuk/Politika": 3, "Zihinsel Yetenek": 2 },
            ("Merkür", 11): { "Yenilikçilik": 3, "İletişim": 3 },
            ("Merkür", 12): { "Akademik/Araştırma": 2, "Maneviyat": 2 },
            # ── VENÜS ──
            ("Venüs", 1):  { "Sanatsal Yetenek": 3, "İletişim": 2 },
            ("Venüs", 2):  { "Zanaatkarlık": 3, "Sanatsal Yetenek": 3 },
            ("Venüs", 3):  { "İletişim": 2, "Sanatsal Yetenek": 2 },
            ("Venüs", 4):  { "Sanatsal Yetenek": 2, "Yardımseverlik": 2 },
            ("Venüs", 5):  { "Sanatsal Yetenek": 4, "Girişimcilik": 2 },
            ("Venüs", 6):  { "Zanaatkarlık": 3, "Sağlık/Tıp": 2 },
            ("Venüs", 7):  { "Hukuk/Politika": 4, "Sanatsal Yetenek": 3, "İletişim": 2 },
            ("Venüs", 8):  { "Stratejik Zeka": 2, "Sanatsal Yetenek": 2 },
            ("Venüs", 9):  { "Sanatsal Yetenek": 3, "Bilgelik": 2 },
            ("Venüs", 10): { "Sanatsal Yetenek": 3, "Hukuk/Politika": 3 },
            ("Venüs", 11): { "Sanatsal Yetenek": 3, "Yenilikçilik": 2 },
            ("Venüs", 12): { "Maneviyat": 3, "Sanatsal Yetenek": 3 },
            # ── MARS ──
            ("Mars", 1):  { "Liderlik": 3, "Spor": 3, "Askeriye": 2, "Girişimcilik": 2 },
            ("Mars", 2):  { "Girişimcilik": 3, "Zanaatkarlık": 2 },
            ("Mars", 3):  { "İletişim": 2, "Zihinsel Yetenek": 2 },
            ("Mars", 4):  { "Zanaatkarlık": 2, "Spor": 2 },
            ("Mars", 5):  { "Spor": 3, "Girişimcilik": 2, "Sanatsal Yetenek": 2 },
            ("Mars", 6):  { "Zanaatkarlık": 3, "Spor": 3, "Askeriye": 2 },
            ("Mars", 7):  { "Askeriye": 3, "Hukuk/Politika": 2 },
            ("Mars", 8):  { "Stratejik Zeka": 4, "Askeriye": 3 },
            ("Mars", 9):  { "Askeriye": 2, "Bilgelik": 2 },
            ("Mars", 10): { "Askeriye": 4, "Liderlik": 3, "Stratejik Zeka": 3 },
            ("Mars", 11): { "Girişimcilik": 3, "Askeriye": 2, "Yenilikçilik": 2 },
            ("Mars", 12): { "Askeriye": 2, "Stratejik Zeka": 2 },
            # ── JÜPİTER ──
            ("Jüpiter", 1):  { "Liderlik": 3, "Bilgelik": 2, "Girişimcilik": 2 },
            ("Jüpiter", 2):  { "Girişimcilik": 3, "Zanaatkarlık": 2 },
            ("Jüpiter", 3):  { "İletişim": 3, "Bilgelik": 2 },
            ("Jüpiter", 4):  { "Yardımseverlik": 3, "Maneviyat": 2 },
            ("Jüpiter", 5):  { "Sanatsal Yetenek": 3, "Girişimcilik": 2 },
            ("Jüpiter", 6):  { "Sağlık/Tıp": 3, "Zanaatkarlık": 2 },
            ("Jüpiter", 7):  { "Hukuk/Politika": 4, "İletişim": 3, "Yardımseverlik": 2 },
            ("Jüpiter", 8):  { "Stratejik Zeka": 3, "Maneviyat": 2 },
            ("Jüpiter", 9):  { "Bilgelik": 5, "Akademik/Araştırma": 3 },
            ("Jüpiter", 10): { "Liderlik": 3, "Hukuk/Politika": 3, "Bilgelik": 2 },
            ("Jüpiter", 11): { "Girişimcilik": 4, "Yenilikçilik": 3 },
            ("Jüpiter", 12): { "Maneviyat": 4, "Yardımseverlik": 3 },
            # ── SATÜRN ──
            ("Satürn", 1):  { "Askeriye": 2, "Stratejik Zeka": 2 },
            ("Satürn", 2):  { "Zanaatkarlık": 3, "Girişimcilik": 2 },
            ("Satürn", 3):  { "Zihinsel Yetenek": 3, "İletişim": 2 },
            ("Satürn", 4):  { "Zanaatkarlık": 3, "Yardımseverlik": 2 },
            ("Satürn", 5):  { "Zanaatkarlık": 3, "Sanatsal Yetenek": 2 },
            ("Satürn", 6):  { "Zanaatkarlık": 4, "Sağlık/Tıp": 3, "Akademik/Araştırma": 2 },
            ("Satürn", 7):  { "Hukuk/Politika": 3, "Stratejik Zeka": 3 },
            ("Satürn", 8):  { "Stratejik Zeka": 4, "Askeriye": 2 },
            ("Satürn", 9):  { "Akademik/Araştırma": 4, "Bilgelik": 3 },
            ("Satürn", 10): { "Askeriye": 3, "Liderlik": 3, "Stratejik Zeka": 3 },
            ("Satürn", 11): { "Yenilikçilik": 3, "Girişimcilik": 3 },
            ("Satürn", 12): { "Maneviyat": 3, "Akademik/Araştırma": 2 },
            # ── URANÜS ──
            ("Uranüs", 1):  { "Yenilikçilik": 4, "Girişimcilik": 3 },
            ("Uranüs", 2):  { "Yenilikçilik": 3, "Zanaatkarlık": 2 },
            ("Uranüs", 3):  { "İletişim": 3, "Yenilikçilik": 3 },
            ("Uranüs", 4):  { "Yenilikçilik": 3, "Zanaatkarlık": 2 },
            ("Uranüs", 5):  { "Sanatsal Yetenek": 3, "Yenilikçilik": 3 },
            ("Uranüs", 6):  { "Yenilikçilik": 3, "Akademik/Araştırma": 2 },
            ("Uranüs", 7):  { "Hukuk/Politika": 3, "Yenilikçilik": 3 },
            ("Uranüs", 8):  { "Yenilikçilik": 3, "Stratejik Zeka": 3 },
            ("Uranüs", 9):  { "Yenilikçilik": 4, "Akademik/Araştırma": 3, "Bilgelik": 2 },
            ("Uranüs", 10): { "Yenilikçilik": 4, "Liderlik": 3, "Stratejik Zeka": 3 },
            ("Uranüs", 11): { "Yenilikçilik": 5, "Girişimcilik": 3 },
            ("Uranüs", 12): { "Yenilikçilik": 3, "Maneviyat": 2 },
            # ── NEPTÜN ──
            ("Neptün", 1):  { "Maneviyat": 3, "Sanatsal Yetenek": 3 },
            ("Neptün", 2):  { "Sanatsal Yetenek": 3, "Zanaatkarlık": 2 },
            ("Neptün", 3):  { "İletişim": 2, "Maneviyat": 3 },
            ("Neptün", 4):  { "Maneviyat": 3, "Yardımseverlik": 3 },
            ("Neptün", 5):  { "Sanatsal Yetenek": 4, "Maneviyat": 3 },
            ("Neptün", 6):  { "Sağlık/Tıp": 4, "Maneviyat": 3 },
            ("Neptün", 7):  { "İletişim": 3, "Sanatsal Yetenek": 3, "Yardımseverlik": 2 },
            ("Neptün", 8):  { "Maneviyat": 4, "Stratejik Zeka": 2 },
            ("Neptün", 9):  { "Bilgelik": 3, "Maneviyat": 4 },
            ("Neptün", 10): { "Maneviyat": 4, "Sanatsal Yetenek": 3 },
            ("Neptün", 11): { "Maneviyat": 3, "Yenilikçilik": 2 },
            ("Neptün", 12): { "Maneviyat": 5, "Yardımseverlik": 4, "Sanatsal Yetenek": 3 },
            # ── PLÜTON ──
            ("Plüton", 1):  { "Stratejik Zeka": 3, "Liderlik": 2 },
            ("Plüton", 2):  { "Stratejik Zeka": 3, "Girişimcilik": 2 },
            ("Plüton", 3):  { "Stratejik Zeka": 3, "Zihinsel Yetenek": 2 },
            ("Plüton", 4):  { "Stratejik Zeka": 3, "Maneviyat": 2 },
            ("Plüton", 5):  { "Stratejik Zeka": 3, "Sanatsal Yetenek": 2 },
            ("Plüton", 6):  { "Stratejik Zeka": 3, "Sağlık/Tıp": 2 },
            ("Plüton", 7):  { "Stratejik Zeka": 4, "Hukuk/Politika": 3 },
            ("Plüton", 8):  { "Stratejik Zeka": 5, "Askeriye": 3 },
            ("Plüton", 9):  { "Stratejik Zeka": 3, "Bilgelik": 3 },
            ("Plüton", 10): { "Stratejik Zeka": 4, "Liderlik": 3, "Askeriye": 3 },
            ("Plüton", 11): { "Stratejik Zeka": 3, "Yenilikçilik": 3 },
            ("Plüton", 12): { "Stratejik Zeka": 3, "Maneviyat": 4 },
        }

        # ═══ HESAPLAMA ═══
        j1 = mc_bilgisi["jd"] if mc_bilgisi else None
        raw = {k: 0.0 for k in tum_kategoriler}
        detay_bilgi = {k: [] for k in tum_kategoriler}

        # --- A) GEZEGEN BURÇ + EV PUANLARI ---
        if j1:
            burclar = ["Koç","Boğa","İkizler","Yengeç","Aslan","Başak",
                       "Terazi","Akrep","Yay","Oğlak","Kova","Balık"]
            gezegen_listesi = [
                ("Güneş", swe.SUN), ("Ay", swe.MOON), ("Merkür", swe.MERCURY),
                ("Venüs", swe.VENUS), ("Mars", swe.MARS), ("Jüpiter", swe.JUPITER),
                ("Satürn", swe.SATURN), ("Uranüs", swe.URANUS), ("Neptün", swe.NEPTUNE),
                ("Plüton", swe.PLUTO),
            ]
            gezegen_agirliklari = {
                "Güneş": 1.7, "Ay": 1.3, "Merkür": 1.1, "Venüs": 0.9,
                "Mars": 1.1, "Jüpiter": 0.7, "Satürn": 0.6,
                "Uranüs": 0.4, "Neptün": 0.4, "Plüton": 0.4,
            }
            for g_isim, g_id in gezegen_listesi:
                try:
                    pos = get_planetary_position(j1, g_id)
                    burc = burclar[int(pos / 30) % 12]
                    ev = gezegen_evleri.get(g_isim, 0)
                    g_agirlik = gezegen_agirliklari.get(g_isim, 1.0)

                    kurallar_burc = GEZEGEN_BURC_KURALLARI.get((g_isim, burc), {})
                    if len(kurallar_burc) > 2:
                        kurallar_burc = dict(sorted(kurallar_burc.items(), key=lambda x: -x[1])[:2])
                    for k, v in kurallar_burc.items():
                        if k in raw:
                            raw[k] += v * g_agirlik
                            detay_bilgi[k].append(f"{g_isim} {burc} (Ev{ev})")

                    if ev in (2, 6, 10):
                        kurallar_ev = GEZEGEN_EV_KURALLARI.get((g_isim, ev), {})
                        for k, v in kurallar_ev.items():
                            if k in raw:
                                raw[k] += v * g_agirlik * 0.2
                except Exception:
                    continue

        # --- B) EV BAZLI BONUSLAR ---
        for g_isim, ev in gezegen_evleri.items():
            if ev in EV_KATEGORI:
                for k, v in EV_KATEGORI[ev].items():
                    if k in raw:
                        bonus = v * 0.2
                        raw[k] += bonus

        # --- C) MC BURÇ PUANLARI ---
        if mc_bilgisi:
            mc_burc = mc_bilgisi.get("mc_burc", "")
            for k, v in MC_BURC_KURALLARI.get(mc_burc, {}).items():
                if k in raw:
                    raw[k] += v * 0.7
                    detay_bilgi[k].append(f"MC {mc_burc}")

            yonetici = mc_bilgisi.get("yonetici_konum", {})
            if yonetici:
                ye = yonetici.get("ev", 0)
                yb = yonetici.get("burc", "")
                if ye in EV_KATEGORI:
                    for k, v in EV_KATEGORI[ye].items():
                        if k in raw:
                            raw[k] += v * 0.3
                yon_kurallar = GEZEGEN_BURC_KURALLARI.get((mc_bilgisi.get("mc_yonetici", ""), yb), {})
                if len(yon_kurallar) > 2:
                    yon_kurallar = dict(sorted(yon_kurallar.items(), key=lambda x: -x[1])[:2])
                for k, v in yon_kurallar.items():
                    if k in raw:
                        raw[k] += v * 0.4

        # --- C2) ASC BURÇ PUANLARI ---
        if j1:
            try:
                _, ascmc_local = swe.houses_ex(j1, self.enlem, self.boylam, b'P')
                asc_derece = ascmc_local[0] % 360
                asc_burc = burclar[int(asc_derece / 30) % 12]
                for k, v in ASC_BURC_KURALLARI.get(asc_burc, {}).items():
                    if k in raw:
                        raw[k] += v * 0.7
                        detay_bilgi[k].append(f"ASC {asc_burc}")
            except Exception:
                pass

        # --- D) SABİT YILDIZLAR ---
        KISISEL_GZ = {"Güneş", "Ay", "Merkür", "Venüs", "Mars"}
        for y in yildiz_bilgisi.get("tum_yildizlar", []):
            orb = y.get("orb", 3.0)
            tip = y.get("tip", "")
            oc = 1.0 if orb <= 1 else 0.8 if orb <= 2 else 0.5
            tc = { "MC_YONETICI": 2.5, "MC": 2.0, "YUKSELEN": 1.5 }.get(tip, 0.8)
            if tip == "GEZEGEN":
                gz = y.get("gezegen", "")
                tc = 1.5 if gz in KISISEL_GZ else 0.8
            for k, v in y.get("meslek_etkileri", {}).items():
                if k in raw:
                    raw[k] += v * oc * tc * 0.4

        # --- E) ARAP NOKTASI ---
        if arap_bilgisi:
            ab = arap_bilgisi.get("ruh_burc", "")
            ae = arap_bilgisi.get("ruh_ev", 0)
            am = self.MESLEK_ARAP_BURC_MAP.get(ab, {})
            AE = {1: 2.0, 4: 1.5, 7: 1.0, 10: 2.5}
            aeb = AE.get(ae, 0)
            for k, v in am.items():
                if k in raw:
                    raw[k] += (v + aeb) * 0.3

        # --- F) ASTEROİDLER ---
        if ast_bilgileri:
            for k, v in ast_bilgileri.items():
                if k in raw:
                    raw[k] += min(v, 10.0) * 0.3

        # --- F2) ASTEROİT-BURÇ BONUS (empirik terzi verisi) ---
        # Sadece en güçlü empirik sinyaller: Vulkanus-İkizler(9/15), Zeus-Aslan(8/15)
        ASTEROIT_ZANAAT_BURC = {
            ("Zeus", "Aslan"):      5,  # 8/15 terzide var
            ("Zeus", "Başak"):      3,  # Tom Ford
            ("Vulkanus", "İkizler"): 7,  # 9/15 terzide — en güçlü sinyal
            ("Vulkanus", "Boğa"):    4,  # 4/15
            ("Pallas", "Oğlak"):     4,  # 6/15
            ("Edison", "Başak"):     5,  # 3/3 terzide var
        }
        try:
            AST_ZN_MAP = {
                "Zeus": swe.ZEUS, "Admetos": swe.ADMETOS, "Vulkanus": swe.VULKANUS,
                "Pallas": swe.PALLAS,
            }
            if j1:
                for ast_ad, ast_id in AST_ZN_MAP.items():
                    try:
                        ast_pos = swe.calc_ut(j1, ast_id)[0][0] % 360
                        ast_burc = burclar[int(ast_pos / 30) % 12]
                        zan_puan = ASTEROIT_ZANAAT_BURC.get((ast_ad, ast_burc), 0)
                        if zan_puan > 0:
                            raw["Zanaatkarlık"] += zan_puan * 0.35
                            detay_bilgi["Zanaatkarlık"].append(f"{ast_ad} {ast_burc}")
                    except:
                        continue
                # Edison Sayili asteroit
                try:
                    ed_pos = swe.calc_ut(j1, swe.AST_OFFSET + 742)[0][0] % 360
                    ed_burc = burclar[int(ed_pos / 30) % 12]
                    zan_puan = ASTEROIT_ZANAAT_BURC.get(("Edison", ed_burc), 0)
                    if zan_puan > 0:
                        raw["Zanaatkarlık"] += zan_puan * 0.35
                        detay_bilgi["Zanaatkarlık"].append(f"Edison {ed_burc}")
                except:
                    pass
        except:
            pass

        # ═══ AÇISAL POTANSİYEL PUANLARI (FBST_POTANSIYEL_EBEVEYN'den) ═══
        # potansiyel_hesapla() aci eslesmelerini bulur; bunlar GEZEGEN_BURC'a ek destek saglar.
        # Kategori basi max 5 puan ile sinirlandirilir (Zihinsel gibi cok girisli kategoriler domine etmesin).
        if potansiyeller:
            pot_kat_puanlari = {}
            for p in potansiyeller:
                alan = p.get("alan", "")
                aci_turu = p.get("aci_turu", "")
                orb = p.get("orb", 8.0)
                if alan in raw:
                    taban = aci_taban_puan.get(aci_turu, 2)
                    orb_c = 1.0 - (orb / 8.0) * 0.6
                    puan = taban * max(orb_c, 0.3) * 0.30
                    pot_kat_puanlari.setdefault(alan, 0)
                    if pot_kat_puanlari[alan] < 5.0:
                        ek = min(puan, 5.0 - pot_kat_puanlari[alan])
                        raw[alan] += ek
                        pot_kat_puanlari[alan] += ek
                        detay_bilgi[alan].append(f"Aci:{p.get('aci','')} {aci_turu}")

        # ═══ ÇAPRAZ BONUS: Liderlik ↔ Hukuk/Politika ═══
        ldr = raw["Liderlik"]
        huk = raw["Hukuk/Politika"]
        if ldr > 0 and huk > 0:
            raw["Liderlik"] += huk * 0.02
            raw["Hukuk/Politika"] += ldr * 0.02
        elif ldr > 0:
            raw["Hukuk/Politika"] += ldr * 0.01
        elif huk > 0:
            raw["Liderlik"] += huk * 0.01

        # ═══ ÇAPRAZ BONUS: Sağlık/Tıp ↔ Zihinsel Yetenek ═══
        zih = raw["Zihinsel Yetenek"]
        sag = raw["Sağlık/Tıp"]
        if zih > 8 and sag > 4:
            raw["Sağlık/Tıp"] += zih * 0.02

        # ═══ ÇAPRAZ BONUS: Bilgelik → Zihinsel Yetenek + Akademik ═══
        bil = raw["Bilgelik"]
        if bil > 3:
            raw["Zihinsel Yetenek"] += bil * 0.03
            raw["Akademik/Araştırma"] += bil * 0.03

        # ═══ ÇAPRAZ BONUS: Liderlik → Stratejik Zeka + Askeriye + Girişimcilik ═══
        ldr2 = raw["Liderlik"]
        if ldr2 > 3:
            raw["Stratejik Zeka"] += ldr2 * 0.02
            raw["Askeriye"] += ldr2 * 0.02
            raw["Girişimcilik"] += ldr2 * 0.02

        # ═══ ÇAPRAZ BONUS: İletişim → Hukuk/Politika + Girişimcilik ═══
        ilet = raw["İletişim"]
        if ilet > 3:
            raw["Hukuk/Politika"] += ilet * 0.02
            raw["Girişimcilik"] += ilet * 0.02

        # ═══ ÇAPRAZ BONUS: Sanatsal Yetenek → Yenilikçilik + Zanaatkarlık ═══
        san = raw["Sanatsal Yetenek"]
        if san > 3:
            raw["Yenilikçilik"] += san * 0.02
            raw["Zanaatkarlık"] += san * 0.02

        # ═══ ÇAPRAZ BONUS: Spor → Askeriye + Sağlık/Tıp ═══
        spr = raw["Spor"]
        if spr > 3:
            raw["Askeriye"] += spr * 0.04
            raw["Sağlık/Tıp"] += spr * 0.03

        # ═══ ÇAPRAZ BONUS: Maneviyat → Yardımseverlik + Akademik ═══
        man = raw["Maneviyat"]
        if man > 3:
            raw["Yardımseverlik"] += man * 0.05
            raw["Akademik/Araştırma"] += man * 0.03

        # ═══ ÇAPRAZ BONUS: Zanaatkarlık → Sanatsal + Girişimcilik ═══
        zan = raw["Zanaatkarlık"]
        if zan > 3:
            raw["Sanatsal Yetenek"] += zan * 0.03
            raw["Girişimcilik"] += zan * 0.02

        # ═══ ÇAPRAZ BONUS: Akademik → Bilgelik + Zihinsel ═══
        aca = raw["Akademik/Araştırma"]
        if aca > 3:
            raw["Bilgelik"] += aca * 0.04
            raw["Zihinsel Yetenek"] += aca * 0.03

        # ═══ ÇAPRAZ BONUS: Stratejik Zeka → Askeriye + Girişimcilik ═══
        strz = raw["Stratejik Zeka"]
        if strz > 3:
            raw["Askeriye"] += strz * 0.03
            raw["Girişimcilik"] += strz * 0.02

        # ═══ EV YÖNETİCİSİ ANALİZİ (2., 6., 10. Ev) ═══
        # Her evin yönetici gezegeninin burcu ve ev konumu kariyer potansiyelini güçlendirir.
        # 10. Ev yöneticisi en önemli kariyer göstergesidir.
        burc_yoneticisi = {
            "Koç": "Mars", "Boğa": "Venüs", "İkizler": "Merkür", "Yengeç": "Ay",
            "Aslan": "Güneş", "Başak": "Merkür", "Terazi": "Venüs", "Akrep": "Mars",
            "Yay": "Jüpiter", "Oğlak": "Satürn", "Kova": "Uranüs", "Balık": "Neptün",
        }
        if j1:
            try:
                _, ascmc_cusps = swe.houses_ex(j1, self.enlem, self.boylam, b'P')
                ev_kritik = {2: 0.6, 6: 0.5, 10: 1.0}
                for ev_no, agirlik in ev_kritik.items():
                    cusp_derece = ascmc_cusps[ev_no - 1] % 360
                    cusp_burc = burclar[int(cusp_derece / 30) % 12]
                    yonetici = burc_yoneticisi.get(cusp_burc, "")
                    if not yonetici:
                        continue
                    yon_ev = gezegen_evleri.get(yonetici, 0)
                    try:
                        yon_id = {"Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY,
                                  "Venüs": swe.VENUS, "Mars": swe.MARS, "Jüpiter": swe.JUPITER,
                                  "Satürn": swe.SATURN, "Uranüs": swe.URANUS, "Neptün": swe.NEPTUNE,
                                  "Plüton": swe.PLUTO}.get(yonetici)
                        if yon_id is not None:
                            yon_pos = get_planetary_position(j1, yon_id)
                            yon_burc = burclar[int(yon_pos / 30) % 12]
                        else:
                            yon_burc = ""
                    except Exception:
                        yon_burc = ""
                    yon_kurallar = GEZEGEN_BURC_KURALLARI.get((yonetici, yon_burc), {})
                    if len(yon_kurallar) > 2:
                        yon_kurallar = dict(sorted(yon_kurallar.items(), key=lambda x: -x[1])[:2])
                    for k, v in yon_kurallar.items():
                        if k in raw:
                            raw[k] += v * agirlik * 0.2
                            detay_bilgi[k].append(f"{ev_no}.Ev Yön. {yonetici} {yon_burc} (Ev{yon_ev})")
                    if yon_ev in EV_KATEGORI:
                        for k, v in EV_KATEGORI[yon_ev].items():
                            if k in raw:
                                raw[k] += v * agirlik * 0.15
                    angular = yon_ev in (1, 4, 7, 10)
                    succedent = yon_ev in (2, 5, 8, 11)
                    if angular:
                        for k in yon_kurallar:
                            if k in raw:
                                raw[k] += 0.7 * agirlik
                    elif succedent:
                        for k in yon_kurallar:
                            if k in raw:
                                raw[k] += 0.35 * agirlik
            except Exception:
                pass

        # ═══ NORMALİZASYON ═══
        alan_puanlari = {}
        alan_aci_detay = {}
        alan_aci_sayisi = {}
        alan_gezegenler = {}

        for k in tum_kategoriler:
            alan_puanlari[k] = round(raw[k], 2)
            alan_aci_detay[k] = "; ".join(detay_bilgi.get(k, []))
            alan_aci_sayisi[k] = len(detay_bilgi.get(k, []))
            alan_gezegenler[k] = set()
            for item in detay_bilgi.get(k, []):
                for g in ["Güneş","Ay","Merkür","Venüs","Mars","Jüpiter","Satürn","Uranüs","Neptün","Plüton"]:
                    if g in item:
                        alan_gezegenler[k].add(g)

        sirali_alanlar = sorted(alan_puanlari.items(), key=lambda x: x[1], reverse=True)

        # ─── MESLEK SEÇİMİ ───
        oneriler = []
        toplam_puan = sum(v for _, v in sirali_alanlar if v > 0)
        kullanilan_meslekler = set()

        for alan, puan in sirali_alanlar[:6]:
            if puan <= 0:
                continue
            if alan not in FBST_MESLEK_EBEVEYN:
                continue
            meslek_listesi = FBST_MESLEK_EBEVEYN[alan]
            yuzde = round((puan / toplam_puan) * 100) if toplam_puan > 0 else 0

            secilen_meslekler = []
            for m in meslek_listesi:
                if len(secilen_meslekler) >= 3:
                    break
                if m["meslek"] not in kullanilan_meslekler:
                    secilen_meslekler.append(m)
                    kullanilan_meslekler.add(m["meslek"])

            if secilen_meslekler:
                # Mesleklere kategori etiketlerini ve modern meslek etiketlerini ekle
                kategori_etiketleri = KATEGORI_ETIKETLERI.get(alan, [])
                for m in secilen_meslekler:
                    m["kategori_etiketleri"] = kategori_etiketleri
                    m["modern_etiketler"] = self._meslek_modern_etiketleri(m["meslek"], alan)
                oneri = {
                    "alan": alan,
                    "puan": puan,
                    "yuzde": yuzde,
                    "aci_sayisi": alan_aci_sayisi.get(alan, 0),
                    "aci_detaylari": alan_aci_detay.get(alan, ""),
                    "meslekler": secilen_meslekler,
                    "gezegenler": sorted(alan_gezegenler.get(alan, set())),
                }
                if mc_bilgisi:
                    oneri["mc_burc"] = mc_bilgisi.get("mc_burc", "")
                    oneri["mc_yonetici"] = mc_bilgisi.get("mc_yonetici", "")
                    yonetici_k = mc_bilgisi.get("yonetici_konum", {})
                    if yonetici_k:
                        oneri["mc_yonetici_konum"] = f"{yonetici_k.get('burc', '')} {yonetici_k.get('ev', '')}. Ev"
                ilgili_yildizlar = []
                for y in yildiz_bilgisi.get("tum_yildizlar", []):
                    if alan in y.get("meslek_etkileri", {}):
                        ilgili_yildizlar.append(f"{y['yildiz']} ({y.get('gezegen', 'MC')}, orb:{y['orb']}°)")
                if ilgili_yildizlar:
                    oneri["sabit_yildizlar"] = ilgili_yildizlar
                oneriler.append(oneri)

        return oneriler[:6]

    def _meslek_modern_etiketleri(self, meslek_adi: str, kategori: str) -> list:
        """
        Meslek adından modern teknoloji/dijital/yaratıcı etiketleri çıkarır.
        FBST_MESLEK_EBEVEYN'deki mesleklerin isimlerindeki anahtar kelimelerden çıkarım yapar.
        """
        etiketler = set()
        m = meslek_adi.lower()

        # Teknoloji / Yazılım / Dijital
        if any(k in m for k in ["yazılım", "kod", "program", "veri bil", "ai ", "yapay zeka", "sibir", "siber", "teknoloji", "dijital", "web", "mobil", "uygulama", "backend", "frontend", "fullstack", "devops", "cloud", "aws", "azure", "blockchain", "kripto", "teknoloji"]):
            etiketler.update(["Teknoloji", "Yazılım", "Dijital", "Modern"])

        # Bilim / Araştırma
        if any(k in m for k in ["araştır", "bilim", "akademik", "laboratuvar", "fizik", "kimya", "biyoloji", "genetik", "nöro", "matematik", "istatistik", "aktüer", "ekonomist", "analist"]):
            etiketler.update(["Bilimsel", "Araştırma", "Analitik", "Akademik"])

        # Tasarım / Yaratıcı / Görsel
        if any(k in m for k in ["tasarım", "grafik", "ux", "ui", "moda", "iç mekan", "endüstriyel", "animasyon", "vfx", "oyun tasar", "görsel", "illüstrat", "fotoğraf"]):
            etiketler.update(["Yaratıcı", "Tasarım", "Görsel", "Estetik"])

        # Medya / İçerik / İletişim
        if any(k in m for k in ["yazar", "içerik", "blog", "influencer", "youtuber", "podcast", "spiker", "sunucu", "gazeteci", "muhabir", "editör", "copywriter", "sosyal medya", "dijital medya", "halkla ilişkiler", "pr ", "marka"]):
            etiketler.update(["Medya", "İçerik", "İletişim", "Dijital Medya", "Yazarlık"])

        # Sağlık / Tıp / Bakım
        if any(k in m for k in ["doktor", "hemsire", "ebe", "fizyoterap", "rehabilitasyon", "diyetisyen", "beslenme", "psikolog", "terapist", "danışman", "koç", "psikoterapi", "cerrahi", "tıp", "sağlık", "ağr", "acil", "yoğun bakım", "ameliyat"]):
            etiketler.update(["Sağlık", "Bakım", "Tedavi", "İnsan Odaklı", "Bilimsel"])

        # Mühendislik / Teknik / Üretim
        if any(k in m for k in ["mühendis", "elektrik", "makine", "inşaat", "mekatronik", "otomasyon", "robotik", "elektronik", "teknisyen", "elektrikçi", "tesisatçı", "kaynakçı", "metal", "boyacı", "dekoratör", "terzi", "dikim", "fırıncı", "pastacı", "aşçı", "gastronomi"]):
            etiketler.update(["Teknik", "Mühendislik", "Üretim", "Uzmanlık", "El Becerisi"])

        # Eğitim / Öğretim
        if any(k in m for k in ["öğretmen", "eğitimci", "eğitim", "özel eğitim", "rehber", "akademi", "kurs", "eğitmen", "mentor"]):
            etiketler.update(["Eğitim", "Öğretim", "Mentorluk", "İnsan Odaklı"])

        # Finans / İş / Yönetim
        if any(k in m for k in ["finans", "yatırım", "portföy", "bankacılık", "sigorta", "aktüer", "risk", "yönetici", "ceo", "müdür", "kurucu", "girişimci", "satış", "pazarlama", "e-ticaret", "dijital pazarlama", "growth", "ticaret", "ihracat", "ithalat", "gayrimenkul", "franchise", "zincir"]):
            etiketler.update(["Finans", "İş Geliştirme", "Yönetim", "Stratejik", "Modern", "Pazarlama"])

        # Hukuk / Adalet / Kamu
        if any(k in m for k in ["avukat", "hakim", "savcı", "hukuk", "adalet", "mevzuat", "diplomat", "siyaset", "politik", "devlet", "kamu", "etk", "yasal"]):
            etiketler.update(["Yasal", "Kamu", "Düzenleme", "Etik", "Hakimiyet"])

        # Spor / Fiziksel
        if any(k in m for k in ["spor", "antrenör", "koç", "futbol", "basketbol", "tenis", "yüzme", "atletizm", "fitnes", "beden eğitimi", "spor bilim", "spor yönet"]):
            etiketler.update(["Spor", "Fiziksel", "Performans", "Antrenman", "Takım"])

        # Sanat / Edebiyat / Performans
        if any(k in m for k in ["müzisyen", "müzik", "besteci", "şarkıcı", "enstrüman", "ses", "sanatçı", "resim", "heykel", "oyuncu", "sahne", "dans", "tiyatro", "sinema", "film", "yönetmen", "yapımcı", "senarist", "şair", "edebiyat", "roman", "hikaye"]):
            etiketler.update(["Sanat", "Yaratıcı", "Performans", "Edebiyat", "Müzik", "Görsel"])

        # Manevi / Psikoloji / Danışmanlık
        if any(k in m for k in ["meditasyon", "yoga", "mindfulness", "şifa", "enerji", "reiki", "kristal", "şaman", "astrolog", "kader", "din", "ilahiyat", "manevi", "ruhani", "içsel çocuk", "rüya"]):
            etiketler.update(["Manevi", "Şifa", "Danışmanlık", "Ruh Sağlığı", "Koçluk"])

        # Güvenlik / Savunma / Askeri
        if any(k in m for k in ["asker", "komutan", "emniyet", "polis", "güvenlik", "istihbarat", "kriz", "acil durum", "savunma"]):
            etiketler.update(["Güvenlik", "Strateji", "Disiplin", "Koruma", "Liderlik"])

        # Zanaat / Ustalık
        if any(k in m for k in ["kuaför", "berber", "güzellik", "marangoz", "ahşap", "mobilya", "kuyumcu", "saatçi", "taş", "maden", "kuyumculuk"]):
            etiketler.update(["Zanaat", "El Becerisi", "Estetik", "Üretim", "Uzmanlık"])

        return sorted(list(etiketler))

    def gezegen_konum_analizi(self):
        if hasattr(self, '_gezegen_konum_cache'):
            return self._gezegen_konum_cache
        """
        Çocuğun natal haritasındaki her gezegenin burcunu, elementini ve evini döndürür.
        Meslek yönlendirmesinde kişiye özel yorum üretmek için kullanılır.
        """
        try:
            if self.mod == "ebeveyn_cocuk":
                d1 = self.event_date.date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            else:
                d1 = self.p1 if isinstance(self.p1, date) else datetime.strptime(str(self.p1), "%Y-%m-%d").date()
                dogum_saat_utc = self.saat_ondalik - self._get_utc_offset(d1.year, d1.month, d1.day)
            j1 = swe.julday(d1.year, d1.month, d1.day, dogum_saat_utc)
        except Exception:
            self._gezegen_konum_cache = {}
            return self._gezegen_konum_cache

        gezegen_id = {
            "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS,
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN, "Uranüs": swe.URANUS,
            "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO, "KAD": swe.MEAN_NODE, "Chiron": 15
        }

        burc_element = {
            "Koç": "Ateş", "Aslan": "Ateş", "Yay": "Ateş",
            "Boğa": "Toprak", "Başak": "Toprak", "Oğlak": "Toprak",
            "İkizler": "Hava", "Terazi": "Hava", "Kova": "Hava",
            "Yengeç": "Su", "Akrep": "Su", "Balık": "Su",
        }

        burc_nitelig = {
            "Koç": "başlangıç, cesaret, eylem", "Boğa": "istikrar, değer, sabır",
            "İkizler": "iletişim, merak, çok yönlülük", "Yengeç": "duygu, koruma, aile",
            "Aslan": "yaratıcılık, liderlik, sahne", "Başak": "detay, analiz, hizmet",
            "Terazi": "denge, estetik, ilişki", "Akrep": "dönüşüm, derinlik, güç",
            "Yay": "özgürlük, felsefe, macera", "Oğlak": "yapı, sorumluluk, kariyer",
            "Kova": "yenilik, topluluk, vizyon", "Balık": "sezgi, merhamet, hayal gücü",
        }

        ev_anlamlari = {
            1: "benlik, görünüm, başlangıç", 2: "değer, para, yetenek",
            3: "iletişim, kardeşler, öğrenme", 4: "yuva, kök, aile",
            5: "yaratıcılık, çocuk, eğlence", 6: "sağlık, iş, hizmet",
            7: "ilişki, ortaklık, evlilik", 8: "dönüşüm, kriz, paylaşılan kaynaklar",
            9: "felsefe, yüksek eğitim, seyahat", 10: "kariyer, toplumsal statü, miras",
            11: "arkadaşlık, gruplar, vizyon", 12: "bilinçaltı, yalnızlık, ruhsallık",
        }

        sonuc = {}
        for isim, pid in gezegen_id.items():
            try:
                ham_derece = get_planetary_position(j1, pid)
                burc = dereceyi_burca_cevir(ham_derece)
                derece_burc_icinde = ham_derece - (int(ham_derece / 30) % 12) * 30
                tam_derece = int(derece_burc_icinde)
                dakika = int((derece_burc_icinde - tam_derece) * 60)
                element = burc_element.get(burc, "Bilinmiyor")
                ev = self.ev_konumu_bul(j1, pid)
                nitelik = burc_nitelig.get(burc, "")
                ev_anlam = ev_anlamlari.get(ev, "")
                sonuc[isim] = {
                    "burc": burc, "element": element, "ev": ev,
                    "nitelik": nitelik, "ev_anlam": ev_anlam,
                    "ham_derece": ham_derece, "derece": tam_derece, "dakika": dakika,
                }
            except Exception:
                continue
        self._gezegen_konum_cache = sonuc
        return self._gezegen_konum_cache

    def element_dengesi_hesapla(self, gezegenler_listesi, konumlar):
        """
        Verilen gezegen listesinin element dengesini hesaplar.
        Baskın elementi ve yüzdelerini döndürür.
        """
        element_sayac = {"Ateş": 0, "Toprak": 0, "Hava": 0, "Su": 0}
        for g in gezegenler_listesi:
            if g in konumlar:
                el = konumlar[g]["element"]
                element_sayac[el] = element_sayac.get(el, 0) + 1

        toplam = sum(element_sayac.values())
        if toplam == 0:
            return {"Ateş": 25, "Toprak": 25, "Hava": 25, "Su": 25}, "Dengeli"

        yuzdeler = {el: round((sayi / toplam) * 100) for el, sayi in element_sayac.items()}

        sirali = sorted(yuzdeler.items(), key=lambda x: x[1], reverse=True)
        baskin = sirali[0][0]
        if sirali[0][1] == sirali[1][1]:
            baskin = f"{sirali[0][0]}-{sirali[1][0]}"

        return yuzdeler, baskin

    def meslek_kisisel_yorum(self, alan, gezegenler_listesi, konumlar):
        """
        Açı yapan gezegenlerin burç, ev ve element bilgisinden kişiye özel meslek yorumu üretir.
        """
        if not konumlar:
            return ""

        detaylar = []
        for g in gezegenler_listesi:
            if g in konumlar:
                k = konumlar[g]
                detaylar.append(f"{g} {k['burc']} ({k['element']}, {k['ev']}. Ev)")

        yuzdeler, baskin_element = self.element_dengesi_hesapla(gezegenler_listesi, konumlar)

        element_meslekleri = {
            "Ateş": "yaratıcı, enerjik ve eylem odaklı",
            "Toprak": "pratik, somut ve sonuç odaklı",
            "Hava": "iletişim, düşünce ve entelektüel",
            "Su": "duygusal, sezgisel ve şifalayıcı",
        }

        baskin_aciklama = element_meslekleri.get(baskin_element, "çok yönlü ve dengeli")

        evler = [konumlar[g]["ev"] for g in gezegenler_listesi if g in konumlar]
        kariyer_evleri = [e for e in evler if e in [1, 2, 5, 6, 10]]
        ev_notu = ""
        if 10 in evler:
            ev_notu = "10. evdeki gezegen güçlü bir kariyer potansiyeline işaret eder."
        elif 6 in evler:
            ev_notu = "6. evdeki gezegen hizmet ve detay odaklı bir kariyere yatkınlık gösterir."
        elif 2 in evler:
            ev_notu = "2. evdeki gezegen maddi değerler ve somut yeteneklere güçlü bir bağlının olduğunu gösterir."
        elif 1 in evler:
            ev_notu = "1. evdeki gezegen bireysel kimliğin ve girişimcilik ruhunun güçlü olduğunu gösterir."
        elif 5 in evler:
            ev_notu = "5. evdeki gezegen yaratıcılık ve kendini ifade etme potansiyeline güçlü bir bağlının olduğunu gösterir."

        ozet = "Gezegenler: " + ", ".join(detaylar) + ". "
        ozet += f"Baskın element: {baskin_element} ({baskin_aciklama}). "
        if ev_notu:
            ozet += ev_notu

        return ozet

    def karmik_ev_aktarimlari(self, pdf_icin=False):
        j_ileri, j_geri = self.get_julian_dates()
        
        if self.mod == "ebeveyn_cocuk":
            ev_muhurleri = {
                "Güneş": {1: "Kimlik ve Benlik Gelişimi: Bu yıl çocuğun kendi kimliğini keşfetme süreci hızlanır. Ebeveyn olarak onun bireysel duruşunu desteklemek, kendi benliğini güçlü bir şekilde ortaya koymasına rehberlik eder.", 5: "Yaratıcılık ve Kendini İfade: Çocuğun sanatsal veya yaratıcı potansiyeli bu evde parlar. Ebeveynin bu enerjiyi beslemesi, çocuğun kendini güvenle ifade etmesinin anahtarıdır.", 7: "İlişki ve Karşılıklı Saygı: Ebeveyn-çocuk arasındaki denge ve karşılıklı saygı bu dönemde test edilir. İkisi de kendi ihtiyaçlarını ifade ederken 'birlikte var olmanın' dersini öğrenir."},
                "Ay": {4: "Yuva ve Güvenli Liman: Çocuğun duygusal kökleri bu dönemde derinleşir. Ebeveynin yarattığı güvenli atmosfer, çocuğun duygusal dayanıklılığının temelini atar.", 8: "Duygusal Dönüşüm: Çocuğun iç dünyasında yoğun değişimler yaşanır. Ebeveynin sabırlı ve anlayışlı tavrı, bu dönüşüm sürecinin sağlıklı ilerlemesini sağlar."},
                "Jüpiter": {2: "Değer ve Özgüven İnşası: Çocuğun kendine olan güveni ve yeteneklerinin farkındalığı bu dönemde artar. Ebeveynin takdiri ve desteği bu sürecin en değerli gübresidir.", 8: "Ortak Öğrenme ve Paylaşım: Ebeveyn ve çocuk birlikte derinlemesine öğrenme deneyimleri yaşar. Birlikte kitap okumak, belgesel izlemek veya yeni bir beceri öğrenmek ruhsal bağı güçlendirir.", 10: "Başarı ve Tanınma: Çocuğun okul veya sosyal alanlardaki başarıları göz doldurur. Ebeveynin gururunu paylaşması ve destek mesajları göndermesi çocuğun motivasyonunu katlar."},
                "Satürn": {4: "Ailevi Sorumluluk ve Yapı: Aile içi kurallar ve sınırlar bu dönemde belirginleşir. Çocuğun disiplin ihtiyacını anlayarak yapı kurmak, uzun vadeli güven inşasının temelidir.", 7: "Karşılıklı Sorumluluk: Ebeveyn ve çocuk birbirlerine karşı sorumluluklarının farkına varır. Bu, karşılıklı güven ve taahhüt dersinin en yoğun yaşandığı dönemdir."},
                "Plüton": {1: "Kimlik Dönüşümü: Çocuğun benlik algısı köklü bir şekilde yeniden şekillenir. Ebeveynin bu dönüşüme müdahale etmeden desteklemesi, çocuğun kendi güç merkezini bulmasını sağlar.", 8: "Derinlenen Bağ ve Paylaşım: Ebeveyn ve çocuk arasında daha önce konuşulmamış konuların yüzeye çıktığı bir dönem. Duygusal derinleşme, karşılıklı güvenin en güçlü testini oluşturur."},
                "Venüs": {5: "Sevgi ve Takdir Dilinin Öğrenilmesi: Birbirinize olan sevginizi ifade etmenin en güzel yollarını keşfedeceğiniz pedagojik bir dönem. Takdir, minnet ve şefkat pratiği yapın.", 7: "Denge ve Uyum Dersi: Ebeveyn-çocuk ilişkisinde dengeyi bulmak, her iki tarafın da ihtiyaçlarını karşılıklı olarak tanımak bu dönemin en değerli kazanımıdır."},
                "Mars": {1: "Eylem ve Cesaret Eğitimi: Çocuğun bağımsız hareket etme arzusu artar. Ebeveynin güvenli sınırlar içinde cesaretlendirmesi, çocuğun kendi güç ve cesaret kaynaklarını keşfetmesini sağlar.", 10: "Hedef Belirleme ve Kararlılık: Çocuğun akademik veya kişisel hedeflerine yönelik kararlılığı artar. Ebeveynin bu hedeflere yönelik yapısal desteği, çocuğun motivasyonunu besler."},
                "Chiron": {4: "Ailevi Yaraların Şifası: Geçmiş nesillerden gelen duygusal yaralar bu dönemde şifalanmaya açılır. Ebeveynin kendi yaralarıyla yüzleşmesi, çocuğa en güçlü şifa modelini sunar.", 12: "Bilinçaltı Şifası: Çocuğun bilinçaltındaki korkular ve endişeler bu dönemde yüzeye çıkabilir. Ebeveynin sabırlı ve anlayışlı yaklaşımı, bu sürecin şifaya dönüşmesinin anahtarıdır."}
            }
        else:
            ev_muhurleri = {
                "Güneş": {1: "Kimlik ve Benlik: Bu vektördeki kişi, diğerinin kimliğini ve benlik algısını güçlendirir. İkiniz de birbirinizin 'ben kimim?' sorusuna cevap bulmasına yardımcı olursunuz. Hayata karşı duruşunuz, birbirinizin öz-güvenini parlatır.", 5: "Yaratıcı Birleşme: Birlikte bir eser ortaya koyma, bir çocuk büyütme ya da büyük bir hayali gerçekleştirme kadersel göreviniz. Yaratıcılığınız birleştiğinde ortaya çıkan enerji, çevrenizdeki herkesi etkiler.", 7: "Kader Kontratı: 'Biz' olmanın en somut hali — bu evde resmiyet, taahhüt ve uzun vadeli bir ittifak kurulur. Eş seçimindeki kadersel tercihiniz burada mühürlenir."},
                "Ay": {4: "Yuva ve Köklenme: Ruhun en sıcak, en güvenli sığınağı bu vektörde inşa edilir. Birlikte kuracağınız yuva, yalnızca bir ev değil, aynı zamanda duygusal olarak besleyen bir limandır.", 8: "Duygusal Yeraltı: Bu evde psikolojik derinlikler, bilinçaltı korkular ve bastırılmış duygular yüzeye çıkar. Birbirinizin en karanlık sırlarını bile kabul edebilmeniz, ilişkinin en güçlü şifa alanıdır."},
                "Jüpiter": {2: "Bereket Kapısı: Bu vektördeki kişi, diğerinin maddi ve manevi bolluğunu doğrudan artırır. Birlikte yatırımlar, ortak gelir kaynakları ya da büyük finansal sıçramalar yaşanabilir.", 8: "Ortak Zenginleşme: Eşin mirası, ortak bir iş ya da birlikte yapılacak bir yatırım kadersel bir büyüme getirir. Birlikte öğrendiğiniz her şey, ruhsal zenginliğinizi katlar.", 10: "Toplumsal Yükseliş: İkisi birlikte toplumda saygı gören, ilham veren bir çift olur. Kariyerdeki başarınız, birbirinizi desteklemenin meyvesidir."},
                "Satürn": {4: "Ailevi Yapı Sınavı: Yuva kurmak, aile olmak bu vektörde ciddi bir sınav gerektirir. Sorumluluklar ağır olabilir ama bu sınav, sağlam bir temel atmanızı sağlar.", 7: "Karmik Evlilik: Bu ilişki resmiyet, evlilik ve uzun vadeli taahhüt için kozmik olarak onaylanmıştır. Zorluklar olsa da, bu birliktelik zamanla çok daha güçlü bir hal alır."},
                "Plüton": {1: "Kimlik Yeniden Doğuşu: Bu kişi, partnerinin eski benliğini tamamen yıkarak daha güçlü, daha oturmuş bir kimlik yaratmasına yardımcı olur. Bu dönüşüm acı verici ama özgürleştiricidir.", 8: "Küllerinden Yükseliş: En derin krizlerin, psikolojik çöküşlerin ardından gelen büyük uyanış ve yeniden doğuş budur. Birbirinizin en karanlık anında bile yan yana durmak, bu ilişkinin en kutsal pratiğidir."},
                "Venüs": {5: "Tutkulu Aşk: Aşk, flört, cinsellik ve yaşamdan alınan keyif bu ilişkinin kalbinde atar. Birlikte geçirdiğiniz her an, sevgiyle bezeli bir sanat eserine dönüşür.", 7: "Kaderin Hediyesi: Uyum, estetik ve sevgi dilinde tam bir uyum — gökyüzünün bu birlikteliğe verdiği en değerli armağan. Evlilik ya da resmi birleşme için en ideal enerji."},
                "Mars": {1: "Savaşçı Ruh: Bu kişi, diğerine inanılmaz bir eylem gücü, cesaret ve mücadele azmi aşılar. Birlikte hayata karşı savaşırken, birbirinizin en güçlü destekçisi olursunuz.", 10: "Zirve Yolculuğu: Kariyerde, hedeflerde ve toplumsal alanda birlikte engelleri aşma potansiyeliniz çok yüksek. İhtiras ve kararlılık birleştiğinde, ulaşamayacakları zirve yoktur."},
                "Chiron": {4: "Ailevi Şifa: Geçmiş nesillerden, aile köklerinden gelen yaralar bu vektörde yüzeye çıkıp şifalanmayı bekler. Birbirinizin yaralarını anlamanız ve onarmanız, nesiller arası şifanın kapısını aralar.", 12: "Bilinçaltı Şifacısı: Mantıkla çözülemeyen, kelimelere dökülemeyen ruhsal sızılar, bu birlikteliğin varlığıyla gizlice iyileşir. Sessiz bir dokunuş bile bin yıllık bir yarayı sarabilir."}
            }
        
        rapor_A = []
        rapor_B = []
        
        for gezegen, ev_detaylari in ev_muhurleri.items():
            gid = GEZEGENLER[gezegen]
            
            ev_A = self.ev_konumu_bul(j_ileri, gid)
            if ev_A in ev_detaylari:
                if pdf_icin:
                    rapor_A.append(f"<font name='DejaVuSans-Bold'>{gezegen} {ev_A}. Evde:</font> {ev_detaylari[ev_A]}")
                else:
                    if self.mod == "ebeveyn_cocuk":
                        rapor_A.append(f"<div style='background-color:#FBF7F4; padding:10px; border-left:3px solid #8FB8CA; margin-bottom:5px;'><font color='#5A9BAD'><b>{gezegen} {ev_A}. Evde:</b></font> <font color='#4A4A4A'>{ev_detaylari[ev_A]}</font></div>")
                    else:
                        rapor_A.append(f"<div style='background-color:#FBF7F4; padding:10px; border-left:3px solid #8FB8CA; margin-bottom:5px;'><font color='#5A9BAD'><b>{gezegen} {ev_A}. Evde:</b></font> <font color='#4A4A4A'>{ev_detaylari[ev_A]}</font></div>")
                    
            ev_B = self.ev_konumu_bul(j_geri, gid)
            if ev_B in ev_detaylari:
                if pdf_icin:
                    rapor_B.append(f"<font name='DejaVuSans-Bold'>{gezegen} {ev_B}. Evde:</font> {ev_detaylari[ev_B]}")
                else:
                    if self.mod == "ebeveyn_cocuk":
                        rapor_B.append(f"<div style='background-color:#FBF7F4; padding:10px; border-left:3px solid #C9A96E; margin-bottom:5px;'><font color='#C9A96E'><b>{gezegen} {ev_B}. Evde:</b></font> <font color='#4A4A4A'>{ev_detaylari[ev_B]}</font></div>")
                    else:
                        rapor_B.append(f"<div style='background-color:#FBF7F4; padding:10px; border-left:3px solid #D4878F; margin-bottom:5px;'><font color='#D4878F'><b>{gezegen} {ev_B}. Evde:</b></font> <font color='#4A4A4A'>{ev_detaylari[ev_B]}</font></div>")
                    
        return rapor_A, rapor_B

    def fbst_analizi_yap(self, sessiz=False): 
        self.haritalari_ciz()

    def haritalari_ciz(self):
        # natal/potansiyel modunda: gerçek natal harita (doğum tarihi Julian günü)
        if self.mod in ("potansiyel_yetenek", "bireysel_natal"):
            j_natal = self.get_natal_julian_day("p1")
            j_ileri = j_natal
            j_geri = j_natal
            self._j_ileri = j_natal
            self._j_geri = j_natal
        else:
            j_ileri, j_geri = self.get_julian_dates()
        
        # --- GEZEGEN SEMBOLLERİ VE RENK KÜTÜPHANESİ (TERAZİ TESİSİ) ---
        gezegen_stilleri = {
            "Güneş": ("☉", "#C9A96E"), "Ay": ("☽", "#8A7F96"), "Merkür": ("☿", "#8FB8CA"),
            "Venüs": ("♀", "#D4878F"), "Mars": ("♂", "#C47A82"), "Jüpiter": ("♃", "#C9A96E"),
            "Satürn": ("♄", "#6B5B7B"), "Uranüs": ("♅", "#8FB8CA"), "Neptün": ("♆", "#B8A9C9"),
            "Plüton": ("♇", "#7A6B8A"), "Lilith": ("⚸", "#8A7F96"), "Chiron": ("⚷", "#8FB8CA"),
            "Juno": ("⚵", "#D4878F"), "Ceres": ("⚳", "#8FB8CA"), "Pallas": ("⚴", "#B8A9C9"),
            "Vesta": ("⚶", "#8FB8CA"), "KAD": ("☊", "#C9A96E"), "GAD": ("☋", "#D4878F")
        }

        BURC_SEMBOLLERI = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
        BURC_ISIMLERI = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
                         "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
        BURC_RENKLERI = {
            "ateş": "#D4878F", "toprak": "#8FB8CA", "hava": "#B8A9C9", "su": "#C9A96E"
        }
        BURC_ELEMENT = {0: "ateş", 1: "toprak", 2: "hava", 3: "su",
                        4: "ateş", 5: "toprak", 6: "hava", 7: "su",
                        8: "ateş", 9: "toprak", 10: "hava", 11: "su"}

        def ciz(j_gun, dosya_adi, baslik):
            if os.path.exists(dosya_adi):
                return
            konumlar = {}
            for isim, gid in GEZEGENLER.items():
                try: 
                    flags = get_safe_flags(gid)
                    konumlar[isim] = swe.calc_ut(j_gun, gid, flags)[0][0]
                except Exception:
                    tahmini = asteroit_tahmini_derece(isim, j_gun)
                    if tahmini is not None:
                        konumlar[isim] = tahmini
            
            asc_derece = 0
            cusps = []
            ascmc = [0, 0, 0, 0]
            try:
                cusps, ascmc = swe.houses(j_gun, self.enlem, self.boylam, b'P')
                asc_derece = ascmc[0]
                konumlar["ASC"] = asc_derece
                konumlar["MC"] = ascmc[1]
            except Exception:
                pass

            def dondur(derece):
                return (derece - asc_derece + 180) % 360

            plt = _plt()
            fig = plt.figure(figsize=(8, 8))
            fig.patch.set_facecolor('#FFFFFF')
            ax = fig.add_subplot(111, projection='polar')
            ax.set_facecolor('#FBF7F4')
            ax.set_theta_zero_location("E")
            ax.set_theta_direction(1)
            ax.set_yticklabels([])
            ax.set_xticklabels([])
            ax.grid(False)
            for spine in ax.spines.values():
                spine.set_visible(False)

            # ── 1) ZODYAK HALKASI: 12 burç segmenti ──
            r_ic, r_dis = 0.72, 0.92
            for i in range(12):
                t_bas = np.deg2rad(dondur(i * 30))
                t_bit = np.deg2rad(dondur((i + 1) * 30))
                element = BURC_ELEMENT[i]
                renk = BURC_RENKLERI[element]
                theta = np.linspace(t_bas, t_bit, 50)
                ax.fill_between(theta, r_ic, r_dis, color=renk, alpha=0.18, linewidth=0)
                ax.plot([t_bas, t_bas], [r_ic, r_dis], color='#E8E0D8', linewidth=0.6, alpha=0.7)
                t_orta = np.deg2rad(dondur(i * 30 + 15))
                ax.text(t_orta, (r_ic + r_dis) / 2, BURC_SEMBOLLERI[i],
                        ha='center', va='center', fontsize=13, color=renk, alpha=0.8, zorder=3)
                t_isim = np.deg2rad(dondur(i * 30 + 15))
                ax.text(t_isim, r_dis + 0.035, BURC_ISIMLERI[i],
                        ha='center', va='center', fontsize=5.5, color='#6B5B7B', alpha=0.7, zorder=3)

            # ── 2) DIŞ ÇEMBER ──
            t_tam = np.linspace(0, 2 * np.pi, 360)
            ax.plot(t_tam, [r_dis] * 360, color='#C9A96E', linewidth=1.5, alpha=0.6)
            ax.plot(t_tam, [r_ic] * 360, color='#E8E0D8', linewidth=0.8, alpha=0.6)

            # ── 3) EV CİZGİLERİ VE DERECE ETİKETLERİ ──
            ev_renkleri = ['#C9A96E', '#8A7F96', '#8FB8CA', '#D4878F', '#B8A9C9',
                           '#C47A82', '#6B5B7B', '#7A6B8A', '#8FB8CA', '#C9A96E',
                           '#D4878F', '#B8A9C9']
            burclar_kisa = ["Koc", "Boga", "Iki", "Yen", "Asl", "Bas",
                            "Ter", "Akr", "Yay", "Ogl", "Kov", "Bal"]
            if len(cusps) >= 12:
                for idx in range(12):
                    cusp_derece = cusps[idx]
                    t_cusp = np.deg2rad(dondur(cusp_derece))
                    ax.plot([t_cusp, t_cusp], [0.18, r_ic], color=ev_renkleri[idx],
                            linewidth=0.7, alpha=0.5, linestyle='--', zorder=2)
                    burc_idx = int(cusp_derece / 30) % 12
                    burc_ic_derece = cusp_derece - burc_idx * 30
                    tam_d = int(burc_ic_derece)
                    dak_d = int((burc_ic_derece - tam_d) * 60)
                    etiket = f"{idx+1}: {tam_d}°{dak_d:02d}'{burclar_kisa[burc_idx]}"
                    t_etiket = np.deg2rad(dondur(cusp_derece))
                    ax.text(t_etiket, r_dis + 0.075, etiket,
                            ha='center', va='center', fontsize=4.5,
                            color=ev_renkleri[idx], alpha=0.85, zorder=4,
                            rotation=np.deg2rad(dondur(cusp_derece)) - np.pi/2,
                            rotation_mode='anchor')

            # ── 4) GEZEGEN POZİSYONLARI (çakışma önlemeli) ──
            yazilar = []
            sirali_gezegenler = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter",
                                "Satürn", "Uranüs", "Neptün", "Plüton", "KAD", "Chiron",
                                "Lilith", "Juno", "Ceres", "Pallas", "Vesta"]
            sirali_gezegenler = [g for g in sirali_gezegenler if g in konumlar]

            # Grupla: aynı dereceye yakın gezegenleri tespit et
            RADIUS_BASE = 0.52
            RADIUS_NAME = 0.42
            RADIUS_STEP = 0.055
            ANGLE_GAP = 10  # derece cinsinden minimum açı

            pozisyonlar = {}
            for g in sirali_gezegenler:
                pozisyonlar[g] = konumlar[g]

            # Gezegenleri dereceye göre sırala
            sirali_isimler = sorted(sirali_gezegenler, key=lambda g: pozisyonlar[g])

            # Grupları bul
            gruplar = []
            aktif = []
            for g in sirali_isimler:
                if not aktif:
                    aktif = [g]
                else:
                    son_derece = pozisyonlar[aktif[-1]]
                    simdi_derece = pozisyonlar[g]
                    if abs(simdi_derece - son_derece) < ANGLE_GAP or abs(simdi_derece - son_derece - 360) < ANGLE_GAP:
                        aktif.append(g)
                    else:
                        gruplar.append(aktif)
                        aktif = [g]
            if aktif:
                gruplar.append(aktif)

            her_gezegen_r = {}
            for grup in gruplar:
                for i, g in enumerate(grup):
                    offset = (i - (len(grup)-1)/2) * RADIUS_STEP if len(grup) > 1 else 0
                    her_gezegen_r[g] = (RADIUS_BASE + offset, RADIUS_NAME + offset)

            for gezegen in sirali_gezegenler:
                derece = pozisyonlar[gezegen]
                gorsel_derece = dondur(derece)
                radyan = np.deg2rad(gorsel_derece)
                sembol, renk = gezegen_stilleri.get(gezegen, ("•", "#8A7F96"))
                r_planet, r_name = her_gezegen_r[gezegen]

                ax.plot(radyan, r_planet, 'o', color=renk, markersize=16, zorder=4)
                ax.plot(radyan, r_planet, 'o', color='#FFFFFF', markersize=12, zorder=5)
                txt1 = ax.text(radyan, r_planet, sembol, color=renk, fontsize=13,
                               ha='center', va='center', zorder=6)
                yazilar.append(txt1)

                burc_idx = int(derece / 30) % 12
                txt2 = ax.text(radyan, r_name, gezegen, color='#6B5B7B', fontsize=5.5,
                               ha='center', va='center', zorder=6)
                yazilar.append(txt2)

            # ── 5) ASC VE MC ──
            for nokta, sembol, renk, isim in [
                ("ASC", "⬆", "#D4878F", "ASC"),
                ("MC", "▼", "#C9A96E", "MC")
            ]:
                if nokta in konumlar:
                    t = np.deg2rad(dondur(konumlar[nokta]))
                    ax.plot(t, 0.95, 'D', color=renk, markersize=10, zorder=7)
                    ax.plot(t, 0.95, 'D', color='#FFFFFF', markersize=6, zorder=8)
                    burc_idx = int(konumlar[nokta] / 30) % 12
                    burc_ic = konumlar[nokta] - burc_idx * 30
                    tam_d = int(burc_ic)
                    dak_d = int((burc_ic - tam_d) * 60)
                    label = f"{isim} {tam_d}°{dak_d:02d}'{BURC_ISIMLERI[burc_idx]}"
                    txt = ax.text(t, 1.02, label, color=renk, fontsize=7.5,
                                  ha='center', va='center', weight='bold', zorder=9)
                    yazilar.append(txt)

            plt.title(baslik, color='#3D2E50', fontsize=13, pad=25, weight='bold', fontfamily='serif')
            ax.set_ylim(0, 1.18)

            plt.tight_layout()
            plt.savefig(dosya_adi, facecolor=fig.get_facecolor(), dpi=300)
            svg_adi = dosya_adi.replace('.png', '.svg')
            if svg_adi != dosya_adi:
                plt.savefig(svg_adi, facecolor=fig.get_facecolor(), format='svg')
            plt.close(fig)
            
        ciz(j_ileri, f"{self._session_id}_Situa_A.png", f"{self.p1_isim} Haritası")
        if self.mod == "potansiyel_yetenek":
            ciz(j_geri, f"{self._session_id}_Situa_B.png", f"{self.p2_isim} Natal Haritası")
        else:
            ciz(j_geri, f"{self._session_id}_Situa_B.png", f"SİTUA B: {self.p2_isim} Vektör Haritası")

    def ciz_titresim_grafigi(self, dosya_adi=None):
        if dosya_adi is None:
            dosya_adi = f"{self._session_id}_Frekans.png"
        t = np.linspace(0, 21.5, 1000)
        ks_yil = self.calculate_ks()
        faz = ks_yil % (2 * np.pi)
        
        y_akis = np.sin(1.5 * t + faz) 
        y_kriz = -np.cos(2.5 * t + faz/2) 
        y_toplam = y_akis + y_kriz
        
        plt = _plt()
        fig, ax = plt.subplots(figsize=(12, 4))
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#FBF7F4')
        
        ax.plot(t, y_akis, color='#8FB8CA', linewidth=1, linestyle='--', alpha=0.5, label="Ruhsal Akış (Sinüs)")
        ax.plot(t, y_kriz, color='#D4878F', linewidth=1, linestyle='--', alpha=0.5, label="Kriz ve Blokaj (Kosinüs)")
        ax.plot(t, y_toplam, color='#B8A9C9', linewidth=2.0, label="Ana Kadersel Vektör")
        
        ax.fill_between(t, y_toplam, 0, where=(y_toplam > 0), color='#B8A9C9', alpha=0.12)
        ax.fill_between(t, y_toplam, 0, where=(y_toplam < 0), color='#D4878F', alpha=0.12)
        
        donemecler = {
            1.375: ("Uyanış", "#C9A96E"), 
            2.225: ("Fraktal", "#C9A96E"), 
            2.4: ("İlişki Krizi", "#D4878F"), 
            4.0: ("Uyum", "#8FB8CA"), 
            7.0: ("1. Satürn", "#C47A82"),
            14.0: ("2. Satürn", "#C47A82"),
            21.0: ("Büyük Hasat", "#8FB8CA")
        }
        
        for yil, (isim, renk) in donemecler.items():
            y_val = np.sin(1.5 * yil + faz) - np.cos(2.5 * yil + faz/2)
            ax.plot(yil, y_val, marker='o', markersize=7, color=renk, markeredgecolor='#FFFFFF', markeredgewidth=1.5, zorder=5)
            ax.annotate(f"{yil} Y.\n{isim}", (yil, y_val), textcoords="offset points", xytext=(0,15), ha='center', fontsize=7.5, color='#4A4A4A', weight='bold')

        ax.axhline(0, color='#C9A96E', linewidth=0.8, linestyle='-', alpha=0.5)
        ax.set_title("FAST Uzun Vadeli Frekans ve 21 Yıllık Ritim", color='#3D2E50', fontsize=13, pad=20, weight='bold')
        ax.set_xlabel("İlişkinin Yaşı (Yıl)", color='#6B5B7B', fontsize=10)
        ax.set_ylabel("Ödül (Zirve) / Kriz (Dip)", color='#6B5B7B', fontsize=10)
        
        ax.set_xticks(np.arange(0, 22, 3))
        ax.tick_params(colors='#6B5B7B')
        ax.legend(loc="upper right", facecolor='#FFFFFF', edgecolor='#E8E0D8', labelcolor='#4A4A4A', fontsize=8)
        
        for spine in ax.spines.values():
            spine.set_color('#E8E0D8')
            spine.set_linewidth(0.5)
            
        plt.tight_layout()
        plt.savefig(dosya_adi, facecolor=fig.get_facecolor(), dpi=300)
        svg_adi = dosya_adi.replace('.png', '.svg')
        if svg_adi != dosya_adi:
            plt.savefig(svg_adi, facecolor=fig.get_facecolor(), format='svg')
        plt.close(fig)
        return dosya_adi

    # ==========================================================================
    # ASTROCARTOGRAPHY: SWISS EPH İLE SIFIRDAN HESAPLAMA + PLOTLY GLOBE
    # ==========================================================================
    def _astrocartography_cizgileri_hesapla(self, julian_day):
        """
        Her gezegen için MC/IC/ASC/DSC çizgi koordinatlarını hesaplar.
        MC/IC: Her enlem için boylam taraması
        ASC/DSC: Her enlem için boylam taraması
        """
        import math

        gezegen_renkleri = {
            "Güneş": "#C9A96E", "Ay": "#8A7F96", "Merkür": "#8FB8CA",
            "Venüs": "#D4878F", "Mars": "#C47A82", "Jüpiter": "#C9A96E",
            "Satürn": "#6B5B7B", "Uranüs": "#8FB8CA", "Neptün": "#B8A9C9",
            "Plüton": "#7A6B8A"
        }

        secili_gezegenler = ["Güneş", "Ay", "Merkür", "Venüs", "Mars",
                             "Jüpiter", "Satürn", "Uranüs", "Neptün", "Plüton"]

        sonuc = {}
        TOLERANS = 2.0  # derece

        for gezegen_adi in secili_gezegenler:
            gid = GEZEGENLER.get(gezegen_adi)
            if gid is None or gid == 999:
                continue

            try:
                coords, _ = swe.calc_ut(julian_day, gid)
                gezegen_derece = coords[0]
            except Exception:
                continue

            renk = gezegen_renkleri.get(gezegen_adi, "#FFFFFF")

            # MC/IC çizgisi: Her enlem için, gezegenin MC'de olduğu boylamı bul
            mc_ic_coords = []
            for lat in range(-70, 71, 4):
                for lon_step in range(-180, 181, 3):
                    try:
                        step_jd = swe.julday(
                            self.event_date.year, self.event_date.month,
                            self.event_date.day, 12.0 + lon_step / 15.0
                        )
                        _, ascmc = swe.houses(step_jd, lat, lon_step, b'P')
                        mc_derece = ascmc[0]
                        fark_mc = abs(gezegen_derece - mc_derece)
                        if fark_mc > 180:
                            fark_mc = 360 - fark_mc
                        if fark_mc <= TOLERANS:
                            mc_ic_coords.append((lon_step, lat))
                            break
                    except Exception:
                        pass

            # ASC/DSC çizgisi: Her enlem için, gezegenin ASC'de olduğu boylamı bul
            asc_coords = []
            dsc_coords = []
            for lat in range(-70, 71, 4):
                for lon_step in range(-180, 181, 3):
                    try:
                        step_jd = swe.julday(
                            self.event_date.year, self.event_date.month,
                            self.event_date.day, 12.0 + lon_step / 15.0
                        )
                        _, ascmc = swe.houses(step_jd, lat, lon_step, b'P')
                        asc_derece = ascmc[0]
                        dsc_derece = (asc_derece + 180) % 360

                        fark_asc = abs(gezegen_derece - asc_derece)
                        if fark_asc > 180:
                            fark_asc = 360 - fark_asc
                        if fark_asc <= TOLERANS:
                            asc_coords.append((lon_step, lat))
                            break

                        fark_dsc = abs(gezegen_derece - dsc_derece)
                        if fark_dsc > 180:
                            fark_dsc = 360 - fark_dsc
                        if fark_dsc <= TOLERANS:
                            dsc_coords.append((lon_step, lat))
                            break
                    except Exception:
                        pass

            sonuc[gezegen_adi] = {
                "renk": renk,
                "mc_ic": mc_ic_coords,
                "asc": asc_coords,
                "dsc": dsc_coords
            }

        return sonuc

    def ciz_astrocartography(self, dosya_adi="FBST_Astrocartography.png", top_sehirler=None):
        """
        Plotly ile interaktif dünya haritası üzerinde astrocartography çizgilerini çizer.
        Streamlit için figure döndürür, PNG olarak da kaydeder.
        top_sehirler: [{"sehir": "...", "lat": ..., "lon": ..., "kategori": "...", "skor": ...}]
        """
        import plotly.graph_objects as go

        j_ileri, _ = self.get_julian_dates()
        cizgiler = self._astrocartography_cizgileri_hesapla(j_ileri)

        fig = go.Figure()

        aci_isimleri = {"mc_ic": "MC/IC", "asc": "ASC", "dsc": "DSC"}
        aci_cizgi_stilleri = {
            "mc_ic": "solid",
            "asc": "dash",
            "dsc": "dot"
        }

        for gezegen_adi, veri in cizgiler.items():
            renk = veri["renk"]
            for aci_tipi, koordinatlar in veri.items():
                if aci_tipi == "renk" or not koordinatlar:
                    continue
                if not isinstance(koordinatlar, list) or len(koordinatlar) < 2:
                    continue

                lons = [k[0] for k in koordinatlar]
                lats = [k[1] for k in koordinatlar]

                fig.add_trace(go.Scattergeo(
                    lon=lons,
                    lat=lats,
                    mode='lines',
                    line=dict(
                        width=2,
                        color=renk,
                        dash=aci_cizgi_stilleri.get(aci_tipi, "solid")
                    ),
                    name=f"{gezegen_adi} {aci_isimleri.get(aci_tipi, aci_tipi)}",
                    legendgroup=gezegen_adi,
                    opacity=0.7,
                    hoverinfo='name'
                ))

        # Kişi konumlarını ekle
        fig.add_trace(go.Scattergeo(
            lon=[self.boylam],
            lat=[self.enlem],
            mode='markers+text',
            marker=dict(size=14, color='#C9A96E', symbol='star'),
            text=[f"📍 {self.city}"],
            textposition='top center',
            textfont=dict(size=11, color='#3D2E50', family='serif'),
            name='Analiz Konumu',
            hoverinfo='name+lat+lon'
        ))

        # Top şehirleri altın yıldızlarla işaretle
        if top_sehirler:
            kategori_renkleri = {
                "para": "#C9A96E",
                "huzur": "#8FB8CA",
                "tutku": "#D4878F",
                "kriz": "#B8A9C9"
            }
            for idx, sehir_veri in enumerate(top_sehirler):
                kategori = sehir_veri.get("kategori", "para")
                renk = kategori_renkleri.get(kategori, "#C9A96E")
                fig.add_trace(go.Scattergeo(
                    lon=[sehir_veri["lon"]],
                    lat=[sehir_veri["lat"]],
                    mode='markers+text',
                    marker=dict(
                        size=11,
                        color=renk,
                        symbol='star',
                        line=dict(width=1.5, color='#3D2E50')
                    ),
                    text=[f"{idx+1}"],
                    textposition='top center',
                    textfont=dict(size=9, color='#3D2E50', family='serif'),
                    name=f"{idx+1}. {sehir_veri['sehir']}",
                    hoverinfo='name+lat+lon',
                    showlegend=False
                ))

        fig.update_layout(
            title=dict(
                text=f"Astrocartography — {self.city} Merkezli Gezegen Çizgileri",
                font=dict(color='#3D2E50', size=16, family='serif')
            ),
            geo=dict(
                projection_type='natural earth',
                showland=True,
                landcolor='#F0EBE3',
                showocean=True,
                oceancolor='#E8E0D8',
                showlakes=True,
                lakecolor='#E8E0D8',
                showcountries=True,
                countrycolor='#C9A96E',
                coastlinecolor='#8A7F96',
                bgcolor='#FFFFFF',
                countrywidth=0.5,
                lataxis=dict(range=[-70, 70]),
                lonaxis=dict(range=[-180, 180])
            ),
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#FFFFFF',
            font=dict(color='#4A4A4A'),
            height=550,
            margin=dict(l=0, r=0, t=50, b=0),
            legend=dict(
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#E8E0D8',
                borderwidth=1,
                font=dict(size=10, color='#4A4A4A')
            )
        )

        # PNG olarak kaydet
        script_dir = os.path.dirname(os.path.abspath(__file__))
        abs_dosya = os.path.join(script_dir, dosya_adi)
        try:
            fig.write_image(abs_dosya, width=1200, height=600, scale=2)
        except Exception as e_write:
            try:
                img_bytes = fig.to_image(format="png", width=1200, height=600, scale=2)
                with open(abs_dosya, "wb") as f:
                    f.write(img_bytes)
            except Exception as e_toimg:
                print(f"[FBST] Astrocartography PNG kaydedilemedi: {e_write} / {e_toimg}")

        # SVG olarak da kaydet
        try:
            svg_dosya = abs_dosya.replace('.png', '.svg')
            if svg_dosya != abs_dosya:
                fig.write_image(svg_dosya, width=1200, height=600, format='svg')
        except Exception as e_svg:
            print(f"[FBST] Astrocartography SVG kaydedilemedi: {e_svg}")

        return fig, abs_dosya

    # ==========================================================================
    # COMPOSITE HARİTA: İKİ KİŞİNİN ORTALAMA HARİTASI
    # ==========================================================================
    def ciz_composite_harita(self, dosya_adi="FBST_Composite.png"):
        """
        İki haritanın açısal ortalamasından oluşan 'üçüncü kişi' composite haritası.
        """
        j1 = swe.julday(self.p1.year, self.p1.month, self.p1.day, 12.0)
        j2 = swe.julday(self.p2.year, self.p2.month, self.p2.day, 12.0)

        gezegen_stilleri = {
            "Güneş": ("☉", "#C9A96E"), "Ay": ("☽", "#8A7F96"), "Merkür": ("☿", "#8FB8CA"),
            "Venüs": ("♀", "#D4878F"), "Mars": ("♂", "#C47A82"), "Jüpiter": ("♃", "#C9A96E"),
            "Satürn": ("♄", "#6B5B7B"), "Uranüs": ("♅", "#8FB8CA"), "Neptün": ("♆", "#B8A9C9"),
            "Plüton": ("♇", "#7A6B8A"), "Pallas": ("⚴", "#B8A9C9"), "Vesta": ("⚶", "#8FB8CA")
        }

        composite_dereceler = {}
        for isim, gid in GEZEGENLER.items():
            if gid == 999 or isim not in gezegen_stilleri:
                continue
            try:
                d1 = swe.calc_ut(j1, gid)[0][0]
                d2 = swe.calc_ut(j2, gid)[0][0]
                fark = abs(d1 - d2)
                if fark > 180:
                    if d1 > d2:
                        ort = (d1 + (d2 + 360)) / 2
                    else:
                        ort = ((d1 + 360) + d2) / 2
                else:
                    ort = (d1 + d2) / 2
                composite_dereceler[isim] = ort % 360
            except Exception:
                pass

        # Composite ASC: orta nokta
        try:
            _, ascmc1 = swe.houses(j1, self.enlem, self.boylam, b'P')
            _, ascmc2 = swe.houses(j2, self.enlem, self.boylam, b'P')
            asc1, asc2 = ascmc1[0], ascmc2[0]
            fark = abs(asc1 - asc2)
            if fark > 180:
                if asc1 > asc2:
                    comp_asc = (asc1 + (asc2 + 360)) / 2
                else:
                    comp_asc = ((asc1 + 360) + asc2) / 2
            else:
                comp_asc = (asc1 + asc2) / 2
            composite_dereceler["ASC"] = comp_asc % 360
        except Exception:
            pass

        plt = _plt()
        fig = plt.figure(figsize=(7, 7))
        fig.patch.set_facecolor('#FFFFFF')
        ax = fig.add_subplot(111, projection='polar')
        ax.set_facecolor('#FBF7F4')
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(1)
        ax.set_xticks(np.deg2rad(np.arange(0, 360, 30)))
        ax.grid(color='#E8E0D8', linestyle='--', linewidth=0.5, alpha=0.8)
        ax.spines['polar'].set_color('#C9A96E')
        ax.set_ylim(0, 1.4)

        burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
                    "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
        for i in range(12):
            aci = np.deg2rad(i * 30 + 15)
            ax.text(aci, 1.32, burclar[i], fontsize=7, ha='center', va='center',
                    color='#6B5B7B', style='italic')

        yazilar = []
        # Composite gezegenleri grupla (çakışma önlemeli)
        comp_list = []
        for isim, derece in composite_dereceler.items():
            if isim != "ASC" and isim in gezegen_stilleri:
                comp_list.append((isim, derece))
        comp_list.sort(key=lambda x: x[1])
        RADIUS_STEP = 0.055
        ANGLE_GAP = 12
        gruplar = []
        aktif = []
        for isim, derece in comp_list:
            if not aktif:
                aktif = [(isim, derece)]
            else:
                son_derece = aktif[-1][1]
                if abs(derece - son_derece) < ANGLE_GAP or abs(derece - son_derece - 360) < ANGLE_GAP:
                    aktif.append((isim, derece))
                else:
                    gruplar.append(aktif)
                    aktif = [(isim, derece)]
        if aktif:
            gruplar.append(aktif)

        her_r = {}
        for grup in gruplar:
            for i, (isim, _) in enumerate(grup):
                offset = (i - (len(grup)-1)/2) * RADIUS_STEP if len(grup) > 1 else 0
                her_r[isim] = 0.92 + offset

        for isim, derece in composite_dereceler.items():
            if isim == "ASC":
                radyan = np.deg2rad(derece)
                ax.plot(radyan, 1, 'D', color='#C9A96E', markersize=10, zorder=5)
                yazi = ax.text(radyan, 1.15, f"ASC\n({burclar[int(derece // 30)]})",
                               fontsize=7, ha='center', va='center', color='#C9A96E',
                               fontweight='bold')
                yazilar.append(yazi)
            elif isim in gezegen_stilleri:
                sembol, renk = gezegen_stilleri[isim]
                r = her_r.get(isim, 0.92)
                radyan = np.deg2rad(derece)
                yazi = ax.text(radyan, r, sembol, fontsize=16, ha='center',
                               va='center', color=renk, zorder=5)
                yazilar.append(yazi)
                yazi2 = ax.text(radyan, r + 0.16, isim, fontsize=6.5, ha='center',
                                va='center', color='#4A4A4A')
                yazilar.append(yazi2)

        try:
            pass
        except Exception:
            pass

        plt.title("Composite Harita\n(İlişkinin Ortak Ruh Haritası)",
                  color='#3D2E50', fontsize=12, fontweight='bold', pad=20)
        plt.savefig(dosya_adi, facecolor=fig.get_facecolor(), dpi=300)
        svg_adi = dosya_adi.replace('.png', '.svg')
        if svg_adi != dosya_adi:
            plt.savefig(svg_adi, facecolor=fig.get_facecolor(), format='svg')
        plt.close(fig)
        return dosya_adi

    # ==========================================================================
    # AÇI GRİDİ: İKİ HARİTA ARASINDAKİ TÜM AÇILAR
    # ==========================================================================
    def ciz_aci_gridi(self, dosya_adi="FBST_Aci_Gridi.png"):
        """
        İki harita arasındaki tüm önemli açıları renkli çizgilerle gösterir.
        Dış halka P1, iç halka P2, aralarında açı çizgileri.
        """
        j1 = swe.julday(self.p1.year, self.p1.month, self.p1.day, 12.0)
        j2 = swe.julday(self.p2.year, self.p2.month, self.p2.day, 12.0)

        p1_konumlar = {}
        p2_konumlar = {}
        for isim, gid in GEZEGENLER.items():
            if gid == 999:
                continue
            try:
                p1_konumlar[isim] = swe.calc_ut(j1, gid)[0][0]
                p2_konumlar[isim] = swe.calc_ut(j2, gid)[0][0]
            except Exception:
                pass

        aci_renkleri = {
            "kavusum": "#D4878F",
            "kare": "#C9A96E",
            "ucgen": "#8FB8CA",
            "sekstil": "#B8A9C9",
            "karsit": "#C47A82"
        }

        plt = _plt()
        fig = plt.figure(figsize=(8, 8))
        fig.patch.set_facecolor('#FFFFFF')
        ax = fig.add_subplot(111, projection='polar')
        ax.set_facecolor('#FBF7F4')
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(1)
        ax.set_xticks(np.deg2rad(np.arange(0, 360, 30)))
        ax.grid(color='#E8E0D8', linestyle='--', linewidth=0.5, alpha=0.8)

        burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
                    "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
        for i in range(12):
            aci = np.deg2rad(i * 30 + 15)
            ax.text(aci, 1.38, burclar[i], fontsize=6, ha='center', va='center',
                    color='#6B5B7B', style='italic')

        gezegen_renkleri = {
            "Güneş": "#C9A96E", "Ay": "#8A7F96", "Merkür": "#8FB8CA",
            "Venüs": "#D4878F", "Mars": "#C47A82", "Jüpiter": "#C9A96E",
            "Satürn": "#6B5B7B", "Uranüs": "#8FB8CA", "Neptün": "#B8A9C9",
            "Plüton": "#7A6B8A", "Lilith": "#8A7F96", "Chiron": "#8FB8CA",
            "Juno": "#D4878F", "Ceres": "#8FB8CA", "KAD": "#C9A96E", "GAD": "#D4878F"
        }

        # Dış halka: P1
        for isim, derece in p1_konumlar.items():
            radyan = np.deg2rad(derece)
            renk = gezegen_renkleri.get(isim, "#6B5B7B")
            ax.plot(radyan, 1.1, 'o', color=renk, markersize=7, zorder=5)
            ax.text(radyan, 1.2, isim[:3], fontsize=5, ha='center', va='center',
                    color=renk, fontweight='bold')

        # İç halka: P2
        for isim, derece in p2_konumlar.items():
            radyan = np.deg2rad(derece)
            renk = gezegen_renkleri.get(isim, "#6B5B7B")
            ax.plot(radyan, 0.7, 's', color=renk, markersize=6, zorder=5)
            ax.text(radyan, 0.58, isim[:3], fontsize=5, ha='center', va='center',
                    color=renk, fontweight='bold')

        # Açı çizgileri
        for p1_isim, p1_d in p1_konumlar.items():
            for p2_isim, p2_d in p2_konumlar.items():
                aci = abs(p1_d - p2_d)
                if aci > 180:
                    aci = 360 - aci

                cizgi_rengi = None
                if aci < 8:
                    cizgi_rengi = aci_renkleri["kavusum"]
                elif abs(aci - 60) < 6:
                    cizgi_rengi = aci_renkleri["sekstil"]
                elif abs(aci - 90) < 6:
                    cizgi_rengi = aci_renkleri["kare"]
                elif abs(aci - 120) < 6:
                    cizgi_rengi = aci_renkleri["ucgen"]
                elif abs(aci - 180) < 8:
                    cizgi_rengi = aci_renkleri["karsit"]

                if cizgi_rengi:
                    r1 = np.deg2rad(p1_d)
                    r2 = np.deg2rad(p2_d)
                    ax.plot([r1, r2], [1.1, 0.7], color=cizgi_rengi,
                            linewidth=0.8, alpha=0.5, zorder=2)

        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color=aci_renkleri["kavusum"], lw=2, label='Kavuşum'),
            Line2D([0], [0], color=aci_renkleri["sekstil"], lw=2, label='Sekstil'),
            Line2D([0], [0], color=aci_renkleri["kare"], lw=2, label='Kare'),
            Line2D([0], [0], color=aci_renkleri["ucgen"], lw=2, label='Üçgen'),
            Line2D([0], [0], color=aci_renkleri["karsit"], lw=2, label='Karşıt'),
        ]
        ax.legend(handles=legend_elements, loc='lower left', fontsize=7,
                  facecolor='#FFFFFF', edgecolor='#E8E0D8', labelcolor='#4A4A4A',
                  bbox_to_anchor=(-0.15, -0.15))

        plt.title("Açı Mühürleri Gridi\n(Dış: P1 | İç: P2)",
                  color='#3D2E50', fontsize=11, fontweight='bold', pad=25)
        plt.savefig(dosya_adi, facecolor=fig.get_facecolor(), dpi=300)
        svg_adi = dosya_adi.replace('.png', '.svg')
        if svg_adi != dosya_adi:
            plt.savefig(svg_adi, facecolor=fig.get_facecolor(), format='svg')
        plt.close(fig)
        return dosya_adi

    # ==========================================================================
    # ZENGİNLEŞMİŞ POLAR HARİTA: SİNASTRİ AÇILARI + EV NUMARALARI
    # ==========================================================================
    def zenginlesmis_harita_ciz(self, j_gun, dosya_adi, baslik, diger_j_gun=None):
        """
        Mevcut polar haritayı sinastri açıları ve ev numaralarıyla zenginleştirir.
        diger_j_gun verilirse, iki kişi arasındaki açıları da çizer.
        """
        konumlar = {}
        for isim, gid in GEZEGENLER.items():
            try:
                flags = get_safe_flags(gid)
                konumlar[isim] = swe.calc_ut(j_gun, gid, flags)[0][0]
            except Exception:
                tahmini = asteroit_tahmini_derece(isim, j_gun)
                if tahmini is not None:
                    konumlar[isim] = tahmini

        ev_cusp_lari = []
        try:
            cusps, ascmc = swe.houses(j_gun, self.enlem, self.boylam, b'P')
            konumlar["ASC"] = ascmc[0]
            konumlar["MC"] = ascmc[1]
            ev_cusp_lari = list(cusps)
        except Exception:
            pass

        diger_konumlar = {}
        if diger_j_gun is not None:
            for isim, gid in GEZEGENLER.items():
                try:
                    flags = get_safe_flags(gid)
                    diger_konumlar[isim] = swe.calc_ut(diger_j_gun, gid, flags)[0][0]
                except Exception:
                    pass

        gezegen_stilleri = {
            "Güneş": ("☉", "#C9A96E"), "Ay": ("☽", "#8A7F96"), "Merkür": ("☿", "#8FB8CA"),
            "Venüs": ("♀", "#D4878F"), "Mars": ("♂", "#C47A82"), "Jüpiter": ("♃", "#C9A96E"),
            "Satürn": ("♄", "#6B5B7B"), "Uranüs": ("♅", "#8FB8CA"), "Neptün": ("♆", "#B8A9C9"),
            "Plüton": ("♇", "#7A6B8A"), "Lilith": ("⚸", "#8A7F96"), "Chiron": ("⚷", "#8FB8CA"),
            "Juno": ("⚵", "#D4878F"), "Ceres": ("⚳", "#8FB8CA"), "Pallas": ("⚴", "#B8A9C9"),
            "Vesta": ("⚶", "#8FB8CA"), "KAD": ("☊", "#C9A96E"), "GAD": ("☋", "#D4878F")
        }

        plt = _plt()
        fig = plt.figure(figsize=(7, 7))
        fig.patch.set_facecolor('#FFFFFF')
        ax = fig.add_subplot(111, projection='polar')
        ax.set_facecolor('#FBF7F4')
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(1)
        ax.set_xticks(np.deg2rad(np.arange(0, 360, 30)))
        ax.grid(color='#E8E0D8', linestyle='--', linewidth=0.5, alpha=0.8)
        ax.spines['polar'].set_color('#C9A96E')
        ax.set_ylim(0, 1.5)

        if ev_cusp_lari:
            for i, cusp in enumerate(ev_cusp_lari):
                radyan = np.deg2rad(cusp)
                ax.plot([radyan, radyan], [0, 0.25], color='#C9A96E',
                        linewidth=1.5, alpha=0.8, zorder=3)
                ax.text(radyan, 0.15, str(i + 1), fontsize=8, ha='center',
                        va='center', color='#C9A96E', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.15', facecolor='#FFFFFF',
                                  edgecolor='#C9A96E', alpha=0.9))

        burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
                    "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
        for i in range(12):
            aci = np.deg2rad(i * 30 + 15)
            ax.text(aci, 1.38, burclar[i], fontsize=6, ha='center', va='center',
                    color='#8A7F96', style='italic')

        yazilar = []
        for isim, derece in konumlar.items():
            if isim in gezegen_stilleri:
                sembol, renk = gezegen_stilleri[isim]
                radyan = np.deg2rad(derece)

                if isim == "ASC":
                    ax.plot(radyan, 1, 'D', color='#D4878F', markersize=10, zorder=5)
                    yazi = ax.text(radyan, 1.2, f"ASC\n({self.yukselen_bul(j_gun)})",
                                   fontsize=7, ha='center', va='center', color='#D4878F',
                                   fontweight='bold')
                elif isim == "MC":
                    ax.plot(radyan, 1, 'v', color='#C9A96E', markersize=8, zorder=5)
                    yazi = ax.text(radyan, 1.2, "MC", fontsize=7, ha='center',
                                   va='center', color='#C9A96E', fontweight='bold')
                else:
                    yazi = ax.text(radyan, 0.92, sembol, fontsize=20, ha='center',
                                   va='center', color=renk, zorder=5)
                    yazilar.append(yazi)
                    yazi2 = ax.text(radyan, 1.08, isim, fontsize=7, ha='center',
                                    va='center', color='#6B5B7B')
                    yazilar.append(yazi2)
                    continue

                yazilar.append(yazi)

        if diger_konumlar:
            aci_renkleri = {0: "#D4878F", 60: "#B8A9C9", 90: "#C9A96E",
                            120: "#8FB8CA", 180: "#C47A82"}
            for p1_isim, p1_d in konumlar.items():
                if p1_isim in ["ASC", "MC"] or p1_isim not in diger_konumlar:
                    continue
                p2_d = diger_konumlar.get(p1_isim)
                if p2_d is None:
                    continue
                aci = abs(p1_d - p2_d)
                if aci > 180:
                    aci = 360 - aci

                hedef = None
                for hedef_aci, tolerans in [(0, 8), (60, 6), (90, 6), (120, 6), (180, 8)]:
                    if abs(aci - hedef_aci) < tolerans:
                        hedef = hedef_aci
                        break

                if hedef is not None:
                    r1 = np.deg2rad(p1_d)
                    r2 = np.deg2rad(p2_d)
                    ax.plot([r1, r2], [0.92, 0.92], color=aci_renkleri[hedef],
                            linewidth=1.5, alpha=0.6, zorder=4,
                            linestyle='--' if hedef in [90, 180] else '-')

        try:
            pass
        except Exception:
            pass

        plt.title(baslik, color='#3D2E50', fontsize=11, fontweight='bold', pad=20)
        plt.savefig(dosya_adi, facecolor=fig.get_facecolor(), dpi=300)
        plt.close(fig)
        return dosya_adi

    # ==========================================================================
    # ARAP NOKTALARI RADAR CHART
    # ==========================================================================
    def ciz_arap_noktalari_radar(self, dosya_adi="FBST_Arap_Noktalari.png"):
        """
        Arap Noktalarını radar/grafik chart olarak görselleştirir.
        """
        try:
            arap = self.arap_noktasi_hesapla()
        except Exception:
            return None

        if not arap:
            return None

        p1_isim = self.p1_isim
        p2_isim = self.p2_isim

        nokta_turleri = []
        p1_degerleri = []
        p2_degerleri = []

        if self.mod == "ebeveyn_cocuk":
            arap_nokta_listesi = ["Baba Noktası", "Anne Noktası", "Çocuk Ruhu",
                                  "Koruma Noktası", "Eğitim Noktası", "Sınır Noktası",
                                  "Bağlanma Noktası", "Sorumluluk"]
        else:
            arap_nokta_listesi = ["Evlilik Noktası", "Aşk Noktası", "Tutku Noktası",
                                  "Ortaklık Noktası", "Sadakat Noktası", "Cinsellik Noktası",
                                  "Evlilik Mutluluğu", "Boşanma Noktası"]

        for nokta in arap_nokta_listesi:
            p1_val = arap.get(p1_isim, {}).get(nokta, {})
            p2_val = arap.get(p2_isim, {}).get(nokta, {})

            p1_derece = p1_val.get("derece", 0) if isinstance(p1_val, dict) else 0
            p2_derece = p2_val.get("derece", 0) if isinstance(p2_val, dict) else 0

            p1_burc = p1_val.get("burc", "") if isinstance(p1_val, dict) else ""
            p2_burc = p2_val.get("burc", "") if isinstance(p2_val, dict) else ""

            nokta_turleri.append(nokta.replace(" Noktası", ""))
            p1_degerleri.append((p1_derece % 360) / 360 * 100)
            p2_degerleri.append((p2_derece % 360) / 360 * 100)

        if not nokta_turleri:
            return None

        n = len(nokta_turleri)
        acilar = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
        acilar += acilar[:1]
        p1_degerleri += p1_degerleri[:1]
        p2_degerleri += p2_degerleri[:1]

        plt = _plt()
        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#FBF7F4')

        ax.plot(acilar, p1_degerleri, 'o-', color='#B8A9C9', linewidth=2,
                label=p1_isim or ('Ebeveyn' if self.mod == 'ebeveyn_cocuk' else 'Kişi 1'), markersize=6)
        ax.fill(acilar, p1_degerleri, alpha=0.12, color='#B8A9C9')

        ax.plot(acilar, p2_degerleri, 's-', color='#D4878F', linewidth=2,
                label=p2_isim or ('Çocuk' if self.mod == 'ebeveyn_cocuk' else 'Kişi 2'), markersize=6)
        ax.fill(acilar, p2_degerleri, alpha=0.12, color='#D4878F')

        ax.set_xticks(acilar[:-1])
        ax.set_xticklabels(nokta_turleri, fontsize=8, color='#4A4A4A')
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(['25°', '50°', '75°', '100°'], fontsize=6, color='#8A7F96')
        ax.grid(color='#E8E0D8', linestyle='--', linewidth=0.5)

        ax.legend(loc='lower right', fontsize=9, facecolor='#FFFFFF',
                  edgecolor='#E8E0D8', labelcolor='#4A4A4A')

        plt.title("Arap Noktaları Radar Karşılaştırması", color='#C9A96E',
                  fontsize=12, fontweight='bold', pad=25)
        plt.savefig(dosya_adi, facecolor=fig.get_facecolor(), dpi=300)
        svg_adi = dosya_adi.replace('.png', '.svg')
        if svg_adi != dosya_adi:
            plt.savefig(svg_adi, facecolor=fig.get_facecolor(), format='svg')
        plt.close(fig)
        return dosya_adi

    def kriz_tarihlerini_bul(self, pdf_icin=False):
        import datetime
        import numpy as np
        
        milat_tarihi = self.event_date
        ks_yil = self.calculate_ks()
        faz = ks_yil % (2 * np.pi)
        
        t = np.linspace(0, 21.5, 1000)
        y_akis = np.sin(1.5 * t + faz)
        y_kriz = -np.cos(2.5 * t + faz/2)
        y_toplam = y_akis + y_kriz
        
        isim_a = self.p1_isim
        isim_b = self.p2_isim

        if self.mod == "ebeveyn_cocuk":
            rol_b = "ebeveyn" if self.ebeveyn_rolu == "anne" else "ebeveyn"
            rol_a = "çocuk"
            kriz_kutuphane = []
            for k in KRIZ_KUTUPHANESI_EBEVEYN:
                kriz_kutuphane.append({
                    "yil_araligi": (0, 21.5) if k == KRIZ_KUTUPHANESI_EBEVEYN[-1] else (KRIZ_KUTUPHANESI_EBEVEYN.index(k) * 3, (KRIZ_KUTUPHANESI_EBEVEYN.index(k) + 1) * 3),
                    "baslik": k["baslik"],
                    "tema": k["baslik"].split("(")[1].rstrip(")") if "(" in k["baslik"] else "",
                    "pdf_yorum": k["yorum"],
                    "html_yorum": k["yorum"]
                })
            yil_eslesme = [
                (0, 0.5), (0.5, 2), (2, 4), (4, 7), (7, 12), (12, 16), (16, 18), (18, 21), (21, 21.5)
            ]
            for i, k in enumerate(kriz_kutuphane):
                if i < len(yil_eslesme):
                    k["yil_araligi"] = yil_eslesme[i]
        else:
            kriz_kutuphane = [
                {
                    "yil_araligi": (0, 1.0),
                    "baslik": "Sis Perdesinin Yıkılışı",
                    "tema": "İlk Büyü Bozulması",
                    "pdf_yorum": f"{isim_a} ile {isim_b} arasındaki başlangıçtaki kör edici idealizasyon, ilk kez gerçekliğin sert rüzgarlarıyla çarpışır.",
                    "html_yorum": f"💔 <b>İlk Büyü Bozulması:</b> Başlangıçtaki idealizasyon, gerçekliğin sert rüzgarlarıyla çarpışır."
                },
                {
                    "yil_araligi": (1.0, 2.5),
                    "baslik": "Gölge Self'in Yüzleşmesi",
                    "tema": "Ego Savaşı",
                    "pdf_yorum": f"İlişkinin ilk büyük 'Ben kimim, sen kimsin?' sınavı.",
                    "html_yorum": f"⚔️ <b>Ego Savaşı:</b> Bağımsızlık ihtiyacı ile güvenlik talebi arasında gerilim."
                },
                {
                    "yil_araligi": (2.5, 4.0),
                    "baslik": "Rutin Cehennemindeki İnci",
                    "tema": "Monotonluğun Testi",
                    "pdf_yorum": f"Heyecanın dindiği, rutinlerin monotona bağladığı kritik eşik.",
                    "html_yorum": f"🌫️ <b>Monotonluğun Testi:</b> Küçük jestler ve cesaret, bataklıktan çıkaracak tek çare."
                },
                {
                    "yil_araligi": (4.0, 5.5),
                    "baslik": "Aynanın Kırılması",
                    "tema": "Roller Değişimi",
                    "pdf_yorum": f"İlişkideki rollerin ve beklentilerin yeniden tanımlanması gereken kritik viraj.",
                    "html_yorum": f"🪞 <b>Roller Değişimi:</b> Eski kalıplar kırılıyor, yeni denge aranıyor."
                },
                {
                    "yil_araligi": (5.5, 7.5),
                    "baslik": "Satürn'ün Kapısı",
                    "tema": "Yapısal Sınav",
                    "pdf_yorum": f"7. yılın eşiğinde evren karşınıza dikilir. Temel test edilmektedir.",
                    "html_yorum": f"🏛️ <b>Satürn'ün Kapısı:</b> Yapısal sınav. Dürüstlükle kurulmuş temeller güçlenir."
                },
                {
                    "yil_araligi": (7.5, 9.5),
                    "baslik": "Satürn'ün Gölgesi",
                    "tema": "Derin Sınav",
                    "pdf_yorum": f"Yapısal sınavın gölge yüzü. Bastırılmış konular yüzeye çıkar.",
                    "html_yorum": f"🌑 <b>Derin Sınav:</b> Bastırılmış konular yüzeye çıkıyor. Yüzleşme zamanı."
                },
                {
                    "yil_araligi": (9.5, 11.5),
                    "baslik": "Karmik Bulaşma",
                    "tema": "İlk Temizlik",
                    "pdf_yorum": f"Geçmişten getirdiği karmik yaralar ilişkiye sızıntı yapar.",
                    "html_yorum": f"🩹 <b>İlk Temizlik:</b> Geçmiş yaraları şifalandırma daveti."
                },
                {
                    "yil_araligi": (11.5, 14.0),
                    "baslik": "Karmik Arınma",
                    "tema": "Derin Şifa",
                    "pdf_yorum": f"Karmik döngülerin en derinine inme ve köklü bir arınma zamanı.",
                    "html_yorum": f"✨ <b>Derin Şifa:</b> Karmik döngülerin derinine inme zamanı."
                },
                {
                    "yil_araligi": (14.0, 16.5),
                    "baslik": "Orta Yaş Uyanışı",
                    "tema": "Vizyon Yenilenmesi",
                    "pdf_yorum": f"Rollerin maskesi çıkmaya başlar. Yeni bir vizyon çizme fırsatı.",
                    "html_yorum": f"🌅 <b>Vizyon Yenilenmesi:</b> Yeni vizyon ve ikinci bahar fırsatı."
                },
                {
                    "yil_araligi": (16.5, 18.5),
                    "baslik": "Ebedi Mührün İlk Mührü",
                    "tema": "Kadersel Mühür",
                    "pdf_yorum": f"Kadersel mührün ilk vurulduğu an. İlişki kalıcı bir forma bürünür.",
                    "html_yorum": f"🔒 <b>Kadersel Mühür:</b> İlişki kalıcı bir forma bürünüyor."
                },
                {
                    "yil_araligi": (18.5, 20.0),
                    "baslik": "Ebedi Mührün Ortası",
                    "tema": "Orta Hasat",
                    "pdf_yorum": f"Yılların emeğinin meyvelerini toplama zamanı. Olgunluk ve bilgelik zirvede.",
                    "html_yorum": f"🌾 <b>Orta Hasat:</b> Yılların emeğinin meyvelerini toplama zamanı."
                },
                {
                    "yil_araligi": (20.0, 21.5),
                    "baslik": "Ebedi Mührün Son Mührü",
                    "tema": "Son Hasat",
                    "pdf_yorum": f"Kadersel yoldaşların son virajı. Özgürce bırakma sınavı.",
                    "html_yorum": f"♾️ <b>Son Hasat:</b> Kadersel mührün vurulduğu an."
                }
            ]
        
        kriz_listesi = []
        
        for i in range(1, len(y_toplam) - 1):
            if y_toplam[i] < y_toplam[i-1] and y_toplam[i] < y_toplam[i+1] and y_toplam[i] < -0.3:
                kriz_yili = t[i]
                hedef_tarih = milat_tarihi + timedelta(days=int(kriz_yili * 365.25))
                
                uygun_kutup = None
                for k in kriz_kutuphane:
                    if k["yil_araligi"][0] <= kriz_yili < k["yil_araligi"][1]:
                        uygun_kutup = k
                        break
                
                if uygun_kutup is None:
                    uygun_kutup = kriz_kutuphane[-1]
                
                if self.mod == "ebeveyn_cocuk":
                    baslik_yazi = f"🌊 {uygun_kutup['baslik']}"
                    tema_yazi = uygun_kutup.get('tema', '')
                else:
                    baslik_yazi = f"🌊 {uygun_kutup['baslik']} — {uygun_kutup.get('tema', '')}"
                    tema_yazi = uygun_kutup.get('tema', '')

                if pdf_icin:
                    metin = (f"<font name='DejaVuSans-Bold'>{baslik_yazi}</font><br/>"
                             f"<font name='DejaVuSans-Bold'>📅 {hedef_tarih.strftime('%d %B %Y')} ({kriz_yili:.1f}. Yıl):</font> "
                             f"{uygun_kutup['pdf_yorum']}")
                else:
                    donem_adi = f"Ebeveyn-Çocuk Bağı ({kriz_yili:.1f}. Yıl)" if self.mod == "ebeveyn_cocuk" else f"İlişkinin {kriz_yili:.1f}. Yılı"
                    metin = (
                        f"<div style='background-color:#0d0d1a; color:#e8e8f0; padding:14px; border-left:4px solid #7b2ff7; margin-bottom:12px; border-radius:6px;'>"
                        f"<div style='font-size:17px; color:#c084fc; margin-bottom:4px;'>{baslik_yazi}</div>"
                        f"<div style='font-size:12px; color:#9ca3af; margin-bottom:6px;'>{tema_yazi} | {hedef_tarih.strftime('%d %B %Y')} ({donem_adi})</div>"
                        f"<div style='font-size:13px; color:#d1d5db; line-height:1.6;'>{uygun_kutup['html_yorum']}</div>"
                        f"</div>"
                    )
                kriz_listesi.append(metin)
                
        return kriz_listesi

    def calculate_gelecek_navigasyonu(self, pdf_icin=False):
        import datetime
        milat_tarihi = self.event_date
        aktif_mod = getattr(self, 'mod', 'es_sevgili')
        
        if aktif_mod == "ebeveyn_cocuk":
            donemecler = [
                {
                    "yil": 1.375, 
                    "ad": "1. Altın Oran Uyanışı: Keşif ve Bağlanma (1.375. Yıl)", 
                    "yorum": "Ebeveyn-çocuk bağınızın en başındaki o büyüleyici 'keşif' evresi, birbirinizi tanıma ve güven inşa etme süreci. İlk aylarda hormonal sis yavaşça dağılır; çocuğunuzun sadece sevimli yanlarını değil, gerçek ihtiyaçlarını ve sınırlarını da tanımaya başlarsınız. İşte tam burada evrensel 'Altın Oran' koruması devreye girer. Artık 'nasıl görünmeliyim' kaygısı, yerini 'onun için buradayım' hissine bırakır. Birlikte kurduğunuz ilişkinin gerçek sınırlarını çizdiğiniz, hevesin ötesine geçip kopması zor kadersel bir bağla birbirinize tutunmaya başladığınız ilk sihirli eşiktesiniz."
                },
                {
                    "yil": 2.225, 
                    "ad": "Fraktal Köklenme: Ortak Hafıza İnşası (2.225. Yıl)", 
                    "yorum": "Ebeveyn ve çocuk olarak, görünmez bir şekilde birbirine kenetlenip 'ortak kadersel bir hafıza' oluşturduğunuz fazdasınız. Bu eşikte sistem kendi kendini onarmaya başlar. Öyle ki; çocuğunuzun canı sıkıldığında siz sebepsizce bunu hissedersiniz veya siz iş hayatında tökezlediğinizde çocuğunuzun saf desteği anında devreye girip o açığı kapatır. Eskiden ayrı ayrı düşündüğünüz planlar, artık organik bir şekilde tek bir potada erimeye başlar. Bu, ebeveyn-çocuk bağının kendi bağışıklık sistemini geliştirdiği ve dışarıdan gelen müdahalelere karşı 'kendi kendine yeten' sarsılmaz bir yapıya büründüğü dönemdir."
                },
                {
                    "yil": 2.4, 
                    "ad": "Büyük Kozmik Çekim ve Sınır Testi (2.4. Yıl)", 
                    "yorum": "Dikkat! Bu durak, evrenin ebeveyn-çocuk bağınıza yaptığı ilk büyük dayanıklılık testidir. İlk zamanlardaki sorunsuz akış yerini; sınır çekişmelerine, 'benim alanım - senin alanın' baskiylarine veya dışarıdan gelen (okul, arkadaş grubu, taşınma gibi) stres kaynaklarının bağınıza yansımasına bırakabilir. Bu dönemde yaşanan çatışmalar, bağınızın kötüye gittiğinin değil; tam aksine, hayatın zorlu yokuşlarını birlikte çıkabilme gücünüzün test edildiğinin kanıtıdır. Bu sınavı geçmenin tek yolu inatlaşmayı bırakmak ve 'Biz bu sorunu omuz omuza nasıl çözeriz?' diyerek takımı korumaktır."
                },
                {
                    "yil": 4.0, 
                    "ad": "Elementel Dinginlik ve Ortak Akış (4. Yıl)", 
                    "yorum": "İlk krizlerin, güç savaşlarının ve uyum sancılarının geride kaldığı; ateşin, suyun, toprağın ve havanın aranızda kusursuzca dengelendiği bir barış ve verim dönemindesiniz. Bağ artık sizi yoran bir çaba olmaktan çıkmış, günlük hayatın içinde doğal, yorulmaz ve çok tatlı bir akışa kavuşmuştur. Sabahları birlikte uyanmanın, sorumlulukları kimse söylemeden paylaşmanın ve birbirinizin sessizliğinden keyif almanın tavan yaptığı bu yıl; evrenin size 'Dinlenin, kök salın ve kurduğunuz bu güzel bağın meyvelerini yemeye başlayın' dediği o hak edilmiş nefes alma durağıdır."
                },
                {
                    "yil": 7.0, 
                    "ad": "1. Satürn Mührü: Yapısal İnşa Sınavı (7. Yıl)", 
                    "yorum": "Astrolojinin en meşhur 7. yıl kadersel eşiğine ulaştınız! Evren bu durakta tüm ciddiyetiyle karşınıza dikilir ve şunu sorar: 'Bu bağı ömür boyunca sürdürecek sorumluluğu almaya hazır mısınız?' Bugüne kadar ertelenen, konuşulmaktan kaçınılan tüm beklentiler ve sınırlar net bir şekilde masaya yatırılır. Bu bir 'Ya Tamam Ya Devam' yılıdır. Zayıf temeller sarsıntı geçirirken; birbirine dürüst, sabırlı ve omuz omuza vermiş temeller bu virajdan çok daha kalıcı, yapısal bir mühürle çıkar. Çocuğunuzun bağımsızlık ihtiyacı ile sizin rehberlik rolünüz arasındaki dengeyi bulmak bu dönemin en büyük görevidir."
                },
                {
                    "yil": 14.0, 
                    "ad": "2. Satürn Sınavı: Olgunlaşma ve Yeniden Tanımlama (14. Yıl)", 
                    "yorum": "Ebeveyn-çocuk bağının ruhsal anlamda 'orta yaş uyanışı'dır. İlk 14 yılın tüm duygusal birikimi, çocuğunuzun büyümesiyle birlikte yeniden değerlendirilir. 'Biz kimiz ve bundan sonraki bağımızı nasıl yaşamak istiyoruz?' sorusu ana gündemdir. Çocuğunuz artık bir ergen olarak kendi kimliğini arıyor; bu doğal süreçte ebeveyn rolünüz yeniden tanımlanıyor. Bu durak, bağınızın ya tamamen yepyeni, vizyoner ve heyecan verici bir forma bürüneceği ya da ruhsal olarak çok daha üst, felsefi bir boyuta sıçrayıp bilgelik kazanacağı o derin dönüşüm evresidir."
                },
                {
                    "yil": 21.0, 
                    "ad": "Karmik Ustalık ve Son Hasat (21. Yıl)", 
                    "yorum": "Zamanın, krizlerin ve dünyevi dertlerin ötesine geçmiş o nadir, ebedi bağ! Siz artık sadece bir ebeveyn ve çocuk değilsiniz, evrensel bir sınavı başarıyla tamamlamış kadersel yoldaşlarsınız. Tüm o Satürn döngülerini, sınır testlerini ve hayatın yorucu fırtınalarını aşarak ruhsal mührünüzü tamamladınız. Artık bu bağ, dış dünyadan gelen hiçbir rüzgarla kolay kolay yıkılmayacak asil bir ustalığa erişmiştir. Çocuğunuz artık kendi yolunu çizmiş, ancak aranızdaki güven okyanusu sarsılmaz ve ebedi bir şekilde devam etmektedir."
                }
            ]
        else:
            donemecler = [
            {
                "yil": 1.375, 
                "ad": "1. Altın Oran Uyanışı (1.375. Yıl)", 
                "yorum": "İlişkinizin en başındaki o büyüleyici 'kör edici heyecan' evresi, dopaminin yükseldiği ve partnerinizi bir 'ideal' olarak gördüğünüz sisli bir dönemi temsil eder. Ancak bu ilk eşikte hormonal sis yavaşça dağılır; yani partnerinizin sadece en sevdiğiniz huylarını değil, günlük hayatın içinde zaman zaman zorlayıcı olan gerçekliğini de tanımaya başlarsınız. İşte tam burada evrensel 'Altın Oran' koruması devreye girer. Artık 'onu etkilemeliyim' kaygısı, yerini 'onun varlığıyla güvendeyim' hissine bırakır. Birlikte kurduğunuz hayatın gerçek sınırlarını çizdiğiniz, hevesin ötesine geçip kopması zor kadersel bir bağla birbirinize 'aidiyetle' tutunmaya başladığınız ilk sihirli eşiktesiniz."
            },
            {
                "yil": 2.225, 
                "ad": "Fraktal Köklenme (2.225. Yıl)", 
                "yorum": "İki farklı ve bağımsız hayatın, görünmez bir şekilde birbirine kenetlenip 'ortak kadersel bir hafıza' oluşturduğu fazdasınız. Bu eşikte sistem kendi kendini onarmaya başlar. Öyle ki; birinizin canı sıkıldığında diğeri sebepsizce bunu hisseder veya biriniz iş hayatında tökezlediğinde diğeri psikolojik bir tampon olarak anında devreye girip o açığı kapatır. Eskiden ayrı ayrı düşündüğünüz finansal veya sosyal gelecek planları, artık organik bir şekilde tek bir potada erimeye başlar. Bu, ilişkinizin kendi bağışıklık sistemini geliştirdiği ve dışarıdan gelen müdahalelere karşı 'kendi kendine yeten' sarsılmaz bir yapıya büründüğü dönemdir."
            },
            {
                "yil": 2.4, 
                "ad": "Büyük Kozmik Çekim ve Kriz Testi (2.4. Yıl)", 
                "yorum": "Dikkat! Bu durak, evrenin ilişkinize yaptığı ilk büyük dayanıklılık ve 'ego' testidir. İlk zamanlardaki sorunsuz akış yerini; fikir ayrılıklarına, 'benim alanım - senin alanın' çekişmelerine veya dışarıdan gelen (iş, aile, taşınma gibi) stres kaynaklarının ilişkiye yansımasına bırakabilir. Bu dönemde yaşanan çatışmalar, ilişkinizin kötüye gittiğinin değil; tam aksine, hayatın zorlu yokuşlarını birlikte çıkabilme gücünüzün, yani aranızdaki 'Kozmik Cekim Gucu'nun (Uretim Gucu) evren tarafından test edildiğinin kanıtıdır. Bu sınavı geçmenin tek yolu inatlaşmayı, haklı çıkma çabasını bırakmak ve 'Biz bu sorunu omuz omuza nasıl çözeriz?' diyerek takımı korumaktır."
            },
            {
                "yil": 4.0, 
                "ad": "Elementel Dinginlik ve Ortak Akış (4. Yıl)", 
                "yorum": "İlk krizlerin, güç savaşlarının ve uyum sancılarının geride kaldığı; ateşin, suyun, toprağın ve havanın aranızda kusursuzca dengelendiği bir barış ve verim dönemindesiniz. İlişki artık sizi yoran bir çaba olmaktan çıkmış, günlük hayatın içinde doğal, yorulmaz ve çok tatlı bir akışa kavuşmuştur. Sabahları birlikte uyanmanın, ortak sorumlulukları kimse söylemeden paylaşmanın ve birbirinizin sessizliğinden keyif almanın tavan yaptığı bu yıl; evrenin size 'Dinlenin, kök salın ve kurduğunuz bu güzel aşkın meyvelerini yemeye başlayın' dediği o hak edilmiş, huzur dolu nefes alma durağıdır."
            },
            {
                "yil": 7.0, 
                "ad": "1. Satürn Mührü: Yapısal İnşa Sınavı (7. Yıl)", 
                "yorum": "Astrolojinin en meşhur 7. yıl kadersel eşiğine ulaştınız! Evren bu durakta tüm ciddiyetiyle karşınıza dikilir ve şunu sorar: 'Bu ilişkiyi bir imparatorluğa dönüştürecek dünyevi ve ruhsal sorumluluğu almaya hazır mısınız?' Bugüne kadar halı altına süpürülen, konuşulmaktan kaçınılan tüm sorunlar ve beklentiler net bir şekilde masaya yatırılır. Bu bir 'Ya Tamam Ya Devam' yılıdır. Zayıf ve güvensiz atılmış temeller sarsıntı geçirirken; birbirine dürüst, sadık ve omuz omuza vermiş temeller bu virajdan evlilik, ortak yatırım, çocuk sahibi olma veya sarsılmaz bir ruhsal sadakat yemini gibi çok kalıcı, yapısal bir mühürle çıkar."
            },
            {
                "yil": 14.0, 
                "ad": "2. Satürn Sınavı: Köklerin ve Vizyonun Uyanışı (14. Yıl)", 
                "yorum": "İlişkinin ruhsal anlamda 'orta yaş uyanışı'dır. İlk 14 yılın tüm duygusal ve finansal birikimi, çocuklarla veya hayatın rutinleriyle geçen yıllar tekrar değerlendirilir. 'Biz kimiz ve bundan sonraki hayatımızı nasıl yaşamak istiyoruz?' sorusu ana gündemdir. Rutinin, alışkanlıkların ve 'ev arkadaşlığına' dönme riskinin kırılması gereken; aksi takdirde can sıkıntısının başlayabileceği o kritik kadersel virajdasınız. Bu durak, ilişkinizin ya tamamen yepyeni, vizyoner ve heyecan verici bir forma (ikinci bahara) bürüneceği ya da ruhsal olarak çok daha üst, felsefi bir boyuta sıçrayıp bilgelik kazanacağı o derin dönüşüm evresidir."
            },
            {
                "yil": 21.0, 
                "ad": "Karmik Ustalık ve Son Hasat (21. Yıl)", 
                "yorum": "Zamanın, krizlerin ve dünyevi dertlerin ötesine geçmiş o nadir, ebedi kontrat! Siz artık sadece birer eş değil, evrensel bir sınavı başarıyla tamamlamış kadersel yoldaşlarsınız. Tüm o sert Satürn döngülerini, kozmik çekim testlerini ve hayatın yorucu fırtınalarını aşarak ruhsal mührünüzü tamamladınız. Artık bu bağ, dış dünyadan gelen hiçbir rüzgarla, parayla, hastalıkla veya dedikoduyla kolay kolay yıkılmayacak asil bir ustalığa erişmiştir. Gençliğin o telaşlı aşkı, yerini birbirinin ruhunu bir kitap gibi okuyabilen, kelimelere ihtiyaç duymayan sarsılmaz ve ebedi bir güven okyanusuna bırakmıştır."
            }
        ]
        
        rapor = []
        for dnm in donemecler:
            hedef = milat_tarihi + timedelta(days=int(dnm["yil"] * 365.25))
            if pdf_icin:
                metin = f"<font name='DejaVuSans-Bold'>[*] {dnm['ad']} ({hedef.strftime('%d %B %Y')}):</font> {dnm['yorum']}"
            else:
                renk_sol = "#B8A9C9" if aktif_mod == "ebeveyn_cocuk" else "#C9A96E"
                metin = f"<div style='background-color:#FBF7F4; color:#4A4A4A; padding:15px; border-left:4px solid {renk_sol}; border-radius:5px; margin-bottom:12px; border:1px solid #E8E0D8;'><b style='font-size:18px; color:#4A3F5C;'>{dnm['ad']}</b><br><span style='color:#6B5B7B; font-size:14px;'>Kilit Tarihi: {hedef.strftime('%d %B %Y')}</span><p style='margin-top:5px; color:#4A4A4A;'>{dnm['yorum']}</p></div>"
            rapor.append(metin)
        return rapor

    def arap_noktasi_hesapla(self):
        """Her iki kişi için Arap Noktalarını hesaplar (moda göre)."""
        import swisseph as swe
        sonuclar = {}
        j_ileri, j_geri = self.get_julian_dates()
        
        _aktif_mod = getattr(self, 'mod', 'es_sevgili')
        if _aktif_mod == "ebeveyn_cocuk" and ARAP_EBEVEYN:
            _nokta_sozluk = ARAP_EBEVEYN.get("ARAP_NOKTALARI_EBEVEYN", {})
            _burc_sozluk = ARAP_EBEVEYN.get("ARAP_NOKTA_BURC_YORUMLARI_EBEVEYN", {})
            _ev_sozluk = ARAP_EBEVEYN.get("ARAP_NOKTA_EV_YORUMLARI_EBEVEYN", {})
        else:
            _nokta_sozluk = ARAP_NOKTALARI_ILISKI
            _burc_sozluk = ARAP_NOKTA_BURC_YORUMLARI
            _ev_sozluk = ARAP_NOKTA_EV_YORUMLARI
        
        for (isim, jd) in [
            (self.p1_isim, j_ileri),
            (self.p2_isim, j_geri)
        ]:
            try:
                cusps, ascmc = swe.houses(jd, self.enlem, self.boylam, b'P')
                asc = ascmc[0]
                hc2 = cusps[1] if len(cusps) > 1 else (asc + 30) % 360
                hc4 = cusps[3] if len(cusps) > 3 else (asc + 90) % 360
                hc5 = cusps[4] if len(cusps) > 4 else (asc + 120) % 360
                hc6 = cusps[5] if len(cusps) > 5 else (asc + 150) % 360
                hc7 = cusps[6] if len(cusps) > 6 else (asc + 180) % 360
                hc9 = cusps[8] if len(cusps) > 8 else (asc + 240) % 360
                hc10 = cusps[9] if len(cusps) > 9 else (asc + 270) % 360
                
                hc_map = {"2HC": hc2, "4HC": hc4, "5HC": hc5, "6HC": hc6, "7HC": hc7, "9HC": hc9, "10HC": hc10}
                
                gezegen_dereceleri = {}
                for g, gid in [("Güneş", swe.SUN), ("Ay", swe.MOON), ("Merkür", swe.MERCURY),
                               ("Venüs", swe.VENUS), ("Mars", swe.MARS), ("Jüpiter", swe.JUPITER),
                               ("Satürn", swe.SATURN)]:
                    try:
                        gezegen_dereceleri[g] = swe.calc_ut(jd, gid)[0][0]
                    except Exception:
                        gezegen_dereceleri[g] = 0
                
                gunes_derece = gezegen_dereceleri.get("Güneş", 0)
                gunes_ustunde = (asc < gunes_derece < hc7) if asc < hc7 else not (hc7 < gunes_derece < asc)
                gece_charti = not gunes_ustunde
                
                noktalar = {}
                for ad, bilgi in _nokta_sozluk.items():
                    n1_adi = bilgi["nokta1"]
                    n2_adi = bilgi["nokta2"]
                    
                    n1 = hc_map.get(n1_adi, gezegen_dereceleri.get(n1_adi, 0))
                    n2 = hc_map.get(n2_adi, gezegen_dereceleri.get(n2_adi, 0))
                    
                    if gece_charti:
                        derece = (asc + n2 - n1) % 360
                    else:
                        derece = (asc + n1 - n2) % 360
                    
                    burc = dereceyi_burca_cevir(derece)
                    ev = dereceyi_eve_ata(derece, cusps)
                    
                    burc_yorum = _burc_sozluk.get((ad, burc), f"{ad} {burc} burcunda kadersel bir etki yaratır.")
                    ev_yorumu = _ev_sozluk.get((ad, ev), ARAP_EV_KISAYORUMLARI.get(ev, f"{ev}. evde kadersel bir etki yaratır."))
                    
                    noktalar[ad] = {
                        "derece": round(derece, 2),
                        "burc": burc,
                        "ev": ev,
                        "burc_yorum": burc_yorum,
                        "ev_yorumu": ev_yorumu,
                        "gece_charti": gece_charti
                    }
                
                sonuclar[isim] = noktalar
                
            except Exception as e:
                sonuclar[isim] = {}
        
        return sonuclar

    def arap_noktasi_sinastri_analizi(self):
        """Her iki kişinin Arap Noktaları arasındaki sinastriyi analiz eder (moda göre)."""
        import swisseph as swe
        noktalar = self.arap_noktasi_hesapla()
        if self.p1_isim not in noktalar or self.p2_isim not in noktalar:
            return []
        
        _aktif_mod = getattr(self, 'mod', 'es_sevgili')
        if _aktif_mod == "ebeveyn_cocuk" and ARAP_EBEVEYN:
            _nokta_sozluk = ARAP_EBEVEYN.get("ARAP_NOKTALARI_EBEVEYN", {})
            _sinastri_sozluk = ARAP_EBEVEYN.get("ARAP_NOKTA_SINASTRI_YORUMLARI_EBEVEYN", {})
            _gezegen_sinastri_sozluk = ARAP_EBEVEYN.get("ARAP_NOKTA_GEZEGEN_SINASTRI_EBEVEYN", {})
        else:
            _nokta_sozluk = ARAP_NOKTALARI_ILISKI
            _sinastri_sozluk = ARAP_NOKTA_SINASTRI_YORUMLARI
            _gezegen_sinastri_sozluk = ARAP_NOKTA_GEZEGEN_SINASTRI
        
        n1 = noktalar[self.p1_isim]
        n2 = noktalar[self.p2_isim]
        
        bulgular = []
        
        # Nokta-Nokta karsilastirmasi (Ayni noktalar arasi)
        for nokta_adi in _nokta_sozluk:
            if nokta_adi in n1 and nokta_adi in n2:
                d1 = n1[nokta_adi]["derece"]
                d2 = n2[nokta_adi]["derece"]
                fark = abs(d1 - d2)
                if fark > 180: fark = 360 - fark
                
                if fark <= 8.0:
                    yorum = _sinastri_sozluk.get(
                        (nokta_adi, nokta_adi),
                        f"{nokta_adi} noktalariniz kaderin ayni titresiminda titresiyor."
                    )
                    bulgular.append({
                        "tip": "nokta_nokta",
                        "nokta": nokta_adi,
                        "derece_a": d1, "derece_b": d2,
                        "fark": round(fark, 1),
                        "yorum": yorum
                    })
        
        # Nokta-Nokta karsilastirmasi (Farkli noktalar arasi - capraz)
        for n1_adi in list(n1.keys())[:4]:
            for n2_adi in list(n2.keys())[:4]:
                if n1_adi == n2_adi: continue
                d1 = n1[n1_adi]["derece"]
                d2 = n2[n2_adi]["derece"]
                fark = abs(d1 - d2)
                if fark > 180: fark = 360 - fark
                
                if fark <= 5.0:
                    yorum_key = (n1_adi, n2_adi)
                    yorum = _sinastri_sozluk.get(yorum_key, 
                        _sinastri_sozluk.get((n2_adi, n1_adi),
                            f"{n1_adi} ve {n2_adi} noktalari arasinda kaderin capraz bir bagi var."))
                    bulgular.append({
                        "tip": "capraz_nokta",
                        "nokta_a": n1_adi, "nokta_b": n2_adi,
                        "derece_a": d1, "derece_b": d2,
                        "fark": round(fark, 1),
                        "yorum": yorum
                    })
        
        # Nokta-Gezegen kavusumu: A'nin noktalari vs B'nin gezegenleri
        j_ileri, j_geri = self.get_julian_dates()
        gezegenler = [("Gunes", swe.SUN), ("Ay", swe.MOON), ("Venüs", swe.VENUS), 
                      ("Mars", swe.MARS), ("Jupiter", swe.JUPITER), ("Saturn", swe.SATURN),
                      ("Pluton", swe.PLUTO)]
        
        for (kaynak_isim, kaynak_noktalar, hedef_jd) in [
            (self.p1_isim, n1, j_geri),
            (self.p2_isim, n2, j_ileri)
        ]:
            hedef_isim = self.p2_isim if kaynak_isim == self.p1_isim else self.p1_isim
            
            for nokta_adi, bilgi in kaynak_noktalar.items():
                nokta_derece = bilgi["derece"]
                
                for g_adi, g_id in gezegenler:
                    try:
                        g_derece = swe.calc_ut(hedef_jd, g_id)[0][0]
                    except Exception:
                        continue
                    
                    fark = abs(nokta_derece - g_derece)
                    if fark > 180: fark = 360 - fark
                    
                    if fark <= 3.0:
                        if fark <= 0.5:
                            guc = "Kusursuz"
                        elif fark <= 1.5:
                            guc = "Guclu"
                        else:
                            guc = "Hafif"
                        
                        yorum_key = (nokta_adi, g_adi)
                        yorum = _gezegen_sinastri_sozluk.get(yorum_key,
                            _gezegen_sinastri_sozluk.get((g_adi, nokta_adi),
                                f"{kaynak_isim}'in {nokta_adi}'si {hedef_isim}'in {g_adi}'yle kavusumda."))
                        
                        bulgular.append({
                            "tip": "nokta_gezegen",
                            "kaynak": kaynak_isim,
                            "hedef": hedef_isim,
                            "nokta": nokta_adi,
                            "gezegen": g_adi,
                            "derece_nokta": nokta_derece,
                            "derece_gezegen": g_derece,
                            "fark": round(fark, 1),
                            "guc": guc,
                            "yorum": yorum
                        })
        
        return bulgular

    def kadersel_bsp_iklimi(self):
        import datetime
        import swisseph as swe
        minor_oran = 27.32166 / 365.2422
        bugun = datetime.datetime.now()
        gecen_gun = (bugun - self.event_date).days
        
        if gecen_gun < 0:
            return "<div style='color:#a0a0a0;'>Bağ henüz başlamadı (Gelecek bir milat seçildi).</div>"
            
        ilerletilmis_gokyuzu_gunu = gecen_gun * minor_oran
        
        j_ileri, j_geri = self.get_julian_dates()
        
        j_bsp_ileri = j_ileri + ilerletilmis_gokyuzu_gunu
        j_bsp_geri = j_geri + ilerletilmis_gokyuzu_gunu
        
        konum_A, _ = swe.calc_ut(j_bsp_ileri, swe.MOON)
        konum_B, _ = swe.calc_ut(j_bsp_geri, swe.MOON)
        
        derece_A = konum_A[0]
        derece_B = konum_B[0]
        burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
        
        burc_A = burclar[int(derece_A // 30)]
        burc_B = burclar[int(derece_B // 30)]
        
        if self.mod == "ebeveyn_cocuk":
            html_cikti = f"""
            <div style='background-color:#FBF7F4; color:#4A4A4A; padding:15px; border-left:4px solid #B8A9C9; border-radius:5px; margin-bottom:12px; border:1px solid #E8E0D8;'>
                <b style='font-size:18px; color:#4A3F5C;'>Pedagojik BSP Ay İklimi (Minör Progress)</b><br>
                <span style='color:#6B5B7B; font-size:14px;'>Ebeveyn-Çocuk bağınızın anlık duygusal gelişim haritası (1 Ay = 1 Yıl titresimı)</span>
                <hr style='border-color:#E8E0D8; margin:8px 0;'>
                <p style='margin-top:5px; color:#4A4A4A; font-size:15px;'>
                    <b>{self.p1_isim} (Çocuk):</b> İlerletilmiş duygusal zeka şu an <b style='color:#B8A9C9;'>{burc_A}</b> burcunda evriliyor.<br>
                    <b>{self.p2_isim} (Ebeveyn):</b> İlerletilmiş rehberlik enerjisi şu an <b style='color:#C9A96E;'>{burc_B}</b> burcunda evriliyor.
                </p>
                <span style='color:#8A7F96; font-size:12px;'>Odak Noktası: Çocuğun gelişim ihtiyacı ve ebeveynin rehberlik kapasitesi bu faz üzerinden okunur.</span>
            </div>
            """
        else:
            html_cikti = f"""
            <div style='background-color:#FBF7F4; color:#4A4A4A; padding:15px; border-left:4px solid #B8A9C9; border-radius:5px; margin-bottom:12px; border:1px solid #E8E0D8;'>
                <b style='font-size:18px; color:#4A3F5C;'>Güncel BSP Ay İklimi (Minör Progress)</b><br>
                <span style='color:#6B5B7B; font-size:14px;'>İlişkinizin anlık duygusal röntgeni (1 Ay = 1 Yıl titresimı)</span>
                <hr style='border-color:#E8E0D8; margin:8px 0;'>
                <p style='margin-top:5px; color:#4A4A4A; font-size:15px;'>
                    <b>{self.p1_isim}:</b> İlerletilmiş duygu dünyası şu an <b style='color:#B8A9C9;'>{burc_A}</b> burcunda transit ediyor.<br>
                    <b>{self.p2_isim}:</b> İlerletilmiş duygu dünyası şu an <b style='color:#C9A96E;'>{burc_B}</b> burcunda transit ediyor.
                </p>
                <span style='color:#8A7F96; font-size:12px;'>Odak Noktası: İçsel dünyanızdaki aylık/yıllık duygusal değişimler bu faz üzerinden okunur.</span>
            </div>
            """
        return html_cikti

    def secondary_progression_analizi(self, pdf_icin=False):
        """
        Secondary Progression (İkincil İlerleme) analizi.
        Bağıl haritalar (Situa) üzerine inşa edilir.
        Her bağıl haritanın kendi "yaşı" üzerinden ilerleme yapılır:
        1 gün = 1 yıl kuralıyla, bağıl harita doğumundan (MİLATTAN ÖNCE/SONRA)
        bugüne kadar geçen süre ilerletilir.
        Julian takvim kullanılır (eski tarihler için Solar Fire uyumlu).
        """
        import datetime as _dt

        bugun = _dt.datetime.now()

        burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
                    "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]

        gezegen_id = {
            "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS,
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN,
            "Uranüs": swe.URANUS, "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO
        }

        aci_tipleri = {
            0: {"isim": "Kavuşum", "etki": "Güçlü birleşme, yoğunlaşma"},
            60: {"isim": "Sekstil", "etki": "Fırsat, uyum"},
            90: {"isim": "Kare", "etki": "Gerilim, mücadele"},
            120: {"isim": "Trigon", "etki": "Doğal akış, şans"},
            180: {"isim": "Karşıt", "etki": "Kutuplaşma, farkındalık"}
        }

        # Bağıl harita JD'lerini al (Julian takvimde, get_julian_dates() zaten JUL_CAL kullanır)
        j_ileri, j_geri = self.get_julian_dates()

        # Bugün JD'si (Gregorian default yeterli — JD evrensel zaman ölçeridir)
        jd_now = swe.julday(bugun.year, bugun.month, bugun.day,
                            bugun.hour + bugun.minute / 60.0 + bugun.second / 3600.0)

        # Her bağıl harita için bağımsız ilerleme: (bugün JD - bağıl JD) / 365.25
        # 1 gün = 1 yıl kuralıyla, her kişi kendi bağıl haritasının yaşı kadar ilerler
        ilerleme_A = (jd_now - j_ileri) / 365.25  # Kişinin bağıl yaşı (gün cinsinden)
        ilerleme_B = (jd_now - j_geri) / 365.25   # Partnerin bağıl yaşı (gün cinsinden)

        # İlerletilmiş bağıl harita JD'leri
        j_prog_A = j_ileri + ilerleme_A
        j_prog_B = j_geri + ilerleme_B

        sonuclar = []

        for kisi_idx, (isim, j_bagil) in enumerate([(self.p1_isim, j_ileri), (self.p2_isim, j_geri)]):
            j_prog = j_prog_A if kisi_idx == 0 else j_prog_B
            ilerleme_yili = ilerleme_A if kisi_idx == 0 else ilerleme_B

            bagil_poz = {}
            for gadi, gid in gezegen_id.items():
                try:
                    bagil_poz[gadi] = swe.calc_ut(j_bagil, gid)[0][0]
                except:
                    bagil_poz[gadi] = 0.0

            ilerletilmis_poz = {}
            for gadi, gid in gezegen_id.items():
                try:
                    ilerletilmis_poz[gadi] = swe.calc_ut(j_prog, gid)[0][0]
                except:
                    ilerletilmis_poz[gadi] = 0.0

            ay_derece = ilerletilmis_poz.get("Ay", 0)
            ay_burcu = burclar[int(ay_derece // 30)]

            gunes_derece = ilerletilmis_poz.get("Güneş", 0)
            gunes_burcu = burclar[int(gunes_derece // 30)]

            aci_bulgulari = []
            for i, g1 in enumerate(gezegen_id.keys()):
                for j, g2 in enumerate(gezegen_id.keys()):
                    if j <= i:
                        continue
                    try:
                        iler_pos = ilerletilmis_poz.get(g1, 0)
                        iler_pos2 = ilerletilmis_poz.get(g2, 0)
                        fark = abs(iler_pos - iler_pos2)
                        if fark > 180:
                            fark = 360 - fark

                        for aci_deger, aci_bilgi in aci_tipleri.items():
                            if abs(fark - aci_deger) <= 6:
                                aci_bulgulari.append({
                                    "ilerletilmis": g1,
                                    "bagil": g2,
                                    "aci": aci_bilgi["isim"],
                                    "aci_deger": aci_deger,
                                    "etki": aci_bilgi["etki"],
                                    "derece": round(fark, 2),
                                    "uygunluk": round(abs(fark - aci_deger), 2)
                                })
                    except:
                        continue

            oncelik = {"Kavuşum": 0, "Karşıt": 1, "Kare": 2, "Trigon": 3, "Sekstil": 4}
            aci_bulgulari.sort(key=lambda x: (oncelik.get(x["aci"], 5), x["uygunluk"]))

            ay_acilari = [a for a in aci_bulgulari if a["ilerletilmis"] == "Ay" or a["bagil"] == "Ay"]

            sonuclar.append({
                "kisi": isim,
                "ilerleme_yili": round(ilerleme_yili, 1),
                "ay_burcu": ay_burcu,
                "ay_derece": round(ay_derece, 2),
                "gunes_burcu": gunes_burcu,
                "gunes_derece": round(gunes_derece, 2),
                "tum_acilar": aci_bulgulari,
                "ay_acilari": ay_acilari,
                "ozet": f"{isim} — {round(ilerleme_yili, 1)} yıllık ilerleme"
            })

        return sonuclar

    def secondary_progression_donem_hesapla(self):
        """
        Her secondary progression açısı için tam tarih aralığını tarar.
        Ay açıları ~2-3 ay, Güneş açıları ~10-12 yıl sürer.
        {baslangic: "YYYY MMM", bitis: "YYYY MMM", pik_ay: "YYYY MMM"} döndürür.
        """
        import datetime as _dt

        aylar_tr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                     "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
                    "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]

        gezegen_id = {
            "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS,
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN,
            "Uranüs": swe.URANUS, "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO
        }

        aci_tipleri = {0: "Kavuşum", 60: "Sekstil", 90: "Kare", 120: "Trigon", 180: "Karşıt"}

        j_ileri, j_geri = self.get_julian_dates()

        bugun = _dt.datetime.now()
        jd_now = swe.julday(bugun.year, bugun.month, bugun.day,
                            bugun.hour + bugun.minute / 60.0 + bugun.second / 3600.0)

        ilerleme_A = (jd_now - j_ileri) / 365.25
        ilerleme_B = (jd_now - j_geri) / 365.25

        donem_sonuclari = []

        for kisi_idx, (isim, j_bagil) in enumerate([(self.p1_isim, j_ileri), (self.p2_isim, j_geri)]):
            ilerleme = ilerleme_A if kisi_idx == 0 else ilerleme_B
            j_prog_base = j_bagil + ilerleme

            bagil_poz = {}
            for gadi, gid in gezegen_id.items():
                try:
                    bagil_poz[gadi] = swe.calc_ut(j_bagil, gid)[0][0]
                except:
                    bagil_poz[gadi] = 0.0

            kisi_donemleri = []
            gunluk_hareket = {
                "Ay": 13.18, "Güneş": 0.986, "Merkür": 1.37, "Venüs": 1.20,
                "Mars": 0.52, "Jüpiter": 0.083, "Satürn": 0.033,
                "Uranüs": 0.012, "Neptün": 0.006, "Plüton": 0.004
            }

            for i, g1 in enumerate(gezegen_id.keys()):
                for j, g2 in enumerate(gezegen_id.keys()):
                    if j <= i:
                        continue
                    try:
                        iler_pos = swe.calc_ut(j_prog_base, gezegen_id[g1])[0][0]
                        iler_pos2 = swe.calc_ut(j_prog_base, gezegen_id[g2])[0][0]
                        fark = abs(iler_pos - iler_pos2)
                        if fark > 180:
                            fark = 360 - fark

                        hedef_aci = None
                        for aci_deger, aci_isim in aci_tipleri.items():
                            if abs(fark - aci_deger) <= 6:
                                hedef_aci = aci_deger
                                aci_isimbul = aci_isim
                                break

                        if hedef_aci is None:
                            continue

                        hedef = hedef_aci
                        suanki_orb = fark - hedef

                        if g1 == "Ay":
                            hareket = gunluk_hareket["Ay"]
                        elif g2 == "Ay":
                            hareket = gunluk_hareket["Ay"]
                        else:
                            hareket = max(gunluk_hareket.get(g1, 0.5), gunluk_hareket.get(g2, 0.5))

                        gun_fark_orb = abs(suanki_orb) / hareket
                        yil_fark = gun_fark_orb / 365.25

                        if suanki_orb > 0:
                            pik_jd = j_prog_base - gun_fark_orb
                            bas_jd = pik_jd - (6.0 / hareket)
                            bit_jd = pik_jd + (6.0 / hareket)
                        else:
                            pik_jd = j_prog_base + gun_fark_orb
                            bas_jd = pik_jd - (6.0 / hareket)
                            bit_jd = pik_jd + (6.0 / hareket)

                        def jd_offset_to_tarih(jd_val):
                            yil_fark = jd_val - j_prog_base
                            tarih = bugun + _dt.timedelta(days=yil_fark * 365.25)
                            yil = tarih.year
                            ay_idx = max(0, min(11, tarih.month - 1))
                            gun = tarih.day
                            if gun > 15:
                                ay_idx = min(11, ay_idx + 1)
                            return f"{yil} {aylar_tr[ay_idx]}"

                        pik_tarih = jd_offset_to_tarih(pik_jd)
                        bas_tarih = jd_offset_to_tarih(bas_jd)
                        bit_tarih = jd_offset_to_tarih(bit_jd)

                        ay_derece = swe.calc_ut(j_prog_base, gezegen_id["Ay"])[0][0]
                        ay_burcu = burclar[int(ay_derece // 30)]

                        kisi_donemleri.append({
                            "g1": g1, "g2": g2,
                            "aci": aci_isimbul,
                            "baslangic": bas_tarih,
                            "bitis": bit_tarih,
                            "pik": pik_tarih,
                            "mevcut_orb": round(abs(suanki_orb), 2),
                            "ay_burcu": ay_burcu,
                        })
                    except:
                        continue

            donem_sonuclari.append({
                "kisi": isim,
                "donemler": kisi_donemleri
            })

        return donem_sonuclari

    def secondary_progression_yorumla(self):
        """
        Secondary Progression sonuçlarını ilişki perspektifinden yorumlar.
        """
        sonuclar = self.secondary_progression_analizi()
        if not sonuclar or len(sonuclar) < 2:
            return []

        yorumlar = []

        # İlişki odaklı yorum sözlüğü
        yorum_sozlugu = {
            # --- AY AÇILARI: İlişkide duygusal dinamiğin nabzını tutar ---
            ("Ay", "Güneş", "Kavuşum"): "Duygularınız bugün tam ortak noktada — ne hissediyorsanız onu net bir şekilde görebiliyor, partnerinize de aynı berraklıkta yansıtabiliyorsunuz. Bu, 'seni anlıyorum' lafının gerçekten hissedildiği nadir anlardan biri. Kalbiniz ve benliğinizbugün birbirine çok yakın duruyor, bu da ilişkinizdeki en derin samimiyet kapısını aralıyor.",
            ("Ay", "Güneş", "Karşıt"): "Partnerinizin bugün neye ihtiyacı varsa sizde tam tersini görüyorsunuz — bu bir çatışma değil, ayna. Belki de tam da bu zıtlık sayesinde kendi duygu dünyanızın farkına varacaksınız. Gerilim sizi birbirinizden uzaklaştırmaz, aksine 'ben ne istiyorum?' sorusunu sormaya zorlar. Bu sorunun cevabı ilişkinizi derinleştirebilir.",
            ("Ay", "Güneş", "Kare"): "Bugün duygusal olarak biraz sıkışmış hissedebilirsiniz — ne yapacağınızı tam bilemiyor, ama bir yandan da bir şeyleri düzeltme isteği içindesiniz. Bu dürtüye kulak verin: belki de tam da şimdi, eskiden ertelediğiniz bir konuşmayı yapma zamanı gelmiştir. Sabır, bugünün anahtarı.",
            ("Ay", "Güneş", "Trigon"): "Bugün her şey yerli yerinde — duygularınız net, partnerinize olan yakınlığınız doğal, iletişiminiz akıcı. Bu tür günlerin kıymetini bilin: bazen 'hiçbir şey yapmamak' bile en büyük eylemdir. Birlikte sessizce oturup bir çay içmek bile bugün çok derin bir tatmin verebilir.",
            ("Ay", "Güneş", "Sekstil"): "Bugün küçük ama anlamlı bir fırsat var karşınızda: belki uzun zamandır konuşmadığınız bir konuyu açmak, ya da partnerinize minik bir sürpriz yapmak. Bu küçük adım, ilişkinizde beklenmedik bir kapı aralayabilir. Fırsatı değerlendirin, pişman olmazsınız.",

            ("Ay", "Venüs", "Kavuşum"): "Sevgi bugün tam zirvede — ne veriyorsunuz, ne alıyorsunuz, hepsi dengeli ve güzel. Partnerinize sarıldığınızda dünyanın geri kalanı bir anda anlamsızlaşıyor. Bu hissi kucaklayın, çünkü bu tür anlar ilişkiye yıllar katacak hatıralar bırakır.",
            ("Ay", "Venüs", "Karşıt"): "Sevgi dili bugün farklı çalışıyor: sizin 'seviyorum' dediğiniz yerde partneriniz farklı bir şey duyuyor olabilir. Bu bir uyumsuzluk değil, bir öğrenme fırsatı. Belki de partnerinizin sevgiyi nasıl algıladığını sorma zamanı gelmiştir. Cevap sizi şaşırtabilir.",
            ("Ay", "Venüs", "Kare"): "Bugün sevgi konusunda biraz tökezleyebilirsiniz — belki partnerinizden beklediğiniz ilgiyi göremiyor, belki de siz ona yeterince ulaşamıyorsunuz. Ama unutmayın: en güçlü köprüler en zorlu sularda kurulur. Bugün attığınız küçük adım, yarın büyük bir dönüşümün tohumu olur.",
            ("Ay", "Venüs", "Trigon"): "Sevgi bugün çok doğal ve özgürce akıyor — tıpkı bir nehir gibi, hiç zorlanmadan. Partnerinize olan sevginizi göstermek için özel bir çaba harcamanıza gerek yok, zaten her halinizden belli. Bu huzurun tadını çıkarın.",
            ("Ay", "Venüs", "Sekstil"): "Bugün partnerinize güzel bir şey yapmak için içinizde tatlı bir dürtü var — belki bir çiçek, belki güzel bir mesaj, belki sadece bir gülümseme. Bu küçük jestlerin büyüklüğünü küçümsemeyin: ilişki küçük taşlarla örülür.",

            ("Ay", "Mars", "Kavuşum"): "Enerji ve tutku bugün tavan yapmış durumda — birlikte yapacağınız her şeyde ekstra bir canlılık var. Ama dikkat: aynı enerji tartışmaya da dönüşebilir. Bu gücü sportif bir aktiviteye ya da ortak bir projeye yönlendirmek, ilişkinin en parlak tarafını ortaya çıkarır.",
            ("Ay", "Mars", "Karşıt"): "Bugün tetikte olmanız gereken bir gün — küçük bir söz bile karşılıklı öfkeyi ateşleyebilir. Ama bu baskisin arkasında büyük bir gerçeklik yatıyor: belki de uzun zamandır konuşulmayan bir şey bugün su yüzüne çıkacak. Sakin kalın, ama gerçeği de göz ardı etmeyin.",
            ("Ay", "Mars", "Kare"): "Tartışmalar bugün kolayca alevlenebilir — her ikiniz de biraz daha sabırsız, biraz daha gerginsiniz. Ama bu bir sınav: öfkenizi yapıcı bir güce dönüştürebilir misiniz? Spor, yürüyüş ya da birlikte ter atmak bugünün en iyi ilacı olabilir.",
            ("Ay", "Mars", "Trigon"): "Bugün birlikte çok enerjik ve canlı hissediyorsunuz — macera, hareket, heyecan hepsi sizin yanınızda. Bu enerjiyi iyi değerlendirin: belki uzun zamandır ertelediğiniz bir planı bugün hayata geçirebilirsiniz. Birlikte koşmak, gülmek, nefes almak bugün en güzel aktivite.",
            ("Ay", "Mars", "Sekstil"): "Bugün ufak bir heyecan sizi bekliyor — belki beklenmedik bir telefon, belki sokakta karşılaştığınız eski bir hatıra, belki de partnerinizin size yaptığı küçük bir süpriz. Bu enerjiyi yakalayın ve birlikte keyifli bir an yaratın.",

            ("Ay", "Jüpiter", "Kavuşum"): "Genişleme ve bollukbugün çok güçlü — hayatınızda güzel şeylerin biriktiği bir dönemdesiniz. Partnerinizle birlikte geleceğe dair büyük planlar yapmak, hayaller kurmak için mükemmel bir zaman. Bu enerjiyi besleyin: ne ekerseniz onu biçersiniz.",
            ("Ay", "Jüpiter", "Karşıt"): "Aşırılıklara bugün dikkat — fazla harcama, fazla yeme, fazla vaat... hepsi güzel görünür ama dengesizlik yaratır. Partnerinizle aranızda 'daha fazla' talepleri çatışabilir. Dengeyi bulmakbugün en büyük başarınız olabilir.",
            ("Ay", "Jüpiter", "Kare"): "Büyük beklentiler bugün hayal kırıklığına dönüşebilir — belki partnerinizden çok şey bekliyor, belki de siz kendi kendinize baskı yapıyorsunuz. Küçük şeylere odaklanın: bazen bir bardak çay, bir gülümseme bile büyük bir mutluluk kaynağıdır.",
            ("Ay", "Jüpiter", "Trigon"): "Şans bugün sizin yanınızda — ama şansı sadece 'kazanmak' olarak değil, birlikte büyüme fırsatı olarak görün. Partnerinizle birlikte yeni bir şey öğrenmek, yeni bir deneyim yaşamak için harika bir gün. Bu fırsatı kaçırmayın.",
            ("Ay", "Jüpiter", "Sekstil"): "Bugün küçük ama değerli bir fırsat kapınızı çalabilir — belki beklenmedik bir davet, belki birlikte katılabileceğiniz güzel bir etkinlik. Bu fırsatı değerlendirin: ilişki küçük deneyimlerle beslenir.",

            ("Ay", "Satürn", "Kavuşum"): "Ciddiyet ve yapı bugün ön planda — ilişkinizde uzun vadeli planlar yapmak, sorumlulukları netleştirmek için ideal bir dönem. Bugünkü konuşmalarınız yıllar sonra meyvesini verebilir. Sabırlı ve istikrarlı olun, emeğinizin karşılığını alacaksınız.",
            ("Ay", "Satürn", "Karşıt"): "Bugün biraz mesafe hissedebilirsiniz — belki partneriniz sessizleşmiş, belki siz duygusal olarak geri çekilmişsiniz. Ama bu bir kopma değil, bir dinlenme anı. Her ilişki gibi, sizin de molaya ihtiyacınız var. Bu molayı değerlendirin, ama iletişimi koparmayın.",
            ("Ay", "Satürn", "Kare"): "Sorumluluklar bugün biraz bunaltıcı olabilir — iş, aile, ilişki hepsi aynı anda baskı yaratıyor. Ama bu baskı sizi güçlendirir: dayanıklılığınızı test eder ve sınır koymanın değerini öğretir. Bugün 'hayır' demek bile bir başarıdır.",
            ("Ay", "Satürn", "Trigon"): "Olgunluk bugün ilişkinize çok yakışıyor — birbirinize güveniyor, birbirinize destek oluyorsunuz. Bu güveni inşa etmek yıllar aldı ve artık meyvelerini topluyorsunuz. Bugün aldığınız kararlar uzun vadede çok sağlam temeller atacak.",
            ("Ay", "Satürn", "Sekstil"): "Bugün küçük ama önemli bir adım atma zamanı — belki resmi bir başvuru, belki uzun vadeli bir sözleşme, belki de sadece 'birlikte yürüyeceğiz' demek. Bu adım küçüktür ama anlam büyüktür. Cesaretinizi toplayın.",

            ("Ay", "Uranüs", "Kavuşum"): "Sürprizler bugün kapınızı çalabilir — belki ani bir karar, belki beklenmedik bir gelişme, belki de partnerinizin size söylediği çok şaşırtıcı bir şey. Bu değişime direnmeyin: Uranüs size yeni bir pencere açıyor. Esnek olun, hayatı kucaklayın.",
            ("Ay", "Uranüs", "Karşıt"): "Özgürlük ihtiyacı bugün biraz gerilim yaratabilir — belki siz çok bağlanmak istiyorsunuz, belki partneriniz biraz alan arıyor. Bu zıtlık doğal: her bireyin kendi ritmi var. Birbirinize alan tanımak, aslında birbirinize daha da yakınlaştıracaktır.",
            ("Ay", "Uranüs", "Kare"): "Ani tartışmalar veya beklenmedik olaylar bugün strese yol açabilir. Ama bu gerginlik geçicidir ve altında büyük bir değişim tohumu yatar. Bugünkü tartışmanız belki de yıllardır ertelediğiniz bir gerçeğin yüzeye çıkmasına vesile olur.",
            ("Ay", "Uranüs", "Trigon"): "Yenilikçi ve yaratıcı bir gün sizi bekliyor — birlikte yeni bir şey deneyin, rutinden çıkın. Belki farklı bir restorana gidin, belki farklı bir rota çizin. Bu küçük macera ilişkinize taze bir soluk getirecektir.",
            ("Ay", "Uranüs", "Sekstil"): "Bugün küçük bir sürpriz ya da beklenmedik bir gelişme ilişkinizi renklendirebilir. Esnek ve açık fikirli olun: beklenmedik olan her şey bugün sizin lehinize çalışıyor.",

            ("Ay", "Neptün", "Kavuşum"): "Manevi derinleşme bugün çok güçlü — birlikte meditasyon yapın, sanatla ilgilenin ya da sadece gözlerinizi kapatıp birbirinizi hissedin. Bu tür anlar, ilişkinin en güzel hazineleridir. Ruhunuz bugün birbiriyle konuşuyor.",
            ("Ay", "Neptün", "Karşıt"): "Yanılsamalarbugün biraz kafa karıştırıcı olabilir — belki partnerinizin söylediği bir şeyi farklı anladınız, belki de kendi hayal gücünüz gerçeği bulanıklaştırdı. Net iletişim bugün çok önemli: 'ben şunu anladım, doğru mu?' diye sormaktan çekinmeyin.",
            ("Ay", "Neptün", "Kare"): "Duygusal bulanıklık bugün hâkim olabilir — ne hissettiğinizi tam bilemiyor, belki de partnerinizin niyetinden emin olamıyorsunuz. Ama bu bulanıklık geçicidir: sakin olun, sabırlı olun, su durulduğunda her şey çok daha net görünecektir.",
            ("Ay", "Neptün", "Trigon"): "Bugün çok romantik ve manevi bir gün — birbirinize olan bağınız çok derin ve güçlü. Bu hissi kucaklayın: belki birlikte bir şarkı dinleyin, belki yıldızlara bakın, belki de sadece sessizce birbirinize sarılın. Bu anlar ruhunuzu besler.",
            ("Ay", "Neptün", "Sekstil"): "Bugün küçük ama derin bir deneyim sizi bekliyor — belki birlikte bir sanat eserine bakarken aynı duyguyu paylaşacaksınız, belki de bir filmin sahnesinde birbirinize bakıp 'aynı şeyi düşünüyoruz' diyeceksiniz. Bu senkronizasyon çok değerli.",

            ("Ay", "Plüton", "Kavuşum"): "Dönüşümbugün çok güçlü — ilişkinizde derin bir değişim yaşanıyor. Belki uzun zamandır bastırdığınız bir duygu bugün yüzeye çıkıyor. Bu yüzleşme korkutucu olabilir ama aynı zamanda çok şifa verici: eskisini yıkarak yeniyi inşa ediyorsunuz.",
            ("Ay", "Plüton", "Karşıt"): "Güç mücadeleleribugün biraz belirgin olabilir — kontrol, güven, bağımlılık konuları gündeme gelebilir. Ama bu yüzleşme bir fırsat: kendinize 'ben nerede kontrolü kaybediyorum?' diye sorun. Cevap, ilişkinizin derinliklerinde sizi bekliyor.",
            ("Ay", "Plüton", "Kare"): "Yoğun duygusal deneyimlerbugün yaşanabilir — eski yaralar, korkular, güvensizlikler yüzeye çıkabilir. Ama bu yüzleşme şifanın başladığı andır: acıya bakabilmek, onu dönüştürebilmek büyük cesaret gerektirir. Bu cesareti gösterin.",
            ("Ay", "Plüton", "Trigon"): "Derin bir dönüşüm bugün ilişkinizi yeniden şekillendiriyor — eski kalıplar kırılıyor, yeni ve daha sağlıklı bir düzen kuruluyor. Bu süreci kucaklayın: değişim korkutucu olabilir ama sonuç, çok daha güçlü bir birliktelik olacak.",
            ("Ay", "Plüton", "Sekstil"): "Bugün küçük ama derin bir değişim yaşanıyor — belki partnerinize daha çok güvenmeye başladınız, belki de kendi duygularınızla daha barışık oldunuz. Bu küçük ilerleme, büyük bir dönüşümün habercisi. Sabırlı olun, meyvelerini toplayacaksınız.",

            # --- GÜNEŞ AÇILARI: Kimlik ve ego etkileşimi ---
            ("Güneş", "Venüs", "Kavuşum"): "Kendinizi bugün çok sevimli ve çekici hissediyorsunuz — partneriniz de bunu fark ediyor. Bu enerjiyi birlikte güzel bir aktiviteye dönüştürün: belki romantik bir akşam yemeği, belki sadece birlikte gülmek. Sevgi bugün çok doğal akıyor.",
            ("Güneş", "Venüs", "Karşıt"): "Kendi ihtiyaçlarınız ile partnerinizin ihtiyaçları arasında bir denge arayışıbugün çok belirgin: belki siz çok şey verirken, partneriniz çok şey alıyor — ya da tam tersi. Bu farkı konuşmak, ilişkinizi çok daha dengeli bir hale getirecektir.",
            ("Güneş", "Venüs", "Kare"): "Değerler ve zevkler konusunda bugün küçük farklılıklar yaşanabilir — belki farklı müzik tarzları, belki farklı tatil planları. Ama unutmayın: farklılıklar ilişkiyi zenginleştirir. Uzlaşmaya açık olun, yeni bir ortak zevk keşfedebilirsiniz.",
            ("Güneş", "Venüs", "Trigon"): "Bugün doğal bir uyum var — partnerinizle aynı dili konuşuyor, aynı şeylere gülüyorsunuz. Bu uyumun tadını çıkarın: ilişki böyle anlarla beslenir. Belki birlikte bir kitap okuyun, bir yürüyüşe çıkın ya da sadece sessizce oturun.",

            ("Güneş", "Mars", "Kavuşum"): "Enerji ve cesaret bugün çok yüksek — birlikte yeni bir maceraya atılmak, cesur adımlar atmak için harika bir zaman. Bu enerjiyi yapıcı kullanın: ortak bir hedefe yönelmek, spor yapmak ya da tutkunuzu paylaşmak bugün çok keyifli olacak.",
            ("Güneş", "Mars", "Karşıt"): "Ego ve öfkebugün biraz tetikte olabilir — her ikiniz de kendi bildiğinizde ısrar edebilirsiniz. Ama bu çatışma bir fırsat: 'ben haklıyım' demek yerine 'sen ne hissediyorsun?' diye sormak, ilişkinizi çok derinleştirebilir.",
            ("Güneş", "Mars", "Kare"): "Sürtünme ve gerilim bugün yaşanabilir — belki planlarınız uyuşmuyor, belki de enerjileriniz çarpışıyor. Ama bu sürtünme sizi güçlendirir: dayanıklılığınızı test eder ve nasıl uzlaşılacağını öğretir. Sabırlı olun.",
            ("Güneş", "Mars", "Trigon"): "Bugün birlikte çok güçlü ve enerjik hissediyorsunuz — ortak hedefler için birleşmek, birlikte bir şeyleri başarmak için mükemmel bir zaman. Bu enerjiyi iyi değerlendirin: birlikte atacağınız adım, uzun veden çok parlak sonuçlar doğurabilir.",

            ("Güneş", "Satürn", "Kavuşum"): "Ciddiyet ve yapı bugün ön planda — ilişkinizde önemli bir adım atma zamanı olabilir. Belki resmi bir karar, belki uzun vadeli bir plan, belki de sadece 'birlikte yürüyeceğiz' demek. Bu adım küçüktür ama temeli çok sağlam atar.",
            ("Güneş", "Satürn", "Karşıt"): "Bugün biraz baskı ve mesafe hissedebilirsiniz — belki partnerinizden beklediğiniz desteği göremiyor, belki de kendi sorumluluklarınız sizi bunaltıyor. Ama bu geçici bir durum: sabırlı olun, bu dönem de geçecek ve geride çok daha güçlü bir ilişki bırakacak.",
            ("Güneş", "Satürn", "Kare"): "Zorlu bir sınavbugün kapınızı çalıyor — sabır, kararlılık ve esneklik gerektiren bir dönemdesiniz. Ama bu sınav sizi olgunlaştırır: dayanıklılığınızı test eder ve 'birlikte zor zamanları aşmanın' değerini öğretir.",
            ("Güneş", "Satürn", "Trigon"): "Olgunluk ve derinleşme bugün çok yakışıyor ilişkinize — birbirinize güveniyor, birbirinize destek oluyorsunuz. Bu güveni besleyin: bugün attığınız adım, yıllar sonra çok sağlam bir temelin üzerine kurulmuş olacak.",
        }

        # Dönem hesaplamalarını al
        donem_verileri = self.secondary_progression_donem_hesapla()

        # Her iki kişi için yorumları oluştur
        for sonuc in sonuclar:
            kisi_donemleri = []
            for dv in donem_verileri:
                if dv["kisi"] == sonuc["kisi"]:
                    kisi_donemleri = dv["donemler"]
                    break

            kisi_yorumlari = []
            for aci in sonuc["ay_acilari"][:5]:  # En önemli 5 Ay açısı
                key = (aci["ilerletilmis"], aci["bagil"], aci["aci"])
                if key in yorum_sozlugu:
                    # Dönem bilgisini bul
                    donem_bilgisi = ""
                    for dk in kisi_donemleri:
                        if (dk["g1"] == aci["ilerletilmis"] and dk["g2"] == aci["bagil"]
                                or dk["g1"] == aci["bagil"] and dk["g2"] == aci["ilerletilmis"]):
                            if dk["aci"] == aci["aci"]:
                                if dk["baslangic"] == dk["bitis"]:
                                    donem_bilgisi = f"📍 {dk['pik']}"
                                else:
                                    donem_bilgisi = f"📅 {dk['baslangic']} — {dk['bitis']}"
                                break

                    kisi_yorumlari.append({
                        "baslik": f"{aci['ilerletilmis']} ({sonuc['ay_burcu']}) → {aci['bagil']} {aci['aci']}",
                        "yorum": yorum_sozlugu[key],
                        "aci_turu": aci["aci"],
                        "etki": aci["etki"],
                        "donem": donem_bilgisi
                    })

            # Genel dönem yorumu
            genel_yorumlari = {
                "Koç": "İlerletilmiş Ay'ınız Koç burcunda — cesaret ve bağımsızlık ön planda. İlişkinizde liderlik almak, inisiyatif kullanmak için güçlü bir dönem. Ama dikkat: acelecilik partnerinizi üzebilir. Tutkunuzu sabırla harmanlayın.",
                "Boğa": "İlerletilmiş Ay'ınız Boğa burcunda — istikrar ve güven arayışınız çok belirgin. İlişkinizde somut adımlar atma, maddi konuları netleştirme zamanı. Değişim korkutucu olabilir ama bu dönem sizi daha sağlam temellere taşıyacak.",
                "İkizler": "İlerletilmiş Ay'ınız İkizler burcunda — iletişim ve merak çok yüksek. Partnerinizle uzun sohbetler, fikir alışverişleri bugün çok keyifli olacak. Ama yüzeysellikten kaçının: derinleşmek için de fırsat var.",
                "Yengeç": "İlerletilmiş Ay'ınız Yengeç burcunda — duygusal derinlik ve aidiyet ihtiyacı çok belirgin. İlişkinizde güvende hissetmek, partnerinize close olmak bugün çok önemli. Geçmişle yüzleşmek, yaraları sarmak için harika bir dönem.",
                "Aslan": "İlerletilmiş Ay'ınız Aslan burcunda — yaratıcılık ve parlama zamanı. İlişkinizde sevginizi göstermek, birlikte eğlenmek, hayatı kutlamak için ideal bir dönem. Ama egonuza çok kapılmayın: partnerinizin de ışığı var.",
                "Başak": "İlerletilmiş Ay'ınız Başak burcunda — detaylar ve mükemmeliyetçilik ön planda. İlişkinizde küçük ama anlamlı düzenlemeler yapmak, alışkanlıkları iyileştirmek için harika bir zaman. Ama eleştirinizi yapıcı tutun.",
                "Terazi": "İlerletilmiş Ay'ınız Terazi burcunda — uyum ve denge arayışınız çok güçlü. İlişkinizde barış, güzellik ve estetik ön planda. Uzlaşmaya açık olun ama kendi ihtiyaçlarınızı da ihmal etmeyin.",
                "Akrep": "İlerletilmiş Ay'ınız Akrep burcunda — yoğunluk ve dönüşüm dönemi. İlişkinizde derinlemesine yüzleşmeler, tutkulu anlar yaşanabilir. Eski yaralar yüzeye çıkabilir ama bu yüzleşme şifanın başladığı andır.",
                "Yay": "İlerletilmiş Ay'ınız Yay burcunda — özgürlük ve macera arayışınız çok belirgin. İlişkinizde yeni ufuklar açmak, birlikte öğrenmek ve keşfetmek için harika bir dönem. Rutinden çıkın, hayatı genişletin.",
                "Oğlak": "İlerletilmiş Ay'ınız Oğlak burcunda — sorumluluk ve yapı kurma ön planda. İlişkinizde uzun vadeli planlar yapmak, ciddi adımlar atmak için ideal bir dönem. Emeklerinizin karşılığını alacaksınız.",
                "Kova": "İlerletilmiş Ay'ınız Kova burcunda — yenilik ve özgünlük çok belirgin. İlişkinizde alışılmadık deneyimler, farklı bakış açıları bugün çok değerli. Sıradanlıktan çıkın, birlikte yeni bir şey keşfedin.",
                "Balık": "İlerletilmiş Ay'ınız Balık burcunda — sezgisellik ve manevi derinleşme çok güçlü. İlişkinizde ruhsal bağ güçleniyor, birbirinizi çok derinden anlayabilirsiniz. Sanat, müzik veya meditasyon bugün çok iyi gelecektir.",
            }
            genel_yorum = genel_yorumlari.get(sonuc["ay_burcu"], f"İlerletilmiş Ay'ınız {sonuc['ay_burcu']} burcunda — dengeli ve uyumlu bir dönemdesiniz.")

            yorumlar.append({
                "kisi": sonuc["kisi"],
                "ilerleme_yili": sonuc["ilerleme_yili"],
                "ay_burcu": sonuc["ay_burcu"],
                "gunes_burcu": sonuc["gunes_burcu"],
                "genel_yorum": genel_yorum,
                "ay_aci_yorumlari": kisi_yorumlari,
                "toplam_aci": len(sonuc["tum_acilar"])
            })

        # İlişki odaklı karşılaştırma yorumu
        if len(yorumlar) >= 2:
            k1 = yorumlar[0]
            k2 = yorumlar[1]

            # Ay burçları uyumu
            burc_gruplari = {
                "ateş": ["Koç", "Aslan", "Yay"],
                "toprak": ["Boğa", "Başak", "Oğlak"],
                "hava": ["İkizler", "Terazi", "Kova"],
                "su": ["Yengeç", "Akrep", "Balık"]
            }

            k1_grup = next((g for g, b in burc_gruplari.items() if k1["ay_burcu"] in b), "")
            k2_grup = next((g for g, b in burc_gruplari.items() if k2["ay_burcu"] in b), "")

            uyum_mesajlari = {
                ("ateş", "ateş"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — aynı element grubundasınız: tutkunuz, cesaretiniz ve enerjiniz birbirini doğal olarak besliyor. Birlikte hayatın tadını çıkarmak için yaratılmışsınız. Ama dikkat: iki ateş bir arada bazen yangın da yaratabilir — sabırlı olun.",
                ("toprak", "toprak"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — toprağın sağlamlığı sizde: istikrar, güven ve somut adımlar bu ilişkinin temeli. Birlikte çok güçlü bir yapı kurabilirsiniz. Ama esnekliği de elden bırakmayın: bazen biraz topraktan kalkıp rüzgara karışmak gerekir.",
                ("hava", "hava"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — zihinsel olarak çok uumlusunuz: sohbetleriniz bitmez, fikirleriniz birbirini besler. Birlikte dünyayı keşfetmek için harika bir ekiptomsunuz. Ama sadece zihinle yetinmeyin: duygularınızı da paylaşın.",
                ("su", "su"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — duygusal derinliğiniz çok güçlü: birbirinizi çok derinden anlıyor, sezgilerinizle bile konuşabiliyorsunuz. Bu ruhsal bağ çok özel. Ama duygusal dalgalanmalara karşı birbirinizi desteklemeyi unutmayın.",
                ("ateş", "hava"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — ateş ve hava çok uyumlu: siz tutku ve enerji getiriyorsunuz, o vizyon ve zekâ. Birlikte çok parlak fikirler üretebilir, büyük hayaller kurabilirsiniz. Bu kombinasyon çok yaratıcı.",
                ("hava", "ateş"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — hava ve ateş çok uyumlu: zihinsel zekânız tutkunuzla buluşuyor. Birlikte hem konuşabilir hem de harekete geçebilirsiniz. Bu denge çok değerli.",
                ("toprak", "su"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — toprak ve su çok besleyici: siz somut bir temel oluşturuyorsunuz, o duygusal derinlik katıyor. Birlikte hem güvenli hem de duygusal bir yuva kurabilirsiniz.",
                ("su", "toprak"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — su ve toprak çok besleyici: duygusal zenginliğiniz somut adımlarla buluşuyor. Birlikte hem hayal kurabilir hem de o hayalleri gerçeğe dönüştürebilirsiniz.",
                ("ateş", "toprak"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — ateş ve toprak zorlu ama değerli bir kombinasyon: siz hız istiyorsunuz, o sabırlı. Bu zıtlık sizi güçlendirir: acelecilikten korur, sabırlı olmayı öğretir.",
                ("toprak", "ateş"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — toprak ve ateş zorlu ama değerli: sabır ve istikrarınız partnerinizin ateşini dengeler. Birlikte hem sağlam hem de tutkulu bir ilişki kurabilirsiniz.",
                ("ateş", "su"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — ateş ve su zorlu ama büyüleyici: siz dışa dönüksünüz, o içe. Bu zıtlık birbirinizi tamamlar ama bazen buhar da yaratır. Sabırlı ve anlayışlı olun.",
                ("su", "ateş"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — su ve ateş zorlu ama büyüleyici: duygusal derinliğiniz partnerinizin enerjisiyle buluşuyor. Birlikte hem tutkulu hem de duygusal bir deneyim yaşayabilirsiniz.",
                ("hava", "toprak"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — hava ve toprak farklı ama tamamlayıcı: siz vizyon getiriyorsunuz, o uygulama. Birlikte büyük projeleri hayata geçirebilirsiniz.",
                ("toprak", "hava"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — toprak ve hava farklı ama tamamlayıcı: somut adımlarınız zihinsel zekânızla buluşuyor. Birlikte hem hayal kurabilir hem de o hayalleri inşa edebilirsiniz.",
                ("hava", "su"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — hava ve su zorlu ama zenginleştirici: siz mantığa, o duyguya önem veriyorsunuz. Bu denge çok değerli: birbirinize farklı pencerelerden bakmayı öğretirsiniz.",
                ("su", "hava"): f"{k1['ay_burcu']} ve {k2['ay_burcu']} — su ve hava zorlu ama zenginleştirici: duygusal derinliğiniz zihinsel berraklıkla buluşuyor. Birlikte hem hissedebilir hem de anlayabilirsiniz.",
            }
            uyum_key = (k1_grup, k2_grup)
            uyum_mesaji = uyum_mesajlari.get(uyum_key, f"{k1['ay_burcu']} ve {k2['ay_burcu']} — farklı elementlerden gelmeniz zenginlik katacak. Farklılıklarınız en büyük gücünüz olacak.")

            yorumlar.append({
                "kisi": "İlişki Uyumu",
                "ilerleme_yili": 0,
                "ay_burcu": "",
                "gunes_burcu": "",
                "genel_yorum": uyum_mesaji,
                "ay_aci_yorumlari": [],
                "toplam_aci": 0,
                "karsilastirma": True
            })

        return yorumlar

    def gunluk_bsp_taramasi(self, gun_sayisi=30, pdf_icin=False):
        import datetime
        import swisseph as swe
        import random
        
        # --- BSP SÖZLÜĞÜ: MODA GÖRE SEÇİM ---
        aktif_mod = getattr(self, 'mod', 'es_sevgili')
        
        if aktif_mod == "ebeveyn_cocuk":
            bsp_sozlugu = {
                "Güneş_0": [
                    "Kimlik Yenilenmesi: Çocuğun benlik algısı bugün güçlü bir şekilde ortaya çıkıyor. Somut: Onunla birlikte yeni bir hobie veya aktiviteye başlamak için harika bir gün. Soyut: Çocuğun 'ben kimim' sorusuna cevap aradığı gelişim anı.",
                    "Ego Parlaması: Çocuk bugün dikkatleri üzerine çekmek istiyor. Somut: Başarılarını kutlayın, övgünüzü eksik etmeyin. Soyut: Ebeveynin onayının çocuk için ne kadar kritik olduğunu gösteren kozmik bir an.",
                    "Canlanma Vakti: Çocuğun enerji seviyesi çok yüksek. Somut: Dışarı çıkın, koşun, oynayın — enerjisini sağlıklı boşaltmasına yardım edin. Soyut: Yaşam enerjisinin_CHILD_üzerinde coşkuyla aktığı büyüme anı.",
                    "Ortak Vizyon: Birlikte geleceğe dair güzel planlar yapabileceğiniz bir gün. Somut: Birlikte bir hedef belirleyin veya hayal kurun. Soyut: Ebeveyn ve çocuğun vizyonlarının kaderde hizalandığı özel an."
                ],
                "Güneş_60": [
                    "İrade Uyumu: Ebeveyn ve çocuk arasında doğal bir uyum var. Somut: Ortak kararlar almak bugün çok kolay. Soyut: Rehberlik ve bağımsızlığın dengelendiği yapıcı pencere.",
                    "Destekleyici Akış: Günün akışı anne/baba ve çocuk için çok yumuşak ilerliyor. Somut: Birlikte yapacağınız küçük aktiviteler büyük mutluluklar yaratabilir. Soyut: Ebeveyn desteğinin çocukta güvenle karşılık bulduğu zaman.",
                    "Tatlı Fırsatlar: Çocuğunuz için güzel bir sürpriz yapma zamanı. Somut: Beklenmedik bir hediye veya aktivite planı keyifli anlar yaratabilir. Soyut: Evrenin ebeveyn-çocuk bağını desteklediği yeşil ışık.",
                    "Yumuşak Geçiş: Gergin bir dönemden çıkıyorsanız bugün rahat bir nefes alma zamanı. Somut: Birlikte sakin bir aktivite yapın, sohbet edin. Soyut: Sabır ve anlayışın meyvelerini topladığınız huzurlu gün."
                ],
                "Güneş_90": [
                    "Ego Sınavı: Çocuğun 'ben istiyorum' talepleri bugün zorlayıcı olabilir. Somut: Sabırlı olun, sınır koymakla dinlemek arasında denge kurun. Soyut: Ebeveyn otoritesi ile çocuğun bireyselliği arasındaki kadersel test.",
                    "İrade Sürtünmesi: Anne/baba ile çocuk arasında fikir ayrılıkları yaşanabilir. Somut: Tartışmadan önce 'neden?' diye sorarak çocuğun iç dünyasını anlamaya çalışın. Soyut: Ebeveyn rehberliğinin esnekliğinin test edildiği gelişim anı.",
                    "Kışkırtıcı Ayna: Çocuğunuzun tavrı sizi kızdırabilir. Somut: Onun davranışında kendi çocukluk deneyimlerinizi görebilirsiniz — sakin kalın. Soyut: Ebeveynin kendi içsel yolculuğunu çocuğun aynasından gördüğü kadersel an.",
                    "Sabir Testi: Disiplin konusunda zorlandığınız saatler. Somut: Kuralları net ama sevgi dolu bir dille açıklayın. Soyut: Ebeveyn ile çocuk arasındakiPOWER dinamiğinin yeniden dengelendiği sınav anı."
                ],
                "Güneş_120": [
                    "Zahmetsiz Parlama: Çocuğunuz bugün parlak bir şekilde parlıyor. Somut: Yeteneklerini sergilemesine fırsat verin, gurur duyacaklarınız var. Soyut: Çocuğun potansiyelinin ebeveyn desteğiyle özgürce aktığı zahmetsiz büyüme.",
                    "Ruhsal Ziyafet: Birlikte geçirdiğiniz her an bugün çok kıymetli. Somut: Birlikte kitap okuyun, sohbet edin veya yürüyüşe çıkın. Soyut: Ebeveyn ve çocuğun ruhsal olarak birbirini beslediği şifa anı.",
                    "Şanslı Gün: Her ikiniz için de çok keyifli bir gün. Somut: Çocuğunuzla birlikte gülün, eğlenin, hayatı kutlayın. Soyut: Ebeveyn-çocuk bağının evrensel olarak kutsandığı altın saatler.",
                    "İlahi Senkronizasyon: Birbirinizi bugün çok iyi anlıyorsunuz. Somut: Aynı şeyleri düşünüp aynı anda gülebilirsiniz — bu bağı takdir edin. Soyut: Ebeveyn ve çocuğun kozmik titresimta hizalandığı mucizevi an."
                ],
                "Güneş_180": [
                    "Kutuplaşma Sınavı: Siz ve çocuğunuz bugün tamamen zıt kutuplarda olabilirsiniz. Somut: 'Haklıymışım' demek yerine 'seni anlamak istiyorum' deyin. Soyut: Ebeveyn ile çocuğun birbirinin gölgesini yansıttığı gelişim aynası.",
                    "Tahterevalli Dengesi: Siz çok ciddiyken çocuk şen, veya tam tersi olabilir. Somut: Birinizin enerjisine diğerinin uyum sağlaması gereken bir denge anı. Soyut: Ebeveyn-çocuk arasındaki ritim farkının test edildiği kadersel viraj.",
                    "Çekim ve İtiş: Çocuğunuza hem çok yakın hem çok uzak hissedebilirsiniz. Somut: Mesafe koymak ile sarılmak arasındaki doğru anı hissedin. Soyut: Bağlanma ile bağımsızlığın kadersel dengesinin sınandığı an.",
                    "Karşı Cephe: Çocuğunuz sizin otoritenize meydan okuyabilir. Somut: Bu bir isyan değil, kimlik arayışıdır — sınırlarınızı korurken onu da dinleyin. Soyut: Ebeveyn otoritesinin çocuğun bireyselliğiyle yüzleştiği kadersel an."
                ],

                "Merkür_0": [
                    "Telepatik Zihin: Çocuğunuzla bugün harika bir iletişim kurabilirsiniz. Somut: Onunla uzun ve derin bir sohbet yapın, ne düşündüğünü dinleyin. Soyut: Ebeveyn ve çocuğun zihinsel titresimlarının tam hizalandığı an.",
                    "Zihinsel Bütünlük: Birlikte önemli bir kararı çok kolay konuşup çözebilirsiniz. Somut: Çocuğun fikrini alın, ortak bir yol bulun. Soyut: İki zihnin tek bir süper-bilgisayar gibi çalıştığı pedagojik an.",
                    "Fikirsel Kıvılcım: Çocuğunuzun yaratıcılığı bugün çok yüksek. Somut: Birlikte bir proje veya sanat aktivitesi yapın. Soyut: Çocuğun zihinsel potansiyelinin ebeveyn desteğiyle kıvılcımlandığı aydınlanma.",
                    "Pürüzsüz İletişim: Yanlış anlaşılmaların buharlaştığı bir gün. Somut: Zor konuları bile bugün rahatça konuşabilirsiniz. Soyut: Anlaşma ve anlama ihtiyacının zihinsel olarak tam karşılandığı döngü."
                ],
                "Merkür_90": [
                    "İletişim Darboğazı: Söylenenler ters anlaşılabilecek bir gün. Somut: Sözlerinizi çok dikkat seçin, çocuğun zihninden düşünmeye çalışın. Soyut: Zihinsel titresimların çatıştığı kadersel 'dinleme' sınavı.",
                    "Sözsel Gerilim: Tartışmalar kolayca alevlenebilir. Somut: Ses tonunuza dikkat edin, dinlemeyi konuşmaya tercih edin. Soyut: Ebeveyn ve çocuk arasındaki iletişim köprüsünün kadersel bakım onarımı.",
                    "Yanlış Anlama: Çocuğunuz şaka yaptığınızı ciddiye alabilir veya tam tersi. Somut: Bugün net ve açık olun, ima yapmaktan kaçının. Soyut: Evren size 'bugün konuşmak yerine sadece dinle' mesajı veriyor.",
                    "Mantık Çatışması: Günlük planlar birbirine uymayabilir. Somut: Esnek olun, planları birlikte yeniden düzenleyin. Soyut: Ortak iletişim mekanizmanızın kadersel bakım onarımı."
                ],
                "Merkür_120": [
                    "Kusursuz Diyalog: Zor bir konuyu bugün masaya yatırmak için mükemmel zaman. Somut: Çocuğunuzla önemli bir konuyu rahatça konuşabilirsiniz. Soyut: Ebeveyn ve çocuk arasındaki iletişim kanalının pırıl pırıl açıldığı an.",
                    "Entelektüel Dans: Birlikte kitap okuyun, film tartışın veya derin sohbetler yapın. Somut: Çocuğun zihinsel dünyasını keşfetmek için harika bir gün. Soyut: Zihinsel olarak birbirini derinden besleyen şifa uyumı.",
                    "Ortak Bağ: Çocuğunuz ne diyeceğinizi o daha söylemeden anlayabilir. Somut: Bu özel bağı ve anlayışı kutlayın. Soyut: Zihinlerin evrensel uyumla birbirini yatıştırdığı gün.",
                    "Sözlerin Şifası: Çocuğunuzla ilgili endişelerinizi bugün rahatça paylaşabilirsiniz. Somut: Onunla empati kurarak duygusal bir köprü kurun. Soyut: İletişim kanalının şifayla dolduğu, güvenin pekiştiği döngü."
                ],
                "Merkür_180": [
                    "Fikir Düellosu: Siz ve çocuğunuz bugün çok farklı bakış açılarına sahip olabilirsiniz. Somut: Farklılıklarınızı çatışma değil zenginlik olarak görün. Soyut: Farklı perspektiflerin masaya yatırıldığı kadersel fırtına.",
                    "Zıt Bakışlar: Aynı olaya tamamen farklı açılardan bakabilirsiniz. Somut: Çocuğunuzun bakış açısını anlamaya çalışın, eleştirmeden dinleyin. Soyut: Birbirinin karar alma mekanizmasındaki açıkları gösteren gelişim aynası.",
                    "Sorgulama Fazı: Çocuğunuzun kararlarını today çok eleştirel değerlendirebilirsiniz. Somut: Eleştirinizi yapıcı ve destekleyici bir dille ifade edin. Soyut: Ebeveyn beklentileri ile çocuğun bireyselliği arasındaki test anı.",
                    "Gerilimli Müzakere: Ev ödevi, kurallar veya sorumluluklar konusunda tartışabilirsiniz. Somut: Kuralları birlikte koyun, çocuğun da fikrini alın. Soyut: İki dünyanın uzlaşmak için kadersel masaya oturduğu zorunlu toplantı."
                ],

                "Venüs_0": [
                    "Sevginin Mührü: Bugün birbirinize karşı çok şefkatli ve sevgi dolusunuz. Somut: Sarılın, öpün, 'seni seviyorum' deyin — sevginizi fiziksel olarak gösterin. Soyut: Ebeveyn ve çocuk arasındaki sevgi bağının kozmik olarak mühürlendiği gün.",
                    "Cazibe Zirvesi: Çocuğunuzun bugün çok çekici ve sevecen bir enerjisi var. Somut: Bu enerjiyi birlikte bir aktiviteye dönüştürün. Soyut: Ebeveyn-çocuk bağının sevgiyle yenilendiği faz.",
                    "Koşulsuz Uyum: Bugün aranızda kavga veya gerginlik olma ihtimali çok düşük. Somut: Bu huzurlu anın tadını çıkarın, birlikte güzel şeyler yapın. Soyut: Evrenin ebeveyn-çocuk sevgisini kutsadığı kadersel uyanış.",
                    "Tatlı Çekim: Çocuğunuzla birlikte güzelleşmek, estetik aktiviteler yapmak için harika zaman. Somut: Birlikte resim yapın, müzik dinleyin veya doğa yürüyüşüne çıkın. Soyut: Sevgi titresimının ebeveyn-çocuk bağının tam merkezine yerleştiği an."
                ],
                "Venüs_90": [
                    "Değer Sınavı: Çocuğunuz bugün kendini değersiz hissedebilir. Somut: Onu koşulsuz sevdiğinizi defalarca söyleyin, somut örnekler verin. Soyut: Çocuğun içsel 'sevilmeme korkusunun' yüzeye çıktığı gelişim anı.",
                    "Duygusal Susuzluk: Çocuğunuz bugün ekstra sevgi ve ilgi talep edebilir. Somut: Bu bir şımarıklık değil, içsel bir ihtiyacı. Sabırla karşılayın. Soyut: Ebeveyn sevgisinin yoğun bir şekilde ihtiyaç duyulduğu kadersel gün.",
                    "Estetik Çatışma: Giyinme, görünüm veya zevkler konusunda anlaşmazlık yaşanabilir. Somut: Çocuğunuzun zevklerine saygı duyun, rehberlik edin ama baskı yapmayın. Soyut: Ebeveyn beğentisi ile çocuğun bireysel zevki arasındaki kadersel test.",
                    "Tutku Darboğazı: Çocuğunuz bugün çok duygusal ve alıngan olabilir. Somut: Onunla sabırla ve şefkatle ilgilenin, duygularını onaylayın. Soyut: Duygusal ihtiyaçların kadersel olarak yüzeye çıktığı hassas saatler."
                ],
                "Venüs_120": [
                    "Koşulsuz Çekim: Bugün çocuğunuzla aranızdaki sevgi çok doğal ve güçlü akıyor. Somut: Hiçbir çaba harcamadan mutluluğu yakalayacağınız yumuşak bir gün. Soyut: Ebeveyn ve çocuk arasındaki sevginin kendiliğinden aktığı eşsiz titresim.",
                    "Romantik Akış: (Ebeveyn-çocuk bağında) Sevginizi dile getirmek, sarılmak, göz göze gelmek için harika zaman. Somut: Küçük sevgi jestleri bugün çok etkili olacak. Soyut: Bağın şifayla dolduğu, aidiyetin tavan yaptığı kozmik an.",
                    "Tatlı Huzur: Ortak bir aktivite yaparak huzurun tadını çıkarın. Somut: Birlikte müzik dinleyin, yemek yapın veya bahçede vakit geçirin. Soyut: Kalplerin senkronize attığı, dış streslerin sevgi duvarından sektiği gün.",
                    "Güzellik Ritmi: Bugün çocuğunuzla birlikte olduğunuz her ortam güzelleşiyor. Somut: Birlikte sosyal ortamlara katılın, birlikte parlayın. Soyut: Ebeveyn-çocuk bağının güzellik ve bereket enerjisiyle yıkandığı lütuf anı."
                ],
                "Venüs_180": [
                    "Sevgi İhtiyacı: Çocuğunuz bugün fazladan sevgiye ihtiyaç duyabilir. Somut: Onu ne kadar sevdiğinizi somut davranışlarınızla gösterin. Soyut: Ebeveyn sevgisi ile çocuğun ihtiyaç duyduğu güven arasındaki denge testi.",
                    "Beklenti Kutuplaşması: Çocuğunuz sizden çok şey beklerken, siz ona sınırlar koymaya çalışıyor olabilirsiniz. Somut: Beklentilerinizi açıkça konuşun, çocuğun beklentilerini de dinleyin. Soyut: Ebeveyn kısıtlamaları ile çocuğun sevgi ihtiyacı arasındaki kadersel gerilim.",
                    "Soğuk Ayna: Bugün duygusal olarak birbirinize mesafeli kalabilirsiniz. Somut: Mesafeyi kapatmak için inisiyatif alın, sarılın. Soyut: Ebeveyn-çocuk arasındaki duygusal mesafenin kadersel olarak test edildiği an.",
                    "Tutku Tahterevallisi: Çocuğunuz bugün duygusal olarak çok inişli çıkışlı olabilir. Somut: Sabırlı olun, duygusal dalgalanmaları normal karşılayın. Soyut: Çocuğun duygusal gelişim sınırlarının kadersel olarak test edildiği gün."
                ],

                "Mars_0": [
                    "Tutku ve Eylem: Çocuğunuzun enerji seviyesi bugün çok yüksek. Somut: Birlikte spor yapın, koşun, oyun oynayın. Soyut: Ebeveyn ve çocuğun birlikte eyleme geçtiği yapi gün.",
                    "Volkanik Enerji: Çocuğunuzda bugün muazzam bir enerji var. Somut: Bu enerjiyi yaratıcı bir projeye yönlendirin. Soyut: Ebeveyn ve çocuğun enerjilerinin birleşip güçlü bir ittifak oluşturduğu an.",
                    "Cesaretin Doğuşu: Çocuğunuz bugün cesur ve girişken. Somut: Yeni bir şey denemesi için onu destekleyin, yüreklendirin. Soyut: Çocuğun cesaretinin ebeveyn desteğiyle parlakça yandığı büyüme anı.",
                    "Hızlı ve Öfkeli: Enerji yüksek ama sabır düşük olabilir. Somut: Sabırsızlığına karşı sabırlı olun, enerjisini doğru kanala yönlendirin. Soyut: Ebeveyn rehberliğinin çocuğun ham enerjisini şekillendirdiği pedagojik an."
                ],
                "Mars_90": [
                    "Ateş Çemberi: Çocuğunuz bugün kolayca kızabilir veya sinirlenebilir. Somut: Onun öfkesini yargılamadan dinleyin, nefes alma tekniklerini öğretin. Soyut: Çocuğun öfke yönetimi becerisinin kadersel olarak test edildiği gelişim sınavı.",
                    "Buyuk Sinav: Ebeveyn ve çocuk arasında sert tartışmalar yaşanabilir. Somut: Seslerinizi yükseltmeyin, sakin kalın — siz model olun. Soyut: Ebeveyn sabrının ve çocuğun öfke kontrolünün test edildiği sınav anı.",
                    "Sürtünme ve Kriz: Kurallar ve bağımsızlık arasındaki çatışma tırmanabilir. Somut: Sınırı koruyun ama Empatiyi de elden bırakmayın. Soyut: Ebeveyn otoritesi ile çocuğun isyan enerjisi arasındaki kadersel yüzleşme.",
                    "Sabır Testi: Çocuğunuzun davranışları today sizi çok zorlayabilir. Somut: Derin nefes alın, 'bu da geçecek' diye hatırlatın. Soyut: Ebeveyn sabrının en büyük sınavlarından birini verdiği hassas an."
                ],
                "Mars_120": [
                    "Yenilmez İttifak: Bugün anne/baba ve çocuk olarak çok güçlü bir takımsınız. Somut: Birlikte zor bir işin üstesinden gelin, takım ruhunuzu gösterin. Soyut: Ebeveyn ve çocuğun tek yürek olduğu ilahi faz.",
                    "Eylem Akışı: Fiziksel olarak çok uyumlusunuz. Somut: Birlikte spor yapın, yürüyüşe çıkın, enerjinizi birlikte harcayın. Soyut: Ebeveyn-çocuk eylem motorunun hiç teklemeden çalıştığı üretim ve enerji zirvesi.",
                    "Takim Calismasi: Çocuğunuzun eksik kalan enerjisini siz tamamlıyorsunuz. Somut: Birbirinizi destekleyerek harika işler başarabilirsiniz. Soyut: Evrenin ebeveyn-çocuk bağına 'engelleri aşma' kalkanı verdiği uyum.",
                    "Hızlı Senkronizasyon: Ortak kararlar bugün çok hızlı uygulamaya geçiyor. Somut: Birlikte bir plan yapın ve hemen başlayın —timing mükemmel. Soyut: Ebeveyn ve çocuğun eylem dilinde tam uyumda olduğu kadersel an."
                ],
                "Mars_180": [
                    "Büyük Düello: Siz ve çocuğunuz bugün sert tartışmalara girebilirsiniz. Somut: Öfkenizi çocuğunuza değil, soruna yönelin. Soyut: Ebeveyn ile çocuğun güç sınırlarının en sert kutuplaştığı kadersel sınav.",
                    "Güç Savaşı: 'Benim dediğim olacak' restleşmeleri yaşanabilir. Somut: Otorite ile demokrasi arasında denge kurun — sınırlar koyun ama dinleyin. Soyut: Ebeveyn otoritesinin çocuğun bireyselliğiyle savaştığı kadersel an.",
                    "Kutuplaşan İrade: Siz ve çocuğunuzbugün çok farklı hızlarda hareket edebilirsiniz. Somut: Çocuğunuzun ritmine saygı duyun, acele ettirmeyin. Soyut: Farklı eylem ritimlerinin kadersel olarak test edildiği denge anı.",
                    "Zıt Ritimler: Siz çok hızlıyken çocuk yavaş, veya tam tersi olabilir. Somut: Ortak bir tempo bulun, birbirinize uyum sağlayın. Soyut: Ebeveyn ve çocuk arasındaki ritim farkının kadersel aynası."
                ],

                "Satürn_0": [
                    "Karmik Köklenme: Bugün ciddi ve sorumluluk odaklı bir gün. Somut: Çocuğunuza önemli bir sorumluluk verin, güvenin. Soyut: Ebeveyn-çocuk arasındaki sorumluluk paylaşımının mühürlendiği köklenme anı.",
                    "Temel İnşası: Geleceğe dair somut planlar yapmak için harika bir gün. Somut: Birlikte bir hedef belirleyin ve adım adım planlayın. Soyut: Ebeveyn-çocuk yapısının görünmez kolonlarının güçlendirildiği faz.",
                    "Sorumluluk Fazı: Bugün sorumluluklar ve kurallar ön planda. Somut: Çocuğunuza disiplin ve düzenin önemini sevgiyle öğretin. Soyut: Ebeveynin çocuğa yaşam dersi verdiği pedagojik disiplin günü.",
                    "Kalıcı Mühür: Verdiğiniz sözlerin bugün çok güçlü bir etkisi var. Somut: Çocuğunuza verdiğiniz sözleri tutun, güven inşa edin. Soyut: Ebeveyn-çocuk güveninin kadersel olarak mühürlendiği kritik an."
                ],
                "Satürn_90": [
                    "Yapısal Direnç: Çocuğunuz bugün disiplin ve kurallara karşı direnç gösterebilir. Somut: Kuralların nedenlerini açıklayın, baskıyla değil anlayışla yaklaşın. Soyut: Ebeveyn disiplini ile çocuğun bağımsızlık ihtiyacı arasındaki yapısal sınav.",
                    "Yetersizlik Sınavı: Kendinizi yetersiz bir ebeveyn hissedebilirsiniz. Somut: Mükemmel olmak zorunda değilsiniz — samimiyet yeterli. Soyut: Ebeveynlik yetkinliğinizin kadersel olarak test edildiği gelişim anı.",
                    "Karmik Duvar: Çocuğunuzla aranızda bugün görünmez bir duvar olabilir. Somut: Bu duvarı şefkatle yıkın, onayakın olun. Soyut: Ebeveyn-çocuk arasındaki duygusal mesafenin kadersel yüzleşmesi.",
                    "Görev Yorgunluğu: Ebeveynlik görevlerinden yorulduğunuz bir gün olabilir. Somut: Kendinize de zaman ayırın, destek istemekten çekinmeyin. Soyut: Ebeveynlik yükünün kadersel olarak tartıldığı hassas an."
                ],
                "Satürn_120": [
                    "Sarsılmaz Liman: Bugün çocuğunuz için güçlü bir liman olduğunuzu hissediyorsunuz. Somut: Ona güvende olduğunu hissettirin, destek olun. Soyut: Ebeveynin çocuğu için güvenli bir liman olduğu gerçeğinin kozmik onaylanması.",
                    "Güven Duvarı: Saygı ve bağlılık bugün çok güçlü. Somut: Birbirinize olan güveninizi somut davranışlarla pekiştirin. Soyut: Ebeveyn-çocuk güven duvarının köklü ve sağlam olduğu onaylayan şifa.",
                    "Ağırbaşlı Aşk: Büyük sözlere gerek yok, sadece yan yana olmanız bile yeterli. Somut: Sessizce birlikte vakit geçirin, bu bile çok değerli. Soyut: Zamanın ebeveyn-çocuk bağını yıpratmadığı, aksine güçlendirdiği an.",
                    "Ortak Disiplin: Kurallar ve sorumluluklar bugün çok uyumlu işliyor. Somut: Çocuğunuz kurallara gönüllü uyuyor — bunu takdir edin. Soyut: Ebeveyn disiplininin çocuğun içselleştirdiği kadersel uyum anı."
                ],
                "Satürn_180": [
                    "Otorite Çarpışması: Siz ve çocuğunuzbugün otorite konusunda çatışabilirsiniz. Somut: 'Büyükler así yapar' değil, 'birlikte böyle karar verdik' dilini kullanın. Soyut: Ebeveyn otoritesinin çocuğun bireyselliğiyle çarpıştığı kadersel an.",
                    "Mesafe Sınavı: Siz çok sıcakken çocuk mesafeli, veya tam tersi olabilir. Somut: Mesafeye rağmen sevginizi göstermeye devam edin. Soyut: Ebeveyn-çocuk arasındaki duygusal mesafenin kadersel olarak test edildiği viraj.",
                    "Katı Duvarlar: Kurallar bugün çok katı hissedilebilir. Somut: Kuralların esnek yanlarını da gösterin, çocuğu bunaltmayın. Soyut: Ebeveyn disiplini ile sevgi arasındaki dengenin kadersel yüzleşmesi.",
                    "Sorumluluk Yükü: Ebeveynlik yükünün tamamen sizin omuzlarınızda olduğu hissine kapılabilirsiniz. Somut: Yardım isteyin, paylaşın. Soyut: Ebeveynlik sorumluluklarının kadersel olarak yeniden dağıtıldığı hassas denge anı."
                ],

                "Jüpiter_0": [
                    "İlahi Lütuf: Bugün çok şanslı ve bereketli bir gün. Somut: Çocuğunuzla birlikte kutlama yapın, sevincinizi paylaşın. Soyut: Ebeveyn-çocuk bağının evrensel bereketle dolduğu ilahi an.",
                    "Genişleyen Ufuk: Çocuğunuzun ufkunun bugün çok genişlediğini göreceksiniz. Somut: Yeni deneyimler ve öğrenme fırsatları sunun. Soyut: Çocuğun gelişiminin ebeveyn desteğiyle genişlediği kozmik genişleme.",
                    "Ortak İnanç: Her ikiniz de geleceğe dair güçlü bir umut taşıyorsunuz. Somut: Bu umudu birlikte bir plana dönüştürün. Soyut: Ebeveyn-çocuk arasındaki inanç bağının tazelendiği özel kalkan.",
                    "Abartılı Neşe: Bugün fazla neşeli ve coşkulu olabilirsiniz. Somut: Bu enerjiyi doğru yönlendirin, sınırlarınızı da koruyun. Soyut: Ebeveyn-çocuk neşesinin taştığı, kozmik bereketin aktığı gün."
                ],
                "Jüpiter_90": [
                    "Beklenti Yanılsaması: Çocuğunuz bugün fazla büyük beklentilere girebilir. Somut: Gerçekçilik öğretin ama hayallerini de öldürmeyin. Soyut: Ebeveynin gerçekçiliği ile çocuğun hayal gücü arasındaki kadersel sınav.",
                    "Aşırı Özgüven: Çocuğunuz bugün aşırı özgüvenli olabilir. Somut: Cesaretini destekleyin ama gerçekçi sınırları da hatırlatın. Soyut: Çocuğun özgüveninin kadersel olarak dengelendiği test anı.",
                    "Şımarıklık Testi: Çocuğunuz bugün fazla talepkar olabilir. Somut: 'Hayır' demeyi sevgiyle öğrenin, sınırlar koyun. Soyut: Ebeveynin cömertliği ile sınır koyma ihtiyacı arasındaki denge testi.",
                    "Felsefi Çatışma: İnançlar ve değerler konusunda tartışabilirsiniz. Somut: Çocuğunuzun farklı bakış açısına saygı duyun. Soyut: Ebeveyn değerleri ile çocuğun bireysel inanç sistemi arasındaki kadersel yüzleşme."
                ],

                "Uranüs_0": [
                    "Elektrikli Uyanış: Bugün çok sürprizli ve heyecan verici bir gün olabilir. Somut: Çocuğunuzun sıra dışı fikirlerine açık olun, destekleyin. Soyut: Ebeveyn-çocuk rutininin kozmik bir şokla tazelandığı devrim anı.",
                    "Sıra Dışı Çekim: Çocuğunuz bugün çok yaratıcı ve yenilikçi. Somut: Fikirlerini ciddiye alın, birlikte deneyin. Soyut: Kalıpların yıkıldığı, çocuğun potansiyelinin yeni bir boyuta açıldığı 'evreka' anı.",
                    "Zincirleri Kırmak: Çocuğunuz bugün kuralları sorgulayabilir. Somut: Bu bir isyan değil, sorgulama yeteneğinin gelişimidir — destekleyin. Soyut: Özgürlüğün ve bireyselliğin ebeveyn-çocuk bağına zarar vermeden entegre edildiği uyanış.",
                    "Sürpriz Rota: Beklenmedik bir gelişmenin yaşanabileceği bir gün. Somut: Çocuğunuzun sürprizlerine hazır olun, esnek davranın. Soyut: Kadersel monotonluğun evrenin şimşekleriyle parçalandığı ve bağın nefes aldığı döngü."
                ],
                "Uranüs_90": [
                    "Özgürlük İsyanı: Çocuğunuz bugün aşırı bağımsızlık talep edebilir. Somut: Bağımsız alanlar verin ama sınırları da koruyun. Soyut: Çocuğun özgürlük ihtiyacı ile ebeveyn kontrolü arasındaki kadersel gerilim.",
                    "Ani Yıkım Güdüsü: Çocuğunuz bugün ani ve öngörülemez davranışlar sergileyebilir. Somut: Sabırlı olun, provokasyona kapılmayın. Soyut: Ebeveyn-çocuk düzeninin ani değişimlerle test edildiği sınav anı.",
                    "Elektrik Yüklü Kriz: Ani tartışmalar veya beklenmedik tepkiler yaşanabilir. Somut: Sakin kalın, fevri kararlardan kaçının — siz model olun. Soyut: Ebeveyn-çocuk yapısının şiddetle sarsıldığı, sabır ve anlayışın test edildiği kırmızı alarm.",
                    "Mesafe Kopuşu: Çocuğunuz bugün size çok uzak hissedebilir. Somut: Bu geçici bir durum — üstüne gitmeyin, bekleyin. Soyut: Ebeveyn-çocuk sürekliliğindeki geçici ayrışmanın kadersel yüzleşmesi."
                ],

                "Neptün_0": [
                    "Ruhsal Simya: Bugün çok duygusal ve manevi bir gün. Somut: Birlikte hayal kurun, sanat yapın veya sadece sarılın. Soyut: Ebeveyn ve çocuk arasındaki empati ve ruhsal kenetlenmenin zirve yaptığı gün.",
                    "İlahi Çözülme: Affetmenin çok kolay olduğu bir gün. Somut: Eski kırgınlıkları bırakın, temiz bir sayfa açın. Soyut: Ebeveyn-çocuk arasındaki duygusal yüklerin kozmik olarak yıkandığı şifa anı.",
                    "Telepatik Teslimiyet: Çocuğunuzun ne hissettiğini bugün çok daha iyi anlayabiliyorsunuz. Somut: Bu empati yeteneğinizi onunla derin bir bağ kurmak için kullanın. Soyut: Ebeveyn ve çocuğun ruhsal olarak birbirine ilahi pamuk ipliğiyle bağlandığı masal saati.",
                    "Tatlı İllüzyon: Bugün her şey çok güzel ve pembe görünebilir. Somut: Bu güzel anın tadını çıkarın ama gerçekleri de göz ardı etmeyin. Soyut: Evrenin ebeveyn-çocuk bağına sunduğu rüya molası."
                ],
                "Neptün_90": [
                    "Sis Perdesi: Bugün yanlış anlaşılmalar olabilir. Somut: Çocuğunuzun sözlerini çok dikkat dinleyin, varsayım yapmayın. Soyut: Gerçeklerin çarpıtılabildiği gün — bugün büyük kararlar almaktan kaçının.",
                    "Kurban Psikolojisi: 'Ben senin için her şeyimi verdim' hissine kapılabilirsiniz. Somut: Fedakarlığınızın sınırlarını koruyun, tükenmişlikten kaçının. Soyut: Ebeveynin fedakarlığı ile sınırları arasındaki kadersel test.",
                    "Hayal Kırıklığı Sınavı: Çocuğunuzun gerçekliği ile hayalleriniz örtüşmeyebilir. Somut: Onu olduğu gibi kabul edin, idealize etmeyi bırakın. Soyut: Ebeveyn beklentileri ile çocuğun gerçek potansiyeli arasındaki kadersel uyanış.",
                    "Kaçış Eğilimi: Sorunları görmezden gelme isteği bugün çok güçlü olabilir. Somut: Kaçmak yerine yüzleşin, destek alın. Soyut: Ebeveyn-çocuk bağının karanlık sularında kaybolma hissinin kadersel yüzleşmesi."
                ],

                "Plüton_0": [
                    "Küllerinden Doğuş: Bugün çok derin ve dönüştürücü bir deneyim yaşanabilir. Somut: Çocuğunuzun derin duygularına kulak verin, onu anladığınızı hissettirin. Soyut: Ebeveyn-çocuk arasındaki derin dönüşümün kozmik olarak gerçekleştiği simyasal gün.",
                    "Hipnotik Çekim: Bugün çocuğunuzla aranızdaki bağ çok derin ve güçlü. Somut: Bu derin bağı hissedin ve takdir edin. Soyut: Ruhların en derin dehlizlerde bile birbirini tanıyıp kucakladığı ebeveyn-çocuk mührü.",
                    "Dönüştürücü Güç: Ortak bir zorluğun üstesinden muazzam bir güç birliğiyle gelebilirsiniz. Somut: Birlikte zorlukların üstesinden gelin, bu deneyimden büyüyerek çıkın. Soyut: Ebeveyn-çocuk bağının deri değiştirdiği, eski toksik kalıpların ölüp güçlü bir bağın doğduğu faz.",
                    "Sessiz İttifak: Bugün birbirinizi sadece göz temasıyla anlayabileceğiniz özel bir an olabilir. Somut: Bu sessiz anları değerli kılın,acele etmeyin. Soyut: Ebeveyn ve çocuğun ruhsal olarak tek vücut olduğu mistik gün."
                ],
                "Plüton_90": [
                    "Karanlık Sınav: Bugün çok yoğun ve zorlayıcı duygular yaşanabilir. Somut: Kontrolü bırakın, teslim olmayı öğrenin — bu bir ebeveyn için en zor ders. Soyut: Kontrol manyaklığının kadersel olarak yüzeye çıktığı derin sınav.",
                    "Güç Savaşı: Siz ve çocuğunuzbugün güç konusunda çatışabilirsiniz. Somut: Gücü değil, şefkati silah olarak kullanın. Soyut: Ebeveyn ile çocuğun güç dengesinin kadersel olarak yeniden yapılandırıldığı sınav anı.",
                    "Paranoya Fazı: Çocuğunuzun her davranışından endişe duyabilirsiniz. Somut: Endişelerinizi abartmayın, gerçekçi olun. Soyut: Geçmiş yaşamlardan veya çocukluktan gelen korkuların kadersel olarak tetiklenmesi.",
                    "Yıkıcı Uretim Gucu: Bastırılmış öfke bugün patlayabilir. Somut: Öfkenizi çocuğunuza değil, soruna yöneltin — panzehir şefkattir. Soyut: Ebeveyn-çocuk arasındaki derin krizin kadersel yüzleşmesi."
                ]
            }
        else:
            bsp_sozlugu = {
                # ☀️ GÜNEŞ (Ortak İrade, Ego, Yaşam Enerjisi)
                "Güneş_0": [
                    "☀️ <b>Kimlik Yenilenmesi:</b> <i>Somut:</i> Birlikte dışarı çıkmak veya ortak bir karar almak için harika bir gün. <i>Soyut:</i> Ruhlarınızın tek bir iradede hizalandığı yüksek enerjili bir faz.",
                    "☀️ <b>Ego Parlaması:</b> <i>Somut:</i> Partnerinizle birlikte bir başarıyı kutlayabilir veya dikkatleri üzerinize çekebilirsiniz. <i>Soyut:</i> 'Biz' bilincinin evren tarafından yeniden tohumlandığı özel bir gün.",
                    "☀️ <b>Canlanma Vakti:</b> <i>Somut:</i> Fiziksel olarak çok daha enerjik ve dışa dönük hissedeceğiniz bir tempo. <i>Soyut:</i> İlişkinizin çekirdek kimliğinin kozmik bir güncelleme aldığı zaman dilimi.",
                    "☀️ <b>Ortak Vizyon:</b> <i>Somut:</i> Geleceğe dair umut veren, net kararlar aldığınız ve inisiyatif kullandığınız anlar. <i>Soyut:</i> Egoların eriyip saf yaşam enerjisinin ilişkinizi yıkadığı bir gün."
                ],
                "Güneş_60": [
                    "☀️ <b>İrade Uyumu:</b> <i>Somut:</i> Günlük akışta işlerin tıkır tıkır ilerlediği, tatlı ve sorunsuz bir gün. <i>Soyut:</i> Egoların çatışmadan, ortak hedeflere hizmet ettiği yapıcı bir pencere.",
                    "☀️ <b>Destekleyici Akış:</b> <i>Somut:</i> Birbirinize küçük yardımlarda bulunarak günün stresini kolayca attığınız saatler. <i>Soyut:</i> İletişimin ve iradenin dostça bir titresimta hizalandığı uyum zamanı.",
                    "☀️ <b>Tatlı Fırsatlar:</b> <i>Somut:</i> İlişkinize keyif katacak sürpriz küçük gelişmeler veya dışarıdan gelen güzel haberler. <i>Soyut:</i> Evrenin ilişkinize 'devam edin' dediği yeşil ışık.",
                    "☀️ <b>Yumuşak Geçiş:</b> <i>Somut:</i> Düne göre çok daha toleranslı ve uyumlu olduğunuz, gerginlikten uzak bir faz. <i>Soyut:</i> Ruhsal dayanışmanın ve onaylanma hissinin içten içe büyüdüğü gün."
                ],
                "Güneş_90": [
                    "☀️ <b>Ego Sınavı:</b> <i>Somut:</i> 'Benim dediğim olacak' inatlaşmaları veya planlarda ufak pürüzler. <i>Soyut:</i> Sivri köşelerinizin birbirinize çarparak törpülendiği gelişim anıdır; esnek olan kazanır.",
                    "☀️ <b>İrade Sürtünmesi:</b> <i>Somut:</i> Dışarıdan gelen bir stresin aranıza yansıması ve haksızlığa uğramışlık hissi. <i>Soyut:</i> İlişkinin kadersel esnekliğinin test edildiği, tahammül gerektiren bir gün.",
                    "☀️ <b>Kışkırtıcı Ayna:</b> <i>Somut:</i> Ortak bir karar alırken zorlanma, partnerin tavrını fazla buyurgan bulma. <i>Soyut:</i> Kendi gücünüzü eşiniz üzerinden kanıtlamaya çalışmayın; rekabeti dış dünyaya saklayın.",
                    "☀️ <b>Sabir Testi:</b> <i>Somut:</i> Enerjinizin bloke olduğunu hissettiğiniz, onay ihtiyacınızın karşılanmadığı saatler. <i>Soyut:</i> Egoların savaşından ziyade, birbirinizin farklılıklarına saygı duyma antrenmanı."
                ],
                "Güneş_120": [
                    "☀️ <b>Zahmetsiz Parlama:</b> <i>Somut:</i> İlişkinin keyfini çıkardığınız, dışarıdan iltifat aldığınız pürüzsüz bir zaman. <i>Soyut:</i> Yaşam enerjisinin kendiliğinden aktığı, evrensel onay günü.",
                    "☀️ <b>Ruhsal Ziyafet:</b> <i>Somut:</i> Eşinizin yanındayken kendinizi en iyi versiyonunuzda hissedeceğiniz rahatlatıcı bir akış. <i>Soyut:</i> Kimliklerinizin birbirini yormadan, doğal bir şekilde şifalandırdığı anlar.",
                    "☀️ <b>Şanslı Gün:</b> <i>Somut:</i> İşlerinizin kolaylaştığı, aranızdaki neşenin ve gülümsemenin tavan yaptığı bir gün. <i>Soyut:</i> Kozmik akışın ilişkinizin yelkenlerini rüzgarla doldurduğu zahmetsiz seyir.",
                    "☀️ <b>İlahi Senkronizasyon:</b> <i>Somut:</i> Aynı anda aynı şeyi düşünüp güldüğünüz, aidiyet hissinin çok güçlü olduğu saatler. <i>Soyut:</i> Gökyüzünün ilişkinizin varlığını ve gücünü kutsadığı altın saatler."
                ],
                "Güneş_180": [
                    "☀️ <b>Kutuplaşma Sınavı:</b> <i>Somut:</i> Partnerinizin tamamen size zıt bir fikirle gelmesi veya aranıza duygusal bir mesafe girmesi. <i>Soyut:</i> Eşiniz bugün sizin gölgenizi yansıtıyor, bu bir gelişim aynasıdır.",
                    "☀️ <b>Tahterevalli Dengesi:</b> <i>Somut:</i> Biriniz çok hevesliyken diğerinin isteksiz olduğu, ritimlerin bir türlü uyuşmadığı anlar. <i>Soyut:</i> İlişkinin iki zıt ucu test ediliyor; dengeyi bulmak için karşılıklı taviz şart.",
                    "☀️ <b>Çekim ve İtiş:</b> <i>Somut:</i> Bir yandan büyük bir fiziksel çekim hissederken, bir yandan uzaklaşma arzusu yaşanabilir. <i>Soyut:</i> Eksik olan yönünüz eşinizde beden buluyor; onu yargılamak yerine tamamlanmayı seçin.",
                    "☀️ <b>Karşı Cephe:</b> <i>Somut:</i> İlişkideki rolünüzün sorgulandığı, kendinizi partnere beğendirme ihtiyacının arttığı gün. <i>Soyut:</i> Dış dünyadaki iradeniz iç dünyanızla çarpışıyor, sakin kalıp merkezinizi koruyun."
                ],

                # 🧠 MERKÜR (Ortak Zihin, İletişim, Kararlar)
                "Merkür_0": [
                    "🧠 <b>Telepatik Zihin:</b> <i>Somut:</i> Mesajlaşmaların arttığı, harika sohbetlerin edildiği veya kısa bir yolculuk planı günü. <i>Soyut:</i> Kelimelere gerek kalmadan birbirinizin zihnini okuyabildiğiniz derin titresim.",
                    "🧠 <b>Zihinsel Bütünlük:</b> <i>Somut:</i> Önemli bir kararı ortak akılla ve çok hızlı bir şekilde masaya yatırıp çözdüğünüz saatler. <i>Soyut:</i> İki ayrı zihnin tek bir süper-bilgisayar gibi evrensel verileri işlediği an.",
                    "🧠 <b>Fikirsel Kıvılcım:</b> <i>Somut:</i> Birbirinize ilham verdiğiniz, yeni projeler veya hobiler hakkında hevesle konuştuğunuz gün. <i>Soyut:</i> Ortak vizyonunuzun zihinsel boyutta yenilendiği aydınlanma fazı.",
                    "🧠 <b>Pürüzsüz İletişim:</b> <i>Somut:</i> Yanlış anlaşılmaların buharlaştığı, en zor konuların bile tatlı dille konuşulabildiği akış. <i>Soyut:</i> Anlaşma ve onaylanma ihtiyacınızın zihinsel olarak tam tatmin edildiği döngü."
                ],
                "Merkür_90": [
                    "🧠 <b>İletişim Darboğazı:</b> <i>Somut:</i> Söylenenlerin ters anlaşıldığı, evrak/teknoloji sorunlarının ilişkiye stres kattığı gün. <i>Soyut:</i> Zihinsel titresimların çatıştığı kadersel bir 'dinleme' sınavı.",
                    "🧠 <b>Sözsel Gerilim:</b> <i>Somut:</i> Tartışmaların kolayca alevlenebileceği, söz kesme ve inatlaşmanın yaşanabileceği saatler. <i>Soyut:</i> Kendi haklılığınızı kanıtlamak yerine, partnerinizin sessizliğindeki nedeni arayın.",
                    "🧠 <b>Yanlış Anlama:</b> <i>Somut:</i> Birinizin şaka yaptığı bir konuya diğerinin ciddi alınıp küsebileceği alınganlık fazı. <i>Soyut:</i> Evren size 'Bugün konuşmak yerine sadece dinle' mesajı veriyor.",
                    "🧠 <b>Mantık Çatışması:</b> <i>Somut:</i> Gündelik planların birbirine uymaması ve organizasyon eksikliği nedeniyle yaşanan sinir harbi. <i>Soyut:</i> Ortak karar mekanizmanızın kadersel bir bakım onarıma girdiği zorlu saatler."
                ],
                "Merkür_120": [
                    "🧠 <b>Kusursuz Diyalog:</b> <i>Somut:</i> Ertelenen zor bir konuyu masaya yatırmak ve tatlıya bağlamak için mükemmel bir gün. <i>Soyut:</i> Evrenin size zihinsel bir kalkan sunduğu, fikirlerin su gibi aktığı faz.",
                    "🧠 <b>Entelektüel Dans:</b> <i>Somut:</i> Birlikte film izlemek, kitap tartışmak veya sadece kahve eşliğinde uzun uzun dertleşmek için harika bir akış. <i>Soyut:</i> Zihinsel olarak birbirinizi çok derinden beslediğiniz şifa uyumı.",
                    "🧠 <b>Ortak Bağ:</b> <i>Somut:</i> Partnerinizin ne diyeceğini o daha söylemeden anladığınız, çok tatlı ve neşeli iletişim saatleri. <i>Soyut:</i> Zihinlerinizin evrensel bir uyumla birbirini yatıştırdığı ve vizyon kattığı gün.",
                    "🧠 <b>Sözlerin Şifası:</b> <i>Somut:</i> Sizi üzen bir konuyu eşinizle paylaştığınızda harika bir tavsiye alıp rahatladığınız anlar. <i>Soyut:</i> İlişkinin iletişim kanalının pırıl pırıl açıldığı, güvenin sözlerle pekiştiği döngü."
                ],
                "Merkür_180": [
                    "🧠 <b>Fikir Düellosu:</b> <i>Somut:</i> Karşılıklı eleştirilerin artabileceği, eski defterlerin açılabileceği diyaloglar. <i>Soyut:</i> Farklı perspektiflerin masaya yatırılmasıdır, ufuk genişleten bir fırtına olarak görün.",
                    "🧠 <b>Zıt Bakışlar:</b> <i>Somut:</i> Birinizin siyah dediğine diğerinin beyaz demekte ısrar edeceği zihinsel inatlaşma. <i>Soyut:</i> Birbirinizin karar alma mekanizmasındaki açıkları size gösteren kadersel bir ayna.",
                    "🧠 <b>Sorgulama Fazı:</b> <i>Somut:</i> Eşinizin aldığı kararları veya mantığını acımasızca eleştirmeye yatkın olduğunuz saatler. <i>Soyut:</i> Kendi içinizdeki kararsızlıkların partneriniz üzerinden size yansıtıldığı test anı.",
                    "🧠 <b>Gerilimli Müzakere:</b> <i>Somut:</i> Ortak bir bütçe, plan veya zaman çizelgesi yaparken zorlanma ve yorgunluk. <i>Soyut:</i> İki farklı dünyanın birbiriyle uzlaşmak için kadersel masaya oturduğu zorunlu toplantı."
                ],

                # ❤️ VENÜS (Aşk, Değer, Estetik, Para)
                "Venüs_0": [
                    "❤️ <b>Aşkın Mührü:</b> <i>Somut:</i> Romantik bir randevu, fiziksel çekimin tavan yapması veya ortak finansal bir kazanç. <i>Soyut:</i> Kalp çakralarının hizalandığı, estetik ve tutkunun ruhlarınızı erittiği gün.",
                    "❤️ <b>Cazibe Zirvesi:</b> <i>Somut:</i> Birbirinize ekstra çekici geldiğiniz, hediyeleşme veya küçük jestlerle sevginin tazelendiği saatler. <i>Soyut:</i> İlişkinin özdeğer algısının ve dişil enerjisinin kozmik olarak şifalandığı faz.",
                    "❤️ <b>Koşulsuz Uyum:</b> <i>Somut:</i> Kavgaların kolayca unutulup sarılarak çözüldüğü, huzur ve tatlılığın hakim olduğu akış. <i>Soyut:</i> Gökyüzünün sevginizi kutsadığı ve aranızdaki bağın yenilendiği kadersel uyanış.",
                    "❤️ <b>Tatlı Çekim:</b> <i>Somut:</i> Birlikte güzelleşmek, alışveriş yapmak veya evinize estetik bir dokunuş katmak için ideal zaman. <i>Soyut:</i> Evrensel sevgi titresimının ilişkinizin tam merkezine yerleştiği derin uyum."
                ],
                "Venüs_90": [
                    "💔 <b>Değer Sınavı:</b> <i>Somut:</i> Kıskançlık krizleri, 'bana yetersiz vakit ayırıyorsun' kaprisleri veya parasal gerginlik. <i>Soyut:</i> Kendi içinizdeki 'sevilmeme korkusunun' yüzeye çıkışıdır, içsel şefkatle doldurun.",
                    "💔 <b>Duygusal Susuzluk:</b> <i>Somut:</i> Partnerinizin jestlerini yetersiz bulma, alınganlık yapma veya değersizlik hissi yaşama. <i>Soyut:</i> Aşkın lisanının karıştığı kadersel gün; beklentilerinizi sıfırlayıp sadece akışta kalın.",
                    "💔 <b>Estetik Çatışma:</b> <i>Somut:</i> Dış görünüş, harcamalar veya sosyal zevkler yüzünden yaşanan ufak çaplı soğuk savaşlar. <i>Soyut:</i> Alma-verme dengenizin kozmik bir testten geçtiği, ego ve sevginin sürtüştüğü an.",
                    "💔 <b>Tutku Darboğazı:</b> <i>Somut:</i> Fiziksel mesafelenme veya eşinizin sizi anlamadığını, takdir etmediğini düşündüğünüz kapalı faz. <i>Soyut:</i> Şımarıklık ve şefkat arasındaki o ince sınırın kadersel olarak sınandığı tehlikeli saatler."
                ],
                "Venüs_120": [
                    "🕊️ <b>Koşulsuz Çekim:</b> <i>Somut:</i> Hiçbir çaba harcamadan mutluluğu yakaladığınız, huzurun hakim olduğu yumuşak gün. <i>Soyut:</i> Aşkın ve dişil enerjinin kendiliğinden, su gibi aktığı eşsiz ruh eşliği titresimı.",
                    "🕊️ <b>Romantik Akış:</b> <i>Somut:</i> Aşkınızı dile getirmek, küçük sürprizler yapmak veya derin bakışmalarla anlaşmak için harika zaman. <i>Soyut:</i> Birbirinizin yaralarını sevgiyle onardığınız ve aidiyetin tavan yaptığı kozmik şifa.",
                    "🕊️ <b>Tatlı Huzur:</b> <i>Somut:</i> Ortak zevklerde buluşup, belki bir müzik veya güzel bir yemek eşliğinde dinlendiğiniz rahatlatıcı saatler. <i>Soyut:</i> Kalplerin senkronize attığı, dünyevi streslerin sevginizin duvarından sektiği gün.",
                    "🕊️ <b>Güzellik Ritmi:</b> <i>Somut:</i> Sosyal ortamlarda gıptayla bakılan bir çift olduğunuz, aranızdaki neşenin dışa yansıdığı faz. <i>Soyut:</i> Evrensel güzellik ve bereket enerjisinin tam olarak ilişkinizin üzerine yağdığı lütuf anı."
                ],
                "Venüs_180": [
                    "🪞 <b>Sevgi İhtiyacı:</b> <i>Somut:</i> İlgisizlik hissi veya 'ben çok veriyorum, o az veriyor' hesaplaşması. <i>Soyut:</i> İlişkinin verme-alma dengesi test ediliyor; dengeyi kurmanın ruhsal kilit noktası.",
                    "🪞 <b>Beklenti Kutuplaşması:</b> <i>Somut:</i> Biriniz çok yapışkan olurken diğerinin kaçmak istemesi, sevgi dillerinin uyuşmaması. <i>Soyut:</i> Kendi özdeğer eksikliğinizi partnerinizin üzerinden tamamlama eğilimi; dikkati kendinize çevirin.",
                    "🪞 <b>Soğuk Ayna:</b> <i>Somut:</i> Aşırı eleştirel olmak, eşinizin zevklerini yargılamak veya finansal konularda zıt düşmek. <i>Soyut:</i> Aşkta karşıt cephelerde gibi hissetseniz de, bu gerilim aslında ilişkinizi dengeleyen bir pusuladır.",
                    "🪞 <b>Tutku Tahterevallisi:</b> <i>Somut:</i> Ani bir kıskançlık ile derin bir soğukluk arasında gidip gelen dengesiz bir duygu durumu. <i>Soyut:</i> İlişkinin sınırlarının test edildiği, 'ne kadar sana aitim' sorusunun kadersel yansıması."
                ],

                # ⚔️ MARS (Eylem, Tutku, Öfke, Rekabet)
                "Mars_0": [
                    "🔥 <b>Tutku ve Eylem:</b> <i>Somut:</i> Birlikte spor yapmak, yorucu bir işi halletmek veya artan fiziksel tutku. <i>Soyut:</i> Birlikte dünyayı fethetme arzusunun zirveye çıktığı yapi gün.",
                    "🔥 <b>Volkanik Enerji:</b> <i>Somut:</i> İlişkide bir anda yükselen enerji, hızlı kararlar ve ortak bir düşmana karşı kenetlenme. <i>Soyut:</i> İradelerin birleşip adeta bir savaşçı gibi tek vücut olduğu kadersel ittifak zamanı.",
                    "🔥 <b>Cesaretin Doğuşu:</b> <i>Somut:</i> Ertelenen zor işlerin üstesinden omuz omuza verip geldiğiniz çok aktif saatler. <i>Soyut:</i> İlişkinin yaşam ateşinin, gökyüzünün eril enerjisiyle harlandığı yenilenme fazı.",
                    "🔥 <b>Hızlı ve Öfkeli:</b> <i>Somut:</i> Biraz sabırsız ama çok üretken olduğunuz, rekabeti dışarıya yönelttiğiniz yapi akış. <i>Soyut:</i> Birlikte terlemenin ve üretmenin getirdiği o derin ruhsal tatmin günü."
                ],
                "Mars_90": [
                    "⚔️ <b>Ateş Çemberi:</b> <i>Somut:</i> İncir çekirdeğini doldurmayan öfke patlamaları, ufak ev kazaları veya tahammülsüzlük. <i>Soyut:</i> Kılıçları birbirinize doğrultmak yerine bu yoğun enerjiyi yorulacağınız bir işe dökün.",
                    "⚔️ <b>Buyuk Sinav:</b> <i>Somut:</i> Seslerin yükselebileceği, 'bana karışma' isyanlarının yaşanabileceği kırmızı alarm günü. <i>Soyut:</i> İlişkinin stres testidir. Patlamaya hazır bu enerjiyi derin bir nefes alarak soğutun.",
                    "⚔️ <b>Sürtünme ve Kriz:</b> <i>Somut:</i> Rekabetin ilişki içine girdiği, inatlaşmaların kalpleri kırabileceği hassas saatler. <i>Soyut:</i> Egonuzun savaş boyalarını sürdüğü kadersel an; partneriniz düşmanınız değil, bunu hatırlayın.",
                    "⚔️ <b>Sabır Testi:</b> <i>Somut:</i> Eşinizin hareketlerinin size batması, tahriklere kapılma ve ani tepki verme riski. <i>Soyut:</i> Agresyonun kadersel olarak partnere yöneldiği bu günde, geri adım atan ilişkiyi kurtarır."
                ],
                "Mars_120": [
                    "🚀 <b>Yenilmez İttifak:</b> <i>Somut:</i> Sırt sırta vererek zorlukların üstesinden geldiğiniz, cesur adımlar attığınız akış. <i>Soyut:</i> Ortak bir hedef uğruna muazzam bir cesaretle tek yürek olduğunuz ilahi faz.",
                    "🚀 <b>Eylem Akışı:</b> <i>Somut:</i> Fiziksel olarak çok uyumlu olduğunuz, hem yorucu işleri halledip hem de eğlendiğiniz gün. <i>Soyut:</i> İlişkinin eylem motorunun hiç teklemeden çalıştığı, üretim ve tutkunun zirvesi.",
                    "🚀 <b>Takim Calismasi:</b> <i>Somut:</i> Birinizin eksik kalan enerjisini diğerinin tamamladığı, harika bir takım arkadaşlığı. <i>Soyut:</i> Evrenin ilişkinize müthiş bir 'ilerleme ve engelleri aşma' kalkanı verdiği özel uyum.",
                    "🚀 <b>Hızlı Senkronizasyon:</b> <i>Somut:</i> Ortak kararların eyleme çok hızlı döküldüğü, aranızdaki ateşin tatlıca yandığı saatler. <i>Soyut:</i> Birbirinizin eylem dilini yargılamadan desteklediğiniz, kadersel bir omuz omuza verme anı."
                ],
                "Mars_180": [
                    "⚔️ <b>Büyük Düello:</b> <i>Somut:</i> Sert tartışmalar, 'benim kurallarım' baskısı veya sinirlerin gergin olduğu kriz potansiyeli. <i>Soyut:</i> Rekabetin ve sınırların en sert kutuplaşması; ateşi eşinize değil, dışarıdaki sorunlara çevirin.",
                    "⚔️ <b>Güç Savaşı:</b> <i>Somut:</i> İlişkide kimin sözünün geçeceğine dair yaşanan gizli veya açık otorite çekişmesi. <i>Soyut:</i> Bireysel iradenizin test edildiği kadersel bir ayna; birbirinizi yok etmek değil, büyütmek için ordasınız.",
                    "⚔️ <b>Kutuplaşan İrade:</b> <i>Somut:</i> Eylemlerinizin birbirini engellediği, 'sen yapmazsan ben de yapmam' noktasına gelinen inat. <i>Soyut:</i> İki savaşçının karşılıklı cephe almasıdır; o kılıçları indirip sadece birbirinizin gözlerine bakın.",
                    "⚔️ <b>Zıt Ritimler:</b> <i>Somut:</i> Biriniz çok hızlı hareket etmek isterken, diğerinin ayak sürüdüğü ve sinirleri bozduğu saatler. <i>Soyut:</i> Kendi eylem eksikliğinizi partnerinizde görüp ona kızdığınız o ilüzyonlu kadersel ayna."
                ],

                # ⏳ SATÜRN
                "Satürn_0": [
                    "⚖️ <b>Karmik Köklenme:</b> <i>Somut:</i> Ciddi bir sorumluluk almak, yatırım konuşmak veya soğuk, mesafeli bir ciddiyet günü. <i>Soyut:</i> Uçarı duyguların yerini ağırbaşlı bir mühür ve sadakat yeminine bıraktığı köklenme anı.",
                    "⚖️ <b>Temel İnşası:</b> <i>Somut:</i> Geleceğe dair somut planlar yapıldığı, sadakatin ve kuralların ön planda olduğu saatler. <i>Soyut:</i> Zamanın testine dayanan ilişkinizin görünmez kolonlarının betonla güçlendirildiği faz.",
                    "⚖️ <b>Sorumluluk Fazı:</b> <i>Somut:</i> Romantizmden çok iş, güç, ailevi görevler ve ciddiyetin konuşulduğu ağırlıklı bir akış. <i>Soyut:</i> Evrenin sizden aşkı değil, partnerliğin dünyevi yükünü paylaşmanızı beklediği disiplin günü.",
                    "⚖️ <b>Kalıcı Mühür:</b> <i>Somut:</i> Birbirinize verdiğiniz sözlerin değerini hissettiğiniz, eski sorunların akıllıca kapatıldığı dönem. <i>Soyut:</i> İlişkinin karmik borçlarının ödendiği ve sarsılmaz bir kale duvarının örüldüğü kadersel an."
                ],
                "Satürn_90": [
                    "🚧 <b>Yapısal Direnç:</b> <i>Somut:</i> Duygusal soğukluk, ilgisizlik hissi veya iş yoğunluğunun ilişkiye engel olması. <i>Soyut:</i> Kadersel bir darboğaz; eğlence değil, sabır zamanıdır. Duvar örmek yerine yaraları sarın.",
                    "🚧 <b>Yetersizlik Sınavı:</b> <i>Somut:</i> 'Beni sevmiyor' kuruntusu, partneri aşırı eleştirme veya kısıtlanmışlık hissi. <i>Soyut:</i> Evren ilişkinin taşıyıcı kolonlarını test ediyor; bugün alınan yaralar, eğer onarılmazsa kalıcı olur.",
                    "🚧 <b>Karmik Duvar:</b> <i>Somut:</i> Eşinizle aranızda görünmez, soğuk bir buzdan duvar olduğunu hissettiğiniz o ağır saatler. <i>Soyut:</i> Kendi içsel yetersizliğinizi ilişkiye yansıtıyorsunuz; şefkat dilenmek yerine şefkat verin.",
                    "🚧 <b>Görev Yorgunluğu:</b> <i>Somut:</i> Hayatın koşturmacası ve maddi dertler yüzünden ilişkinin romantizminin tamamen donduğu gün. <i>Soyut:</i> Aşkın bir rüya değil, dayanıklılık sınavı olduğunu size hatırlatan o sert kozmik çekiç."
                ],
                "Satürn_120": [
                    "⛰️ <b>Sarsılmaz Liman:</b> <i>Somut:</i> 'Bu insanla her şeyi yapabilirim' diyeceğiniz çok sağlam, ayakları yere basan bir gün. <i>Soyut:</i> Evrenin, aşkınızın fırtınaları aşabileceğini fısıldadığı, ruhsal aidiyetin aktığı faz.",
                    "⛰️ <b>Güven Duvarı:</b> <i>Somut:</i> Saygının ve bağlılığın en üst seviyede hissedildiği, yaşça büyüklerden destek alınan zamanlar. <i>Soyut:</i> İlişkinin geçmişten gelen o köklü sağlamlığının meyvelerini yediğiniz çok özel ve güvenli şifa.",
                    "⛰️ <b>Ağırbaşlı Aşk:</b> <i>Somut:</i> Büyük sözlere gerek olmadan, sadece yan yana durmanın bile muazzam bir güç verdiği saatler. <i>Soyut:</i> Zamanın ilişkinizi yıpratmadığını, aksine şarap gibi yıllandırdığını iliklerinize kadar hissettiğiniz an.",
                    "⛰️ <b>Ortak Disiplin:</b> <i>Somut:</i> Finansal, evsel veya kariyer odaklı sorunları birlikte, olgunca ve hızla çözdüğünüz gün. <i>Soyut:</i> Kadersel sorumlulukların bir yük değil, aranızdaki o kutsal bağın harcı olduğunu anladığınız uyum."
                ],
                "Satürn_180": [
                    "🧱 <b>Otorite Çarpışması:</b> <i>Somut:</i> Kısıtlanma hissi, partnerin baba/patron rolüne bürünmesi veya aşırı eleştirel tavırlar. <i>Soyut:</i> Kurallar ve duyguların çarpıştığı an. Üstünlük kurmaya çalışmak yerine eşinizin korkularına şefkatle yaklaşın.",
                    "🧱 <b>Mesafe Sınavı:</b> <i>Somut:</i> Biriniz çok sıcak ve yakınlık ararken diğerinin mesafeli, iş odaklı veya kuralcı olduğu tahterevalli. <i>Soyut:</i> İlişkinin kurallarıyla, sevginin özgürlüğü arasındaki kadersel gerilim noktası.",
                    "🧱 <b>Katı Duvarlar:</b> <i>Somut:</i> 'Senin yüzünden' diyerek eski hataların ve yapısal sorunların sertçe masaya getirildiği saatler. <i>Soyut:</i> Eşinizin hatalarını yargılarken aslında kendi karmik korkularınızı yargıladığınızı unutmayın.",
                    "🧱 <b>Sorumluluk Yükü:</b> <i>Somut:</i> İlişkinin tüm dünyevi yükünün tek bir kişinin omuzlarına bindiği hissi ve bundan doğan soğuk öfke. <i>Soyut:</i> Evren size 'dengeyi kurmazsan duvarın altında kalırsın' uyarısı yapıyor; yükleri hemen paylaşın."
                ],

                # 🍀 JÜPİTER
                "Jüpiter_0": [
                    "🍀 <b>İlahi Lütuf:</b> <i>Somut:</i> Kutlama, hediyeleşme, seyahat planı veya büyük bir mutluluk anı. <i>Soyut:</i> Ruhunuzun sevinçle taştığı büyük büyüme titresimı.",
                    "🍀 <b>Genişleyen Ufuk:</b> <i>Somut:</i> Birlikte çok eğlendiğiniz, felsefi veya manevi derin sohbetler yaptığınız şanslı saatler. <i>Soyut:</i> İlişkinin bereket çakrasının açıldığı, evrenin size cömertçe gülümsediği ilahi mühür.",
                    "🍀 <b>Ortak İnanç:</b> <i>Somut:</i> Karamsarlıktan uzak, her şeyin çözülebileceğine dair güçlü bir umut hissettiğiniz pozitif gün. <i>Soyut:</i> Gökyüzünün aranızdaki inanç bağını tazelediği ve ilişkinizi korumaya aldığı özel kalkan.",
                    "🍀 <b>Abartılı Neşe:</b> <i>Somut:</i> Bol bol gülme, fazla para harcama veya iştahın artması gibi keyifli ama sınırsız deneyimler. <i>Soyut:</i> Ruhsal büyümenin kapılarının ardına kadar açıldığı, neşenin ilişkiye aktığı altın uyum."
                ],
                "Jüpiter_90": [
                    "🎈 <b>Beklenti Yanılsaması:</b> <i>Somut:</i> İsteklerin abartıldığı, lüzumsuz masraf yapılan veya tutulamayacak sözlerin verildiği gün. <i>Soyut:</i> Gerçekçi kalın; kibir ve fazla iyimserlik, yarın hayal kırıklığına dönüşebilir.",
                    "🎈 <b>Aşırı Özgüven:</b> <i>Somut:</i> Tartışmalarda 'ben bilirim' tavrının abartılması, partnerin fikirlerini küçümseme eğilimi. <i>Soyut:</i> İlişkinin büyüme krizidir; fazla genişlemek bazen yapının esnekliğini bozabilir.",
                    "🎈 <b>Şımarıklık Testi:</b> <i>Somut:</i> Verilen değeri yetersiz bulma, sürekli daha fazlasını talep etme ve tatminsizlik hissi. <i>Soyut:</i> Şükran duygunuzun evren tarafından test edildiği kadersel bir savrulma anı.",
                    "🎈 <b>Felsefi Çatışma:</b> <i>Somut:</i> İnançlar, vizyonlar veya hayata bakış açıları konusunda yaşanan fanatik ve yüksek sesli tartışmalar. <i>Soyut:</i> Birbirinizi dinlemek yerine birbirinize 'vaaz verdiğiniz' körlük durumu."
                ],

                # ⚡ URANÜS
                "Uranüs_0": [
                    "⚡ <b>Elektrikli Uyanış:</b> <i>Somut:</i> Beklenmedik sürprizler, ani program değişiklikleri ve sıra dışı fikirler. <i>Soyut:</i> İlişkinizin rutini kadersel bir şokla tazeleniyor, devrimci bir dokunuşa hazır olun.",
                    "⚡ <b>Sıra Dışı Çekim:</b> <i>Somut:</i> İlişkiye ilk günkü o heyecanlı kıvılcımın tekrar düştüğü, çok eğlenceli ve isyankar saatler. <i>Soyut:</i> Kalıpların yıkıldığı, ilişkinin yeni bir boyuta aniden evrildiği 'evreka' anı.",
                    "⚡ <b>Zincirleri Kırmak:</b> <i>Somut:</i> Sizi sıkan veya daraltan her türlü kuraldan eşinizle birlikte kaçıp kurtulma arzusu. <i>Soyut:</i> Özgürlüğün ve bireyselliğin, ilişkiye zarar vermeden entegre edildiği yüksek uyanış.",
                    "⚡ <b>Sürpriz Rota:</b> <i>Somut:</i> Ani gelişen bir seyahat, beklenmedik bir haber veya zihin açıcı teknolojik/modern bir gelişme. <i>Soyut:</i> Kadersel monotonluğun evrenin şimşekleriyle parçalandığı ve ilişkinin nefes aldığı döngü."
                ],
                "Uranüs_90": [
                    "⚡ <b>Özgürlük İsyanı:</b> <i>Somut:</i> Boğulma hissi, 'bana karışma' triplerinin kırıcılığa dönüşebileceği an. <i>Soyut:</i> Birbirinize nefes alacak bağımsız alanlar bırakın, aksi halde bağlar şok edici kopuşlarla sınanabilir.",
                    "⚡ <b>Ani Yıkım Güdüsü:</b> <i>Somut:</i> Sinirlerin çok gergin olduğu, en ufak şeye parlayıp 'her şeyi bırakıp gitme' isteğinin tetiklendiği saatler. <i>Soyut:</i> Düzeni korumak ile isyan etmek arasındaki o yıkıcı fay hattında yürüyorsunuz.",
                    "⚡ <b>Elektrik Yüklü Kriz:</b> <i>Somut:</i> Partnerinizin tamamen öngörülemez ve tutarsız davrandığı, sizi şoka sokan ani tartışmalar. <i>Soyut:</i> İlişkinin statükosunun şiddetle sarsıldığı, fevri kararlardan kaçınılması gereken kırmızı alarm.",
                    "⚡ <b>Mesafe Kopuşu:</b> <i>Somut:</i> Birinizin yoğun bir şekilde bireyselleşmek ve yalnız kalmak istemesi, diğerinin bunu reddedilme sanması. <i>Soyut:</i> Uzay-zaman sürekliliğinizde geçici bir 'veri kaybı'; üstüne gitmeyin, kendi haline bırakın."
                ],

                # 🌊 NEPTÜN
                "Neptün_0": [
                    "🌊 <b>Ruhsal Simya:</b> <i>Somut:</i> Birlikte hayal kurmak, film izlemek, sanatsal bir şey yapmak veya sadece sarılıp uyumak. <i>Soyut:</i> Muazzam bir empati, fedakarlık ve ruhsal kenetlenme. (Ancak gerçeklerden kopmamaya dikkat edin.)",
                    "🌊 <b>İlahi Çözülme:</b> <i>Somut:</i> Affetmenin çok kolay olduğu, şefkatin ve gözyaşının ilişkiyi tertemiz yıkadığı duygu dolu anlar. <i>Soyut:</i> Egoların tamamen eridiği, ruhlarınızın birbirine ilahi bir pamuk ipliğiyle bağlandığı masal saati.",
                    "🌊 <b>Telepatik Teslimiyet:</b> <i>Somut:</i> Eşinizin ne hissettiğini o daha söylemeden gözlerinden anladığınız, çok derin ve mistik bir gün. <i>Soyut:</i> Savunma kalkanlarının indiği, ilişkinin koşulsuz sevgiyle kutsandığı kozmik şifa sığınağı.",
                    "🌊 <b>Tatlı İllüzyon:</b> <i>Somut:</i> Dünyevi dertleri kapının dışında bırakıp, partnerinizi mükemmelleştirerek izlediğiniz romantik faz. <i>Soyut:</i> Evrenin ilişkinize sunduğu bir rüya molası; tadını çıkarın ama büyük imzalar atmayın."
                ],
                "Neptün_90": [
                    "🌫️ <b>Sis Perdesi:</b> <i>Somut:</i> Yanlış anlaşılmalar, söylenen yalanların veya gizlenen şeylerin şüphesi, yoğun bir kafa karışıklığı. <i>Soyut:</i> Gerçeklerin çarpıtılabildiği gün. Bugün büyük kararlar almaktan ve yüzleşmekten kaçının.",
                    "🌫️ <b>Kurban Psikolojisi:</b> <i>Somut:</i> 'Ben senin için saçımı süpürge ettim' hissinin verdiği o ağır melankoli ve alınganlık. <i>Soyut:</i> Sınırlarınızı koruyamadığınız için evren sizi hayal kırıklığı ile test ediyor; fedakarlığı dengeleyin.",
                    "🌫️ <b>Hayal Kırıklığı Sınavı:</b> <i>Somut:</i> Partnerinize yüklediğiniz o 'mükemmel' anlamların gerçek hayatla örtüşmediğini fark edip üzülme anı. <i>Soyut:</i> Gerçeklikten ne kadar koptuğunuzu size gösteren kadersel bir uyanış şokudur.",
                    "🌫️ <b>Kaçış Eğilimi:</b> <i>Somut:</i> Sorunları çözmek yerine susmayı, uyumayı veya konuyu değiştirmeyi seçtiğiniz pasif-agresif saatler. <i>Soyut:</i> İlişkinin karanlık sularında kaybolma hissi; sağlam bir zemine (Satürn'e) tutunmaya çalışın."
                ],

                # 🌋 PLÜTON
                "Plüton_0": [
                    "🦇 <b>Küllerinden Doğuş:</b> <i>Somut:</i> Gizli kalmış sırların döküldüğü, derin bir yüzleşmenin ardından gelen yoğun rahatlama ve tutku. <i>Soyut:</i> Cinselliğin veya psikolojik sırların yüzeye çıkıp aşkın yakıcı gücüyle onarıldığı simyasal gün.",
                    "🦇 <b>Hipnotik Çekim:</b> <i>Somut:</i> Bakışların çok derinleştiği, vazgeçilmezlik hissinin ve aidiyetin neredeyse saplantılı bir hal aldığı anlar. <i>Soyut:</i> Ruhlarınızın en karanlık dehlizlerde bile birbirini tanıyıp kucakladığı yeraltı mühürü.",
                    "🦇 <b>Dönüştürücü Güç:</b> <i>Somut:</i> Ortak bir krizin üstesinden muazzam bir güç birliğiyle geldiğiniz, korkularınızı birlikte yendiğiniz saatler. <i>Soyut:</i> İlişkinin deri değiştirdiği, eski toksik kalıpların ölüp yerine sarsılmaz bir gücün doğduğu faz.",
                    "🦇 <b>Sessiz İttifak:</b> <i>Somut:</i> Dış dünyaya karşı tamamen kapalı, sadece ikinizin bildiği derin bir titresimta anlaştığınız mistik gün. <i>Soyut:</i> Gökyüzünün, ilişkinizin köklerine Plütonyen bir dayanıklılık enjekte ettiği özel zaman."
                ],
                "Plüton_90": [
                    "🌋 <b>Karanlık Sınav:</b> <i>Somut:</i> Kıskançlık, manipülasyon, telefon karıştırma veya 'ya benimsin ya toprağın' tarzı toksik baskılar. <i>Soyut:</i> Kontrol manyaklığının hortladığı derin kriz! Evren sizden gücü bırakıp teslimiyet istiyor.",
                    "🌋 <b>Güç Savaşı:</b> <i>Somut:</i> 'Sana bunu ödeteceğim' mantığıyla hareket edilen, inatlaşmanın ve kin gütmenin ilişkiyi zehirlediği anlar. <i>Soyut:</i> Egonuzun en karanlık tarafıyla yüzleşiyorsunuz; partnerinizi yok etmeye çalışırken ilişkiyi kanatıyorsunuz.",
                    "🌋 <b>Paranoya Fazı:</b> <i>Somut:</i> Eşinizin her hareketinden şüphelenme, en ufak sözün altında büyük bir komplo arama yorgunluğu. <i>Soyut:</i> Geçmiş yaşamlardan veya çocukluktan gelen terk edilme korkularınızın kadersel olarak tetiklenmesi.",
                    "🌋 <b>Yıkıcı Uretim Gucu:</b> <i>Somut:</i> Bastırılmış tüm öfkenin aniden patladığı, köprüleri yakıp atma isteğinin tavan yaptığı kırmızı çizgi. <i>Soyut:</i> Bu enerji bir zehirdir; eğer panzehiri (şefkati) devreye sokmazsanız kalıcı hasar bırakabilir."
                ]
            }
        
        minor_oran = 27.32166 / 365.2422 
        alarmlar = []
        
        j_ileri_kök, j_geri_kök = self.get_julian_dates()
        
        ana_harita_A = {}
        ana_harita_B = {}
        
        hedef_gezegenler = {
            "Güneş": swe.SUN, "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS, 
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN, "Uranüs": swe.URANUS, 
            "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO, "Lilith": swe.MEAN_APOG, "Chiron": swe.CHIRON, 
            "Juno": swe.AST_OFFSET + 3, "Ceres": swe.AST_OFFSET + 1, "Pallas": swe.AST_OFFSET + 2, 
            "Vesta": swe.AST_OFFSET + 4, "KAD": swe.MEAN_NODE
        }
        
        for isim, gid in hedef_gezegenler.items():
            try: 
                flags = get_safe_flags(gid)
                ana_harita_A[isim] = swe.calc_ut(j_ileri_kök, gid, flags)[0][0]
                ana_harita_B[isim] = swe.calc_ut(j_geri_kök, gid, flags)[0][0]
            except Exception:
                pass

        bugun_tarihi = datetime.datetime.now()
        gecen_gun_toplam = (bugun_tarihi - self.event_date).days
        
        # --- HAFIZALI METİN ÜRETİCİ (4 Varyasyondan Rastgele ve Tekrarsız Seçim Yapar) ---
        bsp_hafiza = set()
        def bsp_metin_sec(yorum_havuzu):
            if isinstance(yorum_havuzu, str): return yorum_havuzu
            secenekler = [c for c in yorum_havuzu if c not in bsp_hafiza]
            if not secenekler:
                bsp_hafiza.clear() # Tüm seçenekler tükendiyse hafızayı sıfırla
                secenekler = yorum_havuzu
            secilen = random.choice(secenekler)
            bsp_hafiza.add(secilen)
            return secilen

        # --- MODERN VE YÜKSEK KONTRASTLI ARAYÜZ (UI) MOTORU ---
        def haritayi_tara(ay_derece, harita, kisi_isim, renk_kodu):
            olaylar = []
            for gez_isim, gez_derece in harita.items():
                fark = abs(ay_derece - gez_derece)
                if fark > 180: fark = 360 - fark
                
                orb = 0.6 
                açı_kodu = None
                if fark <= orb: açı_kodu = f"{gez_isim}_0"
                elif abs(fark - 60) <= orb: açı_kodu = f"{gez_isim}_60"
                elif abs(fark - 90) <= orb: açı_kodu = f"{gez_isim}_90"
                elif abs(fark - 120) <= orb: açı_kodu = f"{gez_isim}_120"
                elif abs(fark - 180) <= orb: açı_kodu = f"{gez_isim}_180"
                
                if açı_kodu and açı_kodu in bsp_sozlugu:
                    ham_mesaj = bsp_sozlugu[açı_kodu]
                    # Akis metin seciciyi kullan
                    mesaj = bsp_metin_sec(ham_mesaj)
                    
                    if pdf_icin:
                        # PDF için emojiler ve HTML temizliği
                        mesaj_temiz = mesaj.replace("☀️", "").replace("🧠", "").replace("❤️", "").replace("💔", "")\
                                           .replace("🕊️", "").replace("🪞", "").replace("🔥", "").replace("⚔️", "")\
                                           .replace("🚀", "").replace("🍀", "").replace("🎈", "").replace("⚖️", "")\
                                           .replace("🚧", "").replace("⛰️", "").replace("🧱", "").replace("⚡", "")\
                                           .replace("🌌", "").replace("🌊", "").replace("🌫️", "").replace("🦇", "")\
                                           .replace("🌋", "")
                        olaylar.append(f"<b>[{kisi_isim}] - {gez_isim} Transiti:</b><br/>{mesaj_temiz}")
                    else:
                        # STREAMLIT EKRANI İÇİN VIP DARK-MODE KART TASARIMI
                        kutu_html = f"""
                        <div style="background-color: #FBF7F4; padding: 16px; border-radius: 8px; 
                                    margin-bottom: 15px; border: 1px solid #E8E0D8; 
                                    border-left: 6px solid {renk_kodu}; 
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                            <div style="font-size: 16px; font-weight: 800; color: {renk_kodu}; margin-bottom: 8px;">
                                [{kisi_isim}] ➔ {gez_isim} Transiti
                            </div>
                            <div style="font-size: 14.5px; line-height: 1.6; color: #4A4A4A;">
                                <span style="color: #4A4A4A;">{mesaj}</span>
                            </div>
                        </div>
                        """
                        olaylar.append(kutu_html)
            return olaylar

        for gun in range(gun_sayisi):
            hedef_tarih = bugun_tarihi + timedelta(days=gun)
            toplam_ilerleme_gokyuzu = (gecen_gun_toplam + gun) * minor_oran
            
            j_bsp_A = j_ileri_kök + toplam_ilerleme_gokyuzu
            j_bsp_B = j_geri_kök + toplam_ilerleme_gokyuzu
            
            ay_derece_A = swe.calc_ut(j_bsp_A, swe.MOON)[0][0]
            ay_derece_B = swe.calc_ut(j_bsp_B, swe.MOON)[0][0]
            
            gunun_olaylari = []
            
            gunun_olaylari.extend(haritayi_tara(ay_derece_A, ana_harita_A, self.p1_isim, "#B8A9C9")) 
            gunun_olaylari.extend(haritayi_tara(ay_derece_B, ana_harita_B, self.p2_isim, "#D4878F")) 
            
            if gunun_olaylari:
                tarih_str = hedef_tarih.strftime("%d %B %Y")
                alarmlar.append({"tarih": tarih_str, "mesajlar": gunun_olaylari})
                
        return alarmlar
    
    def pdf_rapor_uret(self, dosya_adi="FBST_Kadersel_Kontrat.pdf"):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak, Spacer, Image
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.graphics.shapes import Drawing, Line
        from reportlab.lib.colors import HexColor

        # 1. KARAKUTU İMHA PROTOKOLÜ
        def pdf_temizle(metin):
            """PDF motorunu bozan emojileri ASCII'ye çevirir, vurguları korur."""
            if not isinstance(metin, str): return str(metin)
            metin = metin.replace("✨", "[*]").replace("🌟", "[*]").replace("🚀", "[>]").replace("📍", "[-]")
            metin = metin.replace("👉", "->").replace("•", "-") 
            # Sembolleri koruyan regex filtresi
            metin = re.sub(r'[^\w\s.,;:!?()\[\]{}<>\-+=/\\\'"&%$#@*|~^\n]', '', metin)
            metin = metin.replace('\r', '').replace('\x0b', '').replace('\x0c', '')
            return metin.strip()

        # --- OPTİMİZE EDİLMİŞ PDF ÜRETİMİ ---
        doc = SimpleDocTemplate(dosya_adi, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        # 2. Tipografi Hiyerarşisinin Yeniden İnşası
        styles.add(ParagraphStyle(name='TurkishNormal', fontName='DejaVuSans', fontSize=10, leading=18, spaceAfter=12, textColor=HexColor(METIN_SIYAH)))
        styles.add(ParagraphStyle(name='TurkishHeading', fontName='DejaVuSans-Bold', fontSize=13, leading=18, spaceBefore=22, spaceAfter=10, textColor=HexColor(DERIN_MAVI)))
        styles.add(ParagraphStyle(name='TurkishTitle', fontName='DejaVuSans-Bold', fontSize=18, leading=22, spaceBefore=20, spaceAfter=15, alignment=1, textColor=HexColor(KADIM_LACIVERT)))
        styles.add(ParagraphStyle(name='CoverTitle', fontName='DejaVuSans', fontSize=28, leading=34, alignment=1, textColor=HexColor(KADIM_LACIVERT)))
        styles.add(ParagraphStyle(name='CoverSub', fontName='DejaVuSans', fontSize=13, leading=18, alignment=1, textColor=HexColor("#4A5568")))
        styles.add(ParagraphStyle(name='CoverFooter', fontName='DejaVuSans', fontSize=9, leading=14, alignment=1, textColor=HexColor("#718096")))
        styles.add(ParagraphStyle(name='CardText', fontName='DejaVuSans', fontSize=9.5, leading=15, textColor=HexColor(METIN_SIYAH)))

        story = []

        # ZAMAN ÇAPALARININ (j_ileri, j_geri) EN BAŞTA HESAPLANMASI
        ileri_tarih, ileri_str, gecici_geri, astro_yil, geri_str = self.calculate_bagil_tarihler()
        j_ileri, j_geri = self.get_julian_dates()

        def kapak_ciz(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(HexColor("#FFFFFF"))
            canvas.rect(0, 0, 595.27, 841.89, fill=True, stroke=False)
            canvas.restoreState()
        
        def luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5):
            d = Drawing(500, 15)
            d.add(Line(0, 7, 500, 7, strokeColor=HexColor(renk), strokeWidth=kalinlik))
            return d

        def sonraki_sayfa_ciz(canvas, doc):
            """Sayfa numarası, üst bilgi ve altın çizgi ekleyen callback."""
            canvas.saveState()
            w, h = A4
            canvas.setFont('DejaVuSans', 8)
            canvas.setFillColor(HexColor('#718096'))
            canvas.drawString(40, h - 25, "ASARTEPE SİNASTRİ AKADEMİSİ")
            canvas.drawRightString(w - 40, h - 25, f"{self.p1_isim} & {self.p2_isim}")
            canvas.setStrokeColor(HexColor('#C9A96E'))
            canvas.setLineWidth(0.5)
            canvas.line(40, h - 30, w - 40, h - 30)
            canvas.setStrokeColor(HexColor('#C9A96E'))
            canvas.setLineWidth(1.0)
            canvas.line(40, 35, w - 40, 35)
            canvas.setFont('DejaVuSans', 9)
            canvas.setFillColor(HexColor('#C9A96E'))
            canvas.drawCentredString(w / 2, 20, f"- {doc.page} -")
            canvas.setFont('DejaVuSans', 7)
            canvas.setFillColor(HexColor('#4A5568'))
            canvas.drawRightString(w - 40, 20, "Fatih Asartepe — © 2026 Tüm hakları saklıdır")
            canvas.restoreState()

        def baslik_karti_ekle(baslik_metni, alt_baslik=None, emoji=""):
            """Bölüm başlıklarını renkli kutu kartı olarak ekler."""
            tam_baslik = f"{emoji} {baslik_metni}" if emoji else baslik_metni
            kart_html = f"""
            <table width="100%" cellpadding="8">
            <tr>
                <td bgcolor="#1A1A2E" width="6">
                    <font color="#C9A96E" size="16">|</font>
                </td>
                <td bgcolor="#F0F4F8" style="padding-left:12px;">
                    <font color="#1A1A2E" size="14"><b>{tam_baslik}</b></font>
                    {"<br/><font color='#4A5568' size='9'>" + alt_baslik + "</font>" if alt_baslik else ""}
                </td>
            </tr>
            </table>
            """
            story.append(Spacer(1, 18))
            story.append(Paragraph(kart_html, styles['TurkishNormal']))
            story.append(Spacer(1, 10))

        def cerceveli_gorsel_ekle(dosya_yolu, genislik, yukseklik, baslik=None):
            """Görselleri ince altın çerçeve ile sararak ekler."""
            if not os.path.exists(dosya_yolu):
                story.append(Paragraph(f"<i>Görsel bulunamadı: {dosya_yolu}</i>", styles['TurkishNormal']))
                return
            ic_gorsel = Image(dosya_yolu, width=genislik, height=yukseklik)
            cerceveli = Table([[ic_gorsel]], colWidths=[genislik + 16])
            cerceveli.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#FBF7F4')),
                ('BOX', (0, 0), (-1, -1), 1.5, HexColor('#C9A96E')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(cerceveli)
            if baslik:
                story.append(Paragraph(f"<font color='#4A5568' size='8'><i>{baslik}</i></font>", styles['TurkishNormal']))
            story.append(Spacer(1, 8))

        # 🏛️ 1. BÖLÜM: KAPAK — Asartepe_Kapak.pdf merge ile 1. sayfaya eklenecek
        # Bu sayfa kapak1.png arka planı ile 2. sayfa olacak
        story.append(Spacer(1, 30))
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kapak1.png")
        if os.path.exists(logo_path):
            story.append(Image(logo_path, width=220, height=220))
            story.append(Spacer(1, 25))
        else:
            story.append(Spacer(1, 60))

        story.append(Paragraph("<b>ASARTEPE SİNASTRİ AKADEMİSİ</b>", styles['CoverTitle']))
        story.append(Spacer(1, 8))
        story.append(Paragraph("<font color='#C9A96E' size='16'>Fatih Asartepe Sinastri Tekniği (FAST)</font>", styles['CoverTitle']))
        story.append(Spacer(1, 20))

        if self.mod == "ebeveyn_cocuk":
            story.append(Paragraph("<font color='#1A1A2E' size='14'>EBEVEYN-ÇOCUK İLİŞKİ ANALİZİ</font>", styles['CoverTitle']))
        else:
            story.append(Paragraph("<font color='#1A1A2E' size='14'>İLİŞKİ ANALİZİ RAPORU</font>", styles['CoverTitle']))
        story.append(Spacer(1, 25))

        kullanici_bilgisi = [
            [Paragraph(f"<b>Kök ve Rehber Ruhlar:</b> {self.p1_isim} & {self.p2_isim}", styles['CoverSub'])],
            [Paragraph(f"<b>Kadersel Akış Miladı:</b> {datetime.now().strftime('%d.%m.%Y')}", styles['CoverSub'])]
        ]
        bilgi_tablosu = Table(kullanici_bilgisi, colWidths=[480])
        bilgi_tablosu.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
        story.append(bilgi_tablosu)
        
        story.append(Spacer(1, 100))
        story.append(Paragraph("Bu doküman, Fatih Asartepe Sinastri Tekniği (FAST) ile kişiye özel üretilmiştir.", styles['CoverFooter']))
        story.append(Spacer(1, 15))
        story.append(Paragraph("© 2026 Fatih Asartepe — Bu çalışmaya ait tüm haklar saklıdır. izinsiz kopyalanması, yayılması veya ticari amaçla kullanılması yasaktır.", styles['CoverFooter']))
        story.append(PageBreak())

        # 🗺️ 3. BÖLÜM: TEKNİK VE GEOMETRİK KOORDİNATLAR
        if self.mod == "ebeveyn_cocuk":
            baslik_karti_ekle("EBEVEYN-ÇOCUK İLİŞKİ RAPORU", alt_baslik=f"{self.p1_isim} & {self.p2_isim} | {self.city}", emoji="📋")
        else:
            baslik_karti_ekle("İLİŞKİ RAPORU", alt_baslik=f"{self.p1_isim} & {self.p2_isim} | {self.city}", emoji="📋")
        
        meta_html = f"""
        <b>Analiz Bolgesi:</b> {self.city}, {self.country} ({self.enlem} enlem, {self.boylam} boylam)<br/>
        <b>Bulusma Noktasi:</b> {self.event_date_str} | {self.event_time_str}<br/>
        <b>Zaman Cizelgesi:</b> {self.p1_isim}: {self.p1.strftime('%d.%m.%Y')} | {self.p2_isim}: {self.p2.strftime('%d.%m.%Y')}<br/>
        <b>Analiz Yöntemi:</b> {self.get_kadersel_durak()}<br/>
        <b>Uyum Oranı:</b> {self.calculate_altin_oran_muhru()}
        """
        meta_table = Table([[Paragraph(meta_html, styles['TurkishNormal'])]], colWidths=[500])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8F9FA')),
            ('BOX', (0,0), (-1,-1), 1, HexColor('#C9A96E')),
            ('LINEBELOW', (0,0), (-1,0), 0.5, HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 15),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
            ('LEFTPADDING', (0,0), (-1,-1), 18),
            ('RIGHTPADDING', (0,0), (-1,-1), 18),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("ILISKININ ENERJISI VE DAYANIKLILIGI", styles['TurkishHeading']))
        # BURAYA: Ki kutuphane metni eklenecek
        tork_metni = self.calculate_tork()
        story.append(Paragraph(tork_metni, styles['TurkishNormal']))
        story.append(Spacer(1, 10))
        
        # LÜKS ÇİZGİMİZ BURAYA GELDİ 🌟
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
        story.append(Spacer(1, 10))
        
        titresim_resmi = self.ciz_titresim_grafigi()

        story.append(Paragraph("İLİŞKİ ENERJİSİ GRAFİĞİ", styles['TurkishHeading']))
        cerceveli_gorsel_ekle(titresim_resmi, 500, 160, "Sinüs Frekans Grafiği")
        
        story.append(Paragraph("ORTAK GELECEK REHBERİ (21 Yıllık Öngörü)", styles['TurkishHeading']))
        for kavsak in self.calculate_gelecek_navigasyonu(pdf_icin=True):
            story.append(Paragraph(f"• {kavsak}", styles['TurkishNormal']))
        story.append(Spacer(1, 15))

        ki_yili = self.calculate_ks()
        
        if ki_yili >= 7.0:
            ki_sinifi = "GÜÇLÜ BAĞ"
            ki_anlami = "Bu ilişki kendi dengesini oluşturmuş, dış etkenlerden etkilenmeyen güçlü bir yapıya sahip."
        elif ki_yili >= 4.0:
            ki_sinifi = "DENGELİ BAĞ"
            ki_anlami = "İlişki ne çok hafif ne de çok ağır — tam olması gereken noktada, esnek ama sağlam."
        else:
            ki_sinifi = "HASSAS BAĞ"
            ki_anlami = "Bu bağ dışarıdan gelen etkilere daha açık; korunmaya ve bilinçli beslenmeye ihtiyaç duyan bir yapıya sahip."

        ki_metni = f"""
<b>🌌 Bağın Gücü: {ki_yili:.2f} — {ki_sinifi}</b>
<br/>{ki_anlami}
"""
        story.append(Paragraph(ki_metni, styles['TurkishNormal']))
        story.append(Spacer(1, 15))

        # 🌌 3. BÖLÜM: KADERSEL PERSPEKTİFLER VE GEZEGEN DÖKÜMLERİ
        story.append(PageBreak())
        
        def gezegen_dokumu(j_gun, taraf_adi, tarih_str, harita_dosyasi, rol=None):
            story.append(Paragraph(f"{taraf_adi} ({tarih_str})", styles['TurkishHeading']))
            cerceveli_gorsel_ekle(harita_dosyasi, 450, 450, f"{taraf_adi} Durumsal Haritası")
                
            asc_burc = self.yukselen_bul(j_gun)
            if asc_burc != "Hesaplanamadi":
                if self.mod == "ebeveyn_cocuk":
                    yorum = fbst_yukselenler_ebeveyn.get(asc_burc, "Bu vitrin henüz tanımlanmadı.")
                else:
                    yorum = fbst_yukselenler.get(asc_burc, "Bu vitrin henüz tanımlanmadı.")
                story.append(Paragraph(f"<b>Yükselen Vitrini ({asc_burc}):</b> {yorum}", styles['TurkishNormal']))
                story.append(Spacer(1, 8))

            burclar_tr = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
            burclar_keys = ["Koc", "Boga", "Ikizler", "Yengec", "Aslan", "Basak", "Terazi", "Akrep", "Yay", "Oglak", "Kova", "Balik"]

            temel_gezegenler = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter", "Satürn", "Uranüs", "Neptün", "Plüton"]
            karmik_noktalar = ["KAD", "Chiron", "Juno", "Lilith", "Ceres"]

            for gezegen_ad in temel_gezegenler:
                if gezegen_ad not in GEZEGENLER: continue
                gezegen_id = GEZEGENLER[gezegen_ad]
                try:
                    flags = get_safe_flags(gezegen_id)
                    res = swe.calc_ut(j_gun, gezegen_id, flags)
                    mutlak_derece = res[0][0]
                    hiz = res[0][3]
                except Exception: continue

                burc_idx = int(mutlak_derece // 30)
                burc_adi_tr = burclar_tr[burc_idx]
                burc_key = burclar_keys[burc_idx]
                
                deg = int(mutlak_derece % 30)
                mnt = int(((mutlak_derece % 30) - deg) * 60)
                rx_str = " (Rx)" if (hiz < 0 and gezegen_id not in [swe.SUN, swe.MOON]) else ""
                burc_arg_key = f"{burc_key} (Rx)" if rx_str else burc_key
                ev_no = self.ev_konumu_bul(j_gun, gezegen_id)
                
                gosterim_hatti = f"🪐 <b>{gezegen_ad}:</b> {burc_adi_tr} {deg}° {mnt:02d}'{rx_str} — {ev_no}. Ev"
                story.append(Paragraph(f"<font color='#1A1A2E'><b>{gosterim_hatti}</b></font>", styles['TurkishNormal']))
                
                yorum_gezegen = self.kadersel_cumle_kur(gezegen_ad, burc_arg_key, ev_no, rol=rol)
                story.append(Paragraph(yorum_gezegen, styles['TurkishNormal']))
                
                sabian_metni = self.sabian_okuyucu(gezegen_ad, mutlak_derece)
                story.append(Paragraph(f"<font color='#5A6A85'><i>{sabian_metni}</i></font>", styles['TurkishNormal']))
                story.append(Spacer(1, 8))

            story.append(Spacer(1, 10))
            story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.0)) # Buraya ince çizgi daha şık olur
            story.append(Spacer(1, 10))
            story.append(Paragraph("DERİN KARMİK MÜHÜRLER VE ASTEROİTLER", styles['TurkishHeading']))
            
            for gezegen_ad in karmik_noktalar:
                if gezegen_ad not in GEZEGENLER: continue
                gezegen_id = GEZEGENLER[gezegen_ad]
                try:
                    flags = get_safe_flags(gezegen_id)
                    res = swe.calc_ut(j_gun, gezegen_id, flags)
                    mutlak_derece = res[0][0]
                except Exception: continue

                burc_idx = int(mutlak_derece // 30)
                burc_adi_tr = burclar_tr[burc_idx]
                burc_key = burclar_keys[burc_idx]
                
                deg = int(mutlak_derece % 30)
                mnt = int(((mutlak_derece % 30) - deg) * 60)
                ev_no = self.ev_konumu_bul(j_gun, gezegen_id)
                
                gosterim_hatti = f"🩸 <b>{gezegen_ad}:</b> {burc_adi_tr} {deg}° {mnt:02d}' — {ev_no}. Ev"
                story.append(Paragraph(f"<font color='#8A1538'><b>{gosterim_hatti}</b></font>", styles['TurkishNormal']))
                
                yorum_gezegen = self.kadersel_cumle_kur(gezegen_ad, burc_key, ev_no, rol=rol)
                story.append(Paragraph(yorum_gezegen, styles['TurkishNormal']))
                story.append(Spacer(1, 8))

        # GEZEGEN DÖKÜMÜ FONKSİYONU SADECE BİR KERE ÇAĞRILIYOR!
        if self.mod == "ebeveyn_cocuk":
            gezegen_dokumu(j_ileri, f"🌱 {self.p1_isim}'in Kadersel Haritası (Çocuk)", ileri_str, f"{self._session_id}_Situa_A.png", rol="cocuk")
            story.append(PageBreak())
            gezegen_dokumu(j_geri, f"🦅 {self.p2_isim}'in Kadersel Haritası (Ebeveyn)", geri_str, f"{self._session_id}_Situa_B.png", rol="ebeveyn")
        else:
            gezegen_dokumu(j_ileri, f"🌱 KÖK RUH (Geçmişin Bilgeliği): {self.p1_isim} Perspektifi", ileri_str, f"{self._session_id}_Situa_A.png")
            story.append(PageBreak())
            gezegen_dokumu(j_geri, f"🦅 REHBER RUH (Geleceğin Vizyonu): {self.p2_isim} Perspektifi", geri_str, f"{self._session_id}_Situa_B.png")

        # 🌍 ASTROCARTOGRAPHY + GLOBAL KADER PUSULASI (PDF - BİRLEŞİK)
        if self.mod == "ebeveyn_cocuk":
            pass
        else:
            story.append(PageBreak())
            baslik_karti_ekle("ŞEHİR VE LOKASYON ANALİZİ",
                              alt_baslik="Size en uygun şehirler ve bölgeler",
                              emoji="🌍")
            story.append(Spacer(1, 10))
            try:
                BUYUK_SEHIRLER = {
                    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Gaziantep",
                    "Mersin", "Diyarbakır", "Kocaeli", "Hatay", "Manisa", "Kayseri", "Samsun",
                    "Balıkesir", "Kahramanmaraş", "Trabzon", "Eskişehir", "Denizli",
                    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "San Antonio",
                    "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", "San Francisco",
                    "Seattle", "Denver", "Boston", "Nashville", "Portland", "Las Vegas", "Miami",
                    "London", "Manchester", "Birmingham", "Glasgow", "Edinburgh", "Liverpool",
                    "Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Bordeaux", "Strasbourg",
                    "Berlin", "Hamburg", "München", "Köln", "Frankfurt", "Stuttgart", "Düsseldorf",
                    "Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Málaga",
                    "Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova",
                    "Moskova", "St. Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan",
                    "Pekin", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu", "Wuhan", "Hangzhou",
                    "Tokyo", "Osaka", "Yokohama", "Nagoya", "Kyoto", "Fukuoka",
                    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune",
                    "São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza",
                    "Buenos Aires", "Córdoba", "Rosario", "Mendoza",
                    "Mexico City", "Guadalajara", "Monterrey", "Cancún",
                    "Kahire", "İskenderiye", "Giza",
                    "Dubai", "Abu Dhabi", "Riyad", "Cidde", "Doha", "Kuveyt", "Manama",
                    "Tel Aviv", "Kudüs", "Hayfa",
                    "Bangkok", "Singapur", "Kuala Lumpur", "Jakarta", "Manila", "Hanoi",
                    "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
                    "Toronto", "Vancouver", "Montreal", "Ottawa", "Calgary",
                    "Kopenhag", "Stokholm", "Oslo", "Helsinki", "Reykjavik",
                    "Atina", "Atina", "Lizbon", "Porto", "Varşova", "Kraków", "Prag", "Budapeşte",
                    "Kapstadt", "Johannesburg", "Nairobi", "Lagos", "Accra", "Kazablanka",
                    "Kolombo", "Kathmandu", "Kabil", "Tiflis", "Bakü", "Erivan",
                    "Tiran", "Üsküp", "Saraybosna", "Zagreb", "Ljubljana", "Bratislava",
                    "Kiev", "Odessa", "Minsk", "Vilnius", "Riga", "Tallinn"
                }

                top_sehirler_pdf = []
                if 'radar_top_para' in st.session_state and st.session_state['radar_top_para']:
                    db = sehir_veritabani_yukle()
                    def _sehir_koordinat_bul(sehir_adi):
                        for ulke, sehirler in db.items():
                            if sehir_adi.endswith(ulke):
                                sehir_ismi = sehir_adi[:-(len(ulke)+2)].strip()
                                if sehir_ismi in sehirler:
                                    v = sehirler[sehir_ismi]
                                    return v["lat"] if isinstance(v, dict) else v[0], v["lon"] if isinstance(v, dict) else v[1]
                            if sehir_adi.startswith(sehir_ismi) if (sehir_ismi := sehir_adi[:-len(ulke)-2].strip()) else False:
                                pass
                        for ulke, sehirler in db.items():
                            for sehir_ismi, koord in sehirler.items():
                                if sehir_adi.lower().startswith(sehir_ismi.lower()):
                                    return (koord["lat"], koord["lon"]) if isinstance(koord, dict) else (koord[0], koord[1])
                        return 0, 0

                    for v in st.session_state['radar_top_para'][:3]:
                        sehir_adi = v["sehir"]
                        sehir_adi_sade = sehir_adi.split(",")[0].strip().split(" (")[0].strip()
                        if sehir_adi_sade not in BUYUK_SEHIRLER:
                            continue
                        lat, lon = _sehir_koordinat_bul(sehir_adi)
                        top_sehirler_pdf.append({"sehir": sehir_adi, "lat": lat, "lon": lon, "kategori": "para", "skor": v["para"]})
                    for v in st.session_state['radar_top_huzur'][:3]:
                        sehir_adi = v["sehir"]
                        sehir_adi_sade = sehir_adi.split(",")[0].strip().split(" (")[0].strip()
                        if sehir_adi_sade not in BUYUK_SEHIRLER:
                            continue
                        lat, lon = _sehir_koordinat_bul(sehir_adi)
                        top_sehirler_pdf.append({"sehir": sehir_adi, "lat": lat, "lon": lon, "kategori": "huzur", "skor": v["huzur"]})
                    for v in st.session_state['radar_top_tutku'][:2]:
                        sehir_adi = v["sehir"]
                        sehir_adi_sade = sehir_adi.split(",")[0].strip().split(" (")[0].strip()
                        if sehir_adi_sade not in BUYUK_SEHIRLER:
                            continue
                        lat, lon = _sehir_koordinat_bul(sehir_adi)
                        top_sehirler_pdf.append({"sehir": sehir_adi, "lat": lat, "lon": lon, "kategori": "tutku", "skor": v["tutku"]})
                    for v in st.session_state['radar_top_kriz'][:2]:
                        sehir_adi = v["sehir"]
                        sehir_adi_sade = sehir_adi.split(",")[0].strip().split(" (")[0].strip()
                        if sehir_adi_sade not in BUYUK_SEHIRLER:
                            continue
                        lat, lon = _sehir_koordinat_bul(sehir_adi)
                        top_sehirler_pdf.append({"sehir": sehir_adi, "lat": lat, "lon": lon, "kategori": "kriz", "skor": v["kriz"]})
                acg_dosya, acg_abs_yol = self.ciz_astrocartography(dosya_adi="FBST_Astrocartography_PDF.png", top_sehirler=top_sehirler_pdf)
                cerceveli_gorsel_ekle(acg_abs_yol, 500, 250, "Astrocartography Dünya Haritası")
                legend_parts = [
                    Paragraph("<font color='#C9A96E'>★</font> <b>Para</b>", styles['TurkishNormal']),
                    Paragraph("<font color='#C0C0C0'>★</font> <b>Huzur</b>", styles['TurkishNormal']),
                    Paragraph("<font color='#FF6347'>★</font> <b>Tutku</b>", styles['TurkishNormal']),
                    Paragraph("<font color='#9370DB'>★</font> <b>Kriz</b>", styles['TurkishNormal']),
                ]
                legend_table = Table([legend_parts], colWidths=[120, 120, 120, 120])
                legend_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                    ('BOX', (0,0), (-1,-1), 0.5, CERCEVE_GRI),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ]))
                story.append(legend_table)
            except Exception:
                story.append(Paragraph("<i>Astrocartography haritası PDF'e eklenemedi.</i>", styles['TurkishNormal']))

            # Radar sonuçları (aynı sayfada, haritanın altında)
            story.append(Spacer(1, 15))
            story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.0))
            story.append(Spacer(1, 10))
            story.append(Paragraph("EN UYGUN LOKASYONLAR", styles['TurkishHeading']))
            if 'radar_top_para' in st.session_state and st.session_state['radar_top_para']:
                hassasiyet_metni = "Sistem, şehirlerin enlem ve boylam koordinatlarındaki milimetrik sapmaları hesaplayarak evrensel dalga boyu imzanıza en uygun lokasyonları tespit etmiştir."
                story.append(Paragraph(hassasiyet_metni, styles['TurkishNormal']))
                story.append(Spacer(1, 10))
                def add_top_5_to_pdf(baslik, liste_adi, skor_anahtari):
                    story.append(Paragraph(baslik, styles['TurkishHeading']))
                    radar_rows = []
                    filtrelenmis = []
                    for veri in st.session_state[liste_adi]:
                        sehir_adi = veri['sehir']
                        sehir_adi_sade = sehir_adi.split(",")[0].strip().split(" (")[0].strip()
                        if sehir_adi_sade not in BUYUK_SEHIRLER:
                            continue
                        filtrelenmis.append(veri)
                        if len(filtrelenmis) >= 10:
                            break
                    for i, veri in enumerate(filtrelenmis):
                        etki_str = ""
                        if veri.get('etkiler'):
                            etki_str = f"<br/><font size='8' color='#666666'>  {veri['etkiler'][0]}</font>" if veri['etkiler'] else ""
                        row_txt = f"<b>{i+1}. {veri['sehir']}</b> - Skor: %{veri[skor_anahtari]}{etki_str}"
                        radar_rows.append([Paragraph(row_txt, styles['TurkishNormal'])])
                    radar_table = Table(radar_rows, colWidths=[500])
                    radar_table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                        ('BOX', (0,0), (-1,-1), 0.5, CERCEVE_GRI),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                        ('TOPPADDING', (0,0), (-1,-1), 6),
                        ('LEFTPADDING', (0,0), (-1,-1), 10),
                    ]))
                    story.append(radar_table)
                    story.append(Spacer(1, 8))
                add_top_5_to_pdf("💰 MALİ AÇIDAN EN İYİ ŞEHİRLER", 'radar_top_para', 'para')
                add_top_5_to_pdf("🕊️ HUZUR AÇISINDAN EN İYİ ŞEHİRLER", 'radar_top_huzur', 'huzur')
                add_top_5_to_pdf("🔥 TUTKU VE ENERJİ AÇISINDAN EN İYİ ŞEHİRLER", 'radar_top_tutku', 'tutku')
                add_top_5_to_pdf("🌋 KRİZ RİSKİ EN YÜKSEK ŞEHİRLER", 'radar_top_kriz', 'kriz')
            else:
                uyari = "⚠️ Radar verileri henüz hesaplanmadı. Lütfen uygulamadaki 'Dünyayı Tara' butonuna basarak kadersel pusulayı aktif hale getirin."
                story.append(Paragraph(uyari, styles['TurkishNormal']))

        # 🔮 COMPOSITE HARİTA (PDF)
        story.append(Spacer(1, 15))
        baslik_karti_ekle("ORTALAMA HARİTA", 
                          alt_baslik="İki kişinin haritasının ortalamasından oluşan ortak harita", 
                          emoji="🔮")
        story.append(Spacer(1, 10))
        try:
            composite_dosya = self.ciz_composite_harita(dosya_adi="FBST_Composite_PDF.png")
            cerceveli_gorsel_ekle(composite_dosya, 350, 350, "Composite Harita")
            # Composite otomatik yorum
            try:
                j1c = swe.julday(self.p1.year, self.p1.month, self.p1.day, 12.0)
                j2c = swe.julday(self.p2.year, self.p2.month, self.p2.day, 12.0)
                burclar_tr = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
                ev_isimleri = [
                    "Benlik, Kimlik ve Beden", "Para, Değerler ve Güvenlik", "İletişim, Kardeşler ve Kısa Yolculuklar",
                    "Aile, Kökler ve Ev", "Yaratıcılık, Çocuklar ve Eğlence", "Günlük Yaşam, Sağlık ve Hizmet",
                    "Evlilik, Ortaklık ve Açık Düşmanlıklar", "Ölüm, Dönüşüm ve Ortak Kaynaklar",
                    "Yükseköğretim, Felsefe ve Uzak Yolculuklar", "Kariyer, Toplumsal Statü ve İtibar",
                    "Arkadaşlıklar, Gruplar ve Özgürlük", "Rüyalar, Bilinçaltı ve Sınırlar"
                ]
                burc_yorumlari = {
                    "Koç": "bağımsızlık, cesaret ve inici ruh",
                    "Boğa": "istikrar, somut değerler ve duyusal bağ",
                    "İkizler": "çok yönlülük, iletişim ve entelektüel paylaşım",
                    "Yengeç": "duygusal derinlik, koruyuculuk ve aidiyet",
                    "Aslan": "yaratıcılık, cömertlik ve sahne ışığı",
                    "Başak": "detaycılık, hizmet ve pratik mükemmeliyet",
                    "Terazi": "denge, estetik ve uyum arayışı",
                    "Akrep": "yoğunluk, dönüşüm ve derin bağlanma",
                    "Yay": "özgürlük, keşif ve felsefi genişleme",
                    "Oğlak": "sorumluluk, yapı ve uzun vadeli hedefler",
                    "Kova": "özgünlük, insancılık ve vizyoner bakış",
                    "Balık": "merhamet, maneviyat ve sınırsız sevgi"
                }

                def ev_hesapla(derece, asc_derece):
                    fark = (derece - asc_derece) % 360
                    return int(fark / 30) + 1

                comp_yorum_parts = []
                if self.mod == "ebeveyn_cocuk":
                    comp_yorum_parts.append("Bu harita, ebeveyn ve çocuk arasındaki enerjinin ortak ruhunu temsil eder. İki bireyin birleşiminden doğan bu bağımsız harita, ebeveynlik yolculuğunuzun kozik imzasıdır.")
                else:
                    comp_yorum_parts.append("Bu harita, iki doğum haritasının açısal ortalamasından oluşan 'üçüncü ruh' - ilişkinizin ortak kimliğidir.")

                # Composite house cusps (equal house from ASC)
                comp_asc = None
                try:
                    _, ascmc1 = swe.houses(j1c, self.enlem, self.boylam, b'P')
                    _, ascmc2 = swe.houses(j2c, self.enlem, self.boylam, b'P')
                    asc1, asc2 = ascmc1[0], ascmc2[0]
                    fark_c = abs(asc1 - asc2)
                    if fark_c > 180:
                        comp_asc = (asc1 + (asc2 + 360)) / 2 if asc1 > asc2 else ((asc1 + 360) + asc2) / 2
                    else:
                        comp_asc = (asc1 + asc2) / 2
                    comp_asc = comp_asc % 360
                    comp_asc_burc = burclar_tr[int(comp_asc / 30)]
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Yükselen: {comp_asc_burc}</b> ({comp_asc:.1f}°)<br/>"
                            f"Ebeveyn-çocuk birliğinin dış dünyaya açılan kapısı <b>{comp_asc_burc}</b> enerjisiyle şekillenir. "
                            f"{comp_asc_burc} yükseleni, bu bağın dışarıdan ilk izlenimini ve genel atmosferini belirler. "
                            f"Birliğiniz dışarıdan <b>{burc_yorumlari.get(comp_asc_burc, '')}</b> özellikleriyle tanınır."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Yükselen: {comp_asc_burc}</b> ({comp_asc:.1f}°)<br/>"
                            f"Bu birlikteliğin dış dünyaya açılan kapısı <b>{comp_asc_burc}</b> enerjisiyle şekillenir. "
                            f"{burclar_tr[int(comp_asc / 30)]} yükseleni, ilişkinizin ilk izlenimini ve genel atmosferini belirler. "
                            f"İlişkiniz dışarıdan <b>{burc_yorumlari.get(comp_asc_burc, '')}</b> özellikleriyle tanınır."
                        )
                except Exception:
                    pass

                # Composite Güneş
                try:
                    d1g = swe.calc_ut(j1c, GEZEGENLER["Güneş"])[0][0]
                    d2g = swe.calc_ut(j2c, GEZEGENLER["Güneş"])[0][0]
                    fark_g = abs(d1g - d2g)
                    if fark_g > 180:
                        ort_g = (d1g + (d2g + 360)) / 2 if d1g > d2g else ((d1g + 360) + d2g) / 2
                    else:
                        ort_g = (d1g + d2g) / 2
                    ort_g = ort_g % 360
                    g_burc = burclar_tr[int(ort_g / 30)]
                    g_ev = ev_hesapla(ort_g, comp_asc) if comp_asc is not None else None
                    ev_metni = f" <b>{g_ev}. Ev'de</b> ({ev_isimleri[g_ev - 1]})" if g_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Güneş: {g_burc}</b> ({ort_g:.1f}°){ev_metni}<br/>"
                            f"Ebeveyn-çocuk birliğinin yaşam gücü <b>{g_burc}</b> burcunda atar. "
                            f"{g_burc} enerjisi, ortak hedeflerinizi ve birlikte nasıl güçlü durduğunuzu belirler. "
                            f"Bu bağın temel motivasyonu <b>{burc_yorumlari.get(g_burc, '')}</b> temalarında yoğunlaşır."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Güneş: {g_burc}</b> ({ort_g:.1f}°){ev_metni}<br/>"
                            f"İlişkinizin kalbi ve yaşam gücü <b>{g_burc}</b> burcunda atar. "
                            f"{g_burc} enerjisi, ortak hedeflerinizi ve birlikte nasıl parladığınızı belirler. "
                            f"Birlikteliğinizin temel motivasyonu <b>{burc_yorumlari.get(g_burc, '')}</b> temalarında yoğunlaşır."
                        )
                except Exception:
                    pass

                # Composite Ay
                try:
                    d1a = swe.calc_ut(j1c, GEZEGENLER["Ay"])[0][0]
                    d2a = swe.calc_ut(j2c, GEZEGENLER["Ay"])[0][0]
                    fark_a = abs(d1a - d2a)
                    if fark_a > 180:
                        ort_a = (d1a + (d2a + 360)) / 2 if d1a > d2a else ((d1a + 360) + d2a) / 2
                    else:
                        ort_a = (d1a + d2a) / 2
                    ort_a = ort_a % 360
                    a_burc = burclar_tr[int(ort_a / 30)]
                    a_ev = ev_hesapla(ort_a, comp_asc) if comp_asc is not None else None
                    ev_metni_a = f" <b>{a_ev}. Ev'de</b> ({ev_isimleri[a_ev - 1]})" if a_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Ay: {a_burc}</b> ({ort_a:.1f}°){ev_metni_a}<br/>"
                            f"Ebeveyn-çocuk arasındaki duygusal bağ ve içsel paylaşım <b>{a_burc}</b> burcunda şekillenir. "
                            f"Birlikte güvende hissettiğiniz anlar, {a_burc} enerjisiyle tanımlanır. "
                            f"Ortak duygusal ihtiyaçlarınız <b>{burc_yorumlari.get(a_burc, '')}</b> ekseninde birleşir."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Ay: {a_burc}</b> ({ort_a:.1f}°){ev_metni_a}<br/>"
                            f"Duygusal bağınız ve iç dünyasal paylaşımınız <b>{a_burc}</b> burcunda şekillenir. "
                            f"Birlikte güvende hissettiğiniz anlar, {a_burc} enerjisiyle tanımlanır. "
                            f"Ortak duygusal ihtiyaçlarınız <b>{burc_yorumlari.get(a_burc, '')}</b> ekseninde birleşir."
                        )
                except Exception:
                    pass

                # Composite Venüs
                try:
                    d1v = swe.calc_ut(j1c, GEZEGENLER["Venüs"])[0][0]
                    d2v = swe.calc_ut(j2c, GEZEGENLER["Venüs"])[0][0]
                    fark_v = abs(d1v - d2v)
                    if fark_v > 180:
                        ort_v = (d1v + (d2v + 360)) / 2 if d1v > d2v else ((d1v + 360) + d2v) / 2
                    else:
                        ort_v = (d1v + d2v) / 2
                    ort_v = ort_v % 360
                    v_burc = burclar_tr[int(ort_v / 30)]
                    v_ev = ev_hesapla(ort_v, comp_asc) if comp_asc is not None else None
                    ev_metni_v = f" <b>{v_ev}. Ev'de</b> ({ev_isimleri[v_ev - 1]})" if v_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Venüs: {v_burc}</b> ({ort_v:.1f}°){ev_metni_v}<br/>"
                            f"Ebeveyn-çocuk arasındaki sevgi dili ve duygusal bağlanma biçimi <b>{v_burc}</b> burcunda ifade bulur. "
                            f"Birbirinize nasıl şefkat gösterdiğinizi ve hangi jestlerin bağınızı güçlendirdiğini bu burç belirler. "
                            f"Ortak sevgi diliniz <b>{burc_yorumlari.get(v_burc, '')}</b> temalarıyla şekillenir."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Venüs: {v_burc}</b> ({ort_v:.1f}°){ev_metni_v}<br/>"
                            f"Aşk diliniz ve romantik çekim merkeziniz <b>{v_burc}</b> burcunda ifade bulur. "
                            f"Birbirinize nasıl sevgi gösterdiğinizi ve hangi romantik jestlerin işe yaradığını bu burç belirler. "
                            f"Ortak aşk diliniz <b>{burc_yorumlari.get(v_burc, '')}</b> temalarıyla şekillenir."
                        )
                except Exception:
                    pass

                # Composite Merkür
                try:
                    d1m = swe.calc_ut(j1c, GEZEGENLER["Merkür"])[0][0]
                    d2m = swe.calc_ut(j2c, GEZEGENLER["Merkür"])[0][0]
                    fark_m = abs(d1m - d2m)
                    if fark_m > 180:
                        ort_m = (d1m + (d2m + 360)) / 2 if d1m > d2m else ((d1m + 360) + d2m) / 2
                    else:
                        ort_m = (d1m + d2m) / 2
                    ort_m = ort_m % 360
                    m_burc = burclar_tr[int(ort_m / 30)]
                    m_ev = ev_hesapla(ort_m, comp_asc) if comp_asc is not None else None
                    ev_metni_m = f" <b>{m_ev}. Ev'de</b> ({ev_isimleri[m_ev - 1]})" if m_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Merkür: {m_burc}</b> ({ort_m:.1f}°){ev_metni_m}<br/>"
                            f"Ebeveyn-çocuk arasındaki iletişim dili ve düşünce paylaşımı <b>{m_burc}</b> burcunda şekillenir. "
                            f"Birlikte nasıl konuştuğunuz, birbirinize nasıl açıklama yaptığınız ve ortak zihinsel dünyanız bu burcun enerjisiyle belirlenir. "
                            f"İletişim tarzınız <b>{burc_yorumlari.get(m_burc, '')}</b> temalarıyla biçimlenir."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Merkür: {m_burc}</b> ({ort_m:.1f}°){ev_metni_m}<br/>"
                            f"İlişkinizin iletişim dili ve düşünce paylaşımı <b>{m_burc}</b> burcunda şekillenir. "
                            f"Birlikte nasıl konuştuğunuz, fikir alışverişleriniz ve ortak zihinsel dünyanız bu burcun enerjisiyle belirlenir. "
                            f"İletişim tarzınız <b>{burc_yorumlari.get(m_burc, '')}</b> temalarıyla biçimlenir."
                        )
                except Exception:
                    pass

                # Composite Mars
                try:
                    d1ma = swe.calc_ut(j1c, GEZEGENLER["Mars"])[0][0]
                    d2ma = swe.calc_ut(j2c, GEZEGENLER["Mars"])[0][0]
                    fark_ma = abs(d1ma - d2ma)
                    if fark_ma > 180:
                        ort_ma = (d1ma + (d2ma + 360)) / 2 if d1ma > d2ma else ((d1ma + 360) + d2ma) / 2
                    else:
                        ort_ma = (d1ma + d2ma) / 2
                    ort_ma = ort_ma % 360
                    ma_burc = burclar_tr[int(ort_ma / 30)]
                    ma_ev = ev_hesapla(ort_ma, comp_asc) if comp_asc is not None else None
                    ev_metni_ma = f" <b>{ma_ev}. Ev'de</b> ({ev_isimleri[ma_ev - 1]})" if ma_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Mars: {ma_burc}</b> ({ort_ma:.1f}°){ev_metni_ma}<br/>"
                            f"Ebeveyn-çocuk arasındaki enerji alışverişi, rekabet duygusu ve ortak eylem tarzı <b>{ma_burc}</b> burcunda ifade bulur. "
                            f"Birlikte nasıl harekete geçtiğiniz, tartışmalarınızda nasıl bir tavır sergilediğiniz ve ortak cesaretiniz bu burcun enerjisiyle şekillenir. "
                            f"Enerji alışverişiniz <b>{burc_yorumlari.get(ma_burc, '')}</b> temalarıyla belirlenir."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Mars: {ma_burc}</b> ({ort_ma:.1f}°){ev_metni_ma}<br/>"
                            f"İlişkinizin enerji kaynağı, tutku dengesi ve eylem tarzı <b>{ma_burc}</b> burcunda ifade bulur. "
                            f"Birlikte nasıl harekete geçtiğiniz, tartışmalarınızda nasıl bir tavır sergilediğiniz ve ortak cesaretiniz bu burcun enerjisiyle şekillenir. "
                            f"Enerji alışverişiniz <b>{burc_yorumlari.get(ma_burc, '')}</b> temalarıyla belirlenir."
                        )
                except Exception:
                    pass

                # Composite Jüpiter
                try:
                    d1j = swe.calc_ut(j1c, GEZEGENLER["Jüpiter"])[0][0]
                    d2j = swe.calc_ut(j2c, GEZEGENLER["Jüpiter"])[0][0]
                    fark_j = abs(d1j - d2j)
                    if fark_j > 180:
                        ort_j = (d1j + (d2j + 360)) / 2 if d1j > d2j else ((d1j + 360) + d2j) / 2
                    else:
                        ort_j = (d1j + d2j) / 2
                    ort_j = ort_j % 360
                    j_burc = burclar_tr[int(ort_j / 30)]
                    j_ev = ev_hesapla(ort_j, comp_asc) if comp_asc is not None else None
                    ev_metni_j = f" <b>{j_ev}. Ev'de</b> ({ev_isimleri[j_ev - 1]})" if j_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Jüpiter: {j_burc}</b> ({ort_j:.1f}°){ev_metni_j}<br/>"
                            f"Ebeveyn-çocuk arasındaki bolluk, genişleme ve ortak inanç sistemi <b>{j_burc}</b> burcunda şekillenir. "
                            f"Birlikte en çok nerede büyüdüğünüz, hangi konularda şanslı olduğunuz ve ortak felsefi bakış açınız bu burcun enerjisiyle belirlenir. "
                            f"Bolluk ve genişleme kaynaklarınız <b>{burc_yorumlari.get(j_burc, '')}</b> temalarıyla beslenir."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Jüpiter: {j_burc}</b> ({ort_j:.1f}°){ev_metni_j}<br/>"
                            f"İlişkinizin bolluk kaynağı, şanslı alanları ve ortak genişleme yönleriniz <b>{j_burc}</b> burcunda şekillenir. "
                            f"Birlikte en çok nerede büyüdüğünüz, hangi konularda talihli olduğunuz ve ortak felsefi bakış açınız bu burcun enerjisiyle belirlenir. "
                            f"Bolluk ve genişleme kaynaklarınız <b>{burc_yorumlari.get(j_burc, '')}</b> temalarıyla beslenir."
                        )
                except Exception:
                    pass

                # Composite Satürn
                try:
                    d1s = swe.calc_ut(j1c, GEZEGENLER["Satürn"])[0][0]
                    d2s = swe.calc_ut(j2c, GEZEGENLER["Satürn"])[0][0]
                    fark_s = abs(d1s - d2s)
                    if fark_s > 180:
                        ort_s = (d1s + (d2s + 360)) / 2 if d1s > d2s else ((d1s + 360) + d2s) / 2
                    else:
                        ort_s = (d1s + d2s) / 2
                    ort_s = ort_s % 360
                    s_burc = burclar_tr[int(ort_s / 30)]
                    s_ev = ev_hesapla(ort_s, comp_asc) if comp_asc is not None else None
                    ev_metni_s = f" <b>{s_ev}. Ev'de</b> ({ev_isimleri[s_ev - 1]})" if s_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Satürn: {s_burc}</b> ({ort_s:.1f}°){ev_metni_s}<br/>"
                            f"Ebeveyn-çocuk arasındaki yapı, sorumluluk ve uzun vadeli öğreti <b>{s_burc}</b> burcunda şekillenir. "
                            f"Birlikte en çok hangi konularda disiplin geliştirdiğiniz, hangi sınavlarla yüzleştiğiniz ve kalıcı yapıları nasıl inşa ettiğiniz bu burcun enerjisiyle belirlenir. "
                            f"Ortak olgunlaşma alanlarınız <b>{burc_yorumlari.get(s_burc, '')}</b> temalarında yoğunlaşır."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Satürn: {s_burc}</b> ({ort_s:.1f}°){ev_metni_s}<br/>"
                            f"İlişkinizin yapı taşı, sınav alanı ve uzun vadeli sorumluluklarınız <b>{s_burc}</b> burcunda şekillenir. "
                            f"Birlikte en çok hangi konularda disiplin geliştirdiğiniz, hangi sınavlarla yüzleştiğiniz ve kalıcı yapıları nasıl inşa ettiğiniz bu burcun enerjisiyle belirlenir. "
                            f"Ortak olgunlaşma alanlarınız <b>{burc_yorumlari.get(s_burc, '')}</b> temalarında yoğunlaşır."
                        )
                except Exception:
                    pass

                # Composite Uranüs
                try:
                    d1u = swe.calc_ut(j1c, GEZEGENLER["Uranüs"])[0][0]
                    d2u = swe.calc_ut(j2c, GEZEGENLER["Uranüs"])[0][0]
                    fark_u = abs(d1u - d2u)
                    if fark_u > 180:
                        ort_u = (d1u + (d2u + 360)) / 2 if d1u > d2u else ((d1u + 360) + d2u) / 2
                    else:
                        ort_u = (d1u + d2u) / 2
                    ort_u = ort_u % 360
                    u_burc = burclar_tr[int(ort_u / 30)]
                    u_ev = ev_hesapla(ort_u, comp_asc) if comp_asc is not None else None
                    ev_metni_u = f" <b>{u_ev}. Ev'de</b> ({ev_isimleri[u_ev - 1]})" if u_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Uranüs: {u_burc}</b> ({ort_u:.1f}°){ev_metni_u}<br/>"
                            f"Ebeveyn-çocuk arasındaki özgürlük, yenilik ve ani değişim enerjisi <b>{u_burc}</b> burcunda ifade bulur. "
                            f"Birlikte en çok nerede özgürleştiğiniz, hangi beklenmedik dönüşümlerle karşılaştığınız ve bağımsızlık dengeniz bu burcun enerjisiyle şekillenir. "
                            f"Özgürlük ve yenilik kaynaklarınız <b>{burc_yorumlari.get(u_burc, '')}</b> temalarıyla beslenir."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Uranüs: {u_burc}</b> ({ort_u:.1f}°){ev_metni_u}<br/>"
                            f"İlişkinin özgürlük alanı, beklenmedik değişimleri ve yenilikçi ruhu <b>{u_burc}</b> burcunda ifade bulur. "
                            f"Birlikte en çok nerede özgürleştiğiniz, hangi ani dönüşümlerle karşılaştığınız ve bağımsızlık dengeniz bu burcun enerjisiyle şekillenir. "
                            f"Özgürlük ve yenilik kaynaklarınız <b>{burc_yorumlari.get(u_burc, '')}</b> temalarıyla beslenir."
                        )
                except Exception:
                    pass

                # Composite Neptün
                try:
                    d1n = swe.calc_ut(j1c, GEZEGENLER["Neptün"])[0][0]
                    d2n = swe.calc_ut(j2c, GEZEGENLER["Neptün"])[0][0]
                    fark_n = abs(d1n - d2n)
                    if fark_n > 180:
                        ort_n = (d1n + (d2n + 360)) / 2 if d1n > d2n else ((d1n + 360) + d2n) / 2
                    else:
                        ort_n = (d1n + d2n) / 2
                    ort_n = ort_n % 360
                    n_burc = burclar_tr[int(ort_n / 30)]
                    n_ev = ev_hesapla(ort_n, comp_asc) if comp_asc is not None else None
                    ev_metni_n = f" <b>{n_ev}. Ev'de</b> ({ev_isimleri[n_ev - 1]})" if n_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Neptün: {n_burc}</b> ({ort_n:.1f}°){ev_metni_n}<br/>"
                            f"Ebeveyn-çocuk arasındaki manevi bağ, rüya dünyası ve koşulsuz fedakarlık enerjisi <b>{n_burc}</b> burcunda şekillenir. "
                            f"Birlikte en çok nerede manevi derinlik yaşadığınız, hangi konularda hayal kırıklığına uğradığınız ve ruhsal paylaşımınız bu burcun enerjisiyle belirlenir. "
                            f"Manevi ve ruhsal paylaşımınız <b>{burc_yorumlari.get(n_burc, '')}</b> temalarıyla beslenir."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Neptün: {n_burc}</b> ({ort_n:.1f}°){ev_metni_n}<br/>"
                            f"İlişkinin ruhsal boyutu, hayal gücü ve koşulsuz sevgi enerjisi <b>{n_burc}</b> burcunda şekillenir. "
                            f"Birlikte en çok nerede manevi derinlik yaşadığınız, hangi konularda hayal kırıklığına uğradığınız ve ruhsal paylaşımınız bu burcun enerjisiyle belirlenir. "
                            f"Manevi ve ruhsal paylaşımınız <b>{burc_yorumlari.get(n_burc, '')}</b> temalarıyla beslenir."
                        )
                except Exception:
                    pass

                # Composite Plüton
                try:
                    d1p = swe.calc_ut(j1c, GEZEGENLER["Plüton"])[0][0]
                    d2p = swe.calc_ut(j2c, GEZEGENLER["Plüton"])[0][0]
                    fark_p = abs(d1p - d2p)
                    if fark_p > 180:
                        ort_p = (d1p + (d2p + 360)) / 2 if d1p > d2p else ((d1p + 360) + d2p) / 2
                    else:
                        ort_p = (d1p + d2p) / 2
                    ort_p = ort_p % 360
                    p_burc = burclar_tr[int(ort_p / 30)]
                    p_ev = ev_hesapla(ort_p, comp_asc) if comp_asc is not None else None
                    ev_metni_p = f" <b>{p_ev}. Ev'de</b> ({ev_isimleri[p_ev - 1]})" if p_ev else ""
                    if self.mod == "ebeveyn_cocuk":
                        comp_yorum_parts.append(
                            f"<b>Composite Plüton: {p_burc}</b> ({ort_p:.1f}°){ev_metni_p}<br/>"
                            f"Ebeveyn-çocuk arasındaki derin dönüşüm, güç mücadelesi ve köklü değişim enerjisi <b>{p_burc}</b> burcunda ifade bulur. "
                            f"Birlikte en çok hangi konularda köklü dönüşümlerden geçtiğiniz, güç dengeleriniz ve ruhsal yeniden doğuşlarınız bu burcun enerjisiyle belirlenir. "
                            f"Dönüşüm ve yeniden doğuş alanlarınız <b>{burc_yorumlari.get(p_burc, '')}</b> temalarında yoğunlaşır."
                        )
                    else:
                        comp_yorum_parts.append(
                            f"<b>Composite Plüton: {p_burc}</b> ({ort_p:.1f}°){ev_metni_p}<br/>"
                            f"İlişkinin en derin dönüşüm alanı, güç dinamikleri ve köklü yeniden yapılanma enerjisi <b>{p_burc}</b> burcunda ifade bulur. "
                            f"Birlikte en çok hangi konularda köklü dönüşümlerden geçtiğiniz, güç dengeleriniz ve ruhsal yeniden doğuşlarınız bu burcun enerjisiyle belirlenir. "
                            f"Dönüşüm ve yeniden doğuş alanlarınız <b>{burc_yorumlari.get(p_burc, '')}</b> temalarında yoğunlaşır."
                        )
                except Exception:
                    pass

                story.append(Spacer(1, 10))
                for part in comp_yorum_parts:
                    story.append(Paragraph(part, styles['CardText']))
                    story.append(Spacer(1, 8))
            except Exception:
                pass
        except Exception:
            story.append(Paragraph("<i>Composite harita PDF'e eklenemedi.</i>", styles['TurkishNormal']))

        # ⚡ AÇI GRIDİ (PDF)
        story.append(Spacer(1, 15))
        baslik_karti_ekle("GEZEGEN AÇILARI HARİTASI", 
                          alt_baslik="İki harita arasındaki tüm açısal bağlantıları gösteren harita", 
                          emoji="⚡")
        story.append(Spacer(1, 10))
        try:
            grid_dosya = self.ciz_aci_gridi(dosya_adi="FBST_Aci_Gridi_PDF.png")
            cerceveli_gorsel_ekle(grid_dosya, 400, 400, "Açı Mühürü Gridi")
        except Exception:
            story.append(Paragraph("<i>Açı gridi PDF'e eklenemedi.</i>", styles['TurkishNormal']))

        # 🎯 4. BÖLÜM: REÇETELER VE EV AKTARIMLARI
        story.append(PageBreak())
        baslik_karti_ekle("EV ANALİZİ VE ÖNERİLER", emoji="🎯")

        rapor_A_pdf, rapor_B_pdf = self.karmik_ev_aktarimlari(pdf_icin=True)
        story.append(Paragraph(f"<b>Ev Aktarımları ({self.p1_isim.upper()})</b>", styles['TurkishHeading']))
        if rapor_A_pdf:
            for satir in rapor_A_pdf: story.append(Paragraph(satir, styles['TurkishNormal']))
        else: story.append(Paragraph("Ağır bir karmik ev mühürlenmesi bulunamadı.", styles['TurkishNormal']))
        
        story.append(Paragraph(f"<b>Ev Aktarımları ({self.p2_isim.upper()})</b>", styles['TurkishHeading']))
        if rapor_B_pdf:
            for satir in rapor_B_pdf: story.append(Paragraph(satir, styles['TurkishNormal']))
        else: story.append(Paragraph("Ağır bir karmik ev mühürlenmesi bulunamadı.", styles['TurkishNormal']))

        story.append(Spacer(1, 15))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
        story.append(Spacer(1, 15))
        
        # --- YENİ SİNASTRİ VE ŞİFA REÇETELERİ ENTEGRASYONU ---
        story.append(Paragraph("GEZEGEN ETKİLEŞİMLERİ", styles['TurkishHeading']))
        
        # Yeni motorumuzdan tek parça HTML dönen veriyi alıyoruz
        sinastri_html = self.sinastri_hesapla(sessiz=True)
        
        # ReportLab (PDF) kütüphanesinin desteklemediği web HTML etiketlerini (div, p, h4) 
        # senin PDF stillerinin (TurkishNormal) anlayacağı formata çeviren güvenlik filtresi:
        import re
        temiz_html = re.sub(r'<div[^>]*>', '', sinastri_html)
        temiz_html = temiz_html.replace('</div>', '<br/><br/>')
        
        temiz_html = re.sub(r'<h4[^>]*>', '<b><font size="12" color="#C47A82">', temiz_html)
        temiz_html = temiz_html.replace('</h4>', '</font></b><br/><br/>')
        
        temiz_html = re.sub(r'<p[^>]*>', '', temiz_html)
        temiz_html = temiz_html.replace('</p>', '<br/>')
        
        # Reçete madde numaralarını yeni satira tasima
        temiz_html = re.sub(r'(\d+)\)\s+', r'<br/><b>\1)</b> ', temiz_html)
        
        # İki ayrı for döngüsü yerine, filtrelenmiş şık metni tek hamlede PDF'e basıyoruz
        story.append(Paragraph(temiz_html, styles['TurkishNormal']))

        # =========================================================
        # 🌋 5. BÖLÜM: DÖNÜŞÜM SINAVLARI VE GLOBAL RADAR
        # =========================================================
        story.append(Spacer(1, 15))
        story.append(Paragraph("ÖNEMLİ DÖNEMLER", styles['TurkishHeading']))
        story.append(Paragraph(
            f"Aşağıdaki tarihler, {self.p1_isim} ve {self.p2_isim} arasındaki ilişkinin en yoğun hissedileceği, "
            "küçük olayların büyük farkındalıklara yol açabileceği dönemlerdir. "
            "Her bir durak, ilişkinizin o aşamadaki önemli dersini ve fırsatını taşır.", styles['TurkishNormal']))
        story.append(Spacer(1, 8))
        story.append(luks_cizgi_ekle(renk="#7b2ff7", kalinlik=1.0))
        story.append(Spacer(1, 8))
        kriz_tarihleri_pdf = self.kriz_tarihlerini_bul(pdf_icin=True)
        if kriz_tarihleri_pdf:
            for idx, kriz in enumerate(kriz_tarihleri_pdf):
                story.append(Paragraph(kriz, styles['TurkishNormal']))
                if idx < len(kriz_tarihleri_pdf) - 1:
                    story.append(Spacer(1, 6))
                    story.append(luks_cizgi_ekle(renk="#2d2d44", kalinlik=0.5))
                    story.append(Spacer(1, 6))
        else: story.append(Paragraph("Yakın vadede sert bir kadersel viraj görünmüyor. İlişkiniz şu an dengeli bir akışın içinde.", styles['TurkishNormal']))

        # 🔮 6. BÖLÜM: İLİŞKİ ÖNGÖRÜSÜ
        story.append(PageBreak())
        story.append(Paragraph("🔮 İLİŞKİ ÖNGÖRÜSÜ", styles['CoverTitle']))
        story.append(Paragraph("Bu bölüm ilişkinizin sırasıyla Yıllık, Aylık ve Günlük kadersel akışlarını gösterir.", styles['CoverSub']))
        story.append(Spacer(1, 30))

        baslik_karti_ekle("YILLIK ÖNGÖRÜ", alt_baslik="Güneş'in her yıl aynı tarihte burcunuza dönüş anının analizi", emoji="☀️")
        mevcut_yil = datetime.now().year
        
        for yil_fark in [0, 1]:
            hedef_yil = mevcut_yil + yil_fark
            sr_metni = self.calculate_solar_return_tema(j_ileri, hedef_yil)
            
            sr_table = Table([[Paragraph(sr_metni, styles['CardText'])]], colWidths=[500])
            sr_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8F9FA')),
                ('BOX', (0,0), (-1,-1), 1.2, HexColor('#C9A96E')),
                ('LINELEFT', (0,0), (0,0), 5, ALTIN_AMBER), 
                ('TOPPADDING', (0,0), (-1,-1), 14),
                ('BOTTOMPADDING', (0,0), (-1,-1), 14),
                ('LEFTPADDING', (0,0), (-1,-1), 18),
                ('RIGHTPADDING', (0,0), (-1,-1), 18),
            ]))
            story.append(sr_table)
            story.append(Spacer(1, 15))

        story.append(Spacer(1, 15))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
        story.append(Spacer(1, 15))
        baslik_karti_ekle("6 AYLIK DUYGUSAL ÖNGÖRÜ", alt_baslik="Ay'ın her ay burcunuzda döndüğü anın analizi", emoji="🌙")
        mevcut_ay = datetime.now().month
        
        for i in range(6):
            hedef_ay = (mevcut_ay - 1 + i) % 12 + 1
            hedef_yil = mevcut_yil + (mevcut_ay - 1 + i) // 12
            
            lr_metni = self.calculate_lunar_return_tema(j_ileri, hedef_yil, hedef_ay)
            
            lr_table = Table([[Paragraph(lr_metni, styles['CardText'])]], colWidths=[500])
            lr_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), HexColor("#FFFFFF")), 
                ('BOX', (0,0), (-1,-1), 1.2, HexColor('#C9A96E')),
                ('LINELEFT', (0,0), (0,0), 5, DERIN_MAVI), 
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 15),
                ('RIGHTPADDING', (0,0), (-1,-1), 15),
            ]))
            story.append(lr_table)
            story.append(Spacer(1, 12))

        story.append(Spacer(1, 15))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
        story.append(Spacer(1, 15))

        # --- SECONDARY PROGRESSION (İlişki Odaklı) ---
        if self.mod == "es_sevgili":
            baslik_karti_ekle("İLERLETİLMİŞ HARİTA ANALİZİ",
                              alt_baslik="1 gün = 1 yıl yöntemiyle ilişkinizin uzun vadeli gelişimi",
                              emoji="🔮")
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                "Secondary Progression, doğum haritanızın 1 gün = 1 yıl ilerlemesiyle "
                "ilişkinizin duygusal evrimini gösterir. İlerletilmiş gezegenlerinizin "
                "doğum haritanızdaki gezegenlerle yaptığı açılar, ilişkinizdeki uzun vadeli "
                "temaları ve dönüşüm süreçlerini ortaya koyar. Özellikle ilerletilmiş Ay'ın "
                "açıları, ilişkinizin duygusal ritmini belirleyen en önemli göstergelerdir.",
                styles['TurkishNormal']))
            story.append(Spacer(1, 10))

            sp_yorumlar = self.secondary_progression_yorumla()
            if sp_yorumlar:
                for yorum in sp_yorumlar:
                    if yorum.get("karsilastirma"):
                        # İlişki uyumu özeti
                        story.append(luks_cizgi_ekle(renk="#7b2ff7", kalinlik=1.0))
                        story.append(Spacer(1, 8))
                        story.append(Paragraph(
                            f"<b><font color='#7b2ff7' size='11'>İLİŞKİ UYUMU</font></b>",
                            styles['TurkishNormal']))
                        story.append(Paragraph(yorum["genel_yorum"], styles['TurkishNormal']))
                        story.append(Spacer(1, 10))
                    else:
                        # Kişi bazlı yorum
                        story.append(Spacer(1, 10))
                        story.append(Paragraph(
                            f"<b><font color='#1A1A2E' size='12'>[ {yorum['kisi']} ] — {yorum['ilerleme_yili']} Yıl İlerleme</font></b>",
                            styles['TurkishNormal']))
                        story.append(Paragraph(
                            f"İlerletilmiş Ay: <b>{yorum['ay_burcu']}</b> | İlerletilmiş Güneş: <b>{yorum['gunes_burcu']}</b>",
                            styles['TurkishNormal']))
                        story.append(Spacer(1, 6))
                        story.append(Paragraph(yorum["genel_yorum"], styles['TurkishNormal']))
                        story.append(Spacer(1, 6))

                        # Ay açıları yorumları
                        for aci_yorum in yorum.get("ay_aci_yorumlari", []):
                            aci_renk = "#C47A82" if aci_yorum["aci_turu"] in ["Kare", "Karşıt"] else "#8FB8CA"
                            donem_satiri = f"<br/><font color='#C9A96E'><b>{aci_yorum['donem']}</b></font>" if aci_yorum.get("donem") else ""
                            aci_metni = (
                                f"<font color='{aci_renk}'><b>{aci_yorum['baslik']}</b></font>{donem_satiri}<br/>"
                                f"<font color='#4A4A4A'>{aci_yorum['yorum']}</font>"
                            )
                            aci_kutu = Table([[Paragraph(aci_metni, styles['TurkishNormal'])]], colWidths=['100%'])
                            aci_kutu.setStyle(TableStyle([
                                ('BACKGROUND', (0,0), (-1,-1), HexColor("#F7F9FC")),
                                ('BOX', (0,0), (-1,-1), 0.5, HexColor(aci_renk)),
                                ('LINELEFT', (0,0), (0,0), 3, HexColor(aci_renk)),
                                ('TOPPADDING', (0,0), (-1,-1), 8),
                                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                                ('LEFTPADDING', (0,0), (-1,-1), 12),
                                ('RIGHTPADDING', (0,0), (-1,-1), 12),
                            ]))
                            story.append(aci_kutu)
                            story.append(Spacer(1, 4))

                        story.append(Paragraph(
                            f"<i>Toplam {yorum['toplam_aci']} ilerletilmiş açı tespit edildi.</i>",
                            styles['TurkishNormal']))
            else:
                story.append(Paragraph("Secondary Progression analizi hesaplanamadı.", styles['TurkishNormal']))

            story.append(Spacer(1, 15))
            story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
            story.append(Spacer(1, 15))

        baslik_karti_ekle("6 AYLIK GÜNLÜK AKIŞ", alt_baslik="Günlük gezegen hareketlerinin etkileri", emoji="⛅")
        
        gunluk_alarmlar = self.gunluk_bsp_taramasi(gun_sayisi=180, pdf_icin=True)
        
        if gunluk_alarmlar:
            for alarm in gunluk_alarmlar:
                tarih_metni = f"<b>Tarih: {alarm['tarih']}</b><br/>"
                for msg in alarm['mesajlar']:
                    tarih_metni += f"- {msg}<br/>"
                
                progress_table = Table([[Paragraph(tarih_metni, styles['TurkishNormal'])]], colWidths=[500])
                progress_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), HexColor("#F7F9FC")),
                    ('BOX', (0,0), (-1,-1), 0.5, HexColor("#E2E8F0")),
                    ('LINELEFT', (0,0), (0,0), 3, HexColor("#718096")),
                    ('TOPPADDING', (0,0), (-1,-1), 8),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                    ('LEFTPADDING', (0,0), (-1,-1), 12),
                    ('RIGHTPADDING', (0,0), (-1,-1), 12),
                ]))
                story.append(progress_table)
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("Önümüzdeki 6 ay boyunca minör bir tetiklenme bulunmuyor. Stabil bir akıştasınız.", styles['TurkishNormal']))

        # 🌟 7. BÖLÜM: KADERSEL YILDIZ MÜHÜRLERİ 🌟
        story.append(PageBreak())
        baslik_karti_ekle("SABİT YILDIZLARIN ETKİLERİ", alt_baslik="Sabit yıldızların gezegenlerle olan bağlantıları", emoji="🌟")
        story.append(Spacer(1, 10))

        try:
            # Hem Natal hem de Bağıl haritalar için tarama katmanları oluşturuyoruz
            p1_jd = swe.julday(self.p1.year, self.p1.month, self.p1.day, self.p1.hour + self.p1.minute / 60.0)
            p2_jd = swe.julday(self.p2.year, self.p2.month, self.p2.day, self.p2.hour + self.p2.minute / 60.0)

            tarama_katmanlari = [
                {"isim": f"{self.p1_isim} (Natal)", "jd": p1_jd, "bağıl": False},
                {"isim": f"{self.p2_isim} (Natal)", "jd": p2_jd, "bağıl": False},
                {"isim": f"{self.p1_isim} (İleri)", "jd": j_ileri, "bağıl": True, "vektör": "ileri"},
                {"isim": f"{self.p2_isim} (Geri)", "jd": j_geri, "bağıl": True, "vektör": "geri"}
            ]

            # ⚙️ HER BİR KATMANI (DÜNYAYI) AYRI AYRI TARAYIP KUTULUYORUZ
            for katman in tarama_katmanlari:
                
                # Her dünyaya özel şık bir alt başlık açıyoruz
                story.append(Spacer(1, 15))
                katman_baslik = f"<b><font size='12' color='#2C3E50'>🏛️ {katman['isim']}</font></b>"
                story.append(Paragraph(katman_baslik, styles['TurkishNormal']))
                story.append(Spacer(1, 8))
                
                katman_muhurleri = []

                for gezegen_adi, gezegen_id in GEZEGENLER.items():
                    try:
                        if katman["bağıl"]:
                            if katman["vektör"] == "ileri":
                                g_derecesi = self.get_bagil_position(gezegen_adi, "ileri") 
                            else:
                                g_derecesi = self.get_bagil_position(gezegen_adi, "geri")
                        else:
                            if gezegen_adi == "GAD":
                                k_derece = swe.calc_ut(katman["jd"], swe.MEAN_NODE)[0][0]
                                g_derecesi = (k_derece + 180.0) % 360.0
                            else:
                                flags = get_safe_flags(gezegen_id)
                                g_derecesi = swe.calc_ut(katman["jd"], gezegen_id, flags)[0][0]

                        # Sabit Yıldız okuyucu global fonksiyon
                        if 'kadersel_yildiz_taramasi' in globals():
                            sonuclar = kadersel_yildiz_taramasi(gezegen_adi, g_derecesi, orb_siniri=2.0)
                            if sonuclar:
                                for sonuc in sonuclar:
                                    kisisel_muhur = sonuc.replace("Kavuşumu", f"Kavuşumu [{katman['isim']}]")
                                    katman_muhurleri.append(kisisel_muhur)
                    except Exception:
                        continue

                # O Katmanda Mühür Yoksa Verilecek Zarif Uyarı
                if not katman_muhurleri:
                    story.append(Paragraph(f"<i>Bu kadersel katmanda ({katman['isim']}), belirlenen tolerans sınırlarında aktif bir sabit yıldız teması bulunmamaktadır.</i>", styles['TurkishNormal']))
                
                # O Katmanda Mühür Varsa Altın Kutular İçinde Ekrana Bas
                else:
                    # 💎 VİP TASARIM: Mühürleri altın şeritli kutulara alıyoruz
                    for muhur in katman_muhurleri:
                        satirlar = []
                        for satir in muhur.split('\n'):
                            temiz_satir = pdf_temizle(satir).strip()
                            if not temiz_satir:
                                continue
                            
                            # Metin İçi Tasarım Katmanı (Kozmik Vurgular)
                            if "Yıldız Hizalanması" in temiz_satir or "Güçlü Etki" in temiz_satir:
                                temiz_satir = f"<b><font color='#C9A96E'>{temiz_satir}</font></b>"
                            elif "Özel Yargı" in temiz_satir:
                                # Yargı kısmını dramatik Bordo/Kırmızı ve Kalın yapıyoruz
                                temiz_satir = f"<b><font color='#8B0000'>{temiz_satir}</font></b>"
                            elif ":" in temiz_satir:
                            # "AŞK (Venüs):" gibi kısımların iki noktadan öncesini kalın yap
                                parcalar = temiz_satir.split(":", 1)
                                temiz_satir = f"<b>{parcalar[0]}:</b>{parcalar[1]}"
                                
                            satirlar.append(temiz_satir)

                        # Tüm satırları tek paragrafta alt alta (<br/>) birleştir
                        kutu_icerigi = Paragraph("<br/>".join(satirlar), styles['TurkishNormal'])

                        # Kutuyu oluştur (ReportLab Table)
                        mühür_kutusu = Table([[kutu_icerigi]], colWidths=['100%'])
                        mühür_kutusu.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FDFBF7')), # Zarif Fildişi/Krem arkaplan
                            ('BOX', (0,0), (-1,-1), 1.2, colors.HexColor('#D4AF37')),   # Altın sarısı çerçeve
                            ('TOPPADDING', (0,0), (-1,-1), 12),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                            ('LEFTPADDING', (0,0), (-1,-1), 15),
                            ('RIGHTPADDING', (0,0), (-1,-1), 15),
                        ]))
                        
                        story.append(mühür_kutusu)
                        story.append(Spacer(1, 12)) # Kutular arası boşluk

        except Exception as e:
            story.append(Paragraph(f"Yıldız mühürleri işlenirken bir kalkan hatası oluştu: {str(e)}", styles['TurkishNormal']))


    # =========================================================================================
        # 👑 BÖLÜM: NESİLLER ARASI ŞİFA / KUTSAL BİRLEŞME (HIEROS) — ÇAPRAZ ASTEROİD SİNASTRİ MÜHÜRLERİ 👑
        # =========================================================================================
        try:
            story.append(PageBreak())
            if self.mod == "ebeveyn_cocuk":
                baslik_karti_ekle("ASTEROİT ETKİLEŞİMLERİ",
                                  alt_baslik="Ceres, Pallas, Vesta, Psyche, Hygiea, Euphrosyne, Nemesis, Chiron asteroitleri.",
                                  emoji="🌱")
                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    "Bu bölüm, ebeveyn ile çocuk arasındaki <b>nesiller arası asteroit etkileşimlerini</b> tarar. "
                    "Ceres (beslenme), Pallas (yaratıcılık), Vesta (adanmışlık), Psyche (ruh bağı), "
                    "Hygiea (sağlık/bakım), Euphrosyne (neşe), Nemesis (karmik denge) ve Chiron (yara-şifa) "
                    "asteroitleri arasındaki çapraz açısal temalar, ebeveyn-çocuk bağının çok boyutlu "
                    "kadersel yapısını ortaya koyar. 0-5 derece aralığındaki bu temalar, ruhlarınızın "
                    "hangi boyutlarda birleştiğini ve iyileşme potansiyelinizi gösterir.",
                    styles['TurkishNormal']))
            else:
                baslik_karti_ekle("ASTEROİT ETKİLEŞİMLERİ",
                                  alt_baslik="Juno, Ceres, Pallas, Vesta, Eros, Psyche, Sappho, Amor asteroidlerinin etkileri",
                                  emoji="👑")
                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    "Bu bölüm, partnerlerin Bağıl Dünyaları arasındaki <b>ilişki asteroidi etkileşimlerini</b> tarar. "
                    "Juno (evlilik), Ceres (beslenme), Pallas (yaratıcılık), Vesta (adanmışlık), Eros (tutku), "
                    "Psyche (ruh), Sappho (romantizm) ve Amor (koşulsuz sevgi) asteroidleri arasındaki "
                    "çapraz açısal temalar, ilişkinizin çok boyutlu kadersel yapısını ortaya koyar. "
                    "0-5 derece aralığındaki bu çapraz temaslar, ruhlarınızın hangi boyutlarda birleştiğini gösterir.",
                    styles['TurkishNormal']))
            story.append(Spacer(1, 15))

            if self.mod == "ebeveyn_cocuk":
                sagaltim_matrisi = {
                    "Koç": {"yara": "Çabuk sinirlenme paterni", "recete": "Çocuğunuzla birlikte 10 nefes egzersizi yapın."},
                    "Boğa": {"yara": "Maddi aşırı koruma", "recete": "Çocuğa küçük sorumluluklar verin, bağımsızlığını besleyin."},
                    "İkizler": {"yara": "İletişim aşırılığı veya kopukluğu", "recete": "Haftada 1 kez ekran olmadan kaliteli zaman geçirin."},
                    "Yengeç": {"yara": "Duygusal bağımlılık", "recete": "Çocuğun kendi duygularını isimlendirmesine alan açın."},
                    "Aslan": {"yara": "Takdir eksikliği veya aşırı beklenti", "recete": "Çocuğun her çabasını sözel olarak takdir edin."},
                    "Başak": {"yara": "Eleştirel mükemmeliyetçilik", "recete": "Kusurları birlikte gülümseyerek kabul edin."},
                    "Terazi": {"yara": "Kardeş veya çocuk arasında adalet arayışı", "recete": "Her çocuğun benzersizliğine özel ilgi gösterin."},
                    "Akrep": {"yara": "Kontrol ve kıskançlık", "recete": "Çocuğun gizli dünyasına saygı gösterin, kapıyı çalın."},
                    "Yay": {"yara": "Aşırı disiplin veya aşırı serbestlik", "recete": "Net sınırlar ve geniş keşif alanı dengesini bulun."},
                    "Oğlak": {"yara": "Duygusal mesafe", "recete": "Fiziksel yakınlık (sarılma) alışkanlığı edinin."},
                    "Kova": {"yara": "Aşırı bağımsızlık veya kopukluk", "recete": "Haftada 1 kez rutin kontrol ve duygusal check-in yapın."},
                    "Balık": {"yara": "Fedakarlık aşırılığı ve sisli sınırlar", "recete": "Kendi ihtiyaçlarınızı da çocuğa model olun."}
                }
            else:
                sagaltim_matrisi = {
                    "Koç": {"yara": "Mükemmel olma stresi", "recete": "Fakirlere veya sokak hayvanlarına et verin."},
                    "Boğa": {"yara": "Statü kaybı korkusu", "recete": "Çocuğa veya kediye süt verin. Küçük hesaplar yapmayın."},
                    "İkizler": {"yara": "Sınır ihlali", "recete": "İnsanlara kitap ve bilgi hediye edin."},
                    "Yengeç": {"yara": "Güvenlik açığı", "recete": "İnsanları doyurun, evlerine eksik eşyalar alın."},
                    "Aslan": {"yara": "Sevgisizlik korkusu", "recete": "Yetim çocukları eğlendirin, ihtiyaçlarını giderin."},
                    "Başak": {"yara": "Eleştirel mükemmeliyetçilik", "recete": "Kusurları kabul etmeyi öğrenin. Rahat olun."},
                    "Terazi": {"yara": "Adaletsizlik ve rekabet", "recete": "Arabuluculuk yapın. Fakirlere yardım edin."},
                    "Akrep": {"yara": "İhanet korkusu", "recete": "Geçmiş karmik hesaplaşmalardır. Affetmeyi öğrenin."},
                    "Yay": {"yara": "İnançlara saygısızlık", "recete": "Farklı kültürlerin eserlerini hediye edin."},
                    "Oğlak": {"yara": "Onur kırılması", "recete": "Başkalarına iş bulun. Yardımsever olun."},
                    "Kova": {"yara": "Kontrol edilme korkusu", "recete": "Kuş besleyin, onlara buğday atın."},
                    "Balık": {"yara": "Gizlilik ve manipülasyon", "recete": "Balık verin, manevi/dini kitaplar dağıtın."}
                }

            def yerel_zodyak_bul(derece):
                burclar = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
                return burclar[int(derece / 30) % 12], derece % 30

            def jd_derece_al(jd, gezegen_adi):
                try:
                    if gezegen_adi == "KAD": 
                        return swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
                    elif gezegen_adi == "GAD":
                        return (swe.calc_ut(jd, swe.MEAN_NODE)[0][0] + 180.0) % 360.0
                    else:
                        gez_id = GEZEGENLER.get(gezegen_adi)
                        if gez_id is not None:
                            try:
                                flags = get_safe_flags(gez_id)
                                return swe.calc_ut(jd, gez_id, flags)[0][0]
                            except Exception:
                                pass
                        return asteroit_tahmini_derece(gezegen_adi, jd)
                except Exception:
                    return asteroit_tahmini_derece(gezegen_adi, jd)

            if self.mod == "ebeveyn_cocuk":
                isim_a = f"Ebeveyn ({self.p1_isim})"
                isim_b = f"Çocuk ({self.p2_isim})"
                taranacak_asteroidler = ["Ceres", "Pallas", "Vesta", "Psyche", "Hygiea", "Euphrosyne", "Nemesis", "Chiron"]
                hedef_gezegenler = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter", "Satürn", "Uranüs", "Neptün", "Plüton"]
            else:
                isim_a = f"Situa A ({self.p1_isim})"
                isim_b = f"Situa B ({self.p2_isim})"
                taranacak_asteroidler = ["Juno", "Ceres", "Pallas", "Vesta", "Eros", "Psyche", "Sappho", "Amor"]
                hedef_gezegenler = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter", "Satürn", "Uranüs", "Neptün", "Plüton", "Chiron"]

            taramalar = [
                {"kaynak_jd": j_ileri, "hedef_jd": j_geri, "sahip": isim_a, "hedef": isim_b},
                {"kaynak_jd": j_geri, "hedef_jd": j_ileri, "sahip": isim_b, "hedef": isim_a}
            ]

            for tarama in taramalar:
                satirlar = []
                toplam_muhur = 0

                for asteroit_adi in taranacak_asteroidler:
                    ast_deg = jd_derece_al(tarama["kaynak_jd"], asteroit_adi)
                    if ast_deg is None:
                        continue

                    ast_burc, _ = yerel_zodyak_bul(ast_deg)

                    for hedef_adi in hedef_gezegenler:
                        hedef_deg = jd_derece_al(tarama["hedef_jd"], hedef_adi)
                        if hedef_deg is None:
                            continue

                        fark = abs(ast_deg - hedef_deg)
                        if fark > 180:
                            fark = 360 - fark

                        if fark <= 5.0:
                            toplam_muhur += 1
                            yorum_key = (asteroit_adi, hedef_adi)
                            varsayilan_yorum = f"{asteroit_adi} - {hedef_adi} karmik teması"
                            _aktif_mod = st.session_state.get("sim_modu", "es_sevgili")
                            if _aktif_mod == "ebeveyn_cocuk" and ASTEROID_SINASTRI_YORUMLARI_EBEVEYN:
                                yorum = ASTEROID_SINASTRI_YORUMLARI_EBEVEYN.get(yorum_key, ASTEROID_SINASTRI_YORUMLARI.get(yorum_key, varsayilan_yorum))
                            else:
                                yorum = ASTEROID_SINASTRI_YORUMLARI.get(yorum_key, varsayilan_yorum)

                            if fark <= 0.5:
                                durum = "KUSURSUZ MÜHÜR"
                                guc_seviyesi = "⭐⭐⭐⭐⭐ Kaderin Kesin Mührü"
                                renk = "#C9A96E"
                            elif fark <= 1.0:
                                durum = "TAŞ MÜHÜR"
                                guc_seviyesi = "⭐⭐⭐⭐ Güçlü Kadersel Bağ"
                                renk = "#2E7D32"
                            elif fark <= 2.0:
                                durum = "TUNÇ MÜHÜR"
                                guc_seviyesi = "⭐⭐⭐ Belirgin Etki"
                                renk = "#1565C0"
                            elif fark <= 3.5:
                                durum = "GÜMÜŞ MÜHÜR"
                                guc_seviyesi = "⭐⭐ Hafif Ama Kalıcı İz"
                                renk = "#6B7280"
                            else:
                                durum = "BRONZ MÜHÜR"
                                guc_seviyesi = "⭐ Uzaktan Gelen Fısıltı"
                                renk = "#9E9E9E"

                            sagaltim = sagaltim_matrisi.get(ast_burc, {"yara": "Yetersiz denge", "recete": "Cömert olun."})

                            satirlar.append(
                                f"<font color='{renk}'><b>* {durum} ({fark:.1f}°): {tarama['sahip']} {asteroit_adi} ({ast_burc}) <-> {tarama['hedef']} {hedef_adi}</b></font><br/><br/>"
                                f"<font color='#4A4A4A'><i>{yorum}</i></font><br/><br/>"
                                f"<font color='#6B7280' size='8'>  Kuvvet: {guc_seviyesi} | Safa: {sagaltim['recete']}</font><br/><br/><br/>"
                            )

                if toplam_muhur == 0:
                    satirlar.append(f"<font color='#4A5568'><i>{tarama['sahip']} ile {tarama['hedef']} arasında 0-5° orb sınırında asteroid sinastri mührü saptanmadı.</i></font><br/>")

                kutu_basligi = f"<b><font color='#1A1A2E' size='12'>[ {tarama['sahip']} → {tarama['hedef']} ] ASTEROİD SİNASTRİ MATRİSİ ({toplam_muhur} Mühür)</font></b><br/><br/>"
                kutu_metni = kutu_basligi + "".join(satirlar)
                hieros_kutu = Table([[Paragraph(kutu_metni, styles['TurkishNormal'])]], colWidths=['100%'])
                hieros_kutu.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                    ('BOX', (0,0), (-1,-1), 1.2, ALTIN_AMBER),
                    ('PADDING', (0,0), (-1,-1), 15),
                ]))
                story.append(hieros_kutu)
                story.append(Spacer(1, 15))

        except Exception as e:
            story.append(Paragraph(f"<font color='red'><b>Kritik Sistem Hatası (Asteroid Sinastri Modülü):</b> {str(e)}</font>", styles['Normal']))
        # =========================================================================================
        # BÖLÜMÜN SONU
        # =========================================================================================  
        
        # =========================================================================================
        # 🌙 ARAP NOKTALARI - İLİŞKİ VE EVLİLİK ANALİZİ (PDF)
        # =========================================================================================
        try:
            story.append(PageBreak())
            if self.mod == "ebeveyn_cocuk":
                baslik_karti_ekle("ARAP NOKTALARI", alt_baslik="Ebeveyn-çocuk bağının farklı boyutları", emoji="🌙")
                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    "Bu bölüm, ebeveyn-çocuk bağının koruma, eğitim, bağlanma ve gelişim gibi boyutlarını "
                    "Arap Noktaları açısından inceler.",
                    styles['TurkishNormal']))
            else:
                baslik_karti_ekle("ARAP NOKTALARI", alt_baslik="İlişkinin farklı boyutlarının analizi", emoji="🌙")
                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    "Bu bölüm, ilişkinizin evlilik, aşk, tutku, sadakat gibi boyutlarını "
                    "Arap Noktaları açısından inceler.",
                    styles['TurkishNormal']))
            story.append(Spacer(1, 10))
            try:
                arap_radar_dosya = self.ciz_arap_noktalari_radar(dosya_adi="FBST_Arap_Radar_PDF.png")
                cerceveli_gorsel_ekle(arap_radar_dosya, 400, 400, "Arap Noktaları Radar Karşılaştırması")
            except Exception:
                story.append(Paragraph("<i>Arap Noktaları radar grafiği PDF'e eklenemedi.</i>", styles['TurkishNormal']))
            story.append(Spacer(1, 15))
            
            arap_noktalari = self.arap_noktasi_hesapla()
            arap_sinastri = self.arap_noktasi_sinastri_analizi()
            
            for isim in [self.p1_isim, self.p2_isim]:
                if isim in arap_noktalari:
                    story.append(Paragraph(f"<b><font color='#1A1A2E' size='12'>[ {isim} ] ARAP NOKTALARI</font></b>", styles['TurkishNormal']))
                    story.append(Spacer(1, 8))
                    
                    for nokta_adi, bilgi in arap_noktalari[isim].items():
                        gece_emoji = "🌙" if bilgi["gece_charti"] else "☀️"
                        pozisyon = dereceyi_dakikaya_cevir(bilgi['derece'])
                        tek_satir = (
                            f"<font color='#1A1A2E'><b>{gece_emoji} {nokta_adi}</b></font><br/>"
                            f"<font color='#4A4A4A'>Konum: {pozisyon} | Ev: {bilgi['ev']}</font><br/>"
                            f"<font color='#4A5568'><i>{bilgi['burc_yorum']}</i></font><br/>"
                            f"<font color='#4A5568'><i>{bilgi['ev_yorumu']}</i></font>"
                        )
                        tek_kutu = Table([[Paragraph(tek_satir, styles['TurkishNormal'])]], colWidths=['100%'])
                        tek_kutu.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                            ('BOX', (0,0), (-1,-1), 0.8, ALTIN_AMBER),
                            ('PADDING', (0,0), (-1,-1), 10),
                        ]))
                        story.append(tek_kutu)
                        story.append(Spacer(1, 6))
            
            # Sinastri Analizi
            if arap_sinastri:
                story.append(Paragraph(f"<b><font color='#1A1A2E' size='12'>[ SİNASTRİ ] ARAP NOKTASI BAĞLARI</font></b>", styles['TurkishNormal']))
                story.append(Spacer(1, 8))
                
                sinastri_satirlar = []
                for bag in arap_sinastri:
                    if bag["tip"] == "nokta_nokta":
                        sinastri_satirlar.append(
                            f"<font color='#1A1A2E'><b>* {bag['nokta']} Noktasi Eslesmesi (Orb: {bag['fark']} derece)</b></font><br/>"
                            f"<font color='#4A4A4A'><i>{bag['yorum']}</i></font>"
                        )
                    elif bag["tip"] == "capraz_nokta":
                        sinastri_satirlar.append(
                            f"<font color='#1A1A2E'><b>* {bag['nokta_a']} <-> {bag['nokta_b']} Capraz Bagi (Orb: {bag['fark']} derece)</b></font><br/>"
                            f"<font color='#4A4A4A'><i>{bag['yorum']}</i></font>"
                        )
                    elif bag["tip"] == "nokta_gezegen":
                        sinastri_satirlar.append(
                            f"<font color='#8B0000'><b>* {bag['kaynak']}'in {bag['nokta']} -> {bag['hedef']}'in {bag['gezegen']} Kavusumu ({bag['guc']}, Orb: {bag['fark']} derece)</b></font><br/>"
                            f"<font color='#4A4A4A'><i>{bag['yorum']}</i></font>"
                        )
                
                if sinastri_satirlar:
                    for satir in sinastri_satirlar:
                        sinastri_kutu = Table([[Paragraph(satir, styles['TurkishNormal'])]], colWidths=['100%'])
                        sinastri_kutu.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                            ('BOX', (0,0), (-1,-1), 0.8, ALTIN_AMBER),
                            ('PADDING', (0,0), (-1,-1), 10),
                        ]))
                        story.append(sinastri_kutu)
                        story.append(Spacer(1, 6))
            
        except Exception as e:
            story.append(Paragraph(f"<font color='red'><b>Kritik Sistem Hatası (Arap Noktaları Modülü):</b> {str(e)}</font>", styles['Normal']))

        # =========================================================================================
        # 📊 GELİŞİM DÖNEMLERİ & POTANSİYEL ANALİZİ (Sadece Ebeveyn-Çocuk PDF)
        # =========================================================================================
        if self.mod == "ebeveyn_cocuk":
            try:
                story.append(PageBreak())
                baslik_karti_ekle("GELİŞİM DÖNEMLERİ & YETENEKLER",
                                  alt_baslik="Çocuğun gelişim dönemleri ve potansiyel alanları",
                                  emoji="📊")
                story.append(Spacer(1, 10))

                # --- GELİŞİM DÖNEMLERİ ---
                story.append(Paragraph("<b><font color='#1A1A2E' size='12'>GELİŞİM DÖNEMLERİ</font></b>", styles['TurkishNormal']))
                story.append(Paragraph(
                    "<i><font color='#6B7280'><b>Not:</b> Bu bölüm çocuğun natal haritasına göre çıkarılmıştır. "
                    "Gelişim dönemleri, çocuğunuzun doğum tarihine göre hesaplanan aktif dönemleri ve "
                    "bu dönemdeki ebeveyn-çocuk etkileşim yapılarını gösterir.</font></i>",
                    styles['TurkishNormal']))
                story.append(Spacer(1, 6))
                story.append(Paragraph(
                    "Her bir gezegenin developmental period'u, "
                    "çocuğunuzun hayatının farklı aşamalarındaki temel ihtiyaçlarını ve "
                    "sizin ebeveyn olarak bu dönemdeki en etkili tutumunuzu gösterir.",
                    styles['TurkishNormal']))
                story.append(Spacer(1, 10))

                gelisim_sonuclari = self.gelisim_donemleri_hesapla()
                if gelisim_sonuclari:
                    for satir in gelisim_sonuclari:
                        konum_bilgisi = ""
                        if satir.get('burc') and satir.get('ev'):
                            konum_bilgisi = f" — <i>{satir['burc']}, {satir['ev']}. Ev</i>"
                        gelisim_metni = (
                            f"<font color='#1A1A2E'><b>{satir['gezegen']}{konum_bilgisi} — {satir['donem']}</b></font><br/>"
                            f"<font color='#4A4A4A'>{satir['metin']}</font>"
                        )
                        gelisim_kutu = Table([[Paragraph(gelisim_metni, styles['TurkishNormal'])]], colWidths=['100%'])
                        gelisim_kutu.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                            ('BOX', (0,0), (-1,-1), 0.8, ALTIN_AMBER),
                            ('PADDING', (0,0), (-1,-1), 10),
                        ]))
                        story.append(gelisim_kutu)
                        story.append(Spacer(1, 6))
                else:
                    story.append(Paragraph("Gelişim dönemi verisi hesaplanamadı.", styles['TurkishNormal']))

                story.append(Spacer(1, 15))
                story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
                story.append(Spacer(1, 15))

                # --- POTANSİYEL VE YETENEK ALANLARI ---
                story.append(Paragraph("<b><font color='#1A1A2E' size='12'>POTANSİYEL VE YETENEK ALANLARI</font></b>", styles['TurkishNormal']))
                story.append(Paragraph(
                    "<i><font color='#6B7280'><b>Not:</b> Bu bölüm çocuğun natal haritasına göre çıkarılmıştır. "
                    "Çocuğunuzun kendi gezegenleri arasındaki açılar değerlendirilerek "
                    "doğal yetenek ve potansiyel alanları tespit edilmiştir.</font></i>",
                    styles['TurkishNormal']))
                story.append(Spacer(1, 6))
                story.append(Paragraph(
                    "Bu bölüm, çocuğunuzun hangi alanlarda doğal bir yatkınlığa sahip olduğunu ve "
                    "sizin bu yetenekleri nasıl besleyebileceğinizi gösterir.",
                    styles['TurkishNormal']))
                story.append(Spacer(1, 10))

                potansiyel_sonuclari = self.potansiyel_hesapla()
                if potansiyel_sonuclari:
                    gorulen_alanlar = set()
                    for satir in potansiyel_sonuclari:
                        if satir['alan'] not in gorulen_alanlar:
                            gorulen_alanlar.add(satir['alan'])
                            potansiyel_metni = (
                                f"<font color='#1A1A2E'><b>{satir['alan']} ({satir['aci']} — {satir['aci_turu']} Açısı)</b></font><br/>"
                                f"<font color='#4A4A4A'>{satir['metin']}</font>"
                            )
                            potansiyel_kutu = Table([[Paragraph(potansiyel_metni, styles['TurkishNormal'])]], colWidths=['100%'])
                            potansiyel_kutu.setStyle(TableStyle([
                                ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                                ('BOX', (0,0), (-1,-1), 0.8, ALTIN_AMBER),
                                ('PADDING', (0,0), (-1,-1), 10),
                            ]))
                            story.append(potansiyel_kutu)
                            story.append(Spacer(1, 6))
                else:
                    story.append(Paragraph("Belirgin bir potansiyel alanı tespit edilemedi.", styles['TurkishNormal']))

                story.append(Spacer(1, 15))
                story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
                story.append(Spacer(1, 15))

                # --- MESLEK YÖNLENDİRME ÖNERİLERİ ---
                story.append(Paragraph("<b><font color='#1A1A2E' size='12'>MESLEK YÖNLENDİRME ÖNERİLERİ</font></b>", styles['TurkishNormal']))
                story.append(Paragraph(
                    "<i><font color='#6B7280'><b>Not:</b> Bu bölüm, çocuğunuzun potansiyel ve yetenek alanlarının "
                    "sentezine dayanmaktadır. Çocuğunuzun doğal yatkınlıkları ve güçlü yönleri değerlendirilerek "
                    "en uygun meslek dalları önerilmiştir.</font></i>",
                    styles['TurkishNormal']))
                story.append(Spacer(1, 6))
                story.append(Paragraph(
                    "Aşağıdaki öneriler, çocuğunuzun natal haritasındaki gezegen açılarının "
                    "potansiyel alanlarıyla eşleştirilmesi sonucu ortaya çıkmıştır. "
                    "Her öneri, çocuğunuzun güçlü yönlerini ve doğal yatkınlıklarını yansıtır.",
                    styles['TurkishNormal']))
                story.append(Spacer(1, 10))

                try:
                    konumlar = self.gezegen_konum_analizi()
                    meslek_onerileri = self.meslek_onerileri()
                    if meslek_onerileri:
                        # Top-6 kategori sıralaması
                        sirali = sorted(meslek_onerileri, key=lambda x: x['puan'], reverse=True)
                        ranking_html = "<font color='#1A1A2E'><b>POTANSİYEL ALANLARI SIRALAMASI:</b></font><br/>"
                        for j, r in enumerate(sirali[:6]):
                            medal = ""
                            if j == 0: medal = " [1.]"
                            elif j == 1: medal = " [2.]"
                            ranking_html += f"<font color='#4A4A4A'>{j+1}. <b>{r['alan']}</b> — {r['puan']:.1f} puan (%{r['yuzde']}){medal}</font><br/>"
                        ranking_kutu = Table([[Paragraph(ranking_html, styles['TurkishNormal'])]], colWidths=['100%'])
                        ranking_kutu.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), HexColor("#F7F3E9")),
                            ('BOX', (0,0), (-1,-1), 0.8, ALTIN_AMBER),
                            ('PADDING', (0,0), (-1,-1), 10),
                        ]))
                        story.append(ranking_kutu)
                        story.append(Spacer(1, 10))

                        for i, oneri in enumerate(meslek_onerileri, 1):
                            aci_sayisi = oneri.get('aci_sayisi', 0)
                            bonus_not = f" ({aci_sayisi} aci, {oneri['puan']:.1f} puan)"
                            oneri_baslik = f"{i}. {oneri['alan']} — %{oneri['yuzde']}{bonus_not}"
                            meslek_satirlari = ""
                            for m in oneri["meslekler"]:
                                meslek_satirlari += f"<br/>• <b>{m['meslek']}</b> — {m['aciklama']}"
                            kisisel_yorum = ""
                            if konumlar:
                                gezegen_listesi = oneri.get('gezegenler', [])
                                kisisel_yorum = self.meslek_kisisel_yorum(oneri['alan'], gezegen_listesi, konumlar)
                            if kisisel_yorum:
                                meslek_satirlari += f"<br/><br/><font color='#C9A96E'><i>{kisisel_yorum}</i></font>"
                            oneri_metni = (
                                f"<font color='#1A1A2E'><b>{oneri_baslik}</b></font><br/>"
                                f"<font color='#4A4A4A'>{meslek_satirlari}</font>"
                            )
                            oneri_kutu = Table([[Paragraph(oneri_metni, styles['TurkishNormal'])]], colWidths=['100%'])
                            oneri_kutu.setStyle(TableStyle([
                                ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                                ('BOX', (0,0), (-1,-1), 0.8, ALTIN_AMBER),
                                ('PADDING', (0,0), (-1,-1), 10),
                            ]))
                            story.append(oneri_kutu)
                            story.append(Spacer(1, 6))
                    else:
                        story.append(Paragraph("Meslek yönlendirme için yeterli potansiyel alanı tespit edilemedi.", styles['TurkishNormal']))
                except Exception as e:
                    story.append(Paragraph(f"<font color='red'><b>Meslek Yönlendirme Hatası:</b> {str(e)}</font>", styles['Normal']))

            except Exception as e:
                story.append(Paragraph(f"<font color='red'><b>Kritik Sistem Hatası (Gelişim & Potansiyel Modülü):</b> {str(e)}</font>", styles['Normal']))

        # 📜 NİHAİ BÖLÜM (PDF'in en sonuna, return dosya_adi'ndan hemen önce ekle)
        # =========================================================
        # =========================================================================================
        # 📜 NİHAİ KADERSEL KONTRAT ÖZETİ (PARLAK FİNAL)
        # =========================================================================================
        story.append(PageBreak())
        story.append(Spacer(1, 20))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=3.0))
        story.append(Spacer(1, 10))
        if self.mod == "ebeveyn_cocuk":
            baslik_karti_ekle("ÖZET VE DEĞERLENDİRME", alt_baslik="Ebeveyn-çocuk bağının genel değerlendirmesi", emoji="📜")
        else:
            baslik_karti_ekle("ÖZET VE DEĞERLENDİRME", alt_baslik="İlişkinin genel değerlendirmesi", emoji="📜")
        story.append(Spacer(1, 8))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=3.0))
        story.append(Spacer(1, 15))

        try:
            # --- 1. TEMEL METRİKLER ---
            tork = round(self.calculate_tork_skoru(), 1)
            fraktal = round(self.calculate_fraktal_uyum(), 1)
            ks_yil = self.calculate_ks()
            altin_oran_metni = self.calculate_altin_oran_muhru()

            # Yükselenleri hesapla
            j_ileri, j_geri = self.get_julian_dates()
            asc_A = self.yukselen_bul(j_ileri)
            asc_B = self.yukselen_bul(j_geri)

            # Sinastri istatistikleri
            sinastri_html = self.sinastri_hesapla(sessiz=True)
            import re
            toplam_kavusum = len(re.findall(r'Kavuşum|Birleşme', sinastri_html))
            toplam_kare = len(re.findall(r'Kare', sinastri_html))
            toplam_3gen = len(re.findall(r'Üçgen', sinastri_html))
            toplam_karsit = len(re.findall(r'Karşıt', sinastri_html))
            toplam_sextil = len(re.findall(r'Sekstil', sinastri_html))
            toplam_aci = toplam_kavusum + toplam_kare + toplam_3gen + toplam_karsit + toplam_sextil

            guclu_acilar_text = []

            # Arap Noktaları özeti
            try:
                arap_noktalari = self.arap_noktasi_hesapla()
                arap_ozet = {}
                for isim in [self.p1_isim, self.p2_isim]:
                    if isim in arap_noktalari:
                        if self.mod == "ebeveyn_cocuk":
                            nok1 = arap_noktalari[isim].get("Baba Noktası", {})
                            nok2 = arap_noktalari[isim].get("Anne Noktası", {})
                            arap_ozet[isim] = {
                                "evlilik": f"{nok1.get('derece', 0):.1f}° {nok1.get('burc', '?')}",
                                "ask": f"{nok2.get('derece', 0):.1f}° {nok2.get('burc', '?')}"
                            }
                        else:
                            evlilik_noktasi = arap_noktalari[isim].get("Evlilik Noktası", {})
                            ask_noktasi = arap_noktalari[isim].get("Aşk Noktası", {})
                            arap_ozet[isim] = {
                                "evlilik": f"{evlilik_noktasi.get('derece', 0):.1f}° {evlilik_noktasi.get('burc', '?')}",
                                "ask": f"{ask_noktasi.get('derece', 0):.1f}° {ask_noktasi.get('burc', '?')}"
                            }
            except Exception:
                arap_ozet = {}

            # --- ANA METRİK KUTUSU ---
            metrik_data = [
                ["ILISKI ANALIZI RAPORU", "", "", ""],
                ["Bag Gucu", f"{tork}/10", "Uyum Oranı", f"%{fraktal}"],
                ["Yas Farki Etkisi", f"{ks_yil:.2f} Yil", "Toplam Aci", f"{toplam_aci}"],
                [f"{self.p1_isim} Yukselen", asc_A, f"{self.p2_isim} Yukselen", asc_B],
            ]
            metrik_tablo = Table(metrik_data, colWidths=['25%', '25%', '25%', '25%'])
            metrik_tablo.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), '#1A1A2E'),
                ('TEXTCOLOR', (0,0), (-1,0), '#C9A96E'),
                ('FONTSIZE', (0,0), (-1,0), 14),
                ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
                ('SPAN', (0,0), (-1,0)),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,1), (-1,-1), 'DejaVuSans'),
                ('FONTSIZE', (0,1), (-1,-1), 10),
                ('BACKGROUND', (0,1), (-1,-1), '#0D1117'),
                ('TEXTCOLOR', (0,1), (-1,-1), '#E0E0E0'),
                ('BOX', (0,0), (-1,-1), 2.5, '#C9A96E'),
                ('INNERGRID', (0,0), (-1,-1), 0.5, '#333333'),
                ('TOPPADDING', (0,0), (-1,-1), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LINEBELOW', (0,0), (-1,0), 2, '#C9A96E'),
            ]))
            story.append(metrik_tablo)
            story.append(Spacer(1, 15))

            # --- SİNASTRİ DAĞILIMI ---
            dagilim_data = [
                ["GEZEGEN ACI DAGILIMI", "ADET", "ANLAMI"],
                ["Kavusum (Birlesme)", str(toplam_kavusum), "Guclu cekim ve uyum"],
                ["Ucgen (Akis)", str(toplam_3gen), "Dogal uyum ve sans akisi"],
                ["Sekstil (Firsat)", str(toplam_sextil), "Yaratici firsat ve destek"],
                ["Kare (Mucadele)", str(toplam_kare), "Gelisim sinavi ve dinamizm"],
                ["Karsit (Gerilim)", str(toplam_karsit), "Farkindalik ve denge arayisi"],
            ]
            dagilim_tablo = Table(dagilim_data, colWidths=['40%', '15%', '45%'])
            dagilim_tablo.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), '#1A1A2E'),
                ('TEXTCOLOR', (0,0), (-1,0), '#C9A96E'),
                ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 11),
                ('FONTNAME', (0,1), (-1,-1), 'DejaVuSans'),
                ('FONTSIZE', (0,1), (-1,-1), 10),
                ('ALIGN', (1,0), (1,-1), 'CENTER'),
                ('BACKGROUND', (0,1), (-1,-1), '#0D1117'),
                ('TEXTCOLOR', (0,1), (-1,-1), '#D1D5DB'),
                ('BOX', (0,0), (-1,-1), 2, '#C9A96E'),
                ('INNERGRID', (0,0), (-1,-1), 0.3, '#222222'),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ('LINEBELOW', (0,0), (-1,0), 2, '#C9A96E'),
            ]))
            story.append(dagilim_tablo)
            story.append(Spacer(1, 15))

            # --- EN GÜÇLÜ AÇILAR ---
            if guclu_acilar_text:
                story.append(Paragraph("<b><font color='#C9A96E' size='11'>ÖNE ÇIKAN KADERSEL BAĞLAR</font></b>", styles['TurkishNormal']))
                story.append(Spacer(1, 8))
                for i, aci_text in enumerate(guclu_acilar_text, 1):
                    aci_kutu = Table([[Paragraph(
                        f"<font color='#C9A96E'><b>* {aci_text}</b></font>",
                        styles['TurkishNormal']
                    )]], colWidths=['100%'])
                    aci_kutu.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), '#0D1117'),
                        ('BOX', (0,0), (-1,-1), 1, '#C9A96E'),
                        ('PADDING', (0,0), (-1,-1), 10),
                    ]))
                    story.append(aci_kutu)
                    story.append(Spacer(1, 6))

            # --- ARAP NOKTALARI ÖZETİ ---
            if arap_ozet:
                story.append(Spacer(1, 10))
                story.append(Paragraph("<b><font color='#C9A96E' size='11'>ARAP NOKTALARI — KADERSEL KAPILAR</font></b>", styles['TurkishNormal']))
                story.append(Spacer(1, 8))
                for isim in [self.p1_isim, self.p2_isim]:
                    if isim in arap_ozet:
                        oz = arap_ozet[isim]
                        if self.mod == "ebeveyn_cocuk":
                            _etiket1, _etiket2 = "Baba", "Anne"
                        else:
                            _etiket1, _etiket2 = "Evlilik", "Ask"
                        arap_satir = Table([[
                            Paragraph(f"<font color='#C9A96E'><b>{isim}</b></font>", styles['TurkishNormal']),
                            Paragraph(f"<font color='#D1D5DB'>{_etiket1}: {oz['evlilik']}</font>", styles['TurkishNormal']),
                            Paragraph(f"<font color='#D1D5DB'>{_etiket2}: {oz['ask']}</font>", styles['TurkishNormal']),
                        ]], colWidths=['25%', '37%', '38%'])
                        arap_satir.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), '#0D1117'),
                            ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'),
                            ('FONTSIZE', (0,0), (-1,-1), 10),
                            ('BOX', (0,0), (-1,-1), 0.5, '#444444'),
                            ('PADDING', (0,0), (-1,-1), 8),
                            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ]))
                        story.append(arap_satir)
                        story.append(Spacer(1, 4))

            # --- NİHAİ YORUM ---
            story.append(Spacer(1, 15))
            story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
            story.append(Spacer(1, 10))

            # Nihai yorum
            if toplam_kavusum >= 3:
                buyuk_guc = "Kuvvetli Kavuşum Gücü"
                buyuk_aciklama = f"{toplam_kavusum} adet kavuşum, bu ilişkinin kozmik bir manyetik alanla birbirine kenetlendiğini gösteriyor. Bu kadar yoğun birleşme noktası nadiren görülür."
            elif toplam_3gen >= 3:
                buyuk_guc = "Doğal Akış ve Uyum"
                buyuk_aciklama = f"{toplam_3gen} adet üçgen açı, ilişkinizin doğuştan uyumlu ve akıcı olduğunu kanıtlıyor. Evren bu birlikteliği kolaylaştırmak için elinden geleni yapıyor."
            elif toplam_kare >= 3:
                buyuk_guc = "Gelişim ve Dönüştürme Gücü"
                buyuk_aciklama = f"{toplam_kare} adet kare açı, bu ilişkinin kolay olmadığını ama her sınavdan geçtiğinizde çok daha güçlü çıktığınızı gösteriyor. Savaşçı bir ruh eşi birlikteliği."
            else:
                buyuk_guc = "Dengeli Kadersel İttifak"
                buyuk_aciklama = "Açı dağılımı dengeli; bu ilişki hem huzur hem de gelişim alanlarını eşit ölçüde sunuyor."

            nihai_yorum = (
                f"<b><font color='#8B0000' size='12'>GENEL DEĞERLENDİRME:</font></b><br/><br/>"
                f"<font color='#8B0000'><b>{self.p1_isim}</b> ve <b>{self.p2_isim}</b> arasındaki bu bağ, "
                f"gezegen konumlarının ortaya koyduğu özellikler taşıyor. Yaş farkı etkisi {ks_yil:.2f} yıl, "
                f"bağ gücü ise {tork}/10 olarak hesaplanmıştır.</font><br/><br/>"
                f"<font color='#8B0000'><b>* {buyuk_guc}:</b></font> "
                f"<font color='#8B0000'>{buyuk_aciklama}</font><br/><br/>"
                f"<font color='#8B0000'>{altin_oran_metni.replace('✨ ', '').replace('🌊 ', '').replace('📏 ', '')}</font><br/><br/>"
                f"<font color='#8B0000'><b>ÖZET:</b> Yukarıdaki analizler, iki kişi arasındaki bağın farklı boyutlarını "
                f"göstermektedir. Gezegen konumları, açılar ve diğer astrolojik veriler "
                f"bu raporun temelini oluşturur.</font>"
            )
            story.append(Paragraph(nihai_yorum, styles['TurkishNormal']))
            story.append(Spacer(1, 30))

            # --- NİHAİ MÜHÜR ---
            muhur_data = [
                ["RAPOR ÖZETİ", ""],
                [f"Bag Gucu: {tork}/10", f"Uyum Orani: %{fraktal}"],
                [f"Toplam Aci: {toplam_aci} | Kavusum: {toplam_kavusum}", f"Yas Farki: {ks_yil:.2f} Yil"],
                ["FAST - Fatih Asartepe Sinastri Tekniği v3.0", ""],
            ]
            muhur_tablo = Table(muhur_data, colWidths=['50%', '50%'])
            muhur_tablo.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), '#C9A96E'),
                ('TEXTCOLOR', (0,0), (-1,0), '#1A1A2E'),
                ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 14),
                ('SPAN', (0,0), (-1,0)),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,1), (-1,-1), 'DejaVuSans'),
                ('FONTSIZE', (0,1), (-1,-1), 10),
                ('BACKGROUND', (0,1), (-1,-1), '#0D1117'),
                ('TEXTCOLOR', (0,1), (-1,-1), '#E0E0E0'),
                ('BOX', (0,0), (-1,-1), 3, '#C9A96E'),
                ('INNERGRID', (0,0), (-1,-1), 0.5, '#444444'),
                ('TOPPADDING', (0,0), (-1,-1), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
                ('LINEBELOW', (0,0), (-1,0), 3, '#C9A96E'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(muhur_tablo)

        except Exception as e:
            story.append(Paragraph(f"<font color='red'>Nihai özet oluşturulurken hata: {str(e)}</font>", styles['TurkishNormal']))

        # FİNAL DOKÜMAN BİRLEŞTİRİCİ
        doc.build(story, onFirstPage=kapak_ciz, onLaterPages=sonraki_sayfa_ciz)

        # Asartepe_Kapak.pdf'i 1. sayfaya, kapak1.png'li sayfayı 2. sayfaya al
        asartepe_pdf_yolu = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Asartepe_Kapak.pdf")
        if os.path.exists(asartepe_pdf_yolu):
            try:
                from pypdf import PdfReader, PdfWriter
                writer = PdfWriter()

                # Asartepe_Kapak.pdf — sadece 1. sayfa
                asartepe_reader = PdfReader(asartepe_pdf_yolu)
                writer.add_page(asartepe_reader.pages[0])

                # Sonra mevcut PDF'in tüm sayfaları
                icerik_reader = PdfReader(dosya_adi)
                for sayfa in icerik_reader.pages:
                    writer.add_page(sayfa)

                with open(dosya_adi, "wb") as f:
                    writer.write(f)
            except Exception as e_merge:
                print(f"[FBST] Asartepe PDF ekleme hatası: {e_merge}")
    
    def pdf_potansiyel_rapor_uret(self, dosya_adi=None):
        """Potansiyel & Yetenek modülü için tek kişilik odaklı PDF raporu üretir."""
        if dosya_adi is None:
            dosya_adi = f"{self._session_id}_Potansiyel_Yetenek.pdf"
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak, Spacer, Image
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.graphics.shapes import Drawing, Line
        from reportlab.lib.colors import HexColor

        def pdf_temizle(metin):
            if not isinstance(metin, str): return str(metin)
            metin = metin.replace("✨", "[*]").replace("🌟", "[*]").replace("🚀", "[>]").replace("📍", "[-]")
            metin = metin.replace("👉", "->").replace("•", "-")
            metin = re.sub(r'[^\w\s.,;:!?()\[\]{}<>\-+=/\\\'"&%$#@*|~^\n]', '', metin)
            metin = metin.replace('\r', '').replace('\x0b', '').replace('\x0c', '')
            return metin.strip()

        doc = SimpleDocTemplate(dosya_adi, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TurkishNormal', fontName='DejaVuSans', fontSize=10, leading=18, spaceAfter=12, textColor=HexColor(METIN_SIYAH)))
        styles.add(ParagraphStyle(name='TurkishHeading', fontName='DejaVuSans-Bold', fontSize=13, leading=18, spaceBefore=22, spaceAfter=10, textColor=HexColor(DERIN_MAVI)))
        styles.add(ParagraphStyle(name='TurkishTitle', fontName='DejaVuSans-Bold', fontSize=18, leading=22, spaceBefore=20, spaceAfter=15, alignment=1, textColor=HexColor(KADIM_LACIVERT)))
        styles.add(ParagraphStyle(name='CoverTitle', fontName='DejaVuSans', fontSize=28, leading=34, alignment=1, textColor=HexColor(KADIM_LACIVERT)))
        styles.add(ParagraphStyle(name='CoverSub', fontName='DejaVuSans', fontSize=13, leading=18, alignment=1, textColor=HexColor("#4A5568")))
        styles.add(ParagraphStyle(name='CoverFooter', fontName='DejaVuSans', fontSize=9, leading=14, alignment=1, textColor=HexColor("#718096")))
        styles.add(ParagraphStyle(name='CardText', fontName='DejaVuSans', fontSize=9.5, leading=15, textColor=HexColor(METIN_SIYAH)))

        story = []

        def luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5):
            d = Drawing(500, 15)
            d.add(Line(0, 7, 500, 7, strokeColor=HexColor(renk), strokeWidth=kalinlik))
            return d

        def kapak_ciz(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(HexColor("#FFFFFF"))
            canvas.rect(0, 0, 595.27, 841.89, fill=True, stroke=False)
            canvas.restoreState()

        def sayfa_ciz(canvas, doc):
            canvas.saveState()
            w, h = A4
            canvas.setFont('DejaVuSans', 8)
            canvas.setFillColor(HexColor('#718096'))
            canvas.drawString(40, h - 25, "ASARTEPE SİNASTRİ AKADEMİSİ")
            canvas.drawRightString(w - 40, h - 25, f"{self.p1_isim}")
            canvas.setStrokeColor(HexColor('#C9A96E'))
            canvas.setLineWidth(0.5)
            canvas.line(40, h - 30, w - 40, h - 30)
            canvas.setStrokeColor(HexColor('#C9A96E'))
            canvas.setLineWidth(1.0)
            canvas.line(40, 35, w - 40, 35)
            canvas.setFont('DejaVuSans', 9)
            canvas.setFillColor(HexColor('#C9A96E'))
            canvas.drawCentredString(w / 2, 20, f"- {doc.page} -")
            canvas.setFont('DejaVuSans', 7)
            canvas.setFillColor(HexColor('#4A5568'))
            canvas.drawRightString(w - 40, 20, "Fatih Asartepe — © 2026 Tüm hakları saklıdır")
            canvas.restoreState()

        def baslik_karti_ekle(baslik_metni, alt_baslik=None, emoji=""):
            tam_baslik = f"{emoji} {baslik_metni}" if emoji else baslik_metni
            kart_html = f"""
            <table width="100%" cellpadding="8">
            <tr>
                <td bgcolor="#1A1A2E" width="6">
                    <font color="#C9A96E" size="16">|</font>
                </td>
                <td bgcolor="#F0F4F8" style="padding-left:12px;">
                    <font color="#1A1A2E" size="14"><b>{tam_baslik}</b></font>
                    {"<br/><font color='#4A5568' size='9'>" + alt_baslik + "</font>" if alt_baslik else ""}
                </td>
            </tr>
            </table>
            """
            story.append(Paragraph(kart_html, styles['TurkishNormal']))

        # ═══ KAPAK SAYFASI ═══
        asartepe_kapak_yolu = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Asartepe_Kapak.pdf")
        _asartepe_kapak_var = os.path.exists(asartepe_kapak_yolu)
        if not _asartepe_kapak_var:
            if os.path.exists("kapak1.png"):
                story.append(Image("kapak1.png", width=515, height=730))
            else:
                story.append(Spacer(1, 100))
                story.append(Paragraph("FATİH ASARTEPE SİNASTRİ TEKNİĞİ", styles['CoverTitle']))
                story.append(Spacer(1, 10))
                story.append(Paragraph("FAST", styles['CoverTitle']))
                story.append(Spacer(1, 20))
                story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=3.0))
                story.append(Spacer(1, 20))
                story.append(Paragraph("POTANSİYEL VE YETENEK RAPORU", styles['CoverSub']))
                story.append(Spacer(1, 30))
                story.append(Paragraph(f"<b>{self.p1_isim}</b>", styles['CoverSub']))
            story.append(PageBreak())

        # ═══ BİLGİ SAYFASI ═══
        baslik_karti_ekle("KİŞİ BİLGİLERİ", alt_baslik="Doğum haritası ve potansiyel analiz özeti", emoji="📋")
        story.append(Spacer(1, 8))

        bilgi_data = [
            ["KİŞİ BİLGİLERİ", ""],
            ["İsim:", self.p1_isim],
            ["Doğum Tarihi:", self.p1.strftime("%d.%m.%Y")],
            ["Doğum Saati:", f"{self.event_time_str} (UTC{self.utc_offset:g})" if self.utc_offset else self.event_time_str],
            ["Doğum Yeri:", f"{self.city}, {self.country}"],
            ["Enlem:", f"{self.enlem:.4f}"],
            ["Boylam:", f"{self.boylam:.4f}"],
        ]
        bilgi_tablo = Table(bilgi_data, colWidths=['30%', '70%'])
        bilgi_tablo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), '#1A1A2E'),
            ('TEXTCOLOR', (0,0), (-1,0), '#C9A96E'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
            ('SPAN', (0,0), (-1,0)),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,1), (-1,-1), 'DejaVuSans'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
            ('BACKGROUND', (0,1), (-1,-1), '#0D1117'),
            ('TEXTCOLOR', (0,1), (-1,-1), '#E0E0E0'),
            ('BOX', (0,0), (-1,-1), 2.5, '#C9A96E'),
            ('INNERGRID', (0,0), (-1,-1), 0.5, '#333333'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(bilgi_tablo)
        story.append(Spacer(1, 15))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
        story.append(Spacer(1, 15))

        # ═══ NATAL HARİTA ═══
        baslik_karti_ekle("NATAL HARİTA", alt_baslik="Doğum anındaki gökyüzü konumları", emoji="🌟")
        story.append(Spacer(1, 8))

        harita_dosya = f"{self._session_id}_Situa_A.png"
        if os.path.exists(harita_dosya):
            story.append(Image(harita_dosya, width=400, height=400))
        else:
            story.append(Paragraph("Natal harita görseli oluşturulamadı.", styles['TurkishNormal']))
        story.append(Spacer(1, 10))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
        story.append(Spacer(1, 15))

        # ═══ GEZEGEN POZİSYONLARI ═══
        baslik_karti_ekle("GEZEGEN POZİSYONLARI", alt_baslik="Doğum anındaki gezegen, asteroid ve kadersel noktalar", emoji="🪐")
        story.append(Spacer(1, 8))

        try:
            gp = self.gezegen_konum_analizi()
            if gp:
                gp_data = [["GEZEGEN", "DERECE", "BURÇ", "EV"]]
                for g_isim, g_bilgi in gp.items():
                    derece_str = f"{g_bilgi['derece']}°{g_bilgi['dakika']}'" if 'dakika' in g_bilgi else f"{g_bilgi.get('ham_derece', 0):.2f}°"
                    gp_data.append([g_isim, derece_str, g_bilgi.get('burc', '—'), f"{g_bilgi.get('ev', '—')}. Ev"])
                gp_tablo = Table(gp_data, colWidths=['25%', '25%', '25%', '25%'])
                gp_tablo.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), '#1A1A2E'),
                    ('TEXTCOLOR', (0,0), (-1,0), '#C9A96E'),
                    ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 10),
                    ('FONTNAME', (0,1), (-1,-1), 'DejaVuSans'),
                    ('FONTSIZE', (0,1), (-1,-1), 9),
                    ('BACKGROUND', (0,1), (-1,-1), '#F8F5F1'),
                    ('TEXTCOLOR', (0,1), (-1,-1), '#1A1A2E'),
                    ('BOX', (0,0), (-1,-1), 1.5, '#C9A96E'),
                    ('INNERGRID', (0,0), (-1,-1), 0.5, '#E8E0D8'),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ]))
                story.append(gp_tablo)
            else:
                story.append(Paragraph("Gezegen pozisyonları hesaplanamadı.", styles['TurkishNormal']))
        except Exception as e:
            story.append(Paragraph(f"<font color='red'>Gezegen pozisyonları hatası: {str(e)}</font>", styles['TurkishNormal']))

        story.append(Spacer(1, 15))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
        story.append(Spacer(1, 15))

        # ═══ POTANSİYEL VE YETENEK ALANLARI ═══
        baslik_karti_ekle("POTANSİYEL VE YETENEK ALANLARI", alt_baslik="Doğal yetenek ve potansiyel alanları açısal analizle belirlenmiştir", emoji="💡")
        story.append(Spacer(1, 8))

        potansiyel_sonuclari = self.potansiyel_hesapla()
        if potansiyel_sonuclari:
            gorulen_alanlar = set()
            for satir in potansiyel_sonuclari:
                if satir['alan'] not in gorulen_alanlar:
                    gorulen_alanlar.add(satir['alan'])
                    potansiyel_metni = (
                        f"<font color='#1A1A2E'><b>{satir['alan']} ({satir['aci']} — {satir['aci_turu']} Açısı)</b></font><br/>"
                        f"<font color='#4A4A4A'>{pdf_temizle(satir['metin'])}</font>"
                    )
                    potansiyel_kutu = Table([[Paragraph(potansiyel_metni, styles['TurkishNormal'])]], colWidths=['100%'])
                    potansiyel_kutu.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                        ('BOX', (0,0), (-1,-1), 0.8, ALTIN_AMBER),
                        ('PADDING', (0,0), (-1,-1), 10),
                    ]))
                    story.append(potansiyel_kutu)
                    story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("Belirgin bir potansiyel alanı tespit edilemedi.", styles['TurkishNormal']))

        story.append(Spacer(1, 15))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
        story.append(Spacer(1, 15))

        # ═══ MESLEK YÖNLENDİRME ÖNERİLERİ ═══
        baslik_karti_ekle("MESLEK YÖNLENDİRME ÖNERİLERİ", alt_baslik="Potansiyel ve yetenek alanlarının senteziyle belirlenen meslek dalları", emoji="🎯")
        story.append(Spacer(1, 8))

        try:
            konumlar = self.gezegen_konum_analizi()
            meslek_onerileri = self.meslek_onerileri()
            if meslek_onerileri:
                sirali = sorted(meslek_onerileri, key=lambda x: x['puan'], reverse=True)
                ranking_html = "<font color='#1A1A2E'><b>POTANSİYEL ALANLARI SIRALAMASI:</b></font><br/>"
                for j, r in enumerate(sirali[:6]):
                    medal = ""
                    if j == 0: medal = " [1.]"
                    elif j == 1: medal = " [2.]"
                    ranking_html += f"<font color='#4A4A4A'>{j+1}. <b>{r['alan']}</b> — {r['puan']:.1f} puan (%{r['yuzde']}){medal}</font><br/>"
                ranking_kutu = Table([[Paragraph(ranking_html, styles['TurkishNormal'])]], colWidths=['100%'])
                ranking_kutu.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), HexColor("#F7F3E9")),
                    ('BOX', (0,0), (-1,-1), 0.8, ALTIN_AMBER),
                    ('PADDING', (0,0), (-1,-1), 10),
                ]))
                story.append(ranking_kutu)
                story.append(Spacer(1, 10))

                for i, oneri in enumerate(meslek_onerileri, 1):
                    aci_sayisi = oneri.get('aci_sayisi', 0)
                    bonus_not = f" ({aci_sayisi} açı, {oneri['puan']:.1f} puan)"
                    oneri_baslik = f"{i}. {oneri['alan']} — %{oneri['yuzde']}{bonus_not}"
                    meslek_satirlari = ""
                    for m in oneri["meslekler"]:
                        meslek_satirlari += f"<br/>• <b>{m['meslek']}</b> — {m['aciklama']}"
                    kisisel_yorum = ""
                    if konumlar:
                        gezegen_listesi = oneri.get('gezegenler', [])
                        kisisel_yorum = self.meslek_kisisel_yorum(oneri['alan'], gezegen_listesi, konumlar)
                    if kisisel_yorum:
                        meslek_satirlari += f"<br/><br/><font color='#C9A96E'><i>{kisisel_yorum}</i></font>"
                    oneri_metni = (
                        f"<font color='#1A1A2E'><b>{oneri_baslik}</b></font><br/>"
                        f"<font color='#4A4A4A'>{meslek_satirlari}</font>"
                    )
                    oneri_kutu = Table([[Paragraph(oneri_metni, styles['TurkishNormal'])]], colWidths=['100%'])
                    oneri_kutu.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), KART_ARKA_PLAN),
                        ('BOX', (0,0), (-1,-1), 0.8, ALTIN_AMBER),
                        ('PADDING', (0,0), (-1,-1), 10),
                    ]))
                    story.append(oneri_kutu)
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph("Meslek yönlendirme için yeterli potansiyel alanı tespit edilemedi.", styles['TurkishNormal']))
        except Exception as e:
            story.append(Paragraph(f"<font color='red'><b>Meslek Yönlendirme Hatası:</b> {str(e)}</font>", styles['TurkishNormal']))

        story.append(Spacer(1, 15))
        story.append(luks_cizgi_ekle(renk="#C9A96E", kalinlik=1.5))
        story.append(Spacer(1, 15))

        # ═══ NİHAİ ÖZET ═══
        baslik_karti_ekle("ÖZET VE DEĞERLENDİRME", alt_baslik="Potansiyel ve yetenek analizinin genel değerlendirmesi", emoji="📜")
        story.append(Spacer(1, 8))

        potansiyel_sayisi = len(set(s['alan'] for s in (potansiyel_sonuclari or [])))
        meslek_sayisi = len(meslek_onerileri) if meslek_onerileri else 0

        ozet_html = (
            f"<font color='#1A1A2E'><b>{self.p1_isim}</b> için potansiyel ve yetenek analizi "
            f"{self.p1.strftime('%d.%m.%Y')} tarihinde {self.city}, {self.country} koordinatlarında "
            f"hesaplanmıştır.</font><br/><br/>"
            f"<font color='#4A4A4A'>"
            f"<b>Tespit edilen potansiyel alanı sayısı:</b> {potansiyel_sayisi}<br/>"
            f"<b>Önerilen meslek dalı sayısı:</b> {meslek_sayisi}<br/><br/>"
            f"Bu rapor, doğum haritasındaki gezegen açılarının potansiyel alanlarıyla eşleştirilmesi "
            f"sonucu ortaya çıkmıştır. Detaylı açıklama ve yorumlar için bir astroloji uzmanına danışmanız önerilir."
            f"</font>"
        )
        ozet_kutu = Table([[Paragraph(ozet_html, styles['TurkishNormal'])]], colWidths=['100%'])
        ozet_kutu.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), HexColor("#FFFAF5")),
            ('BOX', (0,0), (-1,-1), 1.0, ALTIN_AMBER),
            ('PADDING', (0,0), (-1,-1), 15),
        ]))
        story.append(ozet_kutu)

        # FİNAL
        ilk_sayfa_ciz = sayfa_ciz if _asartepe_kapak_var else kapak_ciz
        doc.build(story, onFirstPage=ilk_sayfa_ciz, onLaterPages=sayfa_ciz)

        # Asartepe_Kapak.pdf başa ekle (varsa kapak1.png/text atlanmıştır)
        if _asartepe_kapak_var:
            try:
                from pypdf import PdfReader, PdfWriter
                writer = PdfWriter()
                asartepe_reader = PdfReader(asartepe_kapak_yolu)
                writer.add_page(asartepe_reader.pages[0])
                icerik_reader = PdfReader(dosya_adi)
                for sayfa in icerik_reader.pages:
                    writer.add_page(sayfa)
                with open(dosya_adi, "wb") as f:
                    writer.write(f)
            except Exception as e_merge:
                print(f"[FAST] Asartepe PDF ekleme hatası: {e_merge}")

        return dosya_adi
    
    def pdf_kadersel_muhur_ekle(self, story, styles):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle, Spacer
        
        # Muhur verileri (Akis)
        tork = round(self.calculate_tork_skoru(), 1)
        fraktal = round(self.calculate_fraktal_uyum(), 1)
        
        data = [
            ["FATİH BAĞIL SİNASTRİ TEKNİĞİ MÜHÜR BELGESİ", ""],
            ["İlişkinin Üretim Gücü:", f"{tork}/10.0"],
            ["Ruhsal Uyum Mührü (Altın Oran):", f"{fraktal}%"],
            ["Kadersel Koruma:", "AKTİF KORUMA"]
        ]
        
        t = Table(data, colWidths=[200, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,1), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ]))
        
        story.append(t)
        story.append(Spacer(1, 20))
    
    def calculate_tork_skoru(self):
        """
        Iliskinin toplam uretim gucunu hesaplar.
        Mars ve Satürn'ün açısal gücünden, sinastri kavuşum/kare/oranlarından türetilir.
        0-10 arası skala döndürür.
        """
        import math
        j1 = swe.julday(self.p1.year, self.p1.month, self.p1.day, 12.0)
        j2 = swe.julday(self.p2.year, self.p2.month, self.p2.day, 12.0)

        skor = 5.0

        kritik_gezegenler = {
            "Mars": swe.MARS, "Satürn": swe.SATURN, "Güneş": swe.SUN,
            "Ay": swe.MOON, "Venüs": swe.VENUS, "Jüpiter": swe.JUPITER
        }

        for isim, gid in kritik_gezegenler.items():
            try:
                d1 = swe.calc_ut(j1, gid)[0][0]
                d2 = swe.calc_ut(j2, gid)[0][0]
                aci = abs(d1 - d2)
                if aci > 180:
                    aci = 360 - aci

                if abs(aci - 137.5) < 5:
                    skor += 1.5
                elif aci < 8:
                    skor += 1.2
                elif abs(aci - 60) < 5:
                    skor += 0.8
                elif abs(aci - 120) < 5:
                    skor += 0.9
                elif abs(aci - 90) < 5:
                    skor -= 0.5
                elif abs(aci - 180) < 8:
                    skor -= 0.3
            except Exception:
                pass

        ks = self.calculate_ks()
        if abs(ks - round(ks)) < 0.15:
            skor += 0.5

        return max(0.0, min(10.0, round(skor, 1)))

    def calculate_fraktal_uyum(self):
        """
        İlişkinin altın oran (137.5 derece) uyum skorunu hesaplar.
        Tüm gezegen çiftleri arasındaki açıların 137.5°'ye yakınlığını percentaj olarak ölçer.
        0-100 arası skor döndürür.
        """
        j1 = swe.julday(self.p1.year, self.p1.month, self.p1.day, 12.0)
        j2 = swe.julday(self.p2.year, self.p2.month, self.p2.day, 12.0)

        ALTIN_ACI = 137.5
        toplam = 0
        eslesen = 0

        for isim, gid in GEZEGENLER.items():
            if gid == 999:
                continue
            try:
                d1 = swe.calc_ut(j1, gid)[0][0]
                d2 = swe.calc_ut(j2, gid)[0][0]
                aci = abs(d1 - d2)
                if aci > 180:
                    aci = 360 - aci

                toplam += 1
                sapma = abs(aci - ALTIN_ACI)
                if sapma < 5:
                    eslesen += 1.0
                elif sapma < 10:
                    eslesen += 0.6
                elif sapma < 15:
                    eslesen += 0.3
            except Exception:
                pass

        if toplam == 0:
            return 50.0

        skor = (eslesen / toplam) * 100
        return round(max(0.0, min(100.0, skor)), 1)

    def calculate_solar_return_tema(self, j_referans, hedef_yil):
        import swisseph as swe
        
        try:
            natal_gunes = swe.calc_ut(j_referans, swe.SUN)[0][0]
        except Exception:
            return f"<b>{hedef_yil} YILI:</b> Kadersel güneş verisine ulaşılamadı."

        ref_tarih = swe.revjul(j_referans, swe.GREG_CAL)
        ref_ay = ref_tarih[1]
        ref_gun = ref_tarih[2]
        
        tahmini_j_gun = swe.julday(hedef_yil, ref_ay, ref_gun, 12.0)
        
        j_return = tahmini_j_gun
        for iterasyon in range(15):
            res_trans = swe.calc_ut(j_return, swe.SUN)
            transit_gunes = res_trans[0][0]
            fark = natal_gunes - transit_gunes
            if fark > 180: fark -= 360
            if fark < -180: fark += 360
            if abs(fark) < 0.0001: break
            gunes_hizi = res_trans[0][3] if res_trans[0][3] != 0 else 0.9856
            j_return += fark / gunes_hizi 
            
        asc_burc = self.yukselen_bul(j_return)
        if asc_burc == "Hesaplanamadi": asc_burc = "Koç" 
        
        saturn_ev = self.ev_konumu_bul(j_return, swe.SATURN)
        gunes_ev = self.ev_konumu_bul(j_return, swe.SUN)
        if type(saturn_ev) != int: saturn_ev = 1
        if type(gunes_ev) != int: gunes_ev = 1

        # ---------------------------------------------------------
        # YENİ MODÜL 1: YÜKSELEN YÖNETİCİSİ NEREDE?
        # ---------------------------------------------------------
        yoneticiler = {
            "Koç": swe.MARS, "Boğa": swe.VENUS, "İkizler": swe.MERCURY, "Yengeç": swe.MOON,
            "Aslan": swe.SUN, "Başak": swe.MERCURY, "Terazi": swe.VENUS, "Akrep": swe.PLUTO,
            "Yay": swe.JUPITER, "Oğlak": swe.SATURN, "Kova": swe.URANUS, "Balık": swe.NEPTUNE
        }
        yonetici_gezegen_id = yoneticiler.get(asc_burc, swe.SUN)
        yonetici_ev = self.ev_konumu_bul(j_return, yonetici_gezegen_id)
        if type(yonetici_ev) != int: yonetici_ev = 1

        # ---------------------------------------------------------
        # YENİ MODÜL 2: GÜNEŞ'İN KADERSEL AÇILARI (MAJOR ASPECTS)
        # ---------------------------------------------------------
        gunes_acilar = []
        gezegenler_kontrol = {
            "Ay": swe.MOON, "Merkür": swe.MERCURY, "Venüs": swe.VENUS, 
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN, 
            "Uranüs": swe.URANUS, "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO,
            "KAD": swe.MEAN_NODE # Düğümleri ekledik!
        }
        
        for gez_isim, gez_id in gezegenler_kontrol.items():
            try:
                gez_derece = swe.calc_ut(j_return, gez_id)[0][0]
                aci_farki = abs(transit_gunes - gez_derece)
                if aci_farki > 180: aci_farki = 360 - aci_farki
                
                gez_evi = self.ev_konumu_bul(j_return, gez_id)
                
                # Orblar (Sapma payları)
                if abs(aci_farki - 0) <= 8:
                    gunes_acilar.append({"gezegen": gez_isim, "aci": "Kavuşum", "ev": gez_evi})
                elif abs(aci_farki - 90) <= 8:
                    gunes_acilar.append({"gezegen": gez_isim, "aci": "Kare", "ev": gez_evi})
                elif abs(aci_farki - 120) <= 8:
                    gunes_acilar.append({"gezegen": gez_isim, "aci": "Üçgen", "ev": gez_evi})
                elif abs(aci_farki - 180) <= 8:
                    gunes_acilar.append({"gezegen": gez_isim, "aci": "Karşıt", "ev": gez_evi})
            except Exception:
                pass

        sr_data = {
            "yil": hedef_yil,
            "yilin_vitrini": asc_burc,
            "yonetici_ev": yonetici_ev,
            "yilin_sinavi_ev": saturn_ev,
            "yilin_odagi_ev": gunes_ev,
            "acilar": gunes_acilar
        }
        
        return self.solar_return_metni_yaz(sr_data)

    def solar_return_metni_yaz(self, sr_data):
        yil = sr_data.get("yil", "2024")
        asc = sr_data.get("yilin_vitrini", "Koç")
        yonetici_ev = sr_data.get("yonetici_ev", 1)
        saturn_ev = sr_data.get("yilin_sinavi_ev", 1)
        gunes_ev = sr_data.get("yilin_odagi_ev", 1)
        acilar = sr_data.get("acilar", [])

        if self.mod == "ebeveyn_cocuk":
            vitrin_sozlugu = {
                "Koç": "<b>Keşif ve Bağımsızlık Yılı:</b> Çocuğun kendi kimliğini keşfetmeye başladığı, bağımsız kararlar alma arzusunun güçlendiği bir dönem. Ebeveyn olarak sabır ve destek en kritik araçlarınız. Çocuğun cesaretini kırmadan sınırlar çizmek, bu yılın en önemli pedagojik dersidir.",
                "Boğa": "<b>Güven ve İstikrar Yılı:</b> Çocuğun fiziksel ve duygusal güvenliğinin ön planda olduğu bir dönem. Rutinler, düzen ve tekrar eden alışkanlıklar çocuğun iç huzurunu besler. Sabırlı ve kararlı bir ebeveynlik yaklaşımı, çocuğun kendine olan güveninin temelini atar.",
                "İkizler": "<b>İletişim ve Merak Yılı:</b> Çocuğun soru sorma, keşfetme ve iletişim kurma ihtiyacı tavan yapar. Sabırlı ve açıklayıcı bir dil kullanmak, çocuğun zihinsel gelişimini destekler. Birlikte kitap okumak, sohbet etmek bu yılın en değerli pedagojik faaliyetidir.",
                "Yengeç": "<b>Duygusal Bağlanma Yılı:</b> Ebeveyn ve çocuk arasındaki duygusal bağın derinleştiği, aidiyet ve güven duygusunun güçlendiği bir dönem. Çocuğun duygusal ihtiyaçlarına hassasiyetle yaklaşmak, uzun vadeli güven inşasının temelini atar.",
                "Aslan": "<b>Yaratıcılık ve Takdir Yılı:</b> Çocuğun yaratıcı potansiyelinin parladığı, takdir ve övgü ihtiyacının arttığı bir dönem. Çocuğun çabalarını fark etmek ve takdir etmek, özgüven gelişiminin en güçlü motorudur.",
                "Başak": "<b>Düzen ve Alışkanlık Yılı:</b> Çocuğun düzenli yaşam alışkanlıkları edinmesi, sorumluluk duygusunun gelişmesi için ideal bir dönem. Birlikte küçük görevler paylaşmak, çocuğun sorumluluk bilincini pedagojik bir şekilde inşa eder.",
                "Terazi": "<b>Denge ve Uyum Yılı:</b> Ebeveyn-çocuk ilişkisinde dengeyi bulmanın, karşılıklı saygıyı öğrenmenin ve uyumlu bir iletişim kurmanın ön planda olduğu bir dönem. Tartışmalarda adalet ve eşitlik duygusunu korumak kritiktir.",
                "Akrep": "<b>Derinleşme ve Yüzleşme Yılı:</b> Çocuğun iç dünyasındaki derin duyguların, korkuların ve ihtiyaçların yüzeye çıktığı bir dönem. Ebeveynin sabırlı ve anlayışlı yaklaşımı, bu sürecin şifaya dönüşmesinin anahtarıdır.",
                "Yay": "<b>Genişleme ve Keşif Yılı:</b> Çocuğun ufuklarını genişletme, yeni deneyimler yaşama ve hayata dair bir felsefe geliştirme ihtiyacının arttığı bir dönem. Birlikte seyahat etmek, yeni kültürleri tanımak ve felsefi sohbetler yapmak ruhsal gelişimi besler.",
                "Oğlak": "<b>Yapı ve Sorumluluk Yılı:</b> Çocuğun kendi sınırlarını, kurallarını ve sorumluluklarını öğrenmesi için ideal bir dönem. Net ve tutarlı sınırlar çizmek, çocuğun disiplin ihtiyacını pedagojik bir şekilde karşılar.",
                "Kova": "<b>Özgürlük ve Bireysellik Yılı:</b> Çocuğun bireysel alanına saygı duymanın, onun özgürlüğüne değer vermenin ve bağımsız bir birey olarak gelişmesine destek olmanın ön planda olduğu bir dönem.",
                "Balık": "<b>Sezgi ve Şefkat Yılı:</b> Çocuğun sezgilerinin güçlendiği, empati ihtiyacının arttığı ve duygusal hassasiyetinin yoğunlaştığı bir dönem. Mantıktan ziyade kalbi dinlemek, çocuğun duygusal gelişimini destekler."
            }
        else:
            vitrin_sozlugu = {
                "Koç": "<b>Savaş ve Fetih Yılı:</b> Yeni kararlar almak, cesurca öne atılmak ve ilişkinin temposunu hızlandırmak zorunda kalacaksınız. Bu yıl ertelediğiniz o büyük kararı (taşınma, evlilik veya ortak iş) aniden alabilirsiniz. Eylemsizlik ilişkinizi yoracaktır; birlikte spora başlamak, yeni bir hobi edinmek veya ortak bir hedefe kilitlenmek ilişkinin motor gücünü artırır.",
                "Boğa": "<b>Topraklanma ve İnşa Yılı:</b> Tutku yerini huzur arayışına, finansal güvenliğe ve ilişkinin köklerini sarsılmaz bir şekilde sağlamlaştırmaya bırakıyor. Bu yıl ev almak, birikim yapmak veya ortak bir banka hesabı açmak gibi somut finansal adımlar atacaksınız. Birlikte lüks restoranlara gitmek, ev dekorasyonunu yenilemek ve fiziksel teması (sarılma, masaj) artırmak ruhunuzu besleyecek.",
                "İkizler": "<b>Zihinsel Senkronizasyon Yılı:</b> Bol bol iletişim kuracağınız, planların sürekli değiştiği ve aranızdaki fikirsel uyumun tutkuya dönüştüğü hızlı bir dönem. Kısa hafta sonu kaçamakları, birlikte yeni bir dil veya kurs öğrenmek bu yılın öne çıkan temaları. Saatlerce süren derin sohbetler, ilişkinizdeki düğümleri çözecek en büyük anahtarınız.",
                "Yengeç": "<b>Aidiyet ve Sığınak Yılı:</b> Dış dünyanın gürültüsünden kaçıp, sadece birbirinizin duygusal kalkanına sığınacağınız, yuvayı şifalandıracağınız içsel bir yıl. Ailelerle tanışma, nişanlanma veya aynı eve çıkma gibi aidiyet duygusunu perçinleyen somut adımlar bu yılın gündemi. Evde birlikte yemek yapmak, eski albümlere bakmak ve sadece ikinizin olduğu özel bir kozaya çekilmek size çok iyi gelecek.",
                "Aslan": "<b>Sahne ve Yaratım Yılı:</b> İlişkinizin dışarıdan alkış alacağı, gururun ve cömertliğin ön planda olduğu, aşkın adeta bir şölene dönüştüğü parlak bir dönem. Bu yıl düğün, kutlama veya ilişkinizi herkese ilan edeceğiniz görkemli anlar yaşayabilirsiniz. Bebek sahibi olma fikri veya birlikte ortaya koyacağınız yaratıcı bir proje (sanat, iş) bu yıl ilişkinizin parlayan yıldızı olacak.",
                "Başak": "<b>Hizmet ve Onarım Yılı:</b> Büyük romantik laflardan ziyade, birbirinizin hayatını kolaylaştırma, eksikleri tamir etme ve ilişkiyi kusursuz bir sisteme oturtma zamanı. Sağlık kontrollerinden geçmek, ortak bir diyete veya sağlıklı yaşam rutinine başlamak bu yılın somut olayları. 'Seni seviyorum' demek yerine partnerinizin bozulan arabasını tamir ettirmek veya yorgun olduğunda ona sıcak bir çorba yapmak en büyük aşk göstergeniz olacak.",
                "Terazi": "<b>Diplomasi ve Ayna Yılı:</b> Sen-Ben savaşını tamamen bırakıp, mutlak uyuma odaklanacağınız, ilişkinin vitrinini dış dünyaya karşı parlatacağınız yıl. Ciddi kontratlar (evlilik cüzdanı, ortaklık sözleşmesi) imzalamak için en ideal dönem. Tartışmalarda sesinizi yükseltmek yerine adil bir arabulucu gibi davranmalı, ilişkinizin estetik ve romantik yönünü (hediyeleşme, sürprizler) canlı tutmalısınız.",
                "Akrep": "<b>Simya ve Dönüşüm Yılı:</b> Sırların açığa çıktığı, krizlerin sizi ya tamamen yıkıp ya da küllerinizden eskisinden çok daha sarsılmaz bir bağla doğuracağı yoğun kadersel viraj. Bu yıl halı altına süpürülen hiçbir sorun gizli kalamaz. Ortak krediler, miras veya borç yapılandırmaları gündeme gelebilir. Yüzeysel konuşmalar yerine birbirinizin ruhundaki en derin korkuları şifalandırdığınız muazzam bir psikolojik terapi yılı yaşayacaksınız.",
                "Yay": "<b>Ufukları Aşma Yılı:</b> İlişkinin sınırlarını genişletme, birlikte yeni inançlar geliştirme, dünyayı gezme veya ortak bir vizyonda bilgeleşme dönemi. Uzun süredir hayalini kurduğunuz o uzak yurt dışı tatili bu yıl gerçekleşebilir. Hukuki süreçlerin tatlıya bağlanması veya birlikte akademik bir başarıya imza atmak mümkündür. İlişkinize yeni bir felsefe ve özgürlük katacaksınız.",
                "Oğlak": "<b>İmparatorluk İnşası Yılı:</b> Aşkın en ciddi ve statü odaklı hali. Sorumlulukların arttığı, ilişkinin dış dünyada kalıcı bir kaleye dönüştürüleceği o ağırbaşlı yıl. İlişkinizin resmiyet kazanması, toplum önünde 'saygın bir çift' olarak kabul görmeniz veya ortak bir şirket kurmanız an meselesi. Sorumluluklardan kaçmak yerine omuz omuza verip çalışırsanız, bu yıl ilişkinizin betonlarını atacaksınız.",
                "Kova": "<b>Özgürleşme ve Devrim Yılı:</b> Eski rutinlerin yıkıldığı, birbirinizin bireysel alanına saygı duyarak 'biz' olduğunuz ve ilişkinin sıra dışı bir boyuta evrildiği dönem. Beklenmedik sürprizler, aniden alınan kararlar veya farklı bir şehre taşınma fikri gündeme gelebilir. Bu yıl geleneksel kalıplara (klasik karı-koca rolleri) sığmayacaksınız; birbirinizin en iyi arkadaşı ve vizyoner yoldaşı olmayı başarmanız gerekiyor.",
                "Balık": "<b>İlahi Teslimiyet Yılı:</b> Mantığın sustuğu, rüyaların konuştuğu yıl. Sınırların eridiği ve birbirinizin ruhunda kaybolup şifa bulacağınız o fedakarlık dönemi. Bu yıl dünyevi hırsları bir kenara bırakıp spiritüel konulara yönelebilir, birlikte meditasyon yapabilir veya doğa ile iç içe kamplara katılabilirsiniz. Birbirinizi yargılamadan, sadece koşulsuz sevgiyle kabul ettiğinizde aranızdaki tüm geçmiş karmik düğümler çözülecektir."
            }
        vitrin_yorum = vitrin_sozlugu.get(asc, f"<b>Kadersel Yenilenme Yılı:</b> İlişkiniz bu yıl yeni bir forma bürünüyor.")

        if self.mod == "ebeveyn_cocuk":
            yonetici_sozlugu = {
                1: "Bu yıl ebeveyn olarak kendi içinizden gelen içgüdüsel bir rehberlik enerjisine sahipsiniz. Dışarıdan tavsiye beklemek yerine, çocuğunuzla olan ilişkinizi kendi sezgilerinizle yönlendireceksiniz.",
                2: "Tüm motivasyon çocuğunuzun değerlerini, yeteneklerini ve kendine olan güvenini keşfetmeye ve beslemeye yönelik. Somut adımlar atmak bu yılın anahtarı.",
                3: "Çocuğunuzla iletişim trafiğiniz artıyor. Öğrenme, konuşma, paylaşma ve birlikte yeni şeyler keşfetme ihtiyacı ön planda.",
                4: "Dış dünyadan çekilip aile içi güvenli bir liman yaratmaya odaklanıyorsunuz. Çocuğunuzla baş başa vakit geçirmek bu yılın en değerli yatırımı.",
                5: "Çocuğunuzun yaratıcı potansiyelini keşfetme ve onu sahneye çıkarma yılı. Birlikte sanatsal faaliyetler, oyunlar ve yaratıcı projeler bu yılın kalbinde.",
                6: "Ebeveynlikte rutin, düzen ve hizmet ön planda. Çocuğunuzun günlük ihtiyaçlarını karşılamak, sağlık ve bakım konularına odaklanmak bu yılın odağı.",
                7: "Ebeveyn-çocuk ilişkinizde dengeyi ve uyumu aradığınız bir yıl. Karşılıklı saygı, adalet ve ortak karar alma süreçleri öne çıkıyor.",
                8: "Çocuğunuzla derin bir duygusal bağ kurma, iç dünyasını keşfetme ve dönüşüm sürecine tanık olma yılı. Krizler şifaya dönüşebilir.",
                9: "Çocuğunuzun vizyonunu genişletme, yeni ufuklar keşfetme ve hayata dair bir felsefe geliştirme ihtiyacı ön planda. Birlikte öğrenme dönemi.",
                10: "Ebeveynlikte ciddiyet ve yapı ön planda. Çocuğunuz için kalıcı temeller atma, kurallar ve sorumluluklar oluşturma yılı.",
                11: "Çocuğunuzun sosyal çevre ihtiyaçları, arkadaşlıkları ve geleceğe dair umutları bu yılın odak noktası. Birlikte gelecek planları yapmak kritik.",
                12: "Bu yıl içe çekilme, ruhsal derinleşme ve sezgisel bağın güçlendirilmesi ön planda. Çocuğunuzla sessiz ve derin bir bağ kurmak için ideal bir dönem."
            }
        else:
            yonetici_sozlugu = {
                1: "Bu yıl dışarıdan destek beklemek yerine, ilişkiyi kendi iç yapiylarinizle, tamamen kendi ellerinizle yönetiyorsunuz.",
                2: "İlişkinin tüm temel enerjisi ve yönü; ortak finans, değer yaratma ve maddiyatı katlama üzerine akıyor.",
                3: "Tüm motivasyon zihinsel projelere, imzalara, eğitime ve yoğun bir iletişim trafiğine kaymış durumda.",
                4: "Dış dünyadan çekilip aidiyete, yuvaya, emlak veya ailevi konulara kök salma ihtiyacı içindesiniz.",
                5: "Bu yılın kalbi yaratıcılık, sahne, flörtöz tutku ve belki de bir çocuk (veya yeni bir heyecan) gündemiyle atıyor.",
                6: "Romantizm yerini hizmete bırakıyor. Birlikte çok çalışacağınız, rutini ve iş hayatını dengeleyeceğiniz bir yıl.",
                7: "Kararlarınızı tamamen 'biz' olma bilinciyle aldığınız, kontratlara ve net ortaklıklara odaklı kadersel bir yıl.",
                8: "Psikolojik derinleşme, krizleri aşma ve ortak borç/miras/finansal dönüşüm odaklı yoğun bir simya yılı.",
                9: "İlişkinin yönü uzaklara, yeni felsefelere, yurt dışı planlarına veya inançsal/vizyoner büyümeye dönük.",
                10: "İlişkinin dış dünyada statü kazanmak, kariyer yapmak ve 'imparatorluk' olarak görünmek istediği zirve yılı.",
                11: "Sosyal çevrenizin, ortak arkadaşlarınızın ve geleceğe dair büyük umutlarınızın ilişkinin lokomotifi olduğu bir dönem.",
                12: "Gözlerden uzak kalmak istediğiniz, ruhsal inziva, iyileşme ve gizli korkuları birlikte şifalandırma yılı."
            }
        yonetici_yorum = yonetici_sozlugu.get(yonetici_ev, "Motivasyonunuz kadersel bir hedefe kilitlenmiş durumda.")

        if self.mod == "ebeveyn_cocuk":
            odak_sozlugu = {
                1: "<b>Çocuğun Kimlik Keşfi:</b><br/><i>• Somut Etki:</i> Çocuğun kendi benliğini ifade ettiği, bağımsız kararlar aldığı ve kendini güvende hissettiği bir yıl.<br/><i>• Soyut Etki:</i> Ebeveynin kendi kimliğini de yeniden keşfettiği, çocuğun yansımasında kendini bulduğu pedagojik bir ayna yılı.",
                2: "<b>Değer ve Özgüven İnşası:</b><br/><i>• Somut Etki:</i> Çocuğun yeteneklerinin farkına varması, değerlerini keşfetmesi ve kendine olan güveninin artması için somut adımlar.<br/><i>• Soyut Etki:</i> Ebeveynin çocuğuna olan inancının ve takdirinin, çocuğun iç dünyasını beslediği kutsal bir yıl.",
                3: "<b>Öğrenme ve İletişim Köprüsü:</b><br/><i>• Somut Etki:</i> Bol okuma, yazma, konuşma ve birlikte öğrenme faaliyetleri. Yeni bir beceri veya bilgi alanı keşfetmek için ideal.<br/><i>• Soyut Etki:</i> Ebeveyn ve çocuk arasında zihinsel bir senkronizasyonun oluştuğu, birbirlerini derinlemesine anladıkları bir dönem.",
                4: "<b>Güvenli Liman ve Kökler:</b><br/><i>• Somut Etki:</i> Ev düzeni, aile içi rutinler ve güvenli bir ortam yaratmak bu yılın somut olayları.<br/><i>• Soyut Etki:</i> Çocuğun ruhsal köklerinin derinleştiği, ebeveynin ona sunduğu güvenli limanın kalıcı bir hatıraya dönüştüğü süreç.",
                5: "<b>Yaratıcılık ve Neşe Kaynağı:</b><br/><i>• Somut Etki:</i> Sanatsal faaliyetler, oyunlar, yaratıcı projeler ve çocuğun yeteneklerini sergileme fırsatları.<br/><i>• Soyut Etki:</i> Ebeveyn ve çocuğun birlikte neşeyi, oyunu ve yaratıcılığı deneyimlediği kutsal bir birleşme anı.",
                6: "<b>Rutin, Sağlık ve Hizmet:</b><br/><i>• Somut Etki:</i> Sağlık kontrolleri, düzenli beslenme, temizlik ve günlük bakım rutinleri bu yılın somut olayları.<br/><i>• Soyut Etki:</i> Ebeveynin çocuğuna sunduğu hizmetin ve fedakarlığın, sevginin en somut ifadesi olduğu yıl.",
                7: "<b>Denge ve Uyum Dersi:</b><br/><i>• Somut Etki:</i> Karşılıklı karar alma, tartışmalarda uzlaşma ve ebeveyn-çocuk arasında adil bir denge kurma pratikleri.<br/><i>• Soyut Etki:</i> İlişkinin 'sen' ve 'ben' den 'biz' bilincine geçtiği, karşılıklı saygının derinleştiği kutsal bir dönem.",
                8: "<b>Derinleşme ve Dönüşüm:</b><br/><i>• Somut Etki:</i> Çocuğun iç dünyasındaki korkuların ve endişelerin yüzeye çıktığı, ebeveynin sabırlı yaklaşımlarıyla şifaya dönüştüğü bir dönem.<br/><i>• Soyut Etki:</i> Ebeveyn ve çocuk arasında daha önce hiç yaşanmamış bir derinlikte duygusal paylaşımın gerçekleştiği simya yılı.",
                9: "<b>Vizyon ve Ufuk Genişletme:</b><br/><i>• Somut Etki:</i> Birlikte seyahat etmek, yeni kültürler tanımak, kitap okumak veya felsefi sohbetler yapmak bu yılın somut faaliyetleri.<br/><i>• Soyut Etki:</i> Çocuğun hayata dair bir felsefe geliştirmesine rehberlik ettiği, ebeveynin kendi vizyonunu da yeniden şekillendirdiği genişleme dönemi.",
                10: "<b>Yapı ve Sorumluluk Eğitimi:</b><br/><i>• Somut Etki:</i> Kurallar, sınırlar, sorumluluklar ve disiplin uygulamaları bu yılın somut olayları.<br/><i>• Soyut Etki:</i> Ebeveynin otoritesini sevgiyle harmanladığı, çocuğun yapı ve düzen ihtiyacını pedagojik bir şekilde karşıladığı yıl.",
                11: "<b>Sosyal Çevre ve Gelecek Planları:</b><br/><i>• Somut Etki:</i> Çocuğun arkadaşlık ilişkileri, sosyal etkinlikler ve geleceğe dair planlar bu yılın odak noktası.<br/><i>• Soyut Etki:</i> Ebeveynin çocuğunun geleceğine dair umutlarını ve vizyonunu birlikte şekillendirdiği, ortak hayaller kurduğu dönem.",
                12: "<b>Ruhsal Derinleşme ve Şifa:</b><br/><i>• Somut Etki:</i> Sessizlik, meditasyon, doğa yürüyüşleri ve içe çekilme faaliyetleri bu yılın somut olayları.<br/><i>• Soyut Etki:</i> Ebeveyn ve çocuğun bilinçaltındaki korkuları ve endişeleri birlikte şifalandırdığı, ruhsal olarak derinleştiği kutsal bir dönem."
            }
        else:
            odak_sozlugu = {
                1: "<b>İlişkinin Yeniden Doğuşu:</b><br/><i>• Somut Etki:</i> Birlikte imaj değiştirmek, yeni bir hayata başlamak veya ilişkiyi tazeleyen fiziksel adımlar atmak.<br/><i>• Soyut Etki:</i> Kimliklerin eriyip, evrensel 'biz' bilincinin yeniden doğduğu yüksek enerjili bir başlangıç noktası.",
                2: "<b>Finans ve Özdeğer İnşası:</b><br/><i>• Somut Etki:</i> Ortak bütçeyi büyütmek, büyük harcamalar yapmak, mal mülk almak veya yatırımlara odaklanmak.<br/><i>• Soyut Etki:</i> Birbirinize verdiğiniz değerin ve ruhsal güvenliğinizin en güçlü üretim merkezi olduğu yıl.",
                3: "<b>Zihin ve İletişim Trafiği:</b><br/><i>• Somut Etki:</i> Kısa seyahatler, önemli imzalar, sözleşmeler ve yoğun fikir alışverişleri.<br/><i>• Soyut Etki:</i> Aşkın kalpte değil zihinde yaşandığı; fikirsel olarak tam bir senkronizasyon yakalama yılı.",
                4: "<b>Yuva ve Köklerin Şifası:</b><br/><i>• Somut Etki:</i> Aynı eve çıkmak, taşınmak, ev dekorasyonu yapmak veya ailevi/köklerden gelen meseleleri çözmek.<br/><i>• Soyut Etki:</i> Dış dünyaya kapıları kapatıp birbirinizde mutlak ruhsal aidiyeti ve güvenli limanı bulma süreci.",
                5: "<b>Sahne, Yaratıcılık ve Aşk:</b><br/><i>• Somut Etki:</i> Flörtöz tatiller, ortak hobiler, sahne projeleri veya bir bebek (ya da büyük bir proje) gündemi.<br/><i>• Soyut Etki:</i> İçinizdeki çocuğun uyanması, ilişkinin rutinden çıkıp saf neşe ve tutku ürettiği merkez.",
                6: "<b>Rutin, Hizmet ve Düzen:</b><br/><i>• Somut Etki:</i> Ortak bir diyete/spora başlamak, evcil hayvan sahiplenmek veya iş tempolarının ilişkiyi yönlendirmesi.<br/><i>• Soyut Etki:</i> Sevginin kelimelerle değil, birbirinize sunduğunuz 'hizmet' ve fedakarlıklarla kanıtlandığı onarım yılı.",
                7: "<b>Mutlak Ortaklık ve Denge:</b><br/><i>• Somut Etki:</i> Nişan, evlilik, ciddi bir resmi kontrat veya ilişkinin boyut atladığı radikal bir imza dönemi.<br/><i>• Soyut Etki:</i> 'Sen' ve 'Ben' savaşının tamamen bitip, mutlak aynalama ve ruhsal terazi dengesinin kurulduğu kutsal yıl.",
                8: "<b>Kriz, Simya ve Derinlik:</b><br/><i>• Somut Etki:</i> Ortak krediler, miras/borç çözümleri veya çekim gücünün artmasıyla oluşan güçlü fiziksel tutku.<br/><i>• Soyut Etki:</i> İlişkinin karanlık sularına dalarak tabuları yıktığınız, krizden sarsılmaz bir bağla çıktığınız simya yılı.",
                9: "<b>Vizyon ve Uzak Ufuklar:</b><br/><i>• Somut Etki:</i> Yurtdışı seyahatleri, uluslararası kararlar, akademik/hukuki adımların tatlıya bağlanması.<br/><i>• Soyut Etki:</i> Aşkınızın felsefi bir boyuta sıçradığı, ortak inançlarınızın ilişkinin vizyonunu büyüttüğü genişleme dönemi.",
                10: "<b>Statü, Tepe Noktası ve İtibar:</b><br/><i>• Somut Etki:</i> İlişkinin resmiyet kazanıp toplum önüne çıkması, ortak bir kariyer başarısı veya prestijli bir sıçrama.<br/><i>• Soyut Etki:</i> Emeklerinizin meyvesini verdiği, ilişkinizin dışarıya karşı yıkılmaz bir 'imparatorluk' olarak göründüğü zirve yılı.",
                11: "<b>Gelecek, Umutlar ve Dostluk:</b><br/><i>• Somut Etki:</i> Ortak arkadaş gruplarında parlama, kalabalık etkinlikler ve geleceğe dair büyük bir hayalin tohumunu atma.<br/><i>• Soyut Etki:</i> Aşık olmanın ötesine geçip, birbirinizin 'en iyi vizyoner dostu' olduğunuz o özgür ve umut dolu yıl.",
                12: "<b>İnziva, Karmik Şifa ve Rüyalar:</b><br/><i>• Somut Etki:</i> Gözlerden uzak doğa tatilleri, spiritüel çalışmalar veya kalabalıklardan kopup tamamen baş başa kalma ihtiyacı.<br/><i>• Soyut Etki:</i> Geçmiş karmaların, bilinçaltı korkularının çözüldüğü; mantığın sustuğu ve koşulsuz bir ruhsal teslimiyetin başladığı süreç."
            }
        odak_yorum = odak_sozlugu.get(gunes_ev, "Odak noktanız bu yıl evrenin gizli çekmecelerinde şekilleniyor.")

        if self.mod == "ebeveyn_cocuk":
            sinav_sozlugu = {
                1: "<b>Kimlik ve Bağımsızlık Sınavı:</b> Çocuğunuzun bireysel benliğini tanırken kendi ebeveyn kimliğinizi de korumanız gereken hassas bir denge sınavı.",
                2: "<b>Değer ve Özgüven Sınavı:</b> Çocuğunuzun kendine olan güvenini inşa ederken kendi ebeveyn yetkinizi de sorgulayacağınız bir sınav dönemi.",
                3: "<b>İletişim ve Anlaşma Sınavı:</b> Çocuğunuzla doğru iletişim kurmak, onu dinlemek ve anlaşılmak bu yılın en zor ama en değerli sınavı.",
                4: "<b>Güvenli Ortam Sınavı:</b> Çocuğunuz için ne kadar güvenli ve koruyucu bir ortam yaratabildiğiniz test ediliyor.",
                5: "<b>Yaratıcılık ve Neşe Sınavı:</b> Hayatın ciddiyeti arasında çocuğunuzla birlikte neşeyi ve yaratıcılığı koruma mücadelesi.",
                6: "<b>Rutin ve Hizmet Sınavı:</b> Günlük bakım, sağlık ve düzen konularında ebeveyn olarak yorulma riski var. Kendinize de bakım vermeyi unutmayın.",
                7: "<b>Denge ve Uyum Sınavı:</b> Ebeveyn ve çocuk arasındaki dengeyi korumak, her iki tarafın da ihtiyaçlarını karşılamak bu yılın sınavı.",
                8: "<b>Duygusal Derinlik Sınavı:</b> Çocuğunuzun iç dünyasındaki derin duygularla yüzleşmek ve ona destek olmak sabır gerektiriyor.",
                9: "<b>Vizyon ve Ufuk Sınavı:</b> Çocuğunuzun geleceği için doğru rehberliği yapmak ve kendi vizyonunuzu genişletmek bu yılın sınavı.",
                10: "<b>Yapı ve Otorite Sınavı:</b> Kurallar koyma ve otorite ile sevgiyi dengeleme arasındaki hassas denge test ediliyor.",
                11: "<b>Sosyal Çevre Sınavı:</b> Çocuğunuzun sosyal çevre ihtiyaçlarını karşılarken kendi sosyal yaşamınızı da koruma sınavı.",
                12: "<b>Ruhsal Yüzleşme Sınavı:</b> Kendi ebeveynlik korkularınız ve yetersizlik duygularınızla yüzleşmeniz gereken derin bir sınav."
            }
        else:
            sinav_sozlugu = {
                1: "<b>Kimlik Sınavı:</b> Partnerinizin yükünü taşırken kendi bireyselliğinizi kaybetmemeyi öğrenmelisiniz. Omuzlardaki ağırlık artabilir.",
                2: "<b>Finans Sınavı:</b> Maddiyat veya özdeğer üzerinden gelecek krizler. Parayı nasıl yönettiğiniz ilişkinin güven testine dönüşecek.",
                3: "<b>İletişim Sınavı:</b> Yanlış anlaşılmalar ve zihinsel duvarlar. Kelimeleri keskin bir kılıç değil, yapıcı bir tuğla gibi kullanmayı öğrenmelisiniz.",
                4: "<b>Aidiyet Sınavı:</b> Ev, aile ve 'kökler' test edilecek. Birbirinize dışarıdan bağımsız, ne kadar güvenli bir sığınak olabiliyorsunuz?",
                5: "<b>Neşe Sınavı:</b> Eğlence yerini sorumluluğa bırakıyor. Hayatın ağırlığına rağmen içinizdeki çocuğu ve aşkı koruma mücadelesi.",
                6: "<b>Rutin Sınavı:</b> İş hayatının stresi veya günlük dertler aranıza girebilir. Görev dağılımı yapmazsanız ilişkinin yorulma riski var.",
                7: "<b>Ortaklık Sınavı:</b> Doğrudan evliliğin veya ilişkinin varoluşunun test edildiği, sorunları halı altına süpüremeyeceğiniz mutlak yüzleşme darboğazı.",
                8: "<b>Güven ve Kriz Sınavı:</b> Kıskançlıklar, gizli korkular veya ortak borçlar yüzeye çıkar. Manipülasyonu bırakıp şeffaf olma zamanı.",
                9: "<b>İnanç Sınavı:</b> Felsefi veya vizyon farklılıkları araya girebilir. Mesafeler (fiziksel veya fikirsel) aşılmalı ve ortak bir inanca tutunulmalıdır.",
                10: "<b>Statü Sınavı:</b> Dış dünyanın, ailenin veya kariyerin ilişkiniz üzerindeki baskısı. Aşkınızı dış engellere karşı bir kale gibi savunmalısınız.",
                11: "<b>Sosyal Sınav:</b> Çevrenizin ilişkiyi yıpratma potansiyeli. Gelecek planlarında ortaya çıkan tıkanıklıkları, sadece birbirinize yaslanarak aşabilirsiniz.",
                12: "<b>Karmik Yüzleşme Sınavı:</b> Bilinçaltında yatan en derin kaybetme veya yetersizlik korkularının tetiklendiği, kaçışın değil spiritüel yüzleşmenin gerektiği sınav."
            }
        sinav_yorum = sinav_sozlugu.get(saturn_ev, "Yılın sınavı görünmez kolonların dayanıklılığında gizli.")

        aci_metinleri = []
        if not acilar:
            if self.mod == "ebeveyn_cocuk":
                aci_metinleri.append("• Dışarıdan kadersel bir müdahale yok; ebeveyn-çocuk ilişkinizin akışı tamamen sizin kendi pedagojik kararlarınızda.")
            else:
                aci_metinleri.append("• Dışarıdan kadersel bir müdahale yok, ilişkinin dümeni tamamen sizin kendi saf iradenizde.")
        else:
            for aci in acilar:
                gez = aci["gezegen"]
                tip = aci["aci"]
                
                if self.mod == "ebeveyn_cocuk":
                    if gez == "Ay":
                        if tip == "Kavuşum": aci_metinleri.append("• <b>Güneş-Ay (Kavuşum):</b> Duygusal Senkronizasyon! Ebeveyn ve çocuk arasındaki duygusal bağın en güçlü hissedildiği, sezgisel iletişimin dorukta olduğu bir dönem.")
                        elif tip == "Karşıt": aci_metinleri.append("• <b>Güneş-Ay (Karşıt):</b> Duygusal Çekişme! Ebeveynin beklentileri ile çocuğun duygusal ihtiyaçları arasında bir denge arayışı söz konusu. Sabır ve anlayış kritik.")
                        else: aci_metinleri.append(f"• <b>Güneş-Ay ({tip}):</b> Duygusal ihtiyaçlar ile ortak hedefler arasında destekleyici bir akış var.")
                    elif gez == "Merkür":
                        aci_metinleri.append(f"• <b>Güneş-Merkür:</b> İletişim Köprüsü! Çocuğunuzla zihinsel uyumun arttığı, birbirinizi derinlemesine anladığınız pedagojik bir dönem.")
                    elif gez == "Venüs":
                        aci_metinleri.append(f"• <b>Güneş-Venüs:</b> Sevgi Dili! Bu yıl ebeveyn-çocuk arasındaki sevgi ve şefkat dili en yüksek oktavda çalışıyor. Takdir ve minnet ön planda.")
                    elif gez == "Mars":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"• <b>Güneş-Mars ({tip}):</b> Enerji Çatışması! Çocuğun bağımsızlık ihtiyacı ile ebeveynin sınırları arasındaki gerilim artabilir. Yapıcı yönlendirme kritik.")
                        else: aci_metinleri.append(f"• <b>Güneş-Mars ({tip}):</b> Eylem Gücü! Birlikte enerjik ve verimli bir dönem. Çocuğun cesaretlendirilmesi ve desteklenmesi ön planda.")
                    elif gez == "Satürn":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"• <b>Güneş-Satürn ({tip}):</b> Yapı Sınavı! Kurallar ve sınırlar test ediliyor. Sabırlı ve tutarlı bir yaklaşımla bu sınavı aşabilirsiniz.")
                        else: aci_metinleri.append(f"• <b>Güneş-Satürn ({tip}):</b> Yapı Mührü! Ebeveyn-çocuk ilişkisinde kalıcı temeller atılıyor. Sorumluluk ve güven inşası güçleniyor.")
                    elif gez == "Jüpiter":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"• <b>Güneş-Jüpiter ({tip}):</b> Aşırı İyimserlik! Çocuğunuzla ilgili beklentilerinizi gerçekçi tutun; abartılar hayal kırıklığına dönüşebilir.")
                        else: aci_metinleri.append(f"• <b>Güneş-Jüpiter ({tip}):</b> Genişleme ve Bolluk! Birlikte öğrenme, keşfetme ve büyüme fırsatlarının bol olduğu kadersel bir dönem.")
                    elif gez == "KAD":
                        if tip == "Kavuşum": aci_metinleri.append("• <b>KAD Teması:</b> Kadersel Öğrenme! Ebeveyn-çocuk arasındaki kadersel derslerin en yoğun hissedildiği, birlikte tekamül edildiği uyanış yılı.")
                        elif tip == "Karşıt": aci_metinleri.append("• <b>GAD Teması:</b> Geçmiş Kalıpları Terk Etme! Eski ebeveynlik kalıplarından ve korkularından kurtulma zamanı.")
                        else: aci_metinleri.append(f"• <b>Düğüm Teması ({tip}):</b> Kadersel rotanız ile pedagojik vizyonunuz arasında taşların yerine oturduğu senkronizasyon dönemi.")
                    elif gez == "Uranüs":
                        aci_metinleri.append(f"• <b>Güneş-Uranüs ({tip}):</b> Beklenmedik Değişim! Çocuğunuzun gelişiminde ani sıçramalar veya sürpriz gelişmeler yaşanabilir. Esneklik kritik.")
                    elif gez == "Neptün":
                        aci_metinleri.append(f"• <b>Güneş-Neptün ({tip}):</b> Sezgisel Bağ! Çocuğunuzla aranızdaki sezgisel bağın güçlendiği, birbirinizi sözlerin ötesinde anladığınız bir dönem.")
                    elif gez == "Plüton":
                        aci_metinleri.append(f"• <b>Güneş-Plüton ({tip}):</b> Derin Dönüşüm! Ebeveyn-çocuk ilişkisinde köklü bir dönüşüm yaşanabilir. Krizler şifaya dönüşme potansiyeli taşıyor.")
                else:
                    if gez == "Ay":
                        if tip == "Kavuşum": aci_metinleri.append("• <b>Güneş-Ay (Kavuşum):</b> Muazzam bir Yeniay yılı! Mantık ve duygu kusursuz senkronize; yepyeni bir duygu tohumu atıyorsunuz.")
                        elif tip == "Karşıt": aci_metinleri.append("• <b>Güneş-Ay (Karşıt):</b> Dolunay yılı! İlişkide bir dönemin meyvesini alıyorsunuz ancak beklentilerde ufak bir çekişme yaşanabilir.")
                        else: aci_metinleri.append(f"• <b>Güneş-Ay ({tip}):</b> Duygusal ihtiyaçlar ile ortak hedefler arasında destekleyici bir akış var.")
                    elif gez == "Merkür":
                        aci_metinleri.append(f"• <b>Güneş-Merkür:</b> Telepatik Uyum! Zihinlerin birleştiği, imzaların, sözleşmelerin ve iletişimin yılın kaderini belirlediği rasyonel dönem.")
                    elif gez == "Venüs":
                        aci_metinleri.append(f"• <b>Güneş-Venüs:</b> Aşkın Mührü! Bu yıl tutku, romantizm ve finansal bereket doğrudan ilişkinin merkezine akıyor. Sevgi diliniz en yüksek oktavda.")
                    elif gez == "Mars":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"• <b>Güneş-Mars ({tip}):</b> BUYUK SINAV! Agresyon ve tartışma riski. Bu gergin enerjiyi kavgaya değil, ortak bir projeye harcayın.")
                        else: aci_metinleri.append(f"• <b>Güneş-Mars ({tip}):</b> İnanılmaz bir motor gücü. Birlikte cesaretle ilerlemek ve engelleri aşmak için harika bir eylem yılı.")
                    elif gez == "Satürn":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"• <b>Güneş-Satürn ({tip}):</b> DARBOĞAZ! Kurallar ve engeller ilişkinin neşesini bastırabilir. Bu bir testtir, inşaya ve sabra odaklanın.")
                        else: aci_metinleri.append(f"• <b>Güneş-Satürn ({tip}):</b> Çelik Mühür! İlişkinin temelleri beton dökülmüşcesine sağlamlaşıyor. Uzun vadeli kararlar için koruyucu etki.")
                    elif gez == "Jüpiter":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"• <b>Güneş-Jüpiter ({tip}):</b> Aşırı iyimserlik, lüzumsuz para harcama veya tutulamayacak büyük sözler verme riskine dikkat edin.")
                        else: aci_metinleri.append(f"• <b>Güneş-Jüpiter ({tip}):</b> İlahi Genişleme! Şansın, bolluğun ve vizyonun ilişkinize nehir gibi aktığı kadersel şans yılı.")
                    elif gez == "KAD":
                        if tip == "Kavuşum": aci_metinleri.append("• <b>KAD Teması:</b> Kadersel Sıçrama! İlişkinin tamamen evrenin sizden beklediği ortak tekamül hedefine kilitlendiği uyanış yılı.")
                        elif tip == "Karşıt": aci_metinleri.append("• <b>GAD Teması:</b> Geçmişin Ayak Bağı! İlişkinin ilerleyebilmesi için eski toksik alışkanlıkları ve geçmiş karmaları tamamen terk etme zamanı.")
                        else: aci_metinleri.append(f"• <b>Düğüm Teması ({tip}):</b> Kadersel rotanız ile iradeniz arasında taşların yerine oturduğu senkronizasyon dönemi.")
                    elif gez == "Uranüs":
                        aci_metinleri.append(f"• <b>Güneş-Uranüs ({tip}):</b> Devrim! Ani sürprizlerin veya rutin kırıcı yeniliklerin yılı. Esnek olan ve yeniliğe açık olan kazanır.")
                    elif gez == "Neptün":
                        aci_metinleri.append(f"• <b>Güneş-Neptün ({tip}):</b> İlahi Çekim. Birlikte hayal kurduğunuz, sınırların eridiği bir şifa yılı. Kurban/kurtarıcı tuzağına düşmeyin.")
                    elif gez == "Plüton":
                        aci_metinleri.append(f"• <b>Güneş-Plüton ({tip}):</b> Yeraltı Simyası. İlişkinin saklı gölgelerinin yüzeye çıktığı, yıkıcı ama bir o kadar da baştan yaratıcı kriz yılı.")

        aci_rapor = "<br/>".join(aci_metinleri)

        if self.mod == "ebeveyn_cocuk":
            metin = f"""
            <font color="#1A1A2E">
            <b>📅 {yil} YILI - EBEVEYN-ÇOCUK PEDAGOJİK YIL HARİTASI</b><br/>
            <br/>
            <b>Bu Yılın Pedagojik Vitrini:</b><br/>
            {vitrin_yorum}<br/>
            <br/>
            <b>Ebeveynlik Rotası:</b><br/>
            {yonetici_yorum}<br/>
            <br/>
            <b>Yılın Odak Noktası ve Gelişim Alanı (Güneş):</b><br/>
            {odak_yorum}<br/>
            <br/>
            <b>Yılın Sınavı ve Öğrenme Alanı (Satürn):</b><br/>
            {sinav_yorum}<br/>
            <br/>
            <b>YILIN PEDAGOJİK TETİKLEYİCİLERİ:</b><br/>
            {aci_rapor}
            </font>
            """
        else:
            metin = f"""
            <font color="#1A1A2E">
            <b>📅 {yil} YILI KADERSEL KONTRATI</b><br/>
            <br/>
            <b>İlişkinin Bu Yılki Vitrini:</b><br/>
            {vitrin_yorum}<br/>
            <br/>
            <b>Yükselen Yöneticisinin Rotası:</b><br/>
            {yonetici_yorum}<br/>
            <br/>
            <b>Yılın Kutsal Amacı ve Üretim Merkezi (Güneş):</b><br/>
            {odak_yorum}<br/>
            <br/>
            <b>Yılın Büyük Sınavı ve Darboğazı (Satürn):</b><br/>
            {sinav_yorum}<br/>
            <br/>
            <b>YILIN İLAVE KADERSEL TETİKLEYİCİLERİ:</b><br/>
            {aci_rapor}
            </font>
            """
        return metin

    def calculate_lunar_return_tema(self, j_referans, hedef_yil, hedef_ay):
        """
        Aylık Duygusal İklimi (Lunar Return) İteratif Olarak Bulur.
        Ay'ın, Bağıl Haritadaki (Kök Ruh) doğum derecesine tam döndüğü saniyeyi hesaplar.
        """
        import swisseph as swe
        
        # 1. Kök Ruh'un Ay derecesi
        try:
            natal_ay = swe.calc_ut(j_referans, swe.MOON)[0][0]
        except Exception:
            return f"<b>{hedef_ay}/{hedef_yil} AYLIK İKLİM:</b> Ay verisine ulaşılamadı."

        # 2. O ayın 15'ini (ortasını) tahmini başlangıç noktası alıyoruz
        tahmini_j_gun = swe.julday(hedef_yil, hedef_ay, 15, 12.0)
        
        # 3. İTERATİF ARAMA (Ay çok hızlı olduğu için iterasyon limitini 20 yapıyoruz)
        j_return = tahmini_j_gun
        for iterasyon in range(20):
            res_trans = swe.calc_ut(j_return, swe.MOON)
            transit_ay = res_trans[0][0]
            
            fark = natal_ay - transit_ay
            if fark > 180: fark -= 360
            if fark < -180: fark += 360
            
            if abs(fark) < 0.0001: break
            
            # Ay günde ortalama 13.17 derece hareket eder
            ay_hizi = res_trans[0][3] if res_trans[0][3] != 0 else 13.17
            j_return += fark / ay_hizi 
            
        # 4. AYLIK HARİTA VERİLERİNİ ÇEK
        asc_burc = self.yukselen_bul(j_return)
        if asc_burc == "Hesaplanamadi": asc_burc = "Yengeç" 
        
        ay_ev = self.ev_konumu_bul(j_return, swe.MOON)
        if type(ay_ev) != int: ay_ev = 1

        # AY'IN AÇILARI (Aylık Duygusal Tetikleyiciler)
        ay_acilar = []
        gezegenler_kontrol = {
            "Güneş": swe.SUN, "Merkür": swe.MERCURY, "Venüs": swe.VENUS, 
            "Mars": swe.MARS, "Jüpiter": swe.JUPITER, "Satürn": swe.SATURN, 
            "Uranüs": swe.URANUS, "Neptün": swe.NEPTUNE, "Plüton": swe.PLUTO
        }
        
        for gez_isim, gez_id in gezegenler_kontrol.items():
            try:
                gez_derece = swe.calc_ut(j_return, gez_id)[0][0]
                aci_farki = abs(transit_ay - gez_derece)
                if aci_farki > 180: aci_farki = 360 - aci_farki
                gez_evi = self.ev_konumu_bul(j_return, gez_id)
                
                if abs(aci_farki - 0) <= 8: ay_acilar.append({"gezegen": gez_isim, "aci": "Kavuşum", "ev": gez_evi})
                elif abs(aci_farki - 90) <= 8: ay_acilar.append({"gezegen": gez_isim, "aci": "Kare", "ev": gez_evi})
                elif abs(aci_farki - 120) <= 8: ay_acilar.append({"gezegen": gez_isim, "aci": "Üçgen", "ev": gez_evi})
                elif abs(aci_farki - 180) <= 8: ay_acilar.append({"gezegen": gez_isim, "aci": "Karşıt", "ev": gez_evi})
            except Exception:
                pass

        lr_data = {
            "yil": hedef_yil,
            "ay": hedef_ay,
            "aylik_vitrin": asc_burc,
            "ay_ev": ay_ev,
            "acilar": ay_acilar
        }
        
        return self.lunar_return_metni_yaz(lr_data)

    def lunar_return_metni_yaz(self, lr_data):
        ay_isimleri = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        yil = lr_data["yil"]
        ay_no = lr_data["ay"]
        ay_isim = ay_isimleri[ay_no]
        
        asc = lr_data["aylik_vitrin"]
        ay_ev = lr_data["ay_ev"]
        acilar = lr_data["acilar"]

        if self.mod == "ebeveyn_cocuk":
            vitrin_sozlugu_lr = {
                "Koc": f"Bu ayki duygusal refleksleriniz <b>Koç</b> burcu temasında çalışacak. Çocuğunuzun bağımsızlık ihtiyacı ve keşif enerjisi bu ay yüksek. Sabırlı ve destekleyici bir ebeveynlik yaklaşımı, çocuğun cesaretini besler.",
                "Boga": f"Bu ayki duygusal refleksleriniz <b>Boğa</b> burcu temasında çalışacak. Güven, istikrar ve fiziksel konfor bu ayın odak noktası. Çocuğunuzla birlikte huzurlu ve sakin aktiviteler yapmak ruhunuzu besleyecek.",
                "Ikizler": f"Bu ayki duygusal refleksleriniz <b>İkizler</b> burcu temasında çalışacak. Bol iletişim, merak ve öğrenme ihtiyacı bu ay ön planda. Çocuğunuzla sohbet etmek, kitap okumak ve birlikte yeni şeyler keşfetmek bu ayın anahtarı.",
                "Yengec": f"Bu ayki duygusal refleksleriniz <b>Yengeç</b> burcu temasında çalışacak. Aile, yuva ve duygusal bağlanma bu ay her şeyin önünde. Çocuğunuzla evde vakit geçirmek ve duygusal bağınızı derinleştirmek çok iyi gelecek.",
                "Aslan": f"Bu ayki duygusal refleksleriniz <b>Aslan</b> burcu temasında çalışacak. Takdir, takdir ve yaratıcılık bu ayın anahtarı. Çocuğunuzun çabalarını takdir etmek ve onu cesaretlendirmek bu ay en değerli pedagojik yatırımı olacak.",
                "Basak": f"Bu ayki duygusal refleksleriniz <b>Başak</b> burcu temasında çalışacak. Düzen, sağlık ve pratik konular bu ay ön planda. Çocuğunuzla birlikte düzenli alışkanlıklar edinmek ve sağlık konularına odaklanmak faydalı olacak.",
                "Terazi": f"Bu ayki duygusal refleksleriniz <b>Terazi</b> burcu temasında çalışacak. Uyum, denge ve adalet bu ayın öncelikleri. Ebeveyn-çocuk ilişkisinde dengeyi korumak ve karşılıklı saygıyı güçlendirmek kritik.",
                "Akrep": f"Bu ayki duygusal refleksleriniz <b>Akrep</b> burcu temasında çalışacak. Yoğun duygular ve derinleşme bu ayın imzası. Çocuğunuzun iç dünyasını keşfetmek ve duygusal derinleşmesine tanık olmak bu ayın önemli deneyimi.",
                "Yay": f"Bu ayki duygusal refleksleriniz <b>Yay</b> burcu temasında çalışacak. Keşif, genişleme ve öğrenme ihtiyacı bu ay yüksek. Çocuğunuzla birlikte yeni deneyimler yaşamak ve ufkunuzu genişletmek ruhunuzu besleyecek.",
                "Oglak": f"Bu ayki duygusal refleksleriniz <b>Oğlak</b> burcu temasında çalışacak. Yapı, sorumluluk ve ciddiyet bu ayın duygusal tonu. Kurallar ve sınırlar konusunda net ve tutarlı olmak bu ayın önemli bir sınavı.",
                "Kova": f"Bu ayki duygusal refleksleriniz <b>Kova</b> burcu temasında çalışacak. Bireysel alan ve özgürlük bu ay kritik. Çocuğunuzun bireysel alanına saygı göstermek ve bağımsızlığını desteklemek bu ayın önemli bir dersi.",
                "Balik": f"Bu ayki duygusal refleksleriniz <b>Balık</b> burcu temasında çalışacak. Sezgiler, şefkat ve duygusal hassasiyet bu ayın ana temaları. Mantıktan ziyade kalbi dinlemek, çocuğunuzla sezgisel bir bağ kurmak bu ayın şifası."
            }
        else:
            vitrin_sozlugu_lr = {
                "Koc": f"Bu ayki duygusal refleksleriniz <b>Koç</b> burcu temasında çalışacak. Ani kararlar, ateşli tartışmalar ve hızlı barışmalar bu ayın duygusal ritmi. Enerjinizi kavgaya değil, birlikte yeni bir şeye başlamaya yönlendirin.",
                "Boga": f"Bu ayki duygusal refleksleriniz <b>Boğa</b> burcu temasında çalışacak. Fiziksel temas, güzel yemekler ve huzurlu bir ev ortamı ruhunuzu besleyecek. Bu ay aceleci kararlardan kaçının, sakinlik ve istikrar önceliğiniz.",
                "Ikizler": f"Bu ayki duygusal refleksleriniz <b>İkizler</b> burcu temasında çalışacak. Çok konuşacak, çok mesajlaşacak ve planlarınız sık değişecek. Zihinsel uyum bu ay duygusal yakınlığın anahtarı.",
                "Yengec": f"Bu ayki duygusal refleksleriniz <b>Yengeç</b> burcu temasında çalışacak. Ev, aile ve aidiyet duygusu bu ay her şeyin önüne geçiyor. Birbirinize sığınmak ve dışarıya kapıları kapatmak size iyi gelecek.",
                "Aslan": f"Bu ayki duygusal refleksleriniz <b>Aslan</b> burcu temasında çalışacak. Takdir görmek, cömert olmak ve ilişkinizi kutlamak bu ayın ana ihtiyacı. Birbirinizi bol bol övün ve romantik sürprizler yapın.",
                "Basak": f"Bu ayki duygusal refleksleriniz <b>Başak</b> burcu temasında çalışacak. Pratik yardım ve düzen bu ay sevgi diliniz. Birbirinizin hayatını kolaylaştırmak en büyük duygusal bağ kurma yönteminiz.",
                "Terazi": f"Bu ayki duygusal refleksleriniz <b>Terazi</b> burcu temasında çalışacak. Uyum, adalet ve estetik bu ayın öncelikleri. Tartışmalar yerine uzlaşı arayın; birlikte güzel bir ortam yaratmak ruhunuzu tazeleyecek.",
                "Akrep": f"Bu ayki duygusal refleksleriniz <b>Akrep</b> burcu temasında çalışacak. Yoğun duygular, derin sohbetler ve güçlü bir fiziksel çekim bu ayın imzası. Gizli kalmış duygularınızı paylaşmak ilişkinizi derinleştirecek.",
                "Yay": f"Bu ayki duygusal refleksleriniz <b>Yay</b> burcu temasında çalışacak. Özgürlük, macera ve yeni deneyimler bu ay ruhunuzu besliyor. Birlikte yeni bir şey keşfetmek veya ufku genişleten bir sohbet yapmak duygusal açlığınızı giderecek.",
                "Oglak": f"Bu ayki duygusal refleksleriniz <b>Oğlak</b> burcu temasında çalışacak. Ciddiyet ve sorumluluk bu ayın duygusal tonu. Duygularınızı kelimelerle değil, somut adımlar ve güvenilir davranışlarla gösterin.",
                "Kova": f"Bu ayki duygusal refleksleriniz <b>Kova</b> burcu temasında çalışacak. Bireysel alan ve özgürlük bu ay kritik. Birbirinize nefes alma alanı tanıyın; bağımsızlığa saygı göstermek bu ay ilişkinizi güçlendirecek.",
                "Balik": f"Bu ayki duygusal refleksleriniz <b>Balık</b> burcu temasında çalışacak. Sezgiler, rüyalar ve koşulsuz şefkat bu ayın ana temaları. Mantık yerine kalbi dinleyin; birbirinize karşı nazik ve anlayışlı olmak her şeyi çözecek."
            }
        vitrin_yorum = vitrin_sozlugu_lr.get(asc, f"Bu ayki duygusal refleksleriniz <b>{asc}</b> burcu temasında çalışacak.")

        if self.mod == "ebeveyn_cocuk":
            ay_ev_sozlugu = {
                1: "Bu ay çocuğunuzun bireysel kimliği ve bağımsızlık ihtiyacı ön planda. Onun kendi kararlarını alma sürecine destek olmak, bu ayın en önemli pedagojik fırsatı. Birlikte yeni bir hobi veya aktivite keşfetmek bağınızı güçlendirecek.",
                2: "Bu ay çocuğunuzun kendine olan güveni ve yeteneklerinin farkındalığı artıyor. Takdir ve minnet dilinizi bu ay bol bol kullanın. Birlikte somut bir proje yapmak veya yeni bir beceri öğrenmek bu ayın değerli deneyimi olacak.",
                3: "Bu ay iletişim ve öğrenme ihtiyacı çok yüksek. Çocuğunuzla bol bol sohbet etmek, sorularına sabırla cevap vermek ve birlikte kitap okumak bu ayın en değerli pedagojik faaliyeti. Kısa bir gezinti veya doğa yürüyüşü de ruhunuzu besleyecek.",
                4: "Bu ay ev ve aile içi konular öne çıkıyor. Çocuğunuzla evde güvenli ve huzurlu bir ortam yaratmak, duygusal bağınızı derinleştirecek. Birlikte yemek yapmak, film izlemek veya evi güzelleştirmek bu ayın şifalı aktiviteleri.",
                5: "Bu ay yaratıcılık ve neşe enerjisi çok yüksek. Çocuğunuzla birlikte oyun oynamak, sanatsal faaliyetler yapmak veya sadece eğlenmek bu ayın en önemli ihtiyacı. İçinizdeki çocuğu keşfetmek ve paylaşmak bu ayın hediyesi.",
                6: "Bu ay düzen, sağlık ve pratik konular ön planda. Çocuğunuzla birlikte sağlıklı alışkanlıklar edinmek, düzenli bir rutin oluşturmak bu ayın somut kazanımı. Birlikte temizlik yapmak veya mutfakta vakit geçirmek bile değerli bir deneyim olabilir.",
                7: "Bu ay ebeveyn-çocuk dengesi ve uyumu çok önemli. Çocuğunuzun ihtiyaçlarını anlamak, onun perspektifinden bakmaya çalışmak bu ayın en değerli dersi. Birlikte ortak kararlar almak ve uzlaşmak bu ayın öğretisi.",
                8: "Bu ay duygusal derinleşme ve yüzleşme zamanı. Çocuğunuzun iç dünyasındaki derin duyguları keşfetmek, onun korkularını ve endişelerini anlamak bu ayın önemli bir deneyimi. Sabırlı ve anlayışlı olmak bu ayın şifası.",
                9: "Bu ay ufuk genişletme ve keşif enerjisi çok yüksek. Çocuğunuzla birlikte yeni yerler keşfetmek, yeni şeyler öğrenmek veya felsefi sohbetler yapmak bu ayın değerli deneyimleri. Birlikte büyümenin ve öğrenmenin tadını çıkarın.",
                10: "Bu ay yapı, sorumluluk ve ciddiyet ön planda. Çocuğunuz için kalıcı temeller atmak, kurallar ve sınırlar koymak bu ayın önemli bir görevi. Ebeveyn olarak kararlı ve tutarlı olmak bu ayın en büyük desteği.",
                11: "Bu ay sosyal çevre ve gelecek planları öne çıkıyor. Çocuğunuzun arkadaşlık ilişkilerine ve sosyal ihtiyaçlarına destek olmak bu ayın önemli bir parçası. Birlikte gelecek hakkında konuşmak ve ortak hedefler belirlemek değerli bir deneyim.",
                12: "Bu ay içe çekilme ve ruhsal derinleşme zamanı. Çocuğunuzla sessiz ve derin bir bağ kurmak, sezgisel iletişimi güçlendirmek bu ayın en değerli deneyimi. Doğada vakit geçirmek, meditasyon yapmak veya sadece sessizce birlikte olmak ruhunuzu besleyecek."
            }
        else:
            ay_ev_sozlugu = {
                1: "Bu ay ilişkinizde 'Ben' duygusu çok yüksek. Alınganlıklar artabilir, karşılıklı olarak kendi duygusal sınırlarınızı koruma ihtiyacı hissedeceksiniz. Kendi kişisel ihtiyaçlarınızı dile getirmekten çekinmeyin; kuaföre gitmek, yeni bir kıyafet almak veya imajınızı yenilemek bu ay ilişkinize taze bir hava katacaktır.",
                2: "Bu ayki duygusal güvenliğiniz tamamen 'finansal ve fiziksel değerlere' bağlı. Para harcamak, hediyeleşmek veya lüks bir yemek ruhunuza iyi gelecek. Birlikte bütçe planlaması yapmak veya uzun zamandır almak istediğiniz o özel eşyayı eve sipariş etmek bu ayki duygusal açlığınızı giderecektir.",
                3: "Bu ay sadece konuşmak, anlaşılmak ve mesajlaşmak istiyorsunuz. Zihinsel uyumun, sözlerin ve kısa kaçamak tatillerin şifa vereceği bir dönem. Yakın çevredeki bir göl kenarına veya komşu şehre hafta sonu arabayla gitmek, yol boyunca uzun uzun sohbet etmek bu ayki en büyük kadersel şifanız.",
                4: "Bu ay dışarı çıkmak yerine aynı kanepede film izleme, birbirinize sığınma ve evde baş başa vakit geçirme ayınız. Aidiyet test ediliyor. Eve yeni bir bitki almak, birlikte mutfağa girip yeni bir tarif denemek veya yatak odasının dekorunu değiştirmek ruhsal olarak sizi birbirinize kenetleyecektir.",
                5: "Duygusal olarak flörtöz, eğlenceli ve çocuksu hissettiğiniz bir ay. Romantizm ve tutku ihtiyacı tavan yapıyor. Bu ay ilişkinin sorumluluklarını bir kenara bırakıp sinemaya gitmek, lunaparkta eğlenmek veya sadece tutkulu sürprizlerle birbirinizi şımartmak için harika bir dönem.",
                6: "Bu ay romantizmden ziyade 'Bana ne kadar yardımcı oluyorsun?' ayıdır. Birlikte diyet yapmak, temizlik yapmak veya işleri organize etmek sizi birbirinize bağlar. Evi baştan aşağı temizlemek, birlikte check-up yaptırmak veya ofis stresinizi birbirinize masaj yaparak atmak bu ayın somut sevgi göstergeleridir.",
                7: "Tamamen partnerinize odaklandığınız, 'Biz' olmanın duygusal güvenliğini aradığınız bir dönem. Onaylanma ihtiyacınız yüksek. Kararlar alırken 'Sence nasıl yapalım?' sorusunu sıkça sormalı, baş başa şık bir akşam yemeğine çıkarak aranızdaki o denge terazisini yeniden ayarlamalısınız.",
                8: "Kıskançlık, derin tutku ve 'Bana ruhunu aç' dediğiniz o yoğun simya ayı. Krizleri çözerek veya yatak odası sırlarıyla bağınız güçlenir. Yüzeysel konulardan ziyade, birbirinizin en gizli korkularını dinlediğiniz gece yarısı sohbetleri ve güçlü bir cinsel çekim bu ay ilişkinizi baştan yaratacaktır.",
                9: "Bu ay ilişkinin rutininden sıkılıp, birlikte yeni felsefeler konuşmak, yurt dışı planları yapmak veya uzaklara gitmek istiyorsunuz. Yeni bir belgesel serisine başlamak, yabancı kültürlere ait bir restoranda yemek yemek veya gelecek yılın tatil rotasını planlamak ruhunuza genişleme hissi verecektir.",
                10: "Duygularınızı ulu orta göstermek yerine, ilişkinizin ciddiyetine ve toplum önündeki duruşunuza odaklanıyorsunuz. Aile büyükleri gündemde olabilir. Partnerinizin kariyerindeki bir başarıyı kutlamak, aile yemeklerine katılmak veya ilişkinizin statüsünü (nişan, söz vb.) ciddileştirecek kararlar almak bu ayın ana teması.",
                11: "Bu ay romantik aşıklar olmak yerine 'en iyi iki dost' olmak size iyi gelecek. Sosyalleşmek ve ortak arkadaşlarla vakit geçirmek duyguları şifalandırır. Evinize kalabalık misafirler davet etmek, ortak arkadaşlarınızla oyun geceleri düzenlemek veya bir sosyal sorumluluk projesine birlikte destek vermek ilişkinizi tazeleyecektir.",
                12: "Kozadan çıkmak istemediğiniz, alıngan, mistik ve sezgisel bir ay. Duygusal yorgunlukları sessiz kalarak ve birbirinizin ruhuna dokunarak atabilirsiniz. Kalabalıklardan uzaklaşıp doğada sessiz bir yürüyüş yapmak, birlikte meditasyon yapmak veya birbirinizin rüyalarını yorumlamak bu içsel ayın en büyük ruhsal ilacıdır."
            }
        odak_yorum = ay_ev_sozlugu.get(ay_ev, f"Bu ay duygusal odak noktanız {ay_ev}. evde.")

        aci_metinleri = []
        if not acilar:
            if self.mod == "ebeveyn_cocuk":
                aci_metinleri.append("Bu ay ebeveyn-çocuk duygusal akışınız son derece sakin ve dış etkenlerden bağımsız.")
            else:
                aci_metinleri.append("Bu ay duygusal akışınız son derece sakin ve dış etkenlerden bağımsız (Gezegen açısı yok).")
        else:
            for aci in acilar:
                gez = aci["gezegen"]
                tip = aci["aci"]
                
                if self.mod == "ebeveyn_cocuk":
                    if gez == "Güneş":
                        aci_metinleri.append(f"<b>Ay-Güneş Teması ({tip}):</b> Ebeveyn-çocuk arasındaki duygusal dengenin güçlendiği, sezgisel iletişimin arttığı bir dönem.")
                    elif gez == "Mars":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"<b>Ay-Mars {tip}:</b> Duygusal patlamalar ve alınganlık riski. Çocuğunuzun bağımsızlık ihtiyacı ile sınırlarınız arasındaki gerilim artabilir. Sabırlı ve yapıcı olun.")
                        else: aci_metinleri.append(f"<b>Ay-Mars {tip}:</b> Enerjik ve verimli bir ay. Çocuğunuzla birlikte aktif ve yaratıcı faaliyetler için mükemmel bir dönem.")
                    elif gez == "Satürn":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"<b>Ay-Satürn {tip}:</b> Yapı ve disiplin sınavı. Kurallar ve sınırlar test ediliyor. Sabırlı ve tutarlı olmak bu ayın en büyük dersi.")
                        else: aci_metinleri.append(f"<b>Ay-Satürn {tip}:</b> Yapı ve güvence ayı. Ebeveyn-çocuk ilişkisinde kalıcı temeller atılıyor. Sorumluluk ve güven inşası güçleniyor.")
                    elif gez == "Venüs":
                        aci_metinleri.append(f"<b>Ay-Venüs {tip}:</b> Sevgi ve şefkat ayı. Ebeveyn-çocuk arasındaki sevgi ve şefkat dili bu ay çok güçlü. Takdir ve minnet ön planda.")
                    elif gez == "Plüton":
                        aci_metinleri.append(f"<b>Ay-Plüton {tip}:</b> Duygusal derinleşme ve dönüşüm. Çocuğunuzun iç dünyasındaki derin duygular yüzeye çıkabilir. Sabırlı ve anlayışlı olmak kritik.")
                    elif gez == "Merkür":
                        aci_metinleri.append(f"<b>Ay-Merkür {tip}:</b> İletişim ve anlama ayı. Çocuğunuzla aranızdaki iletişim bu ay çok güçlü. Birbirinizi derinlemesine anlama dönemi.")
                    elif gez == "Jüpiter":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"<b>Ay-Jüpiter {tip}:</b> Duygusal abartı uyarısı. Çocuğunuzla ilgili beklentilerinizi gerçekçi tutun.")
                        else: aci_metinleri.append(f"<b>Ay-Jüpiter {tip}:</b> Bereket ve neşe ayı. Birlikte öğrenme, keşfetme ve büyüme fırsatlarının bol olduğu bir dönem.")
                    elif gez == "Uranüs":
                        aci_metinleri.append(f"<b>Ay-Uranüs {tip}:</b> Beklenmedik gelişmeler ve sürprizler. Çocuğunuzun gelişiminde ani sıçramalar olabilir. Esnek olun.")
                    elif gez == "Neptün":
                        aci_metinleri.append(f"<b>Ay-Neptün {tip}:</b> Sezgisel bağın güçlendiği bir ay. Çocuğunuzla aranızdaki sezgisel iletişim çok güçlü. Birlikte sanatsal faaliyetler yapmak ruhunuzu besleyecek.")
                else:
                    if gez == "Güneş":
                        aci_metinleri.append(f"<b>Ay-Güneş Teması ({tip}):</b> Duygularınızla ortak mantığınız arasında kesişim. Bu ay ilişkinizin kalbiyle ruhu eşzamanlı atıyor.")
                    elif gez == "Mars":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"<b>Ay-Mars {tip}:</b> DIKKAT SINAVI! Duygusal patlamalar, ani sinir harpleri veya gereksiz alınganlıklardan kaynaklı kavga riski yüksek. Tutkuyu kavgaya değil, yapıcı bir fiziksel enerjiye dönüştürün.")
                        else: aci_metinleri.append(f"<b>Ay-Mars {tip}:</b> Bu ay inanılmaz bir eylem ve fiziksel tutku enerjisi var. İsteklerinizi hızlıca hayata geçirebilirsiniz.")
                    elif gez == "Satürn":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"<b>Ay-Satürn {tip}:</b> DARBOĞAZ! Duygusal mesafe, soğukluk veya 'yetersiz sevgi' hissi yaşanabilir. Duvar örmek yerine bu ayki sınavın 'sabır ve olgunluk' olduğunu hatırlayın.")
                        else: aci_metinleri.append(f"<b>Ay-Satürn {tip}:</b> Duyguların çok ayakları yere bastığı, taahhütlerin ve sadakatin perçinlendiği ağırbaşlı ve güven verici bir ay.")
                    elif gez == "Venüs":
                        aci_metinleri.append(f"<b>Ay-Venüs {tip}:</b> Şefkat Mührü! Bu ay ilişkinizde romantizm, dişil enerji ve tatlı dil ön planda. Kusursuz bir barışma ve aşk ayı.")
                    elif gez == "Plüton":
                        aci_metinleri.append(f"<b>Ay-Plüton {tip}:</b> Derin psikolojik okumalar, takıntılar veya tutkulu bir sahiplenme. Zehirli kıskançlıklara dikkat edildiği sürece bağınızı çelikleştirir.")
                    elif gez == "Merkür":
                        aci_metinleri.append(f"<b>Ay-Merkür {tip}:</b> Zihinsel Uyum Ayı! Duygularınızı kelimelerle ifade etme ihtiyacı had safhada. Uzun sohbetler, mesajlaşmak ve birbirinizi dinlemek bu ayın en büyük şifa aracı.")
                    elif gez == "Jüpiter":
                        if tip in ["Kare", "Karşıt"]: aci_metinleri.append(f"<b>Ay-Jüpiter {tip}:</b> Duygusal abartı uyarısı! Beklentilerinizi ve vaatlerinizi gerçekçi tutun; aşırı iyimserlik hayal kırıklığına dönüşebilir.")
                        else: aci_metinleri.append(f"<b>Ay-Jüpiter {tip}:</b> Bereket ve Neşe Ayı! Duygusal açıdan son derece cömert ve pozitif bir dönem. Birlikte kutlamalar yapmak, seyahat etmek veya büyük bir hediye almak için mükemmel zaman.")
                    elif gez == "Uranüs":
                        aci_metinleri.append(f"<b>Ay-Uranüs {tip}:</b> Duygusal Sürpriz! Bu ay beklenmedik bir gelişme veya ani bir karar ilişkinin seyrini değiştirebilir. Esnekliğinizi koruyun ve değişime direnmek yerine ona uyum sağlayın.")
                    elif gez == "Neptün":
                        aci_metinleri.append(f"<b>Ay-Neptün {tip}:</b> İlahi Duygu Dalgası! Bu ay sezgileriniz ve empati kapasiteniz zirveye çıkıyor. Birlikte müzik dinlemek, film izlemek veya sanatsal bir şey üretmek ruhunuzu besler. Hayal kırıklığına karşı gerçekçi kalın.")

        aci_rapor = "<br/>".join(aci_metinleri)

        if self.mod == "ebeveyn_cocuk":
            metin = f"""
            <b>📅 {ay_isim} {yil} - AYLIK EBEVEYN-ÇOCUK PEDAGOJİK İKLİMİ</b><br/>
            <b>Bu Ayın Duygusal Üniforması:</b> {vitrin_yorum}<br/>
            <br/>
            <b>Ayın Pedagojik Odak Noktası:</b> {odak_yorum}<br/>
            <br/>
            <b>AYIN PEDAGOJİK TETİKLEYİCİLERİ:</b><br/>
            {aci_rapor}<br/>
            <hr/>
            """
        else:
            metin = f"""
            <b>📅 {ay_isim} {yil} - AYLIK DUYGUSAL İKLİM (LUNAR RETURN)</b><br/>
            <b>Bu Ayın Duygusal Üniforması:</b> {vitrin_yorum}<br/>
            <br/>
            <b>Ayın Temel İhtiyacı:</b> {odak_yorum}<br/>
            <br/>
            <b>AYIN PSİKOLOJİK TETİKLEYİCİLERİ:</b><br/>
            {aci_rapor}<br/>
            <hr/>
            """
        return metin

@st.cache_resource(ttl=3600, max_entries=3)
def _motor_olustur(p1, p2, event_date, event_time, city, country, lat, lon,
                   p1_isim, p2_isim, mod, ebeveyn_rolu, _uo):
    motor = FBST_Engine(p1=p1, p2=p2, event_date=event_date, event_time=event_time,
                        city=city, country=country, lat=lat, lon=lon,
                        p1_isim=p1_isim, p2_isim=p2_isim, mod=mod,
                        ebeveyn_rolu=ebeveyn_rolu, utc_offset=_uo)
    motor.fbst_analizi_yap(sessiz=True)
    return motor

# --- 2. KISIM: STREAMLIT ARAYÜZÜ (APP) ---
st.markdown(f"""
<div style="text-align:center; padding:8px 0 2px 0;">
    <img src="data:image/png;base64,{_logo_b64}" style="width:110px; height:110px; border-radius:50%; object-fit:cover; border:3px solid #C9A96E; box-shadow:0 4px 20px rgba(201,169,110,0.4); margin-bottom:8px;" />
    <h1 style="margin:0; padding:0; font-family:'Cormorant Garamond',serif; color:#3D2E50; font-size:2.2rem; font-weight:700; letter-spacing:1px;">Fatih Asartepe Sinastri Tekniği</h1>
    <p style="margin:2px 0 0 0; color:#8A7F96; font-family:'DM Sans',sans-serif; font-size:0.85rem; letter-spacing:2px; text-transform:uppercase;">FAST — Kadersel Bağ Analizi Sistemi</p>
</div>
""", unsafe_allow_html=True)
st.markdown("**Sürüm 4.0 | 21 Yıllık Döngü, Çapraz Mühürler ve Nokta Atışı Ev Aktarımları**")
st.divider()

# 🛠️ SESSION STATE BAŞLATMA (önce, kartlardan önce)
if "analiz_ateslendi" not in st.session_state:
    st.session_state.analiz_ateslendi = False
if "radar_calistirildi" not in st.session_state:
    st.session_state.radar_calistirildi = False
if "pdf_hazir" not in st.session_state:
    st.session_state.pdf_hazir = False
if "sim_modu" not in st.session_state:
    st.session_state.sim_modu = "es_sevgili"
if "ebeveyn_rolu" not in st.session_state:
    st.session_state.ebeveyn_rolu = "anne"

# 1900'ü tanımlarken:
min_tarih = datetime(1900, 1, 1).date()

# Bugünün tarihini alırken:
max_tarih = datetime.today().date()

# ══════════════════════════════════════════════════════════════
# SİMÜLASYON SEÇİM KARTLARI (ANA ALAN)
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
.sim-card {
    padding: 32px 22px 22px 22px;
    border-radius: 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 16px;
    border: 2px solid #D4CFC8;
    background: linear-gradient(135deg, #FFFFFF 0%, #FBF7F4 100%);
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
    height: 100%;
}
.sim-card:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}
.sim-card.active {
    border-color: #C9A96E !important;
    box-shadow: 0 4px 20px rgba(201,169,110,0.3);
}
.sim-card-es { border-top: 5px solid #D4878F; }
.sim-card-eb { border-top: 5px solid #8FB8CA; }
.sim-card-py { border-top: 5px solid #B8A9C9; }
.sim-img {
    width: 120px; height: 120px; margin: 0 auto 14px auto;
    border-radius: 50%; overflow: hidden;
    border: 4px solid #C9A96E;
    box-shadow: 0 4px 16px rgba(201,169,110,0.3);
}
.sim-img img { width: 100%; height: 100%; object-fit: cover; }
.sim-title {
    font-size: 24px; font-weight: 700; color: #3D2E50;
    margin-bottom: 4px; font-family: 'Cormorant Garamond', serif;
}
.sim-desc { font-size: 13px; color: #8A7F96; line-height: 1.5; margin-bottom: 10px; }
.sim-features {
    text-align: left; font-size: 12.5px; color: #4A4A4A;
    line-height: 1.7; padding: 10px 6px 6px 6px;
    border-top: 1px solid #E8E0D8; margin-top: 10px;
}
.sim-features span { color: #C9A96E; }
</style>
""", unsafe_allow_html=True)

_es_aktif = st.session_state.sim_modu == "es_sevgili"
_eb_aktif = st.session_state.sim_modu == "ebeveyn_cocuk"
_py_aktif = st.session_state.sim_modu == "potansiyel_yetenek"

r1 = st.columns(2)
with r1[0]:
    st.markdown(f"""
    <div class="sim-card sim-card-es {'active' if _es_aktif else ''}">
        <div class="sim-img"><img src="data:image/png;base64,{_cift_b64}" /></div>
        <div class="sim-title">Eş / Sevgili</div>
        <div class="sim-desc">Sinastri &amp; Kadersel Bağ Analizi</div>
        <div class="sim-features">
            <span>✦</span> Çift haritası &amp; sinastri gezegen konumları<br>
            <span>✦</span> 21 yıllık ortak gelecek öngörüsü (yıllık/aylık/günlük)<br>
            <span>✦</span> Composite harita &amp; ortak kimlik analizi<br>
            <span>✦</span> Gezegen açıları, mühürler &amp; kadersel kontrat<br>
            <span>✦</span> İkili ilişki simyası, karmik bağ &amp; şifa reçeteleri<br>
            <span>✦</span> Açı mühürü gridi &amp; altın oran uyum mührü<br>
            <span>✦</span> Astrocartography küresel şehir taraması<br>
            <span>✦</span> 6 aylık kadersel hava durumu &amp; durak analizi<br>
            <span>✦</span> Arap noktaları radarı, kadersel zaman makinesi<br>
            <span>✦</span> Karmik ev mühürlenmesi &amp; asteroid etkileşimleri<br>
            <span>✦</span> Tam PDF raporu (sınırsız indirme hakkı)
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔥 Bu Simülasyonu Seç", key="btn_mod_es", use_container_width=True, type="primary" if not _es_aktif else "secondary"):
        st.session_state.sim_modu = "es_sevgili"
        st.rerun()

with r1[1]:
    st.markdown(f"""
    <div class="sim-card sim-card-eb {'active' if _eb_aktif else ''}">
        <div class="sim-img"><img src="data:image/png;base64,{_eb_b64}" /></div>
        <div class="sim-title">Ebeveyn / Çocuk</div>
        <div class="sim-desc">Potansiyel &amp; Gelişim Haritası</div>
        <div class="sim-features">
            <span>✦</span> Ebeveyn-çocuk kadersel bağ &amp; sinastri analizi<br>
            <span>✦</span> Composite harita: ortak ruh &amp; aile kimliği<br>
            <span>✦</span> Çocuğun potansiyel &amp; yetenek haritası (7 alan)<br>
            <span>✦</span> Gelişim dönemleri takvimi &amp; büyüme öngörüleri<br>
            <span>✦</span> Yıllık/aylık/günlük çocuk gelişim akışı<br>
            <span>✦</span> Meslek yönlendirme &amp; yetenek simülasyonu<br>
            <span>✦</span> Arap noktaları bağ analizi &amp; kadersel durak<br>
            <span>✦</span> Şifa reçeteleri, destek alanları &amp; asteroid etkileri<br>
            <span>✦</span> Gezegen açıları, mühürler &amp; astrocartography<br>
            <span>✦</span> Kadersel zaman makinesi (21 yıllık gelişim yolu)<br>
            <span>✦</span> Tam PDF raporu (sınırsız indirme hakkı)
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔥 Bu Simülasyonu Seç", key="btn_mod_eb", use_container_width=True, type="primary" if not _eb_aktif else "secondary"):
        st.session_state.sim_modu = "ebeveyn_cocuk"
        st.rerun()

r2 = st.columns([1, 2, 1])
with r2[1]:
    st.markdown(f"""
    <div class="sim-card sim-card-py {'active' if _py_aktif else ''}">
        <div class="sim-img"><img src="data:image/png;base64,{_py_b64}" /></div>
        <div class="sim-title">Potansiyel &amp; Yetenek</div>
        <div class="sim-desc">Tek Kişi Natal Analiz</div>
        <div class="sim-features">
            <span>✦</span> Gezegen pozisyonları &amp; natal harita analizi<br>
            <span>✦</span> Potansiyel ve yetenek alanları tespiti<br>
            <span>✦</span> Meslek yönlendirme önerileri
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔥 Bu Simülasyonu Seç", key="btn_mod_py", use_container_width=True, type="primary" if not _py_aktif else "secondary"):
        st.session_state.sim_modu = "potansiyel_yetenek"
        st.rerun()

st.divider()

# --- SOL PANEL (DANIŞAN BİLGİLERİ GİRİŞİ) ---
st.sidebar.markdown(f"""
<div style="text-align:center; padding: 8px 0 16px 0;">
    <img src="data:image/png;base64,{_logo_b64}" style="width:160px; filter:drop-shadow(0 2px 8px rgba(201,169,110,0.3));" />
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<style>
.mod-card {
    padding: 20px 14px;
    border-radius: 18px;
    text-align: center;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 10px;
    border: 2px solid transparent;
    background: linear-gradient(135deg, #FFFFFF 0%, #FBF7F4 100%);
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
}
.mod-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, #C9A96E, transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.mod-card:hover::before {
    opacity: 1;
}
.mod-card:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}
.mod-card-es {
    border: 2px solid #C9A96E;
    background: linear-gradient(135deg, #FFFAF5 0%, #FFF8F0 100%);
}
.mod-card-eb {
    border: 2px solid #D4CFC8;
    background: linear-gradient(135deg, #F8F5F1 0%, #F3EFEB 100%);
    opacity: 0.7;
}
.mod-card-eb.active {
    border-color: #C9A96E;
    background: linear-gradient(135deg, #FFFAF5 0%, #FFF8F0 100%);
    box-shadow: 0 4px 16px rgba(201,169,110,0.25);
    opacity: 1;
}
.mod-card-es.active {
    opacity: 1;
    box-shadow: 0 4px 16px rgba(201,169,110,0.25);
}
.mod-card-py {
    border: 2px solid #D4CFC8;
    background: linear-gradient(135deg, #F8F5F1 0%, #F3EFEB 100%);
    opacity: 0.7;
}
.mod-card-py.active {
    border-color: #C9A96E;
    background: linear-gradient(135deg, #FFFAF5 0%, #FFF8F0 100%);
    box-shadow: 0 4px 16px rgba(201,169,110,0.25);
    opacity: 1;
}
.mod-icon {
    width: 52px;
    height: 52px;
    margin: 0 auto 10px auto;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #F8F5FF 0%, #F0FAF8 100%);
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}
.mod-icon svg {
    width: 28px;
    height: 28px;
}
.mod-title { 
    font-size: 15px; 
    font-weight: 600; 
    color: #3D2E50; 
    margin-bottom: 3px; 
    font-family: 'Cormorant Garamond', serif;
    letter-spacing: 0.3px;
}
.mod-desc { 
    font-size: 11px; 
    color: #8A7F96; 
    line-height: 1.4;
    font-family: 'DM Sans', sans-serif;
}
.mod-badge {
    display: inline-block;
    background: linear-gradient(135deg, #C9A96E 0%, #D4B88C 100%);
    color: #FFFFFF;
    font-size: 9px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 12px;
    margin-top: 8px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    font-family: 'DM Sans', sans-serif;
}
.mod-badge.inactive {
    background: linear-gradient(135deg, #D4CFC8 0%, #C8C0B8 100%);
    color: #8A7F96;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.header("Sinastri Veri Girişi")

# ══════════════════════════════════════════════════════════════
# EŞ / SEVGİLİ MODU FORMU
# ══════════════════════════════════════════════════════════════
if st.session_state.sim_modu == "es_sevgili":
    p1_isim = st.sidebar.text_input("1. Partnerin İsmi (Opsiyonel)", placeholder="Örn: Ali").strip()
    p1_date = st.sidebar.date_input("1. Kisi Dogum Tarihi", value=datetime(1985, 4, 15).date(), min_value=min_tarih, max_value=max_tarih, format="DD/MM/YYYY")

    st.sidebar.divider()

    p2_isim = st.sidebar.text_input("2. Partnerin İsmi (Opsiyonel)", placeholder="Örn: Ayşe").strip()
    p2_date = st.sidebar.date_input("2. Kisi Dogum Tarihi", value=datetime(1990, 8, 22).date(), min_value=min_tarih, max_value=max_tarih, format="DD/MM/YYYY")

    st.sidebar.divider()

    event_date = st.sidebar.date_input("Tanışma / Evlilik Tarihi", value=datetime(2020, 1, 1).date(), min_value=min_tarih, max_value=max_tarih, format="DD/MM/YYYY")

    if "saat_format" not in st.session_state:
        st.session_state.saat_format = "12:00"

    _saat_girdisi = st.sidebar.text_input("Tanışma / Evlilik Saati", value=st.session_state.saat_format, key="saat_input", placeholder="12:00 veya 1430")

    _girdi_temiz = _saat_girdisi.strip().replace(":", "")
    if _girdi_temiz.isdigit():
        _hane = len(_girdi_temiz)
        if _hane == 1:
            _saat, _dakika = int(_girdi_temiz), 0
        elif _hane == 2:
            _saat, _dakika = int(_girdi_temiz), 0
        elif _hane == 3:
            _saat, _dakika = int(_girdi_temiz[:1]), int(_girdi_temiz[1:])
        elif _hane == 4:
            _saat, _dakika = int(_girdi_temiz[:2]), int(_girdi_temiz[2:])
        else:
            _saat, _dakika = 12, 0

        if 0 <= _saat <= 23 and 0 <= _dakika <= 59:
            event_time = f"{_saat:02d}:{_dakika:02d}"
            st.session_state.saat_format = event_time
        else:
            st.sidebar.warning("Geçersiz saat. 0-23 arası saat, 0-59 arası dakika girin.")
            event_time = "12:00"
    else:
        if _girdi_temiz:
            st.sidebar.warning("Sadece rakam girin (örn: 1430 veya 9:15)")
        event_time = "12:00"

    ebeveyn_rolu = "anne"

# ══════════════════════════════════════════════════════════════
# EBEVEYN / ÇOCUK MODU FORMU
# ══════════════════════════════════════════════════════════════
elif st.session_state.sim_modu == "ebeveyn_cocuk":
    st.sidebar.info("👨‍👧 Ebeveyn-Çocuk Kadersel Bağ Analizi")

    ebeveyn_isim = st.sidebar.text_input("Ebeveynin İsmi (Opsiyonel)", placeholder="Örn: Mehmet").strip()
    ebeveyn_date = st.sidebar.date_input("Ebeveyn Doğum Tarihi", value=datetime(1980, 3, 15).date(), min_value=min_tarih, max_value=max_tarih, format="DD/MM/YYYY")
    ebeveyn_rolu = st.sidebar.selectbox("Ebeveyn Rolü:", ["anne", "baba"], format_func=lambda x: "👩 Anne" if x == "anne" else "👨 Baba")

    st.sidebar.divider()

    cocuk_isim = st.sidebar.text_input("Çocuğun İsmi (Opsiyonel)", placeholder="Örn: Elif").strip()
    cocuk_date = st.sidebar.date_input("Çocuk Doğum Tarihi", value=datetime(2010, 6, 15).date(), min_value=min_tarih, max_value=max_tarih, format="DD/MM/YYYY")

    if "saat_format" not in st.session_state:
        st.session_state.saat_format = "12:00"

    _saat_girdisi = st.sidebar.text_input("Çocuk Doğum Saati", value=st.session_state.saat_format, key="saat_input", placeholder="12:00 veya 1430")

    _girdi_temiz = _saat_girdisi.strip().replace(":", "")
    if _girdi_temiz.isdigit():
        _hane = len(_girdi_temiz)
        if _hane == 1:
            _saat, _dakika = int(_girdi_temiz), 0
        elif _hane == 2:
            _saat, _dakika = int(_girdi_temiz), 0
        elif _hane == 3:
            _saat, _dakika = int(_girdi_temiz[:1]), int(_girdi_temiz[1:])
        elif _hane == 4:
            _saat, _dakika = int(_girdi_temiz[:2]), int(_girdi_temiz[2:])
        else:
            _saat, _dakika = 12, 0

        if 0 <= _saat <= 23 and 0 <= _dakika <= 59:
            event_time = f"{_saat:02d}:{_dakika:02d}"
            st.session_state.saat_format = event_time
        else:
            st.sidebar.warning("Geçersiz saat. 0-23 arası saat, 0-59 arası dakika girin.")
            event_time = "12:00"
    else:
        if _girdi_temiz:
            st.sidebar.warning("Sadece rakam girin (örn: 1430 veya 9:15)")
        event_time = "12:00"

    st.sidebar.divider()
    st.sidebar.markdown("**📍 Çocuğun Doğum Yeri**")

    ulke_listesi = sorted(ULKE_SEHIR_DB.keys())
    secili_ulke = st.sidebar.selectbox("Ülke:", ulke_listesi, index=ulke_listesi.index("Türkiye"), key="eb_ulke")

    sehirler = ULKE_SEHIR_DB[secili_ulke]
    serbest_sehir = ""

    if sehirler:
        secili_sehir = st.sidebar.selectbox("Şehir:", sehirler, key="eb_sehir")
        geo_sonuc = sehir_bul(f"{secili_sehir}, {secili_ulke}")
    else:
        serbest_sehir = st.sidebar.text_input("Şehir adı yazın:", placeholder="Örn: Bali, Muscat, Havana...", key="eb_serbest")
        secili_sehir = serbest_sehir
        geo_sonuc = sehir_bul(f"{serbest_sehir}, {secili_ulke}") if serbest_sehir else None

    if geo_sonuc:
        city = geo_sonuc["sehir"]
        country = geo_sonuc["ulke"] or secili_ulke
        lat = geo_sonuc["lat"]
        lon = geo_sonuc["lon"]
        st.sidebar.success(f" {city}, {country}")
        _auto_uo = otomatik_utc_offset(lat, lon, cocuk_date.year, cocuk_date.month, cocuk_date.day, int(event_time.split(":")[0]))
        st.sidebar.caption(f"Enlem: {lat:.4f} | Boylam: {lon:.4f} | UTC+{_auto_uo:g}")
    else:
        city = secili_sehir if secili_sehir else "Ankara"
        country = secili_ulke
        lat, lon = 39.9334, 32.8597
        if secili_ulke == "Diğer (Serbest Arama)" and serbest_sehir:
            st.sidebar.error("Şehir bulunamadı. Farklı bir isim deneyin.")
        elif not sehirler and not serbest_sehir:
            st.sidebar.warning("Lütfen bir şehir adı girin.")

# ══════════════════════════════════════════════════════════════
# POTANSİYEL & YETENEK MODU FORMU (Tek Kişi)
# ══════════════════════════════════════════════════════════════
elif st.session_state.sim_modu == "potansiyel_yetenek":
    st.sidebar.info("🔮 Potansiyel & Yetenek — Tek Kişi Natal Analizi")

    py_isim = st.sidebar.text_input("Kişinin İsmi (Opsiyonel)", placeholder="Örn: Ahmet").strip()
    py_date = st.sidebar.date_input("Doğum Tarihi", value=datetime(1990, 1, 1).date(), min_value=min_tarih, max_value=max_tarih, format="DD/MM/YYYY", key="py_tarih")

    if "saat_format" not in st.session_state:
        st.session_state.saat_format = "12:00"

    _saat_girdisi = st.sidebar.text_input("Doğum Saati", value=st.session_state.saat_format, key="saat_input", placeholder="12:00 veya 1430")

    _girdi_temiz = _saat_girdisi.strip().replace(":", "")
    if _girdi_temiz.isdigit():
        _hane = len(_girdi_temiz)
        if _hane == 1:
            _saat, _dakika = int(_girdi_temiz), 0
        elif _hane == 2:
            _saat, _dakika = int(_girdi_temiz), 0
        elif _hane == 3:
            _saat, _dakika = int(_girdi_temiz[:1]), int(_girdi_temiz[1:])
        elif _hane == 4:
            _saat, _dakika = int(_girdi_temiz[:2]), int(_girdi_temiz[2:])
        else:
            _saat, _dakika = 12, 0

        if 0 <= _saat <= 23 and 0 <= _dakika <= 59:
            event_time = f"{_saat:02d}:{_dakika:02d}"
            st.session_state.saat_format = event_time
        else:
            st.sidebar.warning("Geçersiz saat. 0-23 arası saat, 0-59 arası dakika girin.")
            event_time = "12:00"
    else:
        if _girdi_temiz:
            st.sidebar.warning("Sadece rakam girin (örn: 1430 veya 9:15)")
        event_time = "12:00"

    st.sidebar.divider()
    st.sidebar.markdown("**📍 Doğum Yeri**")

    ulke_listesi = sorted(ULKE_SEHIR_DB.keys())
    secili_ulke = st.sidebar.selectbox("Ülke:", ulke_listesi, index=ulke_listesi.index("Türkiye"), key="py_ulke")

    sehirler = ULKE_SEHIR_DB[secili_ulke]
    serbest_sehir = ""

    if sehirler:
        secili_sehir = st.sidebar.selectbox("Şehir:", sehirler, key="py_sehir")
        geo_sonuc = sehir_bul(f"{secili_sehir}, {secili_ulke}")
    else:
        serbest_sehir = st.sidebar.text_input("Şehir adı yazın:", placeholder="Örn: Bali, Muscat, Havana...", key="py_serbest")
        secili_sehir = serbest_sehir
        geo_sonuc = sehir_bul(f"{serbest_sehir}, {secili_ulke}") if serbest_sehir else None

    if geo_sonuc:
        city = geo_sonuc["sehir"]
        country = geo_sonuc["ulke"] or secili_ulke
        lat = geo_sonuc["lat"]
        lon = geo_sonuc["lon"]
        st.sidebar.success(f" {city}, {country}")
        _auto_uo = otomatik_utc_offset(lat, lon, py_date.year, py_date.month, py_date.day, int(event_time.split(":")[0]))
        st.sidebar.caption(f"Enlem: {lat:.4f} | Boylam: {lon:.4f} | UTC+{_auto_uo:g}")
    else:
        city = secili_sehir if secili_sehir else "Ankara"
        country = secili_ulke
        lat, lon = 39.9334, 32.8597
        if secili_ulke == "Diğer (Serbest Arama)" and serbest_sehir:
            st.sidebar.error("Şehir bulunamadı. Farklı bir isim deneyin.")
        elif not sehirler and not serbest_sehir:
            st.sidebar.warning("Lütfen bir şehir adı girin.")

# ══════════════════════════════════════════════════════════════
# ORTAK LOKASYON + BUTON (Eş/Sevgili modu için lokasyon aşağıda)
# ══════════════════════════════════════════════════════════════
if st.session_state.sim_modu == "es_sevgili":
    st.sidebar.divider()
    st.sidebar.markdown("**Lokasyon Çapası**")
    st.sidebar.caption("Önce ülkeyi, sonra şehri seçin.")

    ulke_listesi = sorted(ULKE_SEHIR_DB.keys())
    secili_ulke = st.sidebar.selectbox("Ülke:", ulke_listesi, index=ulke_listesi.index("Türkiye"))

    sehirler = ULKE_SEHIR_DB[secili_ulke]
    serbest_sehir = ""

    if sehirler:
        secili_sehir = st.sidebar.selectbox("Şehir:", sehirler)
        geo_sonuc = sehir_bul(f"{secili_sehir}, {secili_ulke}")
    else:
        serbest_sehir = st.sidebar.text_input("Şehir adı yazın:", placeholder="Örn: Bali, Muscat, Havana...")
        secili_sehir = serbest_sehir
        geo_sonuc = sehir_bul(f"{serbest_sehir}, {secili_ulke}") if serbest_sehir else None

    if geo_sonuc:
        city = geo_sonuc["sehir"]
        country = geo_sonuc["ulke"] or secili_ulke
        lat = geo_sonuc["lat"]
        lon = geo_sonuc["lon"]
        st.sidebar.success(f" {city}, {country}")
        _auto_uo_es = otomatik_utc_offset(lat, lon, event_date.year, event_date.month, event_date.day, int(event_time.split(":")[0]))
        st.sidebar.caption(f"Enlem: {lat:.4f} | Boylam: {lon:.4f} | UTC+{_auto_uo_es:g}")
    else:
        city = secili_sehir if secili_sehir else "Ankara"
        country = secili_ulke
        lat, lon = 39.9334, 32.8597
        if secili_ulke == "Diğer (Serbest Arama)" and serbest_sehir:
            st.sidebar.error("Şehir bulunamadı. Farklı bir isim deneyin.")
        elif not sehirler and not serbest_sehir:
            st.sidebar.warning("Lütfen bir şehir adı girin.")

    # Eş/sevgili modunda ebeveyn değişkenlerini ata
    ebeveyn_isim = p1_isim
    ebeveyn_date = p1_date
    cocuk_isim = p2_isim
    cocuk_date = p2_date

# ══════════════════════════════════════════════════════════════
# ANA TETİKLEME BUTONU
# ══════════════════════════════════════════════════════════════
st.sidebar.divider()
if st.session_state.sim_modu == "es_sevgili":
    buton_metni = "🚀 Çift Taraflı Kontratı Ateşle"
elif st.session_state.sim_modu == "ebeveyn_cocuk":
    rol_yazi = "Anne" if ebeveyn_rolu == "anne" else "Baba"
    buton_metni = f"🚀 Ebeveyn-Çocuk ({rol_yazi}) Kontratını Ateşle"
else:
    buton_metni = "✨ Potansiyel ve Yetenek Analizini Başlat"

if st.sidebar.button(buton_metni, key="btn_ana_atesleme", use_container_width=True):
    st.session_state.analiz_ateslendi = True


# --- ANA EKRAN (SONUÇLAR) ---
col_result, _ = st.columns([2, 0.1])

with col_result:
    if st.session_state.analiz_ateslendi: 
        if st.session_state.sim_modu == "es_sevgili":
            st.subheader("2. Canlı Analiz ve Çift Yönlü Hasat Çıktısı")
        elif st.session_state.sim_modu == "ebeveyn_cocuk":
            rol_yazi = "Anne" if ebeveyn_rolu == "anne" else "Baba"
            st.subheader(f"2. Canlı Analiz — Ebeveyn ({rol_yazi}) & Çocuk Bağ Çıktısı")
        else:
            st.subheader("2. Potansiyel ve Yetenek Analizi")
        with st.spinner('Meridyen kilitleri açılıyor, Situa A ve Situa B haritaları çiziliyor...'):
            
            # MOTOR ATEŞLENİYOR
            if st.session_state.sim_modu == "es_sevgili":
                _uo = otomatik_utc_offset(lat, lon, event_date.year, event_date.month, event_date.day, int(event_time.split(":")[0]))
                motor = _motor_olustur(
                    p1=p1_date.strftime("%Y-%m-%d"), 
                    p2=p2_date.strftime("%Y-%m-%d"), 
                    event_date=event_date.strftime("%Y-%m-%d"), 
                    event_time=event_time, 
                    city=city, country=country, lat=lat, lon=lon,
                    p1_isim=p1_isim, p2_isim=p2_isim, mod="es_sevgili",
                    ebeveyn_rolu="anne", _uo=_uo
                )
            elif st.session_state.sim_modu == "ebeveyn_cocuk":
                _uo = otomatik_utc_offset(lat, lon, cocuk_date.year, cocuk_date.month, cocuk_date.day, int(event_time.split(":")[0]))
                motor = _motor_olustur(
                    p1=cocuk_date.strftime("%Y-%m-%d"),
                    p2=ebeveyn_date.strftime("%Y-%m-%d"),
                    event_date=cocuk_date.strftime("%Y-%m-%d"),
                    event_time=event_time,
                    city=city, country=country, lat=lat, lon=lon,
                    p1_isim=cocuk_isim, p2_isim=ebeveyn_isim,
                    mod="ebeveyn_cocuk", ebeveyn_rolu=ebeveyn_rolu, _uo=_uo
                )
            elif st.session_state.sim_modu == "potansiyel_yetenek":
                _uo = otomatik_utc_offset(lat, lon, py_date.year, py_date.month, py_date.day, int(event_time.split(":")[0]))
                motor = _motor_olustur(
                    p1=py_date.strftime("%Y-%m-%d"),
                    p2=py_date.strftime("%Y-%m-%d"),
                    event_date=py_date.strftime("%Y-%m-%d"),
                    event_time=event_time,
                    city=city, country=country, lat=lat, lon=lon,
                    p1_isim=py_isim or "Kişi", p2_isim=py_isim or "Kişi",
                    mod="potansiyel_yetenek", ebeveyn_rolu="anne", _uo=_uo
                )
            
            if st.session_state.sim_modu == "es_sevgili":
                st.success(f"✨ Kadersel çapalama {motor.p1_isim} ve {motor.p2_isim} için mühürlendi!")
            elif st.session_state.sim_modu == "ebeveyn_cocuk":
                st.success(f"✨ Ebeveyn-Çocuk kadersel bağı {motor.p2_isim} ve {motor.p1_isim} için mühürlendi!")
            else:
                st.success(f"✨ {motor.p1_isim} için potansiyel ve yetenek analizi hazır!")
            st.info(f"📍 Sistem Koordinatları Kilitledi: {city}, {country} (Enlem {lat:.4f}, Boylam {lon:.4f})")

            if motor.mod == "potansiyel_yetenek":
                # ══════════════════════════════════════════════════════════════
                # POTANSİYEL & YETENEK MODU — TEK KİŞİ ANALİZİ
                # ══════════════════════════════════════════════════════════════

                # --- 1. NATAL HARİTA ---
                st.markdown("### 🌟 Natal Harita")
                st.markdown(f"<p style='color:#8A7F96; font-size:13px;'>{motor.p1_isim} kişisinin doğum anındaki gökyüzü haritası. Tüm gezegen sembolleri ve açıları gösterilmektedir.</p>", unsafe_allow_html=True)

                if os.path.exists(f"{motor._session_id}_Situa_A.png"):
                    st.image(f"{motor._session_id}_Situa_A.png", caption=f"{motor.p1_isim} Natal Haritası", use_container_width=True)
                st.divider()

                # --- 2. GEZEGEN POZİSYONLARI ---
                st.markdown("### 🪐 Gezegen Pozisyonları")
                st.markdown("<p style='color:#8A7F96; font-size:13px;'>Doğum anındaki tüm gezegen, asteroid ve kadersel noktaların burç, derece ve ev konumları.</p>", unsafe_allow_html=True)
                try:
                    gp = motor.gezegen_konum_analizi()
                    if gp:
                        burc_sembolleri = {
                            "Koç": "♈", "Boğa": "♉", "İkizler": "♊", "Yengeç": "♋",
                            "Aslan": "♌", "Başak": "♍", "Terazi": "♎", "Akrep": "♏",
                            "Yay": "♐", "Oğlak": "♑", "Kova": "♒", "Balık": "♓"
                        }
                        gezegen_sembolleri = {
                            "Güneş": "☉", "Ay": "☽", "Merkür": "☿", "Venüs": "♀",
                            "Mars": "♂", "Jüpiter": "♃", "Satürn": "♄", "Uranüs": "♅",
                            "Neptün": "♆", "Plüton": "♇", "KAD": "☊", "GAD": "☋", "Chiron": "⚷"
                        }
                        html_tablo = """<div style='background:#FBF7F4; border-radius:12px; padding:12px; border:1px solid #E8E0D8;'>
                        <table style='width:100%; border-collapse:collapse; font-family:DM Sans, sans-serif; font-size:13px;'>
                        <tr style='border-bottom:2px solid #C9A96E;'>
                            <th style='text-align:left; padding:6px 8px; color:#3D2E50;'>Gezegen</th>
                            <th style='text-align:left; padding:6px 8px; color:#3D2E50;'>Konum</th>
                            <th style='text-align:center; padding:6px 8px; color:#3D2E50;'>Ev</th>
                        </tr>"""
                        sirali_gezegenler = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter", "Satürn",
                                             "Uranüs", "Neptün", "Plüton", "KAD", "Chiron"]
                        for g in sirali_gezegenler:
                            if g not in gp:
                                continue
                            bilgi = gp[g]
                            g_sembol = gezegen_sembolleri.get(g, "•")
                            b_sembol = burc_sembolleri.get(bilgi['burc'], "")
                            renk = "#C9A96E" if g in ["Güneş", "Jüpiter"] else "#6B5B7B"
                            html_tablo += f"""
                        <tr style='border-bottom:1px solid #E8E0D8;'>
                            <td style='padding:5px 8px; color:{renk}; font-weight:bold;'>{g_sembol} {g}</td>
                            <td style='padding:5px 8px; color:#4A4A4A;'>{b_sembol} {bilgi['burc']} {bilgi['derece']}°{bilgi['dakika']:02d}'</td>
                            <td style='padding:5px 8px; text-align:center; color:#8A7F96;'>{bilgi['ev']}. Ev</td>
                        </tr>"""
                        html_tablo += "</table></div>"
                        st.markdown(html_tablo, unsafe_allow_html=True)
                    else:
                        st.info("Gezegen pozisyonları hesaplanamadı.")
                except Exception as e:
                    st.error(f"Gezegen pozisyonları hesaplanırken hata: {e}")
                st.divider()

                # --- 3. POTANSİYEL VE YETENEK ALANLARI ---
                st.markdown("### 💡 Potansiyel ve Yetenek Alanları")
                st.markdown("<p style='color:#8A7F96; font-size:13px;'>Haritanızdaki gezegen açılarından tespit edilen doğal yetenek ve potansiyel alanları.</p>", unsafe_allow_html=True)
                st.caption("Tarayıcıda sadece ilk 3 yetenek alanı gösterilmektedir. Tüm alanlar PDF raporundadır.")

                try:
                    potansiyel_sonuclari = motor.potansiyel_hesapla()
                    if potansiyel_sonuclari:
                        gorulen_alanlar = set()
                        alan_sayaci = 0
                        for satir in potansiyel_sonuclari:
                            if satir['alan'] not in gorulen_alanlar:
                                gorulen_alanlar.add(satir['alan'])
                                alan_sayaci += 1
                                if alan_sayaci > 3:
                                    continue
                                with st.expander(f"✨ {satir['alan']} ({satir['aci']} — {satir['aci_turu']} Açısı)"):
                                    st.markdown(satir['metin'])
                        st.caption("Tüm potansiyel ve yetenek alanları PDF raporunuzda detaylı şekilde yer almaktadır.")
                    else:
                        st.info("Belirgin bir potansiyel alanı tespit edilemedi.")
                except Exception as e:
                    st.error(f"Potansiyel analizinde hata: {str(e)}")
                st.divider()

                # --- 4. MESLEK YÖNLENDİRME ÖNERİLERİ ---
                st.markdown("### 🎯 Meslek Yönlendirme Önerileri")
                st.markdown("<p style='color:#8A7F96; font-size:13px;'>Potansiyel ve yetenek alanlarının senteziyle belirlenen, yatkın olduğunuz meslek dalları.</p>", unsafe_allow_html=True)
                st.caption("Tarayıcıda sadece 5., 6. ve 7. sıralar gösterilmektedir. Tam sıralama PDF raporundadır.")

                try:
                    konumlar = motor.gezegen_konum_analizi()
                    meslek_onerileri = motor.meslek_onerileri()
                    if meslek_onerileri:
                        sirali = sorted(meslek_onerileri, key=lambda x: x['puan'], reverse=True)
                        st.markdown("**Potansiyel Alanları Sıralaması:**")
                        for j, r in enumerate(sirali[4:7]):
                            st.markdown(f"**{j+5}. {r['alan']}** — {r['puan']:.1f} puan (%{r['yuzde']})")
                        st.markdown("")
                        st.caption("Puanlama: Gezegen-burç eşleşmesi, açı türü, orb yakınlığı, efsane boost, MC bonusu ve asteroid desteği ile hesaplanmıştır.")
                        st.caption("Detaylı açıklama için PDF raporunuzu inceleyin.")
                    else:
                        st.info("Meslek yönlendirme için yeterli potansiyel alanı tespit edilemedi.")
                except Exception as e:
                    st.error(f"Meslek yönlendirme analizinde hata: {str(e)}")
                st.divider()

                # --- 5. POTANSİYEL & YETENEK PDF ---
                st.markdown("### 📄 FAST — Potansiyel & Yetenek Raporu")
                if "pdf_py_hazir" not in st.session_state:
                    st.session_state.pdf_py_hazir = False

                if st.button("⚙️ Potansiyel & Yetenek PDF Raporunu Hazırla", key="btn_pdf_py_hazirla", use_container_width=True):
                    with st.spinner("Potansiyel ve yetenek analizi PDF'e işleniyor..."):
                        rapor_adi = f"{motor._session_id}_Potansiyel_Yetenek.pdf"
                        motor.pdf_potansiyel_rapor_uret(rapor_adi)
                        st.session_state.pdf_py_hazir = True
                        st.success("PDF raporu hazır!")

                if st.session_state.pdf_py_hazir:
                    rapor_adi = f"{motor._session_id}_Potansiyel_Yetenek.pdf"
                    if os.path.exists(rapor_adi):
                        with open(rapor_adi, "rb") as pdf_file:
                            dl_c1, dl_c2, dl_c3 = st.columns([1,2,1])
                            with dl_c2:
                                st.download_button(
                                    label="📥 Potansiyel & Yetenek PDF İndir",
                                    data=pdf_file,
                                    file_name=f"FAST_{motor.p1_isim}_Potansiyel_Yetenek.pdf",
                                    mime="application/pdf",
                                    key="btn_pdf_py_indir",
                                    use_container_width=True,
                                    type="primary"
                                )

            else:
                # ══════════════════════════════════════════════════════════════
                # EŞ/SEVGİLİ + EBEVEYN/ÇOCUK MODLARI İÇİN MEVCUT AKIŞ
                # ══════════════════════════════════════════════════════════════
                st.markdown("### 🎯 Nokta Atışı Ev Aktarımları (Karmik Yaşam Alanları)")
                rapor_A_ui, rapor_B_ui = motor.karmik_ev_aktarimlari(pdf_icin=False)
            
                if motor.mod == "ebeveyn_cocuk":
                    col_ev1, col_ev2 = st.columns(2)
                    with col_ev1:
                        st.markdown(f"**{motor.p1_isim} Dünyası (İleri Vektör)**")
                        if rapor_A_ui:
                            for html in rapor_A_ui: st.markdown(html, unsafe_allow_html=True)
                        else: st.info("Bu vektörde majör bir kadersel ev mühürlenmesi tespit edilmedi.")
                    with col_ev2:
                        st.markdown(f"**{motor.p2_isim} Dünyası (Geri Vektör)**")
                        if rapor_B_ui:
                            for html in rapor_B_ui: st.markdown(html, unsafe_allow_html=True)
                        else: st.info("Bu vektörde majör bir kadersel ev mühürlenmesi tespit edilmedi.")
                st.divider()
            
                st.markdown("### ⏳ Bağıl İklim (Şu An Ne Yaşıyorsunuz?)")
                bsp_html = motor.kadersel_bsp_iklimi()
                st.markdown(bsp_html, unsafe_allow_html=True)

                # --- SECONDARY PROGRESSION (Sadece es_sevgili) ---
                if motor.mod == "es_sevgili":
                    st.markdown("### 🔮 Secondary Progression — İlişki Öngörüsü")
                    st.markdown("<p style='color:#8A7F96; font-size:13px;'>İkincil İlerleme: 1 Gün = 1 Yıl | İlişkinizin duygusal evrim haritası ve uzun vadeli tahminleri.</p>", unsafe_allow_html=True)

                    try:
                        sp_yorumlar = motor.secondary_progression_yorumla()
                        if sp_yorumlar:
                            for yorum in sp_yorumlar:
                                if yorum.get("karsilastirma"):
                                    st.markdown(f"<div style='background-color:#F8F5FF; padding:12px; border-left:4px solid #B8A9C9; border-radius:5px; margin-top:10px;'>"
                                                f"<b style='color:#8B7BB5;'>🔮 İlişki Uyumu:</b> "
                                                f"<span style='color:#4A4A4A;'>{yorum['genel_yorum']}</span></div>",
                                                unsafe_allow_html=True)
                                else:
                                    with st.expander(f"👤 {yorum['kisi']} — {yorum['ilerleme_yili']} Yıl İlerleme | Ay: {yorum['ay_burcu']} | Güneş: {yorum['gunes_burcu']}"):
                                        st.markdown(f"**{yorum['genel_yorum']}")
                                        for aci_y in yorum.get("ay_aci_yorumlari", []):
                                            renk = "#D4878F" if aci_y["aci_turu"] in ["Kare", "Karşıt"] else "#8FB8CA"
                                            donem_etiketi = f"<br/><span style='color:#C9A96E; font-size:12px;'>⏳ {aci_y['donem']}</span>" if aci_y.get("donem") else ""
                                            st.markdown(f"<span style='color:{renk}; font-weight:bold;'>• {aci_y['baslik']}</span>{donem_etiketi}<br/>{aci_y['yorum']}", unsafe_allow_html=True)
                                        st.caption(f"Toplam {yorum['toplam_aci']} ilerletilmiş açı tespit edildi.")
                            st.caption("Detaylı analiz için PDF raporunuzu indirin.")
                        else:
                            st.info("Secondary Progression analizi hesaplanamadı.")
                    except Exception as e:
                        st.error(f"Secondary Progression analizinde hata: {str(e)}")

                    st.divider()

                st.markdown("#### 📅 Önümüzdeki 3 Günün Kadersel Hava Durumu")
                st.caption("Tarayıcıda sadece 3 günlük önizleme gösterilmektedir. 6 aylık kapsamlı günlük akış analizi için PDF raporunu indirin.")
                gunluk_alarmlar = motor.gunluk_bsp_taramasi(gun_sayisi=30)
                if gunluk_alarmlar:
                    for alarm in gunluk_alarmlar[:3]:
                        st.markdown(f"<div style='background-color:#FFFFFF; padding:10px; border-left:3px solid #C9A96E; margin-bottom:5px; border-radius:3px;'>"
                                    f"<b style='color:#8FB8CA;'>🗓️ {alarm['tarih']}</b><br>"
                                    f"<span style='color:#4A4A4A; font-size:14px;'>{'<br>'.join(alarm['mesajlar'])}</span></div>", 
                                    unsafe_allow_html=True)
                else:
                    st.info("Önümüzdeki 3 gün boyunca ilerletilmiş Ay, majör bir kadersel tetikleme yapmıyor. Stabil bir akıştasınız.")
                st.divider()

                st.markdown("### 🔮 Kadersel Zaman Makinesi (21 Yıllık)")
                st.caption("Tarayıcıda sadece ilk 3 kavşak gösterilmektedir. 7 kavşağın tamamı PDF raporundadır.")
                for kavsak in motor.calculate_gelecek_navigasyonu(pdf_icin=False)[:3]:
                    st.markdown(kavsak, unsafe_allow_html=True)

                col_map1, col_map2 = st.columns(2)
                with col_map1:
                    if os.path.exists(f"{motor._session_id}_Situa_A.png"): st.image(f"{motor._session_id}_Situa_A.png", caption=f"{motor.p1_isim} Haritası", use_container_width=True)
                with col_map2:
                    if os.path.exists(f"{motor._session_id}_Situa_B.png"): st.image(f"{motor._session_id}_Situa_B.png", caption=f"SİTUA B: {motor.p2_isim} Vektörü", use_container_width=True)

                st.divider()

                # =========================================================================
                # 🌍 ASTROCARTOGRAPHY + GLOBAL KADER PUSULASI (BİRLEŞİK)
                # =========================================================================
                st.markdown("### 🌍 Astrocartography & Global Kader Pusulası")
                st.markdown("<p style='color:#6B5B7B; font-size:13px;'>Doğum haritanızdaki gezegenlerin dünya üzerinde nerede doruk noktaya ulaştığını gösteren interaktif harita ve 100+ şehirdeki kadersel uyum taraması.</p>", unsafe_allow_html=True)

                col_acg, col_radar = st.columns([3, 2])

                with col_acg:
                    try:
                        acg_fig, _ = motor.ciz_astrocartography(dosya_adi="FBST_Astrocartography.png")
                        st.plotly_chart(acg_fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Astrocartography haritası oluşturulamadı: {e}")

                with col_radar:
                    st.markdown("#### 📡 Kader Pusulası Taraması")
                    st.markdown("<p style='color:#6B5B7B; font-size:12px;'>15.000+ şehirdeki astrokartografi haritasını tarayarak finansal güç, tutku, huzur ve kriz potansiyeli açısından en yüksek noktaları tespit eder.</p>", unsafe_allow_html=True)

                    if st.button("🚀 Dünyayı Tara ve Zirveleri Bul", key="btn_radar_tara", use_container_width=True):
                        with st.spinner("15.000+ şehirdeki astrokartografi haritaları taranıyor — bu birkaç dakika sürebilir..."):
                            if st.session_state.sim_modu == "ebeveyn_cocuk":
                                _radar_p1 = ebeveyn_date.strftime("%Y-%m-%d")
                                _radar_p2 = cocuk_date.strftime("%Y-%m-%d")
                                _radar_p1_isim = ebeveyn_isim
                                _radar_p2_isim = cocuk_isim
                                _radar_event = cocuk_date.strftime("%Y-%m-%d")
                            else:
                                _radar_p1 = p1_date.strftime("%Y-%m-%d")
                                _radar_p2 = p2_date.strftime("%Y-%m-%d")
                                _radar_p1_isim = p1_isim
                                _radar_p2_isim = p2_isim
                                _radar_event = event_date.strftime("%Y-%m-%d")
                            radar_sonuclari = kadersel_radar_analizi(
                                p1_str=_radar_p1,
                                p2_str=_radar_p2,
                                event_date_str=_radar_event,
                                event_time=event_time,
                                p1_isim=_radar_p1_isim,
                                p2_isim=_radar_p2_isim
                            )
                            st.session_state.radar_calistirildi = True
                            st.session_state['radar_top_para'] = sorted(radar_sonuclari, key=lambda x: x["para"], reverse=True)
                            st.session_state['radar_top_huzur'] = sorted(radar_sonuclari, key=lambda x: x["huzur"], reverse=True)
                            st.session_state['radar_top_tutku'] = sorted(radar_sonuclari, key=lambda x: x["tutku"], reverse=True)
                            st.session_state['radar_top_kriz'] = sorted(radar_sonuclari, key=lambda x: x["kriz"], reverse=True)
                            ulke_sayisi = len(sehir_veritabani_yukle())
                            st.success(f"Tarama tamamlandı! {ulke_sayisi} ülkeden {len(radar_sonuclari)} şehir analiz edildi.")

                    if st.session_state.get('radar_calistirildi'):
                        st.warning("🔒 1., 2., 3. ve 4. sıralar gizlidir. Sadece 5. ve 10. sıralar gösteriliyor. 1-10 arası tam listeyi PDF'den görüntüleyin.")
                        r_c1, r_c2 = st.columns(2)
                        with r_c1:
                            st.markdown("**💰 Para**")
                            for i, v in enumerate(st.session_state['radar_top_para'][4:5], start=5):
                                st.markdown(f"**{i}.** {v['sehir']} (%{v['para']})")
                                if v.get('etkiler'):
                                    for e in v['etkiler'][:1]:
                                        st.caption(f"  • {e}")
                            for i, v in enumerate(st.session_state['radar_top_para'][9:10], start=10):
                                st.markdown(f"**{i}.** {v['sehir']} (%{v['para']})")
                                if v.get('etkiler'):
                                    for e in v['etkiler'][:1]:
                                        st.caption(f"  • {e}")
                            st.markdown("**🔥 Tutku**")
                            for i, v in enumerate(st.session_state['radar_top_tutku'][4:5], start=5):
                                st.markdown(f"**{i}.** {v['sehir']} (%{v['tutku']})")
                                if v.get('etkiler'):
                                    for e in v['etkiler'][:1]:
                                        st.caption(f"  • {e}")
                            for i, v in enumerate(st.session_state['radar_top_tutku'][9:10], start=10):
                                st.markdown(f"**{i}.** {v['sehir']} (%{v['tutku']})")
                                if v.get('etkiler'):
                                    for e in v['etkiler'][:1]:
                                        st.caption(f"  • {e}")
                        with r_c2:
                            st.markdown("**🕊️ Huzur**")
                            for i, v in enumerate(st.session_state['radar_top_huzur'][4:5], start=5):
                                st.markdown(f"**{i}.** {v['sehir']} (%{v['huzur']})")
                                if v.get('etkiler'):
                                    for e in v['etkiler'][:1]:
                                        st.caption(f"  • {e}")
                            for i, v in enumerate(st.session_state['radar_top_huzur'][9:10], start=10):
                                st.markdown(f"**{i}.** {v['sehir']} (%{v['huzur']})")
                                if v.get('etkiler'):
                                    for e in v['etkiler'][:1]:
                                        st.caption(f"  • {e}")
                            st.markdown("**🌋 Kriz**")
                            for i, v in enumerate(st.session_state['radar_top_kriz'][4:5], start=5):
                                st.markdown(f"**{i}.** {v['sehir']} (%{v['kriz']})")
                                if v.get('etkiler'):
                                    for e in v['etkiler'][:1]:
                                        st.caption(f"  • {e}")
                            for i, v in enumerate(st.session_state['radar_top_kriz'][9:10], start=10):
                                st.markdown(f"**{i}.** {v['sehir']} (%{v['kriz']})")
                                if v.get('etkiler'):
                                    for e in v['etkiler'][:1]:
                                        st.caption(f"  • {e}")

                st.divider()

                st.divider()

                st.divider()

                st.divider()

                # =========================================================================
                # 🌍 ALTERNATİF EVREN (ASTROKARTOGRAFİ TABANLI)
                # =========================================================================
                st.markdown("### 🌍 Alternatif Evren (Astrokartografi Lokasyon Analizi)")
                st.markdown("<p style='color:#4A4A4A; font-size:14px;'>Bu analiz, seçtiğiniz şehirdeki gökyüzünde hangi gezegenlerin hangi açısal pozisyonda olduğunu (Yükselen, MC, Alçalan, IC) hesaplar. Astrokartografi, bir olay anında dünyanın farklı noktalarında gezegenlerin ev konumlarını haritalandıran bilimsel bir astroloji tekniğidir.</p>", unsafe_allow_html=True)

                alt_ulke_listesi = sorted(ULKE_SEHIR_DB.keys())
                alt_secili_ulke = st.selectbox("Ülke:", alt_ulke_listesi, key="alt_ulke_sec")

                alt_sehirler = ULKE_SEHIR_DB[alt_secili_ulke]

                if alt_sehirler:
                    alt_secili_sehir = st.selectbox("Şehir:", alt_sehirler, key="alt_sehir_sec")
                    alt_geo = sehir_bul(f"{alt_secili_sehir}, {alt_secili_ulke}")
                else:
                    alt_serbest_sehir = st.text_input("Şehir adı yazın:", key="alt_serbest_sehir", placeholder="Örn: Bali, Muscat, Havana...")
                    alt_secili_sehir = alt_serbest_sehir
                    alt_geo = sehir_bul(f"{alt_serbest_sehir}, {alt_secili_ulke}") if alt_serbest_sehir else None

                if alt_geo and st.button(f"🔍 {alt_geo['sehir']} İçin Astrokartografi Analizi Yap", key="btn_alternatif_evren", use_container_width=True):
                    alt_lat, alt_lon = alt_geo["lat"], alt_geo["lon"]
                    alt_city = alt_geo["sehir"]
                    alt_country = alt_geo["ulke"] or alt_secili_ulke

                    tarih = datetime.strptime(f"{event_date.strftime('%Y-%m-%d')} {event_time}", "%Y-%m-%d %H:%M")
                    jd_event = swe.julday(tarih.year, tarih.month, tarih.day, tarih.hour + tarih.minute / 60.0)

                    acg_sonuc = astro_kartografi_skor(jd_event, alt_lat, alt_lon)

                    st.markdown(f"#### 📊 {alt_city} ({alt_country}) Astrokartografi Raporu")
                    st.caption(f"Olay Tarihi: {event_date.strftime('%d.%m.%Y')} {event_time} | Enlem: {alt_lat:.4f} | Boylam: {alt_lon:.4f}")

                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    m_col1.metric("🕊️ Huzur & Mutluluk", f"%{int(acg_sonuc['huzur'])}")
                    m_col2.metric("💳 Finansal Güç", f"%{int(acg_sonuc['para'])}")
                    m_col3.metric("🔥 Tutku & Çekim", f"%{int(acg_sonuc['tutku'])}")
                    m_col4.metric("🌋 Kriz Potansiyeli", f"%{int(acg_sonuc['kriz'])}", delta_color="inverse")

                    if acg_sonuc['etkiler']:
                        st.markdown("##### 🔭 Bu Noktada Aktif olan Astrokartografi Hatları:")
                        for etki in acg_sonuc['etkiler']:
                            st.caption(f"• {etki}")

                    st.markdown("##### 📌 Gezegen Bazlı Yorum:")
                    en_guclu_gezegen = max(acg_sonuc['acg'].items(), key=lambda x: max(0, 5 - x[1]['aci_farki']))
                    g_adi, g_veri = en_guclu_gezegen
                    if g_veri['aci_farki'] < 5:
                        aci_isim = {"AC": "Yükselen (ASC)", "DC": "Alçalan (DSC)", "MC": "Gökyüzü Ortası (MC)", "IC": "Yeraltı (IC)"}
                        deger = GEZEGEN_ANLAMLARI.get(g_adi, {})
                        st.success(f"**{g_adi}** bu noktada **{aci_isim.get(g_veri['en_yakin_aci'], g_veri['en_yakin_aci'])}** hattı üzerinde (Orb: {g_veri['aci_farki']:.1f}°). {deger.get('parlaklik', '')}")

                    if acg_sonuc['para'] >= 75:
                        st.info("💰 **Finansal Potansiyel Yüksek:** Jüpiter veya Venüs bu noktada güçlü açılar yapıyor. Ortak finansal girişimler için destekleyici bir enerji alanı.")
                    if acg_sonuc['tutku'] >= 75:
                        st.warning("🔥 **Yüksek Tutku Alanı:** Mars veya Venüs bu koordinatta aktif. İlişkisel çekim ve enerji seviyesi yüksek.")
                    if acg_sonuc['huzur'] >= 75:
                        st.info("🕊️ **Duygusal Güvenlik Limanı:** Ay veya Venüs bu noktada huzurlu bir hatta. Duygusal bağ ve iç huzur için destekleyici.")
                    if acg_sonuc['kriz'] >= 60:
                        st.error("⚠️ **Satürn/Plüto Etkisi:** Bu noktada yapısal sınavlar ve derin dönüşüm enerjileri aktif. Sabır ve olgunluk gerektiren bir alan.")

                    if st.session_state.sim_modu == "ebeveyn_cocuk":
                        _uo_sim = otomatik_utc_offset(alt_lat, alt_lon, cocuk_date.year, cocuk_date.month, cocuk_date.day, int(event_time.split(":")[0]))
                        sim_motor = FBST_Engine(
                            p1=cocuk_date.strftime("%Y-%m-%d"),
                            p2=ebeveyn_date.strftime("%Y-%m-%d"),
                            event_date=cocuk_date.strftime("%Y-%m-%d"),
                            event_time=event_time,
                            city=alt_city, country=alt_country, lat=alt_lat, lon=alt_lon,
                            p1_isim=cocuk_isim, p2_isim=ebeveyn_isim,
                            mod="ebeveyn_cocuk", ebeveyn_rolu=ebeveyn_rolu,
                            utc_offset=_uo_sim
                        )
                    else:
                        _uo_sim = otomatik_utc_offset(alt_lat, alt_lon, event_date.year, event_date.month, event_date.day, int(event_time.split(":")[0]))
                        sim_motor = FBST_Engine(
                            p1=p1_date.strftime("%Y-%m-%d"),
                            p2=p2_date.strftime("%Y-%m-%d"),
                            event_date=event_date.strftime("%Y-%m-%d"),
                            event_time=event_time,
                            city=alt_city, country=alt_country, lat=alt_lat, lon=alt_lon,
                            p1_isim=p1_isim, p2_isim=p2_isim,
                            utc_offset=_uo_sim
                        )
                    j_ileri, j_geri = sim_motor.get_julian_dates()
                    yeni_asc_A = sim_motor.yukselen_bul(j_ileri)
                    yeni_asc_B = sim_motor.yukselen_bul(j_geri)

                    st.markdown("<br>##### 🔮 Bu Konumdaki Yükselen Değişimleri", unsafe_allow_html=True)
                    col_sim_res1, col_sim_res2 = st.columns(2)
                    with col_sim_res1:
                        _yukselen_soze = fbst_yukselenler_ebeveyn.get(yeni_asc_A, '') if sim_motor.mod == "ebeveyn_cocuk" else fbst_yukselenler.get(yeni_asc_A, '')
                        st.markdown(f"<div style='background-color:#F0FAF8; padding:15px; border-top:4px solid #8FB8CA; border-radius:5px;'>"
                                    f"<h4 style='color:#5A9BAD; margin-bottom:5px;'>{sim_motor.p1_isim} → {yeni_asc_A}</h4>"
                                    f"<p style='color:#4A4A4A; font-size:14px;'>{_yukselen_soze}</p>"
                                    f"</div>", unsafe_allow_html=True)
                    with col_sim_res2:
                        _yukselen_soze2 = fbst_yukselenler_ebeveyn.get(yeni_asc_B, '') if sim_motor.mod == "ebeveyn_cocuk" else fbst_yukselenler.get(yeni_asc_B, '')
                        st.markdown(f"<div style='background-color:#FFF0ED; padding:15px; border-top:4px solid #D4878F; border-radius:5px;'>"
                                    f"<h4 style='color:#C47A82; margin-bottom:5px;'>{sim_motor.p2_isim} → {yeni_asc_B}</h4>"
                                    f"<p style='color:#4A4A4A; font-size:14px;'>{_yukselen_soze2}</p>"
                                    f"</div>", unsafe_allow_html=True)

                st.divider()

                # =========================================================================
                # 🌟 YILDIZ MÜHÜRLERİ (SABİT YILDIZ TEMASLARI)
                # =========================================================================
                st.markdown("### 🌟 Kadersel Yıldız Mühürleri (Sabit Yıldız Temasları)")

                p1_jd = swe.julday(motor.p1.year, motor.p1.month, motor.p1.day, motor.p1.hour + motor.p1.minute / 60.0)
                p2_jd = swe.julday(motor.p2.year, motor.p2.month, motor.p2.day, motor.p2.hour + motor.p2.minute / 60.0)
                ekran_haritalari = [
                    {"isim": motor.p1_isim, "jd": p1_jd},
                    {"isim": motor.p2_isim, "jd": p2_jd}
                ]

                bulunan_ekran_muhurleri = False
                gosterilen_muhur = 0
                MAKS_EKRAN_MUHUR = 3

                for harita in ekran_haritalari:
                    for gezegen_adi, gezegen_id in GEZEGENLER.items():
                        if gosterilen_muhur >= MAKS_EKRAN_MUHUR:
                            break
                        try:
                            if gezegen_adi == "GAD":
                                k_derece = get_planetary_position(harita["jd"], swe.MEAN_NODE)
                                g_derecesi = (k_derece + 180.0) % 360.0
                            else:
                                g_derecesi = get_planetary_position(harita["jd"], gezegen_id)

                            sonuclar = kadersel_yildiz_taramasi(gezegen_adi, g_derecesi, orb_siniri=2.0)

                            if sonuclar:
                                bulunan_ekran_muhurleri = True
                                for sonuc in sonuclar:
                                    if gosterilen_muhur >= MAKS_EKRAN_MUHUR:
                                        break
                                    satirlar = sonuc.split('\n')
                                    baslik = satirlar[0].replace("Kavuşumu", f"Kavuşumu ({harita['isim']})").strip()
                                    icerik = "\n\n".join([s.replace("   👉 ", "• ").replace(" 👉 ", "• ").strip() for s in satirlar[1:] if s.strip()])
                                    with st.expander(f"{baslik}"):
                                        st.markdown(icerik)
                                    gosterilen_muhur += 1
                        except Exception:
                            continue
                    if gosterilen_muhur >= MAKS_EKRAN_MUHUR:
                        break

                if not bulunan_ekran_muhurleri:
                    st.info("Bu kadersel kontratta (2.0° orb sınırı içinde) aktif bir sabit yıldız mührü tespit edilemedi.")
                else:
                    st.warning("🌟 **Ekran sadece 3 sabit yıldız mührü için sınırlıdır** — Sadece ilk 3 mühür gösterilmektedir. **Tüm sabit yıldız tarama sonuçlarını** ve detaylı yorumlarını PDF raporunuzda bulabilirsiniz. PDF indirmek için sayfanın en altına kaydırın.")

                st.divider()

                st.divider()

                # =========================================================================
                # 📊 GELİŞİM DÖNEMLERİ (Sadece Ebeveyn-Çocuk)
                # =========================================================================
                if motor.mod == "ebeveyn_cocuk":
                    st.markdown("### 📊 Çocuğun Gelişim Dönemleri ve Ebeveyn Tutum Analizi")
                    st.markdown("<p style='color:#8A7F96; font-size:13px;'>Çocuğunuzun doğum tarihine göre aktif gelişim dönemleri ve bu dönemdeki ebeveyn-çocuk etkileşim yapıları.</p>", unsafe_allow_html=True)

                    try:
                        gelisim_sonuclari = motor.gelisim_donemleri_hesapla()
                        if gelisim_sonuclari:
                            for satir in gelisim_sonuclari:
                                with st.expander(f"🪐 {satir['gezegen']} — {satir['donem']}"):
                                    st.markdown(satir['metin'])
                            st.caption("Tüm gezegen gelişim dönemleri PDF raporunuzda detaylı şekilde yer almaktadır.")
                        else:
                            st.info("Gelişim dönemi verisi hesaplanamadı.")
                    except Exception as e:
                        st.error(f"Gelişim dönemi analizinde hata: {str(e)}")

                    st.divider()

                if motor.mod == "ebeveyn_cocuk":
                    # =========================================================================
                    # 3. POTANSİYEL VE YETENEK SİMÜLASYONU (Sadece Ebeveyn-Çocuk)
                    # =========================================================================
                    st.subheader("3. Potansiyel ve Yetenek Simülasyonu")
                    st.markdown("<p style='color:#8A7F96; font-size:13px;'>Haritanızdaki gezegen açılarından tespit edilen doğal yetenek, potansiyel alanları ve meslek yönlendirmeleri.</p>", unsafe_allow_html=True)

                    st.markdown("### 💡 Potansiyel ve Yetenek Alanları")
                    st.markdown("<p style='color:#8A7F96; font-size:13px;'>Doğal yetenek ve potansiyel alanları açısal analizle belirlenmiştir.</p>", unsafe_allow_html=True)
                    st.caption("Tarayıcıda sadece ilk 3 yetenek alanı gösterilmektedir. Tüm alanlar PDF raporundadır.")

                    try:
                        potansiyel_sonuclari = motor.potansiyel_hesapla()
                        if potansiyel_sonuclari:
                            gorulen_alanlar = set()
                            alan_sayaci = 0
                            for satir in potansiyel_sonuclari:
                                if satir['alan'] not in gorulen_alanlar:
                                    gorulen_alanlar.add(satir['alan'])
                                    alan_sayaci += 1
                                    if alan_sayaci > 3:
                                        continue
                                    with st.expander(f"✨ {satir['alan']} ({satir['aci']} — {satir['aci_turu']} Açısı)"):
                                        st.markdown(satir['metin'])
                            st.caption("Tüm potansiyel ve yetenek alanları PDF raporunuzda detaylı şekilde yer almaktadır.")
                        else:
                            st.info("Belirgin bir potansiyel alanı tespit edilemedi.")
                    except Exception as e:
                        st.error(f"Potansiyel analizinde hata: {str(e)}")

                    st.divider()

                    # --- MESLEK YÖNLENDİRME ÖNERİLERİ ---
                    st.markdown("### 🎯 Meslek Yönlendirme Önerileri")
                    if st.session_state.sim_modu == "ebeveyn_cocuk":
                        st.markdown("<p style='color:#8A7F96; font-size:13px;'>Çocuğun potansiyel ve yetenek alanlarının senteziyle belirlenen, yatkın olduğu meslek dalları.</p>", unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color:#8A7F96; font-size:13px;'>Potansiyel ve yetenek alanlarının senteziyle belirlenen, yatkın olduğunuz meslek dalları.</p>", unsafe_allow_html=True)
                    st.caption("Tarayıcıda sadece 5., 6. ve 7. sıralar gösterilmektedir. Tam sıralama PDF raporundadır.")

                    try:
                        konumlar = motor.gezegen_konum_analizi()
                        meslek_onerileri = motor.meslek_onerileri()
                        if meslek_onerileri:
                            sirali = sorted(meslek_onerileri, key=lambda x: x['puan'], reverse=True)
                            st.markdown("**Potansiyel Alanları Sıralaması:**")
                            for j, r in enumerate(sirali[4:7]):
                                st.markdown(f"**{j+5}. {r['alan']}** — {r['puan']:.1f} puan (%{r['yuzde']})")
                            st.markdown("")
                            st.caption("Puanlama: Gezegen-burç eşleşmesi, açı türü, orb yakınlığı, efsane boost, MC bonusu ve asteroid desteği ile hesaplanmıştır.")
                            st.caption("Detaylı açıklama için PDF raporunuzu inceleyin.")
                        else:
                            st.info("Meslek yönlendirme için yeterli potansiyel alanı tespit edilemedi.")
                    except Exception as e:
                        st.error(f"Meslek yönlendirme analizinde hata: {str(e)}")

                st.divider()

                # --- PDF ÜRETİMİ VE İNDİRME BUTONU ---
                st.divider()
                st.markdown("### 📄 Fatih Asartepe Sinastri Tekniği - FAST (Full PDF Raporu)")
            
                # PDF'in hazır olup olmadığını state'te tutuyoruz
                if "pdf_hazir" not in st.session_state:
                    st.session_state.pdf_hazir = False

                # 1. AŞAMA: PDF ÜRETİM TETİKLEYİCİSİ
                if st.button("⚙️ Çift Taraflı PDF Raporunu Hazırla (Matbaayı Çalıştır)", key="btn_pdf_hazirla", use_container_width=True):
                    with st.spinner("Kadersel mühürler altın sularla PDF'e işleniyor, lütfen bekleyin..."):
                        rapor_adi = f"{motor._session_id}_Cift_Tarafli_Kontrat.pdf"
                        motor.pdf_rapor_uret(rapor_adi)
                        st.session_state.pdf_hazir = True
                        st.success("PDF Raporu başarıyla mühürlendi! Aşağıdaki butondan indirebilirsiniz.")

                # 2. AŞAMA: İNDİRME BUTONU (Sadece PDF hazırsa görünür)
                if st.session_state.pdf_hazir:
                    rapor_adi = f"{motor._session_id}_Cift_Tarafli_Kontrat.pdf"
                    if os.path.exists(rapor_adi):
                        with open(rapor_adi, "rb") as pdf_file:
                            dl_col1, dl_col2, dl_col3 = st.columns([1,2,1])
                            with dl_col2:
                                st.download_button(
                                    label="📥 Hazırlanan PDF Raporunu İndir", 
                                    data=pdf_file, 
                                    file_name=f"FBST_{city}_Kontrati.pdf", 
                                    mime="application/pdf", 
                                    key="btn_pdf_indir_son",
                                    use_container_width=True,
                                    type="primary" # Butonu belirgin (kırmızı/ana renk) yapar
                                )

    else:
        st.info("👈 Sol panelden isim, tarih, saat ve lokasyon bilgilerini girdikten sonra 'Çift Taraflı Kontratı Ateşle' butonuna basın.")
