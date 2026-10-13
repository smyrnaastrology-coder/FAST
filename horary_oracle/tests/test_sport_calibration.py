# -*- coding: utf-8 -*-
"""Spor gol dakikası KALİBRASYON testleri.

Amaç: ham "kullanıcı taktiği" (sport_goal_minutes) yerine ölçülebilir bir
model kurulduğunu ve ölçüm yetersizken dakika VERİLMEDİĞİNİ kanıtlamak.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from engine.sport_calibration import (
    degree_marks, fit_goal_params, assess, forecast, SportCalibration,
    MINUTE_MIN, MINUTE_MAX,
)
from engine.horary_engine import cast_horary_chart, sport_goal_minutes
from engine.horary_questions import classify_question

_td = tempfile.mkdtemp(prefix="sportcal_")


def _rec(marks, goals, match="m"):
    return {"match": match, "marks": list(marks), "goal_minutes": list(goals)}


def test_degree_marks_increasing():
    cusps = [19.42, 58.42, 82.33, 100.90, 121.38, 152.51,
             199.42, 238.42, 262.33, 280.90, 301.38, 332.51]
    marks = degree_marks(cusps)
    assert len(marks) == 12, marks
    assert all(marks[i] < marks[i + 1] for i in range(len(marks) - 1)), marks
    assert abs(marks[0] - 19.42) < 1e-9
    print("OK 1) degree_marks artan ve 12 isaret")


def test_uncalibrated_gives_no_minutes():
    # hiç kayıt yok -> model eğitilmedi -> dakika YOK
    params = {"fitted": False, "a": None, "b": None, "mae": None}
    cusps = [10, 40, 70, 100, 130, 160, 190, 220, 250, 280, 310, 340]
    tr = assess([], params)
    assert tr["level"] == "zayif" and tr["give_minutes"] is False, tr
    f = forecast(cusps, records=[], params=params)
    assert f["minutes"] is None, f
    assert "yetersiz" in f["text"]
    print("OK 2) kalibrasyon yoksa dakika verilmiyor")


def test_fit_recovers_known_mapping():
    # gerçek eşleme dakika = 0.8*mark + 5 ; sentetik veriyi geri kazanmalı
    A, B = 0.8, 5.0
    recs = []
    for j, base in enumerate((10, 15, 20, 25, 30, 35)):
        marks = [base + 3 * i for i in range(8)]
        goals = [round(max(MINUTE_MIN, min(MINUTE_MAX, A * m + B))) for m in marks[:2]]
        recs.append(_rec(marks, goals, f"m{j}"))
    res = fit_goal_params(recs)
    assert res["fitted"], res
    assert abs(res["a"] - A) <= 0.05, res
    assert abs(res["b"] - B) <= 1.5, res
    assert res["mae"] <= 1.5, res
    tr = assess(recs, res)
    assert tr["level"] == "guclu" and tr["give_minutes"], tr
    print(f"OK 3) a={res['a']} b={res['b']} mae={res['mae']} -> {tr['level']}")


def test_fit_refuses_too_few():
    recs = [_rec([10, 20, 30], [12, 22]) for _ in range(3)]  # < MIN_FIT_MATCHES
    res = fit_goal_params(recs)
    assert not res["fitted"], res
    assert "en az" in res["reason"]
    print("OK 4) yetersiz maçta fit reddediliyor")


def test_gate_blocks_despite_fit_when_few_records():
    # 2 maç -> fit denenmez; zorla fit edilmiş parametre verilse bile n<3 -> zayif
    params = {"fitted": True, "a": 0.8, "b": 5.0, "mae": 3.0}
    recs = [_rec([10, 20, 30], [12, 22]) for _ in range(2)]
    tr = assess(recs, params)
    assert tr["level"] == "zayif" and tr["give_minutes"] is False, tr
    cusps = [10, 40, 70, 100, 130, 160, 190, 220, 250, 280, 310, 340]
    f = forecast(cusps, records=recs, params=params)
    assert f["minutes"] is None, f
    print("OK 5) az maçta fit olsa da dakika verilmiyor")


def test_forecast_minutes_clamped_and_sorted():
    A, B = 2.5, 20.0  # büyük eğim: tavan/taban testi
    params = {"fitted": True, "a": A, "b": B, "mae": 4.0}
    recs = [_rec([10 + 3 * i for i in range(8)], [45 + i for i in range(3)]) for i in range(6)]
    cusps = [10, 40, 70, 100, 130, 160, 190, 220, 250, 280, 310, 340]
    f = forecast(cusps, records=recs, params=params)
    assert f["give_minutes"], f
    mins = f["minutes"]
    assert mins, f
    assert all(MINUTE_MIN <= m <= MINUTE_MAX for m in mins), mins
    assert mins == sorted(mins), mins
    print(f"OK 6) dakikalar [{MINUTE_MIN},{MINUTE_MAX}] aralığında ve sıralı: {mins}")


def test_raw_tactic_is_uncalibrated_red_flag():
    # Ham taktik 7 gol öngörüyor: kalibrasyonun NEDEN gerekli olduğunu belgeler.
    cusps = [19.42, 58.42, 82.33, 100.90, 121.38, 152.51,
             199.42, 238.42, 262.33, 280.90, 301.38, 332.51]
    raw = sport_goal_minutes(cusps)
    assert len(raw) >= 5, raw  # absürt: bir maçta bu kadar gol olmaz
    print(f"OK 7) ham taktik {len(raw)} gol öngörüyor (kalibrasyonsuz - uyarı)")


def test_classify_sport_goals():
    assert (classify_question("Galatasaray Barcelona maçında kaçıncı dakikalarda gol olur?") or {}).get("type") == "sport_goals"
    assert (classify_question("Bu maçta kaç gol olur?") or {}).get("type") == "sport_goals"
    assert (classify_question("Maç kaç kaç biter?") or {}).get("type") == "sport_goals"
    # kazanma sorusu hâlâ taraftar çerçevesi
    assert (classify_question("Galatasaray kazanacak mı?") or {}).get("type") == "sport_fan"
    # spor dışı soru gol/skor kategorisine girmemeli
    assert (classify_question("Babam nerede?") or {}).get("type") != "sport_goals"
    print("OK 8) gol/dakika sorusu sport_goals, kazanma sorusu sport_fan")


def test_chart_carries_no_minutes_when_uncalibrated():
    # gerçek depo boş -> harita sport_goals bloğu dakika vermemeli
    r = cast_horary_chart(2026, 10, 13, 15.5, 38.4237, 27.1428, "sport_goals")
    blk = r.get("sport_goals")
    assert blk is not None, "sport_goals bloğu yok"
    assert blk["give_minutes"] is False, blk
    assert blk["minutes"] is None, blk
    print("OK 9) kalibrasyonsuz haritada dakika yok")


def test_store_roundtrip():
    p = os.path.join(_td, "store.json")
    c = SportCalibration(filename=p)
    cusps = [19.42, 58.42, 82.33, 100.90, 121.38, 152.51,
             199.42, 238.42, 262.33, 280.90, 301.38, 332.51]
    c.add_record(match="gs-bar", date="2026-10-13", cusps=cusps, goal_minutes=[23, 67])
    c.save()
    c2 = SportCalibration(filename=p)
    c2.load()
    assert len(c2.records) == 1
    assert c2.records[0]["marks"] == degree_marks(cusps)
    assert c2.records[0]["goal_minutes"] == [23, 67]
    print("OK 10) depo kaydet/yükle + marks türetme")


if __name__ == "__main__":
    test_degree_marks_increasing()
    test_uncalibrated_gives_no_minutes()
    test_fit_recovers_known_mapping()
    test_fit_refuses_too_few()
    test_gate_blocks_despite_fit_when_few_records()
    test_forecast_minutes_clamped_and_sorted()
    test_raw_tactic_is_uncalibrated_red_flag()
    test_classify_sport_goals()
    test_chart_carries_no_minutes_when_uncalibrated()
    test_store_roundtrip()
    print("\ntest_sport_calibration: 10/10 OK")
