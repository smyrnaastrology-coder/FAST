import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/models/sky_calendar.dart';

void main() {
  test('Tutulma yerel temaslarını ve Saros bilgilerini çözer', () {
    final event = SkyEclipse.fromJson({
      'tip': 'lunar',
      'alt_tip': 'penumbral',
      'zaman': 1803165171,
      'ay': {'mutlak': 151.98, 'burc': 5, 'derece': 1.98},
      'gunes': {'mutlak': 332.08, 'burc': 11, 'derece': 2.08},
      'gorunurluk': {
        'gorunur': true,
        'yerel_tip': 'penumbral',
        'ortulme': null,
        'buyukluk': 0.93,
        'yerel_baslangic': 1803157944,
        'yerel_maksimum': 1803165171,
        'yerel_bitis': 1803172402,
        'saros': 143,
        'saros_uyesi': 18,
        'sonraki_gorunur': null,
      },
    });

    expect(event.visibility.visible, isTrue);
    expect(event.visibility.localStart, isNotNull);
    expect(event.visibility.localMaximum, isNotNull);
    expect(event.visibility.localEnd, isNotNull);
    expect(
      event.visibility.localStart!.isBefore(event.visibility.localMaximum!),
      isTrue,
    );
    expect(
      event.visibility.localMaximum!.isBefore(event.visibility.localEnd!),
      isTrue,
    );
    expect(event.visibility.saros, 143);
    expect(event.visibility.sarosMember, 18);
  });
}
