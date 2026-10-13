"""6-Gunluk: gun sonu soru girisi + odev kiyas yorumu."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from datetime import date
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from backend.database import SessionLocal
from backend.models import Profile, GunlukLog, Odev
from backend.engine.yorum_motoru import gunluk_kiyas, donem_yorumu

st.title("📊 Günlük + Raporlarım")
oid = st.session_state.get("ogrenci_id")
if not oid:
    st.warning("Once 1-Profil sayfasindan ogrenci secin.")
    st.stop()
db = SessionLocal()
pr = db.get(Profile, oid)
st.info("🔔 Gun sonu hatirlatma: bugun cozdugun soru sayisini asagidan gir. Bu bildirim uygulama icidir (push yok).")
with st.form("gunluk"):
    t = st.date_input("Tarih", date.today())
    soru = st.number_input("Cozulen soru", 0, 1000, 50)
    dk = st.number_input("Calisilan dakika", 0, 1200, 90)
    notlar = st.text_input("Not (opsiyonel)", "")
    if st.form_submit_button("Kaydet"):
        var = db.query(GunlukLog).filter_by(ogrenci_id=oid, tarih=t).first()
        if var:
            var.cozulen_soru = soru; var.calisilan_dk = dk; var.notlar = notlar
        else:
            db.add(GunlukLog(ogrenci_id=oid, tarih=t, cozulen_soru=soru, calisilan_dk=dk, notlar=notlar))
        db.commit()
        odevler = db.query(Odev).filter_by(ogrenci_id=oid, tarih=t).all()
        st.success(gunluk_kiyas(pr.gunluk_hedef_soru, soru, [o.adet for o in odevler]))
st.divider()
loglar = db.query(GunlukLog).filter_by(ogrenci_id=oid).order_by(GunlukLog.tarih).all()
if loglar:
    st.subheader("Haftalik / aylik / kumulatif")
    tarihler = [l.tarih.isoformat()[5:] for l in loglar[-30:]]
    sorular = [l.cozulen_soru for l in loglar[-30:]]
    dklar = [l.calisilan_dk for l in loglar[-30:]]
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(tarihler, sorular, color="#FCA311")
    ax.set_title("Gunluk cozulen soru (son 30 kayit)")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)
    fig2, ax2 = plt.subplots(figsize=(8, 3))
    ax2.plot(tarihler, dklar, marker="o", color="#14213D")
    ax2.set_title("Calisilan dakika")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig2)
    haftalik = [sum(sorular[i:i+7]) for i in range(0, len(sorular), 7)]
    st.info(donem_yorumu(haftalik, [], []))
    st.table([{"Tarih": l.tarih.isoformat(), "Soru": l.cozulen_soru, "Dk": l.calisilan_dk} for l in loglar[-14:][::-1]])
else:
    st.write("Henuz gunluk girisi yok.")
st.divider()
st.subheader("🔔 Bildirim kutusu")
st.write("Gun sonu + TG erken uyarilari burada toplanir (uygulama ici).")
from backend.models import Bildirim
from backend.services.bildirim_servisi import gun_sonu_hatirlatma_uret, erken_uyari_tara
if st.button("Bildirimleri tazele"):
    gun_sonu_hatirlatma_uret(db, oid)
    erken_uyari_tara(db)
bils = db.query(Bildirim).filter_by(ogrenci_id=oid).order_by(Bildirim.id.desc()).limit(15).all()
for b in bils:
    kanal = getattr(b, "kanal", "uygulama_ici")
    rozet = "📲 push" if kanal == "push" else "📭 uygulama-içi"
    st.write(f"{'✉️' if not b.okundu else '📭'} [{b.tip}|{rozet}] {b.metin}")
db.close()
