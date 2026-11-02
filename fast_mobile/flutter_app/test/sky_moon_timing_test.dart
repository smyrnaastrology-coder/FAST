import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/sky_moon_timing.dart';
import 'package:fast_app/widgets/moon_timing_card.dart';

int _epoch(DateTime t) => t.millisecondsSinceEpoch ~/ 1000;

Map<String, dynamic> _json(DateTime now) => {
  'ok': true,
  'sunucu_zamani': _epoch(now),
  'ay': {
    'mutlak': 137.5,
    'burc': 4,
    'derece': 17.5,
    'bos': false,
    'bos_baslangic': null,
    'bos_bitis': null,
  },
  'bosluklar': [
    {
      'baslangic': _epoch(now.add(const Duration(hours: 3))),
      'bitis': _epoch(now.add(const Duration(hours: 7))),
      'burc': 5,
    },
    {
      'baslangic': _epoch(now.add(const Duration(days: 2))),
      'bitis': _epoch(now.add(const Duration(days: 2, hours: 4))),
      'burc': 6,
    },
  ],
  'pencereler': {
    'hair_growth': [
      {
        'baslangic': _epoch(now.add(const Duration(days: 3))),
        'bitis': _epoch(now.add(const Duration(days: 3, hours: 5))),
        'burc': 5,
        'evre': 'waxing',
      },
    ],
    'trade': [
      {
        'baslangic': _epoch(now.add(const Duration(days: 4))),
        'bitis': _epoch(now.add(const Duration(days: 4, hours: 6))),
        'burc': 2,
        'evre': 'waxing',
      },
    ],
  },
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
  test('SkyMoonTiming JSON alanlarını doğru çözer', () {
    final now = DateTime.now();
    final timing = SkyMoonTiming.fromJson(_json(now));

    expect(timing.sign, 4);
    expect(timing.degree, 17.5);
    expect(timing.voidNow, isFalse);
    expect(timing.voids, hasLength(2));
    expect(timing.voids.first.sign, 5);
    expect(timing.activities['hair_growth'], hasLength(1));
    expect(timing.activities['trade']!.first.sign, 2);
    expect(timing.activities['trade']!.first.waxing, isTrue);
  });

  testWidgets('VOC kartı anlam açıklaması ve pencereleri gösterir', (
    tester,
  ) async {
    final timing = SkyMoonTiming.fromJson(_json(DateTime.now()));
    await tester.pumpWidget(
      _wrap(
        MoonTimingCard(
          timing: timing,
          onExport: (time, title, description) async {},
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text("Ay'ın Boşta Olduğu Anlar"), findsOneWidget);
    expect(find.text('Sonraki boşluklar'), findsOneWidget);
    expect(find.text('Doğru zaman pencereleri'), findsOneWidget);
    // Seçili eylemin "ne işe yarar" açıklaması görünür.
    expect(find.textContaining('daha hızlı uzadığı'), findsOneWidget);

    // Ticaret sekmesine geçince açıklama da değişir.
    await tester.ensureVisible(find.text('Ticaret'));
    await tester.tap(find.text('Ticaret'));
    await tester.pumpAndSettle();
    expect(find.textContaining('pazarlık'), findsOneWidget);
    expect(find.textContaining('Merkür burçlarında'), findsOneWidget);
  });
}
