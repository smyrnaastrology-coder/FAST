"""7-Admin: JSON veri editoru (kitap / takvim / müfredat goruntuleme).

Guvenlik (MVP): kenar cubugu sifresi (FASTKOC_ADMIN_SIFRE env, varsayilan: fastkoc-admin).
Uretimde bu sayfa kapatilmali veya Supabase rollerine baglanmali.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ui
import streamlit as st

ui.setup("Admin — Veri Editörü", "🛠️")
ui.baslik("Admin — Veri Editörü", ikon="🛠️", alt="Kitap katalogu, deneme takvimi ve Maarif müfredatı JSON editörü.")
sifre = st.sidebar.text_input("Admin şifresi", type="password")
beklenen = os.environ.get("FASTKOC_ADMIN_SIFRE", "fastkoc-admin")
if sifre != beklenen:
    st.warning("Düzenlemek için admin şifresini girin (varsayılan: fastkoc-admin, env ile değiştirin).")
    st.stop()

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "backend", "data")
DOSYALAR = {
    "Kitap katalog": "kitap_katalog.json",
    "Deneme takvimi": "deneme_takvimi_2026_27.json",
    "Maarif müfredat": "maarif_mufredat.json",
}
secim = st.selectbox("Dosya", list(DOSYALAR.keys()))
yol = os.path.join(DATA, DOSYALAR[secim])
with open(yol, encoding="utf-8") as f:
    veri = json.load(f)

st.caption(f"{DOSYALAR[secim]} — düzenle, doğrula, kaydet. Bozuk JSON kaydedilmez.")
if secim == "Kitap katalog":
    st.dataframe([{"id": k["id"], "başlık": k["baslik"], "yayın": k.get("yayin"),
                   "tür": k.get("tur"), "seviye": k.get("seviye"),
                   "isbn": k.get("isbn"), "isbn_durum": k.get("isbn_durum", "dogrulanmadi")}
                  for k in veri["kitaplar"]], use_container_width=True)
elif secim == "Deneme takvimi":
    st.dataframe([{"id": d["id"], "ad": d["ad"], "tarih": d["tarih"],
                   "doğrulama": d.get("dogrulama_durumu", "taslak"),
                   "kaynak": d.get("kaynak_url", "-")}
                  for d in veri["denemeler"]], use_container_width=True)
else:
    st.json({k: f"{sum(len(v) for v in seg['dersler'].values())} konu" for k, seg in veri["segmentler"].items()})

ham = st.text_area("JSON", json.dumps(veri, ensure_ascii=False, indent=1), height=420)
c1, c2 = st.columns(2)
if c1.button("💾 Kaydet"):
    try:
        yeni = json.loads(ham)
        yedek = yol + ".bak"
        with open(yedek, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=1)
        with open(yol, "w", encoding="utf-8") as f:
            json.dump(yeni, f, ensure_ascii=False, indent=1)
        st.success(f"Kaydedildi (yedek: {os.path.basename(yedek)}). API yeniden başlatınca seed güncellenir.")
    except json.JSONDecodeError as e:
        st.error(f"JSON hatası, kaydedilmedi: {e}")
if c2.button("↩️ Yedeğe dön"):
    yedek = yol + ".bak"
    if os.path.exists(yedek):
        with open(yedek, encoding="utf-8") as f:
            geri = f.read()
        with open(yol, "w", encoding="utf-8") as f:
            f.write(geri)
        st.success("Yedekten geri yüklendi.")
    else:
        st.info("Yedek yok.")
