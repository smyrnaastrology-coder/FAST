# Play Store — Satışa Hazırlık Checklist (FAST v4.3)

## 1. AAB
- Dosya: `fast_mobile/FAST_v4_3.aab` (68.1 MB, `com.fastastrology.fast`, version 1.0.0+1)
- Yükle: Play Console > Uygulamanız > Üretim > Yeni sürüm oluştur > AAB yükle
- Not: `flutter build appbundle` ile üretildi, `fbst-release.jks` ile imzalı

## 2. Ürünler (Para kazanma > Ürünler)

### 2.1 Abonelikler (Subscriptions)
| Ürün ID | Ad (TR) | Ad (EN) | Ad (ES) | Fiyat (baz) | Açıklama |
|---------|---------|---------|---------|-------------|----------|
| `sub_daily` | Aylık Canlı Rehber | Monthly Live Guide | Guía Mensual en Vivo | $7.99/ay | Her gün 08:00 Minor Progress push + kriz uyarısı + haftalık özet + canlı 21 yıl tüneli |
| `sub_daily_yearly` | Yıllık Canlı Rehber | Yearly Live Guide | Guía Anual en Vivo | $49.99/yıl | Aylığın yıllık indirimlisi (%38) |

Play Console'da: Abonelik oluştur > Faturalandırma dönemi 1 ay / 1 yıl > Ücretsiz deneme KAPALI (ilk PDF zaten ücretsiz) > Bölgesel fiyat: Play otomatik LatAm indirimi açık bırak.

### 2.2 Tek Seferlik (In-app products)
| Ürün ID | Tip | Fiyat | Açıklama |
|---------|-----|-------|----------|
| `pdf_single` | Yönetilen ürün (managed) | $19.99 | 60-70 sayfalık kitap (Aşk/Anne-Çocuk/Natal/Potansiyel ayrı çağrıda tip parametresi ile) — ilk hak ücretsiz (backend `free_pdf_used` kontrolü) |

> **RevenueCat eşlemesi:** Play ürün ID'leri RevenueCat dashboard'da aynı ID ile Entitlement `premium` altına ekle. Webhook: `https://fbst-api.onrender.com/api/billing/webhook` + `REVENUECAT_WEBHOOK_SECRET` env.

## 3. Mağaza Listesi

### Kısa açıklama (80 karakter)
- TR: FAST — 21 yıllık kadersel döngü, sinastri ve şehir uyumu
- EN: FAST — 21-year karmic cycle, synastry & city compatibility
- ES: FAST — Ciclo kármico de 21 años, sinastría y compatibilidad de ciudades

### Uzun açıklama (örnek ES - EN/TR benzer)
```
Técnica de Sinastría Fatih Asartepe (FAST) — tu carta relacional de 21 años.
• Carta de pareja, padre-hijo, natal y potencial
• 60-70 páginas de informe libro (PDF)
• Flujo diario 6 meses + Flujo Celeste 21 años
• Puntos árabes, sellos estelares, astrocartografía
Primer informe GRATIS. Suscripción: guía diaria en vivo cada mañana.
```

### Grafikler
- İkon: 512x512 (mevcut `assets/logo.png`)
- Özellik grafiği: 1024x500
- Ekran görüntüleri: en az 4 adet (telefon) — Landing > Form > Analiz > PDF (TR/EN/ES ayrı yükle)

## 4. Ülke Dağıtımı
- Play Console > Üretim > Ülkeler > **Türkiye PASİF**, diğer tüm ülkeler AKTİF (global TR hariç stratejisi)
- Backend `GLOBAL_EXCLUDE_TR=1` env açık olmalı

## 5. Veri Güvenliği & İçerik
- Veri güvenliği formu: Konum (şehir), Doğum tarihi, E-posta (auth) topluyor → şifreli aktarım evet, paylaşım hayır
- Gizlilik politikası URL: `https://.../privacy` (ekle, yoksa oluştur)
- Hedef kitle: 18+ , İçerik derecelendirmesi: IARC anketi (astroloji = simüle kumar değil, genel izleyici)
- Şifreleme beyanı: Evet (HTTPS)

## 6. Test
- Kapalı test kanalı: `testers@...` listesi ekle > AAB yükle > lisanslı test kullanıcısı ile gerçek kart olmadan satın alma testi (Google Play Billing test)
- RevenueCat webhook log: Render log'da `upsert_subscription` görülmeli
- FCM: `google-services.json` zaten `android/app/` içinde, bildirim izni isteği `main.dart`'ta

## 7. App Store (iOS) Notu
- `flutter build ipa` sadece Mac+Xcode ile. Bundle ID aynı `com.fastastrology.fast`, Apple Developer $99/yıl, App Store Connect'de ayrı kayıt. Backend aynı kalır.

## 8. Sonraki Komut
- Play'e yüklemeden önce: `flutter build appbundle` zaten hazır, sürüm kodunu artır (+2) için `pubspec.yaml` version `1.0.0+2` yap.
