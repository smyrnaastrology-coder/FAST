# Holavon Horary — soru kredisi

Horary'de tek bir cevap modeli vardır. Abonelik kademesine göre farklı cevap
kalitesi satılmaz; kullanıcı yalnızca **kaç soru sorabileceğini** satın alır.

## İki ayrı bakiye

| Bakiye | Kural | Sıfırlanır mı? |
|---|---|---|
| Günlük / ücretsiz hak | Ücretsiz kullanıcı toplam 3 soru; Pro günde 3 soru | Ücretsiz: hayır. Pro: 00:00 UTC |
| Satın alınmış kredi | Her soru 1 kredi | Hayır, süresiz |

Soru sorulduğunda **önce günlük/ücretsiz hak**, o bittiğinde **satın alınmış
kredi** harcanır. Pro abonelik bitse bile satın alınmış krediler hesapta kalır.

## Ürünler

| Ürün ID | Kredi | Başlangıç fiyatı |
|---|---|---|
| `horary_credits_5` | 5 | ₺69 |
| `horary_credits_15` | 15 | ₺169 |
| `horary_credits_40` | 40 | ₺399 |

Ürün ID'leri üç yerde aynı olmalıdır:

1. `horary_oracle/api.py` → `HORARY_CREDIT_PACKS`
2. `fast_mobile/flutter_app/lib/services/horary_service.dart` → `HoraryCreditPack.all`
3. Play Console / RevenueCat ürünleri (tip: **Consumable**)

Fiyat etiketi uygulamada RevenueCat'ten gelir; `price_label` yalnızca yedektir.

## Akış

1. Uygulama `POST /api/holavon/credits/sync` çağırır (Supabase oturumu ile).
2. Sunucu RevenueCat REST'ten `subscriber.non_subscriptions` kayıtlarını okur.
3. Her satın alma `transaction_id` ile **idempotent** olarak deftere yazılır.
4. Aynı işlem tekrar gelirse kredi ikinci kez eklenmez.
5. RevenueCat webhook'u (`POST /api/holavon/credits/webhook`) uygulama kapalıyken
   de krediyi hesaba işler.

## Sunucu uçları

- `GET /api/holavon/quota` → `remaining`, `limit`, `credits`, `available`,
  `reset_at`, `credit_packs`
- `POST /api/holavon/credits/sync` → oturum sahibinin eksik satın alımlarını işler
- `POST /api/holavon/credits/webhook` → RevenueCat webhook (paylaşılan sır)
- `POST /api/holavon/credits/grant` → yönetici / sunucudan sunucuya grant

## Ortam değişkenleri

| Değişken | Amaç |
|---|---|
| `HORARY_DATABASE_URL` | Kredi defteri ve kota tabloları |
| `REVENUECAT_API_SECRET` | Abonelik ve consumable satın alma doğrulaması |
| `HOLAVON_CREDIT_WEBHOOK_SECRET` | Webhook/grant uçlarının paylaşılan sırrı |
| `HOLAVON_QUOTA_EXPERIMENTAL=true` | Holavon kota uçlarını açar |

Webhook'u RevenueCat panelinde şu adrese bağla:

```
https://horary-oracle-api.onrender.com/api/holavon/credits/webhook
```

Authorization başlığı: `Bearer <HOLAVON_CREDIT_WEBHOOK_SECRET>`

## Veritabanı

`migrations/001_holavon_quota.sql` mevcut tabloları kurar.
`migrations/002_holavon_credits.sql` şunları ekler:

- `holavon_horary_quota.credit_balance`
- `holavon_horary_credit_ledger` (transaction_id birincil anahtar)
- rezervasyon `quota_type` alanına `credit` değeri
