import csv, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","core"))
from engine.horary_engine import cast_horary_chart
from core.timezone_utils import otomatik_utc_offset

# Soru -> quesited ev haritasi (horary_rules.json quesited_map ile uyumlu)
QUESITED_BY_KEYWORD = {
    "marriage": "marriage", "wife": "marriage", "husband": "marriage", "partner": "relationship",
    "ex return": "ex_return", "ex_return": "ex_return",
    "ship": "travel", "travel": "travel",
    "office": "job", "job": "job", "promotion": "job",
    "money lent": "money", "money borrow": "money", "money": "money", "debt": "money",
    "child": "child", "birth": "child", "gender": "child",
    "sick": "health", "disease": "health", "health": "health", "recovery": "health", "cure": "health",
    "lawsuit": "lawsuit", "court": "lawsuit",
    "house": "house_property", "property": "house_property",
    "thief": "thief", "stolen": "thief", "lost": "lost_object", "ring": "lost_object", "horse": "lost_object",
    "prison": "lawsuit", "sibling": "sibling", "brother": "sibling",
    "treasure": "money", "venture": "money", "exams": "education",
}
def guess_quesited(q: str) -> str:
    ql = q.lower()
    for k, v in QUESITED_BY_KEYWORD.items():
        if k in ql:
            return v
    return "general"

rows=list(csv.DictReader(open(os.path.join(os.path.dirname(__file__),"lilly_35.csv"),encoding="utf-8")))
ok=0; total=0
for r in rows:
    d=r["date_gregorian"].split("-")
    y,m,da=map(int,d)
    h,mn=map(int,r["time"].split(":"))
    dec=h+mn/60
    lat=float(r["lat"]); lon=float(r["lon"])
    # JD/UTC fix: <1900 için LMT (lon/15), yoksa tzdb
    if y < 1900:
        off = round(lon/15, 2)
    else:
        try:
            off, _ = otomatik_utc_offset(lat, lon, y, m, da, dec)
        except: off = round(lon/15, 2)
    utc_dec = dec - off
    qtype = guess_quesited(r["question"])
    res=cast_horary_chart(y,m,da,utc_dec,lat,lon,qtype)
    total+=1
    # PARTIAL -> YES/NO tolerans
    exp=r["expected_verdict"]
    got=res["verdict"]
    match = (exp==got) or (exp=="PARTIAL" and got in ("YES","NO","UNCERTAIN"))
    if match: ok+=1
    print(f"{r['id']:2s} {r['question'][:18]:18s} exp:{exp:7s} got:{got:9s} score:{res['score']:3d} perf:{res['perfection']['type']:10s} {'OK' if match else 'FARK'}")
print(f"\nRegresyon: {ok}/{total} eslesti ({ok/total*100:.0f}%)")
