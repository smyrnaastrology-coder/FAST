# -*- coding: utf-8 -*-
"""Lost-object location-only response tests (ring example, 7 Mar 1974).

Historical daylight time applies in Los Angeles: 12:58 local -> 19:58 UTC.
This reproduces Moon 8° Virgo in house 3, POF Sagittarius in house 6, and
Mercury/Jupiter in house 9. The querent asked only where the ring was; do not
volunteer whether it would be found or give timing.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from core.ephemeris import house_of_planet, sign_from_lon
from engine.horary_engine import cast_horary_chart
from engine.horary_questions import classify_question
from engine.lost_object_brief import build_lost_object_brief

LA = (34.0667, -118.25)
ARGS = (1974, 3, 7, 19 + 58 / 60.0, LA[0], LA[1])
QUESTION = "Yüzüğüm nerede?"


def test_ring_question_classifies_as_lost_object():
    assert (classify_question(QUESTION) or {}).get("type") == "lost_object"


def test_ring_chart_matches_book_placements():
    r = cast_horary_chart(*ARGS, "lost_object")
    assert r["quesited"]["planet"] == "Moon"
    moon = r["planets"]["Moon"]
    assert moon["sign"] == "Başak" and 8 <= moon["deg"] < 10
    assert moon["house"] == 3
    pof = r["lots"]["POF"]
    assert sign_from_lon(pof) == "Yay"
    assert house_of_planet(pof, r["houses"]["cusps"]) == 6
    assert r["planets"]["Mercury"]["house"] == 9
    assert r["planets"]["Jupiter"]["sign"] == "Kova" and r["planets"]["Jupiter"]["house"] == 9


def test_lost_object_brief_only_answers_where():
    r = cast_horary_chart(*ARGS, "lost_object")
    brief = build_lost_object_brief(r, "lost_object", "tr")
    assert brief
    assert "Ay" in brief and "Başak" in brief and "3. evde" in brief
    assert "Şans Noktası" in brief and "Yay" in brief and "6. evde" in brief
    assert "Merkür" in brief and "9. evde" in brief
    assert "dolap" in brief and "yüksek" in brief
    # The querent asked only for location: no findability verdict, timing, or direction.
    low = brief.lower()
    assert not any(word in low for word in ("bulursun", "bulamaz", "bulunacak", "bulunmayacak", "zamanlama", "güney", "kuzey", "doğu", "batı"))
    assert build_lost_object_brief(r, "lost_object", "en").startswith("Lost object")
    assert build_lost_object_brief(r, "lost_object", "es").startswith("Objeto perdido")
    assert build_lost_object_brief(r, "relationship", "tr") is None


if __name__ == "__main__":
    test_ring_question_classifies_as_lost_object()
    test_ring_chart_matches_book_placements()
    test_lost_object_brief_only_answers_where()
    print("test_lost_object: 3/3 OK")
