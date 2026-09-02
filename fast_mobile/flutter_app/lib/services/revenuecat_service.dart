import 'package:flutter/foundation.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'billing_service.dart';

/// RevenueCat iskeleti — API key .env / --dart-define ile verilir.
/// Gerçek ürünler: sub_daily ($7.99), sub_daily_yearly ($49.99), pdf_single ($19.99)
class RevenueCatService {
  static bool _inited = false;

  /// Ürün ID -> yerelleştirilmiş (bölgesel) fiyat etiketi.
  /// RevenueCat offering'inden getirilir; yoksa '7.99' gibi sabit düşer.
  static Map<String, String> _prices = {};

  static Future<void> _loadPrices() async {
    if (!_inited) return;
    try {
      final offerings = await Purchases.getOfferings();
      final current = offerings.current;
      if (current == null) return;
      final byId = <String, String>{};
      for (final pkg in current.availablePackages) {
        byId[pkg.storeProduct.identifier] = pkg.storeProduct.priceString;
      }
      // Alt ürünlere de bak (offering yoksa bile paket listesinden)
      if (byId.isEmpty) {
        for (final off in offerings.all.values) {
          for (final pkg in off.availablePackages) {
            byId[pkg.storeProduct.identifier] = pkg.storeProduct.priceString;
          }
        }
      }
      _prices = byId;
    } catch (e) {
      if (kDebugMode) print('[RC] price fetch err $e');
    }
  }

  static String priceFor(String productId, {String fallback = ''}) {
    return _prices[productId] ?? fallback;
  }

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
    await _loadPrices();
    if (kDebugMode) print('[RC] init ok uid=$uid prices=$_prices');
  }

  static Future<bool> purchase(String productId) async {
    if (!_inited) {
      // Mock: backend'e direkt webhook simülasyonu
      if (kDebugMode) print('[RC mock] purchase $productId');
      return true;
    }
    try {
      final offerings = await Purchases.getOfferings();
      Package? pkg;
      for (final off in offerings.all.values) {
        for (final p in off.availablePackages) {
          if (p.storeProduct.identifier == productId) {
            pkg = p;
            break;
          }
        }
        if (pkg != null) break;
      }
      if (pkg == null) {
        if (kDebugMode) print('[RC] product bulunamadı: $productId');
        return false;
      }
      final res = await Purchases.purchase(PurchaseParams.package(pkg));
      return res.customerInfo.entitlements.active.isNotEmpty;
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
