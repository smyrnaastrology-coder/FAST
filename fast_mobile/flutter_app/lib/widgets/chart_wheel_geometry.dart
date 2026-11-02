import 'dart:math' as math;

/// Harita çarkının tüm yarıçaplarını ve yazı boyutlarını tek yerden üretir.
///
/// Tasarım kuralı: **hiçbir değer piksel cinsinden sabit değildir.** Hepsi
/// dış yarıçap `R` üzerinden oranlanır. Böylece harita büyütülüp küçültüldüğünde
/// halkalar, semboller, etiketler ve çizgi kalınlıkları birbirine göre orantılı
/// kalır (bkz. tasarım şartnamesi §2, §5, §10, §14).
///
/// Bu sınıf yalnızca görsel yerleşimi bilir. Gezegen boylamı, ev başlangıcı ve
/// açı hesapları buraya girmez; astronomik veri [ChartData] üzerinden gelir
/// (şartname §16: görsel katman hesaplamayı değiştiremez).
class ChartWheelGeometry {
  /// Dış çember yarıçapı (piksel).
  final double r;

  /// Çift çemberli (natal + transit) harita mı?
  final bool biWheel;

  ChartWheelGeometry(this.r, {required this.biWheel});

  // --- Zodyak kuşakları -----------------------------------------------------

  /// Dış zodyak kuşağı.
  double get signOuter => r * 0.99;
  double get signInner => biWheel ? r * 0.865 : r * 0.840;

  /// İç zodyak kuşağı (yalnızca çift çemberde).
  double get innerSignOuter => biWheel ? r * 0.665 : 0;
  double get innerSignInner => biWheel ? r * 0.545 : 0;

  /// Burç sembollerinin yerleştiği yarıçap (kuşağın ortası).
  double get signGlyphR => (signOuter + signInner) / 2;
  double get innerSignGlyphR => (innerSignOuter + innerSignInner) / 2;

  // --- Gezegen halkaları ----------------------------------------------------

  /// Dış (transit) harita: sembol ve etiket halkaları.
  double get outerGlyphR => biWheel ? r * 0.805 : 0;
  double get outerLabelR => biWheel ? r * 0.715 : 0;
  double get outerBandOuter => biWheel ? r * 0.865 : 0;
  double get outerBandInner => biWheel ? r * 0.685 : 0;

  /// İç (doğum) harita: sembol ve etiket halkaları.
  double get natalGlyphR => biWheel ? r * 0.4875 : r * 0.775;
  double get natalLabelR => biWheel ? r * 0.400 : r * 0.655;
  double get natalBandOuter => biWheel ? r * 0.545 : r * 0.840;
  double get natalBandInner => biWheel ? r * 0.370 : r * 0.620;

  // --- İç çalışma alanı -----------------------------------------------------

  /// Açı çizgilerinin bağlandığı çember.
  double get aspectR => biWheel ? r * 0.330 : r * 0.575;

  /// Ev numaralarının halkası.
  double get houseNumR => biWheel ? r * 0.302 : r * 0.598;

  /// Merkezdeki boş daire.
  double get hubR => biWheel ? r * 0.140 : r * 0.130;

  /// Ev çizgilerinin dış ucu: en içteki zodyak kuşağının iç kenarı.
  double get cuspOuterR => biWheel ? innerSignInner : signInner;

  /// Ev çizgilerinin iç ucu.
  double get cuspInnerR => hubR;

  /// ASC / DSC / MC / IC etiketlerinin yarıçapı.
  double get angleLabelR => hubR + r * 0.075;

  // --- Yazı boyutları -------------------------------------------------------

  /// Burç sembolü boyutu (dış kuşak).
  double get signGlyphSize =>
      ((signOuter - signInner) * 0.62).clamp(10.0, 24.0);

  /// Burç sembolü boyutu (iç kuşak).
  double get innerSignGlyphSize =>
      ((innerSignOuter - innerSignInner) * 0.62).clamp(9.0, 19.0);

  /// Doğum gezegeni sembolü.
  double get natalGlyphSize => (r * (biWheel ? 0.046 : 0.058)).clamp(8.0, 22.0);

  /// Doğum gezegeni derece/dakika etiketi.
  double get natalLabelSize => (r * (biWheel ? 0.030 : 0.038)).clamp(5.5, 11.0);

  /// Transit gezegen sembolü.
  double get outerGlyphSize => (r * 0.042).clamp(8.0, 18.0);

  /// Transit gezegeni derece/dakika etiketi.
  double get outerLabelSize => (r * 0.028).clamp(5.5, 9.5);

  /// Ev numarası boyutu.
  double get houseNumSize => (r * 0.033).clamp(7.5, 14.0);

  /// ASC / DSC / MC / IC etiket boyutu.
  double get angleLabelSize => (r * 0.030).clamp(8.0, 13.0);

  // --- Çizgi kalınlıkları (şartname §10) ------------------------------------

  /// Standart açı çizgisi.
  double get aspectStroke => (r * 0.0060).clamp(0.8, 1.5);

  /// Önemli açı (üçgen / karşıtlık) çizgisi.
  double get majorAspectStroke => aspectStroke * 1.35;

  /// Ev çizgisi.
  double get cuspStroke => (r * 0.0050).clamp(0.7, 1.2);

  /// Dış çember / kuşak sınırı.
  double get ringStroke => (r * 0.0075).clamp(0.9, 1.6);

  /// İnce bölme çizgisi.
  double get hairStroke => (r * 0.0055).clamp(0.7, 1.2);

  /// ASC / DSC / MC / IC ekseni.
  double get axisStroke => (r * 0.0090).clamp(1.1, 2.2);

  /// Gezegen sembolünün merkezine oturan nokta çapı.
  double get dotSize => math.max(1.0, r * 0.008);

  // --- Kabul kriterleri (test edilebilir) -----------------------------------

  /// Halkaların dıştan içe sırası ve çakışmama kontrolü.
  ///
  /// Şartname §16: "Gezegenler doğru boylamlara göre yerleştirilmeli,
  /// sembol boyutları orantılı olmalı, harita ölçeklenince geometri korunmalı."
  bool get isConsistent {
    // Merkezden dışa doğru sıralı halkalar (iç yarıçap, dış yarıçap).
    final bands = <(double, double)>[
      (hubR, hubR),
      (aspectR, aspectR),
      (natalBandInner, natalBandOuter),
      if (biWheel) (innerSignInner, innerSignOuter),
      if (biWheel) (outerBandInner, outerBandOuter),
      (signInner, signOuter),
    ];
    var prevOuter = 0.0;
    for (final b in bands) {
      if (b.$1 < prevOuter - 1e-9) return false;
      prevOuter = b.$2;
    }
    // Etiket halkası sembol halkasının içinde (merkeze daha yakın) olmalı.
    if (natalLabelR >= natalGlyphR) return false;
    if (natalGlyphR >= natalBandOuter) return false;
    if (natalLabelR <= natalBandInner) return false;
    if (biWheel) {
      if (outerLabelR >= outerGlyphR) return false;
      if (outerGlyphR >= outerBandOuter) return false;
      if (outerLabelR <= outerBandInner) return false;
    }
    return true;
  }
}
