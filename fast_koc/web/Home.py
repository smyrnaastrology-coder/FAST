"""Fast Koc — Streamlit ana sayfa. Calistirma: streamlit run web/Home.py (fast_koc klasorunden)."""
import streamlit as st

st.set_page_config(page_title="Fast Koc", page_icon="🚀", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
.main { background: #F7F8FC; }
h1, h2, h3 { color: #14213D; }
.stButton>button { background: #FCA311; color: #14213D; font-weight: 700; border-radius: 12px; border: none; }
.stButton>button:hover { background: #e59400; color: white; }
.kart { background: white; border-radius: 14px; padding: 18px; border: 1px solid #E5E7EB; box-shadow: 0 2px 8px rgba(20,33,61,.06); }
.kucuk { color: #6B7280; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Fast Koç")
st.caption("Maarif Modeli ile kisiye ozel kocluk: analiz → haftalik odev → kitap onerisi → deneme takvimi → gunluk takip.")

c1, c2, c3, c4 = st.columns(4)
c1.markdown('<div class="kart"><b>📝 Sınavlarım</b><br><span class="kucuk">Sonuclari gir, konu konu analiz gor.</span></div>', unsafe_allow_html=True)
c2.markdown('<div class="kart"><b>📚 Ödevlerim</b><br><span class="kucuk">Seviyene gore haftalik + gunluk plan.</span></div>', unsafe_allow_html=True)
c3.markdown('<div class="kart"><b>📖 Kitaplarım</b><br><span class="kucuk">Konu anlatim / soru bankasi / test, kapakli oneriler.</span></div>', unsafe_allow_html=True)
c4.markdown('<div class="kart"><b>🗓️ Takvim</b><br><span class="kucuk">2026-27 Turkiye geneli denemeler + erken uyari.</span></div>', unsafe_allow_html=True)

st.divider()
st.subheader("Basla")
st.write("Soldaki menuden sayfaya git: **1-Profil** ile ogrenci olustur, **2-Sinavlarim** ile ilk sonucu gir, **3-Odevlerim** ile planini al.")
st.info("Segmentler: LGS | 9-10-11 Ara Sınıf | YKS Eski Sistem (12/mezun) | YKS Maarif (11. sınıf erken hazırlık). "
        "2026-27'de 12/mezun eski sistemle, 9-10-11 Maarif ile çalışır; 2027-28'de tümü Maarif'e geçer.")
st.warning("Kitap kapaklari Google Books / Open Library'den anlik cekilir; internet yoksa yer tutucu gosterilir. Tanitim kisa tutulur (telif).")
