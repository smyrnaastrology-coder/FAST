"""A restrained, deterministic checklist for lost-object location questions.

Only describes symbolic location clues. It deliberately does NOT infer whether
the object will be found, whether it is permanently lost, or when someone will
find it. Do not turn symbols into an exact address, room, direction, or distance.
"""

from core.ephemeris import DOMICILE_TRADITIONAL, SIGNS_EN, SIGNS_TR, house_of_planet, sign_from_lon

_SIGNS_ES = {
    "Koç": "Aries", "Boğa": "Tauro", "İkizler": "Géminis", "Yengeç": "Cáncer",
    "Aslan": "Leo", "Başak": "Virgo", "Terazi": "Libra", "Akrep": "Escorpio",
    "Yay": "Sagitario", "Oğlak": "Capricornio", "Kova": "Acuario", "Balık": "Piscis",
}
_PLANETS = {
    "tr": {"Sun": "Güneş", "Moon": "Ay", "Mercury": "Merkür", "Venus": "Venüs", "Mars": "Mars", "Jupiter": "Jüpiter", "Saturn": "Satürn", "Uranus": "Uranüs", "Neptune": "Neptün", "Pluto": "Plüton"},
    "es": {"Sun": "Sol", "Moon": "Luna", "Mercury": "Mercurio", "Venus": "Venus", "Mars": "Marte", "Jupiter": "Júpiter", "Saturn": "Saturno", "Uranus": "Urano", "Neptune": "Neptuno", "Pluto": "Plutón"},
}


def _lang(value):
    return value if value in ("tr", "en", "es") else "en"


def _sign(sign_tr, lang):
    if lang == "tr":
        return sign_tr
    if lang == "es":
        return _SIGNS_ES.get(sign_tr, sign_tr)
    try:
        return SIGNS_EN[SIGNS_TR.index(sign_tr)]
    except ValueError:
        return sign_tr


def _planet(planet, lang):
    if lang == "en":
        return planet
    return _PLANETS.get(lang, {}).get(planet, planet)


def _placement(data, lang):
    if not data:
        return "?"
    sign = _sign(data.get("sign", ""), lang)
    deg = data.get("deg")
    house = data.get("house")
    if lang == "tr":
        return f"{sign} {deg:.1f}°, {house}. evde" if deg is not None and house else sign
    if lang == "es":
        return f"{sign} {deg:.1f}°, en la casa {house}" if deg is not None and house else sign
    return f"{sign} {deg:.1f}°, in house {house}" if deg is not None and house else sign


def build_lost_object_brief(res, qtype, lang="tr"):
    """Return symbolic location clues, or None for non-lost-object questions."""
    if qtype != "lost_object":
        return None
    try:
        lang = _lang(lang)
        cusps = res["houses"]["cusps"]
        planets = res.get("planets") or {}
        # The lost item is primarily represented by the traditional ruler of house 2.
        second_sign = sign_from_lon(cusps[1])
        ruler = DOMICILE_TRADITIONAL.get(second_sign, "Moon")
        item = planets.get(ruler) or {}

        pof = (res.get("lots") or {}).get("POF")
        pof_house = house_of_planet(pof, cusps) if pof is not None else None
        pof_sign = sign_from_lon(pof) if pof is not None else None
        pof_ruler = DOMICILE_TRADITIONAL.get(pof_sign, "Jupiter") if pof_sign else None
        pof_lord = planets.get(pof_ruler) or {} if pof_ruler else {}
        item_lord = DOMICILE_TRADITIONAL.get(item.get("sign", ""), "Mercury") if item else "Mercury"
        item_lord_data = planets.get(item_lord) or {}

        if lang == "tr":
            lines = [
                "Kayıp eşya — sembolik konum ipuçları (klasik horary):",
                f"• Eşyanın ana göstergesi: 2. ev ({_sign(second_sign, lang)}) yöneticisi {_planet(ruler, lang)}, {_placement(item, lang)}.",
            ]
            if pof is not None and pof_house:
                lines.append(f"• Şans Noktası: {_sign(pof_sign, lang)}, {pof % 30:.1f}°, {pof_house}. evde; yöneticisi {_planet(pof_ruler, lang)}, {_placement(pof_lord, lang)}.")
            if item_lord_data:
                lines.append(f"• Ay'ın burç yöneticisi: {_planet(item_lord, lang)}, {_placement(item_lord_data, lang)}.")
            clues = []
            if item.get("sign") == "Başak" or item.get("house") == 6:
                clues.append("kapalı saklama yerleri, dolap/kap, göz önünde olmayan bir yer veya cep/giysi içi")
            if item.get("house") == 3:
                clues.append("yakın çevre, geçiş/günlük eşya alanları")
            if item.get("sign") == "Başak":
                clues.append("Ay'ın doğal teması olarak mutfak ikincil bir kontrol ipucu olabilir")
            if pof_sign == "Yay" or (pof_lord and pof_lord.get("sign") == "Kova") or item_lord_data.get("house") == 9:
                clues.append("yüksek bir konum veya raf")
            if clues:
                lines.append("• Sembolik ortam temaları: " + "; ".join(dict.fromkeys(clues)) + ".")
            lines.append("Bunlar sembolik konum ipuçlarıdır; kesin oda veya eşya tarifi değildir.")
        elif lang == "es":
            lines = [
                "Objeto perdido — pistas simbólicas de ubicación (horaria clásica):",
                f"• Significador principal: regente de la casa 2 ({_sign(second_sign, lang)}), {_planet(ruler, lang)}, {_placement(item, lang)}.",
            ]
            if pof is not None and pof_house:
                lines.append(f"• Parte de la Fortuna: {_sign(pof_sign, lang)}, casa {pof_house}; su regente {_planet(pof_ruler, lang)}, {_placement(pof_lord, lang)}.")
            if item_lord_data:
                lines.append(f"• Regente del signo lunar: {_planet(item_lord, lang)}, {_placement(item_lord_data, lang)}.")
            clues = []
            if item.get("sign") == "Başak" or item.get("house") == 6:
                clues.append("un recipiente o armario cerrado, un lugar poco visible, o dentro de un bolsillo/prenda")
            if item.get("house") == 3:
                clues.append("el entorno cercano o zonas de paso y objetos cotidianos")
            if pof_sign == "Yay" or (pof_lord and pof_lord.get("sign") == "Kova") or item_lord_data.get("house") == 9:
                clues.append("una posición elevada o un estante alto")
            if clues:
                lines.append("• Temas simbólicos del entorno: " + "; ".join(dict.fromkeys(clues)) + ".")
            lines.append("Son pistas simbólicas, no una habitación ni un objeto exactos.")
        else:
            lines = [
                "Lost object — symbolic location clues (classical horary):",
                f"• Main significator: ruler of the 2nd house ({_sign(second_sign, lang)}), {_planet(ruler, lang)}, {_placement(item, lang)}.",
            ]
            if pof is not None and pof_house:
                lines.append(f"• Part of Fortune: {_sign(pof_sign, lang)}, house {pof_house}; its ruler {_planet(pof_ruler, lang)}, {_placement(pof_lord, lang)}.")
            if item_lord_data:
                lines.append(f"• Ruler of the Moon's sign: {_planet(item_lord, lang)}, {_placement(item_lord_data, lang)}.")
            clues = []
            if item.get("sign") == "Başak" or item.get("house") == 6:
                clues.append("a closed container/cupboard, somewhere out of sight, or inside a pocket/garment")
            if item.get("house") == 3:
                clues.append("the nearby environment, passage areas, or everyday belongings")
            if pof_sign == "Yay" or (pof_lord and pof_lord.get("sign") == "Kova") or item_lord_data.get("house") == 9:
                clues.append("an elevated place or high shelf")
            if clues:
                lines.append("• Symbolic environment themes: " + "; ".join(dict.fromkeys(clues)) + ".")
            lines.append("These are symbolic location clues, not an exact room or object.")
        return "\n".join(lines)
    except Exception:
        return None
