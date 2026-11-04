import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/screens/horary_screen.dart';
import 'package:fast_app/services/horary_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  Future<void> showScreen(WidgetTester tester, {required bool pro, int credits = 0}) async {
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
        ok: true, data: {'remaining': 0, 'limit': 3, 'is_pro': pro, 'credits': credits},
      )),
    ));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Will this work?');
    await tester.tap(find.byIcon(Icons.arrow_upward));
    await tester.pumpAndSettle();
  }

  testWidgets('exhausted free users see both Pro and credit offers', (tester) async {
    await showScreen(tester, pro: false);
    expect(find.textContaining('Your free questions are used up'), findsOneWidget);
    expect(find.descendant(of: find.byType(AlertDialog), matching: find.text('Go Pro')), findsOneWidget);
    expect(find.descendant(of: find.byType(AlertDialog), matching: find.text('Buy credits')), findsOneWidget);
  });

  testWidgets('exhausted Pro users see the credit offer and UTC reset, not Pro', (tester) async {
    await showScreen(tester, pro: true);
    expect(find.textContaining('Your daily allowance resets at 00:00 UTC'), findsOneWidget);
    expect(find.descendant(of: find.byType(AlertDialog), matching: find.text('Go Pro')), findsNothing);
    expect(find.descendant(of: find.byType(AlertDialog), matching: find.text('Buy credits')), findsOneWidget);
    expect(find.descendant(of: find.byType(AlertDialog), matching: find.text('Continue tomorrow')), findsOneWidget);
    expect(find.descendant(of: find.byType(AlertDialog), matching: find.text('Purchased credits: 0')), findsOneWidget);
  });

  testWidgets('a purchased credit lets the question through without a dialog', (tester) async {
    await showScreen(tester, pro: true, credits: 1);
    expect(find.byType(AlertDialog), findsNothing);
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
