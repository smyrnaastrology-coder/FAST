import 'dart:async';
import 'package:app_links/app_links.dart';
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
import 'providers/social_provider.dart';
import 'providers/chart_provider.dart';
import 'providers/theme_provider.dart';
import 'screens/auth_screen.dart';
import 'screens/language_intro_screen.dart';
import 'screens/main_shell.dart';
import 'screens/social_profile_screen.dart';
import 'screens/warning_screen.dart';
import 'services/revenuecat_service.dart';
import 'services/notification_service.dart';
import 'services/profile_links.dart';
import 'widgets/splash_logo.dart';

final GlobalKey<NavigatorState> rootNavigatorKey = GlobalKey<NavigatorState>();

Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

/// Günlük kısa vadeli ilerleme bildirimini abonelere özel zamanlar.
Future<void> _scheduleDailyIfSubscribed() async {
  try {
    final isSub = await RevenueCatService.isSubscribed();
    if (!isSub) return;
    await NotificationService.instance
        .scheduleDaily(9, 0, title: 'Holavon', body: 'Günlük kısa vadeli ilerleme akışını keşfet 🌟');
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
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
        ChangeNotifierProvider(create: (_) => LocaleProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => SocialProvider()),
        ChangeNotifierProvider(create: (_) => ChartProvider()),
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
        return Consumer<ThemeProvider>(
          builder: (context, themeProvider, _) {
            return MaterialApp(
              navigatorKey: rootNavigatorKey,
              key: ValueKey('theme-${themeProvider.palette}-${themeProvider.mode}'),
              title: 'Holavon',
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
  bool _startupReady = false;
  StreamSubscription<Uri>? _profileLinks;
  String? _pendingProfile;
  String? _lastProfile;
  DateTime? _lastProfileAt;

  @override
  void initState() {
    super.initState();
    _init();
    _listenProfileLinks();
  }

  Future<void> _listenProfileLinks() async {
    try {
      final links = AppLinks();
      _profileLinks = links.uriLinkStream.listen(_onProfileLink, onError: (Object _) {});
      final initial = await links.getInitialLink();
      if (initial != null) _onProfileLink(initial);
    } catch (_) {
      // OAuth and normal startup must keep working if a platform link is unavailable.
    }
  }

  void _onProfileLink(Uri uri) {
    final id = ProfileLinks.userIdFromUri(uri);
    if (id == null || !mounted) return;
    final now = DateTime.now();
    if (id == _lastProfile && _lastProfileAt != null &&
        now.difference(_lastProfileAt!) < const Duration(seconds: 2)) {
      return;
    }
    _lastProfile = id;
    _lastProfileAt = now;
    setState(() => _pendingProfile = id);
  }

  @override
  void dispose() {
    _profileLinks?.cancel();
    super.dispose();
  }

  Future<void> _init() async {
    final ap = context.read<AuthProvider>();
    await ap.restore();
    if (!mounted) return;
    final tp = context.read<ThemeProvider>();
    await tp.restore();
    var accepted = true;
    try {
      final prefs = await SharedPreferences.getInstance();
      accepted = prefs.getBool(WarningScreen.prefKey) ?? false;
    } catch (_) {}
    if (!mounted) return;
    setState(() {
      _warningAccepted = accepted;
      _startupReady = true;
    });
  }

  Widget _decideHome(LocaleProvider lp, AuthProvider ap) {
    if (!lp.ready) return const SplashLogo();
    if (!lp.hasChoice) return const LanguageIntroScreen();
    if (!_warningAccepted) return WarningScreen(onAccepted: () => setState(() => _warningAccepted = true));
    // Auth-first: oturum henüz geri yüklenmediyse bekle.
    if (ap.status == AuthStatus.unknown) return const SplashLogo();
    // Auth-first: giriş yapmadan uygulama açılmaz (Google/Facebook/e-posta).
    if (ap.enabled && !ap.isLoggedIn) return const AuthScreen(force: true);
    return const MainShell();
  }

  @override
  Widget build(BuildContext context) {
    final lp = context.watch<LocaleProvider>();
    final ap = context.watch<AuthProvider>();
    if (_startupReady && lp.ready && lp.hasChoice && _warningAccepted &&
        ap.enabled && ap.isLoggedIn && _pendingProfile != null) {
      final id = _pendingProfile!;
      _pendingProfile = null;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        final navigator = rootNavigatorKey.currentState;
        if (navigator == null) {
          setState(() => _pendingProfile = id);
          return;
        }
        navigator.push(MaterialPageRoute(builder: (_) => SocialProfileScreen(userId: id)));
      });
    }
    return _decideHome(lp, ap);
  }
}
