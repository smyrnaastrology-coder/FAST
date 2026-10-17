"""2-Sinavlarim: sonuc girisi + konu analizi + grafik."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ui
from datetime import date
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from backend.database import SessionLocal
from backend.models import Profile, SinavSonuc
from backend.engine.analiz_motoru import konu_analiz
from backend.engine import mufredat as muf

ui.setup("Sınavlarım", "📝")
ui.baslik("Sınavlarım", ikon="📝", alt="Deneme sonuçlarını gir; konu konu başarı analizi ve grafiğini gör.")
oid = st.session_state.get("ogrenci_id")
if not oid:
    st.warning("Once 1-Profil sayfasindan ogrenci secin.")
    st.stop()
db = SessionLocal()
pr = db.get(Profile, oid)
seg = muf.coz(pr.segment)
st.info(f"{pr.ad} — {muf.etiket_of(seg)} / {pr.seviye}")

muf_dersler = muf.dersler(seg)

with st.form("sinav"):
    ad = st.text_input("Sinav adi", "Deneme 1")
    tur = st.selectbox("Tur", ["deneme", "okul", "TG"])
    tarih = st.date_input("Tarih", date.today())
    ders = st.selectbox("Ders", list(muf_dersler.keys()))
    st.write("Konu kirimlari (D/Y/B):")
    girisler = []
    for k in muf_dersler[ders]:
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        c1.write(f"{k['baslik']}")
        d = c2.number_input("D", 0, 50, 0, key=f"d{k['kod']}")
        y = c3.number_input("Y", 0, 50, 0, key=f"y{k['kod']}")
        b = c4.number_input("B", 0, 50, 0, key=f"b{k['kod']}")
        girisler.append({"kod": k["kod"], "baslik": k["baslik"], "dogru": d, "yanlis": y, "bos": b})
    if st.form_submit_button("Kaydet ve analiz et"):
        toplam = sum(g["dogru"] + g["yanlis"] + g["bos"] for g in girisler)
        if toplam == 0:
            st.error("En az bir soru girin.")
        else:
            analiz = konu_analiz(girisler, segment=pr.segment)
            db.add(SinavSonuc(ogrenci_id=oid, tur=tur, ad=ad, tarih=tarih, ders=ders,
                              konular=girisler, toplam_dogru=analiz["toplam_dogru"],
                              toplam_yanlis=analiz["toplam_yanlis"], toplam_bos=analiz["toplam_bos"],
                              net=analiz["net"]))
            db.commit()
            st.success(analiz["ozet_cumle"])

st.divider()
ui.bolum("Geçmiş + analiz")
sinavlar = db.query(SinavSonuc).filter_by(ogrenci_id=oid).order_by(SinavSonuc.tarih.desc()).all()
for s in sinavlar[:10]:
    with st.expander(f"{s.tarih} — {s.ad} ({s.ders}) net {s.net}"):
        a = konu_analiz(s.konular or [], segment=pr.segment)
        st.write(a["ozet_cumle"])
        st.table([{"Konu": k["baslik"], "D": k["dogru"], "Y": k["yanlis"], "B": k["bos"],
                   "Basari%": k["basari"], "Durum": k["durum"]} for k in a["konular"]])
        if a["konular"]:
            fig, ax = plt.subplots(figsize=(7, max(2.5, len(a["konular"]) * 0.45)))
            isim = [k["baslik"][:22] for k in a["konular"]]
            deger = [k["basari"] for k in a["konular"]]
            renk = ["#EF4444" if v < 40 else ("#F59E0B" if v < 70 else "#10B981") for v in deger]
            ax.barh(isim, deger, color=renk)
            ax.set_xlim(0, 100); ax.set_xlabel("Basari %")
            st.pyplot(fig)
db.close()
