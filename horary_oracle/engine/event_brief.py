"""Deterministic checklist for "universal" event questions (book case #63).

Example: "Will the Russians come to the Olympics?" — a third party plus an event.
The classical frame used in the book:

  party  = 7th house (its ruler is the third party)
  event  = 5th house (the games) and 10th house (honour / prestige)

If the party's ruler makes no major aspect to the event's rulers, there is no
movement and the party does not come. The module only reports chart facts; the
verdict comes from horary_engine.
"""

from core.ephemeris import DOMICILE, sign_from_lon

from engine.weather_brief import (
    _ASPECTS,
    _VERDICTS,
    _lang,
    _planet_name,
    _sign_name,
    _where,
)


def _ruler_of(res, house):
    cusps = res["houses"]["cusps"]
    sign = sign_from_lon(cusps[house - 1])
    planet = DOMICILE.get(sign, "Saturn")
    return sign, planet


def _nearest_aspect(lon_a, lon_b):
    best = None
    for angle in (0, 60, 90, 120, 180):
        diff = abs((lon_a - lon_b + 180) % 360 - 180)
        orb = abs(diff - angle)
        if best is None or orb < best[1]:
            best = (angle, orb)
    return best


def build_event_brief(res, qtype, lang="tr"):
    """Localized event/attendance checklist, or None for other question types."""
    if qtype != "event_party":
        return None
    try:
        lang = _lang(lang)
        planets = res.get("planets") or {}
        party = (res.get("quesited") or {}).get("planet") or "Mercury"
        party_data = planets.get(party) or {}
        event_sign5, ruler5 = _ruler_of(res, 5)
        event_sign10, ruler10 = _ruler_of(res, 10)

        event_rulers = []
        for r in (ruler5, ruler10):
            if r != party and r not in event_rulers:
                event_rulers.append(r)

        best = None
        for r in event_rulers:
            rd = planets.get(r) or {}
            aspect = _nearest_aspect(party_data.get("lon", 0), rd.get("lon", 0))
            if aspect and (best is None or aspect[1] < best[2]):
                best = (r, aspect[0], aspect[1])

        verdict = _VERDICTS[lang].get(res.get("verdict"), res.get("verdict"))
        score = res.get("score")
        party_name = _planet_name(party, lang)
        hits = bool(best and best[2] <= 8)

        def event_line(ruler, sign, house):
            rd = planets.get(ruler) or {}
            label = {"tr": f"{house}. ev", "en": f"house {house}", "es": f"casa {house}"}[lang]
            role = {
                5: {"tr": "oyunlar", "en": "the games", "es": "los juegos"}[lang],
                10: {"tr": "onur/prestij", "en": "honour/prestige", "es": "honor/prestigio"}[lang],
            }[house]
            return f"{label} ({role}: {_sign_name(sign, lang)}) — {_planet_name(ruler, lang)}, {_where(rd, lang)}"

        if lang == "tr":
            lines = [
                "Etkinlik/katılım kontrolü (klasik horary — evrensel soru):",
                f"• Taraf (üçüncü kişi/kurum): 7. ev — klasik yöneticisi {party_name}, {_where(party_data, lang)}.",
                f"• Etkinlik: {event_line(ruler5, event_sign5, 5)}; {event_line(ruler10, event_sign10, 10)}.",
            ]
            if best:
                aspect_name = _ASPECTS[lang].get(best[1], str(best[1]))
                if hits:
                    lines.append(f"• Açı: {party_name} ile {_planet_name(best[0], lang)} arasında {aspect_name} (~{best[2]:.1f}°) — etkinlikle bağ var.")
                else:
                    lines.append(f"• Açı: majör açı yok; en yakını {party_name}–{_planet_name(best[0], lang)} {aspect_name} yönünde ama ~{best[2]:.1f}° orb — hareket yok.")
            else:
                lines.append("• Açı: taraf ile etkinlik göstergeleri aynı gezegen; ayrı açı okunmuyor.")
            lines.append(f"• Hüküm: {verdict} (skor {score}).")
            lines.append("Not: taraf 7. ev, etkinlik 5. ve 10. ev kuralından geliyor; bu satırlar yorumun dayanağını gösterir.")
        elif lang == "es":
            lines = [
                "Control de evento/participación (horaria clásica — pregunta universal):",
                f"• Parte (tercero): casa 7 — regente clásico {party_name}, {_where(party_data, lang)}.",
                f"• Evento: {event_line(ruler5, event_sign5, 5)}; {event_line(ruler10, event_sign10, 10)}.",
            ]
            if best:
                aspect_name = _ASPECTS[lang].get(best[1], str(best[1]))
                if hits:
                    lines.append(f"• Aspecto: {aspect_name} entre {party_name} y {_planet_name(best[0], lang)} (~{best[2]:.1f}°) — hay vínculo con el evento.")
                else:
                    lines.append(f"• Aspecto: sin aspecto mayor; el más cercano es {aspect_name} {party_name}–{_planet_name(best[0], lang)} con orbe ~{best[2]:.1f}° — no hay movimiento.")
            else:
                lines.append("• Aspecto: la parte y el evento comparten regente; no se lee aspecto aparte.")
            lines.append(f"• Fallo: {verdict} (puntuación {score}).")
            lines.append("Nota: la parte es la casa 7 y el evento las casas 5 y 10; esta lista muestra en qué se apoya la lectura.")
        else:
            lines = [
                "Event/attendance checklist (classical horary — universal question):",
                f"• Party (third party): house 7 — classical ruler {party_name}, {_where(party_data, lang)}.",
                f"• Event: {event_line(ruler5, event_sign5, 5)}; {event_line(ruler10, event_sign10, 10)}.",
            ]
            if best:
                aspect_name = _ASPECTS[lang].get(best[1], str(best[1]))
                if hits:
                    lines.append(f"• Aspect: {aspect_name} between {party_name} and {_planet_name(best[0], lang)} (~{best[2]:.1f}°) — there is contact with the event.")
                else:
                    lines.append(f"• Aspect: no major aspect; closest is {aspect_name} {party_name}–{_planet_name(best[0], lang)} at ~{best[2]:.1f}° orb — no movement.")
            else:
                lines.append("• Aspect: party and event share a ruler; no separate aspect to read.")
            lines.append(f"• Verdict: {verdict} (score {score}).")
            lines.append("Note: party is house 7 and the event houses 5 and 10; this list shows what the reading rests on.")
        return "\n".join(lines)
    except Exception:
        return None
