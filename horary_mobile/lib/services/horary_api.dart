import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

// Horary Oracle API client - yüksek performans, cache backend'de
class HoraryApi {
  // Render prod: https://horary-oracle-api.onrender.com  (örnek)
  // Lokal test: http://10.0.2.2:8000  (emulator) veya http://localhost:8000
  static const String baseUrl = String.fromEnvironment('HORARY_API_URL', defaultValue: 'https://horary-oracle-api.onrender.com');
  static String? _sessionToken;

  static Future<Map<String, dynamic>> cast({
    required String question,
    required double lat,
    required double lon,
    String lang = 'tr',
    String category = 'general',
    String asker = 'ben',
    List<Map<String, dynamic>>? history,
    http.Client? client,
  }) async {
    final uri = Uri.parse('$baseUrl/api/horary/cast');
    final now = DateTime.now(); // yerel saat - transit için kritik
    final prefs = await SharedPreferences.getInstance();
    final email = prefs.getString('email') ?? '';
    final payload = {
      'question': question, 'lat': lat, 'lon': lon, 'lang': lang,
      'quesited_type': category, 'asker': asker,
      'year': now.year, 'month': now.month, 'day': now.day,
      'hour': now.hour + now.minute/60 + now.second/3600,
      if(email.isNotEmpty) 'email': email,
      if(history!=null) 'history': history,
    };
    http.Response? res;
    for (var attempt = 0; attempt < 2; attempt++) {
      try {
        final headers = {'Content-Type': 'application/json', if (_sessionToken != null) 'Authorization': 'Bearer $_sessionToken'};
        final body = jsonEncode(payload);
        res = await (client == null ? http.post(uri, headers: headers, body: body) : client.post(uri, headers: headers, body: body))
            .timeout(const Duration(seconds: 90));
        break;
      } catch (e) {
        if (attempt == 1) rethrow;
        await Future.delayed(const Duration(seconds: 3));
      }
    }
    var r = res!;
    if (r.statusCode == 401) {
      final password = prefs.getString('pass');
      if (email.isNotEmpty && password != null) {
        await login(email: email, password: password, deviceId: prefs.getString('device_id'), client: client);
        final headers = {'Content-Type': 'application/json', if (_sessionToken != null) 'Authorization': 'Bearer $_sessionToken'};
        final body = jsonEncode(payload);
        r = await (client == null ? http.post(uri, headers: headers, body: body) : client.post(uri, headers: headers, body: body))
            .timeout(const Duration(seconds: 90));
      }
    }
    if (r.statusCode != 200) throw Exception('API ${r.statusCode}: ${r.body}');
    return jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> login({required String email, required String password, String? deviceId, http.Client? client}) async {
    final uri = Uri.parse('$baseUrl/api/auth/login');
    final body = {'email':email,'password':password, if(deviceId!=null) 'device_id':deviceId};
    final headers = {'Content-Type':'application/json'};
    final encoded = jsonEncode(body);
    final res = await (client == null ? http.post(uri, headers: headers, body: encoded) : client.post(uri, headers: headers, body: encoded)).timeout(const Duration(seconds:30));
    if(res.statusCode!=200) throw Exception(res.body);
    final result = jsonDecode(utf8.decode(res.bodyBytes)) as Map<String,dynamic>;
    _sessionToken = result['session_token'] as String?;
    return result;
  }

  static Future<Map<String, dynamic>> health() async {
    final res = await http.get(Uri.parse('$baseUrl/api/health'));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }
}
