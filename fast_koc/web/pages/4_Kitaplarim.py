"""4-Kitaplarim: seviyeye gore kapakli oneriler (ISBN API)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
from backend.database import SessionLocal
from backend.models import Profile, SinavSonuc
from backend.engine import mufredat as muf
from backend.services.kitap_servisi import kitap_oner

st.title("📖 Kitaplarım")
oid = st.session_state.get("ogrenci_id")
if not oid:
    st.warning("Once 1-Profil sayfasindan ogrenci secin.")
    st.stop()
db = SessionLocal()
pr = db.get(Profile, oid)
st.caption(f"{muf.etiket_of(pr.segment)} — sistem: {muf.sistem_of(pr.segment)}")
sinavlar = db.query(SinavSonuc).filter_by(ogrenci_id=oid).all()
kodlar = [k.get("kod", "") for s in sinavlar for k in (s.konular or [])]
tur = st.selectbox("Tur filtresi", ["hepsi", "konu_anlatim", "soru_bankasi", "test", "deneme"])
oneriler = kitap_oner(muf.coz(pr.segment), konu_kodlari=kodlar, ogrenci_seviye=pr.seviye,
                      tur=None if tur == "hepsi" else tur, limit=9)
for k in oneriler:
    with st.container(border=True):
        c1, c2 = st.columns([1, 3])
        try:
            c1.image(k["kapak_url"], width=140)
        except Exception:
            c1.write("📕 kapak yuklenemedi")
        c2.subheader(f"{k['baslik']}")
        durum = k.get("isbn_durum", "yer-tutucu-dogrulanmadi")
        rozet = "✅ doğrulanmış" if durum == "dogrulandi" else "⚠️ ISBN yer-tutucu (editör onayı bekliyor)"
        c2.write(f"**{k['yazar']}** — {k['yayin']} | {k['tur']} | seviye: {k['seviye']} | ISBN: {k.get('isbn','-')}")
        c2.caption(rozet)
        if k.get("satin_alma_arama"):
            c2.link_button("🛒 Satın alma seçenekleri", k["satin_alma_arama"])
        c2.write(k.get("aciklama", ""))
        c2.info(f"Neden sana uygun: {k.get('neden','')}")
        c2.caption(f"Ilgili konular: {', '.join(k.get('maarif', []))} | oneri puani: {k.get('onerilme_puani')}")
db.close()
