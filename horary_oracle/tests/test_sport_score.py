# -*- coding: utf-8 -*-
"""Spor SKOR / TOPLAM GOL kalibrasyon testleri.

Amaç: "kaç kaç biter" sorusunda kesin skor UYDURULMADIĞINI, yalnız toplam gol
için ölçülebilir bir model kurulduğunu ve ölçüm yetersizken SAYI VERİLMEDİĞİNİ
kanıtlamak (gol-dakikası modeliyle aynı güven felsefesi).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from engine.sport_score import (
    scoring_index, total_goals, fit_score_params, assess_score, forecast_score,
    MAX_TOTAL_GOALS,
)
from engine.sport_calibration import SportCalibration
from engine.horary_engine import cast_horary_chart

_td = tempfile.mkdtemp(prefix="sportscore_")


def _p(name, lon, speed):
    return {name: {"lon": lon, "speed": speed}}


def test_index_counts_applying_major():
    # Merkür (hızlı) Jüpiter'e yaklaşıyor, kavuşum orbunda -> 1 applying açı
    p = {"Mercury": {"lon": 350.0, "speed": 1.3},
         "Jupiter": {"lon": 358.0, "speed": 0.08}}
    assert scoring_index(p) == 1, scoring_index(p)
    print("OK 1) applying kavuşum sayılıyor")


def test_index_excludes_separating():
    # aynı iki gezegen ama uzaklaşıyor -> 0
    p = {"Mercury": {"lon": 6.0, "speed": 1.3},
         "Jupiter": {"lon": 358.0, "speed": 0.08}}
    assert scoring_index(p) == 0, scoring_index(p)
    assert scoring_index(p, applying_only=False) == 1, scoring_index(p, applying_only=False)
    print("OK 2) uzaklaşan açı sayılmıyor, applying_only=False sayıyor")


def test_index_out_of_orb_ignored():
    p = {"Mercury": {"lon": 340.0, "speed": 1.3},
         "Jupiter": {"lon": 358.0, "speed": 0.08}}  # 18° -> orb dışı
    assert scoring_index(p) == 0, scoring_index(p)
    print("OK 3) orb dışı açı sayılmıyor")


def test_total_goals_derivation():
    assert total_goals({"goal_minutes": [12, 40, 77]}) == 3
    assert total_goals({"total_goals": 4, "goal_minutes": [1, 2]}) == 4
    assert total_goals({}) is None
    print("OK 4) toplam gol türetme")


def _recs_from(mapping):
    return [{"match": f"m{x}", "scoring_index": x, "total_goals": y}
            for x, y in mapping]


def test_fit_recovers_known_mapping():
    mapping = [(x, round(0.4 * x + 1)) for x in range(11)]
    res = fit_score_params(_recs_from(mapping))
    assert res["fitted"], res
    assert abs(res["c"] - 0.4) <= 0.03, res
    assert abs(res["d"] - 1.0) <= 0.3, res
    assert res["mae"] <= 0.2, res
    tr = assess_score(_recs_from(mapping), res)
    assert tr["level"] == "guclu" and tr["give_total"], tr
    print(f"OK 5) c={res['c']} d={res['d']} mae={res['mae']} -> {tr['level']}")


def test_fit_refuses_too_few():
    res = fit_score_params(_recs_from([(x, x % 4) for x in range(3)]))
    assert not res["fitted"], res
    assert "en az" in res["reason"]
    print("OK 6) yetersiz maçta fit reddediliyor")


def test_gate_blocks_despite_fit():
    params = {"fitted": True, "c": 0.4, "d": 1.0, "mae": 0.1}
    recs = _recs_from([(0, 1), (1, 1)])  # 2 maç
    tr = assess_score(recs, params)
    assert tr["level"] == "zayif" and tr["give_total"] is False, tr
    planets = {"Mercury": {"lon": 350.0, "speed": 1.3},
               "Jupiter": {"lon": 358.0, "speed": 0.08}}
    f = forecast_score(planets, records=recs, params=params)
    assert f["total_goals"] is None, f
    print("OK 7) az maçta fit olsa da toplam gol verilmiyor")


def test_uncalibrated_forecast_has_no_number():
    planets = {"Mercury": {"lon": 350.0, "speed": 1.3},
               "Jupiter": {"lon": 358.0, "speed": 0.08}}
    f = forecast_score(planets, records=[],
                       params={"fitted": False, "c": None, "d": None, "mae": None})
    assert f["total_goals"] is None and f["give_total"] is False, f
    assert "yetersiz" in f["text"]
    print("OK 8) kalibrasyonsuz skor tahmini sayı vermiyor")


def test_calibrated_forecast_clamped():
    params = {"fitted": True, "c": 0.4, "d": 1.0, "mae": 0.1}
    recs = _recs_from([(x, round(0.4 * x + 1)) for x in range(11)])
    planets = {"Mercury": {"lon": 350.0, "speed": 1.3},
               "Jupiter": {"lon": 358.0, "speed": 0.08}}
    f = forecast_score(planets, records=recs, params=params)
    assert f["give_total"], f
    assert 0 <= f["total_goals"] <= MAX_TOTAL_GOALS, f
    assert f["over_under"] in ("üst 2.5", "alt 2.5"), f
    print(f"OK 9) kalibre tahmin: toplam={f['total_goals']} ({f['over_under']})")


def test_chart_carries_score_block_uncalibrated():
    r = cast_horary_chart(2026, 10, 13, 15.5, 38.4237, 27.1428, "sport_goals")
    blk = r.get("sport_goals")
    assert blk is not None and "score" in blk, blk
    assert blk["score"]["give_total"] is False, blk["score"]
    assert blk["score"]["total_goals"] is None, blk["score"]
    print("OK 10) kalibrasyonsuz haritada skor bloğu sayı vermiyor")


def test_store_derives_index_and_total():
    p = os.path.join(_td, "store.json")
    c = SportCalibration(filename=p)
    cusps = [19.42, 58.42, 82.33, 100.90, 121.38, 152.51,
             199.42, 238.42, 262.33, 280.90, 301.38, 332.51]
    planets = {"Mercury": {"lon": 350.0, "speed": 1.3},
               "Jupiter": {"lon": 358.0, "speed": 0.08}}
    c.add_record(match="gs-bar", cusps=cusps, goal_minutes=[23, 67],
                 planets=planets)
    c.save()
    c2 = SportCalibration(filename=p)
    c2.load()
    r = c2.records[0]
    assert r["scoring_index"] == 1, r
    assert r["total_goals"] == 2, r
    assert "planets" not in r, "planets sözlüğü depoya yazılmamalı"
    print("OK 11) add_record sinyal+toplam gol türetiyor, planets saklanmıyor")


if __name__ == "__main__":
    test_index_counts_applying_major()
    test_index_excludes_separating()
    test_index_out_of_orb_ignored()
    test_total_goals_derivation()
    test_fit_recovers_known_mapping()
    test_fit_refuses_too_few()
    test_gate_blocks_despite_fit()
    test_uncalibrated_forecast_has_no_number()
    test_calibrated_forecast_clamped()
    test_chart_carries_score_block_uncalibrated()
    test_store_derives_index_and_total()
    print("\ntest_sport_score: 11/11 OK")
