# -*- coding: utf-8 -*-
"""
Ashtakoot bölümünü PDF'e ekler.

Bu modül raporlab'a bağımlıdır ve `app.py` içindeki PDF üretim
fonksiyonlarından çağrılır. Veriyi `st.session_state["ashtakoot_sonuc"]`
sözlüğünden okur; anahtar yoksa (panel hiç açılmamışsa) bölüm eklenmez.
"""

from typing import Optional

#: Renkler (app.py'deki paletle uyumlu).
_LACIVERT = "#1A1A2E"
_ALTIN = "#C9A96E"
_ACIK = "#F0F4F8"
_GRI = "#4A5568"
_SATIR = "#FBF7F4"

#: Toplam puan bandına göre renk.
_SEVIYE_RENK = {
    "cok_dusuk": "#B23A48",
    "dusuk": "#C9762B",
    "orta": "#7BA05B",
    "yuksek": "#2E7D5B",
}


def veri_al(session_state: Optional[dict] = None):
    """Panelin kaydettiği sonucu döndürür; yoksa None."""
    if session_state is None:
        import streamlit as st
        session_state = st.session_state
    try:
        return session_state.get("ashtakoot_sonuc")
    except Exception:                                       # noqa: BLE001
        return None


def ekle(story, styles, veri=None, font_normal="DejaVuSans",
         font_bold="DejaVuSans-Bold") -> bool:
    """Ashtakoot tablosunu `story` listesine ekler. Eklediyse True döner."""
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle

    if veri is None:
        veri = veri_al()
    if not veri:
        return False

    # Görünür metinler panelde seçilen dile göre gelir.
    import ashtakoot_metin as MT
    lang = veri.get("lang", "tr")
    E = MT.ETIKET.get(lang, MT.ETIKET["tr"])
    PM = MT.pdf_metin(lang)

    # Başlık kartı
    baslik = f"ASHTAKOOT &middot; {PM['baslik']}"
    alt = PM["alt"]
    kart = f"""
    <table width="100%" cellpadding="8">
    <tr>
        <td bgcolor="{_LACIVERT}" width="6"><font color="{_ALTIN}" size="16">|</font></td>
        <td bgcolor="{_ACIK}" style="padding-left:12px;">
            <font color="{_LACIVERT}" size="14"><b>{baslik}</b></font>
            <br/><font color="{_GRI}" size="9">{alt}</font>
        </td>
    </tr>
    </table>"""
    p_style = ParagraphStyle(
        "AshTR", parent=styles["BodyText"], fontName=font_normal, fontSize=9.5,
        leading=14, textColor=HexColor("#1A1A2E"))
    p_kucuk = ParagraphStyle(
        "AshTRKucuk", parent=p_style, fontSize=8, leading=11,
        textColor=HexColor(_GRI))
    p_baslik = ParagraphStyle(
        "AshBaslik", parent=p_style, fontSize=8.5, leading=11,
        textColor=HexColor("#FFFFFF"))

    story.append(Spacer(1, 14))
    story.append(Paragraph(kart, p_style))
    story.append(Spacer(1, 8))

    # Kişi başlıkları
    a, b = veri.get("a"), veri.get("b")
    kim = []
    if a:
        kim.append(_kisi_metni(a))
    if b:
        kim.append(_kisi_metni(b))
    if kim:
        story.append(Paragraph(
            f'<font color="{_GRI}" size="9">' + " &nbsp;&nbsp;|&nbsp;&nbsp; ".join(kim)
            + "</font>", p_style))
        story.append(Spacer(1, 8))

    # Toplam özeti
    renk = _SEVIYE_RENK.get(veri.get("seviye", ""), _GRI)
    toplam_metin = (
        f'<b>{veri["toplam"]}/{veri["azami"]}</b> &nbsp;(%{veri.get("yuzde", 0)})'
        f' &nbsp;<font color="{renk}"><b>{_duz(veri.get("toplam_baslik", ""))}</b></font>')
    story.append(Paragraph(
        f'<font size="13" color="{_LACIVERT}">{toplam_metin}</font>', p_style))
    aciklama = _duz(veri.get("toplam_aciklama", ""))
    if aciklama:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f'<font size="8.5" color="{_GRI}">{aciklama}</font>', p_kucuk))
    story.append(Spacer(1, 10))

    # Koota tablosu
    katki_a = veri.get("katki_a") or {}
    katki_b = veri.get("katki_b") or {}

    basliklar = [E["koota"], E["puan"]]
    if a:
        basliklar.append(f"A &middot; {E['kendisiyle']}")
    if b:
        basliklar.append(f"B &middot; {E['kendisiyle']}")

    veriler = [[Paragraph(h, p_baslik) for h in basliklar]]
    for k in veri.get("kootalar", []):
        oran = k["puan"] / k["azami"] if k["azami"] else 0
        puan_html = (
            f'<font color="{_puan_renk(oran)}"><b>{k["puan"]}/{k["azami"]}</b></font>'
            f'<br/><font size="7.5" color="{_GRI}">{_duz(k.get("baslik", ""))}</font>')
        satir = [Paragraph(f"<b>{_duz(k['ad'])}</b>", p_kucuk),
                 Paragraph(puan_html, p_kucuk)]
        anahtar = k.get("anahtar") or k.get("ad_tr") or k["ad"]
        if a:
            satir.append(_katki_hucre(katki_a.get(anahtar), p_kucuk))
        if b:
            satir.append(_katki_hucre(katki_b.get(anahtar), p_kucuk))
        veriler.append(satir)

    tab = Table(veriler, colWidths=_sutun_genislikleri(len(basliklar)),
                repeatRows=1)
    stil = [
        ("BACKGROUND", (0, 0), (-1, 0), HexColor(_LACIVERT)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#DDE3E8")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(veriler)):
        stil.append(("BACKGROUND", (0, i), (-1, i),
                     HexColor(_SATIR if i % 2 else "#FFFFFF")))
    tab.setStyle(TableStyle(stil))
    story.append(tab)

    story.append(Spacer(1, 8))
    notlar = [k for k in veri.get("kootalar", []) if k.get("not")]
    if notlar:
        satir_metni = " &nbsp;&middot;&nbsp; ".join(
            f'<b>{_duz(k["ad"])}</b>: {_duz(k["not"])}' for k in notlar)
        story.append(Paragraph(
            f'<font size="7.5" color="{_GRI}">{satir_metni}</font>', p_kucuk))
    story.append(Paragraph(
        f'<font size="7" color="{_GRI}">{_duz(PM["not"])}</font>', p_kucuk))
    return True


def _katki_hucre(puan, p_style):
    """Kendisiyle karşılaştırma hücresi (Nadi her zaman 0)."""
    from reportlab.platypus import Paragraph

    if puan is None:
        return Paragraph("&mdash;", p_style)
    oran = puan / 8.0 if puan <= 8 else 1.0
    return Paragraph(
        f'<font color="{_puan_renk(oran)}"><b>{puan}</b>/8</font>', p_style)


def _kisi_metni(k: dict) -> str:
    ad = k.get("isim") or ""
    yer = " / ".join(x for x in (k.get("sehir", ""), k.get("ulke", "")) if x)
    parcalar = [
        f'<b>{_duz(ad)}</b>' if ad else "",
        f'{k.get("tarih", "")} {k.get("saat", "")}'.strip(),
        _duz(yer),
        f'{_duz(k.get("nakshatra", ""))} &middot; {_duz(k.get("burc", ""))}',
    ]
    return " &middot; ".join(p for p in parcalar if p)


def _sutun_genislikleri(sutun: int):
    if sutun <= 2:
        return [200, 120]
    if sutun == 3:
        return [130, 110, 80]
    return [110, 90, 70, 70]


def _puan_renk(oran: float) -> str:
    if oran <= 0.0:
        return "#C0392B"
    if oran >= 1.0:
        return "#2E7D5B"
    if oran >= 0.7:
        return "#7BA05B"
    if oran >= 0.45:
        return "#B79A16"
    return "#C9762B"


def _duz(metin: str) -> str:
    """PDF güvenliği için &, <, > kaçışlarını yapar."""
    if not metin:
        return ""
    return (str(metin).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))
