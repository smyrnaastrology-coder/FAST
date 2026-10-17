# AGENTS.md

## Release build kuralı (ÇOK ÖNEMLİ)

Android release AAB/APK **yalnızca** şu betikle üretilir:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\build_release.ps1
powershell -ExecutionPolicy Bypass -File .\tool\build_release.ps1 -Target apk
```

çalışma dizini: `fast_mobile\flutter_app`

**Neden:** Betik `--dart-define` ile `SUPABASE_URL`, `SUPABASE_ANON_KEY` ve
`REVENUECAT_API_KEY` değerlerini geçirir. Doğrudan `flutter build appbundle`
çalıştırılırsa bu değerler gömülmez; `supabaseEnabled` false olur ve
`landing_screen.dart` içindeki `if (!ap.enabled) return SizedBox.shrink();`
satırı nedeniyle giriş / Google-Facebook / profil / kayıtlı kişi arayüzü
**hiç çizilmez**. Kod sağlam görünür ama pakette bu ekranlar yoktur.

> Kural: `flutter build appbundle` / `flutter build apk` komutlarını
> release için **asla** doğrudan çalıştırma. Her zaman yukarıdaki betiği kullan.

Değerler `tool\supabase.local.ps1` ve `tool\revenuecat.local.ps1` içinde tutulur
ve git'e commit edilmez.

## Sürüm

`pubspec.yaml` içindeki `version: 1.0.X+Y` satırındaki `+Y` Play sürüm kodudur.
Her yeni Play yüklemesinde artırılır.
