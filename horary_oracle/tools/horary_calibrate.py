# -*- coding: utf-8 -*-
"""HORARY KALİBRASYON CLI — motorun öğrenme katmanı.

Komutlar:
  list                       mevcut kayıtları göster
  add <gerçek_bilgi_json>    vaka ekle (json dosya yolu)
  stats                      yön/mesafe hata istatistiği (genel + tip bazlı)
  fit                        veriden ev/burç/gezegen ağırlıklarını öğren (>=4 vaka)
  tohum                      seed Kırıkkale veya şehir çifti kaydı ekle

Örn:
  python horary_oracle/tools/horary_calibrate.py stats
  python horary_oracle/tools/horary_calibrate.py add vaka.json
  python horary_oracle/tools/horary_calibrate.py fit
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from engine.horary_distance import (
    HoraryCalibration, fit_direction_weights, load_weights, model_stats,
    save_weights, geographic_distance, geographic_bearing, CITY_COORDINATES,
    HoraryDistanceEngine,
)
from engine.horary_questions import classify_question

CAL = HoraryCalibration()
CAL.load()


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
    elif cmd == "tohum":
        cmd_tohum()
    else:
        print("Bilinmeyen komut. list | add <json> | stats | fit | tohum")