# -*- coding: utf-8 -*-
"""HORARY KALİBRASYON CLI — motorun öğrenme katmanı.

Komutlar:
  list                       mevcut kayıtları göster
  add <gerçek_bilgi_json>    vaka ekle (json dosya yolu)
  stats                      yön/mesafe hata istatistiği (genel + tip bazlı)
  fit                        veriden ev/burç/gezegen ağırlıklarını öğren (>=4 vaka; <1km oda kayıtları yön fit'inden hariç)
  ladder                     ölçek katmanı merdiveni (kayıtların k değerleri hangi katmanda kümeleniyor)
  tohum                      seed Kırıkkale veya şehir çifti kaydı ekle

  goal-add <json>            spor gol dakikası maçı ekle (cusps + goal_minutes)
  goal-list                  maç kayıtlarını göster
  goal-fit                   gol dakikası modelini öğren (dakika = a*mark + b)
  goal-stats                 gol kalibrasyon güven raporu (yetersizse dakika verilmez)

Örn:
  python horary_oracle/tools/horary_calibrate.py stats
  python horary_oracle/tools/horary_calibrate.py add vaka.json
  python horary_oracle/tools/horary_calibrate.py fit
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from engine.horary_distance import (
    HoraryCalibration, fit_direction_weights, load_weights, model_stats,
    save_weights, geographic_distance, geographic_bearing, CITY_COORDINATES,
    HoraryDistanceEngine, DEFAULT_SCALE_TIERS,
    fit_direction_bias, load_direction_bias, save_direction_bias,
)
from engine.horary_questions import classify_question

CAL = HoraryCalibration()
CAL.load()

# Spor gol dakikasi kalibrasyonu (ayri depo: horary_sport_calibration.json)
from engine.sport_calibration import (
    SportCalibration, fit_goal_params, save_params, load_params,
    assess as goal_assess, degree_marks,
)
GOALS = SportCalibration()
GOALS.load()


def _json_print(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_list():
    print(f"{len(CAL.records)} kayit:")
    for r in CAL.records:
        print(f"  #{r['_id']} {r.get('question_type')}  {r.get('origin')} -> {r.get('destination')}  "
              f"H{r.get('house')} {r.get('significator')}  angular={r.get('angular_difference')}  "
              f"gercek={r.get('real_distance_km')}km/{r.get('real_bearing')}°")


def cmd_add(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f) if isinstance(json.load(f), dict) else {"records": json.load(f)}
    if "records" in data:
        for r in data["records"]:
            CAL.add_record(**r)
    else:
        CAL.add_record(**data)
    CAL.save()
    print(f"Kayit eklendi. Toplam {len(CAL.records)}.")


def cmd_stats():
    _json_print(model_stats(CAL.records))


def cmd_fit():
    res = fit_direction_weights(CAL.records)
    if res.get("fitted"):
        save_weights(res["weights"])
        print(f"Ağırlıklar öğrenildi: ev {res['weights']['house']} / burç {res['weights']['sign']} / "
              f"gezegen {res['weights']['planet']} | ort yön hatası {res['mean_err_deg']}° (n={res['n']})")
        print("  kaydedildi -> horary_weights.json")
    else:
        print(f"Ağırlık öğrenilemedi: {res['reason']}")


def cmd_biasfit():
    """Tip bazlı yön sapmasını öğren (>=4 kayıtlı tipler genellenir, şeffaf çıktı)."""
    res = fit_direction_bias(CAL.records)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if res.get("bias"):
        save_direction_bias(res["bias"])
        print("  kaydedildi -> horary_bias.json")
    else:
        print(f"Sapma öğrenilemedi: {res['n']} kullanılabilir vaka (< {MIN_FIT_RECORDS}?)")


def cmd_tohum():
    """Kullanıcının verdiği gerçek konumdan seed kaydı oluştur (koordinat + qtype)."""
    lat, lon = float(input("Soru konumu lat: ")), float(input("Soru konumu lon: "))
    city = input("Gerçek konum şehri: ").strip()
    if city.title() not in CITY_COORDINATES:
        print(f"Bilinmeyen şehir (şu bilinenler: {', '.join(sorted(CITY_COORDINATES))})")
        return
    while True:
        q = input("Soru metni (qtype otomatik): ").strip()
        label = classify_question(q) if q else None
        print(f"  -> qtype: {label['type'] if label else 'BİLİNEMEDİ'} ({label['label'] if label else 'manual verilecek'})")
        if label:
            break
        q2 = input("  tekrar (ya da qtype= koy: friend/spouse/child/mother/father/teacher/student/sibling): ").strip()
        if q2.startswith("qtype="):
            q = f"_ {q2.split('=', 1)[1]}"
    c0 = CITY_COORDINATES[city.title()]
    dm = round(geographic_distance(lat, lon, *c0), 1)
    br = round(geographic_bearing(lat, lon, *c0), 2)
    print(f"Gerçek: {dm} km / {br}°")
    CAL.add_record(question_type=label['type'] if label else q.split("=")[1],
                   origin=f"{lat},{lon}", destination=city.title(),
                   angular_difference=float(input("angular fark (haritadan): ")),
                   real_distance_km=dm, real_bearing=br)
    CAL.save()
    print(f"Seed kaydı #{CAL.records[-1]['_id']} eklendi. Toplam {len(CAL.records)}.")


def cmd_ladder():
    """Ölçek katmanı merdiveni: each kaydın Δθ·M'ye göre katman dağılımı."""
    tiers = {}
    for r in CAL.records:
        base = CAL._base_value(r)
        if not base:
            continue
        k = float(r["real_distance_km"]) / base
        tier = min(DEFAULT_SCALE_TIERS, key=lambda t: abs(math.log10(DEFAULT_SCALE_TIERS[t]) - math.log10(k)))
        tiers.setdefault(tier, []).append((r["_id"], round(k, 4)))
    out = {"likely_tier": CAL.likely_tier(), "tiers": {}}
    for t, rows in sorted(tiers.items(), key=lambda kv: kv[0]):
        out["tiers"][t] = {"n": len(rows), "k_ornekleri": rows[:8]}
    _json_print(out)


# ---------------- SPOR GOL DAKİKASI KALİBRASYONU ----------------
def cmd_goal_list():
    print(f"{len(GOALS.records)} maç kaydı:")
    for r in GOALS.records:
        print(f"  #{r['_id']} {r.get('match','?')} {r.get('date','')} "
              f"goller={r.get('goal_minutes')} marks={[round(m,1) for m in (r.get('marks') or [])][:6]}...")


def cmd_goal_add(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("records") if isinstance(data, dict) else data
    if rows is None:
        rows = [data]
    for r in rows:
        GOALS.add_record(**r)
    GOALS.save()
    print(f"Maç eklendi. Toplam {len(GOALS.records)}. "
          f"(marks türetildi: {bool(GOALS.records[-1].get('marks'))})")


def cmd_goal_fit():
    res = fit_goal_params(GOALS.records)
    if res.get("fitted"):
        save_params(res)
        print(f"Gol modeli: dakika = {res['a']}*mark + {res['b']}  |  "
              f"ortalama sapma {res['mae']} dk (n={res['n']})")
        print("  kaydedildi -> horary_sport_goal_params.json")
    else:
        print(f"Model öğrenilemedi: {res['reason']} (n={res['n']})")


def cmd_goal_stats():
    trust = goal_assess(GOALS.records, load_params())
    _json_print({"kayit_sayisi": len(GOALS.records),
                 "params": load_params(), "guven": trust})


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        cmd_list()
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("Kullanım: horary_calibrate.py add <json>"); sys.exit(1)
        cmd_add(sys.argv[2])
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "fit":
        cmd_fit()
    elif cmd == "ladder":
        cmd_ladder()
    elif cmd == "goal-list":
        cmd_goal_list()
    elif cmd == "goal-add":
        if len(sys.argv) < 3:
            print("Kullanım: horary_calibrate.py goal-add <json>"); sys.exit(1)
        cmd_goal_add(sys.argv[2])
    elif cmd == "goal-fit":
        cmd_goal_fit()
    elif cmd == "goal-stats":
        cmd_goal_stats()
    elif cmd == "tohum":
        cmd_tohum()
    else:
        print("Bilinmeyen komut. list | add <json> | stats | fit | ladder | "
              "goal-list | goal-add <json> | goal-fit | goal-stats | tohum")