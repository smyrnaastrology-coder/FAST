import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/screens/sky_calendar_screen.dart';
import 'package:fast_app/services/api_service.dart';

int _epoch(DateTime t) => t.millisecondsSinceEpoch ~/ 1000;

Map<String, dynamic> _skyJson() => {
  'gunes': {'mutlak': 220.0, 'burc': 7, 'derece': 10.0},
  'ay': {
    'mutlak': 132.3,
    'burc': 4,
    'derece': 12.3,
    'hiz': 13.2,
    'hiz_durumu': 'normal',
  },
  'faz': {'isim': 'full', 'aydinlanma': 0.99, 'buyuyor': false},
  'boslukta': false,
  'acilar': [
    {
      'gezegen': 'jupiter',
      'tip': 'trine',
      'orb': 1.2,
      'uygulama': true,
    },
  ],
  'retrolar': <String>[],
};

class _FakeApi extends ApiService {
  final Map<String, dynamic> moon;

  _FakeApi(this.moon);

  @override
  Future<Map<String, dynamic>> skyCalendar({
    double lat = 41.0082,
    double lon = 28.9784,
    double? tz,
  }) async => {'ok': true, 'fazlar': [], 'tutulmalar': []};

  @override
  Future<Map<String, dynamic>> skyMoonCalendar({int days = 30}) async => moon;

  @override
  Future<Map<String, dynamic>> skyMoonTiming({int days = 30}) async =>
      _timingJson(DateTime.now());

  @override
  Future<Map<String, dynamic>> sky({
    double lat = 41.0082,
    double lon = 28.9784,
    double? tz,
  }) async => _skyJson();
}

Map<String, dynamic> _timingJson(DateTime now) => {
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
  ],
  'pencereler': {
    'hair_growth': [
      {
        'baslangic': _epoch(now.add(const Duration(days: 2))),
        'bitis': _epoch(now.add(const Duration(days: 2, hours: 5))),
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

void main() {
  testWidgets('Ay takvimi kartı burç, pencere ve geri sayımı gösterir', (
    tester,
  ) async {
    final now = DateTime.now();
    final fake = _FakeApi({
      'ok': true,
      'sunucu_zamani': _epoch(now),
      'ay': {
        'burc': 4, // Aslan
        'derece': 12.3,
        'giris': _epoch(now.subtract(const Duration(days: 1))),
        'cikis': _epoch(now.add(const Duration(days: 2, hours: 3))),
      },
      'girisler': [
        {
          'zaman': _epoch(now.add(const Duration(days: 2, hours: 3))),
          'burc': 5, // Başak
          'derece': 0.0,
        },
        {
          'zaman': _epoch(now.add(const Duration(days: 4, hours: 7))),
          'burc': 6, // Terazi
          'derece': 0.0,
        },
      ],
    });

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
        home: SkyCalendarScreen(api: fake, proLoader: () async => true),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Ay Takvimi'), findsOneWidget);
    expect(find.text('Bugünün Gökyüzü'), findsOneWidget);
    expect(find.textContaining('Aslan burcunda Ay'), findsOneWidget);
    expect(find.textContaining('Ay Aslan burcunda'), findsOneWidget);
    expect(find.textContaining('Kalan:'), findsOneWidget);
    expect(find.text('Sıradaki burç geçişleri'), findsOneWidget);
    expect(find.text('Ay Başak burcuna geçiyor'), findsOneWidget);
    expect(find.text('Ay Terazi burcuna geçiyor'), findsOneWidget);
    // VOC + doğru zaman pencereleri kartı (listenin altında olduğu için
    // görünür alana kaydırılır).
    final scrollable = find.byType(Scrollable).first;
    for (final label in [
      "Ay'ın Boşta Olduğu Anlar",
      'Sonraki boşluklar',
      'Doğru zaman pencereleri',
    ]) {
      await tester.scrollUntilVisible(
        find.text(label),
        250,
        scrollable: scrollable,
      );
      expect(find.text(label), findsOneWidget);
    }

    // Geri sayım zamanlayıcısını temizle.
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
  });

  testWidgets('Ay takvimi ucu hata verirse takvim çalışmaya devam eder', (
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
        home: SkyCalendarScreen(
          api: _FailingApi(),
          proLoader: () async => true,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Gökyüzü Takvimi'), findsOneWidget);
    expect(find.text('Ay Evreleri'), findsOneWidget);
    expect(find.text('Yaklaşan olay yok'), findsOneWidget);
  });

  testWidgets('Pro olmayan kullanıcı Ay Takvimi ve günlük yorumu göremez', (
    tester,
  ) async {
    final now = DateTime.now();
    final fake = _FakeApi({
      'ok': true,
      'sunucu_zamani': _epoch(now),
      'ay': {
        'burc': 4,
        'derece': 12.3,
        'giris': _epoch(now.subtract(const Duration(days: 1))),
        'cikis': _epoch(now.add(const Duration(days: 2, hours: 3))),
      },
      'girisler': <Map<String, dynamic>>[],
    });

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
        home: SkyCalendarScreen(api: fake, proLoader: () async => false),
      ),
    );
    await tester.pumpAndSettle();

    // Kilit kartları görünür, Pro'ya özel içerik çizilmez.
    expect(find.text('PRO'), findsNWidgets(3));
    expect(find.text('Pro\'ya Geç'), findsNWidgets(3));
    expect(find.textContaining('Ay Aslan burcunda'), findsNothing);
    expect(find.textContaining('Kalan:'), findsNothing);

    // Temel takvim (ücretsiz) hâlâ çalışır.
    expect(find.text('Gökyüzü Takvimi'), findsOneWidget);
  });
}

class _FailingApi extends ApiService {
  @override
  Future<Map<String, dynamic>> skyCalendar({
    double lat = 41.0082,
    double lon = 28.9784,
    double? tz,
  }) async => {'ok': true, 'fazlar': [], 'tutulmalar': []};

  @override
  Future<Map<String, dynamic>> skyMoonCalendar({int days = 30}) async =>
      throw Exception('not deployed');

  @override
  Future<Map<String, dynamic>> skyMoonTiming({int days = 30}) async =>
      throw Exception('not deployed');

  @override
  Future<Map<String, dynamic>> sky({
    double lat = 41.0082,
    double lon = 28.9784,
    double? tz,
  }) async => throw Exception('not deployed');
}
