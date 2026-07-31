# FAST Backend — Render Deploy Paketi

Bu klasör, FAST backend'ini **Render** platformuna yayınlamak için hazırlanmış eksiksiz pakettir.
Telefon uygulaması bilgisayara bağlı olmadan bu sunucuya bağlanacaktır.

## İçerik

- `backend/main.py` — FastAPI uygulaması
- `core/` — FBST astroloji motoru (engine, data, utils)
- `dejavu-sans/` — PDF raporları için fontlar
- `ephe/` — Swiss Ephemeris asteroid dosyaları
- `cities_db.json`, `core/cities_db.json` — şehir veritabanı
- `FBST_*.py`, `fbst_*.py`, `ARAP_EBEVEYN_DICTS.py` — yorum sözlükleri
- `kapak1.png`, `Asartepe_Kapak.pdf` — PDF kapak görselleri
- `requirements.txt` — Python bağımlılıkları
- `render.yaml` — Render yapılandırması (Blueprint)

## Yayınlama Adımları (tarayıcı ile, git kurulumu gerekmez)

### 1. GitHub'a repo yükle
1. https://github.com adresine girip hesabınızla oturum açın (yoksa ücretsiz kaydolun)
2. Sağ üstten **+ → New repository**
   - Name: `fbst-backend`
   - Public olarak bırakın (ücretsiz)
   - **Create repository**'ye tıklayın
3. Açılan sayfada **"uploading an existing file"** bağlantısına tıklayın
4. Bu `render-deploy` klasöründeki **tüm dosyaları ve klasörleri** sürükleyip bırakın
   (içerideki `backend`, `core`, `dejavu-sans`, `ephe` klasörleri dahil)
5. **Commit changes** butonuna basın

### 2. Render'da servisi aç
1. https://render.com adresinde ücretsiz hesap açın (GitHub ile bağlanın)
2. **New + → Blueprint** veya **New + → Web Service** seçin
   - Web Service seçerseniz: GitHub reposunu (`fbst-backend`) bağlayın
3. Ayarlar (Blueprint seçilmediyse elle girin):
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app_fast --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. **Deploy** butonuna basın, ilk build 5-10 dakika sürebilir

### 3. Çalıştığını doğrula
Deploy tamamlanınca size şuna benzeyen bir adres verilir:
```
https://fbst-api.onrender.com
```
Tarayıcıda şu sayfayı açın → `https://fbst-api.onrender.com/api/health`
`{"status": "ok", "version": "4.0"}` dönerse her şey çalışıyor demektir.

### 4. Telefon uygulamasını güncelle
Flutter projesinde `lib/config/api_config.dart` dosyasındaki:
```dart
static const String baseUrl = 'http://192.168.1.102:8000';
```
satırını:
```dart
static const String baseUrl = 'https://fbst-api.onrender.com';
```
yapın, sonra APK'yı yeniden derleyin.

## Notlar

- **Ücretsiz plan:** 15 dakika istek gelmezse sunucu uykuya geçer; ilk istek ~30-60 saniye sürer. Kalıcı olması için Starter planı ($7/ay) kullanılabilir.
- Üretilen görsel/PDF dosyaları her istekte yeniden oluşturulur; kalıcı depolama gerekmez.
- Stripe ödeme anahtarları yoksa ödeme uçları yer tutucu ile çalışır (hata mesajı döner).
