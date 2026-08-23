import 'dart:convert';
import 'package:http/http.dart' as http;

// Horary Oracle API client - yüksek performans, cache backend'de
class HoraryApi {
  // Render prod: https://horary-oracle-api.onrender.com  (örnek)
  // Lokal test: http://10.0.2.2:8000  (emulator) veya http://localhost:8000
  static const String baseUrl = String.fromEnvironment('HORARY_API_URL', defaultValue: 'https://horary-oracle-api.onrender.com');

  static Future<Map<String, dynamic>> cast({
    required String question,
    required double lat,
    required double lon,
    String lang = 'tr',
    List<Map<String, dynamic>>? history,
  }) async {
    final uri = Uri.parse('$baseUrl/api/horary/cast');
    // OpenAI + Render cold-start için 90sn + 1 retry (20sn çok kısaydı)
    http.Response? res;
    for (var attempt = 0; attempt < 2; attempt++) {
      try {
        res = await http.post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'question': question, 'lat': lat, 'lon': lon, 'lang': lang, if(history!=null) 'history': history}),
        ).timeout(const Duration(seconds: 90));
        break;
      } catch (e) {
        if (attempt == 1) rethrow;
        await Future.delayed(const Duration(seconds: 3));
      }
    }
    final r = res!;
    if (r.statusCode != 200) throw Exception('API ${r.statusCode}: ${r.body}');
    return jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> health() async {
    final res = await http.get(Uri.parse('$baseUrl/api/health'));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }
}
