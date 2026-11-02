import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/chart_data.dart';
import 'package:fast_app/widgets/chart_wheel.dart';

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(body: Center(child: child)),
    );

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
    await tester.pumpWidget(_wrap(ChartWheel(data: data)));
    expect(find.byType(ChartWheel), findsOneWidget);
  });

  testWidgets('ChartWheel bi-wheel (transit dış) çizilir', (tester) async {
    final data = _sample();
    final outer = _sample().planets;
    await tester.pumpWidget(
      _wrap(
        ChartWheel(
          data: data,
          size: 340,
          outerPlanets: outer,
          outerHouses: data.houses,
        ),
      ),
    );
    expect(find.byType(ChartWheel), findsOneWidget);
  });

  testWidgets('Tüm gezegenler aynı burçta olsa da çizim bozulmaz', (
    tester,
  ) async {
    // Şartname §15: tüm gezegenler aynı burçta + birbirine çok yakın.
    final base = _sample();
    final crowded = <PlanetPos>[
      for (var i = 0; i < base.planets.length; i++)
        PlanetPos(
          name: base.planets[i].name,
          lon: 100.0 + i * 0.6,
          sign: 3,
          degree: 10.0 + i * 0.6,
          house: 1,
          speed: 1,
          retrograde: i.isOdd,
        ),
    ];
    final data = ChartData(
      houseSystem: base.houseSystem,
      julianDay: base.julianDay,
      asc: base.asc,
      mc: base.mc,
      planets: crowded,
      houses: base.houses,
      aspects: base.aspects,
      meta: base.meta,
    );

    await tester.pumpWidget(_wrap(ChartWheel(data: data, size: 320)));
    expect(find.byType(ChartWheel), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Çift çember yakın transit gezegenlerle çizilir', (tester) async {
    final data = _sample();
    final outer = <PlanetPos>[
      for (var i = 0; i < 6; i++)
        PlanetPos(
          name: data.planets[i].name,
          lon: 138.0 + i * 0.4,
          sign: 4,
          degree: 18.0 + i * 0.4,
          house: 1,
          speed: 1,
          retrograde: false,
        ),
    ];
    await tester.pumpWidget(
      _wrap(
        ChartWheel(
          data: data,
          size: 320,
          outerPlanets: outer,
          outerHouses: data.houses,
        ),
      ),
    );
    expect(find.byType(ChartWheel), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
