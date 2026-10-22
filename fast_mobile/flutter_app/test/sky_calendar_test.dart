import 'package:flutter_test/flutter_test.dart';
import 'package:fast_app/models/sky_calendar.dart';

void main() {
  test('takvim yanıtı modellere çevrilir', () {
    final cal = SkyCalendar.fromJson({
      'fazlar': [
        {
          'tip': 'full_moon',
          'zaman': 1792987907,
          'ay': {'mutlak': 32.7619, 'burc': 1, 'derece': 2.76},
          'gunes': {'mutlak': 212.7619, 'burc': 7, 'derece': 2.76},
        },
      ],
      'tutulmalar': [
        {
          'tip': 'lunar',
          'alt_tip': 'penumbral',
          'zaman': 1803165171,
          'ay': {'mutlak': 151.9829, 'burc': 5, 'derece': 1.98},
          'gunes': {'mutlak': 332.0855, 'burc': 11, 'derece': 2.09},
          'gorunurluk': {
            'gorunur': true,
            'yerel_tip': 'penumbral',
            'ortulme': null,
            'buyukluk': 0.93,
            'sonraki_gorunur': null,
          },
        },
        {
          'tip': 'solar',
          'alt_tip': 'annular',
          'zaman': 1801929580,
          'ay': {'mutlak': 317.6565, 'burc': 10, 'derece': 17.66},
          'gunes': {'mutlak': 317.6296, 'burc': 10, 'derece': 17.63},
          'gorunurluk': {
            'gorunur': false,
            'sonraki_gorunur': {
              'zaman': 1817199551,
              'tip': 'solar',
              'alt_tip': 'partial',
              'ortulme': 59.4,
              'buyukluk': 0.66,
            },
          },
        },
      ],
    });

    expect(cal.phases.single.type, 'full_moon');
    expect(cal.phases.single.isNewMoon, isFalse);
    expect(cal.phases.single.moon.degree, closeTo(2.76, 0.001));
    expect(cal.eclipses.length, 2);
    expect(cal.eclipses.first.isSolar, isFalse);
    expect(cal.eclipses.first.visibility.visible, isTrue);
    expect(cal.eclipses.first.visibility.magnitude, closeTo(0.93, 0.001));
    expect(cal.eclipses.last.visibility.visible, isFalse);
    expect(cal.eclipses.last.visibility.nextVisible?.variant, 'partial');
    expect(
      cal.eclipses.last.visibility.nextVisible?.obscuration,
      closeTo(59.4, 0.001),
    );
  });
}
