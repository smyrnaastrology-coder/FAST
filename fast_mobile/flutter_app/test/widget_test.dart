import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:fast_app/main.dart';
import 'package:fast_app/providers/analysis_provider.dart';
import 'package:fast_app/providers/auth_provider.dart';
import 'package:fast_app/providers/locale_provider.dart';
import 'package:fast_app/providers/social_provider.dart';
import 'package:fast_app/providers/theme_provider.dart';

void main() {
  testWidgets('App builds without throwing', (WidgetTester tester) async {
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => LocaleProvider()),
          ChangeNotifierProvider(create: (_) => AnalysisProvider()),
          ChangeNotifierProvider(create: (_) => AuthProvider()),
          ChangeNotifierProvider(create: (_) => ThemeProvider()),
          ChangeNotifierProvider(create: (_) => SocialProvider()),
        ],
        child: const FastApp(),
      ),
    );
    await tester.pump();
    expect(tester.takeException(), isNull);
  });
}
