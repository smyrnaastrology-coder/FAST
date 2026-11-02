import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/widgets/chart_wheel_geometry.dart';

void main() {
  group('tek çember (natal)', () {
    test('halkalar merkezden dışa doğru sıralı ve çakışmıyor', () {
      for (final r in [90.0, 140.0, 180.0, 260.0, 420.0]) {
        final g = ChartWheelGeometry(r, biWheel: false);
        expect(g.isConsistent, isTrue, reason: 'r=$r');
      }
    });

    test('yarıçaplar R üzerinden oranlı', () {
      const ratios = {
        'signOuter': 0.99,
        'signInner': 0.84,
        'aspectR': 0.575,
        'hubR': 0.13,
      };
      final g = ChartWheelGeometry(300, biWheel: false);
      expect(g.signOuter / 300, closeTo(ratios['signOuter']!, 1e-9));
      expect(g.signInner / 300, closeTo(ratios['signInner']!, 1e-9));
      expect(g.aspectR / 300, closeTo(ratios['aspectR']!, 1e-9));
      expect(g.hubR / 300, closeTo(ratios['hubR']!, 1e-9));
    });

    test('geometri ölçekle doğrusal büyür', () {
      final small = ChartWheelGeometry(100, biWheel: false);
      final big = ChartWheelGeometry(300, biWheel: false);
      expect(big.signOuter, closeTo(small.signOuter * 3, 1e-9));
      expect(big.natalGlyphR, closeTo(small.natalGlyphR * 3, 1e-9));
      expect(big.aspectR, closeTo(small.aspectR * 3, 1e-9));
    });

    test('gezegen sembolü çapın ~%2,5-4,5 aralığında kalır', () {
      for (final r in [100.0, 160.0, 240.0, 400.0]) {
        final g = ChartWheelGeometry(r, biWheel: false);
        final ratio = g.natalGlyphSize / (2 * r);
        expect(
          ratio,
          inInclusiveRange(0.024, 0.045),
          reason: 'r=$r oran=$ratio',
        );
      }
    });

    test('derece etiketi sembolden küçük', () {
      final g = ChartWheelGeometry(200, biWheel: false);
      expect(g.natalLabelSize, lessThan(g.natalGlyphSize));
    });
  });

  group('çift çember (natal + transit)', () {
    test('halkalar merkezden dışa doğru sıralı ve çakışmıyor', () {
      for (final r in [90.0, 140.0, 180.0, 260.0, 420.0]) {
        final g = ChartWheelGeometry(r, biWheel: true);
        expect(g.isConsistent, isTrue, reason: 'r=$r');
      }
    });

    test('iç ve dış gezegen halkaları ayrı', () {
      final g = ChartWheelGeometry(200, biWheel: true);
      // Doğum gezegenleri içeride, transit gezegenleri dışarıda.
      expect(g.natalGlyphR, lessThan(g.innerSignInner));
      expect(g.outerGlyphR, greaterThan(g.innerSignOuter));
      // Etiketler kendi sembol halkasının içinde.
      expect(g.natalLabelR, lessThan(g.natalGlyphR));
      expect(g.outerLabelR, lessThan(g.outerGlyphR));
    });

    test('çift çemberde doğum gezegeni halkası daralır', () {
      final single = ChartWheelGeometry(200, biWheel: false);
      final bi = ChartWheelGeometry(200, biWheel: true);
      expect(bi.natalGlyphR, lessThan(single.natalGlyphR));
      expect(bi.natalGlyphSize, lessThan(single.natalGlyphSize));
    });
  });

  test('çizgi kalınlıkları artan yarıçapla azalmaz', () {
    var prev = 0.0;
    for (final r in [80.0, 120.0, 200.0, 300.0, 500.0]) {
      final g = ChartWheelGeometry(r, biWheel: false);
      expect(g.aspectStroke, greaterThanOrEqualTo(prev));
      prev = g.aspectStroke;
    }
  });
}
