# Fast Koç — Teknik Şartname (v0.4, Dönem Ayrımı)

Bağımsız uygulama. FBST monolitine dokunmaz; `fast_koc/` altında yaşar.

## Segmentler
- **LGS** (8. sınıf, 6 ders), **ARA_9_10_11** (9-10-11 ortak+alan), **YKS** (TYT+AYT, SAY/EA/SÖZ/DİL).
- Müfredat: `backend/data/maarif_mufredat.json` (Maarif Modeli 2024 özet; MEB dokümanıyla editörce genişletilir).

## Motorlar
- `engine/analiz_motoru.py`: D/Y/B → başarı%, kritik<%40 / gelişmeli<%70 / güçlü, öncelikli 3 konu, net (YKS D-Y/4, LGS ham D).
- `engine/odev_motoru.py`: kritik→konu anlatım 20-30, gelişmeli→soru bankası 30-50, güçlü→zor test; Pazar deneme günü; öncül konu önceliği.
- `engine/yorum_motoru.py`: günlük kıyas cümlesi + dönem trend yorumu.

## Kitaplar
- `backend/data/kitap_katalog.json` seed (16 kitap) + `services/kitap_servisi.py`:
  Google Books ISBN API → kapak/künye; yoksa Open Library cover; cache 30 gün.
- Kartta: kapak görseli, tür/seviye rozeti, kısa tanıtım, "neden uygun", ilgili Maarif kodları.
- Telif: tam içerik yok, kısa alıntı + satın alma linki.

## Takvim (v0.4: gerçek 2026-27 verisi)
- 22 MEBİ (12 YKS + 10 LGS, resmi + ücretsiz, `dogrulandi-meb-resmi`) + 21 yayınevi TG
  (Özdebir/3D/4K/Hız ve Renk/Supara, `duyuru-ikincil-kaynak`) + 2 ara-sınıf izleme (taslak).
- `4K-MAARIF-TYT` yalnızca `YKS_MAARIF` segmentine özeldir; diğer YKS satırları paylaşılır.
- Aralık desteği: `tarih` (başlangıç) + `bitis` kolonu; API ikisini de döner.

## Bildirim (sadece uygulama-içi)
- `services/bildirim_servisi.py`: gün-sonu hatırlatma + TG taraması; `bildirimler` tablosu + Rapor sayfasında inbox.
- Push (FCM) yok — Faz 3'e bırakıldı.

## API (FastAPI :8090)
- `GET /api/health`, `POST /api/profil`, `POST /api/sinav`, `GET /api/analiz/{id}`,
  `POST /api/gunluk`, `GET /api/odev/haftalik/{id}`, `POST /api/odev/onay`,
  `GET /api/kitap/oner/{id}`, `GET /api/takvim`, `GET /api/bildirim/{id}`,
  `GET /api/karne/{id}` (PDF bytes).

## Faz 2 ekleri
- PDF karne: `services/karne_pdf.py` (DejaVu font gömülü, kapak+özet+konu tablosu+grafikler+ödev+kitap+takvim, altlıklı).
  Web `8_Karne.py` + API `/api/karne/{id}`.
- Admin editör: `web/pages/7_Admin.py` (şifre: `FASTKOC_ADMIN_SIFRE`, varsayılan fastkoc-admin;
  JSON doğrula+kaydet+yedek `.bak`). Üretimde kapatılmalı veya role bağlanmalı.
- ISBN: `services/isbn_dogrulama.py` (`python -m backend.services.isbn_dogrulama [--canli]`,
  rapor `data/isbn_dogrulama_raporu.json`). Katalog v0.2.0: 16 ISBN checksum-geçerli
  **yer-tutucu** (`isbn_durum=yer-tutucu-dogrulanmadi`) + `satin_alma_arama` linki.
  Yayın öncesi editör gerçek ISBN girip `--canli` ile doğrulatmalı.
- Takvim: v0.2.0 her satırda `dogrulama_durumu` + `kaynak_url` (yayıncı sitesi);
  tümü `taslak-yayinci-teyidi-gerekir`. DB'ye `dogrulama_durumu/kaynak_url` kolonu eklendi
  (`_hafif_migrasyon` ile mevcut DB'ye ALTER). Seed mevcut satırları günceller.
- Test: `pytest fast_koc/tests` — 7 test (motor 3 + faz2 4).

## Web (Streamlit)
- `web/Home.py` + `pages/1_Profil … 6_Gunluk_Rapor`; tema lacivert `#14213D` + turuncu `#FCA311`.
- Çalıştırma: `cd fast_koc && streamlit run web/Home.py`.

## DB
- `backend/database.py` (SQLite MVP `fastkoc.db`, üretimde `FASTKOC_DATABASE_URL` ile Postgres),
  `backend/models.py` 7 tablo: profiles, sinav_sonuclar, gunluk_log, odevler, kitaplar, deneme_takvim, bildirimler.

## Test
- `pytest fast_koc/tests` — analiz motoru eşikleri, ödev 7 gün kuralı, kitap sıralama, takvim seed idempotency.

## Sonraki fazlar
- Faz 2: PDF karne (reportlab), admin JSON editörü, veli/koç rolü.
- Faz 3: Flutter taşıma, push, ödeme.

## Faz 3 ekleri (v0.3)
- Roller: `profiles.rol` (ogrenci/veli/koc/admin) + `baglantilar` tablosu;
  API `POST /api/baglanti`, `GET /api/koc/{id}/ogrenciler`; Web `9_Koc_Paneli.py`.
- Auth: `backend/auth.py` — Supabase JWT (HS256) + `FASTKOC_DEV_TOKEN` + anonim fallback.
  `GET /api/auth/me`; `AUTH_ZORUNLU=false` iken MVP kırılmaz, üretimde `true` yap.
- Push: `services/push_servisi.py` (FCM legacy; anahtar yoksa kuyrukta bekletir, offline güvenli),
  `cihazlar` tablosu + `POST /api/cihaz`, `POST /api/push/{id}`;
  zamanlayıcı `python -m backend.jobs.gunluk_push` (cron 21:30) + `mobile/README.md` FCM adımları.
- Ödeme: `services/odeme_servisi.py` (ucretsiz/pro); `STRIPE_SECRET_KEY` yoksa stub link,
  varsa gerçek checkout; `GET /api/plan/{id}`, `POST /api/odeme/checkout|aktif/{id}`;
  Web `10_Pro.py` (rozet + test aktivasyon + cihaz kaydı).
- Mobil iskelet: `mobile/lib/api_client.dart` (9 endpoint) + `mobile/lib/models.dart` +
  `mobile/README.md` (9 ekran + FCM + derleme) + `mobile/test/api_sozlesme.md`.
- Test: `pytest fast_koc/tests` — 25 test (motor 3 + faz2 4 + faz3 4 + mufredat 6 + takvim 2 + yeni 6).

## Yeni özellikler (v0.4)
- Optik hızlı giriş: `engine/optik.py` (anahtar+cevap metni → D/Y/B) + `11_Optik.py` + `POST /api/optik`.
- Veli SMS: `services/sms_servisi.py` (anahtar yoksa kuyruk, `kanal=sms`) + `POST /api/sms/{id}`.
- Yapay zekâ koç yorumu: `services/koc_yorumu.py` (`OPENAI_API_KEY` varsa LLM, yoksa şablon) + `GET /api/koc-yorum/{id}`.
