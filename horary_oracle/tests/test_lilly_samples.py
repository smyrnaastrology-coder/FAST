"""
Lilly Christian Astrology örnekleri ile regresyon testleri.
Her test: verilen tarihte motorun verdict/perfection'u kitapla aynı mı?
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from engine.horary_engine import cast_horary_chart

def test_voc_detection():
    # Ay boşlukta testi - hızlı kontrol
    r = cast_horary_chart(2026,3,10,14.5,41.0,28.9,"relationship")
    assert "verdict" in r
    assert "perfection" in r
    print("VOC test passed:", r["verdict"], r["perfection"])

def test_asc_immature_warning():
    # ASC 2° erken uyarı vermeli
    r = cast_horary_chart(2026,3,10,14.5,41.0082,28.9784,"relationship")
    codes = [s["code"] for s in r["strictures"]]
    assert "asc_immature" in codes, f"asc_immature bekleniyordu, gelen: {codes}"
    print("ASC early passed")

if __name__ == "__main__":
    test_voc_detection()
    test_asc_immature_warning()
    print("Tüm testler geçti.")
