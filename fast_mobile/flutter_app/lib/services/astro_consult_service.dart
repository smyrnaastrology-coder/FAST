import 'package:supabase_flutter/supabase_flutter.dart';

/// "Astroloğa Sor" — tek soruluk danışmanlık.
///
/// Faz 1: tek astrolog (platform sahibi). Şema çok astrologlu yapıya hazır
/// olduğu için [astrologers] listesi ileride seçim ekranına dönüşebilir.
class AstroConsultService {
  static const double singleQuestionPrice = 1999.99;
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

  /// Yeni soru oluşturur. Ödeme henüz bağlı olmadığı için
  /// `pending_payment` durumunda kalır; ödeme doğrulanınca sunucu açar.
  static Future<String> createQuestion({
    required String topic,
    required String question,
    required String lang,
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
          'status': 'pending_payment',
        })
        .select('id')
        .single();

    return row['id'] as String;
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
