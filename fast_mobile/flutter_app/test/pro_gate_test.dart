import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/services/pro_service.dart';
import 'package:fast_app/widgets/pro_gate.dart';

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
  testWidgets('Pro abone icerigi gorur', (tester) async {
    await tester.pumpWidget(
      _wrap(
        ProGate(
          icon: Icons.stars,
          title: 'Yildiz Muhurleri',
          body: 'Pro aboneligiyle acilir.',
          statusLoader: () async => true,
          child: const Text('gizli-icerik'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('gizli-icerik'), findsOneWidget);
    expect(find.text('Pro\'ya Geç'), findsNothing);
  });

  testWidgets('Pro olmayan kilit kartini gorur', (tester) async {
    await tester.pumpWidget(
      _wrap(
        ProGate(
          icon: Icons.stars,
          title: 'Yildiz Muhurleri',
          body: 'Pro aboneligiyle acilir.',
          statusLoader: () async => false,
          child: const Text('gizli-icerik'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('gizli-icerik'), findsNothing);
    expect(find.text('Yildiz Muhurleri'), findsOneWidget);
    expect(find.text('Pro aboneligiyle acilir.'), findsOneWidget);
    expect(find.text('Pro\'ya Geç'), findsOneWidget);
    expect(find.text('PRO'), findsOneWidget);
  });

  testWidgets('Paywalldan satin almadan donunce Pro icerik acilmaz', (
    tester,
  ) async {
    var checks = 0;
    await tester.pumpWidget(
      _wrap(
        ProGate(
          icon: Icons.stars,
          title: 'Ay özellikleri',
          body: 'Pro aboneliğiyle açılır.',
          // Simüle et: eski SDK/cache dönüşte true dese bile, satın alma
          // sonucu gelmediyse ProGate kilidi açmamalı.
          statusLoader: () async => ++checks > 1,
          paywallOpener: () async => null,
          child: const Text('gizli-ay-icerigi'),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('gizli-ay-icerigi'), findsNothing);

    await tester.tap(find.text('Pro\'ya Geç'));
    await tester.pumpAndSettle();

    expect(find.text('gizli-ay-icerigi'), findsNothing);
    expect(find.text('Ay özellikleri'), findsOneWidget);
    expect(find.text('Pro\'ya Geç'), findsOneWidget);
    expect(checks, 1, reason: 'iptal dönüşünde yetki sorgusu yapılmamalı');
  });

  testWidgets('Hesap degisince onceki Pro kapisi yeniden kilitlenir', (
    tester,
  ) async {
    var isPro = true;
    await tester.pumpWidget(
      _wrap(
        ProGate(
          icon: Icons.stars,
          title: 'Ay özellikleri',
          body: 'Pro aboneliğiyle açılır.',
          statusLoader: () async => isPro,
          child: const Text('gizli-ay-icerigi'),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('gizli-ay-icerigi'), findsOneWidget);

    isPro = false;
    ProService.invalidate();
    await tester.pumpAndSettle();

    expect(find.text('gizli-ay-icerigi'), findsNothing);
    expect(find.text('Ay özellikleri'), findsOneWidget);
    expect(find.text('Pro\'ya Geç'), findsOneWidget);
  });

  testWidgets('section modunda SectionCard basligi kullanilir', (tester) async {
    await tester.pumpWidget(
      _wrap(
        ProGate(
          section: true,
          icon: Icons.stars,
          title: 'Yildiz Muhurleri',
          body: 'Pro aboneligiyle acilir.',
          statusLoader: () async => false,
          child: const Text('gizli-icerik'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('gizli-icerik'), findsNothing);
    expect(find.text('Yildiz Muhurleri'), findsOneWidget);
    expect(find.text('PRO'), findsNothing);

    // SectionCard kapalıyken gövde gizli; başlığa dokununca kilit görünür.
    await tester.tap(find.text('Yildiz Muhurleri'));
    await tester.pumpAndSettle();
    expect(find.text('Pro\'ya Geç'), findsOneWidget);
  });
}
