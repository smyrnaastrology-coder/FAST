# -*- coding: utf-8 -*-
"""Bilesik/Coklu Sorular (Only Way Learn Horary - Compound and Multiple Questions).

Tek haritadan ayni anda sorulan birden fazla soru: Kim, Nerede, Ne, Ne Zaman,
Neden, Nasil ve Evet/Hayir. Bu modul haritayi YENIDEN dondurmaz; api'nin
urettigi engine_json (ve istenirse raw res) uzerinden her alt soru icin ayni
haritadan gostergeleri toplar, alt soruya ozel HUCM (sub_verdict) hesabi yapar
ve LLM icin per-soru satir yapisini uretir.

Kalibrasyon #56 (Pam - 12 Oca 1990 18:27 PST CDA): "Pam ile is ortagi olmali
miyiz? Esimle Kaliforniya'ya tasinmali miyiz? Finansal mumkun mu?" -> hem Pam
hem es 7. evde; is=10. ev, tasinma=9. ev (4. ev = mevcut ev). Ayrica:
    - is ortakligi: querent(1L) <-> 7L (ortak) + 10L (is) acilari -> acisiz = HAYIR
    - tasinma: 9L (uzak) 4. evde, 4. ev anlamlilarina acisiz -> yerinde kalir
    - finans: oncekiler HAYIR ise gereksiz (moot)
"""

import re

_SLOT_LABEL_TR = {
    "who": "KİM", "where": "NEREDE", "what": "NE", "when": "NE ZAMAN",
    "why": "NEDEN", "how": "NASIL", "choice": "HANGİSİ", "yesno": "EVET/HAYIR",
    "generic": "KONU",
}
_QTYPE_SLOT_TR = {
    "business": "İŞ ORTAKLIĞI", "relocation": "TAŞINMA", "finance": "FİNANS",
    "army": "ASKERLİK", "animal": "HAYVAN SATIN ALMA", None: "GENEL",
}


def _norm(s):
    return (" " + s + " ").lower().replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ı", "i").replace("ö", "o").replace("ç", "c")


def split_questions(text):
    """Soru metnini alt sorulara boler. Oncelik '?', sonra virgulle ayrilmis
    'mi/mi/mu/mu' cümleleri; tek soru ise tek elemanli liste doner."""
    if not text:
        return []
    t = re.sub(r"[؟]", "?", text)
    parts = [p.strip() for p in re.split(r"\?", t) if p.strip()]
    if len(parts) >= 2:
        return parts
    if len(re.findall(r"\bm[iiuü]\b", t.lower())) >= 2:
        cand = [c.strip() for c in re.split(r"[.;]", t) if c.strip()]
        if len(cand) < 2:
            cand = [c.strip() for c in t.split(",") if c.strip()]
        if len(cand) >= 2:
            return cand
    return [t.strip()]


def classify_slot(sub):
    """Alt soruyu KIM/NEREDE/NE/ZAMAN/NEDEN/NASIL/HANGİSİ/EVET-HAYIR'a esler."""
    s = _norm(sub)
    when_kw = ["ne zaman", "nezaman", "ne zamana", "hangi zamanda", "hangi gün", "hangi gun", "ne kadar zamanda", "ne kadar surede", "kac günde", "kac gun", "ne vakit"]
    where_kw = ["nerede", "nerde", "nereye", "nere ", "nere", "hangi yön", "hangi yon", "hangi taraf", "neresi", "konumu", "bulundugu", "bulunduğu", "neresinde", "hangi mekan"]
    who_kw = ["kim", "kimdir", "kimi", "kim bu", "hangi kişi", "hangi kisi", "kimin"]
    why_kw = ["neden", "niye", "nicin", "niçin", "sebebi", "ne icin", "hangi amac", "amacı", "amaci"]
    how_kw = ["nasil", "nasıl", "hangi şekilde", "hangi sekilde", "hangi yontem", "yöntem", "hangi kanal", "hangi üslup"]
    choice_kw = ["hangisi", "hangisini", "hangisine", "yoksa", "veya"]
    what_kw = ["nedir", "ne bu", "neye", "neyi", "ne var", "ne olur", "ne anlama", "ne ifade", "ne getirir", "ne kaybettirir"]
    if any(k in s for k in when_kw):
        return {"slot": "when", "label": _SLOT_LABEL_TR["when"]}
    if any(k in s for k in where_kw):
        return {"slot": "where", "label": _SLOT_LABEL_TR["where"]}
    if any(k in s for k in who_kw):
        return {"slot": "who", "label": _SLOT_LABEL_TR["who"]}
    if any(k in s for k in why_kw):
        return {"slot": "why", "label": _SLOT_LABEL_TR["why"]}
    if any(k in s for k in how_kw):
        return {"slot": "how", "label": _SLOT_LABEL_TR["how"]}
    if any(k in s for k in choice_kw):
        return {"slot": "choice", "label": _SLOT_LABEL_TR["choice"]}
    if any(k in s for k in what_kw) or " ne" in s:
        return {"slot": "what", "label": _SLOT_LABEL_TR["what"]}
    if any(w.strip(".,!?;:").endswith(_q) for w in s.split() for _q in
           ("miyim", "mıyım", "muyum", "müyüm", "misin", "mısın", "musun", "müsün",
            "miyiz", "mıyız", "muyuz", "müyüz", "miydi", "mıydı", "muydu", "müydü",
            "midir", "mıdır", "mudur", "müdür", "misiniz", "mısınız", "musunuz", "müsünüz",
            "mi", "mı", "mu", "mü")):
        return {"slot": "yesno", "label": _SLOT_LABEL_TR["yesno"]}
    return {"slot": "generic", "label": _SLOT_LABEL_TR["generic"]}


def sub_qtype(sub):
    """Alt sorunun tipi: business / relocation / finance / None (genel)."""
    s = _norm(sub)
    if any(k in s for k in ["iş orta", "is orta", "ortak", "hissedar", "hisedar",
                            "sirket kur", "şirket kur", "kur ortak", "partnership",
                            "is kur", "iş kur", "ortaklik", "ortaklık"]):
        return "business"
    if any(k in s for k in ["taşın", "tasin", "taşinalim", "tasinalim", "tasınmal",
                            "taşınmal", "kaliforniya", "yer değiş", "yer degis",
                            "baska sehir", "başka şehir", "baska eyalet", "başka eyalet",
                            "baska ev", "başka ev", "uzak mesafe", "goc", "göç",
                            "yeni sehire", "yeni şehre", "baska ulke", "başka ülke"]):
        return "relocation"
    if any(k in s for k in ["finansal", "maddi", "butce", "bütçe", "kredim", "imkan",
                            "imkân", "karşılay", "karsilay", "mumkun", "mümkün",
                            "para olarak", "finansman"]):
        return "finance"
    if any(k in s for k in ["ordu", "asker", "askerlik", "askere", "military", "army",
                            "nefer", "cephe", "askeriyeye", "er olarak"]):
        return "army"
    toks = {w.strip(".,!?;:()[]'’\"").lstrip("'’") for w in s.split()}
    if toks & {"at", "ati", "atin", "atinizi", "atimizi", "atlar", "atlarini",
               "beygir", "kisrak", "hayvan", "hayvanlar", "hayvancilik",
               "horse", "equine", "nikk", "nikki", "pony"}:
        return "animal"
    return None


def _nearest_aspect(a, b):
    """Iki boylam arasi en yakin majör aci (0/60/90/120/180). (aci, orb)"""
    d = (b - a) % 360
    if d > 180:
        d = 360 - d
    ms = [0, 60, 90, 120, 180]
    mm = min(ms, key=lambda x: abs(x - d))
    return mm, round(abs(mm - d), 1)


def _ruler(cusp_lon, modern=True):
    from core.ephemeris import sign_from_lon, DOMICILE, DOMICILE_TRADITIONAL
    s = sign_from_lon(cusp_lon)
    tbl = DOMICILE if modern else DOMICILE_TRADITIONAL
    return s, tbl.get(s, "Venus")


def _derived_house(base, n):
    """'base' evindeki kisinin n. evi = harita kacinci evi olur (turetim)."""
    return ((base - 1) + (n - 1)) % 12 + 1


def _sat_asc_flag(res):
    return any(str(s.get("code", "")) in ("saturn_1_7", "saturn_asc_conjunction")
               for s in res.get("strictures", []))


def _fuzzy_pair(pl, a, b, orb=8):
    """a,b (boylam+hiz) arasi en yakin majör aci; uygulayan mi bilgisi.
    Sondaki parantez: ayrilan ama tam acidan <1.0 derece sapmaliysa kullanilabilir (kitap)."""
    try:
        from horary_engine import next_aspect_distance
    except Exception:
        return None
    pa, pb = pl.get(a, {}), pl.get(b, {})
    if not pa or not pb:
        return None
    la, sa = pa.get("lon", 0.0), pa.get("speed", 1.0)
    lb, sb = pb.get("lon", 0.0), pb.get("speed", 1.0)
    if sa < sb:                    # hizli olani 'a' yap
        la, sa, lb, sb = lb, sb, la, sa
        a, b = b, a
    r = next_aspect_distance(la, sa, lb, sb, 0, orb)
    return {"a": a, "b": b, "angle": r["target"], "orb": round(r["dist"], 1),
            "applying": r["applying"], "dist": r["dist"]}


def _usable(v):
    """Kullanilabilir: orb <=8 VE (uygulanan VEYA geç-ayrilma <1.0) VE yumusak aci (0/60/120)."""
    return v is not None and v["dist"] <= 8 and (v["applying"] or v["dist"] < 1.0) and v["angle"] in (0, 60, 120)


def _moon_chain(pl, a, b):
    """Ay once a'ya sonra b'ye (veya tersi) apply veya geç-acı yapiyorsa 'iyik tasıma/toplama'.
    Sadece bilgi amacli: IŞIĞIN TAŞINMASI/TOPLANMASI."""
    try:
        from horary_engine import next_aspect_distance
    except Exception:
        return ""
    m = pl.get("Moon", {})
    if not m:
        return ""
    va = _fuzzy_pair(pl, "Moon", a)
    vb = _fuzzy_pair(pl, "Moon", b)
    ok_a = va is not None and (va["applying"] or va["dist"] < 1.0)
    ok_b = vb is not None and (vb["applying"] or vb["dist"] < 1.0)
    if ok_a and ok_b:
        order = a if va["dist"] <= vb["dist"] else b
        return (f"Ay {a}'ya {va['angle']}° (orb {va['orb']}°) ve {b}'ye {vb['angle']}° "
                f"(orb {vb['orb']}°) açı yapacak — önce {order} → IŞIĞIN TAŞINMASI/TOPLANMASI ihtimali; "
                f"revizyon/erteli TRUE eğilim (bkz. Kural 6).")
    return ""


def sub_verdict(res, sub):
    """Alt soruya ozel HUCM (#56/#57 kalibrasyonu). res: ham chart (cusps+planets).
    Doner: dict {qtype, verdict, facts} — qtype yoksa genel motor hukumu kullanilir."""
    try:
        qt = sub_qtype(sub)
        if qt is None:
            return {"qtype": None}
        cusps = res["houses"]["cusps"]
        pl = res["planets"]
        lon = lambda n: pl.get(n, {}).get("lon", 0.0)
        qr = res["querent"].get("planet") if isinstance(res.get("querent"), dict) else res.get("querent", "")
        if isinstance(res.get("quesited"), dict):
            qs = res["quesited"].get("planet")
        else:
            qs = res.get("quesited", "")
        sat = _sat_asc_flag(res)

        def _soft_found(pairs):
            for a, b in pairs:
                if a == b:
                    continue
                v = _fuzzy_pair(pl, a, b)
                if _usable(v):
                    return v
            return None

        def _flag_verdict(name, soft, reason, detail):
            if soft:
                v = "BELİRSİZ" if sat else "YES"
                tail = "Satürn yükselede (saturn_1_7) negatif ağırlık — en güçlü açı olsa bile hayır eğilimi." if sat else "olumlu uygulanan açı var -> EVET"
            else:
                v = "NO"
                tail = reason
            return {"qtype": qt, "verdict": v, "facts": f"{detail} {tail}"}

        if qt == "business":
            qs7, r7 = _ruler(cusps[6])      # 7. ev: ortak
            qs10, r10 = _ruler(cusps[9])    # 10. ev: is/sirket
            vv = _soft_found([(qr, r7), (qr, r10)])
            p7 = pl.get(r7, {}); p10 = pl.get(r10, {}); pq = pl.get(qr, {})
            av_txt = ""
            for a, b in ((qr, r7), (qr, r10)):
                f = _fuzzy_pair(pl, a, b)
                if f:
                    av_txt += f"{a}-{b} {f['angle']}° (orb {f['orb']}°, {'uygulanan' if f['applying'] else 'ayrılan'}) "
            if not av_txt:
                av_txt = "açı yakınlığı yok"
            detail = (f"Ortak hüküm: querent {qr} {pq.get('sign','')} Ev{pq.get('house','?')}; "
                      f"ortak(7.ev {qs7})={r7} {p7.get('sign','')} {p7.get('deg','?')}° Ev{p7.get('house','?')}; "
                      f"iş(10.ev {qs10})={r10} {p10.get('sign','')} {p10.get('deg','?')}° Ev{p10.get('house','?')}. "
                      f"Açılar: {av_txt.strip()}. ")
            reason = "olumlu uygulanan açı yok (ve/veya Satürn yükselen) -> HAYIR"
            return _flag_verdict("business", vv is not None, reason, detail)

        if qt == "army":
            # Kitap #57: subject 7. ev (partner) -> turetimle onun 1/6/7/10 evleri
            base = 7
            qsn, r_self = _ruler(cusps[base - 1])             # onun 1. evi (harita 7.)
            h6 = _derived_house(base, 6); qs6, r6 = _ruler(cusps[h6 - 1])   # onun 6. evi (asker)
            h10 = _derived_house(base, 10); qs10, r10 = _ruler(cusps[h10 - 1])  # onun 10. evi (kariyer)
            h7 = _derived_house(base, 7); qs7, r7a = _ruler(cusps[h7 - 1])   # onun 7. evi
            vv = _soft_found([(r_self, r6), (r_self, r10)])
            pself = pl.get(r_self, {}); p6 = pl.get(r6, {}); p10 = pl.get(r10, {})
            ps7 = pl.get(qs, {}) if qs != r_self else {}
            chain = _moon_chain(pl, r_self, r6) + _moon_chain(pl, r_self, r10)
            av_txt = ""
            for a, b in ((r_self, r6), (r_self, r10)):
                f = _fuzzy_pair(pl, a, b)
                if f:
                    av_txt += f"{a}-{b} {f['angle']}° (orb {f['orb']}°, {'uygulanan' if f['applying'] else 'ayrılan'}) "
            if not av_txt:
                av_txt = "uygulanan açı yakınlığı yok"
            detail = (f"Askerlik hüküm (türetilmiş, subject=7.ev): {r_self} ({pself.get('sign','')} "
                      f"{pself.get('deg','?')}° Ev{pself.get('house','?')}) onun 1.evi ({qsn}); "
                      f"onun 6.evi={h6} ({qs6}) yöneticisi {r6} {p6.get('sign','')} {p6.get('deg','?')}°, "
                      f"onun 10.evi={h10} ({qs10}) yöneticisi {r10} {p10.get('sign','')} {p10.get('deg','?')}°. "
                      f"Açılar: {av_txt.strip()}. ")
            if chain:
                detail += chain + " "
            reason = "onun 1. yöneticisi ile askerlik/kariyer evleri arasında olumlu uygulanan açı yok -> olma olasılığı düşük (HAYIR)"
            return _flag_verdict("army", vv is not None, reason, detail)

        if qt == "animal":
            # Buyuk hayvan = 12. ev; soru sahibi = 1. ev yoneticileri (+ yukselen Saturn agirligi)
            qs12, r12 = _ruler(cusps[11])             # 12. ev yoneticisi
            in12 = [n for n in pl if pl.get(n, {}).get("house") == 12 and n not in ("NorthNode", "SouthNode")]
            sig12 = list(dict.fromkeys([r12] + in12))
            qs1, r1a = _ruler(cusps[0])               # 1. ev yoneticisi (tek)
            sig_q = list(dict.fromkeys([qr, r1a]))
            pairs = [(a, b) for a in sig_q for b in sig12]
            vv = _soft_found(pairs)
            p12 = pl.get(r12, {}); pq = pl.get(qr, {})
            av_txt = ""
            for a, b in pairs:
                f = _fuzzy_pair(pl, a, b)
                if f:
                    av_txt += f"{a}-{b} {f['angle']}° (orb {f['orb']}°, {'uygulanan' if f['applying'] else 'ayrılan'}) "
            if not av_txt:
                av_txt = "uygulanan açı yakınlığı yok"
            detail = (f"Hayvan hüküm: hayvan=12.ev ({qs12}) yöneticisi {r12} {p12.get('sign','')} "
                      f"{p12.get('deg','?')}° Ev{p12.get('house','?')}; 12. ev içindekiler: {', '.join(in12) if in12 else 'yok'}. "
                      f"Soru sahibi={qr} {pq.get('sign','')} Ev{pq.get('house','?')} (1.ev {qs1} yöneticisi {r1a}). "
                      f"Açılar: {av_txt.strip()}. ")
            reason = "1. ev ve 12. ev göstergecileri arasında olumlu uygulanan açı yok; Satürn yükselede (saturn_1_7) hayır işareti -> HAYIR"
            return _flag_verdict("animal", vv is not None, reason, detail)

        if qt == "relocation":
            qs9, r9 = _ruler(cusps[8])             # 9. ev: uzak yolculuk/tasinma
            qs4, r4 = _ruler(cusps[3])             # 4. ev: mevcut ev
            p9 = pl.get(r9, {})
            in4 = [n for n in pl if pl.get(n, {}).get("house") == 4 and n != r9]
            cand = list(dict.fromkeys([r4] + in4))
            vv = None
            asp_pairs = []
            for n in cand:
                if n == r9 or n in ("NorthNode", "SouthNode"):
                    continue
                f = _fuzzy_pair(pl, r9, n)
                if f:
                    asp_pairs.append((n, f))
                    if _usable(f):
                        vv = f   # son yumusak uygulanani kabul et
            as_txt = "; ".join(f"{r9}-{n} {f['angle']}° (orb {f['orb']}°, {'uygulanan' if f['applying'] else 'ayrılan'})" for (n, f) in asp_pairs) or "4. ev anlamlılarına uygulanan açı yok"
            detail = (f"Taşınma hüküm: 9.ev ({qs9}) yöneticisi {r9} {p9.get('sign','')} {p9.get('deg','?')}° "
                      f"Ev{p9.get('house','?')}; mevcut evi 4.ev ({qs4}) yöneticisi {r4} + 4. evdeki: {', '.join(in4) if in4 else 'yok'}. "
                      f"Açılar: {as_txt}. ")
            return _flag_verdict("relocation", vv is not None,
                                 "9. ev yöneticisi ile 4. evi (mevcut ev) destekleyen uygulanan açı yok -> yerinde kalınır (HAYIR)", detail)

        if qt == "finance":
            return {"qtype": qt, "verdict": "BAĞIMLI",
                    "facts": "Finansal mümkünlük önceki alt sorulara BAĞIMLIDIR: iş ortağı ve/veya taşınma/askerlik/at gibi eylemler HAYIR ise finansal konu gereksizleşir/moot olur. Hepsinde HAYIR -> finansal hesap yapma, kısa 'gereksiz' notu düş. (2. evdeki Neptune paraya mantıklı bakmayı zorlaştırır — bkz. Kural: 'Neptune 2. evde' şüpheli finans.)"}
        return {"qtype": qt}
    except Exception:
        return {"qtype": None}


def _moon_next_aspect(engine_json):
    for s in engine_json.get("strictures", []):
        if s.get("code") == "moon_next_aspect":
            return s.get("with"), s.get("angle"), s.get("dist")
    return None, None, None


def sub_answer(engine_json, sub, res=None):
    """Tek alt soru icin gorunur/rakamsal olgu kumesi + hüküm."""
    try:
        part = classify_slot(sub)
        slot = part["slot"]
        pl = engine_json.get("planets", {})
        qr = engine_json.get("querent", "")
        qs = engine_json.get("quesited", "")
        qr_sign = engine_json.get("querent_sign", "")
        qs_sign = engine_json.get("quesited_sign", "")
        loc = engine_json.get("location", {}) or {}
        perf = engine_json.get("perfection", {}) or {}
        timing = engine_json.get("timing", {}) or {}
        asc_sign = (engine_json.get("houses", {}) or {}).get("asc_sign", "")

        def pinfo(n):
            p = pl.get(n)
            if not p:
                return f"{n} (burc bilinmiyor)"
            rx = " Rx" if p.get("retro") else ""
            return f"{n} {p.get('sign','')} {p.get('deg','?')}° Ev{p.get('house','?')}{rx}"

        sv = None
        if res is not None:
            sv = sub_verdict(res, sub)

        facts = ""
        if slot == "who":
            facts = (f"Querent={qr} ({qr_sign}{', ASC ' + asc_sign if asc_sign else ''}); "
                     f"Quesited/karşı taraf={qs} ({qs_sign}). Göstergeler: {pinfo(qr)} vs {pinfo(qs)}.")
        elif slot == "where":
            d = loc.get("direction", "")
            h = loc.get("house", "")
            ht = loc.get("height", "")
            fld = []
            if d:
                fld.append(f"yön={d}")
            if h:
                fld.append(f"ev={h}")
            if ht:
                fld.append(f"yükselti={ht}")
            if loc.get("ev_ici"):
                fld.append(f"ev-içi={loc.get('ev_ici')}")
            facts = f"Konum göstergeleri: {', '.join(fld) if fld else 'genel konum analizi geçerli'}. Significator={qs} ({qs_sign}) Ev{pl.get(qs,{}).get('house','?')}."
        elif slot == "what":
            facts = f"Konu/significator: {qs} {qs_sign}, {pl.get(qs,{}).get('deg','?')}° Ev{pl.get(qs,{}).get('house','?')}{' Rx' if pl.get(qs,{}).get('retro') else ''}. Querent: {qr} {qr_sign}."
        elif slot == "when":
            org = [f"zamanlaması={timing.get('text','belirsiz')}"]
            if timing.get("ephemeris_text"):
                org.append(f"kavuşum={timing.get('ephemeris_text')}")
            mw, ma, md = _moon_next_aspect(engine_json)
            if mw:
                org.append(f"Ay sonraki açısı={mw} {ma}° ({md}° orb)")
            facts = "; ".join(org) + ". Gösterge: " + pinfo(qs) + "."
        elif slot == "why":
            r = perf.get("result", "belirsiz")
            t = perf.get("type", "yok")
            rec = perf.get("reception", "")
            org = [f"perfection={t} ({r})"]
            if rec:
                org.append(f"kabul={rec}")
            mw, ma, md = _moon_next_aspect(engine_json)
            if mw:
                org.append(f"Ay sonraki açısı {ma}° ({mw}) — niyet/gidişat")
            facts = "; ".join(org) + f". Querent={qr} {qr_sign}, Quesited={qs} {qs_sign}."
        elif slot == "how":
            qa = res["planets"].get(qr, {}).get("lon", 0) if res is not None else pl.get(qr, {}).get("lon", 0)
            qs2 = res["planets"].get(qs, {}).get("lon", 0) if res is not None else pl.get(qs, {}).get("lon", 0)
            a, o = _nearest_aspect(qa, qs2)
            mw, ma, md = _moon_next_aspect(engine_json)
            org = [f"{qr}-{qs} arası en yakın majör açı {a}° (orb {o}°)"]
            if mw:
                org.append(f"Ay yaklaşan açısı {mw} {ma}°")
            facts = "; ".join(org) + ". Harita tek, yöntem açılardan okunur."
        elif slot == "choice":
            facts = engine_json.get("two_option", "") or "Seçenekler Ay açısı ile değerlendirilir (iki seçenek kuralı üretmedi)."
        elif slot == "yesno":
            if sv and sv.get("qtype"):
                facts = sv.get("facts", "")
            else:
                me = "perfection=" + str(perf.get("type", "yok")) + " (" + str(perf.get("result", "belirsiz")) + ")"
                facts = f"Hüküm={engine_json.get('verdict','BELİRSİZ')} (skor {engine_json.get('score','?')}); {me}; {qr}-{qs} göstergeleri üzerinden."
        else:
            facts = f"Genel: {pinfo(qr)} vs {pinfo(qs)}; perfection={perf.get('type','yok')} ({perf.get('result','belirsiz')})."

        q_data = pl.get(qs, {})
        return {
            "question": sub,
            "slot": slot,
            "label": part["label"],
            "qtype": (sv or {}).get("qtype"),
            "qtype_label": _QTYPE_SLOT_TR.get((sv or {}).get("qtype")),
            "sub_verdict": (sv or {}).get("verdict"),
            "facts": facts,
            "quesited": qs,
            "quesited_sign": qs_sign,
            "quesited_house": q_data.get("house"),
            "verdict": engine_json.get("verdict"),
        }
    except Exception as e:
        return {"question": sub, "slot": "generic", "label": "KONU",
                "facts": f"Bu alt soru için olgu toplanamadı ({e}).", "verdict": engine_json.get("verdict")}


def sub_answers(engine_json, subs, res=None):
    rows = []
    for s in subs:
        r = sub_answer(engine_json, s, res=res)
        if r and r.get("question"):
            rows.append(r)
    return rows


def multi_instruction_text(engine_json, rows):
    """LLM'e 'her alt soruyu AYNI haritadan, sırayla cevapla' talimati."""
    head = ("Bu soru çoklu/bileşik bir sorudur (Chapter: Compound and Multiple Questions). "
            "Tek harita, birden fazla alt soruyu yanıtlar. Her alt soruyu AYRI PARAGRAF/BAŞLIK "
            "olarak, SIRASIYLA ve alt sorunun verdiğim 'facts' verisine sadık kalarak yanıtla. "
            "Alt soruların hiçbirini atlama, cevapları karıştırma, haritayı yeniden kurma. "
            "Eğer bazı alt sorular aynı konudaysa ortak özeti başa koy. "
            "EVET/HAYIR alt sorularında 'sub_verdict' alanı VARSAA 'sub_verdict' değerini "
            "açıkça söyle (YES/NO/BAĞIMLI), kesin hüküm olarak sun. 'BAĞIMLI' ise önceki "
            "alt sorulara göre gereksiz/moot olduğunu kısaca belirt.")
    lines = [head, ""]
    for r in rows:
        v = f" ({r.get('sub_verdict')})" if r.get("sub_verdict") else ""
        qt = f" [{r.get('qtype_label')}]" if r.get("qtype_label") else ""
        lines.append(f"{r['label']}{qt}{v}: {r['question']}")
        lines.append(f"  -> {r['facts']}")
    return "\n".join(lines)