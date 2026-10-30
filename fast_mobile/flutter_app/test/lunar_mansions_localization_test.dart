import 'package:fast_app/config/lunar_mansions.dart';
import 'package:fast_app/config/lunar_mansions_localized.dart';
import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/sky_snapshot.dart';
import 'package:fast_app/widgets/sky_strip.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('all 28 mansions have English and Spanish descriptions', () {
    expect(lunarMansions, hasLength(28));
    for (final original in lunarMansions) {
      for (final lang in ['en', 'es']) {
        final localized = localizedLunarMansion(original, lang);
        expect(localized.index, original.index);
        expect(localized.name, original.name);
        expect(localized.meaning, isNot(original.meaning));
        expect(localized.doText, isNot(original.doText));
        expect(localized.avoidText, isNot(original.avoidText));
      }
      expect(localizedLunarMansion(original, 'tr'), same(original));
    }
  });

  testWidgets('moon details use the selected language', (tester) async {
    final sky = SkySnapshot.fromJson({
      'ay': {'burc': 6, 'derece': 20.0, 'mutlak': 200.0, 'hiz': 13.0},
      'gunes': {'burc': 0, 'derece': 1.0},
      'faz': {'isim': 'full', 'aydinlanma': 100.0},
      'gezegen_saati': {'yonetici': 'sun', 'sonraki': 'venus'},
    });
    for (final example in [
      ('en', 'Via Combusta', 'Lunar mansion: El-İklil', 'The crown', 'Do:', 'Avoid:'),
      ('es', 'Vía Combusta', 'Mansión lunar: El-İklil', 'La corona', 'Hacer:', 'Evitar:'),
      ('tr', 'Yanık yol', 'Menzil: El-İklil', 'Taç', 'Yap:', 'Kaçın:'),
    ]) {
      await tester.pumpWidget(MaterialApp(
        locale: Locale(example.$1),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(body: SkyDetailSheet(sky: sky)),
      ));
      await tester.pumpAndSettle();
      expect(find.text(example.$2), findsOneWidget);
      expect(find.text(example.$3), findsOneWidget);
      expect(find.text(example.$4), findsOneWidget);
      expect(find.textContaining(example.$5), findsOneWidget);
      expect(find.textContaining(example.$6), findsOneWidget);
      expect(tester.takeException(), isNull);
    }
  });
}
