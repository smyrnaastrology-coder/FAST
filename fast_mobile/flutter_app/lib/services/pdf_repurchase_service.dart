import 'dart:async';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

/// Aynı Google hesabıyla TEKRAR pdf_single alınabilsin diye eski sahiplenmeyi
/// Play'de consume (tüket) eder.
///
/// Managed one-time ürünlerde Play, tüketilmemiş sahiplenme varken yeniden
/// satışı ITEM_ALREADY_OWNED ("bu öğe zaten sizde var") ile bloklar; consume
/// sonrası kilit kalkar ve RevenueCat purchase() ödeme ekranını açar.
/// Sunucu hakkı (webhook / sync_entitlement) kalıcı yazıldığı için consume
/// hak kaybettirmez; sadece Play tarafındaki yeniden-satış kilidini kaldırır.
///
/// Not: in_app_purchase 3.x'te geçmiş sahiplenmeler restorePurchases() ile
/// tetiklenip purchaseStream üzerinden gelir.
class PdfRepurchaseService {
  static const List<String> _pdfProducts = ['pdf_single'];

  static bool _matches(String productId) =>
      _pdfProducts.any((p) => productId == p || productId.startsWith('$p:'));

  /// Tüketilecek sahiplenme bulunup consume edildiyse true döner.
  /// Bulunamazsa (başka hesapta / zaten tüketilmiş / Play yok) false.
  static Future<bool> consumeOwnedPdfSingle() async {
    if (!Platform.isAndroid) return false;
    try {
      final iap = InAppPurchase.instance;
      if (!await iap.isAvailable()) return false;
      final completer = Completer<bool>();
      late final StreamSubscription<List<PurchaseDetails>> sub;
      Timer? timer;
      void done(bool v) {
        if (!completer.isCompleted) completer.complete(v);
      }

      sub = iap.purchaseStream.listen((purchases) async {
        for (final p in purchases) {
          if (!_matches(p.productID)) continue;
          if (p.status != PurchaseStatus.purchased &&
              p.status != PurchaseStatus.restored) {
            continue;
          }
          // Android'de one-time ürün için completePurchase = consume.
          // (RC üzerinden acknowledge edilmiş olsa bile owned managed ürün
          // consume edilebilir; kilit kalkar, yeniden satış açılır.)
          try {
            await iap.completePurchase(p);
            if (kDebugMode) print('[repurchase] consumed ${p.productID}');
            done(true);
          } catch (e) {
            if (kDebugMode) print('[repurchase] consume err $e');
          }
        }
      }, onError: (_) {});
      timer = Timer(const Duration(seconds: 15), () => done(false));
      await iap.restorePurchases();
      final ok = await completer.future;
      await sub.cancel();
      timer.cancel();
      return ok;
    } catch (e) {
      if (kDebugMode) print('[repurchase] err $e');
      return false;
    }
  }
}
