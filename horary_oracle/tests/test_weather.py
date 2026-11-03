"""HAVA DURUMU çerçevesi testleri (kitap #62).

Hedef 6. ev. 6. evin yöneticisi querent göstergesine yumuşak açı yapıyorsa
yağış EVET. #62: 22 Kas 1979 12:40 PST Coeur d'Alene, "Bu gece kar yağacak mı?"
-> Ay 8° Oğlak, querent Uranüs 22° Akrep ile sekstil; gerçekte sert kar yağdı.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from engine.horary_engine import cast_horary_chart
from engine.horary_questions import classify_question, is_weather_question
from engine.weather_brief import build_weather_brief

COEUR = (47.6833, -116.7667)


def test_weather_detection():
    assert is_weather_question("Bu gece kar yağacak mı?")
    assert is_weather_question("Yarın yağmur yağar mı?")
    assert is_weather_question("Will it snow tonight?")
    assert is_weather_question("¿Va a nevar esta noche?")
    assert not is_weather_question("Babam nerede?")
    assert not is_weather_question("Vandals maçı kazanacak mı?")
    assert (classify_question("Bu gece kar yağacak mı?") or {}).get("type") == "weather"
    print("OK weather detection")


def test_62_snow_yes():
    r = cast_horary_chart(1979, 11, 22, 20 + 40 / 60.0, COEUR[0], COEUR[1], "weather")
    codes = [s["code"] for s in r["strictures"]]
    assert "weather_precip_yes" in codes, codes
    assert r["verdict"] == "YES", f"kar sorusu YES olmali, {r['verdict']} score={r['score']}"
    assert r["quesited"]["house"] == 6
    # kitap: hava hedefi 6. evin yöneticisi Ay; querent Uranüs (ASC Kova)
    assert r["quesited"]["planet"] == "Moon", r["quesited"]
    assert r["querent"]["planet"] == "Uranus", r["querent"]
    print(f"OK #62 kar YES score={r['score']}")


def test_weather_brief_lists_the_frame():
    r = cast_horary_chart(1979, 11, 22, 20 + 40 / 60.0, COEUR[0], COEUR[1], "weather")
    brief = build_weather_brief(r, "weather", "tr")
    assert brief, "hava sorusunda kontrol listesi bos olmamali"
    assert "hedef 6. ev" in brief
    assert "Hüküm:" in brief
    assert build_weather_brief(r, "weather", "en").startswith("Weather checklist")
    assert build_weather_brief(r, "weather", "es").startswith("Control del tiempo")
    assert build_weather_brief(r, "relationship", "tr") is None
    print("OK weather brief")


if __name__ == "__main__":
    test_weather_detection()
    test_62_snow_yes()
    test_weather_brief_lists_the_frame()
    print("test_weather: 3/3 OK")
