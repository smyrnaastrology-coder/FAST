import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'config/theme.dart';
import 'l10n/app_localizations.dart';
import 'providers/analysis_provider.dart';
import 'providers/locale_provider.dart';
import 'screens/landing_screen.dart';
import 'screens/language_intro_screen.dart';
import 'widgets/splash_logo.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => LocaleProvider()),
        ChangeNotifierProvider(create: (_) => AnalysisProvider()),
      ],
      child: const FastApp(),
    ),
  );
}

class FastApp extends StatelessWidget {
  const FastApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<LocaleProvider>(
      builder: (context, localeProvider, _) {
        return MaterialApp(
          title: 'FAST',
          debugShowCheckedModeBanner: false,
          theme: FastTheme.dark,
          locale: localeProvider.locale,
          supportedLocales: LocaleProvider.supportedLocales,
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: _decideHome(localeProvider),
        );
      },
    );
  }

  Widget _decideHome(LocaleProvider lp) {
    if (!lp.ready) return const SplashLogo();
    if (!lp.hasChoice) return const LanguageIntroScreen();
    return const LandingScreen();
  }
}