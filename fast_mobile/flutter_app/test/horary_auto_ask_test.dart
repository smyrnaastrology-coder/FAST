import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/screens/horary_screen.dart';
import 'package:fast_app/services/horary_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Otomatik gönderim yalnızca gerçek konum + kota hazırken çalışır.
void main() {
  Future<void> pumpHorary(
    WidgetTester tester, {
    required bool autoAsk,
    Future<({double lat, double lon})?> Function()? locationLoader,
    Future<HoraryResult> Function(String q, double lat, double lon)? castLoader,
  }) async {
    SharedPreferences.setMockInitialValues({
      'holavon_horary_intro_shown': true,
    });
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 2;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(MaterialApp(
      locale: const Locale('en'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: HoraryScreen(
        initialQuestion: 'Will I get the job?',
        skipIntro: true,
        autoAsk: autoAsk,
        locationLoader: locationLoader,
        castLoader: castLoader,
        quotaLoader: () async => const HoraryResult(
          ok: true,
          data: {'remaining': 3, 'limit': 3, 'is_pro': false, 'credits': 0},
        ),
      ),
    ));
    await tester.pumpAndSettle();
  }

  testWidgets('konum ve kota hazırsa ilk soruyu kendiliğinden gönderir',
      (tester) async {
    var casts = 0;
    await pumpHorary(
      tester,
      autoAsk: true,
      locationLoader: () async => (lat: 41.0, lon: 29.0),
      castLoader: (q, lat, lon) async {
        casts++;
        return const HoraryResult(
          ok: true,
          data: {
            'verdict': 'YES',
            'answer': 'Yes, soon.',
            'remaining': 2,
            'limit': 3,
            'is_pro': false,
            'credits': 0,
          },
        );
      },
    );

    expect(casts, 1);
    expect(find.text('Yes, soon.'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('konum yoksa otomatik göndermez, soruyu kutuya bırakır',
      (tester) async {
    var casts = 0;
    await pumpHorary(
      tester,
      autoAsk: true,
      locationLoader: () async => null,
      castLoader: (q, lat, lon) async {
        casts++;
        return const HoraryResult(ok: true, data: {'answer': 'x'});
      },
    );

    expect(casts, 0);
    expect(find.text('Will I get the job?'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('autoAsk kapalıyken de soru kutuya yazılır', (tester) async {
    var casts = 0;
    await pumpHorary(
      tester,
      autoAsk: false,
      locationLoader: () async => (lat: 41.0, lon: 29.0),
      castLoader: (q, lat, lon) async {
        casts++;
        return const HoraryResult(ok: true, data: {'answer': 'x'});
      },
    );

    expect(casts, 0);
    expect(find.text('Will I get the job?'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
