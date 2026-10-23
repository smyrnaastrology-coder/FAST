# read and append biwheel
path = r'C:\Users\LENOVO\Desktop\FBST_Project\render-deploy\backend\main.py'
s = open(path,'r',encoding='utf-8').read()
if 'charts_biwheel' in s:
    print('exists')
    raise SystemExit

add = r'''

class ChartBiwheelIn(BaseModel):
    isim: Optional[str] = None
    natal_tarih: str
    natal_saat: str = "12:00"
    natal_lat: float = 41.0082
    natal_lon: float = 28.9784
    natal_tz: Optional[float] = None
    hedef_tarih: str
    hedef_saat: str = "12:00"
    lat: float = 41.0082
    lon: float = 28.9784
    tz: Optional[float] = None
    house_system: str = "P"


@app_fast.post("/api/charts/biwheel")
def charts_biwheel(inp: ChartBiwheelIn):
    try:
        hsys = (inp.house_system or "P").upper().strip()
        if hsys not in _CHART_HSYS_MAP:
            hsys = "P"

        ephe_yolu = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ephe')
        if os.path.isdir(ephe_yolu):
            swe.set_ephe_path(ephe_yolu)

        # natal
        nt = inp.natal_tarih.split("-")
        ns = inp.natal_saat.split(":")
        ny = int(nt[0]); nm = int(nt[1]); nd = int(nt[2])
        nhh = int(ns[0]); nmm = int(ns[1]) if len(ns) > 1 else 0
        nuo = 3.0 if inp.natal_tz is None else float(inp.natal_tz)
        jd_n = swe.julday(ny, nm, nd, nhh + nmm / 60.0 - nuo)
        ncusps, nasc = swe.houses_ex(jd_n, float(inp.natal_lat), float(inp.natal_lon), _CHART_HSYS_MAP[hsys])
        ncusps_list = [float(ncusps[i]) for i in range(12)]

        natal_planets = []
        for key, pid in _CHART_PLANETS:
            try:
                arr, _ = swe.calc_ut(jd_n, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)
                lonv = _chart_normalize_deg(arr[0])
                speed = float(arr[3]) if len(arr) > 3 else 0.0
                info = _chart_sign_info(lonv)
                h = _chart_house_of(lonv, ncusps_list)
                natal_planets.append({
                    "ad": key,
                    "lon": round(lonv, 4),
                    "burc": info["burc"],
                    "derece": info["derece"],
                    "ev": h,
                    "hiz": round(speed, 4),
                    "retro": speed < 0,
                })
            except Exception:
                continue

        n_asc_deg = _chart_normalize_deg(nasc[0]); n_mc_deg = _chart_normalize_deg(nasc[1])
        n_asc = {"lon": round(n_asc_deg, 4), **_chart_sign_info(n_asc_deg)}
        n_mc = {"lon": round(n_mc_deg, 4), **_chart_sign_info(n_mc_deg)}
        natal_evler = []
        for i in range(12):
            c = _chart_normalize_deg(ncusps_list[i])
            natal_evler.append({"no": i + 1, "lon": round(c, 4), **_chart_sign_info(c)})

        # transit
        tt = inp.hedef_tarih.split("-")
        ts = inp.hedef_saat.split(":")
        ty = int(tt[0]); tm = int(tt[1]); td = int(tt[2])
        thh = int(ts[0]); tmm = int(ts[1]) if len(ts) > 1 else 0
        tuo = 3.0 if inp.tz is None else float(inp.tz)
        jd_t = swe.julday(ty, tm, td, thh + tmm / 60.0 - tuo)
        tcusps, tasc = swe.houses_ex(jd_t, float(inp.lat), float(inp.lon), _CHART_HSYS_MAP[hsys])
        tcusps_list = [float(tcusps[i]) for i in range(12)]

        trans_planets = []
        for key, pid in _CHART_PLANETS:
            try:
                arr, _ = swe.calc_ut(jd_t, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)
                lonv = _chart_normalize_deg(arr[0])
                speed = float(arr[3]) if len(arr) > 3 else 0.0
                info = _chart_sign_info(lonv)
                h = _chart_house_of(lonv, tcusps_list)
                trans_planets.append({
                    "ad": key,
                    "lon": round(lonv, 4),
                    "burc": info["burc"],
                    "derece": info["derece"],
                    "ev": h,
                    "hiz": round(speed, 4),
                    "retro": speed < 0,
                })
            except Exception:
                continue

        t_asc_deg = _chart_normalize_deg(tasc[0]); t_mc_deg = _chart_normalize_deg(tasc[1])
        t_asc = {"lon": round(t_asc_deg, 4), **_chart_sign_info(t_asc_deg)}
        t_mc = {"lon": round(t_mc_deg, 4), **_chart_sign_info(t_mc_deg)}
        trans_evler = []
        for i in range(12):
            c = _chart_normalize_deg(tcusps_list[i])
            trans_evler.append({"no": i + 1, "lon": round(c, 4), **_chart_sign_info(c)})

        aspects_between = []
        for tp in trans_planets:
            for np in natal_planets:
                for ang, atype, orb_max in _CHART_MAJOR_ASPECTS:
                    diff = abs(_chart_wrap180(tp["lon"] - np["lon"] - ang))
                    if diff <= orb_max:
                        aspects_between.append({
                            "p1": tp["ad"], "p2": np["ad"], "tip": atype,
                            "orb": round(diff, 2), "katman": "transit-natal"
                        })
                        break
        aspects_between.sort(key=lambda x: x["orb"])

        return {
            "ok": True,
            "house_system": hsys,
            "natal": {
                "julian_day_ut": round(jd_n, 6),
                "asc": n_asc,
                "mc": n_mc,
                "gezegenler": natal_planets,
                "evler": natal_evler,
                "meta": {"isim": inp.isim, "tarih": inp.natal_tarih, "saat": inp.natal_saat, "lat": inp.natal_lat, "lon": inp.natal_lon}
            },
            "transit": {
                "julian_day_ut": round(jd_t, 6),
                "asc": t_asc,
                "mc": t_mc,
                "gezegenler": trans_planets,
                "evler": trans_evler,
                "meta": {"tarih": inp.hedef_tarih, "saat": inp.hedef_saat, "lat": inp.lat, "lon": inp.lon}
            },
            "acilar_arasi": aspects_between,
            "meta": {"isim": inp.isim, "natal_tarih": inp.natal_tarih, "natal_saat": inp.natal_saat, "hedef_tarih": inp.hedef_tarih, "hedef_saat": inp.hedef_saat}
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
old = '@app_fast.get("/api/debug_ephe")'
if old not in s:
    print('no')
    raise SystemExit
s2 = s.replace(old, add + '\n\n@app_fast.get("/api/debug_ephe")')
open(path,'w',encoding='utf-8').write(s2)
print('added')
