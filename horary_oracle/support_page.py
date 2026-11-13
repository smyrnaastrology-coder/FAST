"""Public support page (App Store / Play require a reachable Support URL)."""

SUPPORT_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Holavon - Destek / Support</title>
<style>
  body { margin:0; background:#181026; color:#EDE7F6; font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif; line-height:1.65; }
  main { max-width:820px; margin:0 auto; padding:48px 22px 80px; }
  h1 { color:#C9A96E; font-size:28px; margin-bottom:4px; }
  h2 { color:#C9A96E; font-size:20px; margin-top:34px; }
  h3 { color:#E0C68A; font-size:16px; margin-top:22px; }
  p, li { color:#D6CEE8; font-size:15px; }
  a { color:#E0C68A; }
  .meta { color:#9C92B4; font-size:13px; }
  hr { border:0; border-top:1px solid #463262; margin:44px 0; }
</style>
</head>
<body>
<main>

<h1>Holavon — Destek</h1>
<p class="meta">Son güncelleme: 13 Kasım 2026</p>

<p>Holavon: Horary Oracle ile ilgili her konuda bize yazabilirsin:
<a href="mailto:smyrnaastrology@gmail.com">smyrnaastrology@gmail.com</a>. Genellikle 1-2 iş günü içinde yanıt veriyoruz.</p>

<h2>Sık sorulanlar</h2>

<h3>Krediler nasıl çalışır?</h3>
<p>Her horary sorusu bir kredi harcar. Ücretsiz 3 deneme hakkın vardır. Pro üyeler her gün 3 soru sorabilir; günlük hakkın bittikten sonra satın aldığın krediler kullanılır. Satın alınan krediler süresiz geçerlidir.</p>

<h3>Satın aldığım kredi görünmüyor</h3>
<p>Uygulamada <strong>Kredi Al</strong> ekranını açıp <em>Satın alımları geri yükle</em> seçeneğini kullan. Sorun sürerse mağaza sipariş numarasıyla bize yaz.</p>

<h3>Aboneliği nasıl iptal ederim?</h3>
<p>iPhone: Ayarlar → Apple Kimliği → Abonelikler. Android: Play Store → Ödemeler ve abonelikler. İptal ettiğinde dönem sonuna kadar Pro hakların devam eder.</p>

<h3>Hesabımı nasıl silerim?</h3>
<p>Uygulamada <strong>Ayarlar → Hesabı sil</strong> yolunu izle. Hesabın, soruların ve sosyal içeriklerin kaldırılır.</p>

<h3>Yorumlar neden kişisel tavsiye değil?</h3>
<p>Holavon eğlence ve kişisel farkındalık amacıyla horary haritası yorumu üretir; tıbbi, hukuki veya finansal tavsiye yerine geçmez.</p>

<hr>

<h1>Holavon — Support</h1>
<p class="meta">Last updated: 13 November 2026</p>

<p>For anything about Holavon: Horary Oracle, email us at
<a href="mailto:smyrnaastrology@gmail.com">smyrnaastrology@gmail.com</a>. We usually reply within 1-2 business days.</p>

<h2>FAQ</h2>

<h3>How do credits work?</h3>
<p>Each horary question costs one credit. You get 3 free questions to start. Pro members get 3 questions per day; after the daily allowance is used, purchased credits are spent. Purchased credits never expire.</p>

<h3>My purchase is missing</h3>
<p>Open the <strong>Get Credits</strong> screen in the app and use <em>Restore purchases</em>. If it still does not appear, email us with your store order number.</p>

<h3>How do I cancel my subscription?</h3>
<p>iOS: Settings → Apple ID → Subscriptions. Android: Play Store → Payments and subscriptions. Pro stays active until the end of the paid period.</p>

<h3>How do I delete my account?</h3>
<p>In the app go to <strong>Settings → Delete account</strong>. Your account, questions and social content are removed.</p>

<h3>Is a reading personal advice?</h3>
<p>Holavon produces horary chart readings for entertainment and self-reflection. They are not medical, legal or financial advice.</p>

</main>
</body>
</html>"""
