import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../providers/locale_provider.dart';
import '../providers/social_provider.dart';
import '../services/social_service.dart';
import '../services/pro_service.dart';
import '../widgets/sky_strip.dart';
import '../widgets/theme_palette_picker.dart';
import 'analyzer_screen.dart';
import 'horary_screen.dart';
import 'landing_screen.dart';
import 'profile_screen.dart';
import 'settings_screen.dart';
import 'chart_list_screen.dart';
import '../widgets/chart_mark.dart';
import '../widgets/first_run_onboarding.dart';
import '../widgets/social_gate.dart';

/// Uygulama kabuÄŸu (Hub): tek giriÅŸten 3 sÃ¼tuna eriÅŸim â€”
/// Sosyal Â· Fast Synastry Â· Horary Oracle. Ãœstte profil.
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  static const _onboardingPrefKey = 'holavon_onboarding_v1';

  bool _wasLoggedIn = false;
  AuthProvider? _ap;
  bool? _isPro;

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
      _loadPro();
      _maybeShowFirstRun();
    });
  }

  Future<void> _loadPro({bool refresh = false}) async {
    final pro = await ProService.isPro(refresh: refresh);
    if (!mounted) return;
    setState(() => _isPro = pro);
  }

  /// Pro satın alma ekranını açar; dönüşte Pro durumunu tazeler.
  Future<void> _openPaywall() async {
    await _pushAndWait(const LandingScreen(asPaywall: true));
    if (!mounted) return;
    await _loadPro(refresh: true);
  }

  Future<void> _pushAndWait(Widget screen) async {
    await Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => screen));
  }

  /// Günlük kişisel yorum: doğrudan kişisel natal haritaya gider.
  Future<void> _openDailyProgress() async {
    // Bildirim hakkı Pro'ya bağlı olsa da yorum ekranının kendisi herkese
    // açıktır; burada Pro kapısı yok. Böylece Pro olan kullanıcı tekrar
    // ödeme ekranına düşmez.
    await _pushAndWait(
      const AnalyzerScreen(initialMode: 'bireysel_natal'),
    );
  }

  /// İlk girişte 3 adımlı tanıtımı göster; bir kez gösterilir.
  Future<void> _maybeShowFirstRun() async {
    bool done = true;
    try {
      final prefs = await SharedPreferences.getInstance();
      done = prefs.getBool(_onboardingPrefKey) ?? false;
    } catch (_) {
      return;
    }
    if (done || !mounted) return;
    await showGeneralDialog<void>(
      context: context,
      barrierDismissible: false,
      barrierLabel: 'onboarding',
      barrierColor: Colors.black.withValues(alpha: 0.86),
      transitionDuration: const Duration(milliseconds: 220),
      transitionBuilder: (_, anim, _, child) =>
          FadeTransition(opacity: anim, child: child),
      pageBuilder: (_, _, _) => FirstRunOnboarding(
        onStart: (question) async {
          await _markOnboardingDone();
          if (!mounted) return;
          _push(
            HoraryScreen(
              initialQuestion: question,
              skipIntro: true,
              autoAsk: true,
            ),
          );
        },
        onSkip: _markOnboardingDone,
      ),
    );
  }

  Future<void> _markOnboardingDone() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_onboardingPrefKey, true);
    } catch (_) {}
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
          ('tr', 'Türkçe'),
          ('en', 'English'),
          ('es', 'Español'),
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

  Widget _proChip(AppLocalizations l10n) {
    final isPro = _isPro == true;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
      child: Tooltip(
        message: isPro ? l10n.settingsProActive : l10n.proEntry,
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(20),
            onTap: _openPaywall,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: FastTheme.accentGold.withValues(alpha: 0.75),
                ),
                gradient: LinearGradient(
                  colors: [
                    FastTheme.accentGold.withValues(alpha: 0.26),
                    FastTheme.accentGold.withValues(alpha: 0.06),
                  ],
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    isPro
                        ? Icons.workspace_premium
                        : Icons.workspace_premium_outlined,
                    color: FastTheme.accentGold,
                    size: 16,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    'PRO',
                    style: TextStyle(
                      color: FastTheme.accentGold,
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _proBanner(AppLocalizations l10n) {
    final isPro = _isPro == true;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: _openPaywall,
        child: Ink(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: LinearGradient(
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
              colors: [
                FastTheme.accentGold.withValues(alpha: 0.30),
                FastTheme.accentGold.withValues(alpha: 0.08),
              ],
            ),
            border: Border.all(
              color: FastTheme.accentGold.withValues(alpha: 0.55),
            ),
          ),
          child: Row(
            children: [
              Icon(
                isPro ? Icons.verified : Icons.workspace_premium,
                color: FastTheme.accentGold,
                size: 26,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isPro ? l10n.settingsProActive : l10n.proEntry,
                      style: TextStyle(
                        color: FastTheme.accentGold,
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      isPro ? l10n.settingsManagePro : l10n.hubProBannerDesc,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: FastTheme.textMuted,
                        fontSize: 11.5,
                        height: 1.3,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: FastTheme.accentGold),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final ap = context.watch<AuthProvider>();

    return PopScope(
      canPop: true,
      child: Scaffold(
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
            _proChip(l10n),
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
                      const SizedBox(height: 14),
                      _proBanner(l10n),
                      const SizedBox(height: 14),
                      _PillarCard(
                        icon: Icons.auto_stories_outlined,
                        activeIcon: Icons.auto_stories,
                        asset: 'assets/fast_synastry_logo.png',
                        title: l10n.hubHoraryTitle,
                        desc: l10n.hubHoraryDesc,
                        badge: l10n.hubFeatured,
                        featured: true,
                        colors: [FastTheme.accentGold, FastTheme.rose],
                        onTap: () => _pushWithNotice(
                          prefKey: 'holavon_horary_notice_v1',
                          title: l10n.horaryIntroTitle,
                          body: l10n.horaryNoticeBody,
                          screen: const HoraryScreen(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      _DailyProgressTile(
                        onTap: _openDailyProgress,
                        title: l10n.proPillarProgress,
                        desc: l10n.proPillarProgressDesc,
                      ),
                      const SizedBox(height: 16),
                      _PillarCard(
                        icon: Icons.auto_graph_outlined,
                        activeIcon: Icons.auto_graph,
                        emblem: const ChartMark(),
                        title: l10n.hubChartsTitle,
                        desc: l10n.hubChartsDesc,
                        colors: [Color(0xFFD9B75B), Color(0xFFF5B700)],
                        onTap: () => _push(const ChartListScreen()),
                      ),
                      const SizedBox(height: 16),
                      _PillarCard(
                        icon: Icons.auto_awesome_outlined,
                        activeIcon: Icons.auto_awesome,
                        asset: 'assets/horary_oracle_logo.png',
                        title: l10n.hubAnalysisTitle,
                        desc: l10n.hubAnalysisDesc,
                        colors: [FastTheme.secondary, FastTheme.accent],
                        onTap: () => _pushWithNotice(
                          prefKey: 'holavon_synastry_notice_v1',
                          title: l10n.warningTitle,
                          body: l10n.warningBody,
                          screen: const AnalyzerScreen(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      _PillarCard(
                        icon: Icons.people_alt_outlined,
                        activeIcon: Icons.people_alt,
                        asset: 'assets/holavon_logo.png',
                        title: l10n.hubSocialTitle,
                        desc: l10n.hubSocialDesc,
                        colors: [
                          FastTheme.accentGold,
                          FastTheme.accentGoldLight,
                        ],
                        onTap: () => _push(const SocialGate()),
                      ),
                    ],
                  ),
                ),
              ],
            ),
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
  final Widget? emblem;
  final String title;
  final String desc;
  final List<Color> colors;
  final VoidCallback onTap;
  final bool featured;
  final String? badge;

  const _PillarCard({
    required this.icon,
    required this.activeIcon,
    this.asset,
    this.emblem,
    required this.title,
    required this.desc,
    required this.colors,
    required this.onTap,
    this.featured = false,
    this.badge,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Ink(
          height: featured ? 150 : 108,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                colors.first.withValues(alpha: featured ? 0.34 : 0.22),
                colors.last.withValues(alpha: featured ? 0.14 : 0.08),
              ],
            ),
            border: Border.all(
              color: colors.first.withValues(alpha: featured ? 0.75 : 0.4),
              width: featured ? 1.6 : 1,
            ),
            boxShadow: featured
                ? [
                    BoxShadow(
                      color: colors.first.withValues(alpha: 0.28),
                      blurRadius: 22,
                      spreadRadius: 1,
                    ),
                  ]
                : null,
          ),
          child: Padding(
            padding: EdgeInsets.symmetric(
              horizontal: 18,
              vertical: featured ? 18 : 16,
            ),
            child: Row(
              children: [
                Container(
                  width: featured ? 72 : 52,
                  height: featured ? 72 : 52,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(colors: colors),
                    boxShadow: featured
                        ? [
                            BoxShadow(
                              color: colors.first.withValues(alpha: 0.55),
                              blurRadius: 18,
                            ),
                          ]
                        : null,
                  ),
                  clipBehavior: Clip.antiAlias,
                  child:
                      emblem ??
                      (asset == null
                          ? Icon(
                              activeIcon,
                              color: FastTheme.bg,
                              size: featured ? 34 : 28,
                            )
                          : Padding(
                              padding: EdgeInsets.all(featured ? 5 : 4),
                              child: ClipOval(
                                child: Image.asset(
                                  asset!,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, _, _) => Icon(
                                    activeIcon,
                                    color: FastTheme.bg,
                                    size: featured ? 34 : 28,
                                  ),
                                ),
                              ),
                            )),
                ),
                const SizedBox(width: 18),
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (badge != null) ...[
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: colors.first,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            badge!,
                            style: TextStyle(
                              color: FastTheme.bg,
                              fontSize: 9.5,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 1.1,
                            ),
                          ),
                        ),
                        const SizedBox(height: 6),
                      ],
                      Text(
                        title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: FastTheme.textLight,
                          fontSize: featured ? 21 : 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        desc,
                        maxLines: featured ? 3 : 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: FastTheme.textMuted,
                          fontSize: featured ? 13 : 12.5,
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
/// Günlük kişisel Minor Progress yorumuna giden kısa yol.
class _DailyProgressTile extends StatelessWidget {
  final VoidCallback onTap;
  final String title;
  final String desc;

  const _DailyProgressTile({
    required this.onTap,
    required this.title,
    required this.desc,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Ink(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            color: FastTheme.cardBg,
            border: Border.all(color: FastTheme.border),
          ),
          child: Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: FastTheme.accentGold.withValues(alpha: 0.16),
                ),
                child: Icon(
                  Icons.wb_sunny_outlined,
                  color: FastTheme.accentGold,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: FastTheme.text,
                        fontSize: 13.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      desc,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: FastTheme.textDim,
                        fontSize: 11.5,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.arrow_forward, color: FastTheme.accentGold, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}

bool socialAvailable() => SocialService.enabled;
