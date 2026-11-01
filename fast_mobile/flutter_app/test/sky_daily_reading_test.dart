import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/sky_snapshot.dart';
import 'package:fast_app/services/sky_daily_reading.dart';
import 'package:fast_app/widgets/sky_daily_reading_card.dart';

SkySnapshot _snapshot({
  double moonLongitude = 132.3,
  String phase = 'full',
  List<SkyAspect> aspects = const [],
  bool voidOfCourse = false,
  String speed = 'normal',
  List<String> retrogrades = const [],
}) => SkySnapshot.fromJson({
  'gunes': {'mutlak': 220.0, 'burc': 7, 'derece': 10.0},
  'ay': {
    'mutlak': moonLongitude,
    'burc': (moonLongitude ~/ 30) % 12,
    'derece': moonLongitude % 30,
    'hiz': 13.2,
    'hiz_durumu': speed,
  },
  'faz': {'isim': phase, 'aydinlanma': 0.99, 'buyuyor': false},
  'boslukta': voidOfCourse,
  'acilar': [
    for (final a in aspects)
      {
        'gezegen': a.planet,
        'tip': a.type,
        'orb': a.orb,
        'uygulama': a.applying,
      },
  ],
  'retrolar': retrogrades,
});

SkyAspect _aspect(String planet, String type, double orb) =>
    SkyAspect.fromJson({'gezegen': planet, 'tip': type, 'orb': orb});

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('en küçük orblu açı günün en güçlü açısı seçilir', () {
    final aspects = [
      _aspect('mars', 'square', 2.4),
      _aspect('jupiter', 'trine', 0.8),
      _aspect('saturn', 'opposition', 1.6),
    ];
    expect(strongestAspect(aspects)?.planet, 'jupiter');
    expect(strongestAspect(const []), isNull);
  });

  test('Türkçe yorum Ay burcu, faz, açı, boşluk, hız ve retroyu birleştirir',
      () async {
    final l = await AppLocalizations.delegate.load(const Locale('tr'));
    final reading = buildSkyDailyReading(
      sky: _snapshot(
        aspects: [
          _aspect('jupiter', 'trine', 0.8),
          _aspect('mars', 'square', 2.4),
        ],
        voidOfCourse: true,
        speed: 'slow',
        retrogrades: ['mercury', 'saturn'],
      ),
      l: l,
      lang: 'tr',
    );

    expect(reading.headline, contains('Aslan'));
    expect(reading.headline, contains('görünür olma'));
    expect(reading.body.first, contains('Kendini ifade etmekten'));
    expect(reading.body, contains(contains('Dolunay')));
    // Yalnızca en güçlü açı anlatılır.
    expect(reading.body, contains(contains('Jüpiter')));
    expect(reading.body.join(' '), isNot(contains('Mars')));
    expect(reading.body, contains(contains('Ay boşlukta')));
    expect(reading.body, contains(contains('yavaş')));
    expect(reading.body.join(' '), contains('Retro gezegenler: Merkür, Satürn'));
    expect(reading.chips, contains('Aslan'));
    expect(reading.chips, contains('Dolunay'));
    expect(reading.chips, contains('üçgen'));
    expect(reading.chips, contains('Ay boşlukta'));
    expect(reading.glyph, '🌕');
  });

  test('İngilizce ve İspanyolca yorumlar tamamen çevrilir', () async {
    final en = await AppLocalizations.delegate.load(const Locale('en'));
    final es = await AppLocalizations.delegate.load(const Locale('es'));

    final enReading = buildSkyDailyReading(
      sky: _snapshot(aspects: [_aspect('jupiter', 'trine', 0.8)]),
      l: en,
      lang: 'en',
    );
    final esReading = buildSkyDailyReading(
      sky: _snapshot(aspects: [_aspect('jupiter', 'trine', 0.8)]),
      l: es,
      lang: 'es',
    );

    expect(enReading.headline, startsWith('Moon in '));
    expect(enReading.body.first, startsWith("Don't hold back"));
    expect(enReading.body, contains(contains('Full Moon')));
    expect(enReading.body, contains(contains('Moon–Jupiter trine')));

    expect(esReading.headline, startsWith('Luna en '));
    expect(esReading.body.first, startsWith('No te frenes'));
    expect(esReading.body, contains(contains('Luna Llena')));
    expect(esReading.body, contains(contains('Luna–Júpiter trígono')));

    // Diller birbirine karışmamalı.
    expect(enReading.body.join(' '), isNot(contains('Dolunay')));
    expect(esReading.body.join(' '), isNot(contains('Dolunay')));
  });

  testWidgets('Günün yorumu kartı başlık, cümleler ve etiketleri çizer', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('tr'),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        home: Scaffold(
          body: SingleChildScrollView(
            child: SkyDailyReadingCard(
              sky: _snapshot(
                aspects: [_aspect('jupiter', 'trine', 0.8)],
              ),
            ),
          ),
        ),
      ),
    );

    expect(find.text('Bugünün Gökyüzü'), findsOneWidget);
    expect(find.textContaining('Aslan burcunda Ay'), findsOneWidget);
    expect(
      find.textContaining('Ay ile Jüpiter arasındaki üçgen'),
      findsOneWidget,
    );
    expect(find.text('Dolunay'), findsWidgets);
    expect(find.text('üçgen'), findsOneWidget);
    expect(find.text('Aslan'), findsOneWidget);
  });
}
