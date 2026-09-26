import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'config/api_config.dart';
import 'config/theme.dart';
import 'l10n/app_localizations.dart';
import 'providers/analysis_provider.dart';
import 'providers/auth_provider.dart';
import 'providers/locale_provider.dart';
import 'providers/theme_provider.dart';
import 'screens/landing_screen.dart';
import 'screens/language_intro_screen.dart';
import 'screens/warning_screen.dart';
import 'services/revenuecat_service.dart';
import 'services/notification_service.dart';
import 'widgets/splash_logo.dart';

Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

/// Günlük minör progress bildirimini abonelere özel zamanlar.
Future<void> _scheduleDailyIfSubscribed() async {
  try {
    final isSub = await RevenueCatService.isSubscribed();
    if (!isSub) return;
    await NotificationService.instance
        .scheduleDaily(9, 0, title: 'Fast Synastry', body: 'Günlük minör ilerleme akışını keşfet 🌟');
  } catch (_) {}
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (ApiConfig.supabaseEnabled) {
    try {
      await Supabase.initialize(
        url: ApiConfig.supabaseUrl,
        publishableKey: ApiConfig.supabaseAnonKey,
      );
    } catch (e) {
      // ignore: avoid_print
      print('[Supabase] init error: $e');
    }
  }
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
  await RevenueCatService.init();
  await NotificationService.instance.init();
  _scheduleDailyIfSubscribed();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => LocaleProvider()),
        ChangeNotifierProvider(create: (_) => AnalysisProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
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
        return Consumer<ThemeProvider>(
          builder: (context, themeProvider, _) {
            return MaterialApp(
              key: ValueKey('theme-${themeProvider.mode}'),
              title: 'Fast Synastry',
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
              home: const StartupGate(),
            );
          },
        );
      },
    );
  }
}

/// Uygulama açılışında sırayla: dil seçimi → uyarı ekranı → ana sayfa.
class StartupGate extends StatefulWidget {
  const StartupGate({super.key});

  @override
  State<StartupGate> createState() => _StartupGateState();
}

class _StartupGateState extends State<StartupGate> {
  bool _warningAccepted = true;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final ap = context.read<AuthProvider>();
    await ap.restore();
    final tp = context.read<ThemeProvider>();
    await tp.restore();
    var accepted = true;
    try {
      final prefs = await SharedPreferences.getInstance();
      accepted = prefs.getBool(WarningScreen.prefKey) ?? false;
    } catch (_) {}
    if (!mounted) return;
    setState(() => _warningAccepted = accepted);
  }

  Widget _decideHome(LocaleProvider lp) {
    if (!lp.ready) return const SplashLogo();
    if (!lp.hasChoice) return const LanguageIntroScreen();
    if (!_warningAccepted) return WarningScreen(onAccepted: () => setState(() => _warningAccepted = true));
    return const LandingScreen();
  }

  @override
  Widget build(BuildContext context) {
    final lp = context.watch<LocaleProvider>();
    return _decideHome(lp);
  }
}