# -*- coding: utf-8 -*-
"""Business agreement/purchase frame tests (book case #64).

12 Dec 1981 11:12 PST, Coeur d'Alene. "Will Murchison buy the Bunker Hill mine?"
Buyer = 7th ruler Sun; seller = buyer's 10th (chart 4) Mercury, with intercepted
Pisces/Neptune as co-ruler. Sun applies to Neptune; Moon applies 150-degree
quincunxes to the significators. Deal was eventually completed after union delay.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from engine.deal_brief import build_deal_brief
from engine.horary_engine import cast_horary_chart
from engine.horary_questions import classify_question, is_deal_question

COEUR = (47.6833, -116.7667)
ARGS = (1981, 12, 12, 19 + 12 / 60.0, COEUR[0], COEUR[1])  # 11:12 PST -> 19:12 UTC
QUESTION = "Murchison Bunker Hill madenini alacak mı?"


def test_deal_question_detection():
    assert is_deal_question(QUESTION)
    assert is_deal_question("Will Murchison buy the Bunker Hill mine?")
    assert (classify_question(QUESTION) or {}).get("type") == "deal"
    assert not is_deal_question("Babam nerede?")
    assert not is_deal_question("Bu gece kar yağacak mı?")
    print("OK deal detection")


def test_64_murchison_deal_yes_with_delay_indicators():
    r = cast_horary_chart(*ARGS, "deal")
    codes = [s["code"] for s in r["strictures"]]
    assert r["verdict"] == "YES", f"#64 anlaşma gerçekleşmeli: {r['verdict']} score={r['score']}"
    assert r["score"] >= 8, r["score"]
    assert r["quesited"]["planet"] == "Sun" and r["quesited"]["house"] == 7
    # Alıcının 10.'su chart 4 = Mercury; Pisces intercepted in buyer's 7th -> Neptune.
    assert "deal_buyer_applies_seller" in codes, codes
    direct = next(s for s in r["strictures"] if s["code"] == "deal_buyer_applies_seller")
    assert direct["with"] == "Neptune" and direct["angle"] == 0 and direct["orb"] < 5, direct
    assert "deal_moon_quincunx_translation" in codes, codes
    assert "deal_union_approval_delay" in codes, codes
    assert "deal_investment_source_aspect" in codes, codes
    assert r["planets"]["Mercury"]["house"] == 10
    assert r["planets"]["Neptune"]["sign"] == "Yay"
    print(f"OK #64 YES score={r['score']}")


def test_deal_brief_uses_turned_houses_and_shows_orb_caveat():
    r = cast_horary_chart(*ARGS, "deal")
    brief = build_deal_brief(r, "deal", "tr")
    assert brief
    assert "Satıcı: alıcının 10. evi (4. ev)" in brief
    assert "araya sıkışmış Balık" in brief
    assert "uyguluyor" in brief and "ayrılıyor/geçmiş" in brief
    assert "kareye 12.4° orb" in brief  # source's claimed Venus-Saturn trine is very wide
    assert "kesin zaman ölçüsü vermez" in brief
    assert build_deal_brief(r, "deal", "en").startswith("Deal/purchase checklist")
    assert build_deal_brief(r, "deal", "es").startswith("Control de compra")
    assert build_deal_brief(r, "relationship", "tr") is None
    print("OK deal brief")


if __name__ == "__main__":
    test_deal_question_detection()
    test_64_murchison_deal_yes_with_delay_indicators()
    test_deal_brief_uses_turned_houses_and_shows_orb_caveat()
    print("test_deal: 3/3 OK")
