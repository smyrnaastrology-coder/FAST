# Fast Koç — Mobil (Flutter) (v0.4: proje kurulu, 7 ekran bağlı)

## Durum
- `flutter create` yapıldı (com.fastkoc, fast_koc). `flutter analyze lib` temiz, `flutter test` yeşil.
- Ekranlar: Profil / Sınav (fl_chart) / Ödev / Kitap (kapak) / Takvim (link) / Günlük / Karne+Bildirim+FCM.
- API istemcisi: `lib/api_client.dart` (11 endpoint) + `lib/models.dart`.

## Çalıştırma
```powershell
cd fast_koc/mobile
flutter run --dart-define=FASTKOC_API_URL=https://fastkoc-api.onrender.com
# yerelde emulator: varsayılan http://10.0.2.2:8090
```

Bağımsız mini-uygulama önerilir (`fast_koc/mobile/`), mevcut FBST Flutter'ına gömülmez.

## Ekranlar (sıra + API)
1. **Profil** — `POST /api/profil`, `GET /api/profil/{id}` (rol: öğrenci/veli/koç)
2. **Sınavlarım** — `POST /api/sinav`, `GET /api/analiz/{id}` (D/Y/B formu, konu grafiği: fl_chart)
3. **Ödevlerim** — `GET /api/odev/haftalik/{id}`, `POST /api/odev/onay`
4. **Kitaplarım** — `GET /api/kitap/oner/{id}` (kapak: cached_network_image)
5. **Takvim** — `GET /api/takvim?segment=` (🔴 erken uyarı rozeti, kaynak linki url_launcher)
6. **Günlük+Rapor** — `POST /api/gunluk`, grafikler
7. **Karne** — `GET /api/karne/{id}` (PDF: open_file + share)
8. **Koç Paneli** — `GET /api/koc/{id}/ogrenciler` (veli/koç rolü, pro rozeti: `GET /api/plan/{id}`)
9. **Bildirimler** — `GET /api/bildirim/{id}` (kanal rozeti: uygulama-içi/push)

## Push (FCM) adımları
1. `flutter pub add firebase_core firebase_messaging http cached_network_image fl_chart`
2. Firebase Console → paket `com.fastkoc.app` → `google-services.json` / `GoogleService-Info.plist`
3. Açılışta token alıp `POST /api/cihaz` ile kaydet (`mobile/lib/api_client.dart:cihazKaydet`)
4. Arka plan handler: `FirebaseMessaging.onBackgroundMessage` → yerel bildirim göster
5. Sunucu: `FCM_SERVER_KEY` env + cron `python -m backend.jobs.gunluk_push` (21:30)

## Auth
- Supabase kullanılıyorsa: login sonrası JWT'yi `FastKocApi(token: jwt)` ile geç.
- Sunucu `AUTH_ZORUNLU=false` iken tokensız çalışır (MVP); üretimde `true` yap.

## Derleme (ilk kurulum zaten yapıldı)
```powershell
cd fast_koc/mobile
flutter pub get
flutter run
```

## Test
- API sözleşme testi: `mobile/test/api_sozlesme.md` (her endpoint için beklenen şema).
- Manuel: profil oluştur → sınav gir → ödev üret → günlük gir → karne indir → push kuyruğu.
