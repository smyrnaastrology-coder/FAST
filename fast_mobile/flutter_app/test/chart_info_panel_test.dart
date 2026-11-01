import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/chart_data.dart';
import 'package:fast_app/widgets/chart_info_panel.dart';
import 'package:fast_app/widgets/chart_wheel.dart';
import 'package:fast_app/widgets/chart_wheel_style.dart';

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

ChartData _chart({String name = 'Test', String date = '1990-01-01'}) {
  const names = ['sun', 'moon', 'mars'];
  return ChartData(
    houseSystem: 'P',
    julianDay: 2447892.5,
    asc: const ChartAngle(lon: 138.0, sign: 4, degree: 18),
    mc: const ChartAngle(lon: 48.0, sign: 1, degree: 18),
    planets: [
      for (var i = 0; i < names.length; i++)
        PlanetPos(
          name: names[i],
          lon: 100.0 + i * 40,
          sign: i,
          degree: 10.0 + i,
          house: i + 1,
          speed: 1,
          retrograde: i == 1,
        ),
    ],
    houses: [
      for (var i = 0; i < 12; i++)
        HouseCusp(
          number: i + 1,
          lon: (138.0 + i * 30) % 360,
          sign: (i + 4) % 12,
          degree: (i * 2.5) % 30,
        ),
    ],
    aspects: const [],
    meta: ChartBody(
      name: name,
      date: date,
      time: '12:00',
      lat: 41.0082,
      lng: 28.9784,
      tz: 3,
      place: 'İstanbul',
    ),
  );
}

void main() {
  testWidgets('ChartInfoPanel gerçek harita verisini gösterir', (tester) async {
    await tester.pumpWidget(
      _wrap(
        SizedBox(
          width: 240,
          child: ChartInfoPanel(
            data: _chart(),
            style: ChartWheelStyle.lightStyle,
            title: 'Doğum Haritası',
          ),
        ),
      ),
    );
    expect(find.text('Doğum Haritası'), findsOneWidget);
    expect(find.text('İstanbul'), findsOneWidget);
    expect(find.text('Yer merkezli'), findsOneWidget);
    expect(find.text('Tropikal zodyak'), findsOneWidget);
    expect(find.text('Placidus'), findsOneWidget);
    expect(find.text('Ortalama Ay Düşümü'), findsNothing);
    expect(find.text('Ortalama Ay Düğümü'), findsOneWidget);
    // Koordinat satırı gerçek enlem/boylamdan üretilir.
    expect(find.textContaining('41°N00′'), findsOneWidget);
  });

  testWidgets('Çift harita iki zodyak kuşağıyla taşmadan çizilir', (
    tester,
  ) async {
    final inner = _chart(name: 'Doğum');
    final outer = _chart(name: 'Transit', date: '2026-11-01');
    await tester.pumpWidget(
      _wrap(
        ChartWheel(
          data: inner,
          size: 340,
          outerPlanets: outer.planets,
          outerHouses: outer.houses,
          outerData: outer,
        ),
      ),
    );
    expect(find.byType(ChartWheel), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
