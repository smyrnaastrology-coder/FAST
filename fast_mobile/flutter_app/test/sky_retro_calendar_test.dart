import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/sky_retro_calendar.dart';
import 'package:fast_app/widgets/retro_calendar_card.dart';

Map<String, dynamic> _json(DateTime now) => {
  'ok': true,
  'sunucu_zamani': now.millisecondsSinceEpoch ~/ 1000,
  'gun': 365,
  'donemler': [
    {
      'gezegen': 'mercury',
      'golge_baslangic':
          (now.add(const Duration(days: 2)).millisecondsSinceEpoch ~/ 1000),
      'retro_baslangic':
          (now.add(const Duration(days: 10)).millisecondsSinceEpoch ~/ 1000),
      'direkt_durak':
          (now.add(const Duration(days: 31)).millisecondsSinceEpoch ~/ 1000),
      'golge_bitis':
          (now.add(const Duration(days: 40)).millisecondsSinceEpoch ~/ 1000),
      'retro_burcu': 0,
      'retro_derece': 24.5,
      'aktif': false,
      'golgede': false,
    },
  ],
};

Widget _wrap(Widget child) => MaterialApp(
  locale: const Locale('tr'),
  localizationsDelegates: const [
    AppLocalizations.delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(body: SingleChildScrollView(child: child)),
);

void main() {
  test('Retro takvimi istasyon ve gölge alanlarını çözer', () {
    final now = DateTime.now();
    final calendar = SkyRetroCalendar.fromJson(_json(now));
    final period = calendar.periods.single;

    expect(calendar.days, 365);
    expect(period.planet, 'mercury');
    expect(
      period.shadowStart!
          .difference(now.add(const Duration(days: 2)))
          .inSeconds
          .abs(),
      lessThanOrEqualTo(1),
    );
    expect(
      period.retroStart
          .difference(now.add(const Duration(days: 10)))
          .inSeconds
          .abs(),
      lessThanOrEqualTo(1),
    );
    expect(
      period.directStation
          .difference(now.add(const Duration(days: 31)))
          .inSeconds
          .abs(),
      lessThanOrEqualTo(1),
    );
    expect(
      period.shadowEnd!
          .difference(now.add(const Duration(days: 40)))
          .inSeconds
          .abs(),
      lessThanOrEqualTo(1),
    );
    expect(period.sign, 0);
    expect(period.degree, 24.5);
    expect(period.active, isFalse);
  });

  testWidgets('Retro kartı tarihleri ve somut gözden geçirme notunu gösterir', (
    tester,
  ) async {
    final calendar = SkyRetroCalendar.fromJson(_json(DateTime.now()));
    await tester.pumpWidget(_wrap(RetroCalendarCard(calendar: calendar)));

    expect(find.text('Merkür'), findsOneWidget);
    expect(find.textContaining('Gölge başlangıcı'), findsOneWidget);
    expect(find.textContaining('Retro başlıyor'), findsOneWidget);
    expect(find.textContaining('Direkt durak'), findsOneWidget);
    expect(find.textContaining('Gölge bitişi'), findsOneWidget);
    expect(find.text('Durağan derece: 24.5° Koç'), findsOneWidget);
    expect(find.textContaining('yedekle'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
