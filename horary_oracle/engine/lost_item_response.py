"""Useful, bounded search guidance for Horary lost-object questions.

This turns the chart's already-computed location testimonies into a short
prioritized search plan. It does not claim GPS-level or verified location.
"""
from __future__ import annotations

import re


_ITEM_LABELS = (
    (("telefon", "phone", "móvil", "movil", "teléfono"), "telefon", "phone", "teléfono"),
    (("anahtar", "keys", "key", "llave", "llaves"), "anahtar", "keys", "llaves"),
    (("cüzdan", "cuzdan", "wallet", "cartera"), "cüzdan", "wallet", "cartera"),
    (("çanta", "canta", "bag", "bolso", "mochila"), "çanta", "bag", "bolso"),
    (("gözlük", "gozluk", "glasses", "gafas"), "gözlük", "glasses", "gafas"),
    (("yüzük", "yuzuk", "ring", "anillo"), "yüzük", "ring", "anillo"),
    (("saat", "watch", "reloj"), "saat", "watch", "reloj"),
    (("evrak", "belge", "document", "paper", "documento", "papeles"), "evrak", "documents", "documentos"),
    (("kulaklık", "kulaklik", "earbud", "headphone", "auricular"), "kulaklık", "earbuds", "auriculares"),
)

_SIGN_HINTS = {
    "Koç": ("giriş/koridor, sıcak bir nokta veya sık kullanılan yüzey", "entryway/hall, a warm spot or a frequently used surface", "entrada/pasillo, un lugar cálido o una superficie de uso frecuente"),
    "Boğa": ("kıyafet, çekmece, değerli eşya kutusu ya da sabit bir yüzey", "clothing, a drawer, a valuables box or a stable surface", "ropa, un cajón, un joyero o una superficie estable"),
    "İkizler": ("çalışma masası, kitap/evrak, telefon ya da iki eşya arasındaki bölge", "desk, books/papers, a phone area or a space between two objects", "escritorio, libros/documentos, zona del teléfono o entre dos objetos"),
    "Yengeç": ("mutfak/yatak odası, kumaşların veya aile eşyalarının yakını", "kitchen/bedroom, near fabric or family belongings", "cocina/dormitorio, cerca de telas o pertenencias familiares"),
    "Aslan": ("hobi/çocuk/dinlenme alanı; aydınlık ve sıcak bir nokta", "hobby/children's/rest area; a bright, warm spot", "zona de ocio/niños/descanso; un lugar luminoso y cálido"),
    "Başak": ("çalışma alanı, düzenleme/temizlik malzemeleri ve küçük bölmeler", "work area, organizing/cleaning supplies and small compartments", "zona de trabajo, artículos de orden/limpieza y compartimentos pequeños"),
    "Terazi": ("salon veya misafir alanı; ayna, pencere, sehpa, kıyafet ya da çanta çevresi", "living or guest area; near a mirror, window, coffee table, clothing or a bag", "salón o zona de invitados; cerca de un espejo, ventana, mesa auxiliar, ropa o bolso"),
    "Akrep": ("kapalı/karanlık bir bölme; banyo veya bir eşyanın altı/arkası", "a closed/dim compartment; bathroom or beneath/behind another object", "un compartimento cerrado/oscuro; baño o debajo/detrás de otro objeto"),
    "Yay": ("kitaplık, çalışma/ibadet köşesi veya seyahat çantalarının yakını", "bookshelf, study/prayer corner or near travel bags", "estantería, rincón de estudio/lectura o cerca del equipaje"),
    "Oğlak": ("iş/çalışma alanı, depo veya kapalı bir dolap/çekmece", "work area, storage room or a closed cabinet/drawer", "zona de trabajo, almacén o armario/cajón cerrado"),
    "Kova": ("elektronik cihazların, kabloların veya çalışma masasının yakını", "near electronics, cables or a desk", "cerca de aparatos electrónicos, cables o un escritorio"),
    "Balık": ("yatak odası/banyo; yumuşak kumaşlar, ayakkabılar veya kapalı bir köşe", "bedroom/bathroom; soft fabrics, shoes or a tucked-away corner", "dormitorio/baño; telas blandas, zapatos o un rincón apartado"),
}

_HOUSE_HINTS = {
    1: ("kişinin üzerinde, çantasında veya her gün kullandığı yerde", "on the person, in their bag or where they use things daily", "encima de la persona, en su bolso o donde usa las cosas a diario"),
    2: ("kişisel eşya/değerli eşya alanında", "a personal or valuables area", "una zona de objetos personales o de valor"),
    3: ("giriş, araç, kısa yol/ulaşım ya da telefon-kitapların olduğu yerde", "entryway, vehicle, short route/transport or near books/phone", "entrada, vehículo, trayecto/transporte o cerca de libros/teléfono"),
    4: ("evin iç/alt bölümü, mutfak, kiler veya eski bir dolapta", "inside/lower part of the home, kitchen, pantry or an old cabinet", "interior/zona baja de la casa, cocina, despensa o un armario antiguo"),
    5: ("dinlenme, hobi veya çocukların kullandığı alanda", "a rest, hobby or children's area", "una zona de descanso, afición o de los niños"),
    6: ("günlük iş/rutin, temizlik veya bakım malzemelerinin yanında", "near daily routines, cleaning or care supplies", "cerca de rutinas diarias, limpieza o artículos de cuidado"),
    7: ("ortak kullanılan ya da başka birinin sık kullandığı alanda; salon/misafir bölümü", "a shared or another person's frequently used area; living/guest room", "una zona compartida o de uso frecuente por otra persona; salón/visitas"),
    8: ("kapalı bir bölme, banyo veya başka eşyaların altında/arkasında", "a closed compartment, bathroom or beneath/behind other belongings", "un compartimento cerrado, baño o debajo/detrás de otras pertenencias"),
    9: ("kitap/evrak, eğitim veya seyahat eşyalarının bulunduğu yerde", "near books/papers, study or travel belongings", "cerca de libros/documentos, estudio o artículos de viaje"),
    10: ("iş/çalışma masası, bilgisayar veya resmî evrakların yanında", "near a work desk, computer or official papers", "cerca del escritorio, ordenador o documentos oficiales"),
    11: ("misafir/sosyal alan, teras/balkon veya elektronik eşyaların yanında", "guest/social area, terrace/balcony or near electronics", "zona social/de visitas, terraza/balcón o cerca de aparatos electrónicos"),
    12: ("yatak odası, dolap, yastık-yorgan veya gözden uzak kapalı bir köşede", "bedroom, wardrobe, bedding or a secluded closed corner", "dormitorio, armario, ropa de cama o un rincón cerrado y apartado"),
}

_DIRECTION_LABELS = {
    "K": ("Kuzey", "North", "Norte"), "KKD": ("Kuzey-kuzeydoğu", "North-northeast", "Nornoreste"),
    "KD": ("Kuzeydoğu", "Northeast", "Noreste"), "DKD": ("Doğu-kuzeydoğu", "East-northeast", "Estenoreste"),
    "D": ("Doğu", "East", "Este"), "DGD": ("Doğu-güneydoğu", "East-southeast", "Estesudeste"),
    "GD": ("Güneydoğu", "Southeast", "Sureste"), "GGD": ("Güney-güneydoğu", "South-southeast", "Sursureste"),
    "G": ("Güney", "South", "Sur"), "GGB": ("Güney-güneybatı", "South-southwest", "Sursuroeste"),
    "GB": ("Güneybatı", "Southwest", "Suroeste"), "BGB": ("Batı-güneybatı", "West-southwest", "Oestesuroeste"),
    "B": ("Batı", "West", "Oeste"), "BKB": ("Batı-kuzeybatı", "West-northwest", "Oestenoroeste"),
    "KB": ("Kuzeybatı", "Northwest", "Noroeste"), "KKB": ("Kuzey-kuzeybatı", "North-northwest", "Nornoroeste"),
}

_SIGNS = {
    "Koç": ("Aries", "Aries"), "Boğa": ("Taurus", "Tauro"), "İkizler": ("Gemini", "Géminis"),
    "Yengeç": ("Cancer", "Cáncer"), "Aslan": ("Leo", "Leo"), "Başak": ("Virgo", "Virgo"),
    "Terazi": ("Libra", "Libra"), "Akrep": ("Scorpio", "Escorpio"), "Yay": ("Sagittarius", "Sagitario"),
    "Oğlak": ("Capricorn", "Capricornio"), "Kova": ("Aquarius", "Acuario"), "Balık": ("Pisces", "Piscis"),
}
_PLANETS = {
    "Sun": ("Sun", "Sol"), "Moon": ("Moon", "Luna"), "Mercury": ("Mercury", "Mercurio"),
    "Venus": ("Venus", "Venus"), "Mars": ("Mars", "Marte"), "Jupiter": ("Jupiter", "Júpiter"),
    "Saturn": ("Saturn", "Saturno"),
}

_COPY = {
    "tr": {
        "intro": "İlk arama önceliği",
        "why": "Harita ipucu",
        "search": "Şöyle ara",
        "direction": "Yön ipucu",
        "distance": "Uzaklık bandı",
        "weak": "Yön/uzaklık göstergesinin doğrulama güveni düşük veya yetersiz; bu nedenle km tahmini vermiyorum.",
        "caution": "Bunlar GPS veya kesin adres değil, haritadaki sembolik arama ipuçlarıdır. Eşyanın tam yerini ya da bulunacağını garanti etmez.",
        "action": "Önce son kullandığın güzergâhı ve bu alanlardaki görünmeyen küçük bölmeleri tek tek kontrol et; mümkünse evdeki diğer kişilere de nereleri toparladıklarını sor.",
        "favorable": "Eşya göstergesinin kendi burcunda ve köşe evde olması, horary sembolizminde izinin belirgin olabileceğine dair olumlu bir işaret; kesin bulunma sözü değildir.",
    },
    "en": {
        "intro": "First search priority",
        "why": "Chart clue",
        "search": "Search in this order",
        "direction": "Directional clue",
        "distance": "Distance band",
        "weak": "The direction/distance model has low or insufficient validation confidence, so I will not give a kilometre estimate.",
        "caution": "These are symbolic chart-based search clues, not GPS or a verified address. They cannot guarantee the item's exact location or recovery.",
        "action": "Retrace the last-use route and check small hidden compartments in those areas one by one; ask others at home what they may have moved.",
        "favorable": "The item's ruler being in its own sign and an angular house is a favorable symbolic clue that its trail may be distinct, not a promise of recovery.",
    },
    "es": {
        "intro": "Primera prioridad de búsqueda",
        "why": "Pista de la carta",
        "search": "Busca en este orden",
        "direction": "Pista de dirección",
        "distance": "Rango de distancia",
        "weak": "La confianza validada del modelo de dirección/distancia es baja o insuficiente; por eso no doy una estimación en kilómetros.",
        "caution": "Son pistas simbólicas basadas en la carta, no GPS ni una dirección verificada. No garantizan el lugar exacto ni que se recupere el objeto.",
        "action": "Repite el recorrido desde el último uso y revisa uno por uno los compartimentos pequeños y ocultos; pregunta también a quienes estén en casa si movieron algo.",
        "favorable": "Que el regente del objeto esté en su propio signo y en una casa angular es una pista simbólica favorable de que su rastro puede ser claro, no una garantía de recuperación.",
    },
}


def _lost_item_question(question: str, location: dict) -> bool:
    if location.get("subject_type") == "person":
        return False
    q = (question or "").lower()
    if location.get("_object"):
        return True
    try:
        from engine.derived_houses import lost_item_offset
        if lost_item_offset(q):
            return True
    except Exception:
        pass
    has_where = any(w in q for w in ("nerede", "nerde", "where", "dónde", "donde"))
    has_lost = any(w in q for w in ("kayıp", "kayip", "kaybol", "lost", "missing", "perdido", "perdida"))
    has_object = any(w in q for w in ("eşya", "esya", "item", "thing", "objeto", "pertenencia"))
    return has_where and has_lost and has_object


def _item_label(question: str, location: dict, lang: str) -> str:
    q = (question or "").lower()
    object_hint = str(location.get("_object", "")).lower()
    for words, tr, en, es in _ITEM_LABELS:
        if any(word in q or word in object_hint for word in words):
            return {"tr": tr, "en": en, "es": es}[lang]
    return {"tr": "eşya", "en": "item", "es": "objeto"}[lang]


def _confidence_is_usable(geo: dict) -> bool:
    label = str(geo.get("direction_confidence", "")).strip().lower()
    n = int(geo.get("direction_n") or 0)
    return n > 0 and label in {"orta", "iyi", "medium", "good", "strong", "high"}


def build_lost_item_answer(engine_json: dict, lang: str = "tr") -> str | None:
    """Build actionable, cautious search guidance from chart output, if eligible."""
    if engine_json.get("verdict") != "LOCATION":
        return None
    location = engine_json.get("location") or {}
    if not isinstance(location, dict) or not _lost_item_question(engine_json.get("question", ""), location):
        return None

    lang = lang if lang in _COPY else "en"
    copy = _COPY[lang]
    geo = location.get("horary_geo") or {}
    house = location.get("house")
    try:
        house = int(house)
    except (TypeError, ValueError):
        house = None
    sign = str(location.get("sign") or "")
    ruler = str(location.get("sig_planet") or location.get("_natural") or "")
    degree = location.get("deg")
    item = _item_label(engine_json.get("question", ""), location, lang)
    house_hints = _HOUSE_HINTS.get(house, ("", "", ""))[{"tr": 0, "en": 1, "es": 2}[lang]]
    sign_hints = _SIGN_HINTS.get(sign, ("", "", ""))[{"tr": 0, "en": 1, "es": 2}[lang]]

    lines = [f"{copy['intro']}: {house_hints or sign_hints or item}."]
    planet = engine_json.get("planets", {}).get(ruler, {})
    planet_sign = str(planet.get("sign") or sign)
    planet_house = planet.get("house", house)
    planet_deg = planet.get("deg", degree)
    if ruler and planet_sign:
        display_ruler = ruler if lang == "tr" else _PLANETS.get(ruler, (ruler, ruler))[{"en": 0, "es": 1}[lang]]
        display_sign = planet_sign if lang == "tr" else _SIGNS.get(planet_sign, (planet_sign, planet_sign))[{"en": 0, "es": 1}[lang]]
        placement = f"{display_ruler} {display_sign}"
        if planet_deg is not None:
            placement += f" {float(planet_deg):.1f}°"
        if planet_house is not None:
            placement += (f", {planet_house}. ev" if lang == "tr" else
                          (f", {planet_house}{'th' if int(planet_house) not in (1, 2, 3) else {1: 'st', 2: 'nd', 3: 'rd'}[int(planet_house)]} house" if lang == "en" else f", casa {planet_house}"))
        if lang == "tr":
            lines.append(f"{copy['why']}: {item} göstergesi {placement}. {house_hints or sign_hints}")
        elif lang == "es":
            lines.append(f"{copy['why']}: el regente del {item} es {placement}. {house_hints or sign_hints}")
        else:
            lines.append(f"{copy['why']}: the ruler of the {item} is {placement}. {house_hints or sign_hints}")
    elif house_hints or sign_hints:
        lines.append(f"{copy['why']}: {house_hints or sign_hints}.")

    direction_code = geo.get("yon")
    direction = geo.get("yon_label") or location.get("direction")
    azimuth = geo.get("azimut")
    if direction_code in _DIRECTION_LABELS:
        direction = _DIRECTION_LABELS[direction_code][{"tr": 0, "en": 1, "es": 2}[lang]]
    if direction or azimuth is not None:
        direction_text = str(direction or "")
        if azimuth is not None:
            try:
                direction_text += f" — azimut {float(azimuth):.0f}°" if lang == "tr" else f" — azimuth {float(azimuth):.0f}°"
            except (TypeError, ValueError):
                pass
        confidence = str(geo.get("direction_confidence") or "").strip()
        if confidence and confidence.lower() not in {"bilinmiyor", "unknown"}:
            if lang == "en":
                confidence = {"düşük": "low confidence", "orta": "moderate confidence", "iyi": "good confidence"}.get(confidence.lower(), confidence)
            elif lang == "es":
                confidence = {"düşük": "confianza baja", "orta": "confianza moderada", "iyi": "confianza buena"}.get(confidence.lower(), confidence)
            direction_text += f" ({confidence})"
        lines.append(f"{copy['direction']}: {direction_text}.")

    # Kilometre tahmini yalnızca kalibrasyon kaydı ve orta/iyi yön doğrulaması varsa.
    if _confidence_is_usable(geo) and geo.get("band"):
        lines.append(f"{copy['distance']}: {geo['band']}.")
    else:
        lines.append(copy["weak"])

    if lang == "tr":
        lines.append(f"{copy['search']}: önce {house_hints or sign_hints}; ardından {sign_hints or house_hints}; özellikle koltuk/sehpa çevresi, ayna-pencere yanı, çanta ve kıyafet cepleri ile başka eşyaların altı/arkası.")
    elif lang == "en":
        lines.append(f"{copy['search']}: first {house_hints or sign_hints}; then {sign_hints or house_hints}; especially around the sofa/table, mirror/window, bag and clothing pockets, and under/behind other belongings.")
    else:
        lines.append(f"{copy['search']}: primero {house_hints or sign_hints}; después {sign_hints or house_hints}; especialmente sofá/mesa, espejo/ventana, bolsos y bolsillos, y debajo/detrás de otras cosas.")

    try:
        from core.ephemeris import DOMICILE_TRADITIONAL
        in_own_sign = DOMICILE_TRADITIONAL.get(planet_sign) == ruler
    except Exception:
        in_own_sign = False
    if house in (1, 4, 7, 10) and ruler and planet_sign and in_own_sign:
        lines.append(copy["favorable"])
    lines.append(copy["action"])
    lines.append(copy["caution"])
    return "\n\n".join(lines)
