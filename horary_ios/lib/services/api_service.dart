import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/analysis_request.dart';

class ApiService {
  Future<Map<String, dynamic>> _post(String url, Map<String, dynamic> body, {Duration? timeout}) async {
    final r = await http.post(
      Uri.parse(url),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    ).timeout(timeout ?? ApiConfig.timeout);
    if (r.statusCode == 200) return jsonDecode(r.body);
    String msg;
    try { final e = jsonDecode(r.body); msg = e['detail'] ?? r.body; } catch (_) { msg = r.body; }
    throw Exception(msg);
  }

  Future<Map<String, dynamic>> _get(String url, {Duration? timeout}) async {
    final r = await http.get(Uri.parse(url)).timeout(timeout ?? ApiConfig.timeout);
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('HTTP ${r.statusCode}');
  }

  Future<List<dynamic>> _getList(String url, {Duration? timeout}) async {
    final r = await http.get(Uri.parse(url)).timeout(timeout ?? ApiConfig.timeout);
    if (r.statusCode == 200) return jsonDecode(r.body);
    throw Exception('HTTP ${r.statusCode}');
  }

  Future<List<dynamic>> getUlkeler() => _getList(ApiConfig.ulkeler);
  Future<Map<String, dynamic>> getUlkelerRaw() => _get(ApiConfig.ulkeler);

  Future<Map<String, dynamic>> geocode(String sehir) =>
      _post(ApiConfig.geocode, {'arama': sehir});

  Future<Map<String, dynamic>> analizYap(AnalysisRequest req) {
    final url = switch (req.mod) {
      'es_sevgili' => ApiConfig.analizEs,
      'ebeveyn_cocuk' => ApiConfig.analizEb,
      'potansiyel_yetenek' => ApiConfig.analizPy,
      _ => ApiConfig.analizNatal,
    };
    return _post(url, req.toJson(), timeout: ApiConfig.longTimeout);
  }

  Future<Map<String, dynamic>> detayliAnaliz(AnalysisRequest req) {
    final url = switch (req.mod) {
      'ebeveyn_cocuk' => ApiConfig.analizEbDetayli,
      _ => ApiConfig.analizEsDetayli,
    };
    return _post(url, req.toJson(), timeout: ApiConfig.longTimeout);
  }

  Future<Map<String, dynamic>> simulasyonRadar(AnalysisRequest req) =>
      _post(ApiConfig.simulasyonRadar, req.toJson(), timeout: ApiConfig.longTimeout);

  Future<Map<String, dynamic>> simulasyonNatalRadar(AnalysisRequest req) =>
      _post(ApiConfig.simulasyonNatalRadar, req.toJson(), timeout: ApiConfig.longTimeout);

  Future<Map<String, dynamic>> simulasyonAlternatif(Map<String, dynamic> data) =>
      _post(ApiConfig.simulasyonAlternatif, data, timeout: ApiConfig.longTimeout);

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

  String getPdfUrl(String sessionId, String tip) =>
      '${ApiConfig.pdfBase}/$sessionId/$tip';

  String getAcgHaritaUrl(String sessionId) =>
      '${ApiConfig.acgHarita}/$sessionId';

  String getSehirGorselUrl(String sehir) =>
      '${ApiConfig.sehirGorsel}/${Uri.encodeComponent(sehir)}';

  Future<Map<String, dynamic>> getSehirBilgi(String sehir) =>
      _get('${ApiConfig.sehirBilgi}/${Uri.encodeComponent(sehir)}');

  Future<Map<String, dynamic>> loadAcgMap(String sessionId) =>
      _get('${ApiConfig.acgHarita}/$sessionId');
}
