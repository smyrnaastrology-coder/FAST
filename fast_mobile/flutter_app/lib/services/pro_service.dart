import 'package:flutter/foundation.dart';
import 'billing_service.dart';
import 'revenuecat_service.dart';

/// Tek Pro hakkı: Horary (günde 3 soru → sınırsız) + Analiz PDF/özellikler.
/// Sosyal bölüm bilinçli olarak serbesttir.
class ProService {
  static bool? _cached;
  static bool _syncTried = false;

  /// Oturumda bir kez döner, sonucu önbellekler.
  static Future<bool> isPro() async {
    if (_cached != null) return _cached!;
    try {
      var pro = await RevenueCatService.isSubscribed();
      // Webhook kaçağı / uid değişimi için oturumda bir kez sunucu kurtarması.
      if (!pro && !_syncTried) {
        _syncTried = true;
        final r = await BillingService.syncEntitlement();
        pro = r['ok'] == true && (r['synced'] == true || r['granted'] == true);
        if (pro && kDebugMode) print('[Pro] entitlement sync ile kurtarıldı');
      }
      _cached = pro;
    } catch (_) {
      _cached = false;
    }
    return _cached!;
  }

  /// Satın alma / çıkış sonrası bayrağı tazele.
  static void invalidate() {
    _cached = null;
    _syncTried = false;
  }
}
