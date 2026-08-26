class ApiConfig {
  // Fiziksel cihaz: bilgisayarın IP'sini yaz (örn: 192.168.1.166)
  // Render üzerinde barındırılan backend (telefon internete bağlıysa her yerden çalışır)
  static const String baseUrl = 'https://fast-oo6w.onrender.com';

  // Health
  static const String health = '$baseUrl/api/health';

  // Ülke/Şehir
  static const String ulkeler = '$baseUrl/api/ulkeler';
  static const String geocode = '$baseUrl/api/geocode';
  static const String sehirBilgi = '$baseUrl/api/sehir_bilgi';
  static const String sehirGorsel = '$baseUrl/api/sehir_gorsel';

  // Analiz
  static const String analizEs = '$baseUrl/api/analiz/es_sevgili';
  static const String analizEsDetayli = '$baseUrl/api/analiz/es_sevgili/detayli';
  static const String analizEb = '$baseUrl/api/analiz/ebeveyn_cocuk';
  static const String analizEbDetayli = '$baseUrl/api/analiz/ebeveyn_cocuk/detayli';
  static const String analizPy = '$baseUrl/api/analiz/potansiyel_yetenek';
  static const String analizNatal = '$baseUrl/api/analiz/bireysel_natal';

  // Simülasyon
  static const String simulasyonRadar = '$baseUrl/api/simulasyon/radar';
  static const String simulasyonNatalRadar = '$baseUrl/api/simulasyon/natal_radar';
  static const String simulasyonAlternatif = '$baseUrl/api/simulasyon/alternatif';

  // Astrokartografi
  static const String astrokartografi = '$baseUrl/api/astrokartografi';
  static const String acgHarita = '$baseUrl/api/astrocartography/harita';

  // Görsel / PDF
  static const String gorselBase = '$baseUrl/api/gorsel';
  static const String pdfBase = '$baseUrl/api/pdf';

  // Ödeme
  static const String paymentCheckout = '$baseUrl/api/payment/create-checkout';
  static const String paymentVerify = '$baseUrl/api/payment/verify';

  // E-posta
  static const String sendPdfEmail = '$baseUrl/api/email/send-pdf';

  // İstatistik
  static const String stats = '$baseUrl/api/stats';

  static const Duration timeout = Duration(seconds: 60);
  static const Duration longTimeout = Duration(seconds: 120);
}
