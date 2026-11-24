import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'config/api_config.dart';
import 'config/theme.dart';
import 'l10n/app_localizations.dart';
import 'providers/auth_provider.dart';
import 'providers/locale_provider.dart';
import 'providers/theme_provider.dart';
import 'screens/auth_screen.dart';
import 'screens/consult_home_screen.dart';
import 'screens/language_intro_screen.dart';
import 'services/notification_service.dart';
import 'services/push_service.dart';
import 'services/revenuecat_service.dart';
import 'widgets/splash_logo.dart';

/// Danışmanlık odaklı iOS giriş noktası.
///
/// Bilinçli olarak dar kapsamlıdır: günlük burç, doğum haritası araçları,
/// sosyal akış ve horary modülleri bu derlemeye **dahil edilmez**. Apple
/// incelemesinde uygulamanın kimliği "astroloji içeriği" değil, "gerçek bir
/// uzmandan 24 saat içinde yazılı danışmanlık" olarak okunmalıdır.
///
/// Derleme:
///   flutter build ipa -t lib/main_consult.dart \
///     --dart-define=SUPABASE_URL=... --dart-define=SUPABASE_ANON_KEY=... \
///     --dart-define=REVENUECAT_API_KEY=...
void main() {
  runZonedGuarded(
    () async {
      WidgetsFlutterBinding.ensureInitialized();

      if (ApiConfig.supabaseEnabled) {
        try {
          await Supabase.initialize(
            url: ApiConfig.supabaseUrl,
            publishableKey: ApiConfig.supabaseAnonKey,
          );
        } catch (e) {
          debugPrint('[Supabase] init error: $e');
        }
      }

      try {
        await Firebase.initializeApp();
      } catch (e) {
        debugPrint('[FCM] init error: $e');
      }

      await RevenueCatService.init();
      try {
        await NotificationService.instance.init();
      } catch (e) {
        debugPrint('[NOTIF] init error: $e');
      }
      try {
        await PushService.instance.init();
      } catch (e) {
        debugPrint('[PUSH] init error: $e');
      }

      runApp(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => ThemeProvider()),
            ChangeNotifierProvider(create: (_) => LocaleProvider()),
            ChangeNotifierProvider(create: (_) => AuthProvider()),
          ],
          child: const ConsultApp(),
        ),
      );
    },
    (error, stack) {
      debugPrint('[consult] uncaught: $error');
    },
  );
}

class ConsultApp extends StatelessWidget {
  const ConsultApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<LocaleProvider>(
      builder: (context, localeProvider, _) {
        return Consumer<ThemeProvider>(
          builder: (context, themeProvider, _) {
            return MaterialApp(
              key: ValueKey(
                'consult-${themeProvider.palette}-${themeProvider.mode}',
              ),
              title: 'Holavon Danışmanlık',
              debugShowCheckedModeBanner: false,
              theme: FastTheme.light,
              darkTheme: FastTheme.dark,
              themeMode: themeProvider.mode,
              locale: localeProvider.locale,
              supportedLocales: LocaleProvider.supportedLocales,
              localizationsDelegates: const [
                AppLocalizations.delegate,
                GlobalMaterialLocalizations.delegate,
                GlobalWidgetsLocalizations.delegate,
                GlobalCupertinoLocalizations.delegate,
              ],
              home: const ConsultGate(),
            );
          },
        );
      },
    );
  }
}

/// Açılış sırası: dil seçimi → giriş → danışmanlık ana ekranı.
class ConsultGate extends StatefulWidget {
  const ConsultGate({super.key});

  @override
  State<ConsultGate> createState() => _ConsultGateState();
}

class _ConsultGateState extends State<ConsultGate> {
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    await context.read<AuthProvider>().restore();
    if (!mounted) return;
    await context.read<ThemeProvider>().restore();
    if (!mounted) return;
    setState(() => _ready = true);
  }

  @override
  Widget build(BuildContext context) {
    final lp = context.watch<LocaleProvider>();
    final ap = context.watch<AuthProvider>();

    if (!_ready || !lp.ready) return const SplashLogo();
    if (!lp.hasChoice) return const LanguageIntroScreen();
    if (ap.status == AuthStatus.unknown) return const SplashLogo();
    if (ap.enabled && !ap.isLoggedIn) {
      return const AuthScreen(force: true, showOauth: false);
    }
    return const ConsultHomeScreen();
  }
}
