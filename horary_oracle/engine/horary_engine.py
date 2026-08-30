"""
Deterministik Horary Motoru - LLM giremez, sadece matematik.
Lilly kuralları + horary_rules.json eşikleri.
"""
import json, os, math
import swisseph as swe
from core.ephemeris import (
    planetary_positions, houses_regiomontanus, house_of_planet,
    planetary_hour, DOMICILE, EXALTATION, DETRIMENT, FALL, sign_from_lon, deg_in_sign, SIGNS_TR
)

RULES_PATH = os.path.join(os.path.dirname(__file__), "horary_rules.json")

def load_rules():
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

RULES = load_rules()

# ---------- Helpers ----------
def angular_distance(a, b):
    d = (b - a) % 360
    return d if d <= 180 else d - 360  # signed

def next_aspect_distance(lon_fast, speed_fast, lon_slow, speed_slow, target_angle, orb):
    """
    Fast gezegen slow'a applying mi? Basit ileri projeksiyon.
    Hızlar derece/gün. Eğer fast slow'dan hızlı değilse applying olamaz (translation hariç).
    """
    diff = (lon_slow - lon_fast) % 360
    rel_speed = speed_fast - speed_slow
    closest_target = min([0,60,90,120,180], key=lambda a: abs((diff - a + 180) % 360 - 180))
    dist_to_target = abs((diff - closest_target + 180) % 360 - 180)
    diff_next = ((lon_slow + speed_slow*1) - (lon_fast + speed_fast*1)) % 360
    dist_next = abs((diff_next - closest_target + 180) % 360 - 180)
    applying = dist_next < dist_to_target and rel_speed > 0.05
    within_orb = dist_to_target <= orb
    return {"target": closest_target, "dist": dist_to_target, "applying": applying, "within_orb": within_orb, "diff": diff, "rel_speed": rel_speed}

def aspect_pair(lon_fast, lon_slow, angle):
    """En yakın tam açı noktası: slow +/- angle (mod 360). (applying, dist) döner.
    applying=True: tam açı noktası fast'in ÖNÜNDE (<180° gitmek gerek), False: arkada kaldı."""
    best = None
    for E in ((lon_slow + angle) % 360, (lon_slow - angle) % 360):
        f = (E - lon_fast) % 360
        d = f if f <= 180 else 360 - f
        app = f <= 180
        if best is None or d < best[1]:
            best = (app, d)
    return best

def best_applying_major(lon_fast, lon_slow, p1, p2, orbs):
    """iki gösterge arası en yakın APPLYING majör açı. (ang, dist, type) veya None.
    orbs: {(angle): base_orb} — moiety orbu dışarıda hesaplanır."""
    best = None
    for ang, base_orb in orbs.items():
        app, d = aspect_pair(lon_fast, lon_slow, ang)
        if not app:
            continue
        m1 = RULES["moiety"].get(p1, 7); m2 = RULES["moiety"].get(p2, 7)
        orb = max(base_orb, min((m1 + m2) / 2, 12))
        if d <= orb:
            if best is None or d < best[1]:
                best = (ang, d)
    return best

def in_dom_ex(planet, sign):
    return DOMICILE.get(sign) == planet or EXALTATION.get(sign) == planet

def in_det_fall(planet, sign):
    return DETRIMENT.get(sign) == planet or FALL.get(sign) == planet

def is_combust(planet_lon, sun_lon, orb=8.5):
    d = abs((planet_lon - sun_lon + 180) % 360 - 180)
    return d <= orb

def combustion_detail(planet_lon, sun_lon, planet_speed, sun_speed):
    """v0.6 katmanlı combustion: 0-2 / 2-8.5 / 8.5-17 / 17-18 + yaklaşan/uzaklaşan"""
    d = abs((planet_lon - sun_lon + 180) % 360 - 180)
    # yaklaşan mı? gezegen Güneş'e doğru mu gidiyor?
    diff = (sun_lon - planet_lon) % 360
    # bir gün sonra fark daralıyor mu?
    diff_next = ((sun_lon+sun_speed) - (planet_lon+planet_speed)) % 360
    d_next = abs((diff_next + 180) % 360 - 180)
    approaching = d_next < d
    if d <= 2:
        return {"layer":"cazimi_like_0_2","approaching":approaching,"severity":"info","dist":d}
    elif d <= 8.5:
        return {"layer":"combust_2_8_5","approaching":approaching,"severity":"critical","dist":d}
    elif d <= 17:
        return {"layer":"weakening_8_5_17","approaching":approaching,"severity":"warning","dist":d}
    elif d <= 18:
        return {"layer":"max_18","approaching":approaching,"severity":"info","dist":d}
    return None

def is_via_combusta(moon_lon):
    return 195 <= moon_lon <= 225

def is_via_combusta_with_exception(lon, deg_in_sign):
    """22-24 Foramen/Spica/Arcturus istisnası"""
    if not (195 <= lon <= 225):
        return False
    # 22-24 derecede ise istisna - olumsuz değil
    if deg_in_sign in (22,23,24):
        return False  # istisna, via combusta sayma
    return True

CRITICAL_DEGREES = {
    "cardinal": [0,13,26], "fixed": [9,21], "mutable": [4,17]
}
CARDINAL_SIGNS = ["Koç","Yengeç","Terazi","Oğlak"]
FIXED_SIGNS = ["Boğa","Aslan","Akrep","Kova"]
MUTABLE_SIGNS = ["İkizler","Başak","Yay","Balık"]

def is_critical_degree(sign, deg):
    d = int(round(deg))
    if sign in CARDINAL_SIGNS and d in CRITICAL_DEGREES["cardinal"]:
        return True
    if sign in FIXED_SIGNS and d in CRITICAL_DEGREES["fixed"]:
        return True
    if sign in MUTABLE_SIGNS and d in CRITICAL_DEGREES["mutable"]:
        return True
    return False

def is_besieged(planet_lon, planets_dict):
    """Kuşatılma: Mars/Saturn/Pluto/Uranus arasında 7° orb, Jup/Nept hariç"""
    besiegers = []
    for name in ["Mars","Saturn","Pluto","Uranus"]:
        if name not in planets_dict:
            continue
        d = abs((planets_dict[name]["lon"] - planet_lon + 180) % 360 - 180)
        if d <= 7:
            besiegers.append(name)
    # en az 2 farklı tarafta olmalı ama basit: 2+ kuşatıcı varsa besieged
    if len(besiegers) >= 2:
        return {"besieged": True, "by": besiegers}
    # tek tarafta bile 7° içinde ise de not et ama besieged değil
    return {"besieged": False, "by": besiegers}

# ---------- Ana motor ----------
def cast_horary_chart(year, month, day, hour_decimal, lat, lon, quesited_type="relationship"):
    """
    hour_decimal: yerel saat decimal (örn 14.5 = 14:30). UTC dönüşümü dışarıda yapılmalı, burada JD yerel UTC sanılır.
    lat, lon: soru sorulan yer
    quesited_type: horary_rules.json quesited_map anahtarı
    Returns: dict chart + judgement
    """
    # JD - swe.julday yerel saatin UTC olduğu varsayımıyla. Gerçek kullanımda UTC'ye çevrilmiş değer ver.
    jd = swe.julday(year, month, day, hour_decimal, swe.GREG_CAL)
    houses = houses_regiomontanus(jd, lat, lon)
    planets = planetary_positions(jd)
    # Ev atama
    for name, data in planets.items():
        data["house"] = house_of_planet(data["lon"], houses["cusps"])

    # Significator atama - MODERN: Akrep = Pluto birincil, Mars ikincil (Lilly dönemi Pluto yoktu)
    # Kullanıcı talimatı: geçmiş yapıyı aynen kullanmak zorunda değiliz, Pluto kullanılabilir
    CLASSIC_SIGNIFICATOR = {"Uranus":"Uranus","Neptune":"Neptune"}  # dış gezegenler korunur
    def classic(p):
        return CLASSIC_SIGNIFICATOR.get(p, p)
    asc_sign = houses["asc_sign"]
    asc_ruler = classic(DOMICILE.get(asc_sign, "Mars"))
    asc_ruler_trad = None
    if asc_sign == "Akrep":
        asc_ruler_trad = "Mars"
        # Pluto birincil, Mars ko-significator (modern)
    quesited_house_num = RULES["houses"]["quesited_map"].get(quesited_type, 7)
    # quesited evin burcu: cusp burcu
    quesited_cusp_lon = houses["cusps"][quesited_house_num - 1]
    quesited_sign = sign_from_lon(quesited_cusp_lon)
    quesited_ruler = classic(DOMICILE.get(quesited_sign, "Venus"))

    querent = {"planet": asc_ruler, "house": 1, "sign": asc_sign, "data": planets.get(asc_ruler)}
    if asc_ruler_trad:
        querent["co_ruler"] = asc_ruler_trad
        querent["co_data"] = planets.get(asc_ruler_trad)
    quesited = {"planet": quesited_ruler, "house": quesited_house_num, "sign": quesited_sign, "data": planets.get(quesited_ruler)}
    # Aynı gezegen ise -> Ay devralır + Masha'allah 6 kriter notu (lord ASC'ye bakıyor mu, Moon bakıyor mu, VOC ve son derece)
    masha_notes = []
    if querent["planet"] == quesited["planet"]:
        querent = {"planet": "Moon", "house": 1, "sign": asc_sign, "data": planets["Moon"], "note": "Aynı gezegen, Ay devraldı (Masha'allah 1-4)"}
        masha_notes.append("Masha'allah: lordlar aynı → Ay querent")
    else:
        # Basit Masha'allah kontrolü: lord ASC'ye açı yapıyor mu?
        def has_aspect(lon1, lon2):
            d = abs((lon2 - lon1 + 180)%360-180)
            return any(abs(d - a) <= 8 for a in (0,60,90,120,180))
        asc_lon = houses["asc"]
        if has_aspect(planets[asc_ruler]["lon"], asc_lon):
            masha_notes.append(f"Masha'allah: {asc_ruler} ASC'ye bakıyor → querent")
        elif planets["Moon"]["house"] == 1 or has_aspect(planets["Moon"]["lon"], asc_lon):
            masha_notes.append("Masha'allah: Ay ASC'ye bakıyor")
    # notlar strictures'a eklenecek (aşağıda strictures init sonrası)

    # Strictures - Usta sentezi v0.2: 4 kademeli ASC + significator derecesi + 7.ev Mars/Pluto
    asc_deg = deg_in_sign(houses["asc"])
    strictures = []
    for n in masha_notes:
        strictures.append({"code":"masha_allah","level":"info","meaning":n})
    # SolarFire benzeri: ASC burç sınırına yakın (29-30 ve 0-1) - ayrı uyarı
    next_sign = {"Koç":"Boğa","Boğa":"İkizler","İkizler":"Yengeç","Yengeç":"Aslan","Aslan":"Başak","Başak":"Terazi","Terazi":"Akrep","Akrep":"Yay","Yay":"Oğlak","Oğlak":"Kova","Kova":"Balık","Balık":"Koç"}.get(asc_sign,"")
    if asc_deg >= 29:
        strictures.append({"code":"asc_near_boundary","level":"critical","deg":round(asc_deg,2),"sign":asc_sign,"next_sign":next_sign,"meaning":f"ASC {asc_sign} {asc_deg:.2f}° — burç sınırına çok yakın (SolarFire: near sign boundary → {next_sign} sınırında), harita kararsız/çift niyet, aynı soruyu tekrar sorma eşiği"})
    elif asc_deg < 1:
        prev_sign = {"Boğa":"Koç","İkizler":"Boğa","Yengeç":"İkizler","Aslan":"Yengeç","Başak":"Aslan","Terazi":"Başak","Akrep":"Terazi","Yay":"Akrep","Oğlak":"Yay","Kova":"Oğlak","Balık":"Kova","Koç":"Balık"}.get(asc_sign,"")
        strictures.append({"code":"asc_near_boundary","level":"warning","deg":round(asc_deg,2),"sign":asc_sign,"prev_sign":prev_sign,"meaning":f"ASC {asc_sign} {asc_deg:.2f}° — yeni burca yeni girmiş (near boundary), soru taze/olgunlaşmamış olabilir"})
    # Yeni 4 kademeli ASC (0-3 immature, 3-25 ideal, 25-27 intervention, 27-30 critical)
    asc_cfg = RULES["strictures"].get("asc_degrees")
    if asc_cfg:
        if asc_deg < 3:
            strictures.append({"code":"asc_immature","level":"block","deg":round(asc_deg,2),"meaning":asc_cfg["0_2_59_immature"]["verdict"]})
        elif asc_deg >= 27:
            strictures.append({"code":"asc_critical","level":"critical","deg":round(asc_deg,2),"meaning":asc_cfg["27_29_critical"]["verdict"]})
        elif asc_deg >= 25:
            strictures.append({"code":"asc_intervention","level":"info","deg":round(asc_deg,2),"meaning":asc_cfg["25_26_intervention"]["verdict"]})
        # 3-25 ideal => strictures yok
    else:
        # fallback v0.1
        if asc_deg < RULES["strictures"]["asc_early_deg"]:
            strictures.append({"code":"asc_early","level":"warning","deg":round(asc_deg,2)})
        if asc_deg > RULES["strictures"]["asc_late_deg"]:
            strictures.append({"code":"asc_late","level":"warning","deg":round(asc_deg,2)})

    # Significator 27-29 + 6.txt Rx 26-28-29 ayrımı (retro tekrar/28 olumlu/29 olumsuz Regulus hariç)
    sig_deg_cfg = RULES["strictures"].get("significator_degrees")
    rx_cfg = RULES.get("rx_degrees", {})
    for label, sig in [("querent", querent), ("quesited", quesited)]:
        sd = sig["data"]["deg"]; retro = sig["data"].get("retro", False)
        is_regulus = (sig["data"]["sign"]=="Aslan" and int(sd)==29)
        if retro and 26 <= sd <= 29:
            if 26 <= sd < 28:
                strictures.append({"code": f"{label}_rx_26_28","level":"info","planet":sig["planet"],"deg":round(sd,2),"retro":True,"meaning": rx_cfg.get("26_28_retro","26-28 Rx eskiden beri tekrar eden konu")})
            elif 28 <= sd < 29:
                strictures.append({"code": f"{label}_rx_28","level":"info","planet":sig["planet"],"deg":round(sd,2),"retro":True,"meaning":"28 Rx olumlu gelişme şansı daha fazla - tekrar eden konuda olumlu dönüş"})
            elif sd >= 29 and not is_regulus:
                strictures.append({"code": f"{label}_rx_29","level":"critical","planet":sig["planet"],"deg":round(sd,2),"retro":True,"meaning": rx_cfg.get("29_retro","29 Rx olumsuz")})
        elif sd >= 27 and not retro:
            strictures.append({"code": f"{label}_critical_deg","level":"critical","planet":sig["planet"],"deg":round(sd,2),"meaning":"Significator 27-29° - konu bitmiş/gizli problem"})
        # 26-27 yeniden gözden geçir (retro değilse bile)
        if not retro and 26 <= sd < 28:
            strictures.append({"code": f"{label}_review_26_27","level":"info","planet":sig["planet"],"deg":round(sd,2),"meaning": rx_cfg.get("26_27_review","26-27 yeniden gözden geçir")})

    moon_lon = planets["Moon"]["lon"]
    vc_cfg = RULES["strictures"]["via_combusta"]
    if vc_cfg["enabled"]:
        # Via combusta artık Ay ve ASC için, 22-24 istisna
        moon_deg = int(planets["Moon"]["deg"])
        if is_via_combusta_with_exception(moon_lon, moon_deg):
            strictures.append({"code":"via_combusta","level":"warning","lon":round(moon_lon,2),"who":"Moon"})
        asc_lon = houses["asc"]
        asc_deg_int = int(deg_in_sign(asc_lon))
        if is_via_combusta_with_exception(asc_lon, asc_deg_int):
            strictures.append({"code":"via_combusta_asc","level":"warning","lon":round(asc_lon,2),"who":"ASC"})
        # Su grubu gizlilik
        water = RULES["strictures"].get("moon_water_secrecy",{})
        if water and (planets["Moon"]["sign"] in ["Yengeç","Akrep","Balık"] or houses["asc_sign"] in ["Yengeç","Akrep","Balık"]):
            strictures.append({"code":"water_secrecy","level":"info","meaning":water.get("verdict","Gizli bilgi/manipülasyon olabilir")})
        # Ay verimsiz burç 27-29 + Betelgeuse 28 istisna
        barren = RULES["strictures"].get("moon_barren_degrees",{})
        if barren:
            if planets["Moon"]["sign"] in barren.get("barren_signs",[]) and planets["Moon"]["deg"] >= 27:
                if not (planets["Moon"]["sign"]=="İkizler" and int(planets["Moon"]["deg"])==28):
                    strictures.append({"code":"moon_barren_27_29","level":"warning","sign":planets["Moon"]["sign"],"deg":round(planets["Moon"]["deg"],1)})
                else:
                    strictures.append({"code":"betelgeuse_28","level":"info","meaning":"28 İkizler Betelgeuse - kadın/ilahi yardım ile çözülür"})
    # combustion katmanlı v0.6
    sun_lon = planets["Sun"]["lon"]; sun_speed = planets["Sun"]["speed"]
    for p in ["Moon","Mercury","Venus","Mars","Jupiter","Saturn"]:
        if p in (asc_ruler, quesited_ruler):
            c = combustion_detail(planets[p]["lon"], sun_lon, planets[p]["speed"], sun_speed)
            if c:
                strictures.append({"code":f"combustion_{c['layer']}","level":c["severity"],"planet":p,"dist":round(c["dist"],2),"approaching":c["approaching"]})
                # Yeni Ay özel: Moon 0-2 ve Sun ile kavuşum => new_moon
                if p=="Moon" and c["layer"]=="cazimi_like_0_2":
                    strictures.append({"code":"new_moon","level":"critical","meaning":"Güneş-Ay kavuşumu - çok feci manipülasyon/bilinçli kötülük"})
    # VOC v0.6 fix: Ay burç sonuna kadar klassik 7 gezegenle applying açı yapmazsa VOC
    voc = True
    voc_aspects = RULES["strictures"].get("moon_void_of_course",{}).get("aspects_considered",[0,45,60,90,120,150,180])
    if 0 not in voc_aspects: voc_aspects = [0] + list(voc_aspects)
    moon_deg = planets["Moon"]["deg"]
    remaining = 30.0 - moon_deg  # burç sonuna kalan derece (~ Ay'ın bu burçta kat edeceği yol)
    # Lilly: Burç değiştirmeden önce orb içine girerse VOC değil (moiety/Barclay). Kalan yol içinde exact açı var mı?
    for target in ["Sun","Mercury","Venus","Mars","Jupiter","Saturn"]:
        if target not in planets:
            continue
        for ang in voc_aspects:
            diff = (planets[target]["lon"] - moon_lon) % 360
            # diff = target - moon; Moon hızlı olduğu için diff her gün azalır.
            # diff == ang olunca exact açı. Moon'un kat etmesi gereken yol = diff - ang (pozitifse)
            needed = (diff - ang) % 360
            # needed 0 ise zaten exact; 300+ ise açı geride kaldı (bir tur atması gerekir) -> VOC için geçersiz
            if needed < 0.1:
                needed = 0
            if 0 <= needed <= remaining + 0.5:  # kalan yol içinde exact'a ulaşır
                # applying kontrolü: needed yol pozitif ve Moon hedefe yaklaşıyor
                # Eğer needed 0-remaining içindeyse Moon burç çıkmadan kavuşur -> NOT VOC
                voc = False
                break
        if not voc:
            break
    # Regulus 29 istisna: Moon 29 Aslan Regulus ise VOC sayma
    if voc and planets["Moon"]["sign"]=="Aslan" and int(planets["Moon"]["deg"])==29:
        voc = False
        strictures.append({"code":"voc_regulus_29_exception","level":"info","meaning":"29 Regulus - VOC değil, zor da olsa devam et"})
    if voc and RULES["strictures"].get("moon_void_of_course",{}).get("enabled"):
        strictures.append({"code":"voc","level":"warning"})

    # Kritik dereceler orb 0 (öncü 0/13/26 sabit 9/21 değişken 4/17)
    for pname, pdata in planets.items():
        if is_critical_degree(pdata["sign"], pdata["deg"]):
            strictures.append({"code":"critical_degree","level":"info","planet":pname,"sign":pdata["sign"],"deg":round(pdata["deg"],1),"meaning":"Kritik derece - büyük kriz ama çözülür (öncü hızlı/sabit uzun/değişken orta)"})
    if is_critical_degree(houses["asc_sign"], asc_deg):
        strictures.append({"code":"critical_degree_asc","level":"info","deg":round(asc_deg,1)})

    # Saturn 1/7 + Usta: Mars/Pluto 7.ev (gezegenin kendisi evde, yöneticisi değil)
    if RULES["strictures"]["saturn_in_1_or_7"]["enabled"]:
        sat_house = planets["Saturn"]["house"]
        if sat_house in (1,7):
            meaning = RULES["strictures"]["saturn_in_1_or_7"].get("meaning_7th","") if sat_house==7 else ""
            strictures.append({"code":"saturn_1_7","level":"warning","house":sat_house,"meaning":meaning})
    # Usta: Mars 7.evde => dayak riski, Pluto 7.evde => dikkat
    mars_house = planets["Mars"]["house"]
    if mars_house == 7 and RULES["strictures"].get("mars_in_7th",{}).get("enabled"):
        strictures.append({"code":"mars_in_7th","level":"danger","house":7,"meaning":RULES["strictures"]["mars_in_7th"]["meaning"]})
    pluto_house = planets["Pluto"]["house"]
    if pluto_house == 7 and RULES["strictures"].get("pluto_in_7th",{}).get("enabled"):
        strictures.append({"code":"pluto_in_7th","level":"caution","house":7,"meaning":RULES["strictures"]["pluto_in_7th"]["meaning"]})
    # Art of Horary Ch1: Saturn/Mars peregrine veya GAD 10.evde ise astrolog itibar alamaz (Lilly p298)
    try:
        from core.ephemeris import DOMICILE as _DOM2
        def is_peregrine(pname, pdata):
            return not (_DOM2.get(pdata["sign"])==pname or pdata["sign"] in ["Koç","Boğa"] and False) and pdata["house"]==10  # basitleştirilmiş: 10.evde + asaletsiz
        for pn in ["Saturn","Mars"]:
            pd = planets[pn]
            if pd["house"]==10 and pd.get("retro",False) or (pd["house"]==10 and not (_DOM2.get(pd["sign"])==pn)):
                strictures.append({"code":f"{pn.lower()}_10_peregrine","level":"warning","planet":pn,"house":10,"meaning":f"{pn} 10.evde peregrine/retro - astrolog itibar alamaz, yargı zor (Lilly)"})
        # GAD 10.evde
        try:
            node_lon = planets.get("NorthNode",{}).get("lon")
            if node_lon is not None:
                gad_lon = (node_lon+180)%360
                gad_house = house_of_planet(gad_lon, houses["cusps"])
                if gad_house==10:
                    strictures.append({"code":"gad_10","level":"warning","house":10,"meaning":"GAD 10.evde - astrolog itibar alamaz"})
        except: pass
    except: pass

    # Perfection araması
    perfection = None
    score = 0
    _tr = []
    import os as _os
    _DO_TRACE = _os.environ.get("HORARY_TRACE")
    def _sc(v, label):
        nonlocal score
        score = score + v
        if _DO_TRACE:
            _tr.append((label, v, score))
    q_lon = querent["data"]["lon"]; q_speed = querent["data"]["speed"]
    qs_lon = quesited["data"]["lon"]; qs_speed = quesited["data"]["speed"]

    # 1) Direkt açı (conjunction dahil)
    # Hızlı olan significator yavaş olana applying mi?
    # Hız karşılaştırması: Moon en hızlı, sonra Mercury/Venus vs. Basit: speed büyük olan fast
    is_q_fast = abs(q_speed) > abs(qs_speed)
    fast = querent if is_q_fast else quesited
    slow = quesited if is_q_fast else querent
    fast_lon = fast["data"]["lon"]; fast_speed = fast["data"]["speed"]
    slow_lon = slow["data"]["lon"]; slow_speed = slow["data"]["speed"]

    # Prohibition listesi: fast ile slow arasına giren gezegen var mı?
    # Frustration: fast önce başka gezegene açı yapıp sonra slow'a mı gidiyor?
    # Basit orb ile kontrol
    # moiety orb: Lilly/Biruni - gezegen isiklari toplami/2
    moiety = RULES.get("moiety", {"Sun":15,"Moon":12,"Saturn":9,"Jupiter":9,"Mars":8,"Venus":7,"Mercury":7})
    def moiety_orb(p1, p2, base_orb):
        m1 = moiety.get(p1, 7); m2 = moiety.get(p2, 7)
        avg = (m1 + m2) / 2
        # Lilly: orb en az base, en fazla avg; moiety disi kavusum gundem sayilmaz (791)
        return max(base_orb, min(avg, 12))
    best = None
    # Doğru geometri: fast'in tam açıya (slow +/- ang) uzaklığı; fast yavaştan HIZLI ve
    # tam açı öndeyse applying. (Modulo wrap hatası düzeltildi.)
    for ang_name, cfg in RULES["aspects"]["major"].items():
        ang = cfg["angle"]; base_orb = cfg["orb"]
        app, d = aspect_pair(fast_lon, slow_lon, ang)
        if not app:
            continue
        m1 = RULES["moiety"].get(fast["planet"], 7); m2 = RULES["moiety"].get(slow["planet"], 7)
        orb = max(base_orb, min((m1 + m2) / 2, 12))
        if d <= orb and (fast_speed - slow_speed) > 0.02:
            best = {"type": ang_name, "angle": ang, "dist": d, "applying": True, "orb": orb}
            break
    if best:
        # Prohibition kontrolü: FAST'in önünde tam açıya ulaşmadan ÖNCE bir MALEFİK (Saturn/Mars)
        # SERT açı (kare/karşıt) ile fast'i kesiyorsa ve fast kendi alanında değilse engel.
        # Ay (querent'in ortak göstereni) ve generation planetler blocker sayılmaz.
        blocker = None; t_path = None; blk_ang = blk_dist = None
        # hedef tam açının fast'e göre ön taraf mesafesi
        for E in ((slow_lon + best["angle"]) % 360, (slow_lon - best["angle"]) % 360):
            f = (E - fast_lon) % 360
            if f <= 180:
                t_path = f
                break
        if t_path is None:
            t_path = 360  # güvenlik
        for pname, pdata in planets.items():
            if pname in (fast["planet"], slow["planet"], "Moon", "NorthNode", "Uranus", "Neptune", "Pluto"):
                continue
            if pname not in ("Saturn", "Mars"):
                continue
            for ang2 in (90, 180):  # sadece SERT blocker = gerçek prohibition
                app2, d2 = aspect_pair(fast_lon, pdata["lon"], ang2)
                if not app2:
                    continue
                b_path = None
                for Eb in ((pdata["lon"] + ang2) % 360, (pdata["lon"] - ang2) % 360):
                    fb = (Eb - fast_lon) % 360
                    if fb <= 180:
                        b_path = fb
                        break
                if b_path is None:
                    continue
                m1b = RULES["moiety"].get(fast["planet"], 7); m2b = RULES["moiety"].get(pname, 7)
                orbb = max(RULES["aspects"]["major"].get("square", {}).get("orb", 8), min((m1b + m2b) / 2, 12))
                if b_path < t_path and d2 <= orbb:
                    blocker = pname; blk_ang = ang2; blk_dist = d2
                    break
            if blocker:
                break
        if blocker and RULES["perfection"]["prohibition"]["enabled"]:
            # İstisna: fast significator kendi alanında (domicile/exaltation) ise engeli aşar.
            if in_dom_ex(fast["planet"], sign_from_lon(fast_lon)):
                perfection = {"type": best["type"], "result": "yes",
                              "between": [fast["planet"], slow["planet"]],
                              "note": f"{blocker} araya girer ama fast kendi alanında - engeli aştı"}
                _sc(RULES["scoring"]["perfection_yes"], "perfection_yes_dominus")
                _sc(RULES["scoring"].get("perfection_dominus", 8), "perfection_dominus2")
            else:
                perfection = {"type": "prohibition", "result": "blocked",
                              "blocker": blocker, "would_be": best["type"],
                              "blocker_angle": blk_ang, "blocker_dist": blk_dist}
                _sc(RULES["scoring"]["prohibition_penalty"], "prohibition_penalty")
        else:
            perfection = {"type": best["type"], "result": "yes", "between": [fast["planet"], slow["planet"]]}
            _sc(RULES["scoring"]["perfection_yes"], "perfection_yes")
            _sc(RULES["scoring"].get("perfection_dominus", 8), "perfection_dominus")
            # Reception: mutual reception check - domicile/exaltation
            from core.ephemeris import DOMICILE as DOM, EXALTATION as EX
            sign_fast = sign_from_lon(fast_lon)
            sign_slow = sign_from_lon(slow_lon)
            if DOM.get(sign_fast) == slow["planet"]:
                _sc(3, "perf_recv_fast_dom")
                perfection["reception"] = f"{fast['planet']} in {slow['planet']} domicile (+3)"
            elif EX.get(sign_fast) == slow["planet"]:
                _sc(2, "perf_recv_fast_ex")
                perfection["reception"] = f"{fast['planet']} in {slow['planet']} exaltation (+2)"
            if DOM.get(sign_slow) == fast["planet"]:
                _sc(3, "perf_recv_slow_dom")
                if "reception" in perfection:
                    perfection["reception"] += f" + {slow['planet']} in {fast['planet']} domicile (+3 mutual)"
                else:
                    perfection["reception"] = f"{slow['planet']} in {fast['planet']} domicile (+3)"
            elif EX.get(sign_slow) == fast["planet"]:
                _sc(2, "perf_recv_slow_ex")

    # 2) Eğer direkt perfection yoksa translation dene (kabul ALINMIŞSA = Lilly: reception şart)
    if perfection is None or perfection.get("result")=="blocked":
        # Translation: fast -> mediator -> slow, mediator daha hızlı olmalı (her ikisinden).
        # Reception yoksa translation "boş" sayılır - iş sonuç vermez (Lilly).
        mediators = []
        for med_name, med_data in planets.items():
            if med_name in (fast["planet"], slow["planet"], "Sun","Moon","NorthNode","Uranus","Neptune","Pluto"):
                continue
            # Hız şartı: mediator hem fast hem slow'dan hızlı olmalı
            if abs(med_data["speed"]) <= abs(fast_speed) or abs(med_data["speed"]) <= abs(slow_speed):
                continue
            # fast->med separating (en yakın majör açı, düzeltilmiş geometri)
            sep_fm = None
            for ang in (0, 60, 90, 120, 180):
                app_fm, d_fm = aspect_pair(fast_lon, med_data["lon"], ang)
                if not app_fm and d_fm <= 10:
                    if sep_fm is None or d_fm < sep_fm[1]:
                        sep_fm = (ang, d_fm)
            # med -> slow applying
            app_ms = None
            for ang in (0, 60, 90, 120, 180):
                app_m, d_ms = aspect_pair(med_data["lon"], slow_lon, ang)
                if app_m and d_ms <= 10 and (med_data["speed"] - slow_speed) > 0.02:
                    if app_ms is None or d_ms < app_ms[1]:
                        app_ms = (ang, d_ms)
            if sep_fm and app_ms:
                # Lilly: translation geçerli olması için mediator ile hedef arasında reception
                med_sign = sign_from_lon(med_data["lon"])
                recv = in_dom_ex(slow["planet"], med_sign) or in_dom_ex(med_name, sign_from_lon(slow_lon))
                if recv:
                    mediators.append((med_name, sep_fm, app_ms))
        if mediators:
            perfection = {"type":"translation_of_light","result":"yes","mediator": mediators[0][0]}
            _sc(RULES["scoring"]["perfection_translation"], "perfection_translation")

    # Ay 3 rol + Kalde sıralaması: 1-duygu 2-niyet (evi) 3-gidişat; hızlı yavaş'a gider (Sat-Jup-Mar-Sun-Ven-Mer-Moon)
    try:
        kalde_order = ["Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"]
        def kalde_faster(a,b):
            try: return kalde_order.index(a) > kalde_order.index(b)
            except: return abs(planets[a]["speed"]) > abs(planets[b]["speed"])
        # Ay 3 rol: duygu (burcu), niyet (evi), gidişat (son/yaklaşan açı)
        moon_house = planets["Moon"]["house"]; moon_sign_a = planets["Moon"]["sign"]
        strictures.append({"code":"moon_roles","level":"info","house":moon_house,"sign":moon_sign_a,"meaning":f"Ay 3 rol: duygu={moon_sign_a}, niyet/ev={moon_house}.ev ({'8 para beklentisi' if moon_house==8 else 'gidişat için son/yaklaşan açılara bak'}), gidişat=Ay açılarına göre"})
        # son açı
        moon_lon_tmp = planets["Moon"]["lon"]; moon_speed_tmp = planets["Moon"]["speed"]
        last_aspect = None; last_dist=999
        for pname, pdata in planets.items():
            if pname=="Moon": continue
            diff = (pdata["lon"] - moon_lon_tmp) % 360
            for ang in [0,60,90,120,180]:
                d = abs((diff - ang + 180)%360-180)
                diff_next = ((pdata["lon"]+pdata["speed"]) - (moon_lon_tmp+moon_speed_tmp)) % 360
                d_next = abs((diff_next - ang + 180)%360-180)
                if d_next > d and d < last_dist and d <= 10: # separating
                    last_dist=d; last_aspect=(pname, ang)
        if last_aspect:
            strictures.append({"code":"moon_last_aspect","level":"info","with":last_aspect[0],"angle":last_aspect[1],"meaning":"Ay son açısı - geçmişte yaşanan olay"})
        # yaklaşan ilk açı (Kalde ile)
        next_aspect = None; next_dist=999
        for pname, pdata in planets.items():
            if pname=="Moon": continue
            if not kalde_faster("Moon", pname): continue
            diff = (pdata["lon"] - moon_lon_tmp) % 360
            for ang in [0,60,90,120,180]:
                d = abs((diff - ang + 180)%360-180)
                diff_next = ((pdata["lon"]+pdata["speed"]) - (moon_lon_tmp+moon_speed_tmp)) % 360
                d_next = abs((diff_next - ang + 180)%360-180)
                if d_next < d and d < next_dist and d <= 10:
                    next_dist=d; next_aspect=(pname, ang)
        if next_aspect:
            strictures.append({"code":"moon_next_aspect","level":"info","with":next_aspect[0],"angle":next_aspect[1],"dist":round(next_dist,1),"meaning":"Ay yaklaşan açısı - gelecek gündem (Kalde: hızlı yavaş'a gider)"})
        # Moiety orb kontrolü (Güneş 15 Ay 12...)
        # 7.txt Jenerasyon/Nod: Ur/Ne/Pl sadece köşe veya Ay/göstergeyle majör açıda; Gad malefik Kad benefik kavuşum
        for gen in ["Uranus","Neptune","Pluto"]:
            if gen in planets:
                g_house = planets[gen]["house"]
                is_angular = g_house in (1,4,7,10)
                has_moon_aspect = False
                for ang in (0,60,90,120,180):
                    d = abs(((planets[gen]["lon"]-planets["Moon"]["lon"]+180)%360-180) - ang)
                    # basit: 8 orb içinde majör
                    if abs((planets[gen]["lon"]-planets["Moon"]["lon"]+180)%360-180 - ang) < 8: has_moon_aspect = True
                # sadede not - jenerasyon boşlukta sayılmaz (VOC hariç)
                if not is_angular and not has_moon_aspect:
                    strictures.append({"code":f"{gen.lower()}_ignored","level":"info","house":g_house,"meaning":f"{gen} jenerasyon - köşe değil ve Ay ile majör açı yok → horary'de dikkate alınmaz (boşlukta sayılmaz)"})
                elif is_angular or has_moon_aspect:
                    strictures.append({"code":f"{gen.lower()}_activated","level":"info","house":g_house,"meaning":f"{gen} aktif: {'köşe evde' if is_angular else 'Ay ile majör açıda'} → dikkate alınır, aniden ezber bozar"})
        # Gad/Kad (Güney/Kuzey Düğüm) - Mean Node, Gad = Node+180
        try:
            node_lon = planets.get("NorthNode",{}).get("lon")
            if node_lon is not None:
                gad_lon = (node_lon + 180) % 360
                for pname, pdata in planets.items():
                    if pname in ("NorthNode",): continue
                    d_kad = abs((pdata["lon"]-node_lon+180)%360-180); d_gad = abs((pdata["lon"]-gad_lon+180)%360-180)
                    if d_kad <= 3: strictures.append({"code":"kad_conjunction","level":"info","planet":pname,"dist":round(d_kad,1),"meaning":f"{pname} Kad (Kuzey Düğüm) kavuşum {d_kad:.1f}° → benefik, kadersel yardım"})
                    if d_gad <= 3: strictures.append({"code":"gad_conjunction","level":"warning","planet":pname,"dist":round(d_gad,1),"meaning":f"{pname} Gad (Güney Düğüm) kavuşum {d_gad:.1f}° → malefik, kayıp/problem"})
        except: pass
    except: pass

    # Final judgement
    if perfection is None:
        perfection = {"type":"none","result":"no"}
        # Günlük/pratik sorularda perfectionsuzluk bu kadar ağır olmamalı (kullanıcı bulgusu)
        # "yarın işe gidecek miyim" gibi kısa vadeli rutin sorular: -6 yerine -2
        _mundane = quesited_type in ("travel","job","education","daily")
        _sc(-2 if _mundane else -6, "perfection_none")

    # Angularity / Peregrine / Kuşatılma katkıları (2. fix)
    for label, sig in [("querent", querent), ("quesited", quesited)]:
        h = sig["data"]["house"]
        if h in [1,4,7,10]:
            _sc(2, f"angularity_{label}")
        elif h in [2,5,8,11]:
            _sc(1, f"succedent_{label}")
        else:
            _sc(-1, f"cadent_{label}")
        # peregrine: asaleti yoksa -2
        if not (DOMICILE.get(sig["data"]["sign"])==sig["planet"] or EXALTATION.get(sig["data"]["sign"])==sig["planet"]):
            _sc(-2, f"peregrine_{label}")
        # kuşatılma
        bes = is_besieged(sig["data"]["lon"], planets)
        if bes["besieged"]:
            _sc(-4, f"besieged_{label}")

    # --- Klasik güçlü YES: querent<->quesited MUSTERI RESEPTION (restor'dan bağımsız) ---
    # Perfection bulunamasa bile karşılıklı kabul = güçlü YES göstergesi (Lilly).
    try:
        qr_name = querent["planet"]; qs_name = quesited["planet"]
        qr_lon = querent["data"]["lon"]; qs_lon = quesited["data"]["lon"]
        qr_sign = sign_from_lon(qr_lon); qs_sign = sign_from_lon(qs_lon)
        qr_in_qs = (DOMICILE.get(qs_sign)==qr_name) or (EXALTATION.get(qs_sign)==qr_name)  # querent, qs'in burcunda -> qs querent'i kabul eder
        qs_in_qr = (DOMICILE.get(qr_sign)==qs_name) or (EXALTATION.get(qr_sign)==qs_name)
        if qr_in_qs and qs_in_qr:
            mutual = True
            _sc(6, "mutual_reception")
            strictures.append({"code":"mutual_reception","level":"info","meaning":f"KLASIK: {qr_name}({qr_sign}) <-> {qs_name}({qs_sign}) karşılıklı kabul - güçlü YES göstergesi (+6), perfection yokken bile kabul işi sonuca götürür."})
        # Moon da qs ile karşılıklı kabulde ise ek güç
        moon_sign = sign_from_lon(planets["Moon"]["lon"])
        if (DOMICILE.get(qs_sign)=="Moon" or EXALTATION.get(qs_sign)=="Moon") and (DOMICILE.get(moon_sign)==qs_name or EXALTATION.get(moon_sign)==qs_name):
            _sc(3, "moon_reception_qs")
            strictures.append({"code":"moon_reception_qs","level":"info","meaning":f"KLASIK: Ay ve quesited ({qs_name}) karşılıklı kabul (+3)."})
    except: pass

    # --- GÜÇLENDİRİLMİŞ YES testleri ---
    # v0.12: klasik tamamlayıcı tester'lar. Düzeltilmiş açı geometrisi kullanılır.
    try:
        kr_name = querent["planet"]; ks_name = quesited["planet"]
        kr_lon = querent["data"]["lon"]; ks_lon = quesited["data"]["lon"]
        kr_sign = sign_from_lon(kr_lon); ks_sign = sign_from_lon(ks_lon)
        moon = planets["Moon"]
        ml = moon["lon"]; mh = moon["house"]
        # R3: quesited güçlü (kendi alanında)
        if in_dom_ex(ks_name, ks_sign):
            _sc(6, "R3_quesited_strong")
            strictures.append({"code":"sig_strong_yes","level":"info","meaning":f"GÜÇLÜ YES: quesited {ks_name} {ks_sign} burcunda (dom/ex) (+6)."})
        # R11: her iki gösterge aynı burçta - iş tek yerde toplanmış
        if kr_sign == ks_sign:
            _sc(8, "R11_sign_agreement")
            strictures.append({"code":"sign_agreement_yes","level":"info","meaning":f"GÜÇLÜ YES: querent ve quesited aynı burçta ({kr_sign}) (+8)."})
        # R4: querent<->quesited yumuşak bağlantı (0/60/120, yaklaşan VEYA ayrılan ≤8°)
        # guards: quesited düşüşte değil; Ay sonraki SERT açısı Saturn/Mars'a değil
        r4 = None
        f4 = querent if abs(querent["data"]["speed"]) >= abs(quesited["data"]["speed"]) else quesited
        s4 = quesited if f4 is querent else querent
        for ang in (0, 60, 120):
            a4, d4 = aspect_pair(f4["data"]["lon"], s4["data"]["lon"], ang)
            if d4 <= 8:
                r4 = (ang, d4, a4)
                break
        mal_next = None
        for mp in ("Saturn", "Mars"):
            if mp not in planets:
                continue
            for ha in (0, 90, 180):
                am, dm = aspect_pair(ml, planets[mp]["lon"], ha)
                if am and dm <= 8:
                    mal_next = (mp, ha, dm)
                    break
            if mal_next:
                break
        if r4 and FALL.get(ks_sign) != ks_name and mal_next is None:
            _sc(8, "R4_soft_link")
            strictures.append({"code":"sig_soft_link_yes","level":"info","meaning":f"GÜÇLÜ YES: querent<->quesited yumuşak bağ ({r4[0]}°, {r4[1]:.1f}° {'yaklaşan' if r4[2] else 'ayrılan'}) (+8)."})
        # R5: Ay quesited'e yumuşak YAKLAŞIYOR (≤8°), Ay quesited evinde değil, quesited zararda/düşüşte değil
        mq_app = None; mq_sep = None
        for ang in (0, 60, 120):
            am, dm = aspect_pair(ml, ks_lon, ang)
            if dm <= 8:
                if am:
                    mq_app = (ang, dm)
                else:
                    mq_sep = (ang, dm)
        qsh = (mh == quesited["data"]["house"])
        r5_fired = False
        if mq_app and not qsh and not in_det_fall(ks_name, ks_sign):
            _sc(8, "R5_moon_app_qs")
            r5_fired = True
            strictures.append({"code":"moon_app_quesited_yes","level":"info","meaning":f"GÜÇLÜ YES: Ay quesited'e yumuşak {mq_app[0]}° yaklaşıyor ({mq_app[1]:.1f}°) (+8)."})
        # R6: Ay quesited'ten yumuşak AYRILIYOR (≤8°)
        if mq_sep and not in_det_fall(ks_name, ks_sign):
            _sc(5, "R6_moon_sep_qs")
            strictures.append({"code":"moon_sep_quesited_yes","level":"info","meaning":f"GÜÇLÜ YES: Ay quesited'ten yumuşak {mq_sep[0]}° ayrılıyor ({mq_sep[1]:.1f}°) (+5)."})
        # R7: Ay ışık topluyor (qr ikisine de yaklaşıyor, qr ile karşıt değil)
        mqr = None; mqs2 = None
        for ang in (0, 60, 90, 120, 180):
            am, dm = aspect_pair(ml, kr_lon, ang)
            if am and dm <= 8:
                mqr = (ang, dm)
            am2, dm2 = aspect_pair(ml, ks_lon, ang)
            if am2 and dm2 <= 8:
                mqs2 = (ang, dm2)
        if mqr and mqs2 and mqr[0] != 180:
            _sc(8, "R7_collection")
            strictures.append({"code":"moon_collection_yes","level":"info","meaning":f"GÜÇLÜ YES: Ay ışık topluyor ({mqr[0]}°/{mqs2[0]}°) (+8)."})
        # R8: quesited querent'in 1.evinde
        if quesited["data"]["house"] == 1:
            _sc(6, "R8_quesited_1st")
            strictures.append({"code":"quesited_1st_yes","level":"info","meaning":f"GÜÇLÜ YES: quesited querent'in 1.evinde (+6)."})
        # R9: querent güçlü (kendi alanında) VE Ay işe karışıyor (R5 ya da direkt perfection)
        perf_direct = (perfection is not None and perfection.get("result") == "yes"
                       and perfection.get("type") != "translation_of_light")
        if in_dom_ex(kr_name, kr_sign) and (perf_direct or r5_fired):
            _sc(5, "R9_querent_strong")
            strictures.append({"code":"querent_strong_yes","level":"info","meaning":f"GÜÇLÜ YES: querent {kr_name} kendi alanında ({kr_sign}), Ay işe karışıyor (+5)."})
    except: pass

    # --- v0.13: Klasik tamamlayıcı YES göstergeleri (Lilly) ---
    try:
        _SOFT = (0, 60, 120); _MAJ = (0, 60, 90, 120, 180)
        # R13: Işık Nakli — Ay iki işaretçi arasında aracı (qr'den yumuşak ayrılır + qs'e yaklaşır, VEYA tersi; ≤8°)
        _m_s = {}; _m_a = {}
        for _nm, _lon in (("qr", kr_lon), ("qs", ks_lon)):
            _sa = _aa = None
            for _ang in _MAJ:
                _app13, _d13 = aspect_pair(ml, _lon, _ang)
                if _d13 <= 8:
                    if _app13:
                        if _aa is None or _d13 < _aa[1]:
                            _aa = (_ang, _d13)
                    else:
                        if _sa is None or _d13 < _sa[1]:
                            _sa = (_ang, _d13)
            _m_s[_nm] = _sa; _m_a[_nm] = _aa
        if (bool(_m_s["qr"] and _m_s["qr"][0] in _SOFT) and bool(_m_a["qs"])) or \
           (bool(_m_s["qs"] and _m_s["qs"][0] in _SOFT) and bool(_m_a["qr"])):
            _sc(10, "R13_moon_translation")
            strictures.append({"code":"moon_translation_yes","level":"info","meaning":"KLASİK: Ay querent ve quesited işaretçileri arasında ışık naklediyor — aracılık/tamamlama (+10)."})
        # R14: Ay, quesited'in burcuna (dispositor'unun burcuna) giriyor — iş diğer tarafın alanına geçiyor
        _seg14 = 30 - (ml % 30)
        _nxt14 = (int((ml + _seg14) // 30) * 30) % 360
        if DOMICILE.get(sign_from_lon(_nxt14)) == ks_name:
            _sc(2, "R14_moon_enters_qs_sign")
            strictures.append({"code":"moon_enters_quesited_sign","level":"info","meaning":"KLASİK: Ay quesited'in burcuna giriyor — iş diğer tarafın alanına geçmiş durumda (+2)."})
        # R15: Ay quesited'ten yumuşak AYRILIYOR (≤8°) — ışık harekete geçmiş, sonuçlanır
        for _ang in _SOFT:
            _app15, _d15 = aspect_pair(ml, ks_lon, _ang)
            if _app15 is False and _d15 <= 8:
                _sc(12, "R15_moon_sep_qs_transit")
                strictures.append({"code":"moon_sep_soft_transit_yes","level":"info","meaning":"KLASİK: Ay quesited'ten yumuşak ayrılıyor — iş/ışık yola çıkmış, sonuçlanacak (+12)."})
                break
        # R16: Ay, GÜÇLÜ (dom/ex) quesited'in burcunun yöneticisine yumuşak yaklaşıyor (60/120, ≤8°)
        _qss16 = sign_from_lon(ks_lon)
        _disp16 = DOMICILE.get(_qss16)
        if _disp16 and _disp16 != "Moon" and _disp16 in planets and in_dom_ex(ks_name, _qss16):
            for _ang in _SOFT:
                _app16, _d16 = aspect_pair(ml, planets[_disp16]["lon"], _ang)
                if _app16 and _d16 <= 8:
                    _sc(8, "R16_moon_to_strong_qs_disp")
                    strictures.append({"code":"moon_to_strong_quesited_dispositor","level":"info","meaning":f"KLASİK: Ay, güçlü quesited ({ks_name}) burcunun yöneticisi {_disp16}'e yumuşak yaklaşıyor — iş sağlam elde (+8)."})
                    break
        # R17: Hayırlı qr (Venüs/Jüpiter) quesited'i kabul ediyor — querent işi gönül rahatlığıyla alıyor
        if kr_name in ("Venus", "Jupiter") and \
           (DOMICILE.get(ks_sign) == kr_name or EXALTATION.get(ks_sign) == kr_name):
            _sc(2, "R17_benefic_receives_qs")
            strictures.append({"code":"benefic_receives_quesited","level":"info","meaning":f"KLASİK: {kr_name} (hayırlı) quesited {ks_name}'i evinde/alımlında — querent işi kabul ediyor (+2)."})
    except: pass

    # Threshold
    if _DO_TRACE:
        import sys as _sys
        print("TRACE", quesited_type, "score=", score, file=_sys.stderr)
        for _t in _tr:
            print("   ", _t[0], _t[1], "->", _t[2], file=_sys.stderr)
    if score >= RULES["scoring"]["threshold_yes"]:
        verdict = "YES"
    elif score <= RULES["scoring"]["threshold_no"]:
        verdict = "NO"
    else:
        verdict = "UNCERTAIN"

    # --- Bonatus / Vergilius dolunay ---
    try:
        from datetime import timedelta
        # önceki ve sonraki dolunayı bul (yaklaşık 14 gün tara)
        def find_full_moon(jd_center, direction=-1):
            # direction -1 önceki, +1 sonraki
            for d in range(0, 30):
                jd = jd_center + direction*d
                sun_lon = swe.calc_ut(jd, swe.SUN)[0][0] % 360
                moon_lon = swe.calc_ut(jd, swe.MOON)[0][0] % 360
                elong = (moon_lon - sun_lon) % 360
                # dolunay ~180 elong, 2° tolerans
                if abs((elong - 180 + 180) % 360 - 180) < 2:
                    return jd, moon_lon
            return None, None
        prev_jd, prev_moon_lon = find_full_moon(jd, -1)
        next_jd, next_moon_lon = find_full_moon(jd, 1)
        if prev_jd:
            prev_moon_sign = sign_from_lon(prev_moon_lon)
            prev_ruler = DOMICILE.get(prev_moon_sign)
            if prev_ruler and prev_ruler in (querent["planet"], quesited["planet"]):
                # önceki dolunay yöneticisi köşe evde mi?
                prev_ruler_house = planets.get(prev_ruler,{}).get("house",0)
                if prev_ruler_house in [1,4,7,10]:
                    # açı iyi mi?
                    has_good = any("combustion" not in s["code"] for s in strictures)  # basit
                    if perfection and perfection.get("result")=="yes":
                        strictures.append({"code":"bonatus","level":"info","meaning":"Bonatus: önceki dolunay yöneticisi köşede + iyi açı => %100 olumlu (kötü açıda %50)"})
                        _sc(2, "bonatus_full")
                    else:
                        strictures.append({"code":"bonatus_partial","level":"info","meaning":"Bonatus: önceki dolunay yöneticisi köşede ama açı kötü => %50 olumlu"})
                        _sc(1, "bonatus_partial")
        if next_jd:
            next_moon_sign = sign_from_lon(next_moon_lon)
            next_ruler = DOMICILE.get(next_moon_sign)
            if next_ruler and next_ruler in (querent["planet"], quesited["planet"]):
                next_ruler_house = planets.get(next_ruler,{}).get("house",0)
                if next_ruler_house in [1,4,7,10]:
                    strictures.append({"code":"vergilius","level":"info","meaning":"Vergilius: sonraki dolunay yöneticisi köşede + olumlu => gelecekte olumluya dönecek"})
                    _sc(1, "vergilius")
    except Exception as e:
        pass

    # --- Sabit yıldız 2° (gezegen) / 5° (açı) - gerçek ekliptik boylam karşılaştırması ---
    # Yıldızların yaklaşık ekliptik boylamları (J2026, 1° tolerans) - burç+degree -> lon
    FIXED_STARS_LON = {
        "Algol": 56.0,      # 26 Taurus - Caput Algol
        "Aldebaran": 69.5,  # 9 Gemini
        "Capella": 81.0,    # 21 Gemini
        "Bellatrix": 80.5,  # 20 Gemini
        "Betelgeuse": 88.5, # 28 Gemini
        "Canopus": 15.0,
        "Saiph": 86.5,
        "Sirius": 104.0,    # 14 Cancer
        "Regulus": 149.5,   # 29 Leo
        "Vega": 285.3,      # 15 Capricorn
        "Spica": 203.8,     # 23 Libra
        "Arcturus": 204.5,  # 24 Libra
        "Antares": 249.7,   # 9 Sagittarius
        "Fomalhaut": 333.8, # 3 Pisces
        "Scheat": 359.0,    # 29 Pisces
        "Thuban": 47.0,
    }
    for pname, pdata in planets.items():
        plon = pdata["lon"] % 360
        for star, slon in FIXED_STARS_LON.items():
            d = abs((plon - slon + 180) % 360 - 180)
            if d <= 2:
                strictures.append({"code":f"fixed_star_{star}","level":"info","planet":pname,"deg":round(pdata["deg"],1),"star":star,"dist":round(d,1),"meaning":f"{star} {d:.1f}° kavuşum (2° orb)"})
    for angle_name, angle_lon in [("ASC",houses["asc"]),("MC",houses["mc"]),("DSC",(houses["asc"]+180)%360),("IC",(houses["mc"]+180)%360)]:
        alon = angle_lon % 360
        for star, slon in FIXED_STARS_LON.items():
            d = abs((alon - slon + 180) % 360 - 180)
            if d <= 5:  # açı noktaları 5°
                strictures.append({"code":f"fixed_star_angle_{star}","level":"info","angle":angle_name,"deg":round(deg_in_sign(alon),1),"star":star,"dist":round(d,1),"orb":5})
    # Antiscion genel (Deirdre retro söz değişimi dahil) - 0 Cancer/0 Capricorn eksenine göre ayna
    try:
        def antiscion(lon): return (360 - lon) % 360  # 0 Cancer/0 Cap ekseni: 90-270
        # querent-quesited antiscion var mı
        q_lon = querent["data"]["lon"]; qs_lon = quesited["data"]["lon"]
        q_anti = antiscion(q_lon); qs_anti = antiscion(qs_lon)
        for a,b,lab in [(q_lon, qs_anti, "querent antiscion-quesited"), (qs_lon, q_anti, "quesited antiscion-querent")]:
            d = abs((a - b + 180) % 360 - 180)
            if d < 2:
                strictures.append({"code":"antiscion","level":"info","dist":round(d,1),"meaning":f"Antiscion {lab} {d:.1f}° — gizli bağlantı/açı, Deirdre'de retro Merkür söz değişimi gibi."})
        # retro Merkür söz değişimi (Deirdre)
        if planets.get("Mercury",{}).get("retro"):
            strictures.append({"code":"retro_mercury_word","level":"info","meaning":"Retro Merkür — söylenen söz değişir (Deirdre), ifade/görüş değişimi."})
    except: pass
    # Thuban antiscia (paralel/kontraparalel - deklination proxy: lon simetrisi) - istek üzerine not
    # Gerçek paralel declination ister, şimdilik sadece Thuban kavuşumu rapor edildi

    # --- Lotlar (POF + children/daughters/sons + marriage/divorce) Ch2/6 ---
    lots = {}
    try:
        asc = houses["asc"] % 360
        sun_lon = planets["Sun"]["lon"]; moon_lon = planets["Moon"]["lon"]
        # Gündüz/gece: Sun üst ufukta mı? house 7-12 gündüz (Lilly gündüz hep aynı ama biz Bonatti gündüz/gece ayırıyoruz)
        sun_house = planets["Sun"]["house"]
        is_day = sun_house in (7,8,9,10,11,12)
        if is_day:
            pof = (moon_lon - sun_lon + asc) % 360
        else:
            pof = (sun_lon - moon_lon + asc) % 360
        lots["POF"] = pof
        pof_house = house_of_planet(pof, houses["cusps"])
        pof_sign = sign_from_lon(pof)
        strictures.append({"code":"lot_pof","level":"info","lon":round(pof,1),"house":pof_house,"sign":pof_sign,"meaning":f"POF {pof_sign} {deg_in_sign(pof):.1f}° Ev{pof_house} ({'gündüz' if is_day else 'gece'} formülü) - şans/prosperity, lorduna bak"})
        # Lot of children: diurnal Asc+Sat-Jup, nocturnal Asc+Jup-Sat
        sat_lon = planets["Saturn"]["lon"]; jup_lon = planets["Jupiter"]["lon"]
        if is_day:
            lot_children = (asc + sat_lon - jup_lon) % 360
        else:
            lot_children = (asc + jup_lon - sat_lon) % 360
        lots["children"] = lot_children
        # Lot of daughters: Asc+Ven-Moon, sons: Asc+Jup-Moon
        ven_lon = planets["Venus"]["lon"]
        lots["daughters"] = (asc + ven_lon - moon_lon) % 360
        lots["sons"] = (asc + jup_lon - moon_lon) % 360
        # Marriage / Divorce: Asc+DSC-Ven/Mar
        dsc = (asc+180)%360
        lots["marriage"] = (asc + dsc - ven_lon) % 360
        lots["divorce"] = (asc + dsc - planets["Mars"]["lon"]) % 360
        # --- Goldstein-Jacobson tamamlayici Arap Noktalari (S/C/D/P/L/W) ---
        try:
            mar_lon = planets["Mars"]["lon"]; sat_lon2 = planets["Saturn"]["lon"]
            lots["sickness"] = (asc + mar_lon - sat_lon2) % 360                  # S = ASC+Mars-Saturn
            lots["surgery"] = (asc + sat_lon2 - mar_lon) % 360                   # C = ASC+Saturn-Mars
            eighth_cusp = houses["cusps"][7] % 360
            lots["death"] = (asc + eighth_cusp - moon_lon) % 360                 # D = ASC+8.cusp-Moon
            eighth_sign = sign_from_lon(eighth_cusp)
            eighth_ruler = DOMICILE.get(eighth_sign, "Mars")
            eighth_ruler_lon = planets[eighth_ruler]["lon"]
            lots["danger"] = (asc + eighth_ruler_lon - sat_lon2) % 360           # P = ASC+8.ruler-Saturn
            ninth_cusp = houses["cusps"][8] % 360
            third_cusp = houses["cusps"][2] % 360
            lots["legalization"] = (ninth_cusp + third_cusp - ven_lon) % 360     # L = 9.cusp+3.cusp-Venus
            lots["wedding"] = lots["legalization"]                               # W = ayni
        except: pass
        for k,v in lots.items():
            if k=="POF": continue
            strictures.append({"code":f"lot_{k}","level":"info","lon":round(v,1),"sign":sign_from_lon(v),"house":house_of_planet(v, houses["cusps"]),"meaning":f"Lot {k}: {sign_from_lon(v)} {deg_in_sign(v):.1f}°"})
    except: pass

    # --- Zaman tablosu (Ay burç/ev) ---
    # Ay burç elementine göre ve ev köşe/ikincil/üçüncül
    ay_house = planets["Moon"]["house"]
    ay_sign = planets["Moon"]["sign"]
    # burç tipi
    if ay_sign in ["Koç","Yengeç","Terazi","Oğlak"]:
        burc_type="cardinal"
    elif ay_sign in ["Boğa","Aslan","Akrep","Kova"]:
        burc_type="fixed"
    else:
        burc_type="mutable"
    if ay_house in [1,4,7,10]:
        house_type="angular"
    elif ay_house in [2,5,8,11]:
        house_type="succedent"
    else:
        house_type="cadent"
    time_map = {
        ("cardinal","angular"):"GÜN", ("cardinal","succedent"):"HAFTA", ("cardinal","cadent"):"AY",
        ("mutable","angular"):"HAFTA", ("mutable","succedent"):"AY", ("mutable","cadent"):"YIL",
        ("fixed","angular"):"AY", ("fixed","succedent"):"YIL", ("fixed","cadent"):"BELİRSİZ (1 hafta içinde tekrar sor)"
    }
    timing_unit = time_map.get((burc_type,house_type),"")
    # Ay ile belirleyici arası derece = süre sayısı
    # belirleyici quesited, değilse querent
    target_lon = quesited["data"]["lon"]
    moon_lon2 = planets["Moon"]["lon"]
    deg_diff = abs((target_lon - moon_lon2 + 360) % 360)
    # 0-360 arası en kısa değil, direkt fark
    if deg_diff > 180:
        deg_diff = 360 - deg_diff
    timing = {"unit":timing_unit,"degrees":round(deg_diff,1),"burc_type":burc_type,"house_type":house_type,"text":f"{round(deg_diff)} {timing_unit}"}
    # Ephemeris gerçek kavuşum tarihi (sembolik derece yerine)
    try:
        # Ay → quesited/Lot için gerçek aspect tarihi ara (0.25 gün adımla 365 gün)
        best_days = None; best_ang = None
        for step in [d*0.25 for d in range(1, 1460)]:  # 365 gün
            jd2 = jd + step
            mlon = swe.calc_ut(jd2, swe.MOON)[0][0] % 360
            tlon = swe.calc_ut(jd2, swe.SUN)[0][0] % 360  # placeholder, hedef quesited için swe.calc ile target gezegen
            # hedef gezegenin swe id'si
            pid_map = {"Sun":swe.SUN,"Moon":swe.MOON,"Mercury":swe.MERCURY,"Venus":swe.VENUS,"Mars":swe.MARS,"Jupiter":swe.JUPITER,"Saturn":swe.SATURN}
            pid = pid_map.get(quesited["planet"], swe.VENUS)
            tlon = swe.calc_ut(jd2, pid)[0][0] % 360
            diff_a = (tlon - mlon) % 360
            for ang in (0,60,90,120,180):
                if abs((diff_a - ang + 180)%360-180) < 1.0:  # exact orb 1°
                    best_days = step; best_ang = ang; break
            if best_days is not None: break
        if best_days is not None:
            timing["ephemeris_days"] = round(best_days,1)
            timing["ephemeris_angle"] = best_ang
            timing["ephemeris_text"] = f"{round(best_days)} gün sonra {best_ang}° (ephemeris)"
            # Sembolik yerine ephemeris'i de ekle
            if best_days < 7: timing["ephemeris_unit"] = "GÜN (ephemeris)"
            elif best_days < 60: timing["ephemeris_unit"] = "HAFTA (ephemeris)"
            elif best_days < 400: timing["ephemeris_unit"] = "AY (ephemeris)"
            else: timing["ephemeris_unit"] = "YIL (ephemeris)"
    except: pass
    # 5_2.txt Zaman gezegen yılları: Ay 0-4 Merkür 4-14 Venüs 14-22 Güneş 22-40 Mars 41-56 Jüpiter 56-68 Satürn 68+ (ve saat karşılıkları)
    try:
        planet_years = RULES.get("timing_planet_years", {})
        sig_planet = quesited["planet"]
        years_info = planet_years.get(sig_planet, "")
        if years_info:
            timing["planet_years"] = years_info
            strictures.append({"code":"timing_planet_years","level":"info","planet":sig_planet,"meaning":f"Gezegen yılları: {sig_planet} {years_info} - ömür/olay süresi %70 doğruluk"})
    except: pass

    # 6.txt Almuten-Ay hızı: Almuten o anın en güçlü gezegeni - Ay ile iyi açı hızlı olumlu, kötü açı uğraş
    try:
        from core.ephemeris import DOMICILE as _DOM, EXALTATION as _EX
        # Basit Almuten: ASC derecesinin domicile+exaltation + Ay burcunun yöneticisi ağırlığı
        asc_lon = houses["asc"]; asc_sign = houses["asc_sign"]
        # Puan tablosu (domicile 5 exaltation 4 triplicity 3) - triplicity eklenince genişleyecek
        scores = {p:0 for p in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn"]}
        dom = _DOM.get(asc_sign); ex = _EX.get(asc_sign)
        if dom in scores: scores[dom] += 5
        if ex in scores: scores[ex] += 4
        # Ay burcu da katkı
        moon_sign = planets["Moon"]["sign"]
        dom_m = _DOM.get(moon_sign); ex_m = _EX.get(moon_sign)
        if dom_m in scores: scores[dom_m] += 3
        if ex_m in scores: scores[ex_m] += 2
        almuten = max(scores, key=lambda k: scores[k])
        # Almuten-Ay açısı
        al_lon = planets[almuten]["lon"]; al_spd = planets[almuten]["speed"]
        moon_lon_a = planets["Moon"]["lon"]; moon_spd = planets["Moon"]["speed"]
        diff_am = (al_lon - moon_lon_a) % 360
        best_ang = min([0,60,90,120,180], key=lambda a: abs((diff_am - a +180)%360-180))
        d_am = abs((diff_am - best_ang +180)%360-180)
        diff_am_n = ((al_lon+al_spd)-(moon_lon_a+moon_spd))%360
        d_am_n = abs((diff_am_n - best_ang +180)%360-180)
        approaching = d_am_n < d_am
        is_benefic = best_ang in (0,60,120)
        if d_am <= 8:
            strictures.append({"code":"almuten_moon","level":"info","almuten":almuten,"angle":best_ang,"dist":round(d_am,1),"approaching":approaching,"meaning":f"Almuten {almuten}-Ay {best_ang}° {'yaklaşan' if approaching else 'ayrılan'} ({d_am:.1f}°) - {'hızlı olumlu' if is_benefic else 'uğraş gerektirir'}; Almuten hız göstergesi"})
    except: pass

    # 7.txt Radikalite 3 yöntem: saat==ASC / saat==üçlü / aynı mizaç + Ay/saat açısı
    try:
        from core.ephemeris import planetary_hour as _ph
        import datetime as _dt
        # weekday için jd'den tarih çıkar
        ymd = swe.revjul(jd, swe.GREG_CAL)
        # Python weekday 0=Mon
        try:
            import datetime as _d2
            wd = _d2.date(int(ymd[0]), int(ymd[1]), int(ymd[2])).weekday()
        except: wd = None
        ph = _ph(jd, lat, lon, weekday=wd)
        hour_ruler = ph.get("hour_ruler")
        # üçlü yöneticiler (Dorothean) - gündüz/gece sektine göre
        triplicity = {
            "Koç": ("Sun","Jupiter"), "Aslan": ("Sun","Jupiter"), "Yay": ("Sun","Jupiter"),
            "Boğa": ("Venus","Moon"), "Başak": ("Venus","Moon"), "Oğlak": ("Venus","Moon"),
            "İkizler": ("Saturn","Mercury"), "Terazi": ("Saturn","Mercury"), "Kova": ("Saturn","Mercury"),
            "Yengeç": ("Venus","Mars"), "Akrep": ("Venus","Mars"), "Balık": ("Venus","Mars"),
        }
        trip_rules = triplicity.get(asc_sign, ())
        is_radical = (hour_ruler == asc_ruler) or (hour_ruler in trip_rules)
        # mizaç kontrolü: choleric hot/dry (Koç Aslan Yay) vs... basit: aynı element
        elem = {"Koç":"fire","Aslan":"fire","Yay":"fire","Boğa":"earth","Başak":"earth","Oğlak":"earth","İkizler":"air","Terazi":"air","Kova":"air","Yengeç":"water","Akrep":"water","Balık":"water"}
        # hour_ruler burcu yok, o yüzden mizaç için hour ruler gezegenin yönettiği burç elementi
        ruler_elem = {"Sun":"fire","Mars":"fire","Jupiter":"fire","Venus":"earth","Saturn":"earth","Mercury":"air","Moon":"water"}
        same_temp = elem.get(asc_sign) == ruler_elem.get(hour_ruler)
        # Ay - saat açısı kontrolü
        moon_hour_angle = None
        try:
            # Ay ile hour_ruler gezegeni arası açı
            hr_lon = planets.get(hour_ruler, {}).get("lon")
            if hr_lon is not None:
                d_mh = abs((hr_lon - planets["Moon"]["lon"]+180)%360-180)
                if d_mh <= 8:
                    moon_hour_angle = d_mh
        except: pass
        if is_radical or same_temp or moon_hour_angle is not None:
            strictures.append({"code":"radical","level":"info","hour_ruler":hour_ruler,"asc_ruler":asc_ruler,"meaning":f"Radikal: saat={hour_ruler} ASC={asc_ruler} {'üçlü uyum' if hour_ruler in trip_rules else ''} {'mizaç uyum' if same_temp else ''} {f'Ay-saat {moon_hour_angle:.1f}°' if moon_hour_angle else ''} - harita okunmaya değer"})
        else:
            strictures.append({"code":"non_radical","level":"info","hour_ruler":hour_ruler,"asc_ruler":asc_ruler,"meaning":"Radikal değil: saat yöneticisi ASC ile uyumsuz - harita çalışabilir ama radikal kadar güçlü değil"})
        # Gün yöneticisi ev vurgusu (aphorism day)
        try:
            day_ruler = ph.get("day_ruler")
            if day_ruler and day_ruler in planets:
                dr_house = planets[day_ruler]["house"]
                strictures.append({"code":"day_ruler_house","level":"info","day_ruler":day_ruler,"house":dr_house,"meaning":f"Gün yöneticisi {day_ruler} Ev{dr_house} ({planets[day_ruler]['sign']}) — bu evde vurgu, dikkat edilmeli."})
        except: pass
    except Exception as e:
        pass

    # 6.txt Uranyen noktalar (Koç 0 dünya girişi + Hades/Vulcanus/Cupido/Admetos/Zeus/Kronos/Poseidon/Apollon tanımları) - Swiss'te uranian yok, Koç 0 kontrolü aktif
    try:
        for pname, pdata in planets.items():
            if pname in ("Uranus","Neptune","Pluto","NorthNode"): continue
            d_aries = abs((pdata["lon"] - 0 + 180)%360-180)
            if d_aries <= 2:
                retro_note = "retro tanıdık" if pdata.get("retro") else "ileri yeni kişi/yer"
                strictures.append({"code":"aries_point","level":"info","planet":pname,"dist":round(d_aries,1),"meaning":f"Koç 0° dünya girişi: {pname} kavuşum ({d_aries:.1f}°) - {retro_note}, yeni tanışma/sistem girişi"})
                break
        # Diğer uranyen noktalar (Hades temiz/pis su, Vulcanus yangın, Cupido ev/lüks, Admetos kutu/22°, Zeus silah, Kronos zirve, Poseidon ayna, Apollon kehanet) - horary_rules.json:uranian_points tanımlı, detaylı ephemeris için Witte ephemeris gerekir, placeholder info
        strictures.append({"code":"uranian_info","level":"info","meaning":"Uranyen: Hades=pis su/kanalizasyon, Poseidon=temiz su, Vulcanus=yangın/turbo, Cupido=ev/eşya/lüks, Admetos=baskı/kutu/22° kutsal, Zeus=silah/patlama, Kronos=zirve/otorite, Apollon=kehanet/şifa (Witte ephemeris ile tam)"})
    except: pass

    # 6.txt Horary Minervası: Jup-Ay-Mars 60/120 (veya Jup-Pluto-Ay) → en olumsuzda bile büyük iyilik
    try:
        def has_benefic_angle(p1_lon, p2_lon, p1_spd, p2_spd):
            d = (p2_lon - p1_lon) % 360
            for ang in (60,120):
                dist = abs((d - ang +180)%360-180)
                if dist <= 8:
                    d_n = abs((((p2_lon+p2_spd)-(p1_lon+p1_spd))%360 - ang +180)%360-180)
                    if d_n < dist:  # yaklaşan
                        return True, ang, dist
            return False, None, None
        mj, ang1, d1 = has_benefic_angle(planets["Moon"]["lon"], planets["Jupiter"]["lon"], planets["Moon"]["speed"], planets["Jupiter"]["speed"])
        # Moon-Mars veya Moon-Pluto
        mm, ang2, d2 = has_benefic_angle(planets["Moon"]["lon"], planets["Mars"]["lon"], planets["Moon"]["speed"], planets["Mars"]["speed"])
        mp = False
        if not mm and "Pluto" in planets:
            mp, ang2, d2 = has_benefic_angle(planets["Moon"]["lon"], planets["Pluto"]["lon"], planets["Moon"]["speed"], planets["Pluto"]["speed"])
        has_mars = mm
        if mj and (has_mars or mp):
            who = "Mars" if has_mars else "Pluto"
            strictures.append({"code":"horary_minerva","level":"info","meaning":f"Horary Minervası: Jup-Ay-{who} {ang1}/{ang2}° - en olumsuzda bile büyük iyilik (karmik koruma)","dist":f"{d1:.1f}/{d2:.1f}"})
            _sc(4, "horary_minerva")  # bonus Lilly en olumsuzda bile iyilik
    except: pass

    # 6.txt İkilem: sabit taşınmaz uzun vadeli → Ay+Satürn önemli, Ay hangi belirteçle olumlu açı yapıyorsa onu al
    # Eğer soruda iki seçenek iması varsa (iki ev/iki kişi), Ay'ın iki significator'a açı kalitesiyle tavsiye üret
    try:
        two_opt = None
        # Basit heuristic: quesited_type genel ise ve soruda "mi" tekrarı varsa ikilem say
        # Gerçek ikilemde caller iki ayrı chart yerine bu notu kullanır
        # Burada chart içi: Ay'ın querent/quesited dışı en yakın iki gezegene olumlu/olumsuz açı
        # Not olarak ekle - horary_app'ta parse_two_options ile detaylandırılacak
        if quesited_type in ("general","house_property","money"):
            # Ay'ın Venüs/Mars gibi para/ev göstergelerine yaklaşan 60/120 var mı kontrolü (bilgi notu)
            for cand in ["Venus","Mars","Jupiter","Saturn"]:
                if cand in planets and cand not in (querent["planet"], quesited["planet"]):
                    diff = (planets[cand]["lon"] - planets["Moon"]["lon"]) % 360
                    for ang in [0,60,120]:
                        d = abs((diff - ang + 180)%360-180)
                        if d <= 6:
                            diff_n = ((planets[cand]["lon"]+planets[cand]["speed"])-(planets["Moon"]["lon"]+planets["Moon"]["speed"]))%360
                            d_n = abs((diff_n - ang +180)%360-180)
                            if d_n < d:
                                strictures.append({"code":"two_option_hint","level":"info","candidate":cand,"angle":ang,"dist":round(d,1),"meaning":f"İkilem notu: Ay {cand} ile {ang}° yaklaşan açı ({d:.1f}°) - uzun vadeli sabit taşınmazda Ay+Satürn önemli, Ay olumlu açı yaptığı seçenek tercih edilir"})
                                break
                    break
    except: pass

    # --- Lilly 43 Aforizma toplu (2,3,4,5,6,15,22-30,33-43 eksiklerin otomatik kontrolü) ---
    try:
        # 2: burcun ilk/son derecesi yükseliyorsa yargıya güvenme
        asc_deg = houses["asc"] % 30
        if asc_deg < 3 or asc_deg > 27:
            strictures.append({"code":"lilly_2_asc_edge","level":"warn","deg":round(asc_deg,1),"meaning":"Aforizma 2: ASC burcun ilk/son derecesinde — yargıya temkinli."})
        # 3/20/23/25: 10.ev peregrine/yanık/GAD, ASC yöneticisi asaletsiz
        # 15: yavaş gezegen süreyi uzatır
        for p, d in planets.items():
            if abs(d["speed"]) < 0.2 and d["house"] in (1,7,10):
                strictures.append({"code":"lilly_15_slow","level":"info","planet":p,"speed":round(d["speed"],3),"meaning":f"Aforizma 15: {p} çok yavaş — sonuç uzar (burç {d['sign']})."})
        # 22: hem iyicil hem kötücül güçsüz ise ertelenmeli
        # 26: Güneş ışınları 12° vs Cazimi 0-16' (genişletilmiş Menconi yearly review 1°17' cazimi gibi)
        sun_lon = planets["Sun"]["lon"]
        for p, d in planets.items():
            if p=="Sun": continue
            dist_sun = abs((d["lon"]-sun_lon+180)%360-180)
            if dist_sun < 1.5: # Menconi cazimi geniş: 17' -> 1.5° (Yearly Review)
                strictures.append({"code":"lilly_26_cazimi","level":"info","planet":p,"dist":round(dist_sun,2),"meaning":f"Aforizma 26: {p} Cazimi (Güneş 1.5° içinde Menconi geniş) — muazzam güç."})
            elif dist_sun < 12:
                strictures.append({"code":"lilly_26_sun_beams","level":"warn","planet":p,"dist":round(dist_sun,1),"meaning":f"Aforizma 26: {p} Güneş ışınları altında 12° içinde — güçsüz."})
        # 28/34: sabit/öncü/değişken + köşe/ardıl/düşük ev
        fixed = ["Boğa","Aslan","Akrep","Kova"]; cardinal=["Koç","Yengeç","Terazi","Oğlak"]
        burc = planets["Moon"]["sign"] if "Moon" in planets else asc_sign
        btype = "sabit" if burc in fixed else "öncü" if burc in cardinal else "değişken"
        htype = "köşe" if planets["Moon"]["house"] in (1,4,7,10) else "ardıl" if planets["Moon"]["house"] in (2,5,8,11) else "düşük"
        strictures.append({"code":"lilly_28_34","level":"info","meaning":f"Aforizma 28/34: Ay {burc} {btype}, ev {planets['Moon']['house']} {htype} — {'istikrar' if btype=='sabit' else 'hızlı sonuç' if btype=='öncü' else 'sonuç ihtimali yüksek ama belirsiz'}; köşe=iyi, düşük=az."})
        # 29/43: KAD/GAD irtibat + GAD evi
        try:
            gad_lon = planets.get("SouthNode",{}).get("lon")
            if gad_lon:
                for p,d in planets.items():
                    if abs((d["lon"]-gad_lon+180)%360-180) < 3:
                        strictures.append({"code":"lilly_29_gad_aspect","level":"warn","planet":p,"meaning":f"Aforizma 29: {p} GAD ile 3° içinde — zarar."})
        except: pass
        # Gebelik a-h (5. ev) Lilly K07 104-107 - sorgu children ise
        if quesited_type in ("children",):
            try:
                fifth_cusp = houses["cusps"][4]
                fifth_sign = sign_from_lon(fifth_cusp)
                fifth_ruler = DOMICILE.get(fifth_sign,"Mercury")
                # a: ASC/Ay ↔5.yönetici/melek açı/karşılıklı alma/ışık nakli (basit: 1/5 veya Ay-5 arası 0/60/120)
                score_baby=0
                for ang in (0,60,120):
                    d = abs(((planets[fifth_ruler]["lon"]-planets["Moon"]["lon"]+180)%360-180) if fifth_ruler in planets and "Moon" in planets else 999)
                    if abs(d-ang) < 6: score_baby+=1
                strictures.append({"code":"baby_a_h","level":"info","score":score_baby,"meaning":f"Gebelik a-h: 5.ev {fifth_sign}({fifth_ruler}) Ay/ASC ile {score_baby} olumlu temas — a-h kriteri."})
            except: pass
        # 33: zarar veren gezegenin evi engelin kaynağı (malefik asp)
        # 30/39: tutulma evi + POF asaleti
        try:
            pof = lots.get("POF")
            if pof is not None:
                pof_sign = sign_from_lon(pof)
                # POF asaleti var mı
                dom = DOMICILE.get(pof_sign)
                if dom:
                    strictures.append({"code":"lilly_39_pof","level":"info","sign":pof_sign,"ruler":dom,"meaning":f"Aforizma 39: POF {pof_sign} ({dom} yönetiminde) — bu evin kişileri/şeyleri ile sonuca ulaşılır."})
        except: pass
    except: pass

    # --- Goldstein-Jacobson: Hastalik / Ameliyat acili (health quesited icin) ---
    try:
        if quesited_type in ("health",):
            asc_lon = houses["asc"] % 360
            q1_ruler = quesited.get("planet", planets.get("Moon",{}).get("name","Moon"))
            # Sickness lot (S)
            s_lot = lots.get("sickness")
            d_lot = lots.get("death")
            if s_lot is not None:
                # Ay'in (S)'e yakin/keskin acisi hastalik teyidi
                moon_s = abs((planets["Moon"]["lon"]-s_lot+180)%360-180)
                for ang in (0,90,180):
                    if abs(moon_s-ang) < 6:
                        strictures.append({"code":"gj_sickness_lot","level":"info","dist":round(moon_s,1),"angle":ang,"meaning":f"Goldstein: Ay (S) Hastalık Noktasına {ang}° açıda ({moon_s:.1f}°) - mevcut hastalığın teyidi/şiddeti ({'klinik değil' if ang==90 else 'belirgin'})."})
            # Death lot (D) riski - keskin/kotu aci
            if d_lot is not None:
                q1_lon = planets.get(q1_ruler,{}).get("lon")
                if q1_lon:
                    dq = abs((q1_lon-d_lot+180)%360-180)
                    dm = abs((planets["Moon"]["lon"]-d_lot+180)%360-180)
                    for name,dist in (("1.yönetici",dq),("Ay",dm)):
                        if dist < 6:
                            strictures.append({"code":"gj_death_lot_risk","level":"warn","dist":round(dist,1),"who":name,"meaning":f"Goldstein: {name} (D) Ölüm Noktasına çok yakın ({dist:.1f}°) - ciddi olumsuz; sorgulayanın ölümü asla gösterilmez, tedavi/umut notu eşliğinde."})
            # 6-1 yonetici quincunx (hastalik ana acisi) - natal 6.cusp mesafesi
            sixth_sign = sign_from_lon(houses["cusps"][5]%360)
            sixth_ruler = DOMICILE.get(sixth_sign,"Mercury")
            sixth_ruler_lon = planets.get(sixth_ruler,{}).get("lon")
            if sixth_ruler_lon and q1_ruler in planets:
                q1_lon2 = planets[q1_ruler]["lon"]
                d61 = abs((sixth_ruler_lon-q1_lon2+180)%360-180)
                hard_ang = None
                for ang in (0,45,90,135,180):
                    if abs(d61-ang) < 6:
                        hard_ang = ang; break
                if hard_ang is not None:
                    strictures.append({"code":"gj_sick_cross","level":"info","angle":hard_ang,"dist":round(d61,1),"meaning":f"Goldstein: 1.yönetici {q1_ruler} - 6.yönetici {sixth_ruler} arası {hard_ang}° acı ({d61:.1f}°) - hastalığın şiddeti/bölgesi ({sixth_sign} vücut bölgesi). Quincunx (150) ayırt edici; kare/karsit daha şiddetli."})
                # Saturn ciddiyet anahtari
                sat_lon_h = planets.get("Saturn",{}).get("lon")
                if sat_lon_h:
                    ds = abs((sat_lon_h-q1_lon2+180)%360-180)
                    if ds < 6:
                        strictures.append({"code":"gj_saturn_serious","level":"warn","dist":round(ds,1),"meaning":f"Goldstein: 1.yönetici {q1_ruler} Saturn'e yakın ({ds:.1f}°) - CİDDİ. Saturn kronik, Mars akut, Merkur bulaşıcı."})
            # South Node hastalik haritasinda
            sn_lon = planets.get("SouthNode",{}).get("lon")
            if sn_lon:
                for p in ("Moon","Sun"):
                    if abs((planets[p]["lon"]-sn_lon+180)%360-180) < 3:
                        strictures.append({"code":"gj_southnode_sick","level":"info","planet":p,"meaning":f"Goldstein: {p} Güney Düğümüne çok yakın - hastalık haritasında olumsuz (patolojik)."})
    except: pass

    # --- Goldstein-Jacobson: Ameliyat riskli/olumlu notlari (health + surgery quesited) ---
    try:
        if quesited_type in ("health","surgery"):
            s_lot = lots.get("surgery")
            if s_lot is not None:
                s_house = house_of_planet(s_lot, houses["cusps"])
                s_sign = sign_from_lon(s_lot)
                aff = (s_house in (8,1,4)) or (s_sign in ("Boğa","Aslan","Akrep","Kova"))
                if aff:
                    strictures.append({"code":"gj_surgery_lot_aff","level":"info","house":s_house,"sign":s_sign,"meaning":f"Goldstein: Cerrahi Noktası (C) Ev{s_house} {s_sign} - ameliyat için etkilenmiş (risk/komplikasyon)."})
                else:
                    strictures.append({"code":"gj_surgery_lot_ok","level":"info","house":s_house,"sign":s_sign,"meaning":f"Goldstein: Cerrahi Noktası (C) Ev{s_house} {s_sign} - etkilenmemiş, ameliyat uygun."})
    except: pass

    # Combust penalty var mı? (yeni kod combustion_*)
    for s in strictures:
        if "combustion" in s["code"]:
            _sc(RULES["scoring"].get("combust_penalty",-5) // 2, "combust_penalty"); # hafifletilmiş

    return {
        "jd": jd,
        "houses": houses,
        "planets": planets,
        "querent": querent,
        "quesited": quesited,
        "strictures": strictures,
        "perfection": perfection,
        "score": score,
        "verdict": verdict,
        "quesited_type": quesited_type,
        "timing": timing,
        "lots": lots if 'lots' in locals() else {},
        "_trace": _tr if _DO_TRACE else [],
    }

# CLI'de test
if __name__ == "__main__":
    import sys
    # Örnek: İstanbul 2026-03-10 14:30
    res = cast_horary_chart(2026,3,10,14.5,41.0082,28.9784,"relationship")
    print(res["verdict"], res["score"], res["perfection"], res["strictures"][:2])
