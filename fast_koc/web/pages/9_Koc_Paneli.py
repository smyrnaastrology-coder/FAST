"""9-Koc Paneli: veli/koc -> ogrenci baglantisi + ozet (Faz 3)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ui
import streamlit as st
from backend.database import SessionLocal, init_db
from backend.models import Profile, Baglanti, SinavSonuc, GunlukLog
from backend.services.odeme_servisi import plan_of

init_db()
ui.setup("Koç / Veli Paneli", "🧑‍🏫")
ui.baslik("Koç / Veli Paneli", ikon="🧑‍🏫", alt="Veli veya koç, öğrenciye bağlanır ve gelişim özetini izler.")
db = SessionLocal()
sahipler = db.query(Profile).filter(Profile.rol.in_(["veli", "koc"])).all()
if not sahipler:
    st.info("Önce 1-Profil sayfasından rolü veli/koç olan profil oluşturun.")
    db.close(); st.stop()
secili = st.selectbox("Veli/Koç seç", [(p.id, f"{p.ad} [{p.rol}]") for p in sahipler],
                      format_func=lambda x: x[1])
sahip_id = secili[0]
plan = plan_of(db, sahip_id)
st.caption(f"Plan: {plan}" + ("" if plan == "pro" else " (koç paneli MVP'de açık, üretimde pro gerekli)"))

with st.form("bagla"):
    ogrenciler = db.query(Profile).filter_by(rol="ogrenci").all()
    if not ogrenciler:
        st.warning("Bağlanacak öğrenci yok.")
    else:
        osec = st.selectbox("Öğrenci", [(o.id, f"{o.ad} ({o.segment})") for o in ogrenciler],
                            format_func=lambda x: x[1])
        rol = st.selectbox("Bağlantı rolü", ["veli", "koc"])
        if st.form_submit_button("Bağla"):
            var = db.query(Baglanti).filter_by(ogrenci_id=osec[0], sahip_id=sahip_id).first()
            if var:
                var.rol = rol; var.durum = "aktif"
            else:
                db.add(Baglanti(ogrenci_id=osec[0], sahip_id=sahip_id, rol=rol))
            db.commit()
            st.success("Bağlandı.")

st.divider()
ui.bolum("Öğrencilerim")
baglar = db.query(Baglanti).filter_by(sahip_id=sahip_id, durum="aktif").all()
for b in baglar:
    o = db.get(Profile, b.ogrenci_id)
    if not o:
        continue
    ss = db.query(SinavSonuc).filter_by(ogrenci_id=o.id).count()
    gs = db.query(GunlukLog).filter_by(ogrenci_id=o.id).count()
    with st.container(border=True):
        st.write(f"**{o.ad}** ({o.segment}/{o.seviye}) — {ss} sınav, {gs} günlük kayıt [{b.rol}]")
        if st.button(f"İncele: {o.ad}", key=f"inc{o.id}"):
            st.session_state["ogrenci_id"] = o.id
            st.success(f"{o.ad} aktif öğrenci yapıldı. Sınavlarım/Günlük sayfalarından bakın.")
db.close()
