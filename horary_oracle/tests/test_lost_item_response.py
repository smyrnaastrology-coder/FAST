from engine.lost_item_response import build_lost_item_answer
from engine.interpreter import call_openai


def _engine(direction_confidence="düşük"):
    return {
        "verdict": "LOCATION",
        "question": "Kaybolan anahtarım nerede?",
        "planets": {"Venus": {"sign": "Terazi", "deg": 23.0, "house": 7}},
        "location": {
            "_object": "anahtar",
            "sig_planet": "Venus",
            "house": 7,
            "sign": "Terazi",
            "deg": 23.0,
            "horary_geo": {
                "yon": "B",
                "yon_label": "Batı",
                "azimut": 270.0,
                "direction_confidence": direction_confidence,
                "direction_n": 8,
                "band": "~250–350 m",
            },
        },
    }


def test_lost_item_answer_gives_prioritized_places_and_azimuth_but_no_weak_km():
    answer = build_lost_item_answer(_engine(), "tr")

    assert "ortak kullanılan" in answer
    assert "salon veya misafir alanı" in answer
    assert "ayna" in answer
    assert "Batı" in answer and "azimut 270°" in answer
    assert "km tahmini vermiyorum" in answer
    assert "~250–350 m" not in answer
    assert "garanti etmez" in answer


def test_lost_item_answer_can_include_calibrated_distance_band():
    answer = build_lost_item_answer(_engine("orta"), "tr")

    assert "Uzaklık bandı: ~250–350 m" in answer
    assert "km tahmini vermiyorum" not in answer


def test_interpreter_uses_specialized_lost_item_answer():
    answer = call_openai(_engine(), "tr")

    assert "İlk arama önceliği" in answer
    assert "sembolik arama ipuçlarıdır" in answer


def test_person_location_does_not_use_lost_object_template():
    engine = _engine()
    engine["question"] = "Öğrencim nerede?"
    engine["location"]["subject_type"] = "person"

    assert build_lost_item_answer(engine, "tr") is None


def test_english_and_spanish_outputs_are_localized():
    english = build_lost_item_answer(_engine(), "en")
    spanish = build_lost_item_answer(_engine(), "es")

    assert "shared" in english and "West" in english and "azimuth" in english
    assert "compartida" in spanish and "Oeste" in spanish and "azimuth" in spanish
    assert "eşya" not in english and "Batı" not in english
