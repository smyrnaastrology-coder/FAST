# -*- coding: utf-8 -*-
"""
Ashtakoot Streamlit bileşenleri.

Bu modül `app.py` içinden çağrılır ve şunları sunar:
    tablo_goster      -> 8 kootalı puan tablosu (metin açıklamalarıyla)
    puan_grafik       -> toplam puanın 36 üzerindeki konumu
    kutu_goster       -> renk kodlu koota kutuları
    uyum_haritasi_ciz -> 27 nakṣatra uyum haritası (tek kişi profili)
    profil_goster     -> Ay Nakṣatra Profili (tek kişi)

Tüm görselleştirmeler matplotlib ile yapılır; Streamlit'e doğrudan bağımlılık
yoktur, böylece aynı fonksiyonlar PDF üretiminde de yeniden kullanılabilir.
"""

from typing import List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

import ashtakoot_metin as MT
from ashtakoot_motoru import (
    AZAMI_TOPLAM, AshtaKootSonuc, AyBilgisi, Koota, ashtakoot_hesapla,
    kendisi_ile, nakshatra_uyum_haritasi,
)

# ---------------------------------------------------------------------------
# Görsel tema
# ---------------------------------------------------------------------------
_LACIVERT = "#12263A"
_ALTIN = "#C9A227"
_GRI = "#5B6B7A"
_ARKA = "#FFFFFF"
_KIZIL = "#B23A48"

#: Puan oranına göre renk (0–1).
RENK_SKALA = [
    (0.00, "#C0392B"),   # 0    kritik
    (0.25, "#D97A26"),   # ~9   zayıf
    (0.50, "#D4B106"),   # ~18  orta
    (0.75, "#7BA05B"),   # ~27  iyi
    (1.00, "#2E7D5B"),   # 36   mükemmel
]


def renk_uret(puan: int, azami: int) -> str:
    """Puanı renk skalasındaki rengin HTML karşılığına çevirir."""
    if azami <= 0:
        return RENK_SKALA[0][1]
    oran = max(0.0, min(1.0, puan / azami))
    for (o0, c0), (o1, c1) in zip(RENK_SKALA, RENK_SKALA[1:]):
        if o0 <= oran <= o1:
            t = 0 if o1 == o0 else (oran - o0) / (o1 - o0)
            return _karis(c0, c1, t)
    return RENK_SKALA[-1][1]


def _karis(c0: str, c1: str, t: float) -> str:
    a = tuple(int(c0[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(c1[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def seviye_renk(seviye: str) -> str:
    return {"cok_dusuk": RENK_SKALA[0][1], "dusuk": RENK_SKALA[1][1],
            "orta": RENK_SKALA[3][1], "yuksek": RENK_SKALA[4][1]}.get(seviye, _GRI)


def koota_adi(k: Koota, lang: str = "tr") -> str:
    """Kootanın dile göre görünen adı."""
    return {"en": getattr(k, "ad_en", None), "es": getattr(k, "ad_es", None)}.get(
        lang) or getattr(k, "ad_tr", None) or k.ad


# ---------------------------------------------------------------------------
# Metin / tablo
# ---------------------------------------------------------------------------
def tablo_goster(sonuc: AshtaKootSonuc, lang: str = "tr", mod: str = "es_sevgili",
                 ay_a: Optional[AyBilgisi] = None, ay_b: Optional[AyBilgisi] = None,
                 ay_b_tek: bool = False, genislik: int = 100) -> None:
    """8 kootalı puan tablosunu Streamlit'e basar.

    `ay_b_tek=True` olduğunda ikinci sütun yerine "kendisiyle" gösterilir.
    """
    import streamlit as st

    st.markdown(f"### Ashtakoot · 36 · {sonuc.toplam}/{AZAMI_TOPLAM}")
    E = MT.ETIKET[lang]
    basliklar = [E["koota"], E["puan"]]
    if ay_a is not None:
        basliklar.append("A · " + _ay_etiket(ay_a, lang))
        # Her kootanın tek kişilik katkısı; PDF tablosuyla aynı düzen.
        basliklar.append("A · " + E["kendisiyle"])
    if ay_b is not None:
        basliklar.append("B · " + _ay_etiket(ay_b, lang))
        basliklar.append("B · " + E["kendisiyle"])

    satirlar = []
    # Her kişinin koota katkısı, kendisiyle karşılaştırmasından okunur.
    katki_a = ashtakoot_hesapla(ay_a, ay_a) if ay_a is not None else None
    katki_b = ashtakoot_hesapla(ay_b, ay_b) if ay_b is not None else None

    for k in sonuc.kootalar:
        m = MT.metin_getir(k.ad, k.puan, k.azami, lang)
        oran = f"{renk_uret(k.puan, k.azami)}"
        sat = [
            f"**{koota_adi(k, lang)}** <span style='color:{_GRI}'>({k.azami})</span>",
            f'<span style="color:{oran}">●</span> **{k.puan}/{k.azami}**<br>'
            f'<span style="color:{_GRI};font-size:0.85em">{m["baslik"]}</span>',
        ]
        if katki_a is not None:
            sat.append(_katki_hucre(katki_a.koota(k.ad)))
        if katki_b is not None:
            sat.append(_katki_hucre(katki_b.koota(k.ad)))
        satirlar.append(sat)

    st.markdown(
        f'<div style="max-width:{genislik}px">'
        + f'<table style="width:100%;border-collapse:collapse;'
          f'font-family:system-ui,sans-serif;font-size:0.92em">'
        + "<thead><tr>"
        + "".join(
            f'<th style="text-align:left;padding:8px 10px;background:{_LACIVERT};'
            f'color:#fff;border:1px solid #fff">{b}</th>' for b in basliklar)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>"
            + "".join(
                f'<td style="padding:8px 10px;border:1px solid #dde3e8;'
                f'vertical-align:top">{c}</td>'
                for c in sat)
            + "</tr>"
            for sat in satirlar)
        + "</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _ay_etiket(ay: AyBilgisi, lang: str) -> str:
    return ay.ozet(lang)


def _katki_hucre(k: "Koota") -> str:
    """Bir kootanın kişiye özel katkısını okunur metne çevirir."""
    not_ = (k.not_ or "").strip()
    renk = renk_uret(k.puan, k.azami)
    p = f'<span style="color:{renk}">●</span> **{k.puan}/{k.azami}**'
    return f"{p}<br><span style='color:{_GRI};font-size:0.82em'>{not_}</span>" if not_ else p


# ---------------------------------------------------------------------------
# Görseller
# ---------------------------------------------------------------------------
def puan_grafik(sonuc: AshtaKootSonuc, lang: str = "tr", mod: str = "es_sevgili") -> None:
    """Toplam puanı 36'lık çubuk üzerinde gösterir."""
    import streamlit as st
    fig = _puan_grafik_fig(sonuc, lang, mod)
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)


def _puan_grafik_fig(sonuc: AshtaKootSonuc, lang: str = "tr", mod: str = "es_sevgili"):
    fig, ax = plt.subplots(figsize=(9, 2.6), dpi=110)
    fig.patch.set_facecolor(_ARKA)
    ax.set_facecolor(_ARKA)

    toplam = sonuc.toplam
    bant = MT.toplam_metni(sonuc.seviye, lang)
    renk = seviye_renk(sonuc.seviye)

    ax.barh([0], [AZAMI_TOPLAM], height=0.5, color="#EDF0F3", zorder=1)
    ax.barh([0], [toplam], height=0.5, color=renk, zorder=2)

    for x, et in ((0, "0"), (AZAMI_TOPLAM, "36")):
        ax.text(x, -0.42, et, ha="center", va="top", fontsize=8, color=_GRI)

    ax.text(toplam / 2, 0, f"{toplam}/36", ha="center", va="center",
            fontsize=15, fontweight="bold", color="#fff", zorder=3)

    ax.text(0, 0.55, bant["baslik"], ha="left", va="bottom", fontsize=10,
            fontweight="bold", color=renk)
    ax.text(0, 0.38, bant["aciklama"][:110], ha="left", va="bottom", fontsize=8, color=_GRI)

    ax.set_xlim(-1, AZAMI_TOPLAM + 1)
    ax.set_ylim(-0.7, 1.1)
    ax.axis("off")
    return fig


def kutu_goster(sonuc: AshtaKootSonuc, lang: str = "tr", mod: str = "es_sevgili",
                sutun: int = 4) -> None:
    """8 koota için renk kodlu kutular basar."""
    import streamlit as st
    html = ['<div style="display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 14px 0">']
    for k in sonuc.kootalar:
        renk = renk_uret(k.puan, k.azami)
        m = MT.metin_getir(k.ad, k.puan, k.azami, lang)
        html.append(
            f'<div style="flex:1 1 {100 // sutun}%;min-width:150px;border-left:5px solid {renk};'
            f'background:#F7F9FA;border-radius:6px;padding:9px 11px">'
            f'<div style="font-weight:700;color:{_LACIVERT};font-size:0.95em">{koota_adi(k, lang)}'
            f' <span style="color:{_GRI};font-weight:400">({k.azami})</span></div>'
            f'<div style="color:{renk};font-weight:700;font-size:1.05em;margin:2px 0">'
            f'{k.puan}/{k.azami}</div>'
            f'<div style="color:{_GRI};font-size:0.78em;line-height:1.35">{m["baslik"]}</div>'
            f'</div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def profil_goster(ay: AyBilgisi, lang: str = "tr") -> None:
    """Tek kişi için Ay Nakṣatra Profili."""
    import streamlit as st
    s = kendisi_ile(ay)
    not_ = MT.kendisi_notu(lang)
    E = MT.ETIKET[lang]
    st.markdown(f"### {not_['baslik']} · {ay.nakshatra(lang)} {ay.pada}. pada")
    st.markdown(
        f"**{E['burc']}:** {ay.burc(lang)} · **{E['lord']}:** {ay.lord_adi(lang)} · "
        f"**{E['tanri']}:** {ay.tanri_adi(lang)} · "
        f"**{E['gana']}:** {ay.gana_adi(lang)} · "
        f"**{E['varna']}:** {ay.varna_adi(lang)} · "
        f"**{E['yoni']}:** {ay.yoni_adi(lang) or E['yoni_bos']} · "
        f"**{E['vashya']}:** {vashya_ad(ay)} · **{E['nadi']}:** {ay.nadi}")
    st.info(f"{not_['baslik']}: **{s.toplam}/{AZAMI_TOPLAM}**. {not_['aciklama']}")
    kutu_goster(s, lang, mod="kendisi")
    _nadi_ve_tara_notu(ay, lang, s)
    st.caption(not_["ipucu"])


def _nadi_ve_tara_notu(ay: AyBilgisi, lang: str, s: AshtaKootSonuc) -> None:
    import streamlit as st
    nadi = s.koota("nadi")
    tara = s.koota("tara")
    st.markdown(f"**Nadi:** {_detay_metni(nadi)} · puan yok (aynı nadi)\n\n"
                f"**Tara:** {_detay_metni(tara)}")


def _detay_metni(k: Koota) -> str:
    """`Koota.detay` sözlüğünü okunur metne çevirir."""
    d = k.detay or {}
    parcalar = [f"{a}: {b}" for a, b in d.items() if b not in (None, "", [], 0)]
    return " · ".join(parcalar) if parcalar else (k.not_ or "—")


def vashya_ad(ay: AyBilgisi) -> str:
    """Burç numarasından vashya grubunun adını çözer (ters eşleme)."""
    from ashtakoot_motoru import VASHYA_GRUPLARI
    for grup, burclar in VASHYA_GRUPLARI.items():
        if ay.burc_no in burclar:
            return grup
    return "—"


def uyum_haritasi_goster(ay: AyBilgisi, lang: str = "tr", mod: str = "es_sevgili") -> None:
    """27 nakṣatra uyum haritasını tablo olarak basar."""
    import streamlit as st
    harita = nakshatra_uyum_haritasi(ay)
    E = MT.ETIKET[lang]
    st.markdown(f"### {E['harita_baslik']}")
    st.caption(E["harita_aciklama"])
    satirlar = []
    for h in harita:
        renk = renk_uret(h["toplam"], AZAMI_TOPLAM)
        et = (f" <span style='color:#C9A227'>◆ {E['kendi']}</span>"
              if h.get("kendisi") else "")
        # Nakṣatra adı Sanskrit kökenli özel ad olduğu için üç dilde de aynı;
        # çevrilen alanlar lord ve burç.
        satirlar.append([
            f"**{h['nakshatra']}**{et}",
            h.get(f"lord_{lang}", h.get("lord", "—")),
            h.get("tanri", "—"),
            f'<span style="color:{renk}">●</span> **{h["toplam"]}/36**',
            h.get("seviye", "—"),
        ])
    st.markdown(
        '<table style="width:100%;border-collapse:collapse;font-size:0.9em">'
        '<thead><tr>'
        + "".join(f'<th style="text-align:left;padding:7px 9px;background:{_LACIVERT};'
                  f'color:#fff;border:1px solid #fff">{h}</th>'
                  for h in (E["nakshatra"], E["lord"], E["tanri"],
                            E["puan"], E["seviye"]))
        + '</tr></thead><tbody>'
        + "".join("<tr>" + "".join(
            f'<td style="padding:6px 9px;border:1px solid #dde3e8">{c}</td>' for c in sat)
            + "</tr>" for sat in satirlar)
        + "</tbody></table>",
        unsafe_allow_html=True,
    )
