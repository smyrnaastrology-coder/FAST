import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'auth_service.dart';

/// Horary API sonucu: 'ok' false ise 'error' alanında kullanıcıya gösterilecek
/// metin vardır (401 kimlik / ağ / sunucu). 'verdict' NO_CREDITS olabilir.
class HoraryResult {
  final bool ok;
  final Map<String, dynamic> data;
  final String? error;
  final bool authError;
  const HoraryResult({required this.ok, this.data = const {}, this.error, this.authError = false});
}

/// Horary Oracle API istemcisi (horary-oracle-api). Kredi için e-posta gönderilir.
class HoraryService {
  static Future<HoraryResult> cast({
    required String question,
    required double lat,
    required double lon,
    String lang = 'tr',
    String category = 'general',
    String asker = 'ben',
    List<Map<String, dynamic>>? history,
  }) async {
    final now = DateTime.now(); // yerel saat — transit için kritik
    final payload = <String, dynamic>{
      'question': question,
      'lat': lat,
      'lon': lon,
      'lang': lang,
      'quesited_type': category,
      'asker': asker,
      'year': now.year,
      'month': now.month,
      'day': now.day,
      'hour': now.hour + now.minute / 60 + now.second / 3600,
    };
    final email = AuthService.email;
    if (email.isNotEmpty) payload['email'] = email;
    if (history != null && history.isNotEmpty) payload['history'] = history;

    http.Response? res;
    for (var attempt = 0; attempt < 2; attempt++) {
      try {
        res = await http
            .post(
              Uri.parse(ApiConfig.horaryCast),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode(payload),
            )
            .timeout(const Duration(seconds: 90));
        break;
      } catch (_) {
        if (attempt == 1) {
          return const HoraryResult(ok: false, error: 'error');
        }
        await Future.delayed(const Duration(seconds: 3));
      }
    }
    final r = res!;
    if (r.statusCode == 401) {
      return const HoraryResult(ok: false, error: 'auth', authError: true);
    }
    if (r.statusCode != 200) {
      return HoraryResult(ok: false, error: 'http_${r.statusCode}');
    }
    try {
      final data = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
      return HoraryResult(ok: true, data: data);
    } catch (_) {
      return const HoraryResult(ok: false, error: 'parse');
    }
  }
}
