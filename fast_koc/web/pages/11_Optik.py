"""11-Optik: cevap anahtari + ogrenci cevabi -> otomatik D/Y/B -> sinava isle."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ui
from datetime import date
import streamlit as st
from backend.database import SessionLocal
from backend.models import Profile, SinavSonuc
from backend.engine import mufredat as muf
from backend.engine.optik import optik_karsilastir
from backend.engine.analiz_motoru import konu_analiz

ui.setup("Optik Hızlı Giriş", "🔲")
ui.baslik("Optik Hızlı Giriş", ikon="🔲", alt="Cevap anahtarı + öğrenci cevabından otomatik D/Y/B ve net hesabı.")
oid = st.session_state.get("ogrenci_id")
if not oid:
    st.warning("Önce 1-Profil sayfasından öğrenci seçin.")
    st.stop()
db = SessionLocal()
pr = db.get(Profile, oid)
seg = muf.coz(pr.segment)
st.info(f"{pr.ad} — {muf.etiket_of(seg)}")
st.caption("Harfler A-E; boş için X. Örn. anahtar: ABCDEABCDE, cevap: ABCDXAB CDE")
dersler = muf.dersler(seg)
with st.form("optik"):
    ad = st.text_input("Sınav adı", "Deneme (optik)")
    tur = st.selectbox("Tür", ["deneme", "okul", "TG"])
    tarih = st.date_input("Tarih", date.today())
    ders = st.selectbox("Ders", list(dersler.keys()))
    konu = st.selectbox("Konu (tek konuluk giriş)", [k["kod"] + " — " + k["baslik"] for ks in dersler.values() for k in ks])
    anahtar = st.text_area("Cevap anahtarı", "ABCDEABCDEABCDEABCDE")
    cevap = st.text_area("Öğrenci cevapları", "ABCDXABCDEABCDEABCDE")
    if st.form_submit_button("Hesapla ve kaydet"):
        try:
            r = optik_karsilastir(anahtar, cevap)
            st.success(f"Doğru {r['dogru']} • Yanlış {r['yanlis']} • Boş {r['bos']}")
            kod = konu.split(" — ")[0]
            baslik = konu.split(" — ", 1)[1] if " — " in konu else kod
            giris = [{"kod": kod, "baslik": baslik, "dogru": r["dogru"], "yanlis": r["yanlis"], "bos": r["bos"]}]
            analiz = konu_analiz(giris, segment=seg)
            db.add(SinavSonuc(ogrenci_id=oid, tur=tur, ad=ad, tarih=tarih, ders=ders,
                              konular=giris, toplam_dogru=analiz["toplam_dogru"],
                              toplam_yanlis=analiz["toplam_yanlis"], toplam_bos=analiz["toplam_bos"],
                              net=analiz["net"]))
            db.commit()
            st.success(f"Kaydedildi, net {analiz['net']}. {analiz['ozet_cumle']}")
        except ValueError as e:
            st.error(str(e))
db.close()
