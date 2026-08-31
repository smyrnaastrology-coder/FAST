# -*- coding: utf-8 -*-
"""HORARY LOKASYON MOTORU testleri — soru tipi, turned-house, yön, mesafe, kalibrasyon.

Çalıştır: python -m pytest horary_oracle/tests/test_horary_location.py -v
veya:    python horary_oracle/tests/test_horary_location.py

GÜVENLİK KURALI: bu testler geçici kalibrasyon dosyası kullanır; asıl
horary_calibration.json'a DOKUNMAZ (fit/apply testleri kendi kalibrasyonunu kurar).
"""
import sys, os, json, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from engine.horary_distance import (
    HoraryDistanceEngine, HoraryCalibration, condition_factor, fit_direction_weights,
    geographic_bearing, geographic_distance, km_category, load_weights, model_stats,
    verify_prediction, MIN_FIT_RECORDS,
)
from engine.horary_questions import (
    classify_question, parse_nested, turned_house, QUESTION_HOUSES, NESTED_PERSON,
)


def test_classify_question_basics():
    assert classify_question("arkadaşım nerede?")["type"] == "friend"
    assert classify_question("öğrencim nerede?")["type"] == "student"
    assert classify_question("üniversitede hoca Yasin nerede?")["type"] == "teacher"
    assert classify_question("annem nerede?")["type"] == "mother"
    assert classify_question("cüzdanım nerede?")["type"] in ("money",)
    # iş arkadaşı -> coworker(6), genel arkadaş -> friend(11) — özgül önce
    assert classify_question("iş arkadaşım ibrahim nerede?")["type"] == "coworker"
    assert classify_question("iş arkadaşım nerede?")["house"] == 6


def test_turned_house_math():
    assert turned_house(11, 7) == 5       # arkadaşımın eşi -> 5.ev
    assert turned_house(4, 3) == 6        # annemin kardeşi -> 6.ev
    assert turned_house(7, 11) == 5       # eşimin arkadaşı -> 5.ev


def test_parse_nested():
    r = parse_nested("arkadaşımın eşi nerede?")
    assert r and r["derived"] == 5 and r["base_word"] == "Arkadaş"
    assert "11. evden 7. ev = 5. ev" in r["formula"]
    assert parse_nested("arkadaşım nerede?") is None  # iyelikli ikinci kişi yok


def test_derived_kuzen_altin_house():
    """Kuzenin kayıp altınları: soran(1)->kuzen(3)->altın(2)=4.ev (iç içe ev zinciri)."""
    from engine.derived_houses import parse_derived
    r = parse_derived("kuzenimin kayıp altınları nerde")
    assert r and r["derived"] == 4
    assert r["base_house"] == 3 and r["offset"] == 2
    assert "3.evden 2.ev = 4.ev" in r["formula"]
    # 'kuzenimin' (benim) iyelikli genitive de çalışmalı
    r2 = parse_derived("kuzenimin altınları kayıp nerede olabilir")
    assert r2 and r2["derived"] == 4


def test_nested_coworker_abi():
    """'iş arkadaşım X'in abisi' -> coworker(6) içinden abi(3) = 8.ev."""
    r = parse_nested("iş arkadaşım muazzezin abisi nerde")
    assert r and r["derived"] == 8
    assert r["base_house"] == 6 and r["nested_house"] == 3
    assert "6. evden 3. ev = 8. ev" in r["formula"]
    # ablası/ağabeyi de kardeş(3) olarak derive edilmeli
    r2 = parse_nested("iş arkadaşımın ablası nerede")
    assert r2 and r2["derived"] == 8


def test_direction_components():
    eng = HoraryDistanceEngine()
    res = eng.analyze(9, "Virgo", "Sun", 152.1, 133.4, return_components=True)
    assert res["house"] == 9
    assert res["significator"] == "Sun"
    assert 0 <= res["azimut"] < 360
    assert set(res["components"]) == {"house", "sign_corr", "planet_corr", "ang_adj", "angular"}
    assert res["ev_tipi"] == "cadent"           # 9.ev cadent
    res2 = eng.analyze(1, "Aries", "Mars", 100.0, 90.0)
    assert res2["ev_tipi"] == "angular"


def test_km_category_two_stage():
    assert km_category(30)["label"] == "çok yakın"
    assert km_category(120)["label"] == "yakın"
    assert km_category(300)["label"] == "orta"
    assert km_category(600)["label"] == "orta-uzak"
    assert km_category(1000)["label"] == "uzak"
    assert km_category(2000)["label"] == "çok uzak"


def test_geographic_izmir_kirikkale():
    dm = geographic_distance(38.3176, 27.2025, 39.8468, 33.5153)
    br = geographic_bearing(38.3176, 27.2025, 39.8468, 33.5153)
    assert 550 <= dm <= 600          # gerçek ~572 km
    assert 60 <= br <= 90            # gerçek ~72° ENE


def test_condition_factor_values():
    f = condition_factor("Sun", "Virgo")
    assert 0.9 <= f["factor"] <= 1.0
    f2 = condition_factor("Sun", "Aries")
    assert f2["factor"] == 1.0
    f3 = condition_factor("Moon", "Scorpio", retro=True)
    assert f3["factor"] > 0  # mevcut implementasyonda her zaman 1.0 döner, retro etiketini de kontrol et
    f4 = condition_factor("Mercury", "Virgo", lon=30.0, sun_lon=26.0)
    assert f4["factor"] < 1.0 and "combust" in f4["labels"]


def test_calibration_scale_and_verify(tmp_path):
    cal = HoraryCalibration(filename=os.path.join(tmp_path, "cal.json"))
    # seed kaydı: teacher -> Kırıkkale, Δθ=5.73 (Ay-Merkür orb), M=1 (öncü card), gerçek 576 km
    cal.add_record(question_type="teacher", house=9, significator="Mercury", sign="Virgo",
                   sign_querent="Aries", angular_difference=5.73, modality="cardinal",
                   modality_multiplier=1.0, condition=1.0,
                   real_distance_km=576, real_bearing=71.94)
    cal.save()
    cal2 = HoraryCalibration(filename=os.path.join(tmp_path, "cal.json"))
    cal2.load()
    assert len(cal2.records) == 1

    eng = HoraryDistanceEngine()
    # sign_querent=Aries (Koç/öncü) → M=1; orb=5.73 → base=5.73, k=576/5.73≈100.5
    geo = eng.analyze(9, "Virgo", "Mercury", 159.78, 4.05, return_components=True, sign_querent="Aries")
    out = cal2.apply(geo, question_type="teacher")
    # k = 576/5.73 ≈ 100.5 → mesafe_kalibre ≈ 576 km
    assert out["mesafe_kalibre_km"] is not None
    assert 520 <= out["mesafe_kalibre_km"] <= 630
    assert out["calibration_scale"] == round(576 / 5.73, 3)
    assert out["km_category"] == "orta-uzak"        # 400–750 km
    assert out["category"] == "uzak"                # 9.ev cadent

    v = verify_prediction(out["azimut"], out["mesafe_kalibre_km"], 38.3176, 27.2025, 39.8468, 33.5153)
    assert v["real_distance_km"] is not None and v["real_bearing"] is not None
    assert v["direction_error_deg"] is not None


def test_fit_direction_weights(tmp_path):
    records = []
    for i in range(MIN_FIT_RECORDS + 1):
        records.append({
            "components": {"house": 90.0, "sign_corr": 10.0, "planet_corr": 5.0,
                           "ang_adj": (i - 2) * 3.0, "angular": 60 + i},
            "real_bearing": 70.0 + i * 2,
            "house": 7, "question_type": "spouse", "condition": 1.0,
            "angular_difference": 60 + i, "real_distance_km": 300 + i * 10,
        })
    res = fit_direction_weights(records)
    assert res["fitted"]
    w = res["weights"]
    assert abs((w["house"] + w["sign"] + w["planet"]) - 1.0) < 0.01
    assert 0 <= w["house"] <= 1 and 0 <= w["sign"] <= 1 and 0 <= w["planet"] <= 1


def test_load_weights_defaults():
    w = load_weights(filename=os.path.join(tempfile.gettempdir(), "no_such_weights.json"))
    assert w == {"house": 0.5, "sign": 0.3, "planet": 0.2}


def test_baseline_izmir_kirikkale_probe():
    """Mevcut motorun gerçek vaka çıktısı (regresyon şamandırası)."""
    eng = HoraryDistanceEngine()
    geo = eng.analyze(9, "Virgo", "Sun", 152.06, 133.42, condition=1.0)
    # v1 motorun verdiği tutarlılık: cadent 9.ev, KD
    assert geo["house"] == 9
    assert geo["ev_tipi"] == "cadent"


if __name__ == "__main__":
    import tempfile as _tf, os
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ok = 0
    for fn in fns:
        try:
            if fn.__name__.startswith("test_calibration") or fn.__name__.startswith("test_fit"):
                tp = _tf.mkdtemp()
                fn(tp)
            else:
                fn()
            print(f"PASS {fn.__name__}")
            ok += 1
        except Exception as e:
            print(f"FAIL {fn.__name__}: {e}")
            import traceback
            traceback.print_exc()
    print(f"\n{ok}/{len(fns)} gecti")
    sys.exit(0 if ok == len(fns) else 1)