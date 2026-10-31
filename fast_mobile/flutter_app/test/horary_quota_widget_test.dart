import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/screens/horary_screen.dart';
import 'package:fast_app/services/horary_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  Future<void> showScreen(WidgetTester tester, {required bool pro}) async {
    SharedPreferences.setMockInitialValues({'holavon_horary_intro_shown': true});
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 2;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('en'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: HoraryScreen(quotaLoader: () async => HoraryResult(
        ok: true, data: {'remaining': 0, 'limit': 3, 'is_pro': pro},
      )),
    ));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Will this work?');
    await tester.tap(find.byIcon(Icons.arrow_upward));
    await tester.pumpAndSettle();
  }

  testWidgets('exhausted free users see the Pro offer', (tester) async {
    await showScreen(tester, pro: false);
    expect(find.textContaining("You've used your 3 free questions"), findsOneWidget);
    expect(find.descendant(of: find.byType(AlertDialog), matching: find.text('Go Pro')), findsOneWidget);
  });

  testWidgets('exhausted Pro users see the UTC reset and no upsell', (tester) async {
    await showScreen(tester, pro: true);
    expect(find.textContaining('Your allowance resets at 00:00 UTC'), findsOneWidget);
    expect(find.descendant(of: find.byType(AlertDialog), matching: find.text('Go Pro')), findsNothing);
  });

  testWidgets('unavailable quota service does not grant a question', (tester) async {
    SharedPreferences.setMockInitialValues({'holavon_horary_intro_shown': true});
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('en'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: HoraryScreen(quotaLoader: () async => const HoraryResult(ok: false)),
    ));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Will this work?');
    await tester.tap(find.byIcon(Icons.arrow_upward));
    await tester.pumpAndSettle();
    expect(find.textContaining('Could not check your question allowance'), findsWidgets);
    expect(find.byType(AlertDialog), findsNothing);
  });
}
