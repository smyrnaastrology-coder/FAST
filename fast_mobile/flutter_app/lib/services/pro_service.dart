import 'package:flutter/foundation.dart';
import 'billing_service.dart';
import 'revenuecat_service.dart';

/// Tek Pro hakkı: Horary (günde 3 soru → sınırsız) + Analiz PDF/özellikler.
/// Sosyal bölüm bilinçli olarak serbesttir.
class ProService {
  static bool? _cached;
  static bool _syncTried = false;
  static int _requestVersion = 0;

  /// İstenirse RevenueCat durumunu önbelleği atlayarak yeniden kontrol eder.
  static Future<bool> isPro({bool refresh = false}) async {
    if (!refresh && _cached != null) return _cached!;
    final version = ++_requestVersion;
    try {
      final pro = await RevenueCatService.isSubscribed(refresh: refresh);
      // Webhook kaçağı / uid değişimi için oturumda bir kez sunucu kurtarması.
      if (!pro && !_syncTried) {
        _syncTried = true;
        // Sunucu eşitlemesi PDF gibi abonelik dışı haklar da döndürebilir.
        // Bu nedenle sonucu Pro yetkisi olarak kullanma.
        await BillingService.syncEntitlement();
        if (kDebugMode) print('[Pro] sunucu hakları eşitlendi');
      }
      if (version == _requestVersion) _cached = pro;
      return pro;
    } catch (_) {
      if (version == _requestVersion) _cached = false;
      return false;
    }
  }

  /// Satın alma / çıkış sonrası bayrağı tazele.
  static void invalidate() {
    _requestVersion++;
    _cached = null;
    _syncTried = false;
  }
}
