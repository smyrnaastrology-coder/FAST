import streamlit as st
import json, os, sys
from datetime import datetime, date, time as dtime

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

from core.ephemeris import SIGNS_TR, sign_from_lon, deg_in_sign
from core.timezone_utils import otomatik_utc_offset
from engine.horary_engine import cast_horary_chart
from engine.interpreter import mock_interpret, call_openai

st.set_page_config(page_title="Horary Oracle", page_icon="🔮", layout="centered")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=DM+Sans:wght@400;500&display=swap');
html, body, .stApp { background: radial-gradient(1200px 600px at 20% -10%, #2a1f38 0%, #1a1423 55%, #0f0a18 100%) !important; color: #e8e0f0; min-height:100vh; }
h1 { color: #C9A96E !important; font-family: 'Cormorant Garamond', serif; font-size: 42px !important; letter-spacing: 0.04em; text-shadow: 0 2px 20px rgba(201,169,110,0.25); }
h1 + div { color: #a898c0 !important; font-family: 'DM Sans', sans-serif; }
[data-testid="stChatMessage"] { background: rgba(42,31,56,0.9); border: 1px solid #3d2e50; border-radius: 16px; backdrop-filter: blur(8px); }
[data-testid="stChatMessage"]:nth-child(odd) { border-left: 3px solid #C9A96E; }
[data-testid="stChatInput"] { position: sticky; bottom: 20px; background: transparent !important; border: none; padding: 4px; }
[data-testid="stChatInput"] textarea { min-height: 110px !important; font-size: 17px !important; background: white !important; color: black !important; border-radius: 16px !important; border: 1px solid #3d2e50 !important; box-shadow: 0 8px 30px rgba(0,0,0,0.4); }
[data-testid="stChatInput"] textarea::placeholder { color: #666 !important; }
[data-testid="stChatInput"] button { background: #C9A96E !important; border-radius: 12px !important; }
.block-container { padding-top: 0.8rem; max-width: 900px; }
[data-testid="stSidebar"] { display:none; }
[data-testid="stHeader"] { background: transparent; }
</style>
<div style="text-align:center; padding: 10px 0 6px 0;">
  <div style="font-family:'Cormorant Garamond',serif; color:#C9A96E; font-size:13px; letter-spacing:0.35em; text-transform:uppercase;">Horary Oracle</div>
  <div style="font-family:'DM Sans',sans-serif; color:#a898c0; font-size:12px; letter-spacing:0.12em;">EVRENLE SORU ANININ DİLİ</div>
</div>
""", unsafe_allow_html=True)

LOCALES = {}
for lang in ["tr","en","es","ar","pt","fr","de","ru","it","hi"]:
    p = os.path.join(os.path.dirname(__file__), "locales", f"{lang}.json")
    if os.path.exists(p):
        with open(p,"r",encoding="utf-8") as f:
            LOCALES[lang]=json.load(f)
# Dil otomatik - sorulan sorunun dilinden (varsayılan tr)
lang = "tr"
L = LOCALES.get(lang, LOCALES["tr"])

st.title(L.get("app_title","Horary Oracle"))
st.caption("Deterministik motor v0.7 (Lilly + Usta 1-6) | Regiomontanus | 4 dil | LLM sadece tercüman")

# Konum - form dışında (butonlar form içinde yasak)
qp = st.query_params
if "lat" in qp and "lon" in qp:
    try:
        st.session_state.lat = float(qp["lat"]); st.session_state.lon = float(qp["lon"]); st.session_state.city = "GPS"
    except: pass
if "lat" not in st.session_state:
    st.session_state.lat, st.session_state.lon, st.session_state.city = 38.4237, 27.1428, "Izmir"

auto = st.checkbox("📍 Konumumu otomatik al", value=True, help="GPS en doğru, kişi dünyanın her yerinde olabilir")
if auto:
    import streamlit.components.v1 as components
    components.html("""
    <button onclick="getGPS()" style="background:#C9A96E;color:#1a1423;border:none;padding:10px 18px;border-radius:8px;font-weight:700;cursor:pointer;width:100%">📍 GPS ile Konumumu Bul (En Doğru)</button>
    <div id="gps" style="color:#a898c0;font-size:12px;margin-top:6px"></div>
    <script>
    function getGPS(){
      document.getElementById('gps').innerText='İzin isteniyor...';
      navigator.geolocation.getCurrentPosition(function(p){
        const lat=p.coords.latitude.toFixed(4), lon=p.coords.longitude.toFixed(4);
        document.getElementById('gps').innerText='Bulundu: '+lat+', '+lon+' — sayfa yenileniyor...';
        const url=new URL(window.parent.location.href);
        url.searchParams.set('lat',lat); url.searchParams.set('lon',lon);
        window.parent.location.href=url.toString();
      }, function(e){ document.getElementById('gps').innerText='Hata: '+e.message; });
    }
    </script>
    """, height=70)
    st.caption(f"📍 {st.session_state.city} — GPS otomatik")
    with st.expander("🌍 Şehir değiştir (opsiyonel)", expanded=False):
        city_search = st.text_input("Şehir ara", placeholder="Paris, Dubai, Tokyo yaz + Enter", label_visibility="collapsed")
        if city_search:
            try:
                from geopy.geocoders import Nominatim
                geo = Nominatim(user_agent="horary_oracle", timeout=5)
                loc = geo.geocode(city_search, language="en", exactly_one=True)
                if loc:
                    st.session_state.lat, st.session_state.lon, st.session_state.city = loc.latitude, loc.longitude, loc.address.split(",")[0]
                    st.success(f"Bulundu: {loc.address}")
                    st.rerun()
                else:
                    st.warning("Bulunamadı")
            except Exception as e:
                st.warning(f"Hata: {e}")

lat_def, lon_def, city_def = st.session_state.lat, st.session_state.lon, st.session_state.city

if "chat" not in st.session_state: st.session_state.chat=[]
# Sohbet geçmişi göster
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input(L.get("ask_placeholder","Sorunuz")+" — muhabbet gibi yaz, örn: babam nerede?")
qtype = "general"  # auto - ev türetme sorudan otomatik
# Tarih/saat/konum tamamen otomatik (profesyonel görünüm için gizli)
lat, lon, city = lat_def, lon_def, city_def
qdate = date.today()
qtime = datetime.now().time()
submitted = question is not None

if submitted and question:
    if not question.strip():
        st.error("❗ Soru boş.")
        st.stop()
    # Sohbete ekle
    st.session_state.chat.append({"role":"user","content":question})
    with st.chat_message("user"):
        st.write(question)
    # Küçük sohbet - horary değil
    small = question.strip().lower()
    if small in ["merhaba","selam","selamlar","hey","hi","hello"] or small.startswith("merhaba") or small.startswith("selam"):
        with st.chat_message("assistant"):
            ans = "Merhaba! Ben Horary Oracle — evrenle soru anının diliyle konuşuyorum. Aklındaki tek ve önemli soruyu sor, haritanı döküp muhabbet gibi anlatayım. Örn: *babam nerede?* veya *bu işe girecek miyim?*"
            st.success(ans)
        st.session_state.chat.append({"role":"assistant","content":ans})
        st.stop()
    if any(k in small for k in ["nasılsın","nasil sin","ne haber","naber"]):
        with st.chat_message("assistant"):
            ans = "İyiyim, senin sorularını bekliyorum! Horary için en önemli soruyu sor — kalbinden geçen, uykunu kaçıran soru. Ne sormak istersin?"
            st.success(ans)
        st.session_state.chat.append({"role":"assistant","content":ans})
        st.stop()
    # Muhabbet devamı - önceki haritayı hatırla
    follow = any(k in small for k in ["açar mısın","acar misin","detay","neden","niçin","nasıl","nasil","biraz daha","açıklar mısın"])
    if follow and "last_res" in st.session_state:
        with st.chat_message("assistant"):
            res = st.session_state.last_res
            engine_json = {"verdict":res["verdict"],"score":res["score"],"perfection":res["perfection"],"timing":res.get("timing"),"strictures":res["strictures"],"querent":res["querent"]["planet"],"quesited":res["quesited"]["planet"],"question":st.session_state.get("last_q",""),"location":st.session_state.get("last_loc",{})}
            detail = f"Tabii — önceki haritanda {res['querent']['planet']} ({res['querent']['data']['sign']}) ile {res['quesited']['planet']} ({res['quesited']['data']['sign']}) arasında {res['perfection'].get('type','')} var. "
            if res['perfection'].get('reception'): detail += f"Ağırlama: {res['perfection']['reception']}. "
            detail += f"Zaman: {res.get('timing',{}).get('text','')} — {res.get('timing',{}).get('unit','')} içinde. "
            # Ev türetme detayı
            if "derived_info" in res:
                d=res["derived_info"]; detail+= f"Ev türetme: {d.get('formula','')}."
            ans = detail + " Başka neyi merak ediyorsun?"
            st.success(ans)
        st.session_state.chat.append({"role":"assistant","content":ans})
        st.stop()
    offset, tzname = otomatik_utc_offset(lat, lon, qdate.year, qdate.month, qdate.day, qtime.hour + qtime.minute/60)
    local_decimal = qtime.hour + qtime.minute/60 + qtime.second/3600
    utc_decimal = local_decimal - offset
    y, m, d = qdate.year, qdate.month, qdate.day
    import swisseph as swe
    jd_utc = swe.julday(y, m, d, utc_decimal, swe.GREG_CAL)
    # Ev türetme - kardeşimin parası gibi
    try:
        from engine.derived_houses import parse_derived, parse_multi
        derived = parse_multi(question) or parse_derived(question)
        if derived and "house" in derived and "derived" not in derived:
            derived["derived"] = derived["house"]
            derived["base_word"] = derived.get("chain","")
        if derived and derived.get("derived"):
            # türetilmiş evi zorla kullan
            qtype_derived = f"derived_{derived['derived']}"
            # cast'i türetilmiş ev numarasıyla yap (quesited_map'e ekle)
            res = cast_horary_chart(y, m, d, utc_decimal, lat, lon, qtype)
            # manuel override: quesited evini türetilmişe çek
            derived_num = derived["derived"]
            from core.ephemeris import sign_from_lon, DOMICILE
            cusp_lon = res['houses']['cusps'][derived_num-1]
            derived_sign = sign_from_lon(cusp_lon)
            derived_ruler = DOMICILE.get(derived_sign,"Venus")
            res['quesited'] = {"planet":derived_ruler,"house":derived_num,"sign":derived_sign,"data":res['planets'].get(derived_ruler)}
            res['derived_info'] = derived
        else:
            res = cast_horary_chart(y, m, d, utc_decimal, lat, lon, qtype)
    except Exception as e:
        res = cast_horary_chart(y, m, d, utc_decimal, lat, lon, qtype)
    res["jd"] = jd_utc
    st.divider()
    # Nerede/nasıl için yer bilgisi - 2 formül (sabit + canlı)
    try:
        from engine.location_engine import direction_by_house, distance_fixed, distance_live, distance_live_advanced, distance_house_cusp, distance_moon_first_major
        is_self = "ben" in question.lower() and ("nerede" in question.lower() or "nerde" in question.lower() or "nere" in question.lower())
        is_live = any(k in question.lower() for k in ["kedi","köpek","kopek","çocuk","cocuk","kişi","kisi","insan"])
        use_house = res['querent']['house'] if is_self else res['quesited']['house']
        use_data = res['querent']['data'] if is_self else res['quesited']['data']
        # Yer için gezegenin bulunduğu ev (actual house) kullan, türetilmiş değil
        actual_house = use_data['house']
        direction = direction_by_house(actual_house)
        dist, unit = distance_fixed(lat, use_data['deg'], use_house, lat>0)
        # canlı ikinci formül
        cusp_lon = res['houses']['cusps'][use_house-1]
        cusp_dist = distance_house_cusp(cusp_lon, use_data['lon'])
        # element
        sign = use_data['sign']
        elem_key = "water" if sign in ["Yengeç","Akrep","Balık"] else "earth" if sign in ["Boğa","Başak","Oğlak"] else "air" if sign in ["İkizler","Terazi","Kova"] else "fire"
        elem_type = "cardinal" if sign in ["Koç","Yengeç","Terazi","Oğlak"] else "fixed" if sign in ["Boğa","Aslan","Akrep","Kova"] else "mutable"
        height = {"water":"alçak/bodrum/su kenarı","earth":"çok alçak/bodrum","air":"yüksek/çatı","fire":"yüksek/orta kat"}[elem_key]
        # canlı mesafe
        live_dist = distance_live(elem_type, use_house)
        live_adv = None
        if is_live:
            adv_val, adv_txt = distance_live_advanced(res['houses']['asc'], use_data['lon'], elem_type)
            live_adv = f"{adv_val:.0f}km ({adv_txt})"
        # Ay hareket alanı
        moon_d, moon_ang = distance_moon_first_major(res['planets']['Moon']['lon'], res['planets']['Moon']['speed'], use_data['lon'], use_data['speed'])
        loc_info = {"direction":direction,"distance":f"{dist:.0f}{unit}","house":actual_house,"height":height,"is_self":is_self,"cusp_km":f"{cusp_dist:.0f}km","live_adv":live_adv,"moon_move":f"{moon_d:.1f}°" if moon_d else None,"person": (derived.get("base_word","") if isinstance(derived.get("base_word",""), str) else "") if 'derived' in locals() and derived else ""}
        # Baba için ikinci gösterge Satürn (doğal baba)
        if "baba" in loc_info.get("person",""):
            try:
                sat = res['planets']['Saturn']
                sat_dir = direction_by_house(sat['house'])
                sat_dist, sat_unit = distance_fixed(lat, sat['deg'], sat['house'], lat>0)
                sat_elem = "water" if sat['sign'] in ["Yengeç","Akrep","Balık"] else "earth" if sat['sign'] in ["Boğa","Başak","Oğlak"] else "air" if sat['sign'] in ["İkizler","Terazi","Kova"] else "fire"
                sat_height = {"water":"alçak/bodrum","earth":"çok alçak/bodrum","air":"yüksek/çatı","fire":"yüksek/orta kat"}[sat_elem]
                loc_info["saturn_second"] = f"Satürn (doğal baba) → {sat_dir} yönünde ~{sat_dist:.0f}{sat_unit}, ev {sat['house']}, {sat_height} ({sat['sign']})"
            except: pass
    except:
        loc_info={}
    engine_json = {"verdict":res["verdict"],"score":res["score"],"perfection":res["perfection"],"timing":res.get("timing"),"strictures":res["strictures"],"querent":res["querent"]["planet"],"quesited":res["quesited"]["planet"],"question":question,"location":loc_info}
    answer = call_openai(engine_json, lang)
    # hafıza
    st.session_state.last_res = res; st.session_state.last_q = question; st.session_state.last_loc = loc_info
    with st.chat_message("assistant"):
        st.success(answer)
        st.caption(f"📍 {loc_info.get('direction','')} {loc_info.get('distance','')} | ⏳ {res.get('timing',{}).get('text','')}")
        # Ses - tarayıcı TTS (ElevenLabs sonra)
        import streamlit.components.v1 as components
        safe = answer.replace("'"," ").replace('"',' ').replace("\n"," ")
        components.html(f"""
        <button onclick="speechSynthesis.speak(new SpeechSynthesisUtterance('{safe[:400]}'))" style="background:#2a1f38;color:#C9A96E;border:1px solid #3d2e50;padding:6px 12px;border-radius:8px;cursor:pointer">🔊 Sesli Dinle</button>
        """, height=40)
    st.session_state.chat.append({"role":"assistant","content":answer})
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**ASC:** {res['houses']['asc']:.2f}° ({res['houses']['asc_sign']} {deg_in_sign(res['houses']['asc']):.1f}°)")
        st.markdown(f"**MC:** {res['houses']['mc']:.2f}° ({res['houses']['mc_sign']})")
        st.markdown(f"**Querent (1.ev):** {res['querent']['planet']} - {res['querent']['data']['sign']} {res['querent']['data']['deg']:.1f}° Ev {res['querent']['data']['house']} {'Rx' if res['querent']['data']['retro'] else ''}")
        st.markdown(f"**Quesited ({res['quesited']['house']}.ev):** {res['quesited']['planet']} - {res['quesited']['data']['sign']} {res['quesited']['data']['deg']:.1f}° Ev {res['quesited']['data']['house']} {'Rx' if res['quesited']['data']['retro'] else ''}")
        st.caption(f"TZ: {tzname} UTC{offset:+.1f} | JD {res['jd']:.5f}")
    with c2:
        st.markdown("**Gezegenler**")
        for name, d in res["planets"].items():
            if name in ["Uranus","Neptune","Pluto","NorthNode"]: continue
            st.text(f"{name:10s} {d['sign']:6s} {d['deg']:5.1f}°  Ev{d['house']} {'Rx' if d['retro'] else ''}")
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; import numpy as np
        fig, ax = plt.subplots(figsize=(4,4), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor('#1a1423'); ax.set_facecolor('#2a1f38')
        cusps = res['houses']['cusps']
        for i, c in enumerate(cusps):
            theta = np.deg2rad(90 - c)
            ax.plot([theta, theta], [0.3, 1], color='#3d2e50', lw=1)
            ax.text(theta, 1.08, str(i+1), color='#C9A96E', ha='center', va='center', fontsize=8, weight='bold')
        colors = {'Sun':'#FFD700','Moon':'#e8e0f0','Mercury':'#a898c0','Venus':'#ff8fab','Mars':'#f87171','Jupiter':'#4ade80','Saturn':'#94a3b8'}
        for name, d in res["planets"].items():
            if name in ["Uranus","Neptune","Pluto","NorthNode"]: continue
            th = np.deg2rad(90 - d['lon'])
            ax.plot(th, 0.85, marker='o', color=colors.get(name,'#C9A96E'), markersize=9)
            lab = name[:2] + (' Rx' if d.get('retro') else '')
            ax.text(th, 0.70, lab, color='white', ha='center', fontsize=6, weight='bold' if d.get('retro') else 'normal')
        perf = res.get('perfection',{})
        if perf.get('between'):
            try:
                p1, p2 = perf['between']
                if p1 in res['planets'] and p2 in res['planets']:
                    th1 = np.deg2rad(90 - res['planets'][p1]['lon']); th2 = np.deg2rad(90 - res['planets'][p2]['lon'])
                    col = '#4ade80' if perf.get('result')=='yes' else '#f87171'
                    ax.plot([th1, th2], [0.85, 0.85], color=col, lw=2, alpha=0.8)
            except: pass
        if perf.get('mediator') and perf['mediator'] in res['planets']:
            thm = np.deg2rad(90 - res['planets'][perf['mediator']]['lon'])
            ax.plot(thm, 0.85, marker='*', color='#C9A96E', markersize=14, markeredgecolor='white')
        ax.set_ylim(0,1); ax.set_yticklabels([]); ax.set_xticklabels([]); ax.grid(False)
        ax.set_title(f"An Haritası — ASC {res['houses']['asc_sign']} {res['houses']['asc']%30:.1f}°  |  {res['querent']['planet']}→{res['quesited']['planet']}", color='#C9A96E', fontsize=10, pad=20)
        st.pyplot(fig, use_container_width=True); plt.close(fig)
    except Exception as e:
        st.caption(f"Harita çizilemedi: {e}")
    try:
        from engine.location_engine import direction_by_house, distance_fixed
        h = res['quesited']['house']
        direction = direction_by_house(h)
        dist, unit = distance_fixed(lat, res['quesited']['data']['deg'], h, lat>0)
        st.caption(f"📍 Yer: {direction} yönünde ~{dist:.0f}{unit} | Ev {h}")
    except: pass
    if "timing" in res:
        st.info(f"⏳ **Zaman:** {res['timing']['text']}  |  Ay {res['timing']['burc_type']} / {res['timing']['house_type']} evinde → {res['timing']['unit']}")
        if res['timing'].get('planet_years'):
            st.caption(f"📅 Gezegen yılları: {res['timing']['planet_years']}")
    # Açıklama katmanı - tüm teknikler kart olarak (debug değil, kullanıcı görür)
    with st.expander("🔮 Teknik Açıklamalar (Lilly + Usta 1-7)", expanded=False):
        for s in res["strictures"]:
            icon = {"critical":"🔴","warning":"🟡","danger":"⛔","caution":"⚠️","info":"🔵"}.get(s.get("level","info"),"🔵")
            st.markdown(f"{icon} **{s['code']}** — {s.get('meaning','')}  {('`'+s['planet']+'`') if s.get('planet') else ''} {('`'+str(s.get('dist'))+'°`') if s.get('dist') else ''}")
        st.json(res["perfection"])
    if st.sidebar.checkbox("🔧 Debug (teknik kodlar)", value=False):
        with st.expander("Teknik Detay", expanded=False):
            st.json(res["perfection"])
            st.json(res["strictures"][:6])
            st.code(json.dumps({"verdict":res["verdict"],"score":res["score"]}, ensure_ascii=False, indent=2), language="json")

pass  # Kuralları Gör ve dil seçeneği gizli - sistem bütün
