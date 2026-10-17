"""8-Karne: PDF karne onizleme + indirme."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ui
import streamlit as st
from backend.database import SessionLocal
from backend.models import Profile, SinavSonuc, GunlukLog, Odev, DenemeTakvim
from backend.engine import analiz_motoru
from backend.engine import mufredat as muf
from backend.services.kitap_servisi import kitap_oner
from backend.services.karne_pdf import karne_pdf_uret

ui.setup("Karnem (PDF)", "🎓")
ui.baslik("Karnem (PDF)", ikon="🎓", alt="Tüm verilerinden tek tıkla indirilebilir gelişim karnesi.")
oid = st.session_state.get("ogrenci_id")
if not oid:
    st.warning("Önce 1-Profil sayfasından öğrenci seçin.")
    st.stop()
db = SessionLocal()
pr = db.get(Profile, oid)
sinavlar = db.query(SinavSonuc).filter_by(ogrenci_id=oid).order_by(SinavSonuc.tarih).all()
loglar = db.query(GunlukLog).filter_by(ogrenci_id=oid).order_by(GunlukLog.tarih).all()
odevler = db.query(Odev).filter_by(ogrenci_id=oid).order_by(Odev.tarih).all()
if sinavlar:
    analiz = analiz_motoru.cok_sinav_birlestir([{"konular": s.konular} for s in sinavlar])
    kodlar = [k.get("kod", "") for s in sinavlar for k in (s.konular or [])]
else:
    analiz = {"konular": [], "kritik_sayisi": 0, "ozet_cumle": "Henüz sınav sonucu yok."}
    kodlar = []
    st.warning("Henüz sınav sonucu yok — karne boş şablon olarak üretilecek.")
oneriler = kitap_oner(muf.coz(pr.segment), konu_kodlari=kodlar, ogrenci_seviye=pr.seviye, limit=6)
yaklasan = db.query(DenemeTakvim).filter(
    DenemeTakvim.segment.in_(muf.takvim_eslesme(pr.segment))).order_by(DenemeTakvim.tarih).all()
st.info(f"{pr.ad} — {len(sinavlar)} sınav, {len(loglar)} günlük kayıt, {len(odevler)} ödev. "
        f"Analiz: {analiz.get('ozet_cumle','')}")
if st.button("📄 PDF üret"):
    with st.spinner("Karne hazırlanıyor..."):
        pdf = karne_pdf_uret(pr, sinavlar, loglar, odevler, analiz, oneriler, yaklasan)
    st.success(f"Hazır ({len(pdf)//1024} KB).")
    st.download_button("⬇️ İndir: fastkoc_karne.pdf", pdf, "fastkoc_karne.pdf", "application/pdf")
db.close()
