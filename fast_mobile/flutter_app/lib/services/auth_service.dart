import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../config/api_config.dart';
import 'revenuecat_service.dart';

/// Kayıtlı kişi modeli (backend auth_people tablosu ile birebir).
class SavedPerson {
  final int id;
  final String name;
  final String? birthDate;
  final String? birthTime;
  final String? city;
  final String? country;
  final double? lat;
  final double? lon;
  final String? utcOffset;
  final String? folder;

  const SavedPerson({
    required this.id,
    required this.name,
    this.birthDate,
    this.birthTime,
    this.city,
    this.country,
    this.lat,
    this.lon,
    this.utcOffset,
    this.folder,
  });

  factory SavedPerson.fromJson(Map<String, dynamic> j) => SavedPerson(
        id: (j['id'] as num?)?.toInt() ?? 0,
        name: (j['name'] ?? '').toString(),
        birthDate: j['birth_date']?.toString(),
        birthTime: j['birth_time']?.toString(),
        city: j['city']?.toString(),
        country: j['country']?.toString(),
        lat: (j['lat'] as num?)?.toDouble(),
        lon: (j['lon'] as num?)?.toDouble(),
        utcOffset: j['utc_offset']?.toString(),
        folder: j['folder']?.toString(),
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'birth_date': birthDate,
        'birth_time': birthTime,
        'city': city,
        'country': country,
        'lat': lat,
        'lon': lon,
        'utc_offset': utcOffset,
        'folder': folder,
      };
}

/// Supabase tabanlı üyelik servisi.
///
/// - Giriş yokken pasif (analiz & ücretsiz PDF akışı eskisi gibi çalışır).
/// - Giriş yapınca Supabase AppAuth session kullanılır; access token backend'e
///   `Authorization: Bearer ...` olarak gider.
/// - "Beni hatırla" -> Supabase persistSession + local flag.
class AuthService {
  static String? _sessionToken;
  static String? _refreshToken;
  static String? _userEmail;
  static String? _userId;
  static Map<String, String> _customFolders = {};
  static const _rememberKey = 'auth_remember_me';

  static bool get enabled => ApiConfig.supabaseEnabled;

  static bool get isLoggedIn => _sessionToken != null && _sessionToken!.isNotEmpty;

  static String get userId => _userId ?? '';

  static String? get refreshToken => _refreshToken;

  static String get email => _userEmail ?? '';

  static Map<String, String> get customFolders => _customFolders;

  static Future<void> init() async {
    if (!enabled) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      final remember = prefs.getBool(_rememberKey) ?? false;
      if (remember) {
        final session = Supabase.instance.client.auth.currentSession;
        if (session != null) {
          _applySession(session);
        }
      }
    } catch (e) {
      if (kDebugMode) print('[Auth] init err $e');
    }
  }

  static void _applySession(Session? session) {
    if (session == null) return;
    _sessionToken = session.accessToken;
    _refreshToken = session.refreshToken;
    _userId = session.user.id;
    _userEmail = session.user.email;
    Future<void>.microtask(() =>
        RevenueCatService.identify(_userId ?? '')).ignore();
  }

  static String? get _authorization =>
      _sessionToken == null ? null : 'Bearer $_sessionToken';

  static Map<String, String> _headers({bool json = false}) => {
        if (_authorization != null) 'Authorization': _authorization!,
        if (json) 'Content-Type': 'application/json',
      };

  /// E-posta + şifre ile kayıt.
  static Future<void> signUp({required String email, required String password, String? fullName}) async {
    if (!enabled) throw StateError('supabase_disabled');
    final res = await Supabase.instance.client.auth.signUp(
      email: email,
      password: password,
      data: {'full_name': fullName ?? ''},
    );
    _applySession(res.session);
  }

  /// E-posta + şifre ile giriş. [remember] -> kalıcı oturum.
  static Future<void> signIn({required String email, required String password, bool remember = true}) async {
    if (!enabled) throw StateError('supabase_disabled');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_rememberKey, remember);
    final res = await Supabase.instance.client.auth.signInWithPassword(
      email: email,
      password: password,
    );
    _applySession(res.session);
  }

  /// Google ile giriş (Supabase OAuth — deep link dönüşü).
  static Future<void> signInWithGoogle() async {
    if (!enabled) throw StateError('supabase_disabled');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_rememberKey, true);
    await Supabase.instance.client.auth.signInWithOAuth(OAuthProvider.google,
        redirectTo: _redirectUri);
    final session = Supabase.instance.client.auth.currentSession;
    _applySession(session);
  }

  /// Facebook ile giriş (Supabase OAuth).
  static Future<void> signInWithFacebook() async {
    if (!enabled) throw StateError('supabase_disabled');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_rememberKey, true);
    await Supabase.instance.client.auth.signInWithOAuth(OAuthProvider.facebook,
        redirectTo: _redirectUri);
    final session = Supabase.instance.client.auth.currentSession;
    _applySession(session);
  }

  static Future<void> signOut() async {
    if (enabled) {
      try {
        await Supabase.instance.client.auth.signOut();
      } catch (_) {}
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_rememberKey, false);
    _sessionToken = null;
    _refreshToken = null;
    _userId = null;
    _userEmail = null;
    RevenueCatService.reset();
  }

  static Future<bool> refreshSession() async {
    if (!enabled || refreshToken == null) return false;
    try {
      final res = await Supabase.instance.client.auth.refreshSession();
      _applySession(res.session);
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Backend'den güncel kullanıcı bilgisi.
  static Future<Map<String, dynamic>?> me() async {
    final ok = await _ensureToken();
    if (!ok) return null;
    try {
      final r = await http.get(Uri.parse('${ApiConfig.baseUrl}/api/auth/me'),
          headers: _headers()).timeout(const Duration(seconds: 12));
      if (r.statusCode == 200) return jsonDecode(r.body) as Map<String, dynamic>;
    } catch (e) {
      if (kDebugMode) print('[Auth] me err $e');
    }
    return null;
  }

  static Future<bool> updateProfile({String? displayName, String? lang}) async {
    if (!await _ensureToken()) return false;
    try {
      final body = <String, dynamic>{
        if (displayName != null) 'display_name': displayName,
        if (lang != null) 'lang': lang,
      };
      final r = await http.put(Uri.parse('${ApiConfig.baseUrl}/api/auth/me'),
          headers: _headers(json: true), body: jsonEncode(body)).timeout(const Duration(seconds: 12));
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Supabase üzerinden şifre değiştir.
  static Future<void> changePassword(String newPassword) async {
    if (!enabled) throw StateError('supabase_disabled');
    await Supabase.instance.client.auth.updateUser(UserAttributes(password: newPassword));
  }

  /// Şifre sıfırlama e-postası gönder.
  static Future<void> resetPasswordEmail(String email) async {
    if (!enabled) throw StateError('supabase_disabled');
    await Supabase.instance.client.auth.resetPasswordForEmail(email, redirectTo: _redirectUri);
  }

  // ─── Kayıtlı kişiler (backend CRUD) ───
  static Future<List<SavedPerson>> listPeople() async {
    if (!await _ensureToken()) return [];
    try {
      final r = await http.get(Uri.parse('${ApiConfig.baseUrl}/api/people'),
          headers: _headers()).timeout(const Duration(seconds: 12));
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body) as Map<String, dynamic>;
        final list = (data['people'] as List? ?? []);
        return list.whereType<Map<String, dynamic>>().map(SavedPerson.fromJson).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<SavedPerson?> createPerson(SavedPerson p) async {
    if (!await _ensureToken()) return null;
    try {
      final r = await http.post(Uri.parse('${ApiConfig.baseUrl}/api/people'),
          headers: _headers(json: true), body: jsonEncode(p.toJson())).timeout(const Duration(seconds: 12));
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body) as Map<String, dynamic>;
        return SavedPerson.fromJson(data['person'] as Map<String, dynamic>);
      }
    } catch (_) {}
    return null;
  }

  static Future<SavedPerson?> updatePerson(SavedPerson p) async {
    if (!await _ensureToken()) return null;
    try {
      final r = await http.put(Uri.parse('${ApiConfig.baseUrl}/api/people/${p.id}'),
          headers: _headers(json: true), body: jsonEncode(p.toJson())).timeout(const Duration(seconds: 12));
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body) as Map<String, dynamic>;
        return SavedPerson.fromJson(data['person'] as Map<String, dynamic>);
      }
    } catch (_) {}
    return null;
  }

  static Future<bool> deletePerson(int id) async {
    if (!await _ensureToken()) return false;
    try {
      final r = await http.delete(Uri.parse('${ApiConfig.baseUrl}/api/people/$id'),
          headers: _headers()).timeout(const Duration(seconds: 12));
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<Map<String, String>> loadFolders() async {
    if (!await _ensureToken()) return {};
    try {
      final r = await http.get(Uri.parse('${ApiConfig.baseUrl}/api/people/folders'),
          headers: _headers()).timeout(const Duration(seconds: 12));
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body) as Map<String, dynamic>;
        final f = (data['folders'] as Map<String, dynamic>? ?? {});
        _customFolders = f.map((k, v) => MapEntry(k, v.toString()));
        return _customFolders;
      }
    } catch (_) {}
    return {};
  }

  static Future<bool> _ensureToken() async {
    if (isLoggedIn) return true;
    if (!enabled) return false;
    if (await refreshSession()) return true;
    await signOut();
    return false;
  }

  static String get _redirectUri {
    // Android deep link — applicationId scheme.
    const scheme = 'com.fastastrology.fast';
    return '$scheme://login-callback';
  }
}