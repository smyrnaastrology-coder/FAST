# Fast Koç — Canlıya Alma (Render)

## 1. Servisler (`render.yaml`)
- `fastkoc-api` — FastAPI (:8090 yerelde), health `/api/health`
- `fastkoc-web` — Streamlit, health `/_stcore/health`
- `fastkoc-gunluk-push` — cron 18:30 UTC (21:30 TSİ)

Blueprint ile kurulum: Render → New → Blueprint → repo + `fast_koc/render.yaml`.

## 2. Zorunlu env (üretim)
| Key | Değer |
|---|---|
| `FASTKOC_DATABASE_URL` | Postgres bağlantısı (Render Postgres önerilir) |
| `AUTH_ZORUNLU` | `true` |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret |
| `FASTKOC_ADMIN_SIFRE` | Güçlü şifre |
| `FCM_SERVER_KEY` | Push için |
| `STRIPE_SECRET_KEY` | Gerçek ödeme için (yoksa stub) |
| `FASTKOC_TUMU_MAARIF` | `false` (2026-27); 2027-28'de `true` |

## 3. Deploy öncesi kontrol
```powershell
cd fast_koc
python -m pytest tests/ -q
python -m backend.jobs.gunluk_push
```

## 4. Dönem geçişi (2027-28)
1. `FASTKOC_TUMU_MAARIF=true` yap → `YKS_ESKI` seçimden kalkar.
2. Mevcut `YKS_ESKI` öğrencileri `YKS_MAARIF`'e taşı (Admin onayı + duyuru).
3. `GET /api/segmentler` ile doğrula.

## 5. Notlar
- SQLite yalnızca yerelde; üretimde Postgres şart (çok kullanıcılı yazma).
- Cron ücretsiz planda uyuyabilir; kritik uyarılar için uygulama-içi bildirim yedeği durur.
- `.env.example` şablon; gerçek secret'lar repoya girmez.
