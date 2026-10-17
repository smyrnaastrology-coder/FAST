"""1-Profil: ogrenci olustur / sec. Veriler SQLite'da (MVP) tutulur."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import ui
from backend.database import SessionLocal, init_db
from backend.models import Profile
from backend.engine import mufredat as muf

ui.setup("Profil", "👤")
ui.baslik("Profil", ikon="👤", alt="Öğrenci profili oluştur veya seç. Sınıfını yazınca segment otomatik önerilir.")
init_db()
db = SessionLocal()
profilller = db.query(Profile).order_by(Profile.id.desc()).all()
if profilller:
    ui.bolum("Kayıtlı profiller")
    for p in profilller:
        rol = getattr(p, "rol", "ogrenci")
        if st.button(f"Sec: {p.ad} [{rol}] ({muf.etiket_of(p.segment)}/{p.seviye})", key=f"sec{p.id}"):
            st.session_state["ogrenci_id"] = p.id
            st.success(f"Secildi: {p.ad}")
secili = st.session_state.get("ogrenci_id")
if secili:
    st.info(f"Aktif ogrenci id: {secili}")
st.divider()
ui.bolum("Yeni profil")
st.caption("2026-27: 9-10-11 Maarif, 12/mezun eski sistem. Sınıfını yaz, segment önerilsin.")
sinif_on = st.text_input("Sinif (örn 8, 10, 12/mezun)", "12", key="sinif_on")
onerilen = muf.siniftan_oner(sinif_on)
st.caption(f"Önerilen segment: **{muf.etiket_of(onerilen)}**")
with st.form("profil"):
    ad = st.text_input("Ad", "Ornek Ogrenci")
    rol = st.selectbox("Rol", ["ogrenci", "veli", "koc"])
    secenekler = muf.secilebilir_segmentler()
    segment = st.selectbox("Segment", secenekler,
                           index=secenekler.index(onerilen) if onerilen in secenekler else 0,
                           format_func=muf.etiket_of)
    sinif = st.text_input("Sinif (kayda geçecek)", sinif_on)
    alan = st.selectbox("Alan (YKS)", ["", "SAY", "EA", "SOZ", "DIL"])
    seviye = st.selectbox("Seviye", ["temel", "orta", "ileri"])
    hedef = st.text_input("Hedef", "TYT 90+ net")
    gunluk = st.number_input("Gunluk hedef soru", 10, 500, 80)
    if st.form_submit_button("Olustur"):
        p = Profile(ad=ad, rol=rol, segment=muf.coz(segment), sinif=sinif, alan=alan, seviye=seviye,
                    hedef=hedef, gunluk_hedef_soru=gunluk)
        db.add(p); db.commit(); db.refresh(p)
        st.session_state["ogrenci_id"] = p.id
        st.success(f"Olusturuldu, id={p.id} rol={rol} ({muf.etiket_of(p.segment)})")
db.close()
