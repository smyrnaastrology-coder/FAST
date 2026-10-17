"""3-Odevlerim: haftalik plan uret + gunluk onay."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ui
from datetime import date
import streamlit as st
from backend.database import SessionLocal
from backend.models import Profile, SinavSonuc, Odev
from backend.engine import analiz_motoru, odev_motoru
from backend.engine import mufredat as muf
from backend.services.kitap_servisi import kitap_oner

ui.setup("Ödevlerim", "📚")
ui.baslik("Ödevlerim", ikon="📚", alt="Seviyene göre haftalık ve günlük, kitap eşlemeli çalışma planı.")
oid = st.session_state.get("ogrenci_id")
if not oid:
    st.warning("Once 1-Profil sayfasindan ogrenci secin.")
    st.stop()
db = SessionLocal()
pr = db.get(Profile, oid)
sinavlar = db.query(SinavSonuc).filter_by(ogrenci_id=oid).all()
if not sinavlar:
    st.warning("Once 2-Sinavlarim sayfasinda sonuc girin.")
    db.close(); st.stop()
analiz = analiz_motoru.cok_sinav_birlestir([{"konular": s.konular} for s in sinavlar])
st.success(analiz["ozet_cumle"])
if st.button("🔄 Bu haftanin planini uret"):
    esleme = {}
    for o in analiz.get("oncelikli", []):
        oner = kitap_oner(muf.coz(pr.segment), konu_kodlari=[o["kod"]], ogrenci_seviye=pr.seviye, limit=1)
        if oner:
            esleme[o["kod"]] = f"{oner[0]['baslik']} ({oner[0]['yayin']})"
    plan = odev_motoru.haftalik_plan(pr.seviye, muf.coz(pr.segment), analiz, kitap_esleme=esleme)
    bugun = date.today()
    hafta = f"{bugun.isocalendar().year}-W{bugun.isocalendar().week:02d}"
    db.query(Odev).filter_by(ogrenci_id=oid, hafta=hafta).delete()
    for o in plan:
        db.add(Odev(ogrenci_id=oid, hafta=hafta, gun=o["gun"],
                    tarih=date.fromisoformat(o["tarih"]), ders=o["ders"],
                    konu_kod=o["konu_kod"], konu_baslik=o["konu_baslik"],
                    kaynak_kitap_id=o.get("kaynak", ""), adet=o["adet"],
                    hedef_dk=o.get("hedef_dk", 45)))
    db.commit()
    st.success(f"{hafta} plani olustu.")
odevler = db.query(Odev).filter_by(ogrenci_id=oid).order_by(Odev.tarih.desc()).limit(21).all()
for o in odevler:
    with st.expander(f"{o.tarih} {o.gun} — {o.ders}: {o.konu_baslik} ({o.adet} soru) [{o.durum}]"):
        st.write(f"Kaynak: {o.kaynak_kitap_id or '-'} | Hedef sure: {o.hedef_dk} dk")
        yap = st.number_input("Yapilan", 0, 500, o.yapilan or 0, key=f"y{o.id}")
        if st.button("Onayla", key=f"ok{o.id}"):
            o.yapilan = yap
            o.durum = "yapildi" if yap >= o.adet else "eksik"
            db.commit()
            st.success(f"Kaydedildi: {o.durum}")
db.close()
