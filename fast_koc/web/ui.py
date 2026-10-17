"""Fast Koç — ortak arayüz teması ve bileşenleri.

Tüm web sayfaları bu modülü kullanır:
    import ui
    ui.setup("Sayfa adı", "🎯")
    ui.baslik("Başlık", alt="açıklama", pill="2026-27")
"""
from __future__ import annotations

import streamlit as st

_MARKA = "Fast Koç"

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif; }

/* Arka plan */
.stApp {
  background:
    radial-gradient(1100px 520px at 8% -12%, #E9F0FF 0%, rgba(233,240,255,0) 62%),
    radial-gradient(900px 480px at 100% 0%, #FFF3E0 0%, rgba(255,243,224,0) 55%),
    #F4F6FB;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }

/* Yan menü */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0E1729 0%, #16223C 55%, #1C2C4E 100%);
  border-right: 1px solid rgba(255,255,255,.06);
}
section[data-testid="stSidebar"] * { color: #E7ECF6 !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
  border-radius: 10px; padding: 6px 10px; margin: 2px 4px; transition: background .15s ease;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover { background: rgba(252,163,17,.14); }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
  background: rgba(252,163,17,.20); box-shadow: inset 3px 0 0 #FCA311;
}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #fff !important; }

/* Başlıklar */
h1, h2, h3, h4 { color: #14213D; letter-spacing: -.2px; }
h2 { font-weight: 800; }

/* Butonlar */
.stButton > button, .stFormSubmitButton > button,
.stDownloadButton > button, .stLinkButton > a {
  border: none !important; border-radius: 11px !important;
  font-weight: 600 !important;
  background: linear-gradient(135deg, #16223D 0%, #2A4A8A 100%) !important;
  color: #fff !important; padding: .48rem 1rem !important;
  box-shadow: 0 3px 10px rgba(20,33,61,.20);
  transition: transform .08s ease, box-shadow .18s ease, filter .18s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover,
.stDownloadButton > button:hover, .stLinkButton > a:hover {
  transform: translateY(-1px); filter: brightness(1.06);
  box-shadow: 0 8px 20px rgba(20,33,61,.30);
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background: linear-gradient(135deg, #FCA311 0%, #FF8A00 100%) !important;
  color: #14213D !important;
  box-shadow: 0 4px 14px rgba(252,163,17,.35);
}

/* Kart (border) konteynerleri */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 16px !important; border: 1px solid #E6EAF2 !important;
  background: #fff; box-shadow: 0 6px 18px rgba(20,33,61,.05);
}

/* Metrik kartları */
[data-testid="stMetric"] {
  background: #fff; border: 1px solid #E6EAF2; border-radius: 16px;
  padding: 16px 18px; box-shadow: 0 6px 18px rgba(20,33,61,.05);
}
[data-testid="stMetricValue"] { color: #14213D; font-weight: 800; }
[data-testid="stMetricLabel"] { color: #64748B; font-weight: 600; }

/* Expander */
[data-testid="stExpander"] {
  border: 1px solid #E6EAF2 !important; border-radius: 14px !important;
  box-shadow: 0 3px 12px rgba(20,33,61,.045); overflow: hidden; background: #fff;
}
[data-testid="stExpander"] summary { font-weight: 600; color: #14213D; }

/* Form / giriş alanları */
[data-baseweb="input"], [data-baseweb="select"] > div,
.stTextArea textarea, [data-testid="stNumberInputContainer"] {
  border-radius: 10px !important;
}
.stTextArea textarea:focus, [data-baseweb="input"]:focus-within { border-color: #FCA311 !important; }

/* Uyarı kutuları */
[data-testid="stAlert"] { border-radius: 13px; border: 1px solid rgba(20,33,61,.06); }

/* Tablo */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border-radius: 14px; overflow: hidden; border: 1px solid #E6EAF2;
}

/* Sekmeler */
[data-baseweb="tab-list"] { gap: 6px; }
[data-baseweb="tab"] { border-radius: 10px 10px 0 0; font-weight: 600; }
[aria-selected="true"][data-baseweb="tab"] { color: #14213D; }

/* ==== Özel bileşen sınıfları ==== */
.fk-hero {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #0E1729 0%, #22355F 58%, #2A4A8A 100%);
  color: #fff; border-radius: 22px; padding: 32px 36px; margin-bottom: 22px;
  box-shadow: 0 18px 44px rgba(14,23,41,.28);
}
.fk-hero::after {
  content: ""; position: absolute; right: -70px; top: -70px;
  width: 260px; height: 260px; border-radius: 50%;
  background: radial-gradient(circle, rgba(252,163,17,.45) 0%, rgba(252,163,17,0) 68%);
}
.fk-hero .fk-ic { font-size: 40px; }
.fk-hero h1 { color: #fff; margin: .35rem 0 0; font-size: 34px; font-weight: 800; letter-spacing: -.6px; }
.fk-hero p { color: #C3CEE6; margin: .45rem 0 0; font-size: 15px; max-width: 760px; line-height: 1.55; }
.fk-pill {
  display: inline-block; background: rgba(252,163,17,.16); color: #FCA311 !important;
  border: 1px solid rgba(252,163,17,.55); padding: 4px 13px; border-radius: 999px;
  font-size: 12px; font-weight: 700; letter-spacing: .3px; text-transform: uppercase;
}
.fk-card {
  background: #fff; border: 1px solid #E6EAF2; border-left: 4px solid #FCA311;
  border-radius: 16px; padding: 20px 20px 18px; height: 100%;
  box-shadow: 0 6px 18px rgba(20,33,61,.06);
  transition: transform .12s ease, box-shadow .2s ease;
}
.fk-card:hover { transform: translateY(-3px); box-shadow: 0 16px 32px rgba(20,33,61,.13); }
.fk-card .fk-ic { font-size: 26px; }
.fk-card h4 { margin: .55rem 0 .3rem; color: #14213D; font-size: 16px; font-weight: 700; }
.fk-card p { color: #64748B; font-size: 13.5px; margin: 0; line-height: 1.55; }
.fk-bolum { display: flex; align-items: center; gap: 10px; margin: 28px 0 14px; }
.fk-bolum .bar { width: 6px; height: 22px; border-radius: 4px; background: linear-gradient(#FCA311, #FF8A00); }
.fk-bolum h3 { margin: 0; color: #14213D; font-size: 20px; font-weight: 700; }
.fk-badge { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.fk-badge.ok { background: #DCFCE7; color: #166534; }
.fk-badge.warn { background: #FEF3C7; color: #92400E; }
.fk-badge.info { background: #DBEAFE; color: #1E40AF; }
.fk-badge.muted { background: #EEF2F7; color: #475569; }
.fk-foot { text-align: center; color: #94A3B8; font-size: 12.5px; margin-top: 40px; }
"""


def setup(page_title: str = "Fast Koç", ikon: str = "🚀") -> None:
    """Sayfa yapılandırması + global CSS. Her sayfanın başında çağrılır."""
    try:
        st.set_page_config(page_title=f"{page_title} · {_MARKA}", page_icon=ikon,
                           layout="wide", initial_sidebar_state="expanded",
                           menu_items={"about": "Fast Koç — Maarif odaklı kişisel koçluk."})
    except Exception:
        pass
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


def baslik(baslik: str, alt: str | None = None, ikon: str | None = None,
           pill: str | None = None) -> None:
    """Sayfa üstünde gradient hero başlık."""
    ic = f'<div class="fk-ic">{ikon}</div>' if ikon else ""
    pi = f'<span class="fk-pill">{pill}</span>' if pill else ""
    p = f"<p>{alt}</p>" if alt else ""
    st.markdown(
        f'<div class="fk-hero">{pi}{ic}<h1>{baslik}</h1>{p}</div>',
        unsafe_allow_html=True,
    )


def bolum(metin: str) -> None:
    """Alt bölüm başlığı (turuncu çizgili)."""
    st.markdown(
        f'<div class="fk-bolum"><span class="bar"></span><h3>{metin}</h3></div>',
        unsafe_allow_html=True,
    )


def kartlar(kart_listesi: list[dict]) -> None:
    """[{ikon, baslik, metin}] listesini eşit sütunlu kartlar olarak çizer."""
    if not kart_listesi:
        return
    kolonlar = st.columns(len(kart_listesi))
    for kolon, k in zip(kolonlar, kart_listesi):
        with kolon:
            st.markdown(
                f'<div class="fk-card"><div class="fk-ic">{k.get("ikon", "")}</div>'
                f'<h4>{k.get("baslik", "")}</h4>'
                f'<p>{k.get("metin", "")}</p></div>',
                unsafe_allow_html=True,
            )


def metrikler(metrik_listesi: list[dict]) -> None:
    """[{etiket, deger, yardim}] listesini metrik kartları olarak çizer."""
    if not metrik_listesi:
        return
    kolonlar = st.columns(len(metrik_listesi))
    for kolon, m in zip(kolonlar, metrik_listesi):
        with kolon:
            st.metric(m.get("etiket", ""), m.get("deger", ""), m.get("yardim"))


def rozet(metin: str, tip: str = "info") -> str:
    """Renkli rozet HTML'i döndürür (st.markdown ile unsafe_allow_html kullanın)."""
    return f'<span class="fk-badge {tip}">{metin}</span>'


def alt_bilgi(metin: str = "Fast Koç · 2026-27 · Maarif + eski sistem") -> None:
    st.markdown(f'<div class="fk-foot">{metin}</div>', unsafe_allow_html=True)
