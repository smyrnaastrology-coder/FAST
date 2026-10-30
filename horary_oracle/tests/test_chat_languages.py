import asyncio

import api
from engine.interpreter import _correct_planet_hallucination, _localized_fallback


def test_greetings_follow_selected_language(monkeypatch):
    monkeypatch.setattr(api, "_require_account", lambda _: {})
    for question, lang, expected in [
        ("merhaba", "tr", "Merhaba"),
        ("merhaba", "en", "Hello"),
        ("hola!", "es", "¡Hola"),
        ("hi", "en", "Hello"),
    ]:
        req = api.CastRequest(question=question, lat=41, lon=29, lang=lang)
        result = asyncio.run(api.cast(req))
        assert result["verdict"] == "CHAT"
        assert expected in result["answer"]
        assert result["strictures"] == []


def test_thanks_and_how_are_you_follow_locale(monkeypatch):
    monkeypatch.setattr(api, "_require_account", lambda _: {})
    for question, lang, expected in [
        ("thank you", "en", "welcome"),
        ("gracias", "es", "nada"),
        ("¿cómo estás?", "es", "escucho"),
    ]:
        req = api.CastRequest(question=question, lat=41, lon=29, lang=lang)
        assert expected in asyncio.run(api.cast(req))["answer"]


def test_sign_correction_keeps_the_requested_language():
    chart = {"planets": {"Jupiter": {"sign": "Yay"}}}
    assert _correct_planet_hallucination("Jupiter Sagittarius", chart, "en") == "Jupiter Sagittarius"
    assert _correct_planet_hallucination("Jupiter Aries", chart, "es") == "Jupiter Sagitario"


def test_offline_fallback_does_not_return_turkish_in_english_or_spanish():
    chart = {"verdict": "YES"}
    assert "preliminary verdict is yes" in _localized_fallback(chart, "en")
    assert "veredicto preliminar" in _localized_fallback(chart, "es")
