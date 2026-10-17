"""Fast Koç — Streamlit ana sayfa. Çalıştırma: streamlit run web/Home.py (fast_koc klasöründen)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

import ui

ui.setup("Ana Sayfa", "🚀")

ui.baslik(
    "Fast Koç",
    ikon="🚀",
    pill="2026-27 · Maarif + Eski Sistem",
    alt="Maarif Modeli'ne uygun kişiye özel koçluk: konu konu analiz → haftalık ödev → kitap önerisi "
        "→ deneme takvimi → günlük takip → PDF karne. Tek panelde uçtan uca.",
)

ui.metrikler([
    {"etiket": "Segment", "deger": "4", "yardim": "LGS · 9-10-11 · YKS Eski · YKS Maarif"},
    {"etiket": "Deneme Takvimi", "deger": "45", "yardim": "2026-27 resmi + yayınevi"},
    {"etiket": "Modül", "deger": "11", "yardim": "analiz → karne → optik"},
])

ui.bolum("Neler yapabilirsin?")
ui.kartlar([
    {"ikon": "📝", "baslik": "Sınavlarım", "metin": "Deneme netlerini gir, konu konu başarı analizini ve grafiklerini gör."},
    {"ikon": "📚", "baslik": "Ödevlerim", "metin": "Seviyene göre haftalık ve günlük, kitap eşlemeli çalışma planı."},
    {"ikon": "📖", "baslik": "Kitaplarım", "metin": "Konu anlatım / soru bankası önerileri, kapak ve ISBN bilgisiyle."},
    {"ikon": "🗓️", "baslik": "Takvim", "metin": "Türkiye geneli denemeler, başvuru tarihleri ve erken uyarı."},
])

ui.kartlar([
    {"ikon": "📊", "baslik": "Günlük Takip", "metin": "Gün sonu soru/dakika girişi, haftalık-aylık kıyas ve bildirimler."},
    {"ikon": "🎓", "baslik": "Karnem (PDF)", "metin": "Tüm verilerden tek tıkla indirilebilir gelişim karnesi."},
    {"ikon": "🧑‍🏫", "baslik": "Koç / Veli Paneli", "metin": "Veli veya koç bağlanır, öğrenci özetini izler."},
    {"ikon": "🔲", "baslik": "Optik Giriş", "metin": "Cevap anahtarı + öğrenci cevabından otomatik D/Y/B."},
])

ui.bolum("Hızlı başlangıç")
adimlar = st.columns(3)
with adimlar[0]:
    st.markdown("**1. Profil oluştur**")
    st.caption("Sınıfını yaz, segment otomatik önerilir.")
with adimlar[1]:
    st.markdown("**2. Sonuç gir**")
    st.caption("Sınavlarım veya Optik ile netlerini ekle.")
with adimlar[2]:
    st.markdown("**3. Planını al**")
    st.caption("Ödevlerim'de haftalık planını üret.")

st.info("Segmentler: LGS | 9-10-11 Ara Sınıf | YKS Eski Sistem (12/mezun) | YKS Maarif (11. sınıf erken hazırlık). "
        "2026-27'de 12/mezun eski sistemle, 9-10-11 Maarif ile çalışır; 2027-28'de tümü Maarif'e geçer.")
st.warning("Kitap kapakları Google Books / Open Library'den anlık çekilir; internet yoksa yer tutucu gösterilir. "
           "Tanıtım kısa tutulur (telif).")

ui.alt_bilgi()
