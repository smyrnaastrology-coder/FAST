"""
Horary Oracle FastAPI - Yüksek Performans
- LRU cache (ephemeris + chart) ~200ms -> ~5ms
- Async + orjson
- Streamlit'ten bağımsız, Flutter APK direkt çağırır
"""
import os, sys, time
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
    # opsiyonel: client kendi zamanını gönderirse
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[float] = None  # local decimal

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
    else:
        now = datetime.now()
        y, mo, da = now.year, now.month, now.day
        local_dec = now.hour + now.minute/60 + now.second/3600
    off, tzname = otomatik_utc_offset(req.lat, req.lon, y, mo, da, local_dec)
    utc_dec = local_dec - off
    return y, mo, da, utc_dec, off, tzname, local_dec

@app.get("/api/health", response_model=HealthResponse)
async def health():
    return {"status":"ok","version":"1.0.0"}

@app.post("/api/horary/cast")
async def cast(req: CastRequest):
    t0 = time.perf_counter()
    y, mo, da, utc_dec, off, tzname, local_dec = resolve_time(req)

    # quesited auto - genel (derived engine içinde question ile override ediliyor)
    qtype = "general"
    try:
        res = cached_chart(y, mo, da, utc_dec, req.lat, req.lon, qtype)
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

    # location (yer bulma) - is_self / is_live mantığı
    loc_info = {}
    try:
        from engine.location_engine import direction_by_house, distance_fixed
        q = req.question.lower()
        is_self = "ben" in q and any(k in q for k in ["nerede","nerde","nere"])
        use_data = res['querent']['data'] if is_self else res['quesited']['data']
        actual_house = use_data['house']
        loc_info = {
            "direction": direction_by_house(actual_house),
            "house": actual_house,
            "distance": f"{distance_fixed(req.lat, use_data['deg'], actual_house, req.lat>0)[0]:.0f}{distance_fixed(req.lat, use_data['deg'], actual_house, req.lat>0)[1]}",
        }
    except: pass

    # LLM sadece tercüman
    engine_json = {
        "verdict": res["verdict"], "score": res["score"],
        "perfection": res["perfection"], "timing": res.get("timing"),
        "strictures": res["strictures"],
        "querent": res["querent"]["planet"], "quesited": res["quesited"]["planet"],
        "question": req.question, "location": loc_info
    }
    answer = call_openai(engine_json, req.lang)

    dt = (time.perf_counter()-t0)*1000
    return {
        "verdict": res["verdict"], "score": res["score"],
        "perfection": res["perfection"], "timing": res.get("timing"),
        "querent": res["querent"], "quesited": res["quesited"],
        "houses": {"asc": res["houses"]["asc"], "asc_sign": res["houses"]["asc_sign"], "mc": res["houses"]["mc"]},
        "strictures": res["strictures"][:12],
        "lots": res.get("lots",{}),
        "location": loc_info,
        "answer": answer,
        "meta": {"tz": tzname, "utc_offset": off, "local_dec": round(local_dec,2), "ms": round(dt,1)}
    }

# Render start: uvicorn horary_oracle.api:app --host 0.0.0.0 --port $PORT
