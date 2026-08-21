import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'config/theme.dart';
import 'l10n/app_localizations.dart';
import 'providers/analysis_provider.dart';
import 'providers/locale_provider.dart';
import 'screens/landing_screen.dart';
import 'screens/language_intro_screen.dart';
import 'widgets/splash_logo.dart';

Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await Firebase.initializeApp();
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
    final messaging = FirebaseMessaging.instance;
    await messaging.requestPermission(alert: true, badge: true, sound: true);
    final token = await messaging.getToken();
    if (token != null) {
      // Token'ı backend'e bildirmek için sakla — abonelikte kullanılacak
      // ignore: avoid_print
      print('[FCM] token: $token');
    }
    // Token yenilenince
    FirebaseMessaging.instance.onTokenRefresh.listen((t) {
      // ignore: avoid_print
      print('[FCM] token refresh: $t');
    });
  } catch (e) {
    // ignore: avoid_print
    print('[FCM] init error: $e');
  }
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