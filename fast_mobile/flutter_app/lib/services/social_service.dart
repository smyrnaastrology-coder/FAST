import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:uuid/uuid.dart';
import '../config/api_config.dart';
import '../config/astro_signs.dart';
import 'api_service.dart';
import 'pro_service.dart';

/// Yükleme sınırları — depolama ve bant genişliğini korumak için.
class UploadLimits {
  /// Tek dosya için azami boyut (5 MB). Üsti reddedilir.
  static const int maxBytes = 5 * 1024 * 1024;

  /// Post/hikâye görseli için azami genişlik (px).
  static const int maxWidth = 1600;

  /// Avatar için azami genişlik (px).
  static const int avatarWidth = 400;

  /// JPEG kalitesi.
  static const int quality = 85;
}

/// Sosyal profil (public.social_profiles satırı).
class SocialProfile {
  final String userId;
  final String username;
  final String? displayName;
  final String? bio;
  final String? avatarUrl;
  final String? sunSign;
  final String? moonSign;

  /// Burç dereceleri (0–30). Yalnızca doğum saati biliniyorsa gösterilir.
  final double? sunDeg;
  final double? moonDeg;

  /// Doğum saati girilmiş mi? Derece gösterimini kontrol eder.
  final bool birthTimeSet;

  /// Astrolog mu (false: astroloji sever) + uzmanlık alanı.
  final bool isAstrologer;
  final String? astroField;
  final List<String> astroFields;

  /// Pro abonelik rozeti (profildeki altın tik). `social_profiles.is_pro`.
  final bool isPro;

  const SocialProfile({
    required this.userId,
    required this.username,
    this.displayName,
    this.bio,
    this.avatarUrl,
    this.sunSign,
    this.moonSign,
    this.sunDeg,
    this.moonDeg,
    this.birthTimeSet = false,
    this.isAstrologer = false,
    this.astroField,
    this.astroFields = const [],
    this.isPro = false,
  });

  factory SocialProfile.fromMap(Map<String, dynamic> m) {
    List<String> fields = [];
    final af = m['astro_fields'];
    if (af is List) {
      fields = af.map((e) => e.toString()).where((e) => e.isNotEmpty).toList();
    }
    final single = m['astro_field']?.toString();
    if (fields.isEmpty && single != null && single.isNotEmpty) {
      fields = single.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();
    }
    return SocialProfile(
      userId: (m['user_id'] ?? '').toString(),
      username: (m['username'] ?? '').toString(),
      displayName: m['display_name']?.toString(),
      bio: m['bio']?.toString(),
      avatarUrl: m['avatar_url']?.toString(),
      sunSign: m['sun_sign']?.toString(),
      moonSign: m['moon_sign']?.toString(),
      sunDeg: (m['sun_deg'] as num?)?.toDouble(),
      moonDeg: (m['moon_deg'] as num?)?.toDouble(),
      birthTimeSet: m['birth_time_set'] == true,
      isAstrologer: m['is_astrologer'] == true || fields.isNotEmpty,
      astroField: single ?? (fields.isNotEmpty ? fields.join(', ') : null),
      astroFields: fields,
      isPro: m['is_pro'] == true,
    );
  }
}

/// Kullanıcının doğum bilgisi (özel tablo `user_birthdates`).
class BirthInfo {
  final String? date; // YYYY-MM-DD
  final String? time; // HH:MM
  final String? city;
  final String? country;
  final double? lat;
  final double? lon;

  const BirthInfo({
    this.date,
    this.time,
    this.city,
    this.country,
    this.lat,
    this.lon,
  });

  bool get hasTime => time != null && time!.isNotEmpty;
}

/// Feed'de gösterilecek bir post (yazar + sayaçlarla zenginleştirilmiş).
class PostItem {
  final String id;
  final String userId;
  final String mediaUrl;
  final String? caption;
  final bool isChart;
  final DateTime createdAt;
  final SocialProfile? author;
  final int likeCount;
  final int commentCount;
  final bool likedByMe;

  const PostItem({
    required this.id,
    required this.userId,
    required this.mediaUrl,
    this.caption,
    required this.isChart,
    required this.createdAt,
    this.author,
    this.likeCount = 0,
    this.commentCount = 0,
    this.likedByMe = false,
  });

  factory PostItem.fromMap(Map<String, dynamic> m) => PostItem(
    id: (m['id'] ?? '').toString(),
    userId: (m['user_id'] ?? '').toString(),
    mediaUrl: (m['media_url'] ?? '').toString(),
    caption: m['caption']?.toString(),
    isChart: m['is_chart'] == true,
    createdAt:
        DateTime.tryParse((m['created_at'] ?? '').toString()) ?? DateTime.now(),
  );

  PostItem copyWith({
    SocialProfile? author,
    int? likeCount,
    int? commentCount,
    bool? likedByMe,
  }) => PostItem(
    id: id,
    userId: userId,
    mediaUrl: mediaUrl,
    caption: caption,
    isChart: isChart,
    createdAt: createdAt,
    author: author ?? this.author,
    likeCount: likeCount ?? this.likeCount,
    commentCount: commentCount ?? this.commentCount,
    likedByMe: likedByMe ?? this.likedByMe,
  );
}

/// Yorum satırı.
class CommentItem {
  final String id;
  final String postId;
  final String userId;
  final String text;
  final DateTime createdAt;
  final SocialProfile? author;

  const CommentItem({
    required this.id,
    required this.postId,
    required this.userId,
    required this.text,
    required this.createdAt,
    this.author,
  });

  factory CommentItem.fromMap(Map<String, dynamic> m) => CommentItem(
    id: (m['id'] ?? '').toString(),
    postId: (m['post_id'] ?? '').toString(),
    userId: (m['user_id'] ?? '').toString(),
    text: (m['text'] ?? '').toString(),
    createdAt:
        DateTime.tryParse((m['created_at'] ?? '').toString()) ?? DateTime.now(),
  );
}

/// Profil rozetindeki bir gezegen konumu (burç + derece).
class PlanetPos {
  final String planet; // 'Güneş' | 'Ay' | 'Merkür' | 'Venüs' | 'Mars'
  final String sign;
  final String? symbol;
  final double? degree; // burç içi derece (0–30)
  final double? absDegree;

  const PlanetPos({
    required this.planet,
    required this.sign,
    this.symbol,
    this.degree,
    this.absDegree,
  });

  factory PlanetPos.fromMap(Map<String, dynamic> m) => PlanetPos(
    planet: (m['planet'] ?? '').toString(),
    sign: (m['sign'] ?? '').toString(),
    symbol: m['symbol']?.toString(),
    degree: (m['degree'] as num?)?.toDouble(),
    absDegree: (m['abs_degree'] as num?)?.toDouble(),
  );
}

/// Tek bir hikâye (24 saatlik görsel).
class StoryItem {
  final String id;
  final String userId;
  final String mediaPath;
  DateTime createdAt;
  List<String> mentionIds;

  /// Görüntüleme URL'i. Hikâyeler private bucket'ta tutulduğu için bu
  /// değer imzalı (signed) bir URL'dir ve periyodik olarak yenilenir.
  String mediaUrl;

  StoryItem({
    required this.id,
    required this.userId,
    required this.mediaUrl,
    required this.createdAt,
    this.mediaPath = '',
    this.mentionIds = const [],
  });

  factory StoryItem.fromMap(Map<String, dynamic> m) => StoryItem(
    id: (m['id'] ?? '').toString(),
    userId: (m['user_id'] ?? '').toString(),
    mediaUrl: (m['media_url'] ?? '').toString(),
    mediaPath: (m['media_path'] ?? '').toString(),
    createdAt:
        DateTime.tryParse((m['created_at'] ?? '').toString()) ?? DateTime.now(),
  );
}

/// Bir kullanıcının aktif hikâyeleri + benim görüp görmediğim.
class UserStories {
  final SocialProfile? profile;
  final List<StoryItem> stories;
  final bool allViewed;
  const UserStories({
    this.profile,
    required this.stories,
    required this.allViewed,
  });
}

/// Tek bir DM mesajı.
class DmMessage {
  final String id;
  final String senderId;
  final String recipientId;
  final String text;
  final DateTime createdAt;
  final DateTime? readAt;

  const DmMessage({
    required this.id,
    required this.senderId,
    required this.recipientId,
    required this.text,
    required this.createdAt,
    this.readAt,
  });

  factory DmMessage.fromMap(Map<String, dynamic> m) => DmMessage(
    id: (m['id'] ?? '').toString(),
    senderId: (m['sender_id'] ?? '').toString(),
    recipientId: (m['recipient_id'] ?? '').toString(),
    text: (m['text'] ?? '').toString(),
    createdAt:
        DateTime.tryParse((m['created_at'] ?? '').toString()) ?? DateTime.now(),
    readAt: DateTime.tryParse((m['read_at'] ?? '').toString()),
  );
}

/// Gelen kutusundaki bir konuşma (tek bir muhatap).
class DmConversation {
  final String peerId;
  final SocialProfile? peer;
  final String lastText;
  final DateTime lastAt;
  final int unread;

  const DmConversation({
    required this.peerId,
    this.peer,
    required this.lastText,
    required this.lastAt,
    this.unread = 0,
  });
}

/// Supabase tabanlı sosyal servis.
///
/// Güvenlik: RLS her yerde `authenticated` kısıtlı. Okuma giriş yapan
/// herkese, yazma yalnızca auth.uid() = user_id.
class SocialService {
  static SupabaseClient get _c => Supabase.instance.client;

  static bool get enabled => ApiConfig.supabaseEnabled;

  static String get _me => _c.auth.currentUser?.id ?? '';

  /// Mevcut oturumdaki kullanıcı kimliği (public).
  static String get currentUserId => _me;

  // ── Profil ────────────────────────────────────────────────────────────────

  static Future<SocialProfile?> myProfile() async {
    if (!enabled || _me.isEmpty) return null;
    try {
      final r = await _c
          .from('social_profiles')
          .select()
          .eq('user_id', _me)
          .maybeSingle();
      return r == null ? null : SocialProfile.fromMap(r);
    } catch (e) {
      if (kDebugMode) print('[Social] myProfile err $e');
      return null;
    }
  }

  static Future<SocialProfile?> profileByUser(String userId) async {
    if (!enabled || userId.isEmpty) return null;
    try {
      final r = await _c
          .from('social_profiles')
          .select()
          .eq('user_id', userId)
          .maybeSingle();
      return r == null ? null : SocialProfile.fromMap(r);
    } catch (_) {
      return null;
    }
  }

  static Future<Map<String, SocialProfile>> profilesByIds(
    Set<String> ids,
  ) async {
    if (!enabled || ids.isEmpty) return {};
    try {
      final r = await _c
          .from('social_profiles')
          .select()
          .inFilter('user_id', ids.toList());
      return {
        for (final row in (r as List))
          (row['user_id'] ?? '').toString(): SocialProfile.fromMap(
            row as Map<String, dynamic>,
          ),
      };
    } catch (_) {
      return {};
    }
  }

  static Future<bool> usernameTaken(String username) async {
    if (!enabled) return false;
    try {
      final r = await _c
          .from('social_profiles')
          .select('user_id')
          .ilike('username', username)
          .limit(1);
      return (r as List).isNotEmpty;
    } catch (_) {
      return false;
    }
  }

  /// @handle alır. Başarılıysa SocialProfile döner; kullanılamazsa hata fırlatır.
  static Future<SocialProfile> claimHandle({
    required String username,
    String? displayName,
    String? bio,
    String? birthDate,
    String? birthTime,
    String? birthCity,
    String? birthCountry,
    double? lat,
    double? lon,
    bool isAstrologer = false,
    String? astroField,
  }) async {
    if (!enabled) throw StateError('supabase_disabled');
    final uid = _me;
    if (uid.isEmpty) throw StateError('not_signed_in');
    final clean = username.trim().toLowerCase();
    if (clean.length < 3) throw StateError('username_too_short');
    if (!RegExp(r'^[a-z0-9_.]+$').hasMatch(clean))
      throw StateError('username_invalid');
    if (await usernameTaken(clean)) throw StateError('username_taken');

    final info = BirthInfo(
      date: birthDate,
      time: birthTime,
      city: birthCity,
      country: birthCountry,
      lat: lat,
      lon: lon,
    );
    final kunye = await _kunyePatch(info);
    final sign = (kunye?['sun_sign'] as String?) ?? _signFromDate(birthDate);
    await _c.from('social_profiles').upsert({
      'user_id': uid,
      'username': clean,
      'display_name': (displayName ?? '').isEmpty ? null : displayName,
      'bio': (bio ?? '').isEmpty ? null : bio,
      'sun_sign': sign,
    });
    // Kunye/rol kolonlari (kunye.sql) henuz eklenmemis olabilir: ayri yaz.
    try {
      await _c
          .from('social_profiles')
          .update({
            ...?kunye,
            'is_astrologer': isAstrologer,
            'astro_field': isAstrologer ? astroField : null,
          })
          .eq('user_id', uid);
    } catch (_) {}
    if (birthDate != null && birthDate.isNotEmpty) {
      await _saveBirthInfo(uid, info);
    }
    if (kunye != null) await _markKunyeSynced(uid);
    final p = await myProfile();
    return p ??
        SocialProfile(
          userId: uid,
          username: clean,
          displayName: displayName,
          bio: bio,
          sunSign: sign,
        );
  }

  static Future<void> updateMyProfile({
    String? displayName,
    String? bio,
    String? birthDate,
    String? avatarUrl,
    String? birthTime,
    String? birthCity,
    String? birthCountry,
    double? lat,
    double? lon,
    bool? isAstrologer,
    String? astroField,
  }) async {
    if (!enabled || _me.isEmpty) return;
    final base = <String, dynamic>{
      if (displayName != null)
        'display_name': displayName.isEmpty ? null : displayName,
      if (bio != null) 'bio': bio.isEmpty ? null : bio,
      if (avatarUrl != null) 'avatar_url': avatarUrl,
    };
    if (birthDate != null) {
      base['sun_sign'] = _signFromDate(birthDate);
    }
    if (base.isNotEmpty) {
      await _c.from('social_profiles').update(base).eq('user_id', _me);
    }

    final info = BirthInfo(
      date: birthDate,
      time: birthTime,
      city: birthCity,
      country: birthCountry,
      lat: lat,
      lon: lon,
    );
    final kunye = birthDate == null ? null : await _kunyePatch(info);
    final extra = <String, dynamic>{
      ...?kunye,
      'is_astrologer': ?isAstrologer,
      if (isAstrologer != null) 'astro_field': isAstrologer ? astroField : null,
    };
    if (extra.isNotEmpty) {
      try {
        await _c.from('social_profiles').update(extra).eq('user_id', _me);
      } catch (_) {}
    }
    if (birthDate != null) {
      await _saveBirthInfo(_me, info);
    }
    if (kunye != null) await _markKunyeSynced(_me);
  }

  static Future<void> _markKunyeSynced(String uid) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('kunye_v2_$uid', true);
    } catch (_) {}
  }

  /// Doğum bilgisini (özel tablo) kaydeder. Yeni kolonlar yoksa yalnızca tarih.
  static Future<void> _saveBirthInfo(String uid, BirthInfo info) async {
    try {
      await _c.from('user_birthdates').upsert({
        'user_id': uid,
        'birth_date': info.date,
      });
    } catch (e) {
      if (kDebugMode) print('[Social] birth upsert err $e');
      return;
    }
    try {
      await _c
          .from('user_birthdates')
          .update({
            'birth_time': info.hasTime ? info.time : null,
            'birth_city': (info.city ?? '').isEmpty ? null : info.city,
            'birth_country': (info.country ?? '').isEmpty ? null : info.country,
            'lat': info.lat,
            'lon': info.lon,
          })
          .eq('user_id', uid);
    } catch (_) {
      // kunye.sql calistirilmamis olabilir.
    }
  }

  /// Doğum tarihi/saat/yer bilgisini döndürür (yoksa null).
  static Future<BirthInfo?> myBirthInfo() async {
    if (!enabled || _me.isEmpty) return null;
    try {
      final r = await _c
          .from('user_birthdates')
          .select('birth_date,birth_time,birth_city,birth_country,lat,lon')
          .eq('user_id', _me)
          .maybeSingle();
      if (r == null) return null;
      return BirthInfo(
        date: r['birth_date']?.toString(),
        time: r['birth_time']?.toString(),
        city: r['birth_city']?.toString(),
        country: r['birth_country']?.toString(),
        lat: (r['lat'] as num?)?.toDouble(),
        lon: (r['lon'] as num?)?.toDouble(),
      );
    } catch (_) {
      try {
        final r = await _c
            .from('user_birthdates')
            .select('birth_date')
            .eq('user_id', _me)
            .maybeSingle();
        return r == null ? null : BirthInfo(date: r['birth_date']?.toString());
      } catch (_) {
        return null;
      }
    }
  }

  /// Güneş/Ay burcu + derecesini sunucudan (Swiss Ephemeris) hesaplar.
  static Future<Map<String, dynamic>?> _kunyePatch(BirthInfo info) async {
    final date = info.date;
    if (date == null || date.isEmpty) return null;
    try {
      final r = await ApiService().kunye(
        tarih: date,
        saat: info.hasTime ? info.time! : '12:00',
        lat: info.lat,
        lon: info.lon,
        sehir: info.city,
        ulke: info.country,
      );
      final sun = r['gunes'];
      final moon = r['ay'];
      if (sun is! Map || moon is! Map) return null;
      final sunAbs = (sun['mutlak'] as num?)?.toDouble();
      final moonAbs = (moon['mutlak'] as num?)?.toDouble();
      if (sunAbs == null || moonAbs == null) return null;
      return {
        'sun_sign': AstroSigns.signNameFromLongitude(sunAbs),
        'sun_deg': double.parse((sunAbs % 30).toStringAsFixed(1)),
        'moon_sign': AstroSigns.signNameFromLongitude(moonAbs),
        'moon_deg': double.parse((moonAbs % 30).toStringAsFixed(1)),
        'birth_time_set': info.hasTime,
      };
    } catch (e) {
      if (kDebugMode) print('[Social] kunye err $e');
      return null;
    }
  }

  /// Mevcut kullanıcı için künyeyi bir kez yeniden hesaplar.
  ///
  /// Eski sürümde sabit gün tablosuyla yazılan `sun_sign` değerini düzeltir;
  /// Ay burcu/derecesi ve rol alanlarını tazeler. `kunye.sql` yoksa sessizce
  /// atlar ve bir sonraki açılışta tekrar dener.
  static Future<void> syncKunye() async {
    if (!enabled || _me.isEmpty) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      final key = 'kunye_v2_$_me';
      if (prefs.getBool(key) == true) return;
      final info = await myBirthInfo();
      if (info == null || info.date == null || info.date!.isEmpty) return;
      final patch = await _kunyePatch(info);
      if (patch == null) return;
      await _c.from('social_profiles').update(patch).eq('user_id', _me);
      await prefs.setBool(key, true);
    } catch (_) {
      // Kolonlar yok ya da ag hatasi: sonraki acilista tekrar denenir.
    }
  }

  /// Şehir adından koordinat/ülke çözer (künye için).
  static Future<Map<String, dynamic>?> geocodeCity(String city) async {
    final clean = city.trim();
    if (clean.length < 3) return null;
    try {
      return await ApiService().geocode(clean);
    } catch (_) {
      return null;
    }
  }

  /// Pro abonelik durumunu sosyal profile yansıtır; yalnızca değiştiyse yazar.
  ///
  /// Profildeki altın tik (`is_pro`) bu değerden okunur. Rozet yalnızca
  /// görsel bir göstergedir: RLS satırın sahibine yazma izni verir, bu yüzden
  /// istemci kendi bayrağını değiştirebilir. Sunucu tarafı doğrulama
  /// (RevenueCat webhook) eklenince yazma service_role'e taşınmalı.
  static Future<void> syncProStatus() async {
    if (!enabled || _me.isEmpty) return;
    try {
      final row = await _c
          .from('social_profiles')
          .select('is_pro')
          .eq('user_id', _me)
          .maybeSingle();
      if (row == null) return;
      final pro = await ProService.isPro();
      if ((row['is_pro'] == true) == pro) return;
      await _c
          .from('social_profiles')
          .update({'is_pro': pro})
          .eq('user_id', _me);
    } catch (_) {
      // Kolon henüz eklenmemiş olabilir (pro_badge.sql) — sessizce geç.
    }
  }

  static Future<String?> myBirthDate() async {
    if (!enabled || _me.isEmpty) return null;
    try {
      final r = await _c
          .from('user_birthdates')
          .select('birth_date')
          .eq('user_id', _me)
          .maybeSingle();
      return r?['birth_date']?.toString();
    } catch (_) {
      return null;
    }
  }

  static String? _signFromDate(String? iso) => AstroSigns.fromIsoDate(iso);

  // ── Gezegenler (profil rozeti) ─────────────────────────────────────────────

  /// Rozette gösterilecek 5 gezegen (sıra önemli).
  static const List<String> badgePlanets = [
    'Güneş',
    'Ay',
    'Merkür',
    'Venüs',
    'Mars',
  ];

  /// Natal analiz sonucundaki `sabianlar` listesinden 5 gezegeni çıkarır.
  /// Her satırda `gezegen` ve `derece` (mutlak boylam 0–360) bulunur.
  static List<PlanetPos> parseBadgePlanets(List<dynamic>? sabianlar) {
    if (sabianlar == null) return [];
    final out = <PlanetPos>[];
    for (final name in badgePlanets) {
      for (final row in sabianlar) {
        if (row is! Map) continue;
        if ((row['gezegen'] ?? '').toString() != name) continue;
        final abs = (row['derece'] as num?)?.toDouble();
        if (abs == null) continue;
        out.add(
          PlanetPos(
            planet: name,
            sign: AstroSigns.signNameFromLongitude(abs),
            symbol: AstroSigns.signSymbolFromLongitude(abs),
            degree: double.parse((abs % 30).toStringAsFixed(1)),
            absDegree: abs,
          ),
        );
        break;
      }
    }
    return out;
  }

  /// 5 gezegeni `user_planets` tablosuna kaydeder (varsa günceller).
  static Future<void> savePlanets(List<PlanetPos> planets) async {
    if (!enabled || _me.isEmpty || planets.isEmpty) return;
    try {
      final rows = [
        for (final p in planets)
          {
            'user_id': _me,
            'planet': p.planet,
            'sign': p.sign,
            'symbol': p.symbol,
            'degree': p.degree,
            'abs_degree': p.absDegree,
            'updated_at': DateTime.now().toIso8601String(),
          },
      ];
      await _c.from('user_planets').upsert(rows, onConflict: 'user_id,planet');
    } catch (e) {
      if (kDebugMode) print('[Social] savePlanets err $e');
    }
  }

  /// Bir kullanıcının rozet gezegenlerini çeker (Güneş→Mars sırasıyla).
  static Future<List<PlanetPos>> fetchPlanets(String userId) async {
    if (!enabled || userId.isEmpty) return [];
    try {
      final raw = await _c.from('user_planets').select().eq('user_id', userId);
      final list = (raw as List)
          .map((e) => PlanetPos.fromMap(e as Map<String, dynamic>))
          .where((p) => badgePlanets.contains(p.planet))
          .toList();
      final order = {
        for (var i = 0; i < badgePlanets.length; i++) badgePlanets[i]: i,
      };
      list.sort(
        (a, b) => (order[a.planet] ?? 99).compareTo(order[b.planet] ?? 99),
      );
      return list;
    } catch (_) {
      return [];
    }
  }

  // ── Hikâyeler ──────────────────────────────────────────────────────────────

  /// Hikâye medyası PRIVATE 'stories' bucket'ında tutulur.
  ///
  /// Görüntüleme için imzalı (signed) URL üretilir; imza 2 saatte bir yenilenir.
  /// Böylece hikâye yalnızca süresi dolana kadar, oturum açmış kullanıcılar
  /// tarafından görülebilir — tahmin edilebilir public URL sorunu biter.
  static const String _storiesBucket = 'stories';
  static const int _signedUrlTtlSeconds = 2 * 60 * 60;

  /// Yeni hikâye yükler (24 saat). [mentionIds] etiketlenen kullanıcılar.
  static Future<void> uploadStory(
    Uint8List bytes, {
    List<String> mentionIds = const [],
  }) async {
    if (!enabled || _me.isEmpty) throw StateError('not_signed_in');
    String mediaUrl;
    String? mediaPath;
    try {
      final path = await _uploadPath(bytes, _storiesBucket, 'jpg');
      mediaPath = path;
      mediaUrl = path; // okuma sırasında imzalanacak
    } on StateError catch (e) {
      // Boyut/giriş hatası gerçek hatadır — public bucket'a düşme.
      if (e.message == 'file_too_large' ||
          e.message == 'not_signed_in' ||
          e.message == 'empty_file') {
        rethrow;
      }
      // 'stories' bucket'ı henüz oluşturulmamışsa geçici olarak public bucket.
      mediaUrl = await _uploadBytes(bytes, 'posts', 'jpg');
    } catch (_) {
      // 'stories' bucket'ı henüz oluşturulmamışsa geçici olarak public bucket.
      mediaUrl = await _uploadBytes(bytes, 'posts', 'jpg');
    }
    final row = await _insertStory(mediaUrl, mediaPath);
    final storyId = (row['id'] ?? '').toString();
    if (mentionIds.isNotEmpty) {
      await _c.from('story_mentions').insert([
        for (final u in mentionIds)
          {'story_id': storyId, 'mentioned_user_id': u},
      ]);
    }
  }

  /// Hikâye satırını ekler. `media_path` kolonu henüz yoksa (SQL geçişi
  /// yapılmamışsa) kolon olmadan yeniden dener — aksi halde hikâye paylaşımı
  /// tamamen kırılırdı.
  static Future<Map<String, dynamic>> _insertStory(
    String mediaUrl,
    String? mediaPath,
  ) async {
    try {
      final r = await _c
          .from('stories')
          .insert({
            'user_id': _me,
            'media_url': mediaUrl,
            if (mediaPath != null) 'media_path': mediaPath,
            'media_type': 'image',
          })
          .select('id')
          .single();
      return (r as Map).cast<String, dynamic>();
    } catch (e) {
      if (mediaPath == null) rethrow;
      if (kDebugMode)
        print('[Social] media_path yok, eski şema ile deneniyor: $e');
      final r = await _c
          .from('stories')
          .insert({
            'user_id': _me,
            'media_url': mediaUrl,
            'media_type': 'image',
          })
          .select('id')
          .single();
      return (r as Map).cast<String, dynamic>();
    }
  }

  /// Aktif (süresi dolmamış) tüm hikâyeleri kullanıcı bazında gruplu çeker.
  static Future<List<UserStories>> fetchStoriesFeed() async {
    if (!enabled || _me.isEmpty) return [];
    try {
      final now = DateTime.now().toUtc().toIso8601String();
      List<Map<String, dynamic>> rows;
      try {
        final raw = await _c
            .from('stories')
            .select('id,user_id,media_url,media_path,created_at')
            .gt('expires_at', now)
            .order('created_at', ascending: true);
        rows = (raw as List).cast<Map<String, dynamic>>();
      } catch (_) {
        // Eski şema (media_path kolonu yok) — geriye dönük uyum.
        final raw = await _c
            .from('stories')
            .select('id,user_id,media_url,created_at')
            .gt('expires_at', now)
            .order('created_at', ascending: true);
        rows = (raw as List).cast<Map<String, dynamic>>();
      }
      if (rows.isEmpty) return [];

      final stories = rows.map(StoryItem.fromMap).toList();
      final userIds = stories.map((s) => s.userId).toSet();
      final authors = await profilesByIds(userIds);

      // PRIVATE bucket -> görüntülemek için imzalı URL üret.
      await _signStoryUrls(stories);

      // Benim gördüğüm hikâye id'leri.
      final ids = stories.map((s) => s.id).toList();
      final viewed = <String>{};
      try {
        final v = await _c
            .from('story_views')
            .select('story_id')
            .eq('viewer_id', _me)
            .inFilter('story_id', ids);
        for (final r in (v as List))
          viewed.add((r['story_id'] ?? '').toString());
      } catch (_) {}

      final byUser = <String, List<StoryItem>>{};
      for (final s in stories) {
        byUser.putIfAbsent(s.userId, () => []).add(s);
      }
      return [
        for (final e in byUser.entries)
          UserStories(
            profile: authors[e.key],
            stories: e.value,
            allViewed: e.value.every((s) => viewed.contains(s.id)),
          ),
      ];
    } catch (e) {
      if (kDebugMode) print('[Social] fetchStoriesFeed err $e');
      return [];
    }
  }

  /// Hikâye medya yolları için tek seferde imzalı URL üretir.
  static Future<void> _signStoryUrls(List<StoryItem> stories) async {
    final byPath = <String, StoryItem>{};
    for (final s in stories) {
      final p = s.mediaPath;
      // Sadece storage yolu olan (public URL olmayan) kayıtlar imzalanır.
      if (p.isNotEmpty && !p.startsWith('http')) byPath[p] = s;
    }
    if (byPath.isEmpty) return;
    try {
      final res = await _c.storage
          .from(_storiesBucket)
          .createSignedUrlsResult(byPath.keys.toList(), _signedUrlTtlSeconds);
      final signed = <String, String>{};
      for (final r in res) {
        switch (r) {
          case SignedUrlSuccess(:final path, :final signedUrl):
            signed[path] = signedUrl;
          case SignedUrlFailure(:final path, :final error):
            if (kDebugMode) print('[Social] imzalanamadı $path: $error');
        }
      }
      for (final s in stories) {
        final u = signed[s.mediaPath];
        if (u != null) s.mediaUrl = u;
      }
    } catch (e) {
      if (kDebugMode) print('[Social] signStoryUrls err $e');
    }
  }

  static Future<void> markStoryViewed(String storyId) async {
    if (!enabled || _me.isEmpty) return;
    try {
      await _c.from('story_views').upsert({
        'story_id': storyId,
        'viewer_id': _me,
      }, onConflict: 'story_id,viewer_id');
    } catch (_) {}
  }

  static Future<int> storyViewCount(String storyId) async {
    if (!enabled) return 0;
    try {
      final r = await _c
          .from('story_views')
          .select('viewer_id')
          .eq('story_id', storyId)
          .count(CountOption.exact);
      return r.count;
    } catch (_) {
      return 0;
    }
  }

  /// Bir hikâyede etiketlenen kullanıcıların @handle'ları.
  static Future<List<String>> storyMentions(String storyId) async {
    if (!enabled) return [];
    try {
      final raw = await _c
          .from('story_mentions')
          .select('mentioned_user_id')
          .eq('story_id', storyId);
      final ids = (raw as List)
          .map((r) => (r['mentioned_user_id'] ?? '').toString())
          .toSet();
      if (ids.isEmpty) return [];
      final profiles = await profilesByIds(ids);
      final out = <String>[];
      for (final u in ids) {
        final un = profiles[u]?.username;
        if (un != null && un.isNotEmpty) out.add('@$un');
      }
      return out;
    } catch (_) {
      return [];
    }
  }

  static Future<void> deleteStory(String id) async {
    if (!enabled) return;
    try {
      await _c.from('stories').delete().eq('id', id);
    } catch (_) {}
  }

  // ── DM (birebir mesajlar) ────────────────────────────────────────────────

  /// Mesaj gönderir. [peerId] karşı tarafın kullanıcı id'si.
  ///
  /// Engelleme mesajlaşmayı da keser: engellediğin kişiye yazamazsın,
  /// seni engelleyen kişiye de yazamazsın (StateError('blocked')).
  static Future<void> sendMessage(String peerId, String text) async {
    if (!enabled || _me.isEmpty) throw StateError('not_signed_in');
    final t = text.trim();
    if (t.isEmpty) return;
    if (await isBlockedEitherWay(peerId)) throw StateError('blocked');
    await _c.from('messages').insert({
      'sender_id': _me,
      'recipient_id': peerId,
      'text': t,
    });
  }

  /// İki kullanıcı arasındaki mesajları kronolojik (eskiden yeniye) çeker.
  static Future<List<DmMessage>> fetchConversation(
    String peerId, {
    int limit = 200,
  }) async {
    if (!enabled || _me.isEmpty || peerId.isEmpty) return [];
    try {
      // Engellenmiş sohbetler hiç açılmaz.
      if (await isBlockedEitherWay(peerId)) return [];
      final raw = await _c
          .from('messages')
          .select()
          .or(
            'and(sender_id.eq.$_me,recipient_id.eq.$peerId),and(sender_id.eq.$peerId,recipient_id.eq.$_me)',
          )
          .order('created_at', ascending: false)
          .limit(limit);
      final list = (raw as List)
          .map((e) => DmMessage.fromMap(e as Map<String, dynamic>))
          .toList();
      list.sort((a, b) => a.createdAt.compareTo(b.createdAt));
      return list;
    } catch (e) {
      if (kDebugMode) print('[Social] fetchConversation err $e');
      return [];
    }
  }

  /// Karşı tarafın bana gönderdiği mesajları "okundu" işaretler.
  static Future<void> markConversationRead(String peerId) async {
    if (!enabled || _me.isEmpty || peerId.isEmpty) return;
    try {
      await _c
          .from('messages')
          .update({'read_at': DateTime.now().toUtc().toIso8601String()})
          .eq('recipient_id', _me)
          .eq('sender_id', peerId)
          .isFilter('read_at', null);
    } catch (e) {
      if (kDebugMode) print('[Social] markConversationRead err $e');
    }
  }

  /// Gelen kutusu: benimle mesajlaşan herkes, son mesaj + okunmamış sayısı.
  static Future<List<DmConversation>> fetchInbox({int limit = 300}) async {
    if (!enabled || _me.isEmpty) return [];
    try {
      final raw = await _c
          .from('messages')
          .select('id,sender_id,recipient_id,text,created_at,read_at')
          .or('sender_id.eq.$_me,recipient_id.eq.$_me')
          .order('created_at', ascending: false)
          .limit(limit);
      final msgs = (raw as List)
          .map((e) => DmMessage.fromMap(e as Map<String, dynamic>))
          .toList();
      if (msgs.isEmpty) return [];

      // Mesajlar yeni->eski gelir; ilk görülen her muhatabın mesajı "son" mesajıdır.
      final peers = <String>[];
      final last = <String, DmMessage>{};
      final unread = <String, int>{};
      for (final m in msgs) {
        final peer = m.senderId == _me ? m.recipientId : m.senderId;
        if (!last.containsKey(peer)) {
          last[peer] = m;
          peers.add(peer);
        }
        if (m.recipientId == _me && m.readAt == null) {
          unread[peer] = (unread[peer] ?? 0) + 1;
        }
      }

      final profiles = await profilesByIds(peers.toSet());
      // Engellenen muhataplar gelen kutusunda görünmez.
      final blocked = await blockedIds();
      final blockedBy = await blockedByIds();
      final out = <DmConversation>[
        for (final p in peers)
          if (!blocked.contains(p) && !blockedBy.contains(p))
            DmConversation(
              peerId: p,
              peer: profiles[p],
              lastText: last[p]!.text,
              lastAt: last[p]!.createdAt,
              unread: unread[p] ?? 0,
            ),
      ];
      out.sort((a, b) => b.lastAt.compareTo(a.lastAt));
      return out;
    } catch (e) {
      if (kDebugMode) print('[Social] fetchInbox err $e');
      return [];
    }
  }

  static Future<void> deleteMessage(String id) async {
    if (!enabled || _me.isEmpty) return;
    try {
      await _c.from('messages').delete().eq('id', id);
    } catch (_) {}
  }

  // ── Görsel yükleme ────────────────────────────────────────────────────────

  static const _uuid = Uuid();

  /// Dosyayı yükler ve **path**'ini döndürür.
  ///
  /// Dosya adı UUID'dir: zaman damgası tahmin edilebilir olduğu için
  /// (msSinceEpoch) URL'ler tahmin edilebilirdi. Artık tahmin edilemez.
  static Future<String> _uploadPath(
    Uint8List bytes,
    String bucket,
    String ext,
  ) async {
    final uid = _me;
    if (uid.isEmpty) throw StateError('not_signed_in');
    if (bytes.isEmpty) throw StateError('empty_file');
    if (bytes.length > UploadLimits.maxBytes)
      throw StateError('file_too_large');
    final path = '$uid/${_uuid.v4()}.$ext';
    await _c.storage
        .from(bucket)
        .uploadBinary(
          path,
          bytes,
          fileOptions: FileOptions(
            contentType: _contentTypeOf(ext),
            upsert: false,
          ),
        );
    return path;
  }

  /// Yükler ve herkese açık URL döndürür (post / avatar).
  static Future<String> _uploadBytes(
    Uint8List bytes,
    String bucket,
    String ext,
  ) async {
    final path = await _uploadPath(bytes, bucket, ext);
    return _c.storage.from(bucket).getPublicUrl(path);
  }

  static Future<String> uploadAvatar(XFile file) async {
    final bytes = await file.readAsBytes();
    if (bytes.length > UploadLimits.maxBytes)
      throw StateError('file_too_large');
    return _uploadBytes(bytes, 'avatars', _extOf(file.path));
  }

  static Future<String> uploadImageBytes(
    Uint8List bytes, {
    String ext = 'jpg',
  }) => _uploadBytes(bytes, 'posts', ext);

  static String _contentTypeOf(String ext) {
    switch (ext.toLowerCase()) {
      case 'png':
        return 'image/png';
      case 'webp':
        return 'image/webp';
      case 'gif':
        return 'image/gif';
      default:
        return 'image/jpeg';
    }
  }

  static String _extOf(String path) {
    final e = path.split('.').last.toLowerCase();
    return (e == 'jpg' || e == 'jpeg' || e == 'png' || e == 'webp')
        ? (e == 'jpeg' ? 'jpg' : e)
        : 'jpg';
  }

  // ── Postlar ───────────────────────────────────────────────────────────────

  static Future<void> createPost({
    required String mediaUrl,
    String? caption,
    bool isChart = false,
  }) async {
    if (!enabled || _me.isEmpty) throw StateError('not_signed_in');
    await _c.from('posts').insert({
      'user_id': _me,
      'media_url': mediaUrl,
      'caption': (caption ?? '').isEmpty ? null : caption,
      'is_chart': isChart,
    });
  }

  static Future<void> deletePost(String id) async {
    if (!enabled) return;
    await _c.from('posts').delete().eq('id', id);
  }

  /// Feed sayfası çeker + yazar/like/yorum sayaçlarını toplu zenginleştirir.
  ///
  /// [blocked] verilirse engellenenler sorgusu atlanır (çağıran zaten biliyor).
  ///
  /// Hata durumunda **istisna fırlatır** (sessizce boş liste döndürmez) —
  /// çağıran taraf kullanıcıya "bağlantı hatası / tekrar dene" gösterebilsin.
  static Future<List<PostItem>> fetchFeed({
    int limit = 15,
    int offset = 0,
    Set<String>? blocked,
    bool onlyFollowing = false,
  }) async {
    if (!enabled || _me.isEmpty) return [];
    List<String>? authorIdsFilter;
    if (onlyFollowing) {
      final rows = await _c
          .from('follows')
          .select('followee_id')
          .eq('follower_id', _me);
      final ids = <String>{_me};
      for (final r in (rows as List)) {
        final id = (r['followee_id'] ?? '').toString();
        if (id.isNotEmpty) ids.add(id);
      }
      authorIdsFilter = ids.toList();
      if (authorIdsFilter.isEmpty) return [];
    }
    var query = _c.from('posts').select();
    if (authorIdsFilter != null) {
      query = query.inFilter('user_id', authorIdsFilter.cast<Object>());
    }
    final raw = await query
        .order('created_at', ascending: false)
        .range(offset, offset + limit - 1);
    final posts = (raw as List)
        .map((e) => PostItem.fromMap(e as Map<String, dynamic>))
        .toList();
    if (posts.isEmpty) return [];

    // Engellenen kullanıcıların postlarını feed'de gösterme.
    final blockedSet = blocked ?? await blockedIds();
    final src = posts.where((p) => !blockedSet.contains(p.userId)).toList();
    if (src.isEmpty) return [];

    final postIds = src.map((p) => p.id).toList();
    final authorIds = src.map((p) => p.userId).toSet();

    final authors = await profilesByIds(authorIds);

    final likeRows = await _c
        .from('likes')
        .select('post_id,user_id')
        .inFilter('post_id', postIds);
    final likeCount = <String, int>{};
    final likedMe = <String>{};
    for (final r in (likeRows as List)) {
      final pid = (r['post_id'] ?? '').toString();
      likeCount[pid] = (likeCount[pid] ?? 0) + 1;
      if ((r['user_id'] ?? '').toString() == _me) likedMe.add(pid);
    }

    final cRows = await _c
        .from('comments')
        .select('post_id')
        .inFilter('post_id', postIds);
    final cCount = <String, int>{};
    for (final r in (cRows as List)) {
      final pid = (r['post_id'] ?? '').toString();
      cCount[pid] = (cCount[pid] ?? 0) + 1;
    }

    return src
        .map(
          (p) => p.copyWith(
            author: authors[p.userId],
            likeCount: likeCount[p.id] ?? 0,
            commentCount: cCount[p.id] ?? 0,
            likedByMe: likedMe.contains(p.id),
          ),
        )
        .toList();
  }

  static Future<List<PostItem>> fetchUserPosts(
    String userId, {
    int limit = 60,
  }) async {
    if (!enabled || userId.isEmpty) return [];
    try {
      final raw = await _c
          .from('posts')
          .select()
          .eq('user_id', userId)
          .order('created_at', ascending: false)
          .limit(limit);
      final posts = (raw as List)
          .map((e) => PostItem.fromMap(e as Map<String, dynamic>))
          .toList();
      if (posts.isEmpty) return [];
      final postIds = posts.map((p) => p.id).toList();
      final author = await profileByUser(userId);

      final likeRows = await _c
          .from('likes')
          .select('post_id,user_id')
          .inFilter('post_id', postIds);
      final likeCount = <String, int>{};
      final likedMe = <String>{};
      for (final r in (likeRows as List)) {
        final pid = (r['post_id'] ?? '').toString();
        likeCount[pid] = (likeCount[pid] ?? 0) + 1;
        if ((r['user_id'] ?? '').toString() == _me) likedMe.add(pid);
      }
      final cRows = await _c
          .from('comments')
          .select('post_id')
          .inFilter('post_id', postIds);
      final cCount = <String, int>{};
      for (final r in (cRows as List)) {
        final pid = (r['post_id'] ?? '').toString();
        cCount[pid] = (cCount[pid] ?? 0) + 1;
      }

      return posts
          .map(
            (p) => p.copyWith(
              author: author,
              likeCount: likeCount[p.id] ?? 0,
              commentCount: cCount[p.id] ?? 0,
              likedByMe: likedMe.contains(p.id),
            ),
          )
          .toList();
    } catch (_) {
      return [];
    }
  }

  static Future<int> postCount(String userId) async {
    if (!enabled || userId.isEmpty) return 0;
    try {
      final r = await _c
          .from('posts')
          .select('id')
          .eq('user_id', userId)
          .count(CountOption.exact);
      return r.count;
    } catch (_) {
      return 0;
    }
  }

  // ── Beğeni ────────────────────────────────────────────────────────────────

  /// Beğen/beğeniyi kaldır. Yeni durumu döndürür.
  static Future<bool> toggleLike(String postId) async {
    if (!enabled || _me.isEmpty) return false;
    final existing = await _c
        .from('likes')
        .select('post_id')
        .eq('post_id', postId)
        .eq('user_id', _me)
        .maybeSingle();
    if (existing != null) {
      await _c.from('likes').delete().eq('post_id', postId).eq('user_id', _me);
      return false;
    }
    await _c.from('likes').insert({'post_id': postId, 'user_id': _me});
    return true;
  }

  // ── Yorumlar ──────────────────────────────────────────────────────────────

  static Future<List<CommentItem>> fetchComments(String postId) async {
    if (!enabled) return [];
    try {
      final raw = await _c
          .from('comments')
          .select()
          .eq('post_id', postId)
          .order('created_at', ascending: true);
      final list = (raw as List)
          .map((e) => CommentItem.fromMap(e as Map<String, dynamic>))
          .toList();
      final uids = list.map((c) => c.userId).toSet();
      final authors = await profilesByIds(uids);
      return list
          .map(
            (c) => CommentItem(
              id: c.id,
              postId: c.postId,
              userId: c.userId,
              text: c.text,
              createdAt: c.createdAt,
              author: authors[c.userId],
            ),
          )
          .toList();
    } catch (_) {
      return [];
    }
  }

  /// Post altında önizleme için en yeni [limit] yorumu yazarıyla çeker.
  static Future<List<CommentItem>> fetchRecentComments(
    String postId, {
    int limit = 3,
  }) async {
    if (!enabled) return [];
    try {
      final raw = await _c
          .from('comments')
          .select()
          .eq('post_id', postId)
          .order('created_at', ascending: false)
          .limit(limit);
      final list = (raw as List)
          .map((e) => CommentItem.fromMap(e as Map<String, dynamic>))
          .toList();
      if (list.isEmpty) return [];
      final authors = await profilesByIds(list.map((c) => c.userId).toSet());
      return list
          .map(
            (c) => CommentItem(
              id: c.id,
              postId: c.postId,
              userId: c.userId,
              text: c.text,
              createdAt: c.createdAt,
              author: authors[c.userId],
            ),
          )
          .toList();
    } catch (_) {
      return [];
    }
  }

  static Future<bool> addComment(String postId, String text) async {
    if (!enabled || _me.isEmpty) return false;
    await _c.from('comments').insert({
      'post_id': postId,
      'user_id': _me,
      'text': text.trim(),
    });
    return true;
  }

  static Future<void> deleteComment(String id) async {
    if (!enabled) return;
    await _c.from('comments').delete().eq('id', id);
  }

  // ── Takip ─────────────────────────────────────────────────────────────────

  /// Aktif kullanıcının takip ettiği kişilerin profilleri (DM alıcı seçimi).
  static Future<List<SocialProfile>> followingProfiles({
    int limit = 100,
  }) async {
    if (!enabled || _me.isEmpty) return const [];
    try {
      final rows = await _c
          .from('follows')
          .select('followee_id')
          .eq('follower_id', _me)
          .limit(limit);
      final ids = <String>[
        for (final r in (rows as List)) (r['followee_id'] ?? '').toString(),
      ]..removeWhere((e) => e.isEmpty);
      if (ids.isEmpty) return const [];
      final profs = await profilesByIds(ids.toSet());
      return [
        for (final id in ids)
          if (profs[id] != null) profs[id]!,
      ];
    } catch (_) {
      return const [];
    }
  }

  /// Belirli bir kullanıcının takipçileri.
  static Future<List<SocialProfile>> fetchFollowers(
    String userId, {
    int limit = 200,
  }) async {
    if (!enabled || userId.isEmpty) return const [];
    try {
      final rows = await _c
          .from('follows')
          .select('follower_id')
          .eq('followee_id', userId)
          .limit(limit);
      final ids = <String>[
        for (final r in (rows as List)) (r['follower_id'] ?? '').toString(),
      ]..removeWhere((e) => e.isEmpty);
      if (ids.isEmpty) return const [];
      final profs = await profilesByIds(ids.toSet());
      return [
        for (final id in ids)
          if (profs[id] != null) profs[id]!,
      ];
    } catch (_) {
      return const [];
    }
  }

  /// Belirli bir kullanıcının takip ettikleri.
  static Future<List<SocialProfile>> fetchFollowing(
    String userId, {
    int limit = 200,
  }) async {
    if (!enabled || userId.isEmpty) return const [];
    try {
      final rows = await _c
          .from('follows')
          .select('followee_id')
          .eq('follower_id', userId)
          .limit(limit);
      final ids = <String>[
        for (final r in (rows as List)) (r['followee_id'] ?? '').toString(),
      ]..removeWhere((e) => e.isEmpty);
      if (ids.isEmpty) return const [];
      final profs = await profilesByIds(ids.toSet());
      return [
        for (final id in ids)
          if (profs[id] != null) profs[id]!,
      ];
    } catch (_) {
      return const [];
    }
  }

  static Future<bool> isFollowing(String userId) async {
    if (!enabled || _me.isEmpty || userId == _me) return false;
    try {
      final r = await _c
          .from('follows')
          .select('follower_id')
          .eq('follower_id', _me)
          .eq('followee_id', userId)
          .maybeSingle();
      return r != null;
    } catch (_) {
      return false;
    }
  }

  static Future<void> follow(String userId) async {
    if (!enabled || _me.isEmpty || userId == _me) return;
    await _c.from('follows').upsert({
      'follower_id': _me,
      'followee_id': userId,
    });
  }

  static Future<void> unfollow(String userId) async {
    if (!enabled || _me.isEmpty) return;
    await _c
        .from('follows')
        .delete()
        .eq('follower_id', _me)
        .eq('followee_id', userId);
  }

  static Future<int> followerCount(String userId) async {
    if (!enabled || userId.isEmpty) return 0;
    try {
      final r = await _c
          .from('follows')
          .select('follower_id')
          .eq('followee_id', userId)
          .count(CountOption.exact);
      return r.count;
    } catch (_) {
      return 0;
    }
  }

  static Future<int> followingCount(String userId) async {
    if (!enabled || userId.isEmpty) return 0;
    try {
      final r = await _c
          .from('follows')
          .select('followee_id')
          .eq('follower_id', userId)
          .count(CountOption.exact);
      return r.count;
    } catch (_) {
      return 0;
    }
  }

  // ── Arama ─────────────────────────────────────────────────────────────────

  static Future<List<SocialProfile>> searchUsers(
    String query, {
    int limit = 30,
  }) async {
    if (!enabled || _me.isEmpty) return [];
    final q = query.trim();
    if (q.isEmpty) return [];
    try {
      final r = await _c
          .from('social_profiles')
          .select('user_id,username,display_name,avatar_url,sun_sign')
          .or('username.ilike.%$q%,display_name.ilike.%$q%')
          .neq('user_id', _me)
          .limit(limit);
      return (r as List)
          .map((e) => SocialProfile.fromMap(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  // ── Engelle / Bildir ──────────────────────────────────────────────────────

  static Future<void> block(String userId) async {
    if (!enabled || _me.isEmpty || userId == _me) return;
    await _c.from('blocks').upsert({'blocker_id': _me, 'blocked_id': userId});
    // Karşılıklı takipleri kaldır.
    await _c
        .from('follows')
        .delete()
        .eq('follower_id', _me)
        .eq('followee_id', userId);
    await _c
        .from('follows')
        .delete()
        .eq('follower_id', userId)
        .eq('followee_id', _me);
  }

  static Future<void> unblock(String userId) async {
    if (!enabled || _me.isEmpty) return;
    await _c
        .from('blocks')
        .delete()
        .eq('blocker_id', _me)
        .eq('blocked_id', userId);
  }

  /// Benim engellediğim kullanıcılar (tek yönlü).
  static Future<Set<String>> blockedIds() async {
    if (!enabled || _me.isEmpty) return {};
    try {
      final r = await _c
          .from('blocks')
          .select('blocked_id')
          .eq('blocker_id', _me);
      return (r as List).map((e) => (e['blocked_id'] ?? '').toString()).toSet();
    } catch (_) {
      return {};
    }
  }

  /// Beni engelleyen kullanıcılar (ters yön).
  static Future<Set<String>> blockedByIds() async {
    if (!enabled || _me.isEmpty) return {};
    try {
      final r = await _c
          .from('blocks')
          .select('blocker_id')
          .eq('blocked_id', _me);
      return (r as List).map((e) => (e['blocker_id'] ?? '').toString()).toSet();
    } catch (_) {
      return {};
    }
  }

  /// İki taraf arasında engel var mı (herhangi bir yönde)?
  ///
  /// Engelleme artık mesajlaşmayı da keser: engellediğin kişi sana yazamaz,
  /// seni engelleyen kişiye de yazamazsın.
  static Future<bool> isBlockedEitherWay(String userId) async {
    if (!enabled || _me.isEmpty || userId.isEmpty) return false;
    if (userId == _me) return false;
    try {
      final r = await _c
          .from('blocks')
          .select('blocker_id,blocked_id')
          .or(
            'and(blocker_id.eq.$_me,blocked_id.eq.$userId),and(blocker_id.eq.$userId,blocked_id.eq.$_me)',
          );
      return (r as List).isNotEmpty;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> isBlocked(String userId) async {
    final s = await blockedIds();
    return s.contains(userId);
  }

  static Future<void> report({
    required String targetType,
    required String targetId,
    String? reason,
  }) async {
    if (!enabled || _me.isEmpty) return;
    await _c.from('reports').insert({
      'reporter_id': _me,
      'target_type': targetType,
      'target_id': targetId,
      'reason': reason,
    });
  }
}
