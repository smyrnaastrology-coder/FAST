// Fast Koç — mobil API istemcisi (Faz 3 iskelet).
// Kullanim: FastKocApi(baseUrl: 'http://10.0.2.2:8090') — Android emulator localhost eslemesi.
// Bagimlilik: http paketi (Diclofenak: flutter pub add http firebase_messaging).
import 'dart:convert';
import 'package:http/http.dart' as http;

class FastKocApi {
  final String baseUrl;
  final String? token;
  FastKocApi({required this.baseUrl, this.token});

  Map<String, String> get _h => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  Future<Map<String, dynamic>> profilOlustur(Map<String, dynamic> p) async {
    final r = await http.post(Uri.parse('$baseUrl/api/profil'),
        headers: _h, body: jsonEncode(p));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> analiz(int ogrenciId) async {
    final r = await http.get(Uri.parse('$baseUrl/api/analiz/$ogrenciId'), headers: _h);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> haftalikOdev(int ogrenciId) async {
    final r = await http.get(Uri.parse('$baseUrl/api/odev/haftalik/$ogrenciId'), headers: _h);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> gunlukKaydet(Map<String, dynamic> g) async {
    final r = await http.post(Uri.parse('$baseUrl/api/gunluk'), headers: _h, body: jsonEncode(g));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> takvim([String? segment]) async {
    final q = segment == null ? '' : '?segment=$segment';
    final r = await http.get(Uri.parse('$baseUrl/api/takvim$q'), headers: _h);
    return jsonDecode(r.body) as List<dynamic>;
  }

  Future<List<dynamic>> bildirimler(int ogrenciId) async {
    final r = await http.get(Uri.parse('$baseUrl/api/bildirim/$ogrenciId'), headers: _h);
    return jsonDecode(r.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> kitapOner(int ogrenciId) async {
    final r = await http.get(Uri.parse('$baseUrl/api/kitap/oner/$ogrenciId'), headers: _h);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> segmentler() async {
    final r = await http.get(Uri.parse('$baseUrl/api/segmentler'), headers: _h);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> kocYorum(int ogrenciId) async {
    final r = await http.get(Uri.parse('$baseUrl/api/koc-yorum/$ogrenciId'), headers: _h);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// FCM token kaydi — firebase_messaging token'i burada gonderilir:
  ///   final t = await FirebaseMessaging.instance.getToken();
  ///   await api.cihazKaydet(ogrenciId, t!);
  Future<Map<String, dynamic>> cihazKaydet(int ogrenciId, String fcmToken,
      {String platform = 'android'}) async {
    final r = await http.post(Uri.parse('$baseUrl/api/cihaz'), headers: _h,
        body: jsonEncode({'ogrenci_id': ogrenciId, 'fcm_token': fcmToken, 'platform': platform}));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> kocOgrenciler(int sahipId) async {
    final r = await http.get(Uri.parse('$baseUrl/api/koc/$sahipId/ogrenciler'), headers: _h);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> plan(int ogrenciId) async {
    final r = await http.get(Uri.parse('$baseUrl/api/plan/$ogrenciId'), headers: _h);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }
}
