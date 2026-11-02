import 'package:flutter/foundation.dart';
import 'billing_service.dart';
import 'revenuecat_service.dart';

/// Tek Pro hakkı: Horary (günde 3 soru → sınırsız) + Analiz PDF/özellikler.
/// Sosyal bölüm bilinçli olarak serbesttir.
class ProService {
  static bool? _cached;
  static String? _cachedIdentity;
  static bool _syncTried = false;
  static int _requestVersion = 0;
  static final ValueNotifier<int> revision = ValueNotifier<int>(0);

  /// İstenirse RevenueCat durumunu önbelleği atlayarak yeniden kontrol eder.
  static Future<bool> isPro({bool refresh = false}) async {
    final identity = await BillingService.getBillingUid();
    if (!refresh && _cached != null && _cachedIdentity == identity) {
      return _cached!;
    }
    if (_cachedIdentity != identity) {
      _cached = null;
      _cachedIdentity = null;
      _syncTried = false;
    }
    final version = ++_requestVersion;
    try {
      // RevenueCat'in önceki Google/Supabase hesabında kalmış olma ihtimalini
      // kapat: sorgu öncesi app user ID'yi güncel billing kimliğine bağla.
      await RevenueCatService.identify(identity);
      final pro = await RevenueCatService.isSubscribed(refresh: refresh);
      final currentIdentity = await BillingService.getBillingUid();
      // Hesap sorgu sürerken değiştiyse eski hesabın sonucunu hiçbir kapıya
      // verme ve önbelleğe yazma.
      if (currentIdentity != identity) return false;
      // Webhook kaçağı / uid değişimi için oturumda bir kez sunucu kurtarması.
      if (!pro && !_syncTried) {
        _syncTried = true;
        // Sunucu eşitlemesi PDF gibi abonelik dışı haklar da döndürebilir.
        // Bu nedenle sonucu Pro yetkisi olarak kullanma.
        await BillingService.syncEntitlement();
        if (kDebugMode) print('[Pro] sunucu hakları eşitlendi');
      }
      if (version == _requestVersion) {
        _cached = pro;
        _cachedIdentity = identity;
      }
      return pro;
    } catch (_) {
      if (version == _requestVersion) {
        _cached = false;
        _cachedIdentity = identity;
      }
      return false;
    }
  }

  /// Satın alma / çıkış sonrası bayrağı tazele.
  static void invalidate({bool notify = true}) {
    _requestVersion++;
    _cached = null;
    _cachedIdentity = null;
    _syncTried = false;
    if (notify) revision.value++;
  }
}
