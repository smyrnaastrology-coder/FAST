"""Safety and intent handling for horary questions about a real person's location.

Astrological chart data cannot verify anyone's live physical location. Keep
person-location questions out of the lost-object prompt and avoid fabricated
directions, distances, rooms, or cities. Instead, translate the significator's
sign/house into a symbolic *kind of environment* (school routine, home, group
setting, ...), and say plainly that it is symbolism, not a verified address.
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
_STUDENT_TYPES = {"student", "astrology_student"}
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

# House -> kind of environment. Student variant speaks to school/course life;
# the general variant stays valid for any adult (parent, friend, teacher).
_THEMES = {
    "tr": {
        "student": {
            1: "kişinin kendi yakın çevresi; sınıf, atölye ya da hemen yanı başındaki bir ortam",
            2: "kantin, kırtasiye, harçlık/burs işleri gibi günlük ihtiyaç çevresi",
            3: "ders, kurs ya da okul çevresi; kısa bir yol veya ulaşım/iletişim hattı",
            4: "ev, yurt, aile yanı ya da tanıdık özel bir mekân",
            5: "ders dışı etkinlik, kulüp, spor/sanat çalışması ya da arkadaş buluşması",
            6: "okul, staj ya da iş rutini; ders programının geçtiği yerler, revir/sağlık gibi düzenli uğrak noktaları",
            7: "birlikte çalıştığı kişilerin yanı, özel ders/danışma ortamı ya da yüz yüze görüşülen bir yer",
            8: "yurt odası, kütüphane ya da ortak çalışma alanı gibi paylaşılan veya mahrem bir mekân",
            9: "üniversite, kurs merkezi, uzak eğitim, seyahat ya da yurt dışı bağlantılı bir yer",
            10: "okul yönetimi, resmi kurum, staj yeri ya da kariyerle ilgili görünür bir ortam",
            11: "arkadaş grubu, kulüp, kampüs topluluğu ya da bir etkinlik alanı",
            12: "sessiz/sakin bir köşe, kütüphane, istirahat ya da geri planda kalınan bir yer",
        },
        "person": {
            1: "kişinin kendi yakın çevresi ve gündelik alanı",
            2: "alışılmış günlük yaşam, alışveriş ve kaynak çevresi",
            3: "yakın çevre, haberleşme, kısa yol ya da kardeş/komşu çevresi",
            4: "ev, aile, kökler ya da tanıdık özel bir mekân",
            5: "sosyal/yaratıcı ortam, eğlence ya da çocuklarla ilgili bir alan",
            6: "günlük iş, rutin, hizmet ya da sağlık ortamı",
            7: "başkalarıyla yüz yüze olunan ortak veya sosyal bir ortam",
            8: "paylaşılan ya da mahrem bir ortam",
            9: "eğitim kurumu, yüksek öğrenim ya da uzak yol teması",
            10: "resmi kurum, iş ya da görünür sorumluluk alanı",
            11: "arkadaş çevresi, grup ya da topluluk",
            12: "daha kapalı, geri planda ya da inzivaya uygun bir ortam",
        },
    },
    "en": {
        "student": {
            1: "the person's immediate surroundings, such as a classroom, workshop, or somewhere right next to you",
            2: "everyday needs such as the canteen, stationery shop, or scholarship/allowance errands",
            3: "the lesson, course, or school surroundings, a short trip, or a transport/communication link",
            4: "home, a dormitory, staying with family, or a familiar private place",
            5: "an extracurricular activity, club, sport/art session, or meeting friends",
            6: "the school, internship, or work routine, places on the class schedule, or regular stops such as the infirmary",
            7: "being with people they work with, a tutoring/consultation setting, or a face-to-face meeting place",
            8: "a shared or private place such as a dorm room, library, or shared study area",
            9: "a university, course centre, distance study, travel, or an abroad-related place",
            10: "school administration, an official institution, an internship, or a career-related visible setting",
            11: "a friend group, club, campus community, or an event venue",
            12: "a quiet corner, library, rest area, or a place where they stay in the background",
        },
        "person": {
            1: "the person's immediate surroundings and everyday personal space",
            2: "familiar daily-life, shopping, and resource settings",
            3: "nearby surroundings, communication, a short trip, or the sibling/neighbour circle",
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
    },
    "es": {
        "student": {
            1: "el entorno inmediato de la persona, como un aula, un taller o un lugar justo a su lado",
            2: "necesidades cotidianas como la cafetería, la papelería o los trámites de beca y paga",
            3: "el entorno de la clase, el curso o la escuela, un trayecto corto o una vía de transporte/comunicación",
            4: "la casa, una residencia, el hogar familiar o un lugar privado conocido",
            5: "una actividad extraescolar, un club, una sesión de deporte/arte o una quedada con amistades",
            6: "la rutina del colegio, las prácticas o el trabajo, los lugares del horario lectivo o paradas habituales como la enfermería",
            7: "estar con las personas con quienes trabaja, una tutoría/consulta o un lugar de encuentro cara a cara",
            8: "un lugar compartido o privado como una habitación de residencia, la biblioteca o una sala de estudio común",
            9: "una universidad, un centro de cursos, estudio a distancia, un viaje o un lugar vinculado al extranjero",
            10: "la administración del centro, una institución oficial, unas prácticas o un entorno visible de carrera",
            11: "un grupo de amistades, un club, la comunidad del campus o un lugar de eventos",
            12: "un rincón tranquilo, la biblioteca, una zona de descanso o un lugar donde se mantiene en segundo plano",
        },
        "person": {
            1: "el entorno inmediato y el espacio cotidiano de la persona",
            2: "entornos habituales de la vida diaria, las compras y los recursos personales",
            3: "el entorno cercano, la comunicación, un trayecto corto o el círculo de hermanos y vecinos",
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
    },
}
_TR_PLANETS = {
    "Sun": "Güneş", "Moon": "Ay", "Mercury": "Merkür", "Venus": "Venüs",
    "Mars": "Mars", "Jupiter": "Jüpiter", "Saturn": "Satürn",
}
_TR_SIGNS = {
    "Koç": "Koç", "Boğa": "Boğa", "İkizler": "İkizler", "Yengeç": "Yengeç",
    "Aslan": "Aslan", "Başak": "Başak", "Terazi": "Terazi", "Akrep": "Akrep",
    "Yay": "Yay", "Oğlak": "Oğlak", "Kova": "Kova", "Balık": "Balık",
}
_ES_PLANETS = {
    "Sun": "Sol", "Moon": "Luna", "Mercury": "Mercurio", "Venus": "Venus",
    "Mars": "Marte", "Jupiter": "Júpiter", "Saturn": "Saturno",
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


def classical_significator(house_number, cusps, planets):
    """Ruler of a house cusp using traditional rulership (no Uranus/Neptune/Pluto).

    Traditional horary assigns Aquarius to Saturn and Scorpio to Mars, so the
    chart reading stays inside the classical tradition and we can say which
    tradition the significator came from.
    """
    try:
        from core.ephemeris import DOMICILE_TRADITIONAL, sign_from_lon
        cusp = cusps[int(house_number) - 1]
        ruler_sign = sign_from_lon(cusp)
        planet = DOMICILE_TRADITIONAL.get(ruler_sign)
        data = (planets or {}).get(planet) or {}
        return {
            "ruler_sign": ruler_sign,
            "planet": planet,
            "sign": data.get("sign"),
            "house": data.get("house"),
        }
    except Exception:
        return {}


def person_location_answer(
    language: str,
    subject: str,
    reported_missing: bool,
    context: dict | None = None,
) -> str:
    """Give a chart-grounded symbolic environment, never a claimed live address."""
    language = (language or "en").lower()
    language = language if language in _THEMES else "en"
    context = context or {}
    subject_type = context.get("subject_type") or "person"
    variant = "student" if subject_type in _STUDENT_TYPES else "person"
    target_house = context.get("_derived_house")
    position_house = context.get("house")
    theme = _THEMES[language][variant].get(position_house)
    planet = context.get("sig_planet")
    sign = context.get("sign")
    ruler_sign = context.get("ruler_sign")
    trust = context.get("trust_level")

    if language == "tr":
        if planet:
            planet = _TR_PLANETS.get(planet, planet)
        lines = [f"Anladığım: {subject} şu anda nerede olabilir diye soruyorsun."]
        if target_house and ruler_sign and planet:
            lines.append(
                f"Klasik horary'de {subject.lower()} {target_house}. evle temsil ediliyor; "
                f"bu evin burcu {ruler_sign}, klasik yöneticisi {planet}."
            )
        elif target_house:
            lines.append(
                f"Klasik horary'de {subject.lower()} {target_house}. evle temsil ediliyor."
            )
        if planet and sign and position_house:
            lines.append(
                f"Gösterge {planet} {sign} burcunda, {position_house}. evde."
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
        if planet:
            planet = _ES_PLANETS.get(planet, planet)
        lines = [f"Entiendo que preguntas dónde podría estar {subject}."]
        if target_house and ruler_sign and planet:
            lines.append(
                f"En horaria clásica se representa por la casa {target_house}; la cúspide "
                f"está en {ruler_sign} y su regente clásico es {planet}."
            )
        elif target_house:
            lines.append(f"En horaria clásica se representa por la casa {target_house}.")
        if planet and sign and position_house:
            lines.append(f"El significador {planet} está en {sign}, casa {position_house}.")
        if theme:
            lines.append(f"Esa posición destaca simbólicamente {theme}.")
        lines.append(
            "Es una pista astrológica general, no una ubicación real verificada ni una dirección."
        )
        if reported_missing:
            lines.append(
                "Si realmente ha desaparecido o hay riesgo, contacta con la escuela, sus "
                "responsables o los servicios locales."
            )
        return " ".join(lines)

    lines = [f"I understand you are asking where {subject} might be."]
    if target_house and ruler_sign and planet:
        lines.append(
            f"Classical horary represents them by house {target_house}; its cusp is "
            f"{ruler_sign} and its classical ruler is {planet}."
        )
    elif target_house:
        lines.append(f"Classical horary represents them by house {target_house}.")
    if planet and sign and position_house:
        lines.append(f"The significator {planet} is in {sign}, house {position_house}.")
    if theme:
        lines.append(f"That placement symbolically highlights {theme}.")
    lines.append("This is a general astrological theme, not a verified live location or address.")
    if trust == "zayif":
        lines.append(
            "Direction and distance are not reliable for this question type, so I won't "
            "give a compass bearing or kilometers."
        )
    if reported_missing:
        lines.append(
            "If the person is actually missing or at risk, contact the school/guardian and "
            "local authorities as appropriate."
        )
    return " ".join(lines)
