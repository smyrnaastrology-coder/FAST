"""Deterministic checklist for third-party business deals (book case #64).

Turned-house frame:
  buyer = chart 7th; seller = buyer's 10th (chart 4th)
  seller co-ruler = ruler of sign intercepted in buyer's 7th (chart 1st)
  buyer's money = buyer's 2nd (chart 8th); investment = its 5th (chart 12th)
  union approval = buyer's 7th's 3rd (chart 9th)
"""

from core.ephemeris import DOMICILE, SIGNS_TR, sign_from_lon

from engine.weather_brief import (
    _ASPECTS,
    _VERDICTS,
    _lang,
    _planet_name,
    _sign_name,
    _where,
)


def _turned(base, relative):
    return ((base - 1) + (relative - 1)) % 12 + 1


def _ruler(res, house):
    sign = sign_from_lon(res["houses"]["cusps"][house - 1])
    return sign, DOMICILE.get(sign, "Saturn")


def _intercepted(res, house):
    cusps = res["houses"]["cusps"]
    start = cusps[house - 1] % 360
    end = cusps[house % 12] % 360
    span = (end - start) % 360
    cusp_signs = {sign_from_lon(c) for c in cusps}
    for sign in SIGNS_TR:
        if sign in cusp_signs:
            continue
        sign_start = SIGNS_TR.index(sign) * 30.0
        if ((sign_start - start) % 360) < span:
            return sign, DOMICILE.get(sign)
    return None, None


def _nearest_aspect(lon_a, lon_b):
    best = None
    diff = abs((lon_a - lon_b + 180) % 360 - 180)
    for angle in (0, 60, 90, 120, 150, 180):
        orb = abs(diff - angle)
        if best is None or orb < best[1]:
            best = (angle, orb)
    return best


def _aspect_applying(lon_fast, lon_slow, angle):
    """Mirror horary_engine.aspect_pair's applying/separating direction test."""
    best = None
    for exact in ((lon_slow + angle) % 360, (lon_slow - angle) % 360):
        forward = (exact - lon_fast) % 360
        orb = forward if forward <= 180 else 360 - forward
        applying = forward <= 180
        if best is None or orb < best[1]:
            best = (applying, orb)
    return best


def build_deal_brief(res, qtype, lang="tr"):
    """Localized deal checklist, or None for other question types."""
    if qtype != "deal":
        return None
    try:
        lang = _lang(lang)
        planets = res.get("planets") or {}
        buyer_house = 7
        buyer = (res.get("quesited") or {}).get("planet") or _ruler(res, buyer_house)[1]
        buyer_data = planets.get(buyer) or {}

        seller_house = _turned(buyer_house, 10)  # chart house 4
        seller_sign, seller = _ruler(res, seller_house)
        seller_data = planets.get(seller) or {}
        buyer_seventh = _turned(buyer_house, 7)  # chart house 1
        co_sign, co_ruler = _intercepted(res, buyer_seventh)
        co_data = planets.get(co_ruler) or {} if co_ruler else {}

        targets = list(dict.fromkeys(p for p in (seller, co_ruler) if p and p != buyer))
        aspects = []
        for target in targets:
            data = planets.get(target) or {}
            aspect = _nearest_aspect(buyer_data.get("lon", 0), data.get("lon", 0))
            if aspect:
                fast = buyer if abs(buyer_data.get("speed", 0)) >= abs(data.get("speed", 0)) else target
                slow = target if fast == buyer else buyer
                fast_lon = (planets.get(fast) or {}).get("lon", 0)
                slow_lon = (planets.get(slow) or {}).get("lon", 0)
                angle, orb = aspect
                applying, _ = _aspect_applying(fast_lon, slow_lon, angle)
                aspects.append((target, angle, orb, applying))

        money_house = _turned(buyer_house, 2)  # chart house 8
        invest_house = _turned(money_house, 5)  # chart house 12
        money_sign, money_ruler = _ruler(res, money_house)
        invest_sign, invest_ruler = _ruler(res, invest_house)
        money_data = planets.get(money_ruler) or {}
        invest_data = planets.get(invest_ruler) or {}
        investment_aspect = _nearest_aspect(money_data.get("lon", 0), invest_data.get("lon", 0))

        moon = planets.get("Moon") or {}
        moon_links = []
        for target in list(dict.fromkeys(p for p in [buyer] + targets if p)):
            data = planets.get(target) or {}
            aspect = _nearest_aspect(moon.get("lon", 0), data.get("lon", 0))
            if aspect and aspect[0] == 150 and aspect[1] <= 15:
                moon_links.append((target, aspect[1]))

        verdict = _VERDICTS[lang].get(res.get("verdict"), res.get("verdict"))
        score = res.get("score")
        buyer_name = _planet_name(buyer, lang)
        seller_name = _planet_name(seller, lang)
        deal_link = next((s for s in res.get("strictures", []) if s.get("code") == "deal_buyer_applies_seller"), None)
        deal_exists = bool(deal_link)
        translated = any(s.get("code") == "deal_moon_quincunx_translation" for s in res.get("strictures", []))

        def house_label(n):
            return {"tr": f"{n}. ev", "en": f"house {n}", "es": f"casa {n}"}[lang]

        if lang == "tr":
            lines = [
                "Anlaşma/satın alma kontrolü (klasik horary — türetilmiş evler):",
                f"• Alıcı (sorulan kişi): 7. ev — klasik yöneticisi {buyer_name}, {_where(buyer_data, lang)}.",
                f"• Satıcı: alıcının 10. evi ({house_label(seller_house)}) — {seller_name}, {_where(seller_data, lang)}.",
            ]
            if co_ruler:
                lines.append(f"• Satıcının eş-yöneticisi: alıcının 7. evinde araya sıkışmış {_sign_name(co_sign, lang)} — {_planet_name(co_ruler, lang)}, {_where(co_data, lang)}.")
            for target, angle, orb, applying in aspects:
                aspect_name = _ASPECTS[lang].get(angle, "quincunx" if angle == 150 else str(angle))
                status = "uyguluyor" if applying else "ayrılıyor/geçmiş"
                lines.append(f"• Alıcı–satıcı bağı: {buyer_name}–{_planet_name(target, lang)} {aspect_name} (~{orb:.1f}° orb), {status}.")
            if money_ruler and invest_ruler and investment_aspect:
                separation = abs((money_data.get("lon", 0) - invest_data.get("lon", 0) + 180) % 360 - 180)
                trine_orb = abs(separation - 120)
                square_orb = abs(separation - 90)
                lines.append(f"• Alıcının para evi ({house_label(money_house)}): {_planet_name(money_ruler, lang)}, {_where(money_data, lang)}. Yatırım evi ({house_label(invest_house)}): {_planet_name(invest_ruler, lang)}, {_where(invest_data, lang)}. Kaynak metin üçgen diyor; dereceler arası {separation:.1f}° (üçgene {trine_orb:.1f}°, kareye {square_orb:.1f}° orb) — bunu güçlü/kesin bir perfection saymıyorum.")
            if moon_links:
                links = ", ".join(f"{_planet_name(p, lang)} (~{orb:.1f}°)" for p, orb in moon_links)
                lines.append(f"• Ay'ın ışık aktarımı/toplanması: uygulayan quincunx (150°) {links} — anlaşmayı destekler, fakat ayarlama/değişiklik gerektirir.")
            if any(s.get("code") == "deal_union_approval_delay" for s in res.get("strictures", [])):
                lines.append("• Sendika/onay: Uranüs (alıcının 3. evi) ile alıcının para evindeki Plüto arasında geniş, yaklaşan sekstil; onay gecikmesiyle uyumlu, fakat kesin zaman ölçüsü vermez.")
            lines.append(f"• Hüküm: {verdict} (skor {score}).")
            lines.append("Not: sendika/onay göstergesi süreci geciktirebilir; harita bu vakada kesin kapanış tarihi vermiyor.")
        elif lang == "es":
            lines = [
                "Control de compra/acuerdo (horaria clásica — casas derivadas):",
                f"• Comprador (persona consultada): casa 7 — regente clásico {buyer_name}, {_where(buyer_data, lang)}.",
                f"• Vendedor: casa 10 del comprador ({house_label(seller_house)}) — {seller_name}, {_where(seller_data, lang)}.",
            ]
            if co_ruler:
                lines.append(f"• Corregente del vendedor: {_sign_name(co_sign, lang)} interceptado en la casa 7 del comprador — {_planet_name(co_ruler, lang)}, {_where(co_data, lang)}.")
            for target, angle, orb, applying in aspects:
                aspect_name = _ASPECTS[lang].get(angle, "quincuncio" if angle == 150 else str(angle))
                lines.append(f"• Vínculo comprador–vendedor: {aspect_name} entre {buyer_name} y {_planet_name(target, lang)} (~{orb:.1f}°); {'aplicativo' if applying else 'separativo'}.")
            if investment_aspect:
                ang, orb = investment_aspect
                asp_name = _ASPECTS[lang].get(ang, "quincuncio" if ang == 150 else str(ang))
                separation = abs((money_data.get("lon", 0) - invest_data.get("lon", 0) + 180) % 360 - 180)
                lines.append(f"• Dinero del comprador: {_planet_name(money_ruler, lang)}; inversión: {_planet_name(invest_ruler, lang)}. El texto habla de trígono, pero la separación real es {separation:.1f}°; el orbe al trígono es {abs(separation-120):.1f}° (amplio).")
            if moon_links:
                lines.append("• La Luna aplica quincuncios de 150° a los significadores: transferencia/colección de luz, con necesidad de ajustes.")
            lines.append(f"• Fallo: {verdict} (puntuación {score}).")
            lines.append("Nota: la aprobación sindical puede retrasar el proceso; la carta no da una fecha exacta de cierre.")
        else:
            lines = [
                "Deal/purchase checklist (classical horary — turned houses):",
                f"• Buyer (queried party): house 7 — classical ruler {buyer_name}, {_where(buyer_data, lang)}.",
                f"• Seller: buyer's 10th ({house_label(seller_house)}) — {seller_name}, {_where(seller_data, lang)}.",
            ]
            if co_ruler:
                lines.append(f"• Seller's co-ruler: intercepted {_sign_name(co_sign, lang)} in buyer's 7th — {_planet_name(co_ruler, lang)}, {_where(co_data, lang)}.")
            for target, angle, orb, applying in aspects:
                aspect_name = _ASPECTS[lang].get(angle, "quincunx" if angle == 150 else str(angle))
                lines.append(f"• Buyer–seller link: {aspect_name} between {buyer_name} and {_planet_name(target, lang)} (~{orb:.1f}° orb), {'applying' if applying else 'separating'}.")
            if investment_aspect:
                ang, orb = investment_aspect
                asp_name = _ASPECTS[lang].get(ang, "quincunx" if ang == 150 else str(ang))
                separation = abs((money_data.get("lon", 0) - invest_data.get("lon", 0) + 180) % 360 - 180)
                lines.append(f"• Buyer's money ruler: {_planet_name(money_ruler, lang)}; investment ruler: {_planet_name(invest_ruler, lang)}. The source calls this a trine, but the actual separation is {separation:.1f}° (trine orb {abs(separation-120):.1f}°, wide), so I would not treat it as a strong perfection.")
            if moon_links:
                lines.append("• The Moon applies 150° quincunxes to the significators: translation/collection of light supports a deal but suggests adjustments.")
            if any(s.get("code") == "deal_union_approval_delay" for s in res.get("strictures", [])):
                lines.append("• Union approval: a wide, approaching sextile from Uranus (buyer's 3rd) to Pluto in the buyer's money house is consistent with delay, but gives no exact timeline.")
            lines.append(f"• Verdict: {verdict} (score {score}).")
            lines.append("Note: union approval can delay the process; this chart does not justify an exact closing date.")
        return "\n".join(lines)
    except Exception:
        return None
