"""Deterministic weather (6th house) checklist shown next to the horary verdict.

Book rule (case #62): for a weather question the target is the **6th house**.
If the ruler of the 6th house makes a soft aspect (conjunction / sextile /
trine) to the querent's significator, precipitation follows; a hard aspect
(square / opposition) blocks it.

The module only reports chart facts; the score comes from horary_engine.
"""

from core.ephemeris import SIGNS_EN, SIGNS_TR, sign_from_lon

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
_VERDICTS = {
    "tr": {"YES": "EVET", "NO": "HAYIR", "UNCERTAIN": "KARARSIZ"},
    "en": {"YES": "YES", "NO": "NO", "UNCERTAIN": "UNCERTAIN"},
    "es": {"YES": "SÍ", "NO": "NO", "UNCERTAIN": "INCIERTO"},
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


def _nearest_aspect(lon_a, lon_b):
    """Nearest major aspect between two longitudes: (angle, orb) or None."""
    best = None
    for angle in (0, 60, 90, 120, 180):
        diff = abs((lon_a - lon_b + 180) % 360 - 180)
        orb = abs(diff - angle)
        if best is None or orb < best[1]:
            best = (angle, orb)
    return best


def _where(data, lang):
    if not data:
        return "?"
    bits = []
    if data.get("sign") is not None and data.get("deg") is not None:
        bits.append(f"{_sign_name(data['sign'], lang)} {data['deg'] % 30:.1f}°")
    if data.get("house"):
        bits.append({"tr": f"{data['house']}. evde",
                     "en": f"in house {data['house']}",
                     "es": f"en la casa {data['house']}"}[lang])
    if data.get("retro"):
        bits.append({"tr": "retro", "en": "retrograde", "es": "retrógrado"}[lang])
    return ", ".join(bits) if bits else "?"


def build_weather_brief(res, qtype, lang="tr"):
    """Localized weather checklist, or None for non-weather questions."""
    if qtype != "weather":
        return None
    try:
        lang = _lang(lang)
        cusps = res["houses"]["cusps"]
        target_sign = sign_from_lon(cusps[5])
        ruler = (res.get("quesited") or {}).get("planet") or "Moon"
        planets = res.get("planets") or {}
        rdata = planets.get(ruler) or {}
        qname = (res.get("querent") or {}).get("planet") or "Moon"
        qdata = planets.get(qname) or {}

        aspect = _nearest_aspect(rdata.get("lon", 0), qdata.get("lon", 0))
        angle = aspect[0] if aspect else None
        orb = aspect[1] if aspect else None

        verdict = _VERDICTS[lang].get(res.get("verdict"), res.get("verdict"))
        score = res.get("score")
        ruler_name = _planet_name(ruler, lang)
        q_label = _planet_name(qname, lang)
        aspect_name = _ASPECTS[lang].get(angle, str(angle))
        soft = angle in (0, 60, 120)

        if lang == "tr":
            lines = [
                "Hava durumu kontrolü (klasik horary — hedef 6. ev):",
                f"• Soruyu soranın göstergesi: {q_label}, {_where(qdata, lang)}.",
                f"• Hava hedefi: 6. ev ({_sign_name(target_sign, lang)}) — klasik yöneticisi {ruler_name}, {_where(rdata, lang)}.",
            ]
            if aspect and (soft or angle in (90, 180)):
                tone = "yumuşak açı, yağış lehine" if soft else "sert açı, yağışa engel"
                lines.append(f"• Açı: {ruler_name} ile {q_label} arasında {aspect_name} (~{orb:.1f}°) — {tone}.")
            else:
                lines.append("• Açı: 6. ev yöneticisi ile soranın göstergesi arasında belirgin açı yok.")
            lines.append(f"• Hüküm: {verdict} (skor {score}).")
            lines.append("Not: hedef 6. ev kuralından geliyor; bu satırlar yorumun dayanağını gösterir, kesin sonuç garantisi değildir.")
        elif lang == "es":
            lines = [
                "Control del tiempo (horaria clásica — objetivo: casa 6):",
                f"• Significador del consultante: {q_label}, {_where(qdata, lang)}.",
                f"• Objetivo meteorológico: casa 6 ({_sign_name(target_sign, lang)}) — regente clásico {ruler_name}, {_where(rdata, lang)}.",
            ]
            if aspect and (soft or angle in (90, 180)):
                tone = "aspecto suave, favorable a la precipitación" if soft else "aspecto duro, bloquea la precipitación"
                lines.append(f"• Aspecto: {aspect_name} entre {ruler_name} y {q_label} (~{orb:.1f}°) — {tone}.")
            else:
                lines.append("• Aspecto: no hay aspecto definido entre el regente de la casa 6 y el consultante.")
            lines.append(f"• Fallo: {verdict} (puntuación {score}).")
            lines.append("Nota: la casa 6 es el objetivo clásico; esta lista muestra en qué se apoya la lectura, no es una garantía.")
        else:
            lines = [
                "Weather checklist (classical horary — target: 6th house):",
                f"• Querent's significator: {q_label}, {_where(qdata, lang)}.",
                f"• Weather target: 6th house ({_sign_name(target_sign, lang)}) — classical ruler {ruler_name}, {_where(rdata, lang)}.",
            ]
            if aspect and (soft or angle in (90, 180)):
                tone = "soft aspect, favours precipitation" if soft else "hard aspect, blocks precipitation"
                lines.append(f"• Aspect: {aspect_name} between {ruler_name} and {q_label} (~{orb:.1f}°) — {tone}.")
            else:
                lines.append("• Aspect: no clear aspect between the 6th-house ruler and the querent.")
            lines.append(f"• Verdict: {verdict} (score {score}).")
            lines.append("Note: the target is the classical 6th house; this list shows what the reading rests on, not a guarantee.")
        return "\n".join(lines)
    except Exception:
        return None
