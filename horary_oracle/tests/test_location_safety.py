import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.location_safety import person_location_answer, person_location_subject
from fastapi.testclient import TestClient
import api


def test_student_where_is_person_even_if_lost_object_ui_category_selected():
    target = person_location_subject("öğrencim nerde?", "lost_object")

    assert target == {"type": "student", "label": "Öğrenci"}


def test_student_bag_question_remains_a_lost_object_question():
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


def test_missing_person_answer_does_not_invent_location_details():
    answer = person_location_answer("tr", "öğrencin", reported_missing=False).lower()

    assert "gerçek zamanlı konumunu doğrulayamaz" in answer
    assert "uydurmamam gerekir" in answer
    assert not re.search(r"\b\d+\s*(km|kilometre|metre)\b", answer)
    assert "kuzeydoğu" not in answer
    assert "çatı katı" not in answer


def test_explicit_missing_person_gets_practical_safety_guidance():
    answer = person_location_answer("tr", "öğrencin", reported_missing=True).lower()

    assert "okul/veliyle hemen iletişime geç" in answer
    assert "acil yardım" in answer
    assert not re.search(r"\b\d+\s*(km|kilometre|metre)\b", answer)


def test_api_does_not_send_student_location_to_llm_or_return_fake_geo(monkeypatch):
    monkeypatch.setattr(api, "_require_account", lambda _email: {"credits": 10})

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
            # Simulate a stale/wrong UI category.
            "quesited_type": "lost_object",
            "email": "location-test@example.com",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "gerçek zamanlı konumunu doğrulayamaz" in body["answer"]
    assert "kuzeydoğu" not in body["answer"].lower()
    assert not re.search(r"\b\d+\s*(km|kilometre|metre)\b", body["answer"].lower())
    assert body["location"] == {
        "subject_type": "person",
        "subject": "Öğrenci",
        "urgency": "merak",
        "real_time_location_available": False,
    }
