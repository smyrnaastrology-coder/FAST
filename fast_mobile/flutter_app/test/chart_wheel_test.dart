import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/models/chart_data.dart';
import 'package:fast_app/widgets/chart_wheel.dart';

ChartData _sample() {
  const meta = ChartBody(
    name: 'Test',
    date: '1990-01-01',
    time: '12:00',
    lat: 41.0082,
    lng: 28.9784,
    place: 'İstanbul',
  );
  const names = [
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
  final planets = <PlanetPos>[
    for (var i = 0; i < 12; i++)
      PlanetPos(
        name: names[i],
        lon: (i * 29.5) % 360,
        sign: i % 12,
        degree: (i * 3.1) % 30,
        house: i + 1,
        speed: i.isEven ? 1.0 : -1.0,
        retrograde: i.isOdd,
      ),
  ];
  final houses = <HouseCusp>[
    for (var i = 0; i < 12; i++)
      HouseCusp(
        number: i + 1,
        lon: (138.0 + i * 30) % 360,
        sign: (i + 4) % 12,
        degree: (i * 2.5) % 30,
      ),
  ];
  return ChartData(
    houseSystem: 'P',
    julianDay: 2447892.5,
    asc: const ChartAngle(lon: 138.0, sign: 4, degree: 18),
    mc: const ChartAngle(lon: 48.0, sign: 1, degree: 18),
    planets: planets,
    houses: houses,
    aspects: const [
      ChartAspect(p1: 'sun', p2: 'moon', type: 'trine', orb: 1.2),
      ChartAspect(p1: 'mars', p2: 'venus', type: 'square', orb: 3.4),
      ChartAspect(p1: 'jupiter', p2: 'saturn', type: 'opposition', orb: 2.0),
    ],
    meta: meta,
  );
}

void main() {
  testWidgets('ChartWheel natal çizilir', (tester) async {
    final data = _sample();
    await tester.pumpWidget(
      MaterialApp(home: Scaffold(body: Center(child: ChartWheel(data: data)))),
    );
    expect(find.byType(ChartWheel), findsOneWidget);
  });

  testWidgets('ChartWheel bi-wheel (transit dış) çizilir', (tester) async {
    final data = _sample();
    final outer = _sample().planets;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Center(
            child: ChartWheel(
              data: data,
              size: 340,
              outerPlanets: outer,
              outerHouses: data.houses,
            ),
          ),
        ),
      ),
    );
    expect(find.byType(ChartWheel), findsOneWidget);
  });
}
