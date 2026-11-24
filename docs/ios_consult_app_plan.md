# iOS Danışmanlık Sürümü — Plan ve Kabul Notları

Amaç: App Store'da **astroloji içerik uygulaması** olarak değil, **gerçek bir uzmandan
24 saat içinde yazılı danışmanlık** hizmeti olarak listelenmek. Gerekçe:
`docs/ios_app_store_rekabet_analizi.md` (4.3(b) reddi ve pazar taraması).

Android sürümü ve Play **+85** numaralı AAB bu çalışmadan **etkilenmez**:
`pubspec.yaml` sürümü değiştirilmedi, ayrı giriş noktası (`lib/main_consult.dart`)
kullanılıyor.

## 1. Kapsam

### Giren ekranlar
- Dil seçimi (`LanguageIntroScreen`)
- Giriş / kayıt (`AuthScreen`, Google/Facebook gizli)
- Danışmanlık ana ekranı (`ConsultHomeScreen`)
- Soru formu, ödeme, cevaplar (`AstroConsultScreen`)
- Hesap: dil, tema, çıkış, hesap silme, gizlilik/şartlar/destek (`ConsultAccountScreen`)

### Bilinçli olarak girmeyenler
- Günlük burç, gökyüzü takvimi, ay fazı ekranları
- Doğum haritası çizimi/arşivi, sinastri, horary, astrokartografi, PDF mağazası
- Sosyal akış, reels, DM, hikâye

Gerekçe: Apple 4.3(b) kararında "astroloji/burç içeriği" tekrarını işaret etti.
Danışmanlık akışı dışındaki içerik ekranları bu sürümde yok.

## 2. Derleme

```powershell
flutter build ipa -t lib/main_consult.dart `
  --dart-define=SUPABASE_URL=... `
  --dart-define=SUPABASE_ANON_KEY=... `
  --dart-define=REVENUECAT_API_KEY_IOS=...
```

- iOS derlemesi **macOS** gerektirir (Codemagic veya Mac).
- Android/Kotlin tarafında değişiklik yok; mevcut AAB geçerli.
- Sürüm: `pubspec.yaml` `1.0.18+85` korunur. App Store `CFBundleVersion`
  Play'den bağımsızdır; ilk iOS yüklemesi için 85 uygundur.

## 3. App Store Connect hazırlığı

1. **Uygulama kaydı**: Mevcut (reddedilen) kayıt kullanılır; yeni bundle ID açılmaz.
2. **Uygulama adı**: "Holavon — Uzman Danışmanlık" gibi hizmet odaklı ad.
   Alt başlık: "24 saatte yazılı uzman cevabı" (burç/horoscope kelimesi yok).
3. **Kategori**: Lifestyle. İkincil kategori eklenmez.
4. **IAP**: Consumable ürün `sor_tek`, fiyat 2.399,99 TL.
5. **RevenueCat**: iOS uygulaması eklenir, `sor_tek` ürünü aynı offering'e bağlanır;
   iOS public SDK key `REVENUECAT_API_KEY_IOS` olarak verilir.
6. **Gizlilik**: veri toplama beyanı (e-posta, doğum bilgisi, satın alma).
7. **Hesap silme**: uygulama içinde mevcut (Apple 5.1.1(v)).
8. **Giriş**: Google/Facebook bu sürümde kapalı; Apple 4.8 kapsamı dışında kalır.
   (İleride sosyal giriş açılırsa Sign in with Apple zorunlu olur.)

## 4. Ödeme doğrulama

- İstemci: `RevenueCatService.purchaseConsumableWithTransaction('sor_tek')`
  (iOS'ta da `nonSubscriptionTransactions` döner).
- Sunucu: `POST /api/astro/verify-question-payment` → RevenueCat abone kaydı →
  `non_subscriptions.sor_tek` içinde işlem aranır.
- **Güncelleme**: store filtresi artık `app_store`/`appstore` değerlerini de kabul
  ediyor (`render-deploy/backend/main.py`). Bu değişiklik Render'a deploy edilmeden
  iOS ödemesi doğrulanamaz.

## 5. Apple'a verilecek kanıt seti

1. Ekran kaydı: giriş → soru → ödeme → 24 saat → yazılı cevap + PDF.
2. Uzman profili: Fatih Asartepe, özgeçmiş, uzmanlık alanı.
3. Hizmet taahhüdü: 24 saat SLA, cevap gelmezse otomatik iade.
4. Üç dilde hizmet (tr/en/es).
5. Son teslim süreleri / tamamlanan danışmanlık sayısı (panelden).
6. Bu klasördeki rekabet analizi: asenkron yazılı danışmanlık + iade + PDF
   kombinasyonunun App Store'da bulunmadığı.

## 6. Review Notes taslağı (İngilizce)

> Holavon is not a horoscope app. It is a one-to-one consultation service with a
> single, identity-verified practitioner. The user submits one question with
> birth details, pays once (consumable IAP), and receives a written answer plus
> a PDF consultation file within 24 hours. If the answer does not arrive in 24
> hours, the purchase is refunded automatically. The app contains no daily
> horoscopes, no auto-generated reports, no social feed and no chart-generation
> tools; those live only in our separate Android product. The App Store build is
> limited to the consultation workflow: expert profile → question → payment →
> written answer + PDF → archive.

## 7. Riskler

- Apple aynı kategori gerekçesiyle yine reddedebilir. Bu durumda tekrar denemek
  yerine web/PWA yolu izlenir (Apple'ın kendi önerisi).
- iOS derlemesi ve IAP testleri macOS/StoreKit gerektirir; bu makinede yapılamaz.
- `sor_tek` iOS ürünü App Store Connect'te "Ready to Submit" olmadan satın alma
  testi yapılamaz.
