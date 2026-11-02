import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/moon_mansion_content.dart';
import 'package:fast_app/models/sky_moon_guide.dart';
import 'package:fast_app/widgets/moon_guide_card.dart';

int _epoch(DateTime time) => time.millisecondsSinceEpoch ~/ 1000;

Map<String, dynamic> _json(DateTime now) => {
  'ok': true,
  'sunucu_zamani': _epoch(now),
  'gun': 30,
  'menzil_modeli': 'lahiri_equal_28',
  'menzil': {
    'sira': 3,
    'baslangic': _epoch(now.subtract(const Duration(hours: 8))),
    'bitis': _epoch(now.add(const Duration(hours: 16))),
    'derece': 6.2,
    'ilerleme': 48.3,
  },
  'faz': {
    'faz': 'waxing_crescent',
    'aydinlanma': 28.4,
    'buyuyor': true,
    'baslangic': _epoch(now.subtract(const Duration(days: 1))),
    'bitis': _epoch(now.add(const Duration(days: 2))),
  },
  'menzil_gecisleri': [
    {'zaman': _epoch(now.add(const Duration(hours: 16))), 'menzil': 4},
    {'zaman': _epoch(now.add(const Duration(days: 1, hours: 15))), 'menzil': 5},
  ],
};

Widget _wrap(Widget child, Locale locale) => MaterialApp(
  locale: locale,
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
  test('Ay rehberi faz, menzil ve geçişleri çözer', () {
    final now = DateTime.now();
    final guide = SkyMoonGuide.fromJson(_json(now));

    expect(guide.days, 30);
    expect(guide.mansion.number, 3);
    expect(guide.mansion.progress, 48.3);
    expect(guide.phase.phase, 'waxing_crescent');
    expect(guide.phase.illumination, 28.4);
    expect(guide.phase.waxing, isTrue);
    expect(guide.transitions.map((e) => e.number), [4, 5]);
    expect(MoonMansionContent.names, hasLength(28));
    for (final language in ['tr', 'en', 'es']) {
      for (var n = 1; n <= 28; n++) {
        expect(MoonMansionContent.prompt(n, language), isNotEmpty);
      }
    }
  });

  for (final locale in const [Locale('tr'), Locale('en'), Locale('es')]) {
    testWidgets('Ay Rehberi ${locale.languageCode} dilinde çizilir', (
      tester,
    ) async {
      final guide = SkyMoonGuide.fromJson(_json(DateTime.now()));
      await tester.pumpWidget(_wrap(MoonGuideCard(guide: guide), locale));

      expect(find.textContaining('Ath-Thurayya'), findsOneWidget);
      final phaseLabel = switch (locale.languageCode) {
        'en' => 'Moon phase',
        'es' => 'Fase lunar',
        _ => 'Ay fazı',
      };
      final mansionLabel = switch (locale.languageCode) {
        'en' => 'Lunar mansion',
        'es' => 'Mansión lunar',
        _ => 'Ay menzili',
      };
      expect(find.text(phaseLabel), findsOneWidget);
      expect(find.text(mansionLabel), findsOneWidget);
      expect(find.byType(LinearProgressIndicator), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
}
