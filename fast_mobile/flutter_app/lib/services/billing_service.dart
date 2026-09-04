import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart';
import 'package:fast_app/config/api_config.dart';

class BillingService {
  static const _uidKey = 'fbst_uid';
  // Render backend — ana API base'i kullan (aynı sunucu)
  static String get _base => ApiConfig.baseUrl;

  static String? _cachedUid;

  static Future<String> getUid() async {
    if (_cachedUid != null) return _cachedUid!;
    final prefs = await SharedPreferences.getInstance();
    var uid = prefs.getString(_uidKey);
    if (uid == null) {
      uid = 'uid_${DateTime.now().millisecondsSinceEpoch}_${(1000 + (DateTime.now().microsecond % 9000))}';
      await prefs.setString(_uidKey, uid);
    }
    _cachedUid = uid;
    return uid;
  }

  static Future<Map<String, dynamic>> getStatus() async {
    try {
      final uid = await getUid();
      final r = await http.get(Uri.parse('$_base/api/billing/status?uid=$uid')).timeout(const Duration(seconds: 8));
      if (r.statusCode == 200) return jsonDecode(r.body) as Map<String, dynamic>;
    } catch (e) {
      if (kDebugMode) print('billing status error: $e');
    }
    return {'is_subscribed': false, 'has_free_used': false};
  }

  static Future<bool> claimFree() async {
    try {
      final uid = await getUid();
      final r = await http.post(Uri.parse('$_base/api/billing/claim-free'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'uid': uid})).timeout(const Duration(seconds: 10));
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Map<String, String> authHeaders(String uid) => {'X-UID': uid};
}
