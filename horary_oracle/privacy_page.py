"""Static privacy policy page (App Store / Play require a public URL)."""

PRIVACY_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Holavon - Gizlilik Politikasi / Privacy Policy</title>
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

<h1>Holavon — Gizlilik Politikası</h1>
<p class="meta">Son güncelleme: 13 Kasım 2026</p>

<p>Bu politika, <strong>Holavon: Horary Oracle</strong> mobil uygulamasında (iOS ve Android) kişisel verilerin nasıl işlendiğini açıklar. Veri sorumlusu Fatih Asartepe'dir. İletişim: <a href="mailto:smyrnaastrology@gmail.com">smyrnaastrology@gmail.com</a>.</p>

<h2>1. İşlediğimiz veriler</h2>
<ul>
  <li><strong>Hesap bilgileri:</strong> e-posta adresi, şifre (Supabase Auth tarafından hash'lenerek saklanır), görünen ad ve kullanıcı adı.</li>
  <li><strong>Doğum bilgileri:</strong> doğum tarihi, saati, şehri/ülkesi ve koordinatları — natal harita ve kişisel yorumlar için.</li>
  <li><strong>Horary soruları ve yanıtları:</strong> yazdığınız veya cihazınızda sesle yazıya çevirdiğiniz sorular ve üretilen yorumlar. Ses kaydı sunucuya gönderilmez; dikte cihazda yapılır.</li>
  <li><strong>Sosyal içerik:</strong> profil bilgileri, gönderiler, yorumlar, beğeniler ve mesajlar.</li>
  <li><strong>Satın alma bilgileri:</strong> abonelik/kredi durumu. Ödeme kartı bilgileri Apple, Google veya RevenueCat tarafından işlenir; biz kart bilgisi görmeyiz.</li>
  <li><strong>Cihaz ve tanılama verileri:</strong> bildirim jetonu, cihaz türü, uygulama sürümü ve hata kayıtları.</li>
</ul>

<h2>2. Kullanım amaçları</h2>
<ul>
  <li>Hesabınızı oluşturmak ve oturum açmanızı sağlamak.</li>
  <li>Horary haritası ve yorumu üretmek, natal analizler sunmak.</li>
  <li>Kredi ve abonelik haklarınızı doğrulamak.</li>
  <li>Sosyal özellikleri ve bildirimleri çalıştırmak.</li>
  <li>Hataları gidermek, güvenliği sağlamak ve yasal yükümlülükleri yerine getirmek.</li>
</ul>

<h2>3. Paylaşılan hizmet sağlayıcılar</h2>
<ul>
  <li><strong>Supabase</strong> — kimlik doğrulama, veritabanı ve dosya saklama.</li>
  <li><strong>OpenAI</strong> — horary yorumu üretmek için soru ve harita verisinin işlenmesi.</li>
  <li><strong>RevenueCat, Apple, Google</strong> — uygulama içi satın alma ve abonelik yönetimi.</li>
  <li><strong>Firebase (Google)</strong> — bildirim iletimi ve hata raporlama.</li>
</ul>
<p>Verileriniz reklam amacıyla satılmaz veya kiralanmaz.</p>

<h2>4. Saklama ve silme</h2>
<p>Veriler hesabınız aktif olduğu sürece saklanır. Hesabınızı uygulama içinden <strong>Ayarlar → Hesabı sil</strong> yolundan silebilirsiniz; silme talebiyle birlikte hesap verileriniz ve kişisel içerikleriniz kaldırılır. Yasal olarak saklanması gereken kayıtlar bu kapsam dışındadır.</p>

<h2>5. Haklarınız</h2>
<p>KVKK ve GDPR kapsamında verilerinize erişme, düzeltme, silme, işlemeye itiraz etme ve taşınabilirlik haklarına sahipsiniz. Talepleriniz için <a href="mailto:smyrnaastrology@gmail.com">smyrnaastrology@gmail.com</a> adresine yazabilirsiniz.</p>

<h2>6. Güvenlik ve çocuklar</h2>
<p>Veriler şifreli bağlantı (HTTPS) üzerinden iletilir ve erişim yetkileriyle korunur. Uygulama 13 yaşın altındaki çocuklara yönelik değildir; bu yaş grubundan bilerek veri toplamayız.</p>

<h2>7. Değişiklikler</h2>
<p>Bu politika güncellendiğinde bu sayfada yayımlanır ve “son güncelleme” tarihi değişir.</p>

<hr>

<h1>Holavon — Privacy Policy</h1>
<p class="meta">Last updated: 13 November 2026</p>

<p>This policy explains how <strong>Holavon: Horary Oracle</strong> (iOS and Android) processes personal data. The data controller is Fatih Asartepe. Contact: <a href="mailto:smyrnaastrology@gmail.com">smyrnaastrology@gmail.com</a>.</p>

<h2>1. Data we process</h2>
<ul>
  <li><strong>Account data:</strong> email address, password (hashed by Supabase Auth), display name and username.</li>
  <li><strong>Birth data:</strong> date, time, city/country and coordinates — used for natal charts and personal readings.</li>
  <li><strong>Horary questions and answers:</strong> questions you type or dictate on-device, and the generated readings. Audio is not uploaded; dictation happens on your device.</li>
  <li><strong>Social content:</strong> profile details, posts, comments, likes and messages.</li>
  <li><strong>Purchase data:</strong> subscription and credit status. Payment card details are handled by Apple, Google or RevenueCat; we never see them.</li>
  <li><strong>Device and diagnostics:</strong> notification token, device type, app version and crash logs.</li>
</ul>

<h2>2. Why we use it</h2>
<ul>
  <li>To create your account and keep you signed in.</li>
  <li>To cast horary charts and generate readings, and to provide natal analyses.</li>
  <li>To verify credits and subscription entitlements.</li>
  <li>To run social features and notifications.</li>
  <li>To fix errors, keep the service secure and meet legal obligations.</li>
</ul>

<h2>3. Service providers</h2>
<ul>
  <li><strong>Supabase</strong> — authentication, database and file storage.</li>
  <li><strong>OpenAI</strong> — processing the question and chart data to generate horary readings.</li>
  <li><strong>RevenueCat, Apple, Google</strong> — in-app purchases and subscriptions.</li>
  <li><strong>Firebase (Google)</strong> — push delivery and crash reporting.</li>
</ul>
<p>We do not sell or rent your data for advertising.</p>

<h2>4. Retention and deletion</h2>
<p>Data is kept while your account is active. You can delete your account in the app via <strong>Settings → Delete account</strong>; your account data and personal content are then removed. Records we must keep by law are excluded.</p>

<h2>5. Your rights</h2>
<p>Under GDPR/KVKK you may access, correct, delete, object to processing and request portability of your data. Contact <a href="mailto:smyrnaastrology@gmail.com">smyrnaastrology@gmail.com</a>.</p>

<h2>6. Security and children</h2>
<p>Data is transmitted over HTTPS and protected by access controls. The app is not directed to children under 13 and we do not knowingly collect their data.</p>

<h2>7. Changes</h2>
<p>Updates are published on this page and the “last updated” date changes accordingly.</p>

</main>
</body>
</html>"""
