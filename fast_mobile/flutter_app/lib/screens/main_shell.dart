import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../providers/locale_provider.dart';
import '../providers/social_provider.dart';
import '../services/social_service.dart';
import '../widgets/sky_strip.dart';
import '../widgets/theme_palette_picker.dart';
import 'analyzer_screen.dart';
import 'auth_screen.dart';
import 'social_shell.dart';
import 'handle_claim_screen.dart';
import 'horary_screen.dart';
import 'landing_screen.dart';
import 'profile_screen.dart';
import 'settings_screen.dart';
import 'chart_list_screen.dart';

/// Uygulama kabuÄŸu (Hub): tek giriÅŸten 3 sÃ¼tuna eriÅŸim â€”
/// Sosyal Â· Fast Synastry Â· Horary Oracle. Ãœstte profil.
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  bool _wasLoggedIn = false;
  AuthProvider? _ap;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final ap = context.read<AuthProvider>();
      _ap = ap;
      _wasLoggedIn = ap.isLoggedIn;
      ap.addListener(_onAuth);
      final sp = context.read<SocialProvider>();
      if (sp.enabled && sp.signedIn) sp.init();
    });
  }

  void _onAuth() {
    final ap = context.read<AuthProvider>();
    final giris = ap.isLoggedIn;
    if (giris != _wasLoggedIn) {
      _wasLoggedIn = giris;
      context.read<SocialProvider>().onAuthChanged();
    }
  }

  @override
  void dispose() {
    _ap?.removeListener(_onAuth);
    super.dispose();
  }

  void _push(Widget screen) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
  }

  Widget _languageButton(LocaleProvider lp) {
    final current = lp.locale.languageCode;
    return PopupMenuButton<String>(
      tooltip: AppLocalizations.of(context).settingsLanguage,
      onSelected: lp.setLanguage,
      color: FastTheme.bgSecondary,
      itemBuilder: (_) => [
        for (final e in const [
          ('tr', 'TÃ¼rkÃ§e'),
          ('en', 'English'),
          ('es', 'EspaÃ±ol'),
        ])
          CheckedPopupMenuItem(
            value: e.$1,
            checked: current == e.$1,
            child: Text(e.$2, style: TextStyle(color: FastTheme.text)),
          ),
      ],
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8),
        child: Row(
          children: [
            Icon(Icons.language, color: FastTheme.accentGold, size: 20),
            const SizedBox(width: 3),
            Text(
              current.toUpperCase(),
              style: TextStyle(
                color: FastTheme.accentGold,
                fontSize: 11,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// BÃ¶lÃ¼me Ã¶zel metodoloji uyarÄ±sÄ±nÄ± (bir kez) gÃ¶ster, sonra hedef ekranÄ± aÃ§.
  Future<void> _pushWithNotice({
    required String prefKey,
    required String title,
    required String body,
    required Widget screen,
  }) async {
    bool shown = false;
    try {
      final prefs = await SharedPreferences.getInstance();
      shown = prefs.getBool(prefKey) ?? false;
    } catch (_) {}
    if (!mounted) return;
    if (shown) {
      _push(screen);
      return;
    }
    final l10n = AppLocalizations.of(context);
    var dontShow = false;
    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => AlertDialog(
          backgroundColor: FastTheme.bgSecondary,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
            side: BorderSide(
              color: FastTheme.accentGold.withValues(alpha: 0.4),
            ),
          ),
          title: Row(
            children: [
              Icon(Icons.info_outline, color: FastTheme.accentGold),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    color: FastTheme.accentGold,
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          content: SingleChildScrollView(
            child: Text(
              body,
              style: TextStyle(
                color: FastTheme.textLight,
                fontSize: 13.5,
                height: 1.6,
              ),
            ),
          ),
          actions: [
            Row(
              children: [
                Checkbox(
                  value: dontShow,
                  onChanged: (v) => setS(() => dontShow = v ?? false),
                  activeColor: FastTheme.accentGold,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                Expanded(
                  child: Text(
                    l10n.noticeDontShow,
                    style: TextStyle(color: FastTheme.textMuted, fontSize: 13),
                  ),
                ),
              ],
            ),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () async {
                  if (dontShow) {
                    try {
                      final prefs = await SharedPreferences.getInstance();
                      await prefs.setBool(prefKey, true);
                    } catch (_) {}
                  }
                  if (ctx.mounted) Navigator.pop(ctx);
                  _push(screen);
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: FastTheme.accentGold,
                  padding: const EdgeInsets.symmetric(vertical: 13),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: Text(
                  l10n.warningAcknowledge,
                  style: TextStyle(
                    color: FastTheme.bg,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final ap = context.watch<AuthProvider>();
    final sp = context.watch<SocialProvider>();

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bgSecondary,
        elevation: 0,
        title: Text(
          l10n.appTitle,
          style: TextStyle(
            color: FastTheme.accentGold,
            fontWeight: FontWeight.w700,
            letterSpacing: 1,
          ),
        ),
        actions: [
          _languageButton(context.watch<LocaleProvider>()),
          IconButton(
            tooltip: l10n.settingsTitle,
            onPressed: () => _push(const SettingsScreen()),
            icon: Icon(Icons.settings_outlined, color: FastTheme.accentGold),
          ),
          IconButton(
            tooltip: l10n.themeAppearanceTitle,
            onPressed: () => showThemePaletteSheet(context),
            icon: Icon(Icons.palette_outlined, color: FastTheme.accentGold),
          ),
          IconButton(
            tooltip: l10n.proEntry,
            onPressed: () => _push(const LandingScreen(asPaywall: true)),
            icon: Icon(
              Icons.workspace_premium_outlined,
              color: FastTheme.accentGold,
            ),
          ),
          IconButton(
            tooltip: l10n.navProfile,
            onPressed: () => _push(const ProfileScreen()),
            icon: Icon(Icons.person_outline, color: FastTheme.accentGold),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                ap.email.isNotEmpty
                    ? '${l10n.hubWelcome}\n${ap.email}'
                    : l10n.hubWelcome,
                style: TextStyle(
                  color: FastTheme.textMuted,
                  fontSize: 14,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                l10n.hubChoose,
                style: TextStyle(
                  color: FastTheme.textLight,
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 20),
              Expanded(
                child: ListView(
                  children: [
                    const SkyStrip(),
                    _PillarCard(
                      icon: Icons.people_alt_outlined,
                      activeIcon: Icons.people_alt,
                      asset: 'assets/holavon_logo.png',
                      title: l10n.hubSocialTitle,
                      desc: l10n.hubSocialDesc,
                      colors: [FastTheme.accentGold, FastTheme.accentGoldLight],
                      onTap: () =>
                          _push(_SocialGate(l10n: l10n, enabled: sp.enabled)),
                    ),
                    const SizedBox(height: 16),
                    _PillarCard(
                      icon: Icons.auto_graph_outlined,
                      activeIcon: Icons.auto_graph,
                      asset: 'assets/holavon_logo.png',
                      title: 'Haritalarım',
                      desc: 'Natal haritanı oluştur ve incele',
                      colors: [Color(0xFFD9B75B), Color(0xFFF5B700)],
                      onTap: () => _push(const ChartListScreen()),
                    ),
                    const SizedBox(height: 16),
                    _PillarCard(
                      icon: Icons.auto_stories_outlined,
                      activeIcon: Icons.auto_stories,
                      asset: 'assets/horary_oracle_logo.png',
                      title: l10n.hubHoraryTitle,
                      desc: l10n.hubHoraryDesc,
                      colors: [FastTheme.rose, FastTheme.secondary],
                      onTap: () => _pushWithNotice(
                        prefKey: 'holavon_horary_notice_v1',
                        title: l10n.horaryIntroTitle,
                        body: l10n.horaryNoticeBody,
                        screen: const HoraryScreen(),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Sosyal sÃ¼tunu kapÄ±sÄ±: giriÅŸ (auth-first ile her zaman var) â†’ @handle â†’ feed.
class _SocialGate extends StatelessWidget {
  final AppLocalizations l10n;
  final bool enabled;
  const _SocialGate({required this.l10n, required this.enabled});

  @override
  Widget build(BuildContext context) {
    if (!enabled) {
      return _SimpleMessage(
        icon: Icons.people_alt_outlined,
        title: l10n.communityLoginTitle,
        desc: l10n.communityLoginSubtitle,
      );
    }
    final sp = context.watch<SocialProvider>();
    if (!sp.signedIn) {
      return const AuthScreen(force: true);
    }
    if (!sp.hasHandle) {
      return HandleClaimScreen(
        onClaimed: () => context.read<SocialProvider>().refreshProfile(),
      );
    }
    return const SocialShell();
  }
}

class _SimpleMessage extends StatelessWidget {
  final IconData icon;
  final String title;
  final String desc;
  const _SimpleMessage({
    required this.icon,
    required this.title,
    required this.desc,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bgSecondary,
        iconTheme: IconThemeData(color: FastTheme.accentGold),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 64, color: FastTheme.accentGold),
              const SizedBox(height: 20),
              Text(
                title,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  color: FastTheme.accentGold,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                desc,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  color: FastTheme.textMuted,
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PillarCard extends StatelessWidget {
  final IconData icon;
  final IconData activeIcon;
  final String? asset;
  final String title;
  final String desc;
  final List<Color> colors;
  final VoidCallback onTap;

  const _PillarCard({
    required this.icon,
    required this.activeIcon,
    this.asset,
    required this.title,
    required this.desc,
    required this.colors,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Ink(
          height: 108,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                colors.first.withValues(alpha: 0.22),
                colors.last.withValues(alpha: 0.08),
              ],
            ),
            border: Border.all(
              color: colors.first.withValues(alpha: 0.4),
              width: 1,
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
            child: Row(
              children: [
                Container(
                  width: 52,
                  height: 52,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(colors: colors),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: asset == null
                      ? Icon(activeIcon, color: FastTheme.bg, size: 28)
                      : Padding(
                          padding: const EdgeInsets.all(4),
                          child: ClipOval(
                            child: Image.asset(
                              asset!,
                              fit: BoxFit.cover,
                              errorBuilder: (_, _, _) =>
                                  Icon(activeIcon, color: FastTheme.bg, size: 28),
                            ),
                          ),
                        ),
                ),
                const SizedBox(width: 18),
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          color: FastTheme.textLight,
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        desc,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: FastTheme.textMuted,
                          fontSize: 12.5,
                          height: 1.3,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right, color: FastTheme.textDim),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Sosyal servis kapalÄ±ysa (Supabase define yok) false dÃ¶ner.
bool socialAvailable() => SocialService.enabled;
