# FAST Satış Politikası — Teknik Spec v1 (TR hariç Global)

## 1. Hedef
- TR hariç global dağıtım (Store + IP)
- PDF (kitap) ve Abonelik ayrı ürün
- İlk PDF ücretsiz (suistimal korumalı)
- Günlük bildirim abonelikte canlı değer

## 2. Ürünler
| Ürün | Tip | Fiyat (global ortalama) | Açıklama |
|------|-----|------------------------|----------|
| `pdf_single` | One-time (non-consumable) | $19.99 / adet (4 mod ayrı) | 60-70 sayfa kitap, o anın gökyüzü snapshot |
| `sub_daily` Monthly | Subscription | $7.99/ay | Minor Progress günlük push + kriz uyarısı + haftalık özet + canlı 21yıl tüneli + aylık 1 sayfa ek |
| `sub_daily_yearly` | Subscription | $49.99/yıl | Aylığın yıllık indirimlisi |
| Bundle | Promo | $24.99 | PDF + 1 ay abonelik (opsiyonel) |

Regional: Liste $19.99/$7.99, Play otomatik LatAm indirimi (~30%).

## 3. Dağıtım
- Play Console: Türkiye pasif, diğer tüm ülkeler aktif.
- Backend IP gate: `CF-IPCountry` / `X-Forwarded-For` -> TR ise 403 (TR paketine yönlendirme mesajı).

## 4. Entitlement Model
```
free_pdf_used(uid, device_token_hash, ip_hash, used_at)
subscriptions(uid, product_id, expiry, status, provider, receipt)
```
- RevenueCat (önerilen) veya Google Play Developer API doğrulaması.
- Her istekte `Authorization: Bearer <Firebase_ID_Token>` + `X-Device-Token` header.

## 5. Akışlar
### İlk PDF Ücretsiz
1. `POST /api/pdf/free` -> uid + device token hash kontrol -> `free_pdf_used` yoksa üret, varsa 402 `free_already_used`.
### Satın Alma
1. Client RevenueCat purchase -> webhook `POST /api/billing/webhook` -> subscriptions upsert.
### Günlük Bildirim
- Cron: `render-deploy/cron_daily.py` 00:00 UTC, aktif aboneleri tara -> her biri için `tarih=bugün` minor progress hesapla -> FCM `send_to_token`.
### Astrokartografi Kilidi
- PDF: her PDF üretiminde dahil (satın alan zaten görür).
- Browser (GET /api/astrocartography): `hasActiveSubscription` yoksa `{"locked":true,"preview":blurred3}` dön. Var ise tam data.

## 6. Güvenlik
- API: JWT, rate limit 20 req/dk/IP (slowapi), CORS whitelist (paket adı).
- APK: R8 + obfuscation, Play Integrity API, cert pinning.
- PDF: footer + invisible watermark `session_id|uid`.

## 7. Flutter Paywall
- `if (hasPdf || isSubscribed)` -> tam harita (eski OR, şimdi ayrı kilit için: hasPdf sadece PDF sayfasında, isSubscribed sadece browser haritasında).
- Free kullanıcı: blur + CTA `PDF $19.99` / `Abone ol $7.99`.

## 8. Sonraki Dil
- v4.2 release (mevcut ES), v4.3 PT+HI aynı şablonda.

## 9. Uygulama Sırası
1. IP gate middleware
2. DB tabloları + /api/billing/webhook + /api/pdf/free
3. Astrokartografi gate
4. FCM cron iskeleti
5. Rate limit + watermark
