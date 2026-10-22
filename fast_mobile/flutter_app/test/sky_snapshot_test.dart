import 'package:flutter_test/flutter_test.dart';
import 'package:fast_app/models/sky_snapshot.dart';

void main() {
  test('sky yanÄ±tÄ± modele ve yerel saatlere Ã§evrilir', () {
    final snap = SkySnapshot.fromJson({
      'ay': {
        'burc': 11,
        'derece': 17.34,
        'mutlak': 347.3432,
        'hiz': 13.09,
        'hiz_durumu': 'normal',
      },
      'gunes': {'burc': 6, 'derece': 29.48, 'mutlak': 209.478},
      'faz': {'isim': 'waxing_gibbous', 'aydinlanma': 87.1, 'buyuyor': true},
      'boslukta': false,
      'bosluk_biter': 1792785212,
      'gezegen_saati': {
        'yonetici': 'venus',
        'sonraki': 'mercury',
        'index': 6,
        'gunduz': false,
        'baslangic': 1792701780,
        'bitis': 1792705731,
      },
      'acilar': [
        {'gezegen': 'mercury', 'tip': 'trine', 'orb': 3.5, 'uygulama': true},
      ],
      'retrolar': ['venus', 'saturn'],
    });

    expect(snap.moonSign, 11);
    expect(snap.moonDegree, closeTo(17.34, 0.001));
    expect(snap.moonSpeed, closeTo(13.09, 0.001));
    expect(snap.speedKey, 'normal');
    expect(snap.phaseKey, 'waxing_gibbous');
    expect(snap.illumination, closeTo(87.1, 0.001));
    expect(snap.waxing, isTrue);
    expect(snap.voidOfCourse, isFalse);
    expect(snap.voidUntil?.toUtc().year, 2026);
    expect(snap.hourRuler, 'venus');
    expect(snap.nextHourRuler, 'mercury');
    expect(snap.aspects.single.type, 'trine');
    expect(snap.aspects.single.applying, isTrue);
    expect(snap.retrogrades, ['venus', 'saturn']);
  });
}
