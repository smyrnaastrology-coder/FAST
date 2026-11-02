import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/widgets/chart_wheel_style.dart';

void main() {
  for (final style in [
    ChartWheelStyle.lightStyle,
    ChartWheelStyle.darkStyle,
  ]) {
    final theme = style.light ? 'açık' : 'koyu';

    test('$theme temada burç renkleri element gruplarını korur', () {
      // Ateş, toprak, hava ve su burçları; aynı element aynı aile rengi.
      expect(style.signColor(0), style.signColor(4));
      expect(style.signColor(0), style.signColor(8));
      expect(style.signColor(1), style.signColor(5));
      expect(style.signColor(2), style.signColor(6));
      expect(style.signColor(3), style.signColor(7));
      expect(
        {
          style.signColor(0),
          style.signColor(1),
          style.signColor(2),
          style.signColor(3),
        }.length,
        4,
      );
    });

    test('$theme temada gezegen renkleri birbirinden ayırt edilir', () {
      const planets = [
        'sun',
        'moon',
        'mercury',
        'venus',
        'mars',
        'jupiter',
        'saturn',
        'uranus',
        'neptune',
        'pluto',
        'north_node',
        'chiron',
      ];
      final colors = planets.map(style.planetColor).toSet();
      expect(colors.length, planets.length);
    });
  }
}
