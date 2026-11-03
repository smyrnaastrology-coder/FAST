"""EVRENSEL / ETKİNLİK-KATILIM çerçevesi testleri (kitap #63).

#63: 8 May 1984 23:14 PDT (11:14 pm), Coeur d'Alene. "Ruslar Olimpiyatlara
gelecek mi?" Kitap: taraf = 7. ev (Merkür 26° Koç, 4. evde), etkinlik = 5. ve
10. ev (Venüs 8° Boğa). Merkür ile Venüs arasında açı yok -> gelmediler
(SSCB 1984 Los Angeles Olimpiyatlarını boykot etti).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from engine.horary_engine import cast_horary_chart
from engine.horary_questions import classify_question, is_event_party_question
from engine.event_brief import build_event_brief

COEUR = (47.6833, -116.7667)
# 8 May 1984 23:14 PDT (UTC-7) -> 9 May 1984 06:14 UTC
ARGS = (1984, 5, 9, 6 + 14 / 60.0)


def test_event_party_detection():
    assert is_event_party_question("Ruslar Olimpiyatlara gelecek mi?")
    assert is_event_party_question("Will Russia come to the Olympics?")
    assert (classify_question("Ruslar Olimpiyatlara gelecek mi?") or {}).get("type") == "event_party"
    # etkinlik yok / katılım fiili yok -> bu çerçeveye girmez
    assert not is_event_party_question("Babam nerede?")
    assert not is_event_party_question("Vandals maçı kazanacak mı?")
    assert not is_event_party_question("Bu gece kar yağacak mı?")
    print("OK event detection")


def test_63_russians_no():
    r = cast_horary_chart(*ARGS, COEUR[0], COEUR[1], "event_party")
    codes = [s["code"] for s in r["strictures"]]
    assert "event_party_no_aspect" in codes, codes
    assert r["verdict"] == "NO", f"#63 NO olmali, {r['verdict']} score={r['score']}"
    # kitaptaki yerleşimler: 7. ev İkizler -> Merkür 26° Koç, 4. evde
    assert r["quesited"]["planet"] == "Mercury", r["quesited"]
    merc = r["planets"]["Mercury"]
    assert merc["sign"] == "Koç" and 26 <= merc["deg"] < 28, merc
    assert merc["house"] == 4, merc
    # etkinlik göstergesi Venüs (5. ve 10. ev aynı yönetici)
    venus = r["planets"]["Venus"]
    assert venus["sign"] == "Boğa" and 8 <= venus["deg"] < 9.5, venus
    print(f"OK #63 NO score={r['score']}")


def test_event_brief_lists_the_frame():
    r = cast_horary_chart(*ARGS, COEUR[0], COEUR[1], "event_party")
    brief = build_event_brief(r, "event_party", "tr")
    assert brief, "etkinlik sorusunda kontrol listesi bos olmamali"
    assert "Etkinlik/katılım" in brief
    assert "Taraf (üçüncü kişi/kurum): 7. ev" in brief
    assert "Hüküm:" in brief
    assert build_event_brief(r, "event_party", "en").startswith("Event/attendance checklist")
    assert build_event_brief(r, "event_party", "es").startswith("Control de evento")
    assert build_event_brief(r, "relationship", "tr") is None
    print("OK event brief")


if __name__ == "__main__":
    test_event_party_detection()
    test_63_russians_no()
    test_event_brief_lists_the_frame()
    print("test_event_party: 3/3 OK")
