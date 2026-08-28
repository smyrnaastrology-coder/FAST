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
    # sohbet hafızası: önceki sorular (horary_app.py:96 ile aynı)
    history: Optional[list] = None
    # opsiyonel: client kendi zamanını gönderirse
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[float] = None  # local decimal

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
    if qlow in chat_greetings or any(qlow.startswith(g) for g in chat_greetings):
        return {"verdict":"CHAT","score":0,"perfection":{"type":"none"},"timing":{},"querent":{},"quesited":{},"houses":{},"strictures":[],"lots":{},"location":{},"answer":"Merhaba! Ben Horary Oracle — evrenle soru anının diliyle konuşuyorum. Aklındaki tek ve önemli soruyu sor, haritanı döküp muhabbet gibi anlatayım. Örn: *babam nerede?* / *bu işe girecek miyim?* / *bana yazacak mı?*","meta":{"tz":"chat","utc_offset":0,"local_dec":0,"ms":0}}
    if any(k in qlow for k in ["nasılsın","nasil sin","ne haber","naber","nasilsin"]):
        return {"verdict":"CHAT","score":0,"perfection":{"type":"none"},"timing":{},"querent":{},"quesited":{},"houses":{},"strictures":[],"lots":{},"location":{},"answer":"İyiyim, seni dinliyorum! Biraz dertleşelim mi, yoksa aklındaki o tek önemli soruyu mu soralım? Örn: 'aklımdaki kişi beni seviyor mu?' gibi — net bir soru haritayı çok keskinleştirir.","meta":{"tz":"chat","utc_offset":0,"local_dec":0,"ms":0}}
    # Kısa sohbet / dertleşme / teşekkür - horary kelimesi yoksa sohbet et ve öneri sun
    # Follow-up ise bu guard atlanır (açıklama isteniyor)
    horary_keys = ["evlenecek","boşan","bosan","seviyor","arar mı","yazar mı","dönecek","gelcek","gelecek","işe girecek","ise girecek","kazanır","kaybol","kayıp","nerede","nerde","alacak","satacak","hasta","iyileşecek","hamile","sınav","okul","para","ev al","araba","kedi","köpek","rüya","ruya","borç","mahkeme","taşın","evlene","ayrıl","barış","neden geldi","kim bu"]
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
        from engine.location_engine import direction_by_house, distance_fixed, house_location_meaning, height_by_sign, ELEMENT, ELEMENT_KALITE, burc_yer_detay
        q = req.question.lower()
        # derived house varsa (anne/baba/eş/öğrenci/ben vb) onu kullan
        derived_loc = None
        try:
            from engine.derived_houses import parse_derived
            d = parse_derived(req.question)
            if d and d.get("derived"):
                derived_loc = d
        except: pass
        # doğal gezegen ikincili: anne->Ay, baba->Satürn
        natural = None
        if "anne" in q or "annem" in q:
            natural = "Moon"
        elif "baba" in q or "babam" in q:
            natural = "Saturn"
        # kullanım: derived varsa derived evinin yöneticisi, yoksa is_self mantığı
        if derived_loc:
            # derived evinin burcu ve yöneticisi
            cusp_lon = res['houses']['cusps'][derived_loc["derived"]-1]
            from core.ephemeris import sign_from_lon as _sfl2, DOMICILE as _DOM2
            dsign = _sfl2(cusp_lon)
            dplanet = _DOM2.get(dsign, "Moon")
            use_data = res['planets'].get(dplanet, res['quesited']['data'])
            actual_house = use_data['house']
            # doğal ikon ek not için sakla
            if natural:
                loc_info["_natural"] = natural
        else:
            is_self = "ben" in q and any(k in q for k in ["nerede","nerde","nere"])
            use_data = res['querent']['data'] if is_self else res['quesited']['data']
            actual_house = use_data['house']
            if natural:
                # doğal gezegeni de ikincil gösterge olarak ekle
                nat_data = res['planets'].get(natural)
                if nat_data:
                    loc_info["_natural_sec"] = f"{natural} {nat_data['sign']} Ev{nat_data['house']}"
        loc_info = {
            "direction": direction_by_house(actual_house),
            "house": actual_house,
            "distance": f"{distance_fixed(req.lat, use_data['deg'], actual_house, req.lat>0)[0]:.0f}{distance_fixed(req.lat, use_data['deg'], actual_house, req.lat>0)[1]}",
            "place": house_location_meaning(actual_house),
            "height": height_by_sign(use_data['sign']),
            "element_kalite": ELEMENT_KALITE.get(ELEMENT.get(use_data['sign'],''),''),
            "burc_detail": burc_yer_detay(use_data['sign']),
            "sign": use_data['sign'],
            "deg": round(use_data['deg'],1),
            "center": f"{req.lat},{req.lon} merkezine gore"
        }
    except Exception as e:
        print(f"loc_info hata: {e}")
        loc_info = {"house": 7, "direction": "BATI", "distance": "", "place": "", "height": "", "element_kalite": "", "burc_detail": ""}

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
    answer = call_openai(engine_json, req.lang)

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
        "answer": answer,
        "meta": {"tz": tzname, "utc_offset": off, "local_dec": round(local_dec,2), "ms": round(dt,1)}
    }

# Render start: uvicorn horary_oracle.api:app --host 0.0.0.0 --port $PORT
