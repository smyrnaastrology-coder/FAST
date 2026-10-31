import 'dart:convert';
import 'dart:math';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'auth_service.dart';

/// A successful response may still contain a NO_QUOTA verdict.
class HoraryResult {
  final bool ok;
  final Map<String, dynamic> data;
  final String? error;
  final bool authError;
  const HoraryResult({required this.ok, this.data = const {}, this.error, this.authError = false});
}

/// Authenticated Holavon Horary API client.
class HoraryService {
  static Map<String, String>? _headers(String? accessToken) {
    final token = accessToken ?? AuthService.accessToken;
    if (token.isEmpty) return null;
    return {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'};
  }

  static String _requestId() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  }

  static Future<HoraryResult> quota({http.Client? client, String? accessToken}) async {
    final headers = _headers(accessToken);
    if (headers == null) return const HoraryResult(ok: false, error: 'auth', authError: true);
    try {
      final uri = Uri.parse(ApiConfig.horaryQuota);
      final response = await (client == null ? http.get(uri, headers: headers) : client.get(uri, headers: headers))
          .timeout(const Duration(seconds: 90));
      if (response.statusCode == 401) return const HoraryResult(ok: false, error: 'auth', authError: true);
      if (response.statusCode != 200) return HoraryResult(ok: false, error: 'http_${response.statusCode}');
      final data = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      if (data['remaining'] is! int || data['limit'] is! int || data['is_pro'] is! bool ||
          (data['limit'] as int) <= 0 || (data['remaining'] as int) < 0 ||
          (data['remaining'] as int) > (data['limit'] as int)) {
        return const HoraryResult(ok: false, error: 'parse');
      }
      return HoraryResult(ok: true, data: data);
    } catch (_) {
      return const HoraryResult(ok: false, error: 'error');
    }
  }

  static Future<HoraryResult> cast({
    required String question,
    required double lat,
    required double lon,
    String lang = 'tr',
    String category = 'general',
    String asker = 'ben',
    List<Map<String, dynamic>>? history,
    http.Client? client,
    String? accessToken,
  }) async {
    final headers = _headers(accessToken);
    if (headers == null) return const HoraryResult(ok: false, error: 'auth', authError: true);
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
      'request_id': _requestId(),
    };
    if (history != null && history.isNotEmpty) {
      payload['history'] = history.skip(max(0, history.length - 4)).toList();
    }

    http.Response? res;
    for (var attempt = 0; attempt < 4; attempt++) {
      try {
        final uri = Uri.parse(ApiConfig.horaryCast);
        final body = jsonEncode(payload);
        res = await (client == null
            ? http.post(uri, headers: headers, body: body)
            : client.post(uri, headers: headers, body: body))
            .timeout(const Duration(seconds: 90));
        // The server may still be processing the same request after a
        // timeout. Reuse its UUID; never reserve another question here.
        if (res.statusCode == 409 && attempt < 3) {
          await Future.delayed(const Duration(seconds: 3));
          continue;
        }
        break;
      } catch (_) {
        if (attempt == 3) {
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
