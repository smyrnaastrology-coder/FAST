# Fast Koç 🚀

Maarif Modeli ile kişiye özel koçluk: sınav analizi → haftalık ödev → seviyeye göre kitap önerisi (kapaklı) → 2026-27 TG takvimi → günlük takip.

## Hızlı başlat (Windows)

```powershell
cd fast_koc
pip install -r requirements.txt
streamlit run web\Home.py
```

API (opsiyonel):

```powershell
cd fast_koc
uvicorn backend.main:app --reload --port 8090
```

## Yapı

- `backend/data/` — müfredat, kitap katalog, TG takvimi (JSON)
- `backend/engine/` — analiz / ödev / yorum motorları
- `backend/services/` — kitap (ISBN API), bildirim, seed
- `web/` — Streamlit MVP (6 sayfa)
- `docs/FAST_KOC_SPEC.md` — şartname
