import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../services/social_service.dart';

enum SocialStatus { idle, loading, ready, error }

/// Sosyal akış + profil durumunu tutan ChangeNotifier.
class SocialProvider extends ChangeNotifier {
  SocialProfile? _myProfile;
  final List<PostItem> _feed = [];
  final List<UserStories> _stories = [];
  Set<String> _blocked = {};
  SocialStatus _status = SocialStatus.idle;
  String? _error;
  bool _loadingMore = false;
  bool _hasMore = true;
  bool _initialized = false;

  static const int _pageSize = 15;

  bool _followingOnly = true;

  /// Akis yalnizca takip edilenleri mi gosteriyor (varsayilan)?
  bool get followingOnly => _followingOnly;

  SocialProfile? get myProfile => _myProfile;
  List<PostItem> get feed => List.unmodifiable(_feed);
  List<UserStories> get stories => List.unmodifiable(_stories);
  Set<String> get blocked => Set.unmodifiable(_blocked);
  SocialStatus get status => _status;

  /// Son hatanın kullanıcıya gösterilebilir metni (ağ/sunucu hatası).
  String? get error => _error;
  bool get loadingMore => _loadingMore;
  bool get hasMore => _hasMore;

  /// Kullanıcının sosyal profili var mı (handle aldı mı)?
  bool get hasHandle => _myProfile != null;

  bool get enabled => SocialService.enabled;
  bool get signedIn =>
      SocialService.enabled &&
      Supabase.instance.client.auth.currentUser != null;

  /// Uygulama açılışında çağrılır (giriş varsa profili + feed'i yükler).
  Future<void> init() async {
    if (!enabled || !signedIn) {
      _initialized = true;
      return;
    }
    await refresh();
    _initialized = true;
  }

  /// Feed'i baştan çeker (pull-to-refresh).
  Future<void> refresh() async {
    if (!enabled || !signedIn) return;
    _status = SocialStatus.loading;
    _error = null;
    notifyListeners();

    try {
      _blocked = await SocialService.blockedIds();
      await SocialService.syncProStatus();
      unawaited(SocialService.syncKunye());
      _myProfile = await SocialService.myProfile();
      final page = await SocialService.fetchFeed(
        limit: _pageSize,
        offset: 0,
        blocked: _blocked,
        onlyFollowing: _followingOnly,
      );
      _feed
        ..clear()
        ..addAll(page);
      _hasMore = page.length >= _pageSize;
      _status = SocialStatus.ready;
    } catch (e) {
      // Hata "boş feed" olarak yutulmaz — kullanıcı retry görebilsin.
      _status = SocialStatus.error;
      _error = _describe(e);
    }
    notifyListeners();
    refreshStories();
  }

  static String _describe(Object e) {
    final s = e.toString();
    if (s.contains('SocketException') ||
        s.contains('Failed host lookup') ||
        s.contains('Network')) {
      return 'net';
    }
    if (s.contains('401') || s.contains('403') || s.contains('JWT'))
      return 'auth';
    return 'unknown';
  }

  /// Aktif hikâyeleri çeker.
  Future<void> refreshStories() async {
    if (!enabled || !signedIn) return;
    final list = await SocialService.fetchStoriesFeed();
    _stories
      ..clear()
      ..addAll(list);
    notifyListeners();
  }

  /// Hikâye izlendikten sonra ring'i günceller (yerel).
  void markStoriesViewed(String userId) {
    final i = _stories.indexWhere(
      (s) => s.profile?.userId == userId || _isUserStories(s, userId),
    );
    if (i >= 0) {
      _stories[i] = UserStories(
        profile: _stories[i].profile,
        stories: _stories[i].stories,
        allViewed: true,
      );
      notifyListeners();
    }
  }

  bool _isUserStories(UserStories s, String userId) =>
      s.stories.isNotEmpty && s.stories.first.userId == userId;

  /// Sonraki sayfayı ekler.
  Future<void> loadMore() async {
    if (!enabled || !signedIn || _loadingMore || !_hasMore) return;
    _loadingMore = true;
    notifyListeners();
    try {
      final page = await SocialService.fetchFeed(
        limit: _pageSize,
        offset: _feed.length,
        blocked: _blocked,
        onlyFollowing: _followingOnly,
      );
      if (page.isNotEmpty) _feed.addAll(page);
      _hasMore = page.length >= _pageSize;
    } catch (e) {
      // Sayfa yüklenemedi -> sonsuz kaydırma kilitlenmesin.
      _hasMore = false;
      if (kDebugMode) print('[Social] loadMore err $e');
    }
    _loadingMore = false;
    notifyListeners();
  }

  /// Akis kapsamini degistirir: takip edilenler <-> kesfet.
  Future<void> setFollowingOnly(bool value) async {
    if (_followingOnly == value) return;
    _followingOnly = value;
    _feed.clear();
    _hasMore = true;
    notifyListeners();
    await refresh();
  }

  /// Yeni post yayınlandıktan sonra feed'in başına ekler.
  void prepend(PostItem post) {
    _feed.insert(0, post);
    notifyListeners();
  }

  /// Beğeniyi yerel olarak tersine çevirir. Yeni durumu döndürür.
  Future<bool> toggleLike(PostItem post) async {
    final nowLiked = await SocialService.toggleLike(post.id);
    final i = _feed.indexWhere((p) => p.id == post.id);
    if (i >= 0) {
      final p = _feed[i];
      _feed[i] = p.copyWith(
        likedByMe: nowLiked,
        likeCount: p.likeCount + (nowLiked ? 1 : -1),
      );
      notifyListeners();
    }
    return nowLiked;
  }

  /// Yorum sayısını yerel olarak artırır.
  void incrementCommentCount(String postId) {
    final i = _feed.indexWhere((p) => p.id == postId);
    if (i >= 0) {
      _feed[i] = _feed[i].copyWith(commentCount: _feed[i].commentCount + 1);
      notifyListeners();
    }
  }

  /// Postu feed'den kaldırır (silince).
  void removePost(String postId) {
    _feed.removeWhere((p) => p.id == postId);
    notifyListeners();
  }

  /// Bir kullanıcıyı engelledikten sonra feed'den temizler.
  void filterBlockedFeed() {
    _feed.removeWhere((p) => _blocked.contains(p.userId));
    notifyListeners();
  }

  void setBlocked(Set<String> ids) {
    _blocked = Set.of(ids);
    notifyListeners();
  }

  Future<void> refreshProfile() async {
    if (!enabled || !signedIn) return;
    await SocialService.syncProStatus();
    await SocialService.syncKunye();
    _myProfile = await SocialService.myProfile();
    notifyListeners();
  }

  /// Giriş durumu değişince çağrılır (auth_provider.onSessionChanged tetikler).
  Future<void> onAuthChanged() async {
    if (!enabled) return;
    final giris = signedIn;
    if (!giris) {
      _myProfile = null;
      _feed.clear();
      _stories.clear();
      _blocked = {};
      _status = SocialStatus.idle;
      notifyListeners();
      return;
    }
    await refresh();
  }

  bool get initialized => _initialized;
}
