"""
Horary Oracle FastAPI - Yüksek Performans
- LRU cache (ephemeris + chart) ~200ms -> ~5ms
- Async + orjson
- Streamlit'ten bağımsız, Flutter APK direkt çağırır
"""
import os, sys, time, copy
from functools import lru_cache
from datetime import datetime, date
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field

from core.timezone_utils import otomatik_utc_offset
from engine.horary_engine import cast_horary_chart
from engine.interpreter import call_openai

app = FastAPI(title="Horary Oracle API", version="1.0.0", default_response_class=ORJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ---------- Models ----------
class CastRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, example="babam nerede?")
    lat: float = Field(..., ge=-90, le=90, example=38.4237)
    lon: float = Field(..., ge=-180, le=180, example=27.1428)
    lang: str = Field("tr", pattern="^(tr|en|es|ar|pt|fr|de|ru|it|hi)$")
    quesited_type: str = Field("general", description="UI kategori: relationship/money/job/lost_object/missing_person vb.")
    asker: str = Field("ben", description="ben / baskasi - yükselen kim?")
    # sohbet hafızası: önceki sorular (horary_app.py:96 ile aynı)
    history: Optional[list] = None
    # opsiyonel: client kendi zamanını gönderirse
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[float] = None  # local decimal
    # kalibrasyon/doğrulama: gerçek konum şehir adı (tahmine asla karışmaz, sadece kayıt)
    verify_city: Optional[str] = None

class AuthRequest(BaseModel):
    email: str
    password: str
    device_id: str | None = None

class HealthResponse(BaseModel):
    status: str
    version: str

# ---------- Cache ----------
@lru_cache(maxsize=1024)
def cached_chart(y, m, d, utc_dec, lat, lon, qtype):
    # swisseph + Regiomontanus en pahalı kısım -> cache
    return cast_horary_chart(y, m, d, utc_dec, lat, lon, qtype)

# ---------- Helpers ----------
def resolve_time(req: CastRequest):
    if req.year and req.month and req.day and req.hour is not None:
        y, mo, da, local_dec = req.year, req.month, req.day, req.hour
        # Tarihsel (<1900) için modern tzdb anachronistic -> LMT kullan (lon/15)
        if y < 1900:
            off = round(req.lon / 15.0, 2)
            # Londra için LMT ~0, hassas: lon/15
            tzname = "LMT"
        else:
            off, tzname = otomatik_utc_offset(req.lat, req.lon, y, mo, da, local_dec)
        utc_dec = local_dec - off
        # gün sarkması düzeltmesi (gece 00:30 local -> utc önceki gün)
        if utc_dec < 0:
            utc_dec += 24
            # tarih bir gün geri (basit - ay sınırı için datetime kullan)
            try:
                from datetime import timedelta
                dt = datetime(y, mo, da) + timedelta(days=-1)
                y, mo, da = dt.year, dt.month, dt.day
            except: pass
        elif utc_dec >= 24:
            utc_dec -= 24
            try:
                from datetime import timedelta
                dt = datetime(y, mo, da) + timedelta(days=1)
                y, mo, da = dt.year, dt.month, dt.day
            except: pass
        return y, mo, da, utc_dec, off, tzname, local_dec
    else:
        utc_now = datetime.utcnow()
        y, mo, da = utc_now.year, utc_now.month, utc_now.day
        utc_dec = utc_now.hour + utc_now.minute/60 + utc_now.second/3600
        off, tzname = otomatik_utc_offset(req.lat, req.lon, y, mo, da, 12)
        local_dec = utc_dec + off
        if local_dec >= 24: local_dec -= 24
        if local_dec < 0: local_dec += 24
        return y, mo, da, utc_dec, off, tzname, local_dec

@app.get("/api/health", response_model=HealthResponse)
async def health():
    return {"status":"ok","version":"1.0.0"}

@app.post("/api/auth/login")
async def auth_login(req: AuthRequest):
    from auth import verify
    ok, info = verify(req.email, req.password, req.device_id)
    if not ok: raise HTTPException(401, str(info))
    return {"ok":True, **info}

@app.get("/admin")
async def admin_page():
    from fastapi.responses import HTMLResponse
    import pathlib
    html = pathlib.Path("horary_oracle/admin.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@app.get("/admin/list")
async def admin_list(key: str = ""):
    import os, json
    admin_key = os.getenv("ADMIN_KEY", "")
    # Env set ise key zorunlu, yoksa geçici açık (ama logla)
    if admin_key and key != admin_key:
        raise HTTPException(403, "forbidden: admin key required")
    db_path = os.path.join(os.path.dirname(__file__), "users.json")
    if os.path.exists(db_path):
        return json.load(open(db_path,encoding='utf-8'))
    if os.path.exists("horary_oracle/users.json"):
        return json.load(open("horary_oracle/users.json",encoding='utf-8'))
    return {}

@app.post("/admin/create")
async def admin_create(email: str, key: str = ""):
    import os
    admin_key = os.getenv("ADMIN_KEY", "")
    if admin_key and key != admin_key:
        raise HTTPException(403, "forbidden: admin key required")
    from auth import create_user
    pwd = create_user(email)
    return {"email":email, "password":pwd, "expiry": "1 yil"}

@app.post("/api/horary/cast")
async def cast(req: CastRequest):
    # --- Sohbet modülü (horary_app.py:118 ile birebir) ---
    qlow = req.question.strip().lower()
    # Sohbet sürekliliği: takip mi yeni soru mu?
    is_followup = False
    if req.history and len(req.history) >= 2:
        has_qmark = "?" in req.question or "mı" in qlow or "mi" in qlow or "mu" in qlow
        # yeni horary sorgu anahtarları
        new_q_keys = ["evlenecek","bosanacak","bosan","ise girecek","seviyor","kayip","kayi","nerede","nerde","hasta","araba","para","is yeri","kedi","kopek","ev al","satin"]
        is_new_question = has_qmark and any(k in qlow for k in new_q_keys)
        if not is_new_question:
            follow_keys = ["peki","ya o","o ne","bu ne","nasıl","nasil","neden","niye","sonra","devam","acikla","açar mısın","acar misin"]
            if len(qlow.split()) < 10 and any(k in qlow for k in follow_keys):
                is_followup = True
            if any(k in qlow for k in ["o","bu","şu"]) and len(qlow) < 40 and not has_qmark:
                is_followup = True
            # soru işareti yok + kısa cümle = normal akış
            if "?" not in req.question and len(qlow.split()) < 12 and not is_new_question:
                is_followup = True
    if is_followup:
        # takip: yeni chart açmadan önceki cevabın üzerine muhabbet devam (LLM'e history ver)
        pass  # aşağıda engine_json'a history eklenecek
    # Doğal sohbet yakalama - her yazılanı horary sanma
    chat_greetings = ["merhaba","selam","selamlar","hey","hi","hello","günaydın","iyi akşamlar","iyi geceler","sa","mrb"]
    if qlow in chat_greetings or (len(qlow)<=8 and any(qlow.startswith(g) for g in ["merhaba","selam","günaydın","iyi akşam","iyi geceler","hey","hello"])):
        return {"verdict":"CHAT","score":0,"perfection":{"type":"none"},"timing":{},"querent":{},"quesited":{},"houses":{},"strictures":[],"lots":{},"location":{},"answer":"Merhaba! Ben Horary Oracle — evrenle soru anının diliyle konuşuyorum. Aklındaki tek ve önemli soruyu sor, haritanı döküp muhabbet gibi anlatayım. Örn: *babam nerede?* / *bu işe girecek miyim?* / *bana yazacak mı?*","meta":{"tz":"chat","utc_offset":0,"local_dec":0,"ms":0}}
    if any(k in qlow for k in ["nasılsın","nasil sin","ne haber","naber","nasilsin"]):
        return {"verdict":"CHAT","score":0,"perfection":{"type":"none"},"timing":{},"querent":{},"quesited":{},"houses":{},"strictures":[],"lots":{},"location":{},"answer":"İyiyim, seni dinliyorum! Biraz dertleşelim mi, yoksa aklındaki o tek önemli soruyu mu soralım? Örn: 'aklımdaki kişi beni seviyor mu?' gibi — net bir soru haritayı çok keskinleştirir.","meta":{"tz":"chat","utc_offset":0,"local_dec":0,"ms":0}}
    # Kısa sohbet / dertleşme / teşekkür - horary kelimesi yoksa sohbet et ve öneri sun
    # Follow-up ise bu guard atlanır (açıklama isteniyor)
    horary_keys = ["evlenecek","boşan","bosan","seviyor","arar mı","yazar mı","dönecek","gelcek","gelecek","işe girecek","ise girecek","kazanır","kaybol","kayıp","nerede","nerde","alacak","satacak","hasta","iyileşecek","hamile","sınav","okul","para","ev al","araba","kedi","köpek","rüya","ruya","borç","mahkeme","taşın","evlene","ayrıl","barış","neden geldi","kim bu","çalınd","calind","çalın","calin","çaldı","caldi","hırsız","hirsiz","soyuldu","soygun","aşırdı","asirdi","hangi","hangisi","ameliyat","tedavi","iyile","iyiles","kanser","şifa","sifa","doktor","cerrahi","sağlık","saglik"]
    is_horary = any(k in qlow for k in horary_keys) or "?" in req.question
    if not is_followup and not is_horary and len(qlow.split()) < 12:
        # sohbet modu - öneri sun
        if any(k in qlow for k in ["teşekkür","sağol","sagol","eyvallah","tamam","anladım","anladim","haklısın","haklisin"]):
            return {"verdict":"CHAT","score":0,"perfection":{"type":"none"},"timing":{},"querent":{},"quesited":{},"houses":{},"strictures":[],"lots":{},"location":{},"answer":"Rica ederim, ne demek! Aklına başka bir soru düşerse buradayım — tek ve net sorarsan harita daha keskin konuşur. Örn: 'o iş olacak mı?' gibi.","meta":{"tz":"chat","utc_offset":0,"local_dec":0,"ms":0}}
        if len(qlow) < 40 and "?" not in req.question:
            return {"verdict":"CHAT","score":0,"perfection":{"type":"none"},"timing":{},"querent":{},"quesited":{},"houses":{},"strictures":[],"lots":{},"location":{},"answer":"Seni dinliyorum — biraz daha anlatır mısın? İstersen bunu horary sorusuna çevirelim: tek cümlede, net sor. Örn: 'bu evi alacak mıyım?' / 'bana dönecek mi?' / 'kaybolan nerede?' — hangisi kalbine yakın?","meta":{"tz":"chat","utc_offset":0,"local_dec":0,"ms":0}}
    # follow-up: önceki haritayı hatırla (history içinde son assistant charth olabilir, ama basit: client history gönderirse)
    # history varsa ve soru "açar mısın / neden / nasıl" ise önceki chart'a dair detay dön (horary_app.py:132)
    # Bu endpoint stateless olduğu için follow-up için history'de son chart'ı client göndermeli; şimdilik passthrough
    t0 = time.perf_counter()
    y, mo, da, utc_dec, off, tzname, local_dec = resolve_time(req)

    # quesited auto - UI kategori varsa onu kullan, yoksa genel + derived override
    qtype = req.quesited_type if req.quesited_type and req.quesited_type != "general" else "general"
    try:
        res = copy.deepcopy(cached_chart(y, mo, da, utc_dec, req.lat, req.lon, qtype))
    except Exception as e:
        raise HTTPException(500, f"Chart error: {e}")

    # derived override (babam nerede gibi) - horary_app ile aynı mantık
    try:
        from engine.derived_houses import parse_multi, parse_derived
        from core.ephemeris import sign_from_lon, DOMICILE
        derived = parse_multi(req.question) or parse_derived(req.question)
        if derived and derived.get("derived"):
            derived_num = derived["derived"]
            cusp_lon = res['houses']['cusps'][derived_num-1]
            derived_sign = sign_from_lon(cusp_lon)
            derived_ruler = DOMICILE.get(derived_sign,"Venus")
            res['quesited'] = {"planet":derived_ruler,"house":derived_num,"sign":derived_sign,"data":res['planets'].get(derived_ruler)}
            res['derived_info'] = derived
    except: pass

    # location (yer bulma) - is_self / is_live + doğal gösterge + derived house
    loc_info = {}
    try:
        from engine.location_engine import direction_by_house, distance_fixed, house_location_meaning, height_by_sign, ELEMENT, ELEMENT_KALITE, burc_yer_detay, ev_ici_yer
        q = req.question.lower()
        # derived house varsa (anne/baba/eş/öğrenci/ben vb) onu kullan
        derived_loc = None
        try:
            from engine.derived_houses import parse_derived
            d = parse_derived(req.question)
            if d and d.get("derived"):
                derived_loc = d
        except: pass
        # doğal gezegen ikincili: anne->Ay, baba->Güneş(birincil)+Satürn(ikincil)
        # Kullanıcı bulgusu: baba sorusunda Güneş=1. gösterge (yön ve mesafede nokta atışı),
        # "güneş de baba demek" + querent×quesited×10 formülü (bkz. distance_querent_quesited)
        is_male_sib = any(k in q for k in ["erkek kardeş","erkek kardes","erkek kardeşim","erkek kardesim","ağabey","agabey","abi","abim","abisi","ağabeyi","agabeyi"])
        is_female_sib = any(k in q for k in ["kız kardeş","kiz kardes","kız kardeşim","kiz kardesim","bacı","baci","abla","ablam","ablası","ablasi"])
        natural = None
        natural_second = None
        # çok-katmanlı iç içe ilişkide doğal göstergeyi SON sorulan kişinin cinsiyetine bağla
        # ('iş arkadaşım X'in abisinin kızı Defne' -> kızı = dişil -> Venüs/Ay)
        from engine.horary_questions import parse_nested as _pn_local
        _pn = _pn_local(req.question) if not ("ben" in q and any(k in q for k in ("nerede","nerde","nere"))) else None
        _pgen = None
        if _pn:
            _nw = _pn.get("nested_word", "")
            if any(s in _nw for s in ("kızı","kizi","ablası","ablasi","annesi","karısı","karisi","sevgilisi","bacısı")):
                _pgen = "female"
            elif any(s in _nw for s in ("abisi","ağabeyi","agabeyi","oğlu","oglu","babası","babasi","kocası","kocasi")):
                _pgen = "male"
        if _pn and _pgen == "female":
            natural = "Moon"; natural_second = "Venus"
        elif _pn and _pgen == "male":
            natural = "Mars"; natural_second = "Sun"
        elif "anne" in q or "annem" in q:
            natural = "Moon"
        elif "baba" in q or "babam" in q:
            natural = "Sun"        # baba: Güneş birincil
            natural_second = "Saturn"  # Satürn ikincil teyit
        elif is_male_sib:
            natural = "Mars"       # erkek kardeş/abi/asker: Mars birincil (kullanıcı bulgusu)
            natural_second = "Sun"  # Güneş ikincil teyit
        elif is_female_sib:
            natural = "Moon"       # kız kardeş: Ay birincil (kadının doğalı)
            natural_second = "Venus"  # Venüs ikincil teyit
        # kayıp eşya doğal göstergeleri (Deneb Kaitos yöntemi: bıçak=Mars, yüzük=Venüs,
        # değerli saat=Satürn(+Venüs), evrak/not=Merkür). Cüzdan/tekstil 1. ev, kıymetli mal 2. ev işler.
        object_label = None
        if any(k in q for k in ["bıçak","bicak","bıçağım","bicagim","çakı","caki","silah","bıçakla","kılıç","kılic"]):
            natural, natural_second, object_label = "Mars", None, "bıçak"
        elif any(k in q for k in ["yüzük","yuzuk","yüzüğüm","yuzugum","yüzükler","alyans"]):
            natural, natural_second, object_label = "Venus", None, "yüzük"
        elif any(k in q for k in ["saatim","saatini","kol saat","kol saati","kol saatim"]) or ("saat" in q and "yi kir" not in q and "yı kir" not in q):
            natural, natural_second, object_label = "Saturn", "Venus", "saat"
        elif any(k in q for k in ["evrak","evrakım","evrakları","doküman","dokuman","evrakını","ders notu","ders notlarım","notlarım","belge","belgeler","sözleşme","sozlesme","kontrat","diploma","pasaport"]):
            natural, natural_second, object_label = "Mercury", None, "evrak"
        if object_label:
            loc_info["_object"] = object_label
        # öncelik: doğal gezegen varsa onu baz al (baba=Güneş, anne=Ay)
        if natural and res['planets'].get(natural):
            use_data = res['planets'][natural]
            actual_house = use_data['house']
            sig_planet = natural
            loc_info["_natural"] = natural
            if natural_second:
                loc_info["_natural_second"] = natural_second
            # derived bilgisini de ek not
            if derived_loc:
                loc_info["_derived_house"] = derived_loc["derived"]
        elif derived_loc:
            cusp_lon = res['houses']['cusps'][derived_loc["derived"]-1]
            from core.ephemeris import sign_from_lon as _sfl2, DOMICILE_TRADITIONAL as _DOM2
            dsign = _sfl2(cusp_lon)
            dplanet = _DOM2.get(dsign, "Moon")
            use_data = res['planets'].get(dplanet, res['quesited']['data'])
            actual_house = use_data['house']
            sig_planet = dplanet
            loc_info["_derived_house"] = derived_loc["derived"]
        else:
            is_self = "ben" in q and any(k in q for k in ["nerede","nerde","nere"])
            sig_planet = res['querent']['planet'] if is_self else res['quesited']['planet']
            use_data = res['querent']['data'] if is_self else res['quesited']['data']
            actual_house = use_data['house']
        # kardeş belirsizliği: ad/cinsiyet/büyüklük yoksa hangi kardeş? netleştir
        is_generic_sib = ("kardeş" in q or "kardes" in q) and not is_male_sib and not is_female_sib
        if is_generic_sib:
            loc_info["clarify"] = "Hangi kardeş olduğunu netleştir (erkek mi/kız mı, adı veya büyük-küçük) — birden fazla kardeşten hangisini sorduğunu söylersen nokta atışı çıkar."
        from engine.location_engine import direction_by_sign
        house_dir = direction_by_house(actual_house)
        sign_dir = direction_by_sign(use_data['sign'])
        # Kural (kullanıcı): gösterge ASC/MC/DSC/IC'den <=10° ise kişi sorana ÇOK YAKINDIR.
        # patron testi: 10.ev Aslan, yöneticisi Güneş; Güneş MC'ye 9.8° -> birlikte 12-13 m gerçeği.
        _angles = {"ASC": res['houses']['asc'], "MC": res['houses']['mc']}
        _angles["DSC"] = (_angles["ASC"]+180)%360
        _angles["IC"] = (_angles["MC"]+180)%360
        _prox_name, _prox_dist = None, 999.0
        _plon = use_data['lon']
        for _an, _av in _angles.items():
            _ad = min(abs(_plon - _av), 360 - abs(_plon - _av))
            if _ad < _prox_dist:
                _prox_dist, _prox_name = _ad, _an
        if _prox_dist <= 10.0:
            loc_info["proximity"] = "cok yakin"
            loc_info["proximity_angle"] = f"{_prox_name}'ye {_prox_dist:.1f}°"
            loc_info["proximity_orb"] = round(_prox_dist, 1)
        # çocuk/kayıp hayvan için çift teyit: ev yönü + burç yönü + Ay yönü en az 2 uyuşsun
        is_child = "çocuk" in q or "cocuk" in q or "oğlum" in q or "kızım" in q or req.quesited_type in ("missing_child","child")
        is_pet = "kedi" in q or "köpek" in q or "kopek" in q or "hayvan" in q or "evcil" in q or req.quesited_type in ("pet","lost_pet","animal")
        direction_ok = True
        direction_note = ""
        if is_child or is_pet:
            who = "çocuk kayıp" if is_child else "kedi/köpek"
            # basit uyum: aynı ana yön kelimesi geçiyor mu?
            house_main = house_dir.split()[0]
            sign_main = sign_dir.split()[0]
            moon_dir = direction_by_sign(res['planets']['Moon']['sign'])
            moon_main = moon_dir.split()[0]
            matches = sum([house_main in sign_dir or sign_main in house_dir, house_main in moon_dir or moon_main in house_dir, sign_main in moon_dir or moon_main in sign_dir])
            if matches < 1:
                direction_ok = False
                direction_note = f"{who}da yön teyidi zayıf: ev {house_dir} / burç {sign_dir} / Ay {moon_dir} — tek başına güvenme, teyit gerek"
        # Uzaklık: soruyu soran yükselen yöneticisi derecesi × sorulan derecesi ×10 (kullanıcı bulgusu)
        # Merkür 8.45 × Güneş 6.35 = 53.65 → ×10 = 536 km (İzmir→Bağcılar 480 km bandı, nokta atışı)
        # 2026-08-30 Gaziemir testi: Akrep ASC klasik yöneticisi MARS 12.36° × Moon 3.49° ×10 = 431 km (gerçek Manavgat ~413 km ✓);
        # modern Pluto dersek 123.7 km çıkıyor (yanlış) → km formülünde klasik yönetici (DOMICILE_TRADITIONAL) kullanılır.
        try:
            from engine.location_engine import distance_querent_quesited
            from core.ephemeris import DOMICILE_TRADITIONAL as _DOMT
            _asc_sign_r = res['houses']['asc_sign']
            asc_ruler_klasik = _DOMT.get(_asc_sign_r, res['querent']['planet'])
            qr_deg = res['planets'][asc_ruler_klasik]['deg'] % 30
            qs_deg = use_data['deg'] % 30
            qq_dist = distance_querent_quesited(qr_deg, qs_deg)
            loc_info["_qr_ruler_klasik"] = f"{asc_ruler_klasik} {qr_deg:.1f}° ({_asc_sign_r} yöneticisi)"
        except Exception:
            qq_dist = None
        # çok yakın kuralı: km formülü geçersiz, analtitik izler sıfırlanır
        if loc_info.get("proximity"):
            qq_dist = None
        # ikincil doğal gösterge notu (baba=Satürn / kız kardeş=Venüs)
        second_note = ""
        if loc_info.get("_natural_second") and res['planets'].get(loc_info["_natural_second"]):
            s2 = res['planets'][loc_info["_natural_second"]]
            s2_deg = s2['deg'] % 30
            second_note = f"{loc_info['_natural_second']} {s2['sign']} {s2_deg:.1f}° Ev{s2['house']}"
        loc_info = {
            "direction": house_dir,
            "sign_direction": sign_dir,
            "direction_ok": direction_ok,
            "direction_note": direction_note,
            "house": actual_house,
            "sig_planet": sig_planet,
            "distance": f"{distance_fixed(req.lat, use_data['deg'], actual_house, req.lat>0)[0]:.0f}{distance_fixed(req.lat, use_data['deg'], actual_house, req.lat>0)[1]}",
            "qq_distance_km": qq_dist,
            "saturn_second": second_note,
            "proximity": loc_info.get("proximity",""),
            "proximity_angle": loc_info.get("proximity_angle",""),
            "proximity_orb": loc_info.get("proximity_orb",""),
            "_object": loc_info.get("_object",""),
            "_natural": loc_info.get("_natural",""),
            "_derived_house": loc_info.get("_derived_house",""),
            "place": house_location_meaning(actual_house),
            "ev_ici": ev_ici_yer(actual_house),
            "height": height_by_sign(use_data['sign']),
            "element_kalite": ELEMENT_KALITE.get(ELEMENT.get(use_data['sign'],''),''),
            "burc_detail": burc_yer_detay(use_data['sign']),
            "sign": use_data['sign'],
            "deg": round(use_data['deg'],1),
            "center": f"{req.lat},{req.lon} merkezine gore",
            "clarify": loc_info.get("clarify", ""),
            "_qr_ruler_klasik": loc_info.get("_qr_ruler_klasik", "")
        }
        # Yeni HORARY UZAKLIK MOTORU (ev+burç+gezegen ağırlıklı yön; kalibrasyonlu mesafe bandı)
        # NOT: legacy 'proximity' (Jüpiter açıya yakın vs.) bu motoru ASLA kapatmaz;
        #      aktif motorun kendi yakınlık kuralı var (angular<5 -> mesafe yok).
        geo_res = None
        try:
            from engine.horary_distance import (HoraryDistanceEngine, HoraryCalibration,
                                                condition_factor, load_weights, verify_prediction, CITY_COORDINATES)
            from engine.horary_questions import classify_question, parse_nested
            from engine.derived_houses import parse_derived as _parse_derived_g
            from core.ephemeris import DOMICILE_TRADITIONAL as _DOMT3, sign_from_lon as _sfl_g
            _asc_s3 = res['houses']['asc_sign']
            _qur3 = _DOMT3.get(_asc_s3, res['querent']['planet'])
            # soru tipi -> kalibrasyon bucket'ı (hoca/arkadaş/öğrenci/...)
            _qc = classify_question(req.question) or {}
            _qn = parse_nested(req.question)
            # derived-house fallback: 'kuzenimin altınları' gibi ev-zinciri soruları için
            _qd = _parse_derived_g(req.question) if (not _qn and not _qc.get("house")) else None
            qtype_g = _qc.get("type") or (req.quesited_type if req.quesited_type != "general" else "location")
            # significator: iç içe ilişkiyse (arkadaşımın eşi) turned-house yöneticisi
            # EV ÖNCELİĞİ: nested-derived > soru-tipi evi > derived(parse_derived) > gösterge gezegeninin bulunduğu ev
            # doğal gösterge (Mars=abi/asker, Ay=anne...) tespit edildiyse ÖNCELİKLİ:
            # nested/turned ev yöneticisi onu ezmesin (muazzezin abisi -> Mars, 8.ev Merkür değil)
            _natural_g = loc_info.get("_natural")
            _ghouse = actual_house
            if _qn and not _natural_g:
                _ghouse = _qn["derived"]
            elif _qc.get("house") and not _natural_g:
                _ghouse = _qc["house"]
            elif _qd and _qd.get("derived") and not _natural_g:
                _ghouse = _qd["derived"]
            _gplanet, _gsign, _guse = sig_planet, use_data['sign'], use_data
            if _qn and not _natural_g:
                _cusp_g = res['houses']['cusps'][_qn["derived"] - 1]
                _gsign = _sfl_g(_cusp_g)
                _gplanet = _DOMT3.get(_gsign, "Moon")
                _guse = res['planets'].get(_gplanet, use_data)
            elif _qc.get("house") and not _natural_g:
                _cusp_g = res['houses']['cusps'][_qc["house"] - 1]
                _gsign = _sfl_g(_cusp_g)
                _gplanet = _DOMT3.get(_gsign, "Moon")
                _guse = res['planets'].get(_gplanet, use_data)
            elif _qd and _qd.get("derived") and not _natural_g:
                _cusp_g = res['houses']['cusps'][_qd["derived"] - 1]
                _gsign = _sfl_g(_cusp_g)
                _gplanet = _DOMT3.get(_gsign, "Moon")
                _guse = res['planets'].get(_gplanet, use_data)
            # gezegen gücü (F3/F4): asalet + retro + combust -> mesafe katsayısı
            _cf = condition_factor(_gplanet, _gsign, lon=_guse.get('lon'),
                                   retro=_guse.get('retro', False),
                                   sun_lon=res['planets']['Sun'].get('lon'))
            _eng_g = HoraryDistanceEngine(weights=load_weights())
            geo_res = _eng_g.analyze(
                house=_ghouse,
                sign=_gsign,
                planet=_gplanet,
                friend_longitude=_guse.get('lon'),
                querent_longitude=res['planets'][_qur3]['lon'],
                condition=_cf['factor'],
                return_components=True,
                sign_querent=res['planets'][_qur3].get('sign'),
            )
            geo_res["dignity"] = ", ".join(_cf["labels"])
            if _qc:
                geo_res["qtype"] = _qc["type"]
                geo_res["qtype_label"] = _qc["label"]
            if _qn:
                geo_res["chain"] = _qn["formula"]
            elif _qd and _qd.get("formula"):
                geo_res["chain"] = _qd["formula"]
            _cal3 = HoraryCalibration()
            _cal3.load()
            geo_res = _cal3.apply(geo_res, question_type=qtype_g, origin=(req.lat, req.lon))
            if geo_res.get("angular") < 5:
                geo_res["band"] = ""
                geo_res["category"] = "yakın (soranın kendisi şu an bulunduğu konumda)"
                geo_res["mesafe_kalibre_km"] = None
            # DOĞRULAMA: gerçek konum tahmine ASLA karışmaz; sadece kayıt + geri bildirim
            if req.verify_city:
                _cl = req.verify_city.strip().lower()
                _mcity = next((k for k in CITY_COORDINATES if k.lower() == _cl), None)
                if _mcity and geo_res.get("mesafe_kalibre_km") is not None:
                    _c0, _c1 = CITY_COORDINATES[_mcity]
                    _verify = verify_prediction(geo_res["azimut"], geo_res["mesafe_kalibre_km"],
                                                req.lat, req.lon, _c0, _c1)
                    if _verify.get("real_bearing") is not None:
                        _cal3.add_record(
                            upsert=True,
                            question_type=qtype_g,
                            origin=f"{req.lat},{req.lon}",
                            destination=_mcity,
                            house=geo_res["house"],
                            significator=geo_res["significator"],
                            sign=geo_res["sign"],
                            sign_querent=res['planets'][_qur3].get('sign'),
                            degree=round(_guse.get('deg', 0) % 30, 2),
                            querent_planet=_qur3,
                            querent_degree=round(res['planets'][_qur3].get('deg', 0) % 30, 2),
                            angular_difference=geo_res["orb_deg"],
                            modality=geo_res["modality"],
                            modality_multiplier=geo_res["modality_multiplier"],
                            components=geo_res.get("components"),
                            condition=geo_res.get("condition", 1.0),
                            real_distance_km=_verify["real_distance_km"],
                            real_bearing=_verify["real_bearing"],
                        )
                        _cal3.save()
                        _rec_id = _cal3.records[-1]["_id"]
                        _verify["record_added"] = _rec_id
                        _verify["feedback"] = (
                            f"Vaka #{_rec_id} kalibrasyona eklendi — gerçek {_mcity}: "
                            f"{_verify['real_distance_km']} km / yön {_verify['real_bearing']}°. "
                            f"Yön hatası {_verify['direction_error_deg']}°, mesafe hatası {_verify['distance_error_km']} km. "
                            f"({_verify['verdict_text']})"
                        )
                        geo_res["calibration_n"] = len(_cal3.records)
                        _cal3.apply(geo_res, question_type=qtype_g, origin=(req.lat, req.lon))
                        geo_res["verification"] = _verify
        except Exception as _e3:
            print(f"horary_geo hata: {_e3}")
            geo_res = None
        loc_info["horary_geo"] = geo_res
    except Exception as e:
        print(f"loc_info hata: {e}")
        loc_info = {"house": 7, "direction": "BATI", "distance": "", "place": "", "height": "", "element_kalite": "", "burc_detail": "", "ev_ici": ""}

    # --- NEREDE/KAYIP soruları: YES/NO değil LOCATION (baba nerede, kaybolan nerede) ---
    # Konum sorusu olduğu için karar "evet/hayır" değil; sorgulayan hep NO almamalı
    qlow3 = req.question.lower()
    is_where_q = any(k in qlow3 for k in ["nerede","nerde","nere","nereye","nere da","kaybol","kayıp","kayip","tutar mı","nere git","nereye gid","hangi yön","hangi yon","hangi taraf"]) or req.quesited_type in ("missing_person","missing_child","pet","lost_object")
    if is_where_q:
        loc_info["person"] = "quesited"
        # kimin yerini soruyoruz (person etiketi - mock_interpret label için)
        for kw,lab in [("anne","anne"),("babam","baba"),("baba","baba"),("kardeş","kardeş"),("kardes","kardeş"),("ablam","kardeş"),("abim","kardeş"),("abla","kardeş"),("abi","kardeş"),("ağabey","kardeş"),("agabey","kardeş"),("bacı","kardeş"),("baci","kardeş"),("öğrencim","öğrenci"),("ogrencim","öğrenci"),("öğrenci","öğrenci"),("ogrenci","öğrenci"),("arkadaş","arkadaş"),("arkadas","arkadaş"),("eşim","eş"),("esim","eş"),("kocam","koca"),("karım","karı"),("oğlum","oğlum"),("og lum","oğlum"),("kızım","kızım"),("kizim","kızım"),("çocuk","çocuk"),("cocuk","çocuk"),("kedi","kedi"),("kopek","köpek"),("köpek","köpek"),("patronum","patron"),("patron","patron"),("müdürüm","patron"),("müdür","patron"),("yüzüğüm","yüzük"),("yüzüğ","yüzük"),("yuzug","yüzük"),("yüzük","yüzük"),("yuzuk","yüzük"),("bıçak","bıçak"),("bicak","bıçak"),("bıçağ","bıçak"),("bicag","bıçak"),("evrak","evrak"),("doküman","evrak"),("dokuman","evrak"),("belge","evrak"),("ders notu","evrak"),("saatim","saat"),("kol saati","saat")]:
            if kw in qlow3:
                loc_info["person"] = lab.replace("oğlum","çocuk").replace("kızım","çocuk").replace("kocam","eş")
                break
        if any(k in qlow3 for k in ["ben nerede","ben nerde","ben şimdi","ben simdi","neredeyim","nerdeyim"]):
            loc_info["is_self"] = True
            loc_info["person"] = ""
        # Kayıp mı merak mı ayrımı: gerçek kayıp/çalınma işareti yoksa "merak" (manasızlık riski, hafif yorum)
        kayip_kw = ["kaybol","kayıp ","kayipli","kayip ","kaybettim","kaybetti","kaybettik","kaybetmiş","kaybetmis","bulunamıyor","bulunamiyor","bulunmuyor","çalındı","calindi","çalınd","calind","çalınmış","calinmis","çalındılar","calindilar","çaldılar","caldilar","aşırdı","asirdi","aşırdılar","asirdilar","dönmedi","donmedi","geri gelmedi","geri donmedi","ulaşamıyorum","ulasamiyorum","ulasamıyorum","uzun zamandır yok","haber yok","kayıpsa","kayıp ise"]
        loc_info["urgency"] = "kayip" if any(k in qlow3 for k in kayip_kw) else "merak"
        res["verdict"] = "LOCATION"

    # --- Gizli visitor modelleri (sistem içinde, dışarıda görünmez) ---
    qlow2 = req.question.lower()
    is_visitor_who = any(k in qlow2 for k in ["yanıma gelen","yanimda gelen","yanımdaki kişi","yanimdaki kisi","karşımdaki kişi","karsimdaki kisi","kim bu kişi","nasıl biri","nasil biri"])
    is_visitor_why = any(k in qlow2 for k in ["neden geldi","neden aradı","neden yazdı","neden aradi","niyeti ne","neden mesaj","neden geldiğini"])
    is_dream = any(k in qlow2 for k in ["rüya","ruya","rüyam","ruyam","rüyam ne","ruyam ne","rüyada gördüm","ruyada gordum"])
    if is_visitor_who or is_visitor_why or is_dream:
        try:
            # visitor_who: ASC + ASC yöneticisi burç/ev + sabit yıldız karakteri
            asc_sign = res['houses']['asc_sign']; asc_deg = res['houses']['asc'] % 30
            ruler = res['querent']['planet']; ruler_data = res['querent']['data']
            # sabit yıldız
            star_note = ""
            for s in res['strictures']:
                if s['code'].startswith('fixed_star') and s.get('planet')==ruler:
                    star_note = f" Sabit yıldızı {s.get('star')} ({s.get('dist')}°) karakterine damga vuruyor."
                    break
            elem = {"Koç":"ateş","Boğa":"toprak","İkizler":"hava","Yengeç":"su","Aslan":"ateş","Başak":"toprak","Terazi":"hava","Akrep":"su","Yay":"ateş","Oğlak":"toprak","Kova":"hava","Balık":"su"}
            if is_visitor_who:
                res['strictures'].insert(0, {"code":"visitor_who","level":"info","meaning":f"Gizli WHO: ASC {asc_sign} {asc_deg:.1f}° — gelen kişi {elem.get(asc_sign,'')} enerjisinde, yöneticisi {ruler} {ruler_data['sign']} {ruler_data['deg']:.1f}° Ev{ruler_data['house']}{' Rx' if ruler_data['retro'] else ''} → o evin konularıyla tanımlı kişi.{star_note}"})
            if is_visitor_why:
                sev_house = res['quesited']['house']; moon_house = res['planets']['Moon']['house']
                third_cusp = res['houses']['cusps'][2] % 360
                from core.ephemeris import sign_from_lon as _sfl
                third_sign = _sfl(third_cusp)
                res['strictures'].insert(0, {"code":"visitor_why","level":"info","meaning":f"Gizli WHY: 7.yöneticisi {res['quesited']['planet']} Ev{sev_house} ({res['quesited']['sign']}), Ay Ev{moon_house} ({res['planets']['Moon']['sign']}) niyeti gösteriyor; 3.ev {third_sign} mesaj/arma şekli. 7→1 açısı varsa doğrudan sana yönelik niyet."})
            if is_dream:
                # dream: 12. ev + 9. ev + Ay + Neptune
                twelfth_cusp = res['houses']['cusps'][11] % 360
                from core.ephemeris import sign_from_lon as _sfl2, DOMICILE as _DOM
                twelfth_sign = _sfl2(twelfth_cusp)
                twelfth_ruler = _DOM.get(twelfth_sign, "Saturn")
                tw_data = res['planets'].get(twelfth_ruler, {})
                moon_sign = res['planets']['Moon']['sign']; moon_house = res['planets']['Moon']['house']
                neptune = res['planets'].get('Neptune', {})
                nept_note = f" Neptune Ev{neptune.get('house','?')} {neptune.get('sign','')}" if neptune else ""
                # 9. ev kehanet kontrol
                ninth_sign = _sfl2(res['houses']['cusps'][8] % 360)
                res['strictures'].insert(0, {"code":"dream_meaning","level":"info","meaning":f"Gizli DREAM: 12.ev {twelfth_sign} yöneticisi {twelfth_ruler} {tw_data.get('sign','')} Ev{tw_data.get('house','?')} → rüyanın kaynağı o evin konuları; Ay {moon_sign} Ev{moon_house} rüyanın taşıyıcısı; {nept_note} prophetic/karmaşa ayırt eder; 9.ev {ninth_sign} kehanet potansiyeli."})
        except: pass

    # LLM sadece tercüman - GERÇEK harita verisini gönder (halüsinasyonu önle)
    engine_json = {
        "verdict": res["verdict"], "score": res["score"],
        "perfection": res["perfection"], "timing": res.get("timing"),
        "strictures": res["strictures"],
        "querent": res["querent"]["planet"], "quesited": res["quesited"]["planet"],
        "querent_sign": res["querent"]["sign"], "quesited_sign": res["quesited"]["sign"],
        "houses": {"asc": res["houses"]["asc"], "asc_sign": res["houses"]["asc_sign"], "mc": res["houses"]["mc"]},
        "planets": {k: {"sign": v["sign"], "deg": round(v["deg"],2), "house": v["house"], "retro": v.get("retro",False)} for k,v in res.get("planets",{}).items()},
        "question": req.question, "location": loc_info,
        "is_followup": is_followup, "history": req.history[-4:] if req.history and is_followup else []
    }
    # visitor/dream için prompt'a gizli talimat ekle (dışarıda görünmez)
    if is_visitor_who or is_visitor_why or is_dream:
        hidden = []
        if is_visitor_who: hidden.append("WHO: ASC ve yöneticisinin burç/ev/sabit yıldızına göre karakteri muhabbet gibi anlat")
        if is_visitor_why: hidden.append("WHY: 7.yönetici evi + Ay evi + 3.ev ile niyeti anlat")
        if is_dream: hidden.append("DREAM: 12.ev yöneticisi evi + Ay burç/ev + Neptune ile rüyanın kaynağı/prophetic mi/kaygı mı olduğunu muhabbet gibi anlat, standart horary kalıbının dışına çık")
        engine_json["hidden_instruction"] = "Bu soru gizli model: " + " | ".join(hidden) + " - insani dil kullan."
    # NEREDE sorularında mesafe: daima querent×quesited×10 formülü (qq_distance_km) esas
    if res["verdict"] == "LOCATION" and loc_info.get("proximity"):
        engine_json["loc_instruction"] = "Bu bir NEREDE/KONUM sorusu ve gösterge bir açıya (ASC/MC/DSC/IC) çok yakın (" + str(loc_info.get("proximity_angle","")) + " ≤10°) — kural: KİŞİ SORANA ÇOK YAKINDIR. Cevabında kişinin hemen yakınlarda/aynı mekanda olduğunu söyle; km çarpım formülü bu durumda GEÇERSİZ, HİÇBİR km/metre rakamı verme. Yine de 'Ev yönü: location['direction']' ve 'Burç yönü: location['sign_direction']' kısımlarını rapor et (kişinin hangi yönde durduğuna işaret eder). Gösterge: " + str(loc_info.get('_qr_ruler_klasik','')) + "."
        if loc_info.get("clarify"):
            engine_json["loc_instruction"] += f" Soru hangi kardeş olduğunu söylemiyor — cevabın SONUNA şu netleştirmeyi de ekle: {loc_info['clarify']}"
    elif res["verdict"] == "LOCATION" and loc_info.get("horary_geo"):
        g = loc_info["horary_geo"]
        engine_json["loc_instruction"] = (
            "Bu bir NEREDE/KONUM sorusu - HORARY UZAKLIK MOTORU ciktisini kullan, kendi km hesabi/carpim yapma.\n"
            "Panel (cevabinda bu blok gibi profesyonel sun):\n"
            + (f"- Soru kategorisi: {g['qtype_label']}{' | Zincir: ' + g['chain'] if g.get('chain') else ''}\n" if g.get("qtype") else "")
            + f"- Sorulan evi: H{g['house']} | Significator: {g['significator']} {g['sign']} ({loc_info.get('deg','')}°) | Querent: {loc_info.get('_qr_ruler_klasik','')} | Ekliptik fark: {g['angular']}°\n"
            + (f"- Gösterge gücü: {g['dignity']}\n" if g.get("dignity") else "")
            + f"- Yon: {g['yon_label']} civari (model isabeti: {g.get('direction_confidence','belirsiz')} - kalibrasyon ort yon hatasi {g.get('direction_mean_err_deg','?')} derece) - ev {g['house']} temel + {g['sign']} burc + {g['significator']} gezegen duzeltmesi (ağırlıklar: ev .50 / burç .30 / gezegen .20, azimut yaklasik {g['azimut']} derece)\n"
            + f"- Mesafe: " + (g['band'] + " km" if g.get('band') else "kisa, su anki konumu")
            + (f" | Bolge: {g['km_category']} ({g['km_category_range']})" if g.get('km_category') else "")
            + f" | Kategori: {g['category']} | Guven: {g['confidence']} (kalibrasyon: {g['calibration_n']} vaka, olcek {g['calibration_scale']})\n"
            + (f"- Olcek merdiveni (aynı Δθ farklı ölçekte farklı km demek — mentor kuralı): oda içi ~{g['scale_ladder'].get('oda içi','?')} m / şehir içi ~{g['scale_ladder'].get('şehir içi','?')} km / ülke içi ~{g['scale_ladder'].get('ülke içi','?')} km / kıtalararası ~{g['scale_ladder'].get('kıtalararası','?')} km. Şu an varsayılan katman: {g.get('likely_tier','şehir içi')}.\n" if g.get("scale_ladder") else "")
            + ("- Doğrulama (kullanıcının verdiği gerçek konum): " + g['verification']['feedback'] + "\n" if g.get("verification") else "")
            + "Ev-ici ipucu: " + loc_info.get("ev_ici", "") + " | Yukseklik: " + loc_info.get("height", "")
        )
        if loc_info.get("clarify"):
            engine_json["loc_instruction"] += f" Soru hangi kardeş olduğunu söylemiyor — cevabın SONUNA şu netleştirmeyi de ekle: {loc_info['clarify']}"
    elif res["verdict"] == "LOCATION" and loc_info.get("qq_distance_km"):
        engine_json["loc_instruction"] = "Bu bir NEREDE/KONUM sorusu. Yönü İKİ kısımda rapor et, birbirine karıştırma: 'Ev yönü: location['direction']' ve 'Burç yönü: location['sign_direction']'. MESAFE: KESİNLİKLE kendi hesap/çarpma yapma ve 'qq_distance_km' dışında başka hiçbir km/metre rakamı verme. location['qq_distance_km'] değerini aynen 'km' cinsinden söyle (örneğin 'yaklaşık 1514 km'), formülünün 'Yükselen yönetici derecesi × sorulanın derecesi × 10' olduğunu kısaca belirt. Yükselen yöneticisi (klasik tablo): location['_qr_ruler_klasik']. location['distance'] (metre) değerini ana mesafe olarak kullanma. location['saturn_second'] sadece ikinci doğal gösterge bilgisi, mesafe hesabına karıştırma."
        if loc_info.get("clarify"):
            engine_json["loc_instruction"] += f" Soru hangi kardeş olduğunu söylemiyor — cevabın SONUNA şu netleştirmeyi de ekle: {loc_info['clarify']}"
    # Kayıp yakın/ev içi ise: 12-ev eviçi tablosu (kaybolanın göstergesinin evi -> ev içi yer)
    if res["verdict"] == "LOCATION" and loc_info.get("ev_ici"):
        engine_json["loc_instruction"] = (engine_json.get("loc_instruction","") or "") + " Ev-içi yer ipucu (kaybolanın göstergesinin evi): " + loc_info["ev_ici"] + " — cevabında bu oda/eşya tarifini kullan, kısa tut."
    if res["verdict"] == "LOCATION" and loc_info.get("urgency") == "merak":
        engine_json["loc_instruction"] = (engine_json.get("loc_instruction","") or "") + " NOT: bu soru kayıp/çalınma değil, gündelik MERAK kategorisinde (manasızlık riski) — kişinin şu an nerede olabileceğini yön+mesafe ile NAZİKÇE söyle, 'gitmiş/dönmüyor/kayıp' gibi kesin telaşlı hüküm ve tehdit tespiti verme. Cevabının SONUNA şunu da ekle: 'Kişi gerçekten kayıpsa veya ulaşamıyorsan bunu ayrıca söyle, kayıp analizi açarım.'"
    # --- HIRSIZLIK/KAYIP AYRIMI (Deneb Kaitos): 12. ev yöneticisinin açıları ---
    theft_kw = ["hırsız","hirsiz","hırsızlık","hirsizlik","çalınd","calind","çalın","calin","çaldı","caldi","aşırdı","asirdi","aşırıldı","asirildi","çalınmış","calinmis","soyuldu","soygun","kaptırdı","kaptirdi"]
    if any(k in req.question.lower() for k in theft_kw):
        try:
            from core.ephemeris import sign_from_lon as _sfl_teft
            from core.ephemeris import DOMICILE_TRADITIONAL as _DOMT_teft
            _c12 = res['houses']['cusps'][11] % 360
            _s12 = _sfl_teft(_c12)
            _l12p = _DOMT_teft.get(_s12, "Moon")
            _l12 = res['planets'].get(_l12p, {})
            _asc_p = _DOMT_teft.get(res['houses']['asc_sign'], res['querent']['planet'])
            _asc_l = res['planets'].get(_asc_p, {})
            _moon = res['planets'].get('Moon', {})
            def _asp_12(a, b):
                d = (b - a) % 360
                if d > 180: d = 360 - d
                ms = [0, 60, 90, 120, 180]
                mm = min(ms, key=lambda m: abs(m - d))
                return mm, round(abs(mm - d), 1)
            a1, o1 = _asp_12(_l12.get('lon', 0), _asc_l.get('lon', 0))
            a2, o2 = _asp_12(_l12.get('lon', 0), _moon.get('lon', 0))
            hards = [x for x in ((a1, o1), (a2, o2)) if x[0] in (90, 180) and x[1] <= 6]
            softs = [x for x in ((a1, o1), (a2, o2)) if x[0] in (0, 60, 120) and x[1] <= 6]
            if hards and not softs:
                verdict_hm = "ÇALINTI (dürüst kayıp değil, biri almış)"
            elif hards:
                verdict_hm = "ÇALINTI-MELEZ (sert açı baskın ama iyi açı da var — bazı parçalar geri gelebilir)"
            elif softs:
                verdict_hm = "KAYIP (çalınmamış, kaybolmuş/yer değiştirmiş)"
            else:
                verdict_hm = "KAYIP-BELİRSİZ (12. ev yöneticisi 6° içinde belirgin açı yapmıyor — çoğunlukla kayıptır)"
            _c7 = res['houses']['cusps'][6] % 360
            _s7 = _sfl_teft(_c7)
            _l7p = _DOMT_teft.get(_s7, "Venus")
            _l7h = res['planets'].get(_l7p, {}).get('house')
            un_txt = "AÇIK DÜŞMAN/AİLE İÇİ — hırsız tanıdık, ev içi (bakıcı, temizlikçi, sekreter, gelin gibi; 7. ev karşıdan gelir)" if _l7h in (1, 4, 7, 10) else "UZAK/DIŞARI — hırsız tanımadığın biri, 7. ev köşe evde değil"
            th_txt = (f"HIRSIZLIK/ÇALINMA analizi (12. evin açı kuralı): karar → {verdict_hm}. "
                      f"12.ev {_s12} yöneticisi {_l12p} {_l12.get('sign','')} Ev{_l12.get('house','?')}, "
                      f"ASC yöneticisi {_asc_p} ile {a1}° ({'hard' if a1 in (90,180) else 'soft' if a1 in (0,60,120) else 'none'}, {o1}° orb); "
                      f"Ay ile {a2}° ({o2}° orb). Hırsız konumu: {un_txt}. "
                      f"7.ev yöneticisi {_l7p} Ev{_l7h}. Not: hırsızı gösteren mitolojik göstergeler Neptün (=12, dolandırıcı) ile 12. ev yöneticisidir.")
            res['strictures'].insert(0, {"code": "theft_analysis", "level": "info", "meaning": th_txt})
            engine_json["theft_analysis"] = th_txt
            engine_json["theft_verdict"] = verdict_hm
            engine_json["theft_thief"] = un_txt
        except Exception as e:
            engine_json["theft_analysis"] = f"HIRSIZLIK analizi hesaplanamadı ({e}) — genel kayıp kuralları (12. ev) geçerli."
    # --- İKİ SEÇENEK / HANGİ? kararı (Deneb Kaitos: Ay'ın olumlu açısı) ---
    import re as _re2
    _mıc = len(_re2.findall(r"\bm[ıiuü]\b", qlow))
    _hangi = any(k in qlow for k in ["hangisini", "hangisine", "hangisi ", "hangisi?", "hangisinde", "hangisini ?"])
    if _mıc >= 2 or _hangi:
        try:
            _moon2 = res['planets'].get('Moon', {})
            OPT_PLANET = {
                "dolar": "Jupiter", "usd": "Jupiter", "euro": "Jupiter", "avro": "Jupiter", "döviz": "Jupiter", "doviz": "Jupiter",
                "altın": "Venus", "altin": "Venus", "gümüş": "Venus", "gumus": "Venus", "para": "Venus", "pırlanta": "Venus",
                "ev": "Saturn", "daire": "Saturn", "rezidans": "Saturn", "arsa": "Saturn", "taşınmaz": "Saturn", "tasınmaz": "Saturn",
                "bina": "Saturn", "gayrimenkul": "Saturn", "villa": "Saturn", "yazlık": "Saturn", "yazlik": "Saturn", "tarla": "Saturn",
                "araba": "Mars", "oto": "Mars", "taşıt": "Mars", "tasit": "Mars",
                "iş": "Mercury", "is": "Mercury", "işyeri": "Mercury", "isyeri": "Mercury", "okul": "Mercury", "şirket": "Jupiter", "sirket": "Jupiter", "ders": "Mercury",
                "anne": "Moon", "annem": "Moon", "kız": "Venus", "kiz": "Venus", "sevgili": "Venus", "karı": "Venus", "kari": "Venus",
                "baba": "Sun", "babam": "Sun", "erkek": "Mars", "abi": "Mars", "ağabey": "Mars", "agabey": "Mars",
            }
            _words2 = _re2.findall(r"[a-zçğıöşü]+", qlow)
            _stops2 = {"mı", "mi", "mu", "mü", "miyim", "miyiz", "ile", "yoksa", "veya", "ya", "ama", "ben", "sen", "hangi", "hangisini", "hangisi", "olsa", "olsun", "alsam", "alsaydım", "alsaydim", "alayım", "alayim", "alan", "hmm", "karar", "veremiyorum", "veremem", "kararım", "kararim"}
            _seen2 = []
            for _w in _words2:
                if len(_w) > 16 or _w in _stops2 or _w in _seen2:
                    continue
                _best = ""
                for _k in OPT_PLANET:
                    if _w.startswith(_k) and len(_k) > len(_best):
                        _best = _k
                if _best and _best not in _seen2:
                    _seen2.append(_best)
            def _asp3(a, b):
                d = (b - a) % 360
                if d > 180:
                    d = 360 - d
                ms = [0, 60, 90, 120, 180]
                mm = min(ms, key=lambda x: abs(x - d))
                return mm, round(abs(mm - d), 1)
            _rows2 = []
            _fav2 = []
            for _w in _seen2:
                _pp = OPT_PLANET[_w]
                _pl = res['planets'].get(_pp, {})
                if not _pl:
                    continue
                _a, _o = _asp3(_moon2.get('lon', 0), _pl.get('lon', 0))
                _k = "OLUMLU" if (_a in (0, 60, 120) and _o <= 6) else ("OLUMSUZ" if (_a in (90, 180) and _o <= 6) else "SIFIR")
                if _k == "OLUMLU":
                    _fav2.append(_w)
                _rows2.append(f"{_w} ({_pp} {_pl.get('sign','')} Ev{_pl.get('house','?')}) -> Ay-{_pp}: {_a} derece {_k}, orb {_o} derece")
            if len(_fav2) == 1:
                _verdict2 = f"AY'IN LEHİNE OLAN SEÇENEK: '{_fav2[0]}' — Ay, bu seçeneğin temsilcisiyle olumlu açı yapan tek seçenek (mentor karar kuralı). Diğer seçeneklere sert/sıfır açı var."
            elif len(_fav2) > 1:
                _verdict2 = f"Birden fazla seçenek Ay ile olumlu: {', '.join(_fav2)} — uzun vadeli/taşınmaz seçimlerde uzun vadeyi Satürn belirler, ona göre yorumla; Ay'ın yaklaşan açısı kime önce dokunacaksa hafif avantaj o seçenekte."
            elif _seen2:
                _verdict2 = "Ay, seçeneklerin hiçbiriyle 6° içinde olumlu açı yapmıyor — karar belirsiz, acele etme; Ay'ın bir sonraki yaklaşan açısına bak (hangi gezegene gidecekse konu oraya kayar)."
            else:
                _verdict2 = "Seçenekler gezegen karşılığı çıkarılamadı (ise/isim gibi ifadeler) — Ay'ın burcu/evi ve sonraki açısı üzerinden insani şekilde yorumla; 'hangisi olumlu' diye kesin rakam verme."
            _t2 = "İKİLİ KARAR kuralı (mentor/Deneb Kaitos: Ay, sorunun belirteciyle hangisiyle olumlu açı yapıyorsa onu seç; uzun vadeli/taşınmazda Ay+Satürn belirler): " + _verdict2 + ". " + (" | ".join(_rows2) if _rows2 else f"Ay {_moon2.get('sign','')} Ev{_moon2.get('house','?')}, sonraki yaklaşan açısına bak.")
            res['strictures'].insert(0, {"code": "two_option", "level": "info", "meaning": _t2})
            engine_json["two_option"] = _t2
            engine_json["two_option_verdict"] = _verdict2
        except Exception as e:
            engine_json["two_option"] = f"İkili karar hesaplanamadı ({e}) — Ay'ın burç/ev durumuna göre değerlendir."
            engine_json["two_option_verdict"] = "belirsiz"
    # --- SAĞLIK AKSI (Deneb Kaitos: hasta=1, hastalık=6L, doktor=7L, ameliyat=8L, tedavi=10L, sonuç=4L) ---
    health_kw = ["hasta", "hastay", "hastası", "hastasi", "iyileş", "iyiles", "şifa", "sifa", "ameliyat", "tedavi", "doktor", "cerrahi", "kanser", "tümör", "tumor", "ağrı", "agri", "sancı", "sanci", "rahatsız", "rahatsiz", "sağlık", "saglik", "sıhhat", "sihhat"]
    if any(k in qlow for k in health_kw):
        try:
            from core.ephemeris import sign_from_lon as _sfl_hl, DOMICILE_TRADITIONAL as _DOMT_hl
            from core.ephemeris import EXALTATION as _EX_hl, DETRIMENT as _DET_hl, FALL as _FALL_hl
            _pat_kw_child = any(k in qlow for k in ["kızım", "kizim", "oğlum", "oglum", "çocuğ", "cocug", "bebeğ", "bebeg"])
            _pat_kw_es = any(k in qlow for k in ["eşim", "esim", "karım", "karim", "kocam", "sevgilim", "arkadaşımın"])
            _pat_h = 5 if _pat_kw_child else (7 if _pat_kw_es else 1)
            _pat_s = _sfl_hl(res['houses']['cusps'][_pat_h - 1] % 360)
            _pat_r = _DOMT_hl.get(_pat_s, res['querent']['planet'])
            _pat_p = res['planets'].get(_pat_r, {})
            def _rlr_h(h):
                s = _sfl_hl(res['houses']['cusps'][h - 1] % 360)
                return s, _DOMT_hl.get(s, "Moon")
            _rows_h = []
            for h in (6, 8, 12, 4):
                _s, _p = _rlr_h(h)
                _pl = res['planets'].get(_p, {})
                _st = []
                if _pl.get('sign') == _s:
                    _st.append("domicile")
                if _EX_hl.get(_pl.get('sign', '')) == _p:
                    _st.append("exaltation")
                if _DET_hl.get(_pl.get('sign', '')) == _p:
                    _st.append("detriment")
                if _FALL_hl.get(_pl.get('sign', '')) == _p:
                    _st.append("fall")
                _rows_h.append(f"H{h}L({h}.ev {_s}): {_p} {_pl.get('sign','')} {(_pl.get('deg',0)%30):.1f}° Ev{_pl.get('house','?')}{' Rx' if _pl.get('retro') else ''}[{','.join(_st) if _st else 'nötr'}]")
            def _asp_h(a, b):
                d = (b - a) % 360
                if d > 180:
                    d = 360 - d
                ms = [0, 60, 90, 120, 180]
                mm = min(ms, key=lambda m: abs(m - d))
                return mm, round(abs(mm - d), 1)
            _krit = []
            for h in (6, 8, 12, 4):
                _s, _p = _rlr_h(h)
                _pl = res['planets'].get(_p, {})
                if not _pl or not _pat_p:
                    continue
                _aa, _oo = _asp_h(_pat_p.get('lon', 0), _pl.get('lon', 0))
                if _aa in (90, 180) and _oo <= 6:
                    _krit.append(f"H{_pat_h} yöneticisi {_pat_r} <-> H{h} yöneticisi {_p} {_aa}° kare/karşıt")
            for _pn, _pd in res['planets'].items():
                if _pn in ("NorthNode", "SouthNode"):
                    continue
                if _pd.get('house') in (6, 8, 12) and _pn in ("Mars", "Saturn", "Pluto", "Uranus"):
                    _krit.append(f"Malefik {_pn} H{_pd['house']} ({_pd['sign']})")
            _sun_h = res['planets'].get('Sun', {})
            if _sun_h and _pat_p:
                _dd = abs((_pat_p.get('lon', 0) - _sun_h.get('lon', 0) + 180) % 360 - 180)
                if _dd < 8.5:
                    _krit.append(f"{_pat_r} {_dd:.1f}° Güneş yanığı — gizli durum/Hasta hali saklı")
            _sn_h = res['planets'].get('SouthNode', {})
            _moon_h = res['planets'].get('Moon', {})
            for _nm, _np in (("Hasta gösterge", _pat_p), ("Moon", _moon_h)):
                if _sn_h and _np:
                    _dd = abs((_np.get('lon', 0) - _sn_h.get('lon', 0) + 180) % 360 - 180)
                    if _dd <= 3:
                        _krit.append(f"{_nm} {_np.get('sign','')} GAD kavuşumu ({_dd:.1f}°) — ağır")
            ORG_H = {"Saturn": "kemik/eklem/cilt/kronik/urlar", "Mars": "kesik/yara/iltihap/yüksek ateş/ameliyat", "Sun": "kalp/sırt/göz/bilinç kaybı", "Moon": "rahim/mide/hormon/gebelik/alerji", "Mercury": "sinir/zihinsel/solunum/ciğer", "Venus": "şeker/böbrek/yumurtalık kisti/kadın hastalıkları", "Jupiter": "karaciğer", "Pluto": "kanser/dönüşüm", "Neptune": "belirsiz/hayal kırıklığı", "Uranus": "sinir sistemi/vücut ritmi"}
            _org = set()
            for _pn, _pd in res['planets'].items():
                if _pd.get('house') in (6, 8, 12) and _pn in ORG_H:
                    _org.add(f"{_pn} H{_pd['house']} → {ORG_H[_pn]}")
            _orgz = "; ".join(sorted(_org)) if _org else "belirgin organ ipucu yok"
            _n = len(_krit)
            _hast = _pat_kw_child and 5 or (_pat_kw_es and 7 or 1)
            if _n >= 2:
                _dk = f"DURUM KRİTİK — {_n} ağır gösterge (6/8/12/4 yöneticileri H{_hast} göstergesine sert açı + malefik/yanık/GAD): tıbbi teyit şart, akışı monitörize edin"
            elif _n == 1:
                _dk = "DURUM DİKKAT — tek sert gösterge: toparlanma mümkün ama kötüleşme ihtimali izlenmeli, doktor görüşü alın"
            else:
                _dk = "DURUM NİSPETEN İYİ — 6/8/12/4 yöneticileri H" + str(_hast) + " göstergesine 6° içinde sert açı yapmıyor, malefik evlerde tehdit yok"
            _ht = ("SAĞLIK ANALİZİ: " + _dk + " | Hasta=H" + str(_hast) + "(" + str(_pat_r) + " " + _pat_p.get('sign','') + " Ev" + str(_pat_p.get('house','?')) + (" Rx" if _pat_p.get('retro') else "") + ") Hastalık=6L Doktor=7L Ameliyat=8L Tedavi=10L Sonuç=4L | " + " | ".join(_rows_h) + (" | Kritik işaretler: " + "; ".join(_krit) if _krit else " | Keskin kritik işaret yok") + " | Organ ipucu: " + _orgz)
            res['strictures'].insert(0, {"code": "health_axis", "level": "info", "meaning": _ht})
            engine_json["health_analysis"] = _ht
            engine_json["health_verdict"] = _dk
        except Exception as e:
            engine_json["health_analysis"] = f"Sağlık analizi hesaplanamadı ({e})"
            engine_json["health_verdict"] = "belirsiz"
    answer = call_openai(engine_json, req.lang)
    if engine_json.get("theft_verdict"):
        answer = "Hırsızlık/çalınma kararı: " + engine_json["theft_verdict"] + " — " + engine_json.get("theft_thief","") + "\n\n" + answer
    if engine_json.get("two_option_verdict") and engine_json["two_option_verdict"] != "belirsiz":
        answer = "İki seçenek kararı (Ay açısı kuralı): " + engine_json["two_option_verdict"] + "\n\n" + answer
    if engine_json.get("health_verdict") and engine_json["health_verdict"] != "belirsiz":
        answer = "Sağlık analizi: " + engine_json["health_verdict"] + "\n\n" + answer

    dt = (time.perf_counter()-t0)*1000
    # planets for mini chart
    planets_out = {k:{"lon":v["lon"],"sign":v["sign"],"deg":round(v["deg"],2),"house":v["house"]} for k,v in res.get("planets",{}).items() if k in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Pluto","Uranus","Neptune"]}
    return {
        "verdict": res["verdict"], "score": res["score"],
        "perfection": res["perfection"], "timing": res.get("timing"),
        "querent": res["querent"], "quesited": res["quesited"],
        "houses": {"asc": res["houses"]["asc"], "asc_sign": res["houses"]["asc_sign"], "mc": res["houses"]["mc"], "cusps": res["houses"]["cusps"]},
        "planets": planets_out,
        "strictures": res["strictures"][:12],
        "lots": res.get("lots",{}),
        "location": loc_info,
        "derived_info": res.get("derived_info"),
        "answer": answer,
        "meta": {"tz": tzname, "utc_offset": off, "local_dec": round(local_dec,2), "ms": round(dt,1)}
    }

# Render start: uvicorn horary_oracle.api:app --host 0.0.0.0 --port $PORT
