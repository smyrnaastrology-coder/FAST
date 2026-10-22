import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../providers/locale_provider.dart';
import '../providers/theme_provider.dart';
import '../services/auth_service.dart';
import '../services/notification_service.dart';
import '../services/pro_service.dart';
import '../services/revenuecat_service.dart';
import '../widgets/theme_palette_picker.dart';
import 'landing_screen.dart';

/// Ayarlar: görünüm, dil, bildirimler, abonelik, hesap ve hakkında.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  static const String _reminderKey = 'daily_reminder_on';

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _reminder = false;
  bool? _pro;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _reminder = prefs.getBool(SettingsScreen._reminderKey) ?? false;
    } catch (_) {}
    final pro = await ProService.isPro();
    if (!mounted) return;
    setState(() => _pro = pro);
  }

  Future<void> _toggleReminder(bool on) async {
    final l10n = AppLocalizations.of(context);
    setState(() => _reminder = on);
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(SettingsScreen._reminderKey, on);
    } catch (_) {}
    if (on) {
      await NotificationService.instance.scheduleDaily(
        9,
        0,
        title: 'Holavon',
        body: l10n.settingsDailyReminder,
      );
    } else {
      await NotificationService.instance.cancelDaily();
    }
  }

  Future<void> _restore() async {
    setState(() => _busy = true);
    try {
      await RevenueCatService.restore();
      ProService.invalidate();
      final pro = await ProService.isPro();
      if (!mounted) return;
      setState(() => _pro = pro);
      final l10n = AppLocalizations.of(context);
      _snack(pro ? l10n.settingsProActive : l10n.settingsProFree);
    } catch (_) {
      if (mounted) _snack(AppLocalizations.of(context).shareFailed);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _signOut() async {
    await context.read<AuthProvider>().signOut();
    if (mounted) Navigator.of(context).popUntil((r) => r.isFirst);
  }

  Future<void> _deleteAccount() async {
    final l10n = AppLocalizations.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: FastTheme.bgSecondary,
        title: Text(
          l10n.accountDeleteTitle,
          style: TextStyle(color: FastTheme.text),
        ),
        content: Text(
          l10n.accountDeleteConfirm,
          style: TextStyle(color: FastTheme.textMuted, height: 1.45),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(l10n.peopleCancel),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(
              l10n.accountDeleteConfirmBtn,
              style: TextStyle(color: FastTheme.error),
            ),
          ),
        ],
      ),
    );
    if (ok != true) return;
    setState(() => _busy = true);
    try {
      await AuthService.deleteAccount();
      if (!mounted) return;
      final ap = context.read<AuthProvider>();
      await ap.signOut();
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(l10n.accountDeleteDone)));
      Navigator.of(context).popUntil((r) => r.isFirst);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(l10n.accountDeleteFailed)));
        setState(() => _busy = false);
      }
    }
  }

  void _snack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final tp = context.watch<ThemeProvider>();
    final lp = context.watch<LocaleProvider>();
    final ap = context.watch<AuthProvider>();

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text(
          l10n.settingsTitle,
          style: TextStyle(
            color: FastTheme.accentGold,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      body: ListView(
        padding: EdgeInsets.fromLTRB(
          20,
          12,
          20,
          32 + MediaQuery.of(context).viewPadding.bottom,
        ),
        children: [
          _section(l10n.settingsAppearance),
          _tile(
            icon: Icons.palette_outlined,
            title: l10n.themeAppearanceTitle,
            subtitle: l10n.themeAppearanceHint,
            onTap: () => showThemePaletteSheet(context),
          ),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: tp.isDark,
            activeThumbColor: FastTheme.accentGold,
            title: Text(
              l10n.themePaletteDark,
              style: TextStyle(color: FastTheme.text, fontSize: 14),
            ),
            onChanged: (_) => tp.toggle(),
          ),
          const SizedBox(height: 8),
          _section(l10n.settingsLanguage),
          Wrap(
            spacing: 8,
            children: [
              for (final e in const [
                ('tr', 'Türkçe'),
                ('en', 'English'),
                ('es', 'Español'),
              ])
                ChoiceChip(
                  label: Text(e.$2),
                  selected: lp.locale.languageCode == e.$1,
                  onSelected: (_) => lp.setLanguage(e.$1),
                ),
            ],
          ),
          const SizedBox(height: 16),
          _section(l10n.settingsNotifications),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: _reminder,
            activeThumbColor: FastTheme.accentGold,
            title: Text(
              l10n.settingsDailyReminder,
              style: TextStyle(color: FastTheme.text, fontSize: 14),
            ),
            onChanged: _toggleReminder,
          ),
          const SizedBox(height: 8),
          _section(l10n.settingsSubscription),
          _tile(
            icon: (_pro ?? false)
                ? Icons.workspace_premium
                : Icons.workspace_premium_outlined,
            title: (_pro ?? false)
                ? l10n.settingsProActive
                : l10n.settingsProFree,
            subtitle: l10n.settingsManagePro,
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => const LandingScreen(asPaywall: true),
              ),
            ),
          ),
          _tile(
            icon: Icons.restore,
            title: l10n.settingsRestore,
            onTap: _busy ? null : _restore,
          ),
          const SizedBox(height: 8),
          _section(l10n.settingsAccount),
          _tile(
            icon: Icons.mail_outline,
            title: ap.email.isEmpty ? l10n.settingsAccount : ap.email,
            subtitle: l10n.settingsAccount,
            onTap: null,
          ),
          _tile(
            icon: Icons.logout,
            title: l10n.settingsSignOut,
            onTap: _signOut,
          ),
          _tile(
            icon: Icons.delete_outline,
            title: l10n.accountDelete,
            danger: true,
            onTap: _busy ? null : _deleteAccount,
          ),
          const SizedBox(height: 8),
          _section(l10n.settingsAbout),
          _tile(
            icon: Icons.info_outline,
            title: l10n.settingsVersion,
            subtitle: '1.0.12 (57)',
            onTap: null,
          ),
          _tile(
            icon: Icons.camera_alt_outlined,
            title: '@holavonastrology',
            subtitle: 'Instagram',
            onTap: () => launchUrl(
              Uri.parse('https://instagram.com/holavonastrology'),
              mode: LaunchMode.externalApplication,
            ),
          ),
        ],
      ),
    );
  }

  Widget _section(String t) => Padding(
    padding: const EdgeInsets.only(top: 16, bottom: 6),
    child: Text(
      t,
      style: TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w700,
        color: FastTheme.accentGold,
        letterSpacing: 0.6,
      ),
    ),
  );

  Widget _tile({
    required IconData icon,
    required String title,
    String? subtitle,
    VoidCallback? onTap,
    bool danger = false,
  }) {
    final color = danger ? FastTheme.error : FastTheme.text;
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(
        icon,
        color: danger ? FastTheme.error : FastTheme.accentGold,
        size: 22,
      ),
      title: Text(title, style: TextStyle(color: color, fontSize: 14)),
      subtitle: subtitle == null
          ? null
          : Text(
              subtitle,
              style: TextStyle(color: FastTheme.textDim, fontSize: 12),
            ),
      trailing: onTap == null
          ? null
          : Icon(Icons.chevron_right, color: FastTheme.textDim, size: 20),
      onTap: onTap,
    );
  }
}
