"""Yanıt katmanı "bugün"ü bilmediği için geçmiş tarih uyduruyordu.

Ölçüm (2026-11): soru 2026'da sorulurken yanıt "2025 ortalarında" diyordu.
Modelin eğitim kesimi 2025 olduğu için bugünü 2025 sanıyor. Bu testler tarih
kilidini ve deterministik düzeltmeyi doğrular.
"""

from engine.interpreter import (
    _correct_past_date_hallucination,
    build_prompt,
)


CHART = {
    "cast_date": "2026-11-06",
    "verdict": "YES",
    "timing": {"text": "3 AY", "unit": "AY", "degrees": 3},
    "planets": {"Moon": {"sign": "Oğlak", "deg": 10}},
}


def test_turkish_mid_2025_is_moved_into_the_future():
    out = _correct_past_date_hallucination(
        "Cevap 2025 ortalarında netleşir.", CHART, "tr")
    assert "2025" not in out
    assert "2027" in out


def test_english_mid_2025_is_moved_into_the_future():
    out = _correct_past_date_hallucination(
        "It should settle around mid-2025.", CHART, "en")
    assert "2025" not in out
    assert "2027" in out


def test_spanish_mid_2025_is_moved_into_the_future():
    out = _correct_past_date_hallucination(
        "Se resolverá a mediados de 2025.", CHART, "es")
    assert "2025" not in out
    assert "2027" in out


def test_birth_years_are_not_touched():
    text = "1990 doğumlu kişi 2026'da karar verir."
    assert _correct_past_date_hallucination(text, CHART, "tr") == text


def test_future_years_are_kept():
    text = "2028 yılında netleşir."
    assert _correct_past_date_hallucination(text, CHART, "tr") == text


def test_prompt_contains_the_cast_date_lock():
    prompt = build_prompt(CHART, "tr")
    assert "2026-11-06" in prompt
    assert "TARİH KİLİDİ" in prompt
    assert "Never output a date or year before today" in prompt
