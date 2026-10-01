<#
    Release AAB build - Supabase degerlerini DAIMA gecirir.

    Kullanim (flutter_app klasorunden):
        .\tool\build_release.ps1

    Neden bu betik var:
    lib/config/api_config.dart icindeki
        static const String supabaseUrl = String.fromEnvironment('SUPABASE_URL', defaultValue: '');
    degeri verilmezse supabaseEnabled false olur ve landing_screen.dart'deki
        if (!ap.enabled) return SizedBox.shrink();
    satiri giris/profil butonunu HIC cizmez. Yani uygulama "girisi olmayan"
    gorunur ama kod saglamdir. Bu, 2026-10'da Play yuklemesinde gecilmis bir
    hatadir; betik bunu tekrar onlemmek icin yazildi.

    Degerler tool\supabase.local.ps1 icinde tutulur ve git'e commit edilmez.
#>

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..   # flutter_app kokune gec

$local = Join-Path $PSScriptRoot 'supabase.local.ps1'
if (-not (Test-Path $local)) {
    Write-Host "HATA: $local bulunamadi." -ForegroundColor Red
    Write-Host "Olusturun: tool\supabase.local.ps1 icine `$SupabaseUrl ve `$SupabaseAnonKey yazin." -ForegroundColor Yellow
    Write-Host "Supabase Dashboard > Project Settings > Data API" -ForegroundColor Yellow
    exit 1
}

. $local

if ([string]::IsNullOrWhiteSpace($SupabaseUrl) -or [string]::IsNullOrWhiteSpace($SupabaseAnonKey)) {
    Write-Host "HATA: Supabase degerleri bos. tool\supabase.local.ps1 dosyasini duzenleyin." -ForegroundColor Red
    exit 1
}

# Yanlislikla secret key girilmesini engelle.
if ($SupabaseAnonKey -like 'sb_secret_*') {
    Write-Host "HATA: sb_secret_ (secret key) girilmis. Bu anahtar MOBIL PAKETE GIRMEZ." -ForegroundColor Red
    Write-Host "Publishable key kullanin: sb_publishable_... veya eski anon key." -ForegroundColor Yellow
    exit 1
}

# Sondaki /rest/v1/ gibi yollari soy - SDK kendisi ekler.
$SupabaseUrl = $SupabaseUrl.TrimEnd('/')
$SupabaseUrl = $SupabaseUrl -replace '/rest/v1/?$', ''

Write-Host "Supabase URL   : $SupabaseUrl" -ForegroundColor DarkGray
Write-Host "Publishable key: $($SupabaseAnonKey.Substring(0, [Math]::Min(22, $SupabaseAnonKey.Length)))..." -ForegroundColor DarkGray
Write-Host ""

flutter build appbundle --release `
    --dart-define="SUPABASE_URL=$SupabaseUrl" `
    --dart-define="SUPABASE_ANON_KEY=$SupabaseAnonKey"

if ($LASTEXITCODE -ne 0) { Write-Host "BUILD BASARISIZ" -ForegroundColor Red; exit $LASTEXITCODE }

$aab = 'build\app\outputs\bundle\release\app-release.aab'
if (Test-Path $aab) {
    $mb = [Math]::Round((Get-Item $aab).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Tamam: $aab ($mb MB)" -ForegroundColor Green
    Write-Host "Bu paket giris/profil/kayitli kisi ekranlarini ICERIR." -ForegroundColor Green
}
