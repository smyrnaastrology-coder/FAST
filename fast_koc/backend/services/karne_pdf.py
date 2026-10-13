"""Fast Koc — PDF karne raporu (reportlab + matplotlib grafikler)."""
from __future__ import annotations
import io
import os
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak)

FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "fonts")
LACIVERT = colors.HexColor("#14213D")
TURUNCU = colors.HexColor("#FCA311")
GRIMSI = colors.HexColor("#6B7280")


def _fontlari_kaydet():
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONTS_DIR, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf")))
        return "DejaVu", "DejaVu-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


NORMAL, BOLD = _fontlari_kaydet()


def _stilleri():
    base = getSampleStyleSheet()
    baslik = ParagraphStyle("Baslik", parent=base["Title"], fontName=BOLD, textColor=LACIVERT, fontSize=22)
    h2 = ParagraphStyle("H2", parent=base["Heading2"], fontName=BOLD, textColor=LACIVERT, fontSize=14,
                        spaceBefore=10, spaceAfter=6)
    normal = ParagraphStyle("Normal2", parent=base["Normal"], fontName=NORMAL, fontSize=10, leading=14)
    kucuk = ParagraphStyle("Kucuk", parent=base["Normal"], fontName=NORMAL, fontSize=8.5,
                           leading=11, textColor=GRIMSI)
    return baslik, h2, normal, kucuk


def _grafik_soru(loglar) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(7, 2.8))
    tarihler = [l.tarih.isoformat()[5:] for l in loglar[-14:]]
    sorular = [l.cozulen_soru for l in loglar[-14:]]
    ax.bar(tarihler, sorular, color="#FCA311")
    ax.set_title("Günlük çözülen soru (son 14 kayıt)")
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def _grafik_konu(analiz) -> io.BytesIO:
    konular = analiz.get("konular", [])[:12]
    fig, ax = plt.subplots(figsize=(7, max(2.5, len(konular) * 0.4)))
    isim = [(k["baslik"] or k["kod"])[:24] for k in konular]
    deger = [k["basari"] for k in konular]
    renk = ["#EF4444" if v < 40 else ("#F59E0B" if v < 70 else "#10B981") for v in deger]
    ax.barh(isim, deger, color=renk)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Başarı %")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def karne_pdf_uret(profil, sinavlar, loglar, odevler, analiz, kitap_onerileri, yaklasan_denemeler) -> bytes:
    """Tüm veriyi alıp PDF bytes döndürür. DB bağımsız (test edilebilir)."""
    baslik_st, h2_st, normal_st, kucuk_st = _stilleri()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=15 * mm,
                            title=f"Fast Koc Karne - {profil.ad}")

    ogeler = []
    ogeler.append(Paragraph("🚀 Fast Koç — Öğrenci Karnesi", baslik_st))
    try:
        from ..engine import mufredat as _muf
        seg_etiket = _muf.etiket_of(getattr(profil, "segment", ""))
    except Exception:
        seg_etiket = getattr(profil, "segment", "")
    ogeler.append(Paragraph(
        f"{profil.ad} &nbsp;|&nbsp; {seg_etiket} &nbsp;|&nbsp; Seviye: {profil.seviye} "
        f"&nbsp;|&nbsp; Hedef: {profil.hedef or '-'} &nbsp;|&nbsp; Tarih: {date.today().isoformat()}",
        kucuk_st))
    ogeler.append(Spacer(1, 6))

    # Özet metrikler
    toplam_soru = sum(l.cozulen_soru for l in loglar)
    toplam_dk = sum(l.calisilan_dk for l in loglar)
    son_netler = [s.net for s in sinavlar[-5:]]
    ozet_veri = [
        ["Sınav sayısı", "Toplam soru", "Toplam süre (sa)", "Son net", "Kritik konu"],
        [str(len(sinavlar)), str(toplam_soru), f"{toplam_dk / 60:.1f}",
         f"{son_netler[-1]:.1f}" if son_netler else "-",
         str(analiz.get("kritik_sayisi", 0))],
    ]
    t = Table(ozet_veri, colWidths=[32 * mm] * 5)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LACIVERT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), BOLD),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8FC")]),
    ]))
    ogeler.append(t)
    ogeler.append(Spacer(1, 4))
    ogeler.append(Paragraph(analiz.get("ozet_cumle", ""), normal_st))

    # Konu analizi
    ogeler.append(Paragraph("1. Konu Bazında Analiz", h2_st))
    if analiz.get("konular"):
        satirlar = [["Konu", "D", "Y", "B", "Başarı%", "Durum"]]
        for k in analiz["konular"]:
            satirlar.append([Paragraph((k["baslik"] or k["kod"])[:40], normal_st),
                             str(k["dogru"]), str(k["yanlis"]), str(k["bos"]),
                             f"%{k['basari']}", k["durum"]])
        tk = Table(satirlar, colWidths=[70 * mm, 12 * mm, 12 * mm, 12 * mm, 22 * mm, 28 * mm])
        tk.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TURUNCU),
            ("FONTNAME", (0, 0), (-1, 0), BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        ogeler.append(tk)
        ogeler.append(Spacer(1, 4))
        ogeler.append(Image(_grafik_konu(analiz), width=150 * mm, height=70 * mm))
    else:
        ogeler.append(Paragraph("Henüz sınav sonucu yok.", normal_st))

    # Günlük trend
    ogeler.append(Paragraph("2. Günlük Takip Trendi", h2_st))
    if loglar:
        ogeler.append(Image(_grafik_soru(loglar), width=150 * mm, height=60 * mm))
        son7 = loglar[-7:]
        tab = [["Tarih", "Soru", "Süre (dk)"]] + [
            [l.tarih.isoformat(), str(l.cozulen_soru), str(l.calisilan_dk)] for l in son7]
        tg = Table(tab, colWidths=[40 * mm, 30 * mm, 30 * mm])
        tg.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), LACIVERT),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("FONTNAME", (0, 0), (-1, 0), BOLD),
                                ("FONTSIZE", (0, 0), (-1, -1), 9),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        ogeler.append(tg)
    else:
        ogeler.append(Paragraph("Günlük giriş yok.", normal_st))

    ogeler.append(PageBreak())

    # Haftalık ödev
    ogeler.append(Paragraph("3. Haftalık Ödev Planı", h2_st))
    if odevler:
        ot = [["Gün", "Ders", "Konu", "Soru", "Kaynak"]]
        for o in odevler[:14]:
            ot.append([o.gun, Paragraph((o.ders or "")[:20], normal_st),
                       Paragraph((o.konu_baslik or "")[:40], normal_st),
                       str(o.adet), Paragraph((o.kaynak_kitap_id or "-")[:36], kucuk_st)])
        to = Table(ot, colWidths=[24 * mm, 28 * mm, 55 * mm, 14 * mm, 39 * mm])
        to.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TURUNCU),
                                ("FONTNAME", (0, 0), (-1, 0), BOLD),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        ogeler.append(to)
    else:
        ogeler.append(Paragraph("Ödev planı üretilmemiş.", normal_st))

    # Kitap önerileri
    ogeler.append(Paragraph("4. Seviyene Göre Kitap Önerileri", h2_st))
    for k in (kitap_onerileri or [])[:6]:
        ogeler.append(Paragraph(
            f"<b>{k.get('baslik','')}</b> — {k.get('yayin','')} | {k.get('tur','')} | "
            f"seviye {k.get('seviye','')} | ISBN {k.get('isbn','-')}", normal_st))
        if k.get("neden"):
            ogeler.append(Paragraph(f"Neden: {k['neden']}", kucuk_st))

    # Takvim
    ogeler.append(Paragraph("5. Yaklaşan Denemeler", h2_st))
    if yaklasan_denemeler:
        dt = [["Deneme", "Tarih", "Kalan"]] + [
            [Paragraph(d.ad[:50], normal_st), d.tarih.isoformat(), str((d.tarih - date.today()).days)]
            for d in yaklasan_denemeler[:6]]
        td = Table(dt, colWidths=[90 * mm, 30 * mm, 25 * mm])
        td.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), LACIVERT),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("FONTNAME", (0, 0), (-1, 0), BOLD),
                                ("FONTSIZE", (0, 0), (-1, -1), 9),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        ogeler.append(td)
    else:
        ogeler.append(Paragraph("Yaklaşan deneme yok.", normal_st))

    ogeler.append(Spacer(1, 8))
    ogeler.append(Paragraph(
        "Fast Koç ile üretildi. Kitap kapak/tanıtımları bilgilendirme amaçlıdır; "
        "telifli içerik kopyalanmaz.", kucuk_st))

    def _altlik(canvas, doc):
        canvas.saveState()
        canvas.setFont(NORMAL, 8)
        canvas.setFillColor(GRIMSI)
        canvas.drawString(15 * mm, 12 * mm, f"Fast Koç • {profil.ad} • {date.today().isoformat()}")
        canvas.drawRightString(195 * mm, 12 * mm, f"Sayfa {doc.page}")
        canvas.restoreState()

    doc.build(ogeler, onFirstPage=_altlik, onLaterPages=_altlik)
    return buf.getvalue()
