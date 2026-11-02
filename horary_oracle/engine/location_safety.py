"""Safety and intent handling for horary questions about a real person's location.

Astrological chart data cannot verify anyone's live physical location. Keep
person-location questions out of the lost-object prompt and avoid fabricated
directions, distances, rooms, or cities.
"""

import re

from engine.derived_houses import lost_item_offset
from engine.horary_questions import classify_question


_PERSON_TYPES = {
    "friend", "friend_of_friend", "partner", "spouse", "child", "mother",
    "father", "boss", "employer", "coworker", "employee", "sibling",
    "uncle", "court", "teacher", "hoca", "student", "astrology_student",
    "missing_person", "missing_child",
}
_WHERE_WORDS = (
    "nerede", "nerde", "nereye", "kaybol", "kayıp", "kayip", "where",
    "missing", "dónde", "donde",
)
_FOREIGN_ITEM_POSSESSION = re.compile(
    r"\b(?:my|his|her|their|the)\s+(?:student['’]s\s+)?"
    r"(?:bag|backpack|phone|wallet|book|keys|notebook|laptop|"
    r"mochila|bolso|cartera|teléfono|telefono|libro|llaves)\b"
    r"|\bstudent['’]s\s+(?:bag|backpack|phone|wallet|book|keys|notebook|laptop)\b"
    r"|\b(?:mochila|bolso|cartera)\s+del\s+estudiante\b",
    re.IGNORECASE,
)


def person_location_subject(question: str, quesited_type: str = "general"):
    """Return a person target; text intent outranks a stale UI object category."""
    q = (question or "").lower()
    if not any(word in q for word in _WHERE_WORDS):
        return None
    if lost_item_offset(q) or _FOREIGN_ITEM_POSSESSION.search(q):
        return None

    if any(word in q for word in ("öğrenci", "öğrencim", "ogrenci", "ogrencim")):
        return {"type": "student", "label": "Öğrenci"}
    if "student" in q:
        return {"type": "student", "label": "student"}
    if "estudiante" in q:
        return {"type": "student", "label": "estudiante"}

    classification = classify_question(question) or {}
    question_type = classification.get("type")
    if question_type in _PERSON_TYPES:
        return {
            "type": question_type,
            "label": classification.get("label") or "kişi",
        }
    if quesited_type in _PERSON_TYPES:
        labels = {
            "student": "öğrenci", "astrology_student": "astroloji öğrencisi",
            "teacher": "öğretmen", "hoca": "hoca",
            "missing_child": "çocuk", "missing_person": "kişi",
        }
        return {"type": quesited_type, "label": labels.get(quesited_type, "kişi")}
    return None


def person_location_answer(language: str, subject: str, reported_missing: bool) -> str:
    """A deterministic, non-speculative reply for a person's live location."""
    language = (language or "en").lower()
    if language == "tr":
        if reported_missing:
            return (
                f"Anladığım: {subject} için konum arıyorsun. Astrolojik harita bir kişinin "
                "gerçek zamanlı konumunu doğrulayamaz; yön, kilometre, şehir veya oda tahmini "
                "vermem doğru olmaz. Öğrenciyle ve gerekiyorsa okul/veliyle hemen iletişime "
                "geçip durumu doğrula. Güvenliğinden endişe ediyorsan yerel acil yardım veya "
                "yetkili birimlere başvur."
            )
        return (
            f"Anladığım: {subject} şu anda nerede diye soruyorsun. Astrolojik harita bir "
            "kişinin gerçek zamanlı konumunu doğrulayamaz; bu yüzden yön, kilometre, şehir "
            "veya oda tahmini uydurmamam gerekir. Öğrenciye doğrudan ulaşmayı ya da gerekiyorsa "
            "okul/veliyle teyit etmeyi dene. Gerçekten kayıp veya güvenlik riski varsa bunu "
            "belirtip uygun yerel destek birimlerine başvur."
        )
    if language == "es":
        if reported_missing:
            return (
                f"Entiendo que buscas a {subject}. Una carta astrológica no puede verificar "
                "la ubicación física en tiempo real de una persona; no sería responsable "
                "inventar una dirección, distancia, ciudad o habitación. Contacta cuanto antes "
                "con la persona y, si corresponde, con la escuela o sus responsables. Si temes "
                "por su seguridad, contacta con los servicios locales de emergencia."
            )
        return (
            f"Entiendo que preguntas dónde está {subject}. Una carta astrológica no puede "
            "verificar la ubicación física en tiempo real de una persona; no debo inventar "
            "una dirección, distancia, ciudad o habitación. Intenta contactar directamente "
            "con el estudiante o confirmar con la escuela o sus responsables. Si realmente "
            "está desaparecido o existe un riesgo, busca ayuda local adecuada."
        )
    if reported_missing:
        return (
            f"I understand that you are trying to locate {subject}. An astrological chart "
            "cannot verify a person's real-time physical location, so I shouldn't invent a "
            "direction, distance, city, or room. Contact the student and, where appropriate, "
            "the school or their guardian promptly. If you fear for their safety, contact "
            "local emergency services or the relevant authorities."
        )
    return (
        f"I understand you are asking where {subject} is right now. An astrological chart "
        "cannot verify a person's real-time physical location, so I shouldn't invent a "
        "direction, distance, city, or room. Try contacting the student directly or confirming "
        "with the school or their guardian. If they are actually missing or at risk, seek "
        "appropriate local help."
    )
