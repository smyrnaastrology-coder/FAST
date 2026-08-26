import 'package:flutter/foundation.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'billing_service.dart';

/// RevenueCat iskeleti — API key .env / --dart-define ile verilir.
/// Gerçek ürünler: sub_daily ($7.99), sub_daily_yearly ($49.99), pdf_single ($19.99)
class RevenueCatService {
  static bool _inited = false;

  static Future<void> init() async {
    const key = String.fromEnvironment('REVENUECAT_API_KEY', defaultValue: '');
    if (key.isEmpty) {
      if (kDebugMode) print('[RC] API key yok — iskelet mod (mock)');
      return;
    }
    await Purchases.setLogLevel(LogLevel.debug);
    final uid = await BillingService.getUid();
    PurchasesConfiguration config = PurchasesConfiguration(key)..appUserID = uid;
    await Purchases.configure(config);
    _inited = true;
    if (kDebugMode) print('[RC] init ok uid=$uid');
  }

  static Future<bool> purchase(String productId) async {
    if (!_inited) {
      // Mock: backend'e direkt webhook simülasyonu
      if (kDebugMode) print('[RC mock] purchase $productId');
      return true;
    }
    try {
      final res = await Purchases.purchaseProduct(productId);
      return res.entitlements.active.isNotEmpty;
    } catch (e) {
      if (kDebugMode) print('[RC] purchase err $e');
      return false;
    }
  }

  static Future<bool> isSubscribed() async {
    if (!_inited) {
      final s = await BillingService.getStatus();
      return s['is_subscribed'] == true;
    }
    try {
      final info = await Purchases.getCustomerInfo();
      return info.entitlements.active.isNotEmpty;
    } catch (_) {
      return false;
    }
  }
}
