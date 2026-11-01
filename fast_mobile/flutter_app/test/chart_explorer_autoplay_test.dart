import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/chart_data.dart';
import 'package:fast_app/models/chart_frame.dart';
import 'package:fast_app/screens/chart_explorer_screen.dart';

ChartData _chart() => ChartData(
  houseSystem: 'P',
  julianDay: 2447892.5,
  asc: const ChartAngle(lon: 138.0, sign: 4, degree: 18),
  mc: const ChartAngle(lon: 48.0, sign: 1, degree: 18),
  planets: [
    const PlanetPos(
      name: 'sun',
      lon: 100.0,
      sign: 3,
      degree: 10,
      house: 1,
      speed: 1,
      retrograde: false,
    ),
  ],
  houses: [
    for (var i = 0; i < 12; i++)
      HouseCusp(
        number: i + 1,
        lon: (138.0 + i * 30) % 360,
        sign: (i + 4) % 12,
        degree: 0,
      ),
  ],
  aspects: const [],
  meta: const ChartBody(
    name: 'Test',
    date: '1990-01-01',
    time: '12:00',
    lat: 41.0082,
    lng: 28.9784,
    tz: 3,
    place: 'İstanbul',
  ),
);

Widget _app(Widget child) => MaterialApp(
  locale: const Locale('tr'),
  localizationsDelegates: const [
    AppLocalizations.delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  supportedLocales: AppLocalizations.supportedLocales,
  home: child,
);

void main() {
  testWidgets('Oynat zamanı ilerletir, duraklat durdurur', (tester) async {
    var loads = 0;
    final start = DateTime(2026, 1, 1, 12);
    final frame = ChartFrame(data: _chart(), title: 'Harita');
    await tester.pumpWidget(
      _app(
        ChartExplorerScreen(
          initial: frame,
          initialDate: start,
          loadFrame: (date) async {
            loads++;
            return ChartFrame(data: _chart(), title: 'Harita');
          },
        ),
      ),
    );

    expect(find.text('01.01.2026 12:00'), findsOneWidget);
    await tester.tap(find.byIcon(Icons.play_circle_filled));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));
    await tester.pump();
    expect(loads, 1);
    expect(find.text('02.01.2026 12:00'), findsOneWidget);

    // Duraklat: yeni istek gelmemeli.
    await tester.tap(find.byIcon(Icons.pause_circle_filled));
    await tester.pump();
    await tester.pump(const Duration(seconds: 5));
    await tester.pump();
    expect(loads, 1);
    expect(find.text('02.01.2026 12:00'), findsOneWidget);

    // Zamanlayıcıyı temizle.
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
  });
}
