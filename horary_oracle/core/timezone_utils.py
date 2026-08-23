"""Timezone & şehir - FBST app.py'den kopya, bağımsız."""
import json, os
from datetime import datetime

try:
    from timezonefinder import TimezoneFinder
    _tzf = TimezoneFinder()
except ImportError:
    _tzf = None

try:
    import pytz as _pytz
except ImportError:
    _pytz = None

def _turkiye_offset(yil, ay, gun):
    if yil > 2016:
        return 3
    # eski DST logic sade
    return 3 if 4 <= ay <= 9 else 2

def otomatik_utc_offset(lat, lon, yil, ay, gun, saat=12):
    # Türkiye için düzeltme - pytz Etc/GMT veriyor, hatalı
    if 35 <= lat <= 43 and 25 <= lon <= 45:
        return float(_turkiye_offset(yil, ay, gun)), "Europe/Istanbul"
    if _tzf is not None and _pytz is not None:
        try:
            tz_name = _tzf.timezone_at(lat=lat, lng=lon)
            if not tz_name:
                tz_name = _tzf.closest_timezone_at(lat=lat, lng=lon)
            if tz_name:
                tz = _pytz.timezone(tz_name)
                dt = tz.localize(datetime(yil, ay, gun, int(saat), int((saat % 1)*60)))
                return dt.utcoffset().total_seconds()/3600, tz_name
        except Exception:
            pass
    tahmin = round(lon/15.0)
    return max(-12, min(12, int(tahmin))), "Etc/GMT"

def load_cities():
    p = os.path.join(os.path.dirname(__file__), "cities_db.json")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
