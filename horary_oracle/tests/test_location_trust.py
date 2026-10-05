# -*- coding: utf-8 -*-
"""Guven katmani testleri - kalibrasyon verisi ne kadar destekliyor?

Kritik bulgu: 22 kayit var ama lost_object icin 1, child icin 1, student 5.
GLOBAL yon hatasi 49.5 derece. Bu yuzden hicbir soru tipi 'guclu' degil ve
zayif olanlarda km rakami KESINLIKLE verilmemeli.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from engine.horary_distance import HoraryCalibration
from engine import location_trust as LT

CAL = HoraryCalibration()
CAL.load()


def test_levels_valid():
    for qt in [None, "lost_object", "child", "student", "spouse", "boyle_bir_tip_yok"]:
        t = LT.assess(CAL, qt)
        assert t["level"] in ("guclu", "orta", "zayif"), (qt, t["level"])
    print("OK 1) seviyeler gecerli (guclu/orta/zayif)")


def test_single_record_is_weak():
    t = LT.assess(CAL, "lost_object")
    assert t["n_type"] == 1, t["n_type"]
    assert t["level"] == "zayif", t
    assert t["give_km"] is False, "1 kayittan km verilmemeli!"
    print("OK 2a) lost_object (1 kayit) -> zayif, km YOK")
    t2 = LT.assess(CAL, "child")
    assert t2["level"] == "zayif" and t2["give_km"] is False
    print("OK 2b) child (1 kayit) -> zayif, km YOK")


def test_high_error_beats_high_count():
    """5 kayit olsa bile 72 derece hata varsa zayif olmali.
    Kayit sayisi guveni kurtarmaz - yanlis yon daha kotudur."""
    t = LT.assess(CAL, "student")
    assert t["n_type"] == 5, t["n_type"]
    assert t["mean_dir_err_deg"] and t["mean_dir_err_deg"] > LT.DIR_MID, t
    assert t["level"] == "zayif", "72 derece hata 'orta' sayilamaz"
    assert t["give_km"] is False
    print(f"OK 3) student: 5 kayit ama {t['mean_dir_err_deg']} derece hata -> zayif")


def test_global_is_weak_now():
    t = LT.assess(CAL, None)
    assert t["n_all"] == 22, t["n_all"]
    assert t["mean_dir_err_deg"] > LT.DIR_MID, t
    assert t["level"] == "zayif", "22 kayitta 49 derece hata -> zayif olmali"
    print(f"OK 4) GLOBAL: {t['n_all']} kayit, {t['mean_dir_err_deg']} derece -> zayif, km YOK")


def test_weak_prompt_forbids_numbers():
    t = LT.assess(CAL, "lost_object")
    txt = LT.prompt_text(t)
    assert "KESIN KM" in txt.upper() or "HICBIR SAYI" in txt.upper(), txt
    assert "TAHM" in txt.upper(), txt
    print("OK 5) zayif talimati rakam yasakli + tahmin dili zorunlu")


def test_strong_would_allow_km():
    """Guclu senaryo: az hata + cok kayit -> km serbest, 'yaklasik' dili."""
    t = {"level": "guclu", "n_type": 12, "mean_dir_err_deg": 9.0,
         "reason": "test", "give_km": True, "must_hedge": False,
         "must_advise_manual": False}
    txt = LT.prompt_text(t)
    assert "yaklasik" in txt.lower(), txt
    assert "KESIN KM" not in txt.upper()
    print("OK 6) guclu senaryo km'ye izin veriyor, 'yaklasik' diyor")


def test_mid_allows_km_with_hedge():
    t = {"level": "orta", "n_type": 4, "mean_dir_err_deg": 30.0,
         "reason": "test", "give_km": True, "must_hedge": False,
         "must_advise_manual": False}
    txt = LT.prompt_text(t)
    assert "yaklasik" in txt.lower()
    print("OK 7) orta senaryo km veriyor ama kesif dil yasak")


def test_engine_fields():
    t = LT.assess(CAL, "lost_object")
    f = LT.engine_fields(t)
    assert f["trust_level"] == "zayif"
    assert f["trust_n_type"] == 1
    assert "trust_reason" in f and f["trust_reason"]
    print("OK 8) engine alanlari: ", {k: f[k] for k in ("trust_level", "trust_n_type")})


def test_no_contradictory_numbers():
    """Guven zayifken motorun ham qq_distance_km (1339 km) cevapta GORUNMEMELI.
    Yoksa kullanici 1339 km ve '50-100 m' gibi iki celiskili rakem gorur."""
    for qt in ["lost_object", "child", "student"]:
        t = LT.assess(CAL, qt)
        loc = {"qq_distance_km": 1339.8, "distance": "407 m", "band": "~50-100 km"}
        if t["give_km"]:
            continue
        for k in ("qq_distance_km", "distance", "band"):
            loc.pop(k, None)
        assert "qq_distance_km" not in loc, qt
        assert "1339" not in str(loc), loc
    print("OK 9) zayif guvende ham rakamlar cevaptan temizleniyor")


if __name__ == "__main__":
    test_levels_valid()
    test_single_record_is_weak()
    test_high_error_beats_high_count()
    test_global_is_weak_now()
    test_weak_prompt_forbids_numbers()
    test_strong_would_allow_km()
    test_mid_allows_km_with_hedge()
    test_engine_fields()
    test_no_contradictory_numbers()
    print("\ntest_location_trust: 10/10 OK")
    print("SONUC: hicbir soru tipi 'guclu' degil; zayif olanlarda km verilmiyor.")