"""Deterministic sports checklist shown next to the horary verdict.

The engine already scores a match question, but the answer used to hide *why*.
This module prints the classical "sports horary" skeleton in plain language:

  team = 7th house (fan frame) or 1st house (own-team frame)
  rival = the opposite house
  team's 5th  = its success / performance
  team's 10th = its honour and the trophy
  sign rulers are taken from traditional rulership (Kova -> Saturn)
  plus the Moon's last/next aspect and the Part of Fortune's house

It only reports chart facts; it never invents a score or guarantees a result.
"""

from core.ephemeris import (
    DETRIMENT,
    DOMICILE_TRADITIONAL,
    EXALTATION,
    FALL,
    SIGNS_EN,
    SIGNS_TR,
    sign_from_lon,
)

_SIGNS_ES = {
    "Koç": "Aries", "Boğa": "Tauro", "İkizler": "Géminis", "Yengeç": "Cáncer",
    "Aslan": "Leo", "Başak": "Virgo", "Terazi": "Libra", "Akrep": "Escorpio",
    "Yay": "Sagitario", "Oğlak": "Capricornio", "Kova": "Acuario", "Balık": "Piscis",
}
_PLANETS_TR = {
    "Sun": "Güneş", "Moon": "Ay", "Mercury": "Merkür", "Venus": "Venüs",
    "Mars": "Mars", "Jupiter": "Jüpiter", "Saturn": "Satürn",
    "Uranus": "Uranüs", "Neptune": "Neptun", "Pluto": "Pluton",
}
_PLANETS_ES = {
    "Sun": "Sol", "Moon": "Luna", "Mercury": "Mercurio", "Venus": "Venus",
    "Mars": "Marte", "Jupiter": "Júpiter", "Saturn": "Saturno",
    "Uranus": "Urano", "Neptune": "Neptuno", "Pluto": "Plutón",
}
_ASPECTS = {
    "tr": {0: "kavuşum", 60: "sekstil", 90: "kare", 120: "üçgen", 180: "karşıtlık"},
    "en": {0: "conjunction", 60: "sextile", 90: "square", 120: "trine", 180: "opposition"},
    "es": {0: "conjunción", 60: "sextil", 90: "cuadratura", 120: "trígono", 180: "oposición"},
}
_FRAMES = {
    "tr": {"sport_fan": "taraftar çerçevesi", "sport_fav": "kendi takım çerçevesi", "sport_rival": "kendi takım çerçevesi"},
    "en": {"sport_fan": "supporter frame", "sport_fav": "own-team frame", "sport_rival": "own-team frame"},
    "es": {"sport_fan": "marco de aficionado", "sport_fav": "marco de equipo propio", "sport_rival": "marco de equipo propio"},
}
_VERDICTS = {
    "tr": {"YES": "EVET", "NO": "HAYIR", "UNCERTAIN": "KARARSIZ"},
    "en": {"YES": "YES", "NO": "NO", "UNCERTAIN": "UNCERTAIN"},
    "es": {"YES": "SÍ", "NO": "NO", "UNCERTAIN": "INCIERTO"},
}
_DIGNITY = {
    "tr": {"domicile": "kendi burcunda", "exaltation": "yücelmiş", "detriment": "zelil", "fall": "düşüşte"},
    "en": {"domicile": "in domicile", "exaltation": "exalted", "detriment": "in detriment", "fall": "in fall"},
    "es": {"domicile": "en domicilio", "exaltation": "exaltado", "detriment": "en detrimento", "fall": "en caída"},
}


def _lang(value):
    return value if value in ("tr", "en", "es") else "en"


def _sign_name(sign_tr, lang):
    if lang == "tr":
        return sign_tr
    if lang == "es":
        return _SIGNS_ES.get(sign_tr, sign_tr)
    try:
        return SIGNS_EN[SIGNS_TR.index(sign_tr)]
    except ValueError:
        return sign_tr


def _planet_name(planet, lang):
    if lang == "tr":
        return _PLANETS_TR.get(planet, planet)
    if lang == "es":
        return _PLANETS_ES.get(planet, planet)
    return planet


def _derived(base_house, offset):
    """Turned house: base_house's Nth house in chart numbering."""
    return ((base_house - 1) + (offset - 1)) % 12 + 1


def _house_of(lon, cusps):
    """Whole-chart house number for a longitude, using the cusps in order."""
    for i in range(12):
        start = cusps[i] % 360
        end = cusps[(i + 1) % 12] % 360
        if start <= end:
            if start <= lon % 360 < end:
                return i + 1
        elif lon % 360 >= start or lon % 360 < end:
            return i + 1
    return 1


def _dignity(planet, sign_tr):
    if DOMICILE_TRADITIONAL.get(sign_tr) == planet:
        return "domicile"
    if EXALTATION.get(sign_tr) == planet:
        return "exaltation"
    if DETRIMENT.get(sign_tr) == planet:
        return "detriment"
    if FALL.get(sign_tr) == planet:
        return "fall"
    return ""


def _placement(res, house_number, lang):
    """Ruler of a house cusp plus where that ruler actually sits."""
    cusps = res["houses"]["cusps"]
    cusp_sign = sign_from_lon(cusps[house_number - 1])
    planet = DOMICILE_TRADITIONAL.get(cusp_sign, "Saturn")
    data = (res.get("planets") or {}).get(planet) or {}
    return {
        "house": house_number,
        "cusp_sign": cusp_sign,
        "planet": planet,
        "sign": data.get("sign"),
        "deg": data.get("deg"),
        "pos_house": data.get("house") or _house_of(data.get("lon", 0), cusps),
        "retro": bool(data.get("retro")),
        "dignity": _dignity(planet, data.get("sign") or ""),
    }


def _placement_line(label, item, lang):
    bits = []
    if item.get("sign") is not None and item.get("deg") is not None:
        bits.append(f"{_sign_name(item['sign'], lang)} {item['deg'] % 30:.1f}°")
    if item.get("pos_house"):
        bits.append(
            {"tr": f"{item['pos_house']}. evde",
             "en": f"in house {item['pos_house']}",
             "es": f"en la casa {item['pos_house']}"}[lang]
        )
    if item.get("retro"):
        bits.append({"tr": "retro", "en": "retrograde", "es": "retrógrado"}[lang])
    dignity = _DIGNITY[lang].get(item.get("dignity") or "")
    if dignity:
        bits.append(dignity)
    detail = ", ".join(bits) if bits else "?"
    ruler = _planet_name(item["planet"], lang)
    return f"{label} {ruler}, {detail}"


def _moon_note(res, lang):
    last = next((s for s in res.get("strictures") or []
                 if s.get("code") == "moon_last_aspect"), None)
    nxt = next((s for s in res.get("strictures") or []
                if s.get("code") == "moon_next_aspect"), None)
    aspects = _ASPECTS[lang]
    parts = []
    if last:
        parts.append(
            {"tr": f"son açısı {_planet_name(last.get('with'), lang)} ile {aspects.get(last.get('angle'), '')} (geçmiş)",
             "en": f"last aspect {aspects.get(last.get('angle'), '')} to {last.get('with')} (past)",
             "es": f"último aspecto {aspects.get(last.get('angle'), '')} con {last.get('with')} (pasado)"}[lang]
        )
    if nxt:
        orb = nxt.get("dist")
        base = {"tr": f"yaklaşanı {_planet_name(nxt.get('with'), lang)} ile {aspects.get(nxt.get('angle'), '')}",
                "en": f"next aspect {aspects.get(nxt.get('angle'), '')} to {nxt.get('with')}",
                "es": f"siguiente aspecto {aspects.get(nxt.get('angle'), '')} con {nxt.get('with')}"}[lang]
        parts.append(base + (f" ({orb:.1f}°)" if isinstance(orb, (int, float)) else ""))
    if not parts:
        return None
    return "; ".join(parts)


def build_sport_brief(res, qtype, lang="tr"):
    """Return a localized, human-readable checklist, or None for non-sport questions."""
    if qtype not in ("sport_fan", "sport_fav", "sport_rival"):
        return None
    try:
        lang = _lang(lang)
        base = 7 if qtype == "sport_fan" else 1
        team = _placement(res, base, lang)
        rival = _placement(res, _derived(base, 7), lang)   # team's 7th = opponent
        success = _placement(res, _derived(base, 5), lang)
        honor = _placement(res, _derived(base, 10), lang)

        pof = (res.get("lots") or {}).get("POF")
        pof_house = _house_of(pof, res["houses"]["cusps"]) if pof is not None else None
        moon = _moon_note(res, lang)

        verdict = _VERDICTS[lang].get(res.get("verdict"), res.get("verdict"))
        score = res.get("score")
        frame = _FRAMES[lang].get(qtype, "")

        lines = []
        if lang == "tr":
            lines.append(f"Spor kontrol listesi (klasik horary — {frame}):")
            lines.append(f"• Takım: {base}. ev — {_placement_line('klasik yöneticisi', team, lang)}.")
            lines.append(f"• Rakip: {_derived(base, 7)}. ev — {_placement_line('klasik yöneticisi', rival, lang)}.")
            lines.append(
                f"• Takımın başarı evi (kendi 5.'si = haritanın {success['house']}.'si) — "
                f"{_placement_line('klasik yöneticisi', success, lang)}."
            )
            lines.append(
                f"• Takımın onur/zafer evi (kendi 10.'u = haritanın {honor['house']}.'sü) — "
                f"{_placement_line('klasik yöneticisi', honor, lang)}."
            )
            if pof_house:
                lines.append(f"• Şans Noktası haritanın {pof_house}. evinde.")
            if moon:
                lines.append(f"• Ay: {moon}.")
            lines.append(f"• Hüküm: {verdict} (skor {score}).")
            lines.append(
                "Not: göstergeler klasik yöneticilikten alındı; bu liste yorumun dayanağını "
                "gösterir, kesin sonuç garantisi değildir."
            )
        elif lang == "es":
            lines.append(f"Lista de control deportiva (horaria clásica — {frame}):")
            lines.append(f"• Equipo: casa {base} — {_placement_line('regente clásico', team, lang)}.")
            lines.append(f"• Rival: casa {_derived(base, 7)} — {_placement_line('regente clásico', rival, lang)}.")
            lines.append(
                f"• Casa del éxito del equipo (su 5.ª = casa {success['house']} de la carta) — "
                f"{_placement_line('regente clásico', success, lang)}."
            )
            lines.append(
                f"• Casa del honor/la victoria (su 10.ª = casa {honor['house']} de la carta) — "
                f"{_placement_line('regente clásico', honor, lang)}."
            )
            if pof_house:
                lines.append(f"• Parte de la Fortuna en la casa {pof_house} de la carta.")
            if moon:
                lines.append(f"• Luna: {moon}.")
            lines.append(f"• Fallo: {verdict} (puntuación {score}).")
            lines.append(
                "Nota: los regentes son clásicos; esta lista muestra en qué se apoya la lectura, "
                "no es una garantía de resultado."
            )
        else:
            lines.append(f"Sports checklist (classical horary — {frame}):")
            lines.append(f"• Team: house {base} — {_placement_line('classical ruler', team, lang)}.")
            lines.append(f"• Rival: house {_derived(base, 7)} — {_placement_line('classical ruler', rival, lang)}.")
            lines.append(
                f"• Team's house of success (its 5th = chart house {success['house']}) — "
                f"{_placement_line('classical ruler', success, lang)}."
            )
            lines.append(
                f"• Team's house of honour/victory (its 10th = chart house {honor['house']}) — "
                f"{_placement_line('classical ruler', honor, lang)}."
            )
            if pof_house:
                lines.append(f"• Part of Fortune in chart house {pof_house}.")
            if moon:
                lines.append(f"• Moon: {moon}.")
            lines.append(f"• Verdict: {verdict} (score {score}).")
            lines.append(
                "Note: rulers come from traditional rulership; this list shows what the reading "
                "rests on, it is not a guarantee of the result."
            )
        return "\n".join(lines)
    except Exception:
        return None
