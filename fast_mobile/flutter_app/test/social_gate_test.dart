import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/providers/social_provider.dart';
import 'package:fast_app/screens/handle_claim_screen.dart';
import 'package:fast_app/widgets/social_gate.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Sosyal giriş hatasının kök nedeni: profil sorgusu tamamlanmadan
/// "profil oluştur" ekranına düşülmesi. Bu testler doğrulama yokken
/// yükleniyor/hata gösterildiğini garanti eder.
void main() {
  Future<void> pumpGate(
    WidgetTester tester, {
    required bool profileVerified,
    required bool hasHandle,
    SocialStatus status = SocialStatus.idle,
    Future<void> Function()? onRetry,
  }) async {
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: SocialGateView(
        enabled: true,
        signedIn: true,
        profileVerified: profileVerified,
        hasHandle: hasHandle,
        status: status,
        retryLabel: 'Tekrar dene',
        onRetry: onRetry,
      ),
    ));
    await tester.pump();
  }

  testWidgets('profil doğrulanmadan profil oluştur ekranı açılmaz',
      (tester) async {
    await pumpGate(tester, profileVerified: false, hasHandle: true);

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.byType(HandleClaimScreen), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('profil yok bilgisi kesinleşmeden talep ekranı gösterilmez',
      (tester) async {
    await pumpGate(tester, profileVerified: false, hasHandle: false);

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.byType(HandleClaimScreen), findsNothing);
  });

  testWidgets('sorgu hata verirse tekrar dene gösterilir ve çalışır',
      (tester) async {
    var retried = 0;
    await pumpGate(
      tester,
      profileVerified: false,
      hasHandle: true,
      status: SocialStatus.error,
      onRetry: () async => retried++,
    );

    expect(find.text('Tekrar dene'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    await tester.tap(find.text('Tekrar dene'));
    await tester.pumpAndSettle();
    expect(retried, 1);
  });
}
