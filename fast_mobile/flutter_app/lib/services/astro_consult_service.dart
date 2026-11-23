import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:supabase_flutter/supabase_flutter.dart';

import '../config/api_config.dart';

/// "Astroloğa Sor" — tek soruluk danışmanlık.
///
/// Faz 1: tek astrolog (platform sahibi). Şema çok astrologlu yapıya hazır
/// olduğu için [astrologers] listesi ileride seçim ekranına dönüşebilir.
class AstroConsultService {
  static const String singleQuestionProductId = 'sor_tek';
  static const double singleQuestionPrice = 2399.99;
  static const double followUpPrice = 399.99;
  static const int answerWindowHours = 24;

  static SupabaseClient get _c => Supabase.instance.client;

  static bool get _ready {
    try {
      _c;
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Aktif astrolog(lar). Faz 1'de tek satır döner.
  static Future<List<Map<String, dynamic>>> astrologers() async {
    if (!_ready) return const [];
    final rows = await _c
        .from('astrologers')
        .select()
        .eq('status', 'active')
        .order('sort_order');
    return (rows as List).cast<Map<String, dynamic>>();
  }

  /// `DateTime` → `YYYY-MM-DD` (Supabase `date` alanı için).
  static String isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';

  /// Yeni soru oluşturur. Ödeme henüz bağlı olmadığı için
  /// `pending_payment` durumunda kalır; ödeme doğrulanınca sunucu açar.
  ///
  /// Doğum bilgisi zorunludur: astrolog haritayı ancak tarih + saat + yer ile
  /// çıkarabilir. [birthTz] saat dilimi farkıdır (ör. Türkiye için 3).
  static Future<String> createQuestion({
    required String topic,
    required String question,
    required String lang,
    required DateTime birthDate,
    required String birthTime,
    required String birthPlace,
    double? birthLat,
    double? birthLon,
    double? birthTz,
    String? astrologerId,
    double price = singleQuestionPrice,
  }) async {
    final uid = _c.auth.currentUser?.id;
    if (uid == null) throw const AuthException('not_authenticated');

    final row = await _c
        .from('astro_questions')
        .insert({
          'user_id': uid,
          'astrologer_id': astrologerId,
          'topic': topic,
          'question': question.trim(),
          'lang': lang,
          'price_try': price,
          'product_id': singleQuestionProductId,
          'status': 'pending_payment',
          'birth_date': isoDate(birthDate),
          'birth_time': birthTime,
          'birth_place': birthPlace.trim(),
          'birth_lat': birthLat,
          'birth_lon': birthLon,
          'birth_tz': birthTz,
        })
        .select('id')
        .single();

    return row['id'] as String;
  }

  /// RevenueCat transaction is verified server-side before the 24-hour
  /// answer window starts. `paid: false` means the store transaction is not
  /// available yet; callers may then open the Play purchase sheet.
  static Future<Map<String, dynamic>> verifyQuestionPayment({
    required String questionId,
    String? transactionId,
    bool storePurchaseCompleted = false,
  }) async {
    final session = _c.auth.currentSession;
    if (session == null) throw const AuthException('not_authenticated');
    final response = await http
        .post(
          Uri.parse(ApiConfig.astroVerifyQuestionPayment),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ${session.accessToken}',
          },
          body: jsonEncode({
            'question_id': questionId,
            if (transactionId != null && transactionId.isNotEmpty)
              'transaction_id': transactionId,
            if (storePurchaseCompleted) 'store_purchase_completed': true,
          }),
        )
        .timeout(const Duration(seconds: 25));
    Map<String, dynamic> body;
    try {
      body = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      throw Exception('payment_verification_http_${response.statusCode}');
    }
    if (response.statusCode != 200) {
      final detail = body['detail'];
      throw Exception(detail is Map ? detail['code'] ?? detail : detail);
    }
    return body;
  }

  /// Kullanıcının kendi soruları (yeniden eskiye).
  static Future<List<Map<String, dynamic>>> myQuestions() async {
    if (!_ready) return const [];
    final uid = _c.auth.currentUser?.id;
    if (uid == null) return const [];
    final rows = await _c
        .from('astro_questions')
        .select()
        .eq('user_id', uid)
        .order('created_at', ascending: false)
        .limit(50);
    return (rows as List).cast<Map<String, dynamic>>();
  }

  /// Cevaba puan verir (yalnızca bir kez).
  static Future<void> rate({
    required String questionId,
    required int rating,
    String? note,
  }) async {
    await _c.rpc(
      'rate_astro_question',
      params: {'p_id': questionId, 'p_rating': rating, 'p_note': note},
    );
  }
}
