# -*- coding: utf-8 -*-
"""SPOR/TARAFTAR çerçevesi testleri (kitap #59 + #60, #34 koruması).

#59 Vandals: 9 Mar 1982 19:38 PST Coeur d'Alene -> EVET (69-67 uzatma), taraftar çerçevesi.
#60 Houston: 4 Ara 1980 17:35 PST Coeur d'Alene -> EVET (kıl payı), taraftar çerçevesi.
   'Maç' kelimesi yok -> takım adı (sport_team_lexicon) + kazanma fiili ile de tespit edilir.
#34 softball: 22 Jun 1978 17:28 PDT Los Angeles -> EVET, KENDİ takım çerçevesi (bu kurala GİRMEMELİ).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from engine.horary_engine import cast_horary_chart
from engine.horary_questions import classify_question, is_fan_sport_question

COEUR = (47.6833, -116.7667)
LA = (34.0522, -118.2437)


def test_fan_frame_detection():
    # #59: üçüncü taraf takım -> taraftar çerçevesi
    assert is_fan_sport_question("Vandals play-off maçını kazanacak mı?")
    assert is_fan_sport_question("Beşiktaş maçı kazanacak mı?")
    # taraftar "kazanacak mıyım?" derse de taraftar çerçevesi (tekil şahıs takımı değil)
    assert is_fan_sport_question("Vandals maçını kazanacak mıyım?")
    assert (classify_question("Vandals play-off maçını kazanacak mı?") or {}).get("type") == "sport_fan"
    # #34: kendi takımı -> KENDİ çerçevesi (fan değil)
    assert not is_fan_sport_question("Cumartesi gunu kazanacak miyiz?")
    assert not is_fan_sport_question("Bizim takımımız maçı kazanacak mı?")
    assert (classify_question("Cumartesi gunu kazanacak miyiz?") or {}).get("type") == "sport_fav"
    # kim kazanacak -> iki taraf, fan değil
    assert not is_fan_sport_question("Maçı kim kazanacak?")
    # spor dışı soru -> fan değil
    assert not is_fan_sport_question("Babam nerede?")
    print("OK frame detection")


def test_59_vandals_yes():
    r = cast_horary_chart(1982, 3, 10, 3 + 38 / 60.0, COEUR[0], COEUR[1], "sport_fan")
    assert r["verdict"] == "YES", f"#59 verdict {r['verdict']} score={r['score']}"
    assert r["score"] >= 8, r["score"]
    codes = [s["code"] for s in r["strictures"]]
    assert "sport_team_ruler_in_opponent_1st" in codes, codes
    assert "sport_team_ruler_conj_honor_ruler" in codes, codes
    assert "sport_opponent_ruler_in_honor" in codes, codes
    # uygulanan açı/perfection yok -> kitap "dar evet" (uzatma)
    assert r["perfection"].get("type") in (None, "none"), r["perfection"]
    assert r["quesited"]["planet"] == "Mars" and r["quesited"]["house"] == 7
    assert r["houses"]["asc_sign"] == "Terazi"
    print(f"OK #59 YES score={r['score']} timing={r['timing'].get('text')}")


def test_59_same_chart_own_team_frame_unchanged():
    # Aynı harita "kendi takımı" kutusundan sorulursa fan kuralı işlemez (regresyon koruması)
    r = cast_horary_chart(1982, 3, 10, 3 + 38 / 60.0, COEUR[0], COEUR[1], "sport_fav")
    codes = [s["code"] for s in r["strictures"]]
    assert not any(c.startswith("sport_") for c in codes), codes
    assert r["verdict"] == "UNCERTAIN", r["verdict"]
    print("OK #59 kendi-takim kutusu degismedi:", r["verdict"])


def test_34_own_team_still_yes():
    r = cast_horary_chart(1978, 6, 23, 0 + 28 / 60.0, LA[0], LA[1], "sport_fav")
    assert r["verdict"] == "YES", f"#34 verdict {r['verdict']} score={r['score']}"
    codes = [s["code"] for s in r["strictures"]]
    assert not any(c.startswith("sport_") for c in codes), "#34 kendi takim cercevesine girmemeli"
    print(f"OK #34 YES score={r['score']} perfection={r['perfection'].get('type')}")


def test_60_houston_detected_without_match_word():
    # #60: 'maç/derbi/final' kelimesi YOK; takım adı + kazanma fiili yeterli
    assert is_fan_sport_question("Houston bu gece kazanacak mı?")
    assert is_fan_sport_question("Houston bu gece kazanacak mi?")
    assert (classify_question("Houston bu gece kazanacak mı?") or {}).get("type") == "sport_fan"
    assert is_fan_sport_question("Galatasaray kazanır mı?")
    assert is_fan_sport_question("Real Madrid kazanır mı?")
    # 'kazan' fiili olmayan spor cümlesi taraftar çerçevesi DEĞİL
    assert not is_fan_sport_question("Houston maçı ne zaman?")
    # sınav/özel hayat: takım yok -> fan değil
    assert not is_fan_sport_question("İş sınavını kazanacak mıyım?")
    print("OK #60 tespit (maç kelimesiz)")


def test_60_houston_yes():
    r = cast_horary_chart(1980, 12, 5, 1 + 35 / 60.0, COEUR[0], COEUR[1], "sport_fan")
    assert r["verdict"] == "YES", f"#60 verdict {r['verdict']} score={r['score']}"
    assert r["score"] >= 8, r["score"]
    codes = [s["code"] for s in r["strictures"]]
    # takımın yöneticisi (Saturn) onur/zafere evinde + yücelmiş
    assert "sport_team_ruler_in_own_honor" in codes, codes
    # Jüpiter takım yöneticisine kavuşum uyguluyor
    assert "sport_benefic_applies_team_ruler" in codes, codes
    # rakibin gösteresi (Ay) düşüşte
    assert "sport_opponent_ruler_fall" in codes, codes
    # uygulama/perfection yok -> kitap "kıl payı"
    assert r["perfection"].get("type") in (None, "none"), r["perfection"]
    assert r["quesited"]["planet"] == "Saturn" and r["quesited"]["house"] == 7
    assert r["houses"]["asc_sign"] == "Yengeç"
    print(f"OK #60 YES score={r['score']} timing={r['timing'].get('text')}")


def test_60_same_chart_own_team_frame_unchanged():
    r = cast_horary_chart(1980, 12, 5, 1 + 35 / 60.0, COEUR[0], COEUR[1], "sport_fav")
    codes = [s["code"] for s in r["strictures"]]
    assert not any(c.startswith("sport_") for c in codes), codes
    assert r["verdict"] == "UNCERTAIN", r["verdict"]
    print("OK #60 kendi-takim kutusu degismedi:", r["verdict"])


if __name__ == "__main__":
    test_fan_frame_detection()
    test_59_vandals_yes()
    test_59_same_chart_own_team_frame_unchanged()
    test_34_own_team_still_yes()
    test_60_houston_detected_without_match_word()
    test_60_houston_yes()
    test_60_same_chart_own_team_frame_unchanged()
    print("test_sport_fan: 7/7 OK")
