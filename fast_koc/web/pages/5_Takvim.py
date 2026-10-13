"""5-Takvim: 2026-27 TG denemeleri + erken uyari."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from datetime import date
import streamlit as st
from backend.database import SessionLocal, init_db
from backend.models import Profile, DenemeTakvim
from backend.engine import mufredat as muf
from backend.services.takvim_seed import takvim_seed_yukle

init_db()
db = SessionLocal()
takvim_seed_yukle(db)
st.title("🗓️ Deneme Takvimi (2026-27)")
oid = st.session_state.get("ogrenci_id")
segment = None
if oid:
    pr = db.get(Profile, oid)
    segment = muf.coz(pr.segment) if pr else None
    st.info(f"Segmentin: {muf.etiket_of(segment)} — asagida sana uygun denemeler.")
q = db.query(DenemeTakvim).order_by(DenemeTakvim.tarih)
if segment:
    q = q.filter(DenemeTakvim.segment.in_(muf.takvim_eslesme(segment)))
bugun = date.today()
for d in q.all():
    kalan = (d.tarih - bugun).days
    renk = "🔴" if 0 <= kalan <= (d.erken_uyari_gun or 7) else ("⚪" if kalan < 0 else "🟢")
    with st.container(border=True):
        st.write(f"{renk} **{d.ad}** ({d.yayin})")
        bitis = getattr(d, "bitis", None)
        aralik = f"{d.tarih} – {bitis}" if bitis and bitis != d.tarih else str(d.tarih)
        st.write(f"Tarih: {aralik} | kalan {kalan} gun | basvuru son: {d.basvuru_son or '-'}")
        dogrulama = getattr(d, "dogrulama_durumu", "") or ""
        kaynak = getattr(d, "kaynak_url", "") or "-"
        if dogrulama.startswith("dogrulandi"):
            st.caption("✅ MEB resmi takvim")
        elif dogrulama.startswith("duyuru"):
            st.caption("📌 Yayınevi duyurusu (ikincil derleme — kayıt öncesi teyit edin)")
        else:
            st.caption(f"⚠️ Taslak tarih — teyit gerekli ({dogrulama or 'taslak'})")
        if kaynak and kaynak != "-":
            st.link_button("🔗 Yayıncı duyurusu", kaynak)
        if 0 <= kalan <= (d.erken_uyari_gun or 7):
            st.warning(f"Erken uyari: {kalan} gun kaldi! Konu tekrar + uyku duzenini simdiden kur.")
db.close()
