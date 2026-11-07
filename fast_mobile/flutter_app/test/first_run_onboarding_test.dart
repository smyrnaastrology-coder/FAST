import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/widgets/first_run_onboarding.dart';

Widget _host({
  required ValueChanged<String?> onStart,
  required VoidCallback onSkip,
  String lang = 'tr',
}) {
  return MaterialApp(
    locale: Locale(lang),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Builder(
      builder: (context) => Scaffold(
        body: Center(
          child: ElevatedButton(
            onPressed: () => showDialog<void>(
              context: context,
              barrierDismissible: false,
              builder: (_) => FirstRunOnboarding(
                onStart: onStart,
                onSkip: onSkip,
              ),
            ),
            child: const Text('open'),
          ),
        ),
      ),
    ),
  );
}

void main() {
  testWidgets('3 adım sonunda seçilen soruyla başlatır', (tester) async {
    String? started;
    await tester.pumpWidget(_host(onStart: (q) => started = q, onSkip: () {}));

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    expect(find.text("Holavon'a hoş geldin"), findsOneWidget);

    await tester.tap(find.text('Devam'));
    await tester.pumpAndSettle();
    expect(find.text('Nasıl çalışır?'), findsOneWidget);

    await tester.tap(find.text('Devam'));
    await tester.pumpAndSettle();
    expect(find.text('İlk sorunu seç'), findsOneWidget);

    await tester.tap(find.text('İşe girecek miyim?'));
    await tester.pumpAndSettle();
    expect(find.text('İlk sorumu sor'), findsOneWidget);

    await tester.tap(find.text('İlk sorumu sor'));
    await tester.pumpAndSettle();

    expect(started, 'İşe girecek miyim?');
    expect(find.text('İlk sorunu seç'), findsNothing);
  });

  testWidgets('soru seçilmezse kendi sorusunu yazma seçeneği sunar',
      (tester) async {
    String? started = 'unset';
    await tester.pumpWidget(_host(onStart: (q) => started = q, onSkip: () {}));

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Devam'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Devam'));
    await tester.pumpAndSettle();

    expect(find.text('Kendi sorumu yazacağım'), findsOneWidget);
    await tester.tap(find.text('Kendi sorumu yazacağım'));
    await tester.pumpAndSettle();
    expect(started, isNull);
  });

  testWidgets('şimdi değil akışı atlar', (tester) async {
    var skipped = false;
    await tester.pumpWidget(
      _host(onStart: (_) {}, onSkip: () => skipped = true),
    );

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Şimdi değil'));
    await tester.pumpAndSettle();

    expect(skipped, isTrue);
  });

  testWidgets('İngilizce metinler gösterilir', (tester) async {
    await tester.pumpWidget(
      _host(onStart: (_) {}, onSkip: () {}, lang: 'en'),
    );

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
    expect(find.text('Welcome to Holavon'), findsOneWidget);
    expect(find.text('Not now'), findsOneWidget);
  });
}
