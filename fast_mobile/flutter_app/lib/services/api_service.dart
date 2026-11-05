import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/analysis_request.dart';
import 'billing_service.dart';

class ApiService {
  Future<Map<String, dynamic>> _post(
    String url,
    Map<String, dynamic> body, {
    Duration? timeout,
  }) async {
    final r = await http
        .post(
          Uri.parse(url),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(timeout ?? ApiConfig.timeout);
    if (r.statusCode == 200) return jsonDecode(r.body);
    String msg;
    try {
      final e = jsonDecode(r.body);
      msg = e['detail'] ?? r.body;
    } catch (_) {
      msg = r.body;
    }
    throw Exception(msg);
  }

  Future<Map<String, dynamic>> _get(String url, {Duration? timeout}) async {
    final r = await http
        .get(Uri.parse(url))
        .timeout(timeout ?? ApiConfig.timeout);
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('HTTP ${r.statusCode}');
  }

  Future<Map<String, dynamic>> getUlkelerRaw() => _get(ApiConfig.ulkeler);

  Future<Map<String, dynamic>> geocode(String sehir) =>
      _post(ApiConfig.geocode, {'arama': sehir});

  Future<Map<String, dynamic>> analizYap(AnalysisRequest req) {
    final url = switch (req.mod) {
      'es_sevgili' => ApiConfig.analizEs,
      'ebeveyn_cocuk' => ApiConfig.analizEb,
      'potansiyel_yetenek' => ApiConfig.analizPy,
      'ashtakoot' => ApiConfig.analizAshtakoot,
      _ => ApiConfig.analizNatal,
    };
    return _post(url, req.toJson(), timeout: ApiConfig.longTimeout);
  }

  Future<List<Map<String, dynamic>>> minorProgressNotifications({
    required String date,
    required String time,
    required String city,
    required String country,
    required double latitude,
    required double longitude,
    required String language,
    int days = 30,
  }) async {
    final response = await _post(
      ApiConfig.minorProgressNotifications,
      {
        'tarih': date,
        'saat': time,
        'sehir': city,
        'ulke': country,
        'enlem': latitude,
        'boylam': longitude,
        'lang': language,
        'days': days.clamp(1, 30).toInt(),
      },
      timeout: const Duration(seconds: 45),
    );
    final entries = response['entries'];
    if (entries is! List) throw const FormatException('invalid minor progress');
    return entries
        .whereType<Map>()
        .map((entry) => Map<String, dynamic>.from(entry))
        .toList(growable: false);
  }

  Future<Map<String, dynamic>> detayliAnaliz(AnalysisRequest req) {
    final url = switch (req.mod) {
      'ebeveyn_cocuk' => ApiConfig.analizEbDetayli,
      _ => ApiConfig.analizEsDetayli,
    };
    return _post(url, req.toJson(), timeout: ApiConfig.longTimeout);
  }

  Future<Map<String, dynamic>> simulasyonRadar(AnalysisRequest req) => _post(
    ApiConfig.simulasyonRadar,
    req.toJson(),
    timeout: ApiConfig.longTimeout,
  );

  Future<Map<String, dynamic>> simulasyonNatalRadar(AnalysisRequest req) =>
      _post(
        ApiConfig.simulasyonNatalRadar,
        req.toJson(),
        timeout: ApiConfig.longTimeout,
      );

  Future<Map<String, dynamic>> simulasyonAlternatif(
    Map<String, dynamic> data,
  ) => _post(
    ApiConfig.simulasyonAlternatif,
    data,
    timeout: ApiConfig.longTimeout,
  );

  Future<Map<String, dynamic>> astroKartografi(Map<String, dynamic> data) =>
      _post(ApiConfig.astrokartografi, data, timeout: ApiConfig.longTimeout);

  Future<Map<String, dynamic>> paymentCheckout(Map<String, dynamic> data) =>
      _post(ApiConfig.paymentCheckout, data);

  Future<Map<String, dynamic>> paymentVerify(String sessionId) =>
      _get('${ApiConfig.paymentVerify}/$sessionId');

  Future<Map<String, dynamic>> sendPdfEmail(Map<String, dynamic> data) =>
      _post(ApiConfig.sendPdfEmail, data);

  Future<Map<String, dynamic>> getStats() => _get(ApiConfig.stats);

  String getGorselUrl(String sessionId, String tip) =>
      '${ApiConfig.gorselBase}/$sessionId/$tip';

  Future<String> getPdfUrl(String sessionId, String tip) async {
    final uid = await BillingService.getBillingUid();
    return '${ApiConfig.pdfBase}/$sessionId/$tip?uid=${Uri.encodeQueryComponent(uid)}';
  }

  String getAcgHaritaUrl(String sessionId) =>
      '${ApiConfig.acgHarita}/$sessionId';

  String getSehirGorselUrl(String sehir) =>
      '${ApiConfig.sehirGorsel}/${Uri.encodeComponent(sehir)}';

  Future<Map<String, dynamic>> getSehirBilgi(String sehir) =>
      _get('${ApiConfig.sehirBilgi}/${Uri.encodeComponent(sehir)}');

  Future<Map<String, dynamic>> loadAcgMap(String sessionId) =>
      _get('${ApiConfig.acgHarita}/$sessionId');

  /// Doğum tarihi/saati/yeri → Güneş + Ay burcu ve dereceleri (künye).
  Future<Map<String, dynamic>> kunye({
    required String tarih,
    String saat = '12:00',
    double? lat,
    double? lon,
    String? sehir,
    String? ulke,
  }) => _post(ApiConfig.kunye, {
    'tarih': tarih,
    'saat': saat,
    if (sehir != null && sehir.isNotEmpty) 'sehir': sehir,
    if (ulke != null && ulke.isNotEmpty) 'ulke': ulke,
    'enlem': ?lat,
    'boylam': ?lon,
  });

  /// Anlık gökyüzü şeridi. Konum verilmezse İstanbul, saat dilimi cihazdan.
  Future<Map<String, dynamic>> sky({
    double lat = 41.0082,
    double lon = 28.9784,
    double? tz,
  }) {
    final offset = tz ?? DateTime.now().timeZoneOffset.inMinutes / 60.0;
    return _get(
      '${ApiConfig.sky}?lat=$lat&lon=$lon&tz=$offset',
      timeout: const Duration(seconds: 20),
    );
  }

  /// Yaklaşan ay fazları ve tutulmalar.
  Future<Map<String, dynamic>> skyCalendar({
    double lat = 41.0082,
    double lon = 28.9784,
    double? tz,
  }) {
    final offset = tz ?? DateTime.now().timeZoneOffset.inMinutes / 60.0;
    return _get(
      '${ApiConfig.skyCalendar}?lat=$lat&lon=$lon&tz=$offset',
      timeout: const Duration(seconds: 20),
    );
  }

  /// Ay'ın mevcut burcu (giriş/çıkış) ve yaklaşan burç geçişleri.
  Future<Map<String, dynamic>> skyMoonCalendar({int days = 30}) {
    return _get(
      '${ApiConfig.skyMoonCalendar}?days=$days',
      timeout: const Duration(seconds: 20),
    );
  }

  /// Ay boşta (VOC) dönemleri ve eylemlere göre doğru zaman pencereleri.
  Future<Map<String, dynamic>> skyMoonTiming({int days = 30}) {
    return _get(
      '${ApiConfig.skyMoonTiming}?days=$days',
      timeout: const Duration(seconds: 20),
    );
  }

  /// Gezegen retrosu, durağan anlar ve gölge dönemleri.
  Future<Map<String, dynamic>> skyRetroCalendar({int days = 365}) {
    return _get(
      '${ApiConfig.skyRetroCalendar}?days=$days',
      timeout: const Duration(seconds: 30),
    );
  }

  /// Ay'ın faz aralığı ve 28 eşit menzildeki geçişleri.
  Future<Map<String, dynamic>> skyMoonGuide({int days = 30}) {
    return _get(
      '${ApiConfig.skyMoonGuide}?days=$days',
      timeout: const Duration(seconds: 25),
    );
  }
}
