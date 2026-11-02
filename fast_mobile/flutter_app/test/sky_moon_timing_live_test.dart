import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/sky_moon_timing.dart';
import 'package:fast_app/widgets/moon_timing_card.dart';

/// Canlı `GET /api/sky/moon-timing?days=30` yanıtının birebir kopyası.
/// Amaç: backend sözleşmesi ile istemci modeli/kartı arasındaki uyumu
/// gerçek bir yanıt üzerinden doğrulamak (ağ erişimi olmadan).
Map<String, dynamic> _live() {
  final raw = File('test/fixtures/live_moon_timing.json').readAsStringSync();
  return jsonDecode(raw) as Map<String, dynamic>;
}

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
  test('Canlı yanıt modele kayıpsız çözülür', () {
    final timing = SkyMoonTiming.fromJson(_live());

    // Üst durum bloğu.
    expect(timing.sign, 4);
    expect(timing.degree, 17.75);
    expect(timing.voidNow, isFalse);

    // 8 eylemin tamamı gelir.
    expect(
      timing.activities.keys.toSet(),
      {
        'hair_growth',
        'hair_thicken',
        'trade',
        'education',
        'contract',
        'wedding',
        'moving',
        'planting',
      },
    );

    // Her pencere tutarlı: bitiş başlangıçtan sonra, burç 0..11.
    for (final entry in timing.activities.entries) {
      for (final w in entry.value) {
        expect(w.end.isAfter(w.start), isTrue, reason: entry.key);
        expect(w.sign, inInclusiveRange(0, 11), reason: entry.key);
      }
    }

    // VOC boşlukları da tutarlı.
    expect(timing.voids, isNotEmpty);
    for (final v in timing.voids) {
      expect(v.end.isAfter(v.start), isTrue);
    }
  });

  testWidgets('Canlı yanıtla kart hatasız çizilir', (tester) async {
    final timing = SkyMoonTiming.fromJson(_live());
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
    expect(find.text('Doğru zaman pencereleri'), findsOneWidget);
    // Eylem çiplerinin hepsi mevcut.
    for (final label in [
      'Saç uzatma',
      'Saç gürleştirme',
      'Ticaret',
      'Eğitim',
      'İmza',
      'Düğün',
      'Taşınma',
      'Ekim',
    ]) {
      expect(find.text(label), findsOneWidget, reason: label);
    }
    expect(tester.takeException(), isNull);
  });
}
