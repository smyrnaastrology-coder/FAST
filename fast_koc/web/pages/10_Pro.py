"""10-Pro: plan + odeme stub + push cihaz kaydi (Faz 3)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from backend.database import SessionLocal, init_db
from backend.models import Profile, Cihaz
from backend.services.odeme_servisi import plan_of, checkout_link, pro_aktif_et, PLANLAR

init_db()
st.title("⭐ Pro & Cihazlar")
oid = st.session_state.get("ogrenci_id")
if not oid:
    st.warning("Önce 1-Profil sayfasından profil seçin.")
    st.stop()
db = SessionLocal()
pr = db.get(Profile, oid)
plan = plan_of(db, oid)
st.info(f"{pr.ad} — mevcut plan: **{plan}** | özellikler: {', '.join(PLANLAR[plan]['ozellik'])}")
c1, c2 = st.columns(2)
with c1:
    st.subheader("Pro'ya yükselt")
    st.write(f"Pro: {PLANLAR['pro']['ucret']} {PLANLAR['pro']['para']} — koç paneli + push önceliği.")
    if st.button("Checkout linki üret (stub)"):
        link = checkout_link(oid)
        st.json(link)
    if st.button("Test modunda Pro'yu aktif et"):
        ab = pro_aktif_et(db, oid, "test-session")
        st.success(f"Pro aktif: {ab.bitis}")
with c2:
    st.subheader("Push cihazı kaydet")
    st.caption("Mobil FCM token buraya yapıştırılır (gerçek token Firebase'den gelir).")
    token = st.text_input("FCM token")
    platform = st.selectbox("Platform", ["android", "ios", "web"])
    if st.button("Kaydet"):
        if not token:
            st.error("Token girin.")
        else:
            var = db.query(Cihaz).filter_by(fcm_token=token).first()
            if var:
                var.ogrenci_id = oid; var.aktif = True
            else:
                db.add(Cihaz(ogrenci_id=oid, fcm_token=token, platform=platform))
            db.commit()
            st.success("Cihaz kaydedildi.")
    cihazlar = db.query(Cihaz).filter_by(ogrenci_id=oid, aktif=True).all()
    st.write(f"Kayıtlı cihaz: {len(cihazlar)}")
db.close()
