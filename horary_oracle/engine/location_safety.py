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

_HOUSE_THEMES = {
    "tr": {
        1: "soranın yakın çevresi ve kişinin kendi gündelik alanı",
        2: "kişisel eşyalar değil, alışılmış günlük yaşam ve kaynak çevresi",
        3: "yakın çevre, öğrenim, haberleşme veya kısa yol",
        4: "ev, aile, kökler ya da tanıdık özel çevre",
        5: "sosyal/yaratıcı ortam, eğlence veya çocuklarla ilgili alan",
        6: "günlük iş, rutin, hizmet veya sağlık ortamı",
        7: "başkalarıyla yüz yüze olunan ortak veya sosyal ortam",
        8: "paylaşılan veya mahrem bir ortam",
        9: "eğitim kurumu, yüksek öğrenim veya uzak yol teması",
        10: "resmi kurum, iş veya görünür sorumluluk alanı",
        11: "arkadaş çevresi, grup veya topluluk",
        12: "daha kapalı, geri planda veya inzivaya uygun ortam",
    },
    "en": {
        1: "the person's immediate surroundings and everyday personal space",
        2: "familiar daily-life and resource settings",
        3: "nearby surroundings, learning, communication, or a short trip",
        4: "home, family, roots, or a familiar private setting",
        5: "social or creative settings, recreation, or children-related places",
        6: "daily work, routines, service, or health settings",
        7: "a shared or social setting with other people",
        8: "a shared or private setting",
        9: "an educational institution, higher learning, or long-distance travel",
        10: "an official institution, work, or a visible responsibility",
        11: "friends, groups, or a community",
        12: "a more private, secluded, or withdrawn setting",
    },
    "es": {
        1: "el entorno inmediato y el espacio cotidiano de la persona",
        2: "entornos habituales de la vida diaria y los recursos personales",
        3: "el entorno cercano, el estudio, la comunicación o un trayecto corto",
        4: "el hogar, la familia, las raíces o un entorno privado conocido",
        5: "un entorno social o creativo, recreativo o relacionado con niños",
        6: "el trabajo diario, las rutinas, los servicios o la salud",
        7: "un entorno compartido o social con otras personas",
        8: "un entorno compartido o privado",
        9: "un centro educativo, estudios superiores o un viaje largo",
        10: "una institución oficial, el trabajo o una responsabilidad visible",
        11: "amistades, grupos o una comunidad",
        12: "un entorno más privado, apartado o de retiro",
    },
}
_TR_PLANETS = {
    "Sun": "Güneş", "Moon": "Ay", "Mercury": "Merkür", "Venus": "Venüs",
    "Mars": "Mars", "Jupiter": "Jüpiter", "Saturn": "Satürn",
}


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


def person_location_answer(
    language: str,
    subject: str,
    reported_missing: bool,
    context: dict | None = None,
) -> str:
    """Give a chart-grounded symbolic environment, never a claimed live address."""
    language = (language or "en").lower()
    language = language if language in _HOUSE_THEMES else "en"
    context = context or {}
    theme = _HOUSE_THEMES[language].get(context.get("house"))
    target_house = context.get("_derived_house")
    planet = context.get("sig_planet")
    if language == "tr" and planet:
        planet = _TR_PLANETS.get(planet, planet)
    sign = context.get("sign")
    position_house = context.get("house")
    trust = context.get("trust_level")

    if language == "tr":
        lines = [f"Anladığım: {subject} şu anda nerede olabilir diye soruyorsun."]
        if target_house:
            lines.append(
                f"Horary'de {subject.lower()} {target_house}. ev göstergesiyle ele alınıyor."
            )
        if planet and sign and position_house:
            lines.append(
                f"Göstergesi {planet} {sign} burcunda, {position_house}. evde."
            )
        if theme:
            lines.append(f"Bu yerleşim sembolik olarak {theme} temasını öne çıkarıyor.")
        if trust == "zayif":
            lines.append(
                "Bu soru türünde yön doğrulamamız zayıf; bu yüzden kesin pusula yönü "
                "ve kilometre vermiyorum. Bu, gerçek konum/adres tespiti değil, horary "
                "sembolizmine dayalı genel bir ortam ipucudur."
            )
        else:
            lines.append(
                "Bunu doğrulanmış gerçek konum değil, horary sembolizmine dayalı genel bir "
                "ortam ipucu olarak değerlendir."
            )
        if reported_missing:
            lines.append(
                "Gerçekten kayıpsa veya güvenliğinden endişe ediyorsan öğrenciyi ve gerekiyorsa "
                "okul/veliyi doğrudan ara; acil riskte yerel yetkililere başvur."
            )
        return " ".join(lines)

    if language == "es":
        if theme:
            return (
                f"Entiendo que preguntas dónde podría estar {subject}. En horaria se representa "
                f"mediante la casa {target_house or 'correspondiente'}; su significador está en "
                f"la casa {position_house or '?'}, lo que simbólicamente destaca {theme}. "
                "Es una pista astrológica general, no una ubicación real verificada ni una dirección."
                + (" Si realmente ha desaparecido o hay riesgo, contacta con la escuela, sus responsables o los servicios locales." if reported_missing else "")
            )
    if theme:
        result = (
            f"I understand you are asking where {subject} might be. In horary, the person is "
            f"represented by house {target_house or 'the relevant turned house'}; the significator "
            f"is in house {position_house or '?'}, symbolically highlighting {theme}. This is a "
            "general astrological theme, not a verified live location or address."
        )
        if trust == "zayif":
            result += " Direction and distance are not reliable for this question type, so I won't give a compass bearing or kilometers."
        if reported_missing:
            result += " If the person is actually missing or at risk, contact the school/guardian and local authorities as appropriate."
        return result

    return (
        f"I understand you are asking where {subject} might be. The chart does not provide "
        "a reliable location clue for this question, so I won't invent a place or distance. "
        "If they are actually missing or at risk, contact them, the school/guardian, or local help."
    )
