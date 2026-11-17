<#
    Build the browser version of Holavon using the same Flutter screens/assets.

    This is separate from the Android release script. It does not build an APK
    or AAB. The generated app is served by horary_oracle at /app/.

    Usage from fast_mobile/flutter_app:
      powershell -ExecutionPolicy Bypass -File .\tool\build_web.ps1

    Supabase values are read from the existing ignored local config and are
    embedded as the public Supabase URL/publishable key required by the client.
#>

$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

$local = Join-Path $PSScriptRoot 'supabase.local.ps1'
if (-not (Test-Path $local)) {
    throw "Missing $local. Create it with `$SupabaseUrl and `$SupabaseAnonKey."
}
. $local

if ([string]::IsNullOrWhiteSpace($SupabaseUrl) -or
    [string]::IsNullOrWhiteSpace($SupabaseAnonKey)) {
    throw 'Supabase URL and publishable/anon key are required for web login.'
}
if ($SupabaseAnonKey -like 'sb_secret_*') {
    throw 'A Supabase secret key must never be embedded in a browser build.'
}

$SupabaseUrl = $SupabaseUrl.TrimEnd('/') -replace '/rest/v1/?$', ''
$defines = @(
    "--dart-define=SUPABASE_URL=$SupabaseUrl"
    "--dart-define=SUPABASE_ANON_KEY=$SupabaseAnonKey"
)

flutter build web --release --base-href /app/ @defines
if ($LASTEXITCODE -ne 0) { throw 'Flutter web build failed.' }

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$destination = Join-Path $repoRoot 'horary_oracle\site\app'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item -Path (Join-Path (Get-Location) 'build\web\*') `
    -Destination $destination -Recurse -Force

Write-Host "Web app staged at $destination" -ForegroundColor Green
Write-Host 'Before enabling browser OAuth, allow https://holavon.com/app/ in Supabase Auth Redirect URLs.' -ForegroundColor Yellow
