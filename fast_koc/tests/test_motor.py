import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.engine.analiz_motoru import konu_analiz
from backend.engine.odev_motoru import haftalik_plan
from backend.engine.yorum_motoru import gunluk_kiyas


def test_analiz_esik():
    konular = [
        {"kod": "A", "baslik": "Kritik", "dogru": 2, "yanlis": 6, "bos": 2},
        {"kod": "B", "baslik": "Guclu", "dogru": 9, "yanlis": 1, "bos": 0},
    ]
    a = konu_analiz(konular, segment="YKS")
    assert a["kritik_sayisi"] == 1
    assert a["konular"][0]["durum"] == "kritik"
    assert a["net"] == round(11 - 7 / 4.0, 2)


def test_odev_7_gun():
    analiz = {"konular": [
        {"kod": "TYT-MAT-06", "baslik": "Problemler", "dogru": 3, "yanlis": 5, "bos": 2, "toplam": 10, "basari": 30.0, "durum": "kritik"},
        {"kod": "TYT-TR-01", "baslik": "Paragraf", "dogru": 8, "yanlis": 2, "bos": 0, "toplam": 10, "basari": 80.0, "durum": "guclu"},
    ], "oncelikli": []}
    plan = haftalik_plan("orta", "YKS", analiz)
    assert len(plan) == 7
    assert plan[-1]["konu_kod"] == "DENEME"


def test_gunluk_kiyas():
    assert "Harikasin" in gunluk_kiyas(80, 85, [80])
    assert "soru girisi yok" in gunluk_kiyas(80, 0, [])
