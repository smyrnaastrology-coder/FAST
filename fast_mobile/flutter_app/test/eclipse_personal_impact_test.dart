import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/models/chart_data.dart';
import 'package:fast_app/models/eclipse_personal_impact.dart';
import 'package:fast_app/models/sky_calendar.dart';

ChartData _natal() => ChartData(
  houseSystem: 'P',
  julianDay: 2451545,
  asc: const ChartAngle(lon: 0, sign: 0, degree: 0),
  mc: const ChartAngle(lon: 270, sign: 9, degree: 0),
  planets: const [
    PlanetPos(
      name: 'mars',
      lon: 105,
      sign: 3,
      degree: 15,
      house: 4,
      speed: 0.5,
      retrograde: false,
    ),
    PlanetPos(
      name: 'jupiter',
      lon: 75,
      sign: 2,
      degree: 15,
      house: 3,
      speed: 0.1,
      retrograde: false,
    ),
  ],
  houses: [
    for (var i = 0; i < 12; i++)
      HouseCusp(number: i + 1, lon: i * 30.0, sign: i, degree: 0),
  ],
  aspects: const [],
  meta: const ChartBody(
    name: 'Owner',
    date: '1990-01-01',
    time: '12:00',
    lat: 41,
    lng: 29,
  ),
);

SkyEclipse _solar() => SkyEclipse.fromJson({
  'tip': 'solar',
  'alt_tip': 'total',
  'zaman': 1800000000,
  'ay': {'mutlak': 15, 'burc': 0, 'derece': 15},
  'gunes': {'mutlak': 15, 'burc': 0, 'derece': 15},
  'gorunurluk': {'gorunur': false},
});

void main() {
  test('Tutulma kişisel etkisi kendi natal evini ve yakın açıları bulur', () {
    final impact = EclipsePersonalImpact.calculate(_solar(), _natal());

    expect(impact.house, 1);
    expect(impact.aspects, hasLength(2));
    expect(impact.aspects[0].planet, 'mars');
    expect(impact.aspects[0].type, 'square');
    expect(impact.aspects[0].orb, 0);
    expect(impact.aspects[1].planet, 'jupiter');
    expect(impact.aspects[1].type, 'sextile');
  });
}
