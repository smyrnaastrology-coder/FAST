import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:fast_app/config/theme.dart';
import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/providers/theme_provider.dart';
import 'package:fast_app/widgets/theme_palette_picker.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  tearDown(() async {
    final tp = ThemeProvider();
    await tp.setPalette('dark');
  });

  test('her palet kendi renklerini uygular', () async {
    final tp = ThemeProvider();
    expect(tp.palette, 'dark');
    expect(FastTheme.isDark, isTrue);
    expect(FastTheme.bg, FastTheme.darkBg);

    await tp.setPalette('spain');
    expect(tp.palette, 'spain');
    expect(FastTheme.bg, FastTheme.spainBg);
    expect(FastTheme.accentGold, FastTheme.spainAccentGold);

    await tp.setPalette('argentina');
    expect(FastTheme.isDark, isFalse);
    expect(FastTheme.bg, FastTheme.argBg);
    expect(FastTheme.accentGold, FastTheme.argAccentGold);

    await tp.setPalette('light');
    expect(FastTheme.bg, FastTheme.lightBg);

    await tp.setPalette('dark');
    expect(FastTheme.bg, FastTheme.darkBg);
  });

  test('seçilen palet geri yüklenir', () async {
    SharedPreferences.setMockInitialValues({'theme_palette': 'argentina'});
    final tp = ThemeProvider();
    await tp.restore();
    expect(tp.palette, 'argentina');
    expect(FastTheme.isDark, isFalse);
    expect(FastTheme.bg, FastTheme.argBg);
  });

  testWidgets('palet seçici 4 seçenek gösterir ve seçimi uygular', (tester) async {
    final tp = ThemeProvider();
    await tester.pumpWidget(
      ChangeNotifierProvider<ThemeProvider>.value(
        value: tp,
        child: MaterialApp(
          locale: const Locale('tr'),
          supportedLocales: const [Locale('tr'), Locale('en'), Locale('es')],
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const Scaffold(body: SingleChildScrollView(child: ThemePalettePicker())),
        ),
      ),
    );

    expect(find.text('Mor (Koyu)'), findsOneWidget);
    expect(find.text('Yumuşak Krem (Açık)'), findsOneWidget);
    expect(find.text('İspanya Kırmızısı (Koyu)'), findsOneWidget);
    expect(find.text('Arjantin Mavisi (Açık)'), findsOneWidget);

    await tester.tap(find.text('İspanya Kırmızısı (Koyu)'));
    await tester.pumpAndSettle();
    expect(tp.palette, 'spain');
    expect(FastTheme.bg, FastTheme.spainBg);
  });
}
