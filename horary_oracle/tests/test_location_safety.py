import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

import api
import auth
from engine.location_safety import (
    classical_significator,
    person_location_answer,
    person_location_subject,
)


def test_student_where_is_person_even_if_lost_object_ui_category_selected():
    assert person_location_subject("öğrencim nerde?", "lost_object") == {
        "type": "student",
        "label": "Öğrenci",
    }


def test_student_possessions_remain_lost_object_questions():
    assert person_location_subject("öğrencimin çantası nerede?", "general") is None
    assert person_location_subject("öğrencimin altınları nerede?", "general") is None
    assert person_location_subject("Where is my student's bag?", "general") is None


def test_student_where_is_detected_in_supported_languages():
    assert person_location_subject("Where is my student?", "general") == {
        "type": "student",
        "label": "student",
    }
    assert person_location_subject("¿Dónde está mi estudiante?", "general") == {
        "type": "student",
        "label": "estudiante",
    }


def test_classical_ruler_is_used_instead_of_modern_outer_planets():
    # Kova burcu klasikte Saturn, modern astrolojide Uranüs'tür.
    assert classical_significator(
        3,
        [0, 0, 310],
        {"Saturn": {"sign": "İkizler", "house": 6}},
    ) == {
        "ruler_sign": "Kova",
        "planet": "Saturn",
        "sign": "İkizler",
        "house": 6,
    }
    # Akrep klasikte Mars, modern astrolojide Plüton'dur.
    assert classical_significator(
        7, [0, 0, 0, 0, 0, 0, 220], {"Mars": {"sign": "Yay", "house": 9}}
    )["planet"] == "Mars"


def test_person_location_answer_states_tradition_and_does_not_invent_details():
    answer = person_location_answer(
        "tr",
        "Öğrenci",
        reported_missing=False,
        context={
            "subject_type": "student",
            "_derived_house": 3,
            "sig_planet": "Saturn",
            "sign": "İkizler",
            "house": 6,
            "ruler_sign": "Kova",
            "trust_level": "zayif",
        },
    ).lower()
    assert "klasik horary'de öğrenci 3. evle temsil ediliyor" in answer
    assert "klasik yöneticisi satürn" in answer
    assert "satürn i̇kizler burcunda, 6. evde" in answer
    assert "okul, staj ya da iş rutini" in answer
    assert not re.search(r"\b\d+\s*(km|kilometre|metre)\b", answer)
    assert "kuzeydoğu" not in answer
    assert "kiler" not in answer


def test_general_person_theme_is_not_school_specific():
    answer = person_location_answer(
        "tr",
        "Arkadaş",
        reported_missing=False,
        context={
            "subject_type": "friend",
            "_derived_house": 7,
            "sig_planet": "Venus",
            "sign": "Boğa",
            "house": 6,
            "ruler_sign": "Terazi",
            "trust_level": "orta",
        },
    ).lower()
    assert "günlük iş, rutin, hizmet ya da sağlık ortamı" in answer
    assert "staj" not in answer


def test_explicit_missing_person_gets_practical_safety_guidance():
    answer = person_location_answer("tr", "öğrencin", reported_missing=True).lower()
    assert "öğrenciyi" in answer
    assert "okul/veliyi" in answer
    assert "acil riskte yerel yetkililere" in answer
    assert not re.search(r"\b\d+\s*(km|kilometre|metre)\b", answer)


def test_api_bypasses_llm_and_redacts_fake_geo_for_student(monkeypatch):
    monkeypatch.setattr(api, "_require_account", lambda _email: {"credits": 10})
    monkeypatch.setattr(auth, "get_user", lambda _email: {"credits": 10})
    monkeypatch.setattr(auth, "spend_credit", lambda _email: 9)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("person-location questions must not use the LLM")

    monkeypatch.setattr(api, "call_openai", fail_if_called)
    response = TestClient(api.app).post(
        "/api/horary/cast",
        json={
            "question": "öğrencim nerde?",
            "lat": 38.4237,
            "lon": 27.1428,
            "lang": "tr",
            "quesited_type": "lost_object",
            "email": "location-test@example.com",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "3. evle temsil ediliyor" in body["answer"]
    assert "klasik yöneticisi" in body["answer"]
    assert "sembolik olarak" in body["answer"]
    assert "uranüs" not in body["answer"].lower()
    assert "kuzeydoğu" not in body["answer"].lower()
    assert not re.search(r"\b\d+\s*(km|kilometre|metre)\b", body["answer"].lower())
    assert body["location"] == {
        "subject_type": "person",
        "subject": "Öğrenci",
        "urgency": "merak",
        "real_time_location_available": False,
    }
