import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../services/auth_service.dart';
import 'auth_screen.dart';

/// Profil ekranı (Madde 4): hesap bilgisi, kayıtlı kişiler, çıkış.
/// Giriş yapan kullanıcı için doldurulur; giriş yoksa [AuthScreen]'e gönderir.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  List<SavedPerson> _people = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final r = await AuthService.listPeople();
    if (!mounted) return;
    setState(() {
      _people = r;
      _loading = false;
    });
  }

  Future<void> _confirmDelete(SavedPerson p) async {
    final l10n = AppLocalizations.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: FastTheme.cardBg,
        title: Text(p.name, style:  TextStyle(color: FastTheme.text, fontSize: 18)),
        content: Text(l10n.peopleDelete, style:  TextStyle(color: FastTheme.textMuted)),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(l10n.warningBack, style:  TextStyle(color: FastTheme.textMuted)),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(l10n.peopleDelete, style:  TextStyle(color: FastTheme.error)),
          ),
        ],
      ),
    );
    if (ok != true) return;
    await AuthService.deletePerson(p.id);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.peopleDeleted)));
    _load();
  }

  Future<void> _changePassword() async {
    final l10n = AppLocalizations.of(context);
    final ctrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: FastTheme.cardBg,
        title: Text(l10n.profileChangePassword, style:  TextStyle(color: FastTheme.accentGold)),
        content: TextField(
          controller: ctrl,
          obscureText: true,
          style:  TextStyle(color: FastTheme.text),
          decoration: InputDecoration(labelText: l10n.profileNewPassword, labelStyle:  TextStyle(color: FastTheme.textDim)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(l10n.warningBack, style:  TextStyle(color: FastTheme.textMuted)),
          ),
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(ctrl.text.isNotEmpty),
            child: Text(l10n.profileSave, style:  TextStyle(color: FastTheme.accentGold)),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await AuthService.changePassword(ctrl.text);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.profilePasswordChanged)));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.loginErrorGeneric)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final ap = context.watch<AuthProvider>();
    if (!ap.enabled) {
      return Scaffold(
        appBar: AppBar(title: Text(l10n.profileTitle, style:  TextStyle(color: FastTheme.accentGold))),
        backgroundColor: FastTheme.bg,
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(l10n.loginErrorDisabled,
                textAlign: TextAlign.center, style:  TextStyle(color: FastTheme.textMuted)),
          ),
        ),
      );
    }
    if (!ap.isLoggedIn) {
      return const AuthScreen();
    }
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        foregroundColor: FastTheme.text,
        title: Text(l10n.profileTitle, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
        actions: [
          IconButton(
            onPressed: ap.signOut,
            icon:  Icon(Icons.logout, color: FastTheme.accentGold),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _sectionCard(
            children: [
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(
                  radius: 24,
                  backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
                  child: Text(ap.email.isEmpty ? '?' : ap.email[0].toUpperCase(),
                      style:  TextStyle(color: FastTheme.accentGold, fontSize: 20, fontWeight: FontWeight.w700)),
                ),
                title: Text(ap.email, style:  TextStyle(color: FastTheme.text, fontSize: 15)),
                subtitle: Text(l10n.profileEmailLabel, style:  TextStyle(color: FastTheme.textDim, fontSize: 12)),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: _changePassword,
                style: OutlinedButton.styleFrom(
                  side:  BorderSide(color: FastTheme.border),
                  foregroundColor: FastTheme.accentGold,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: Text(l10n.profileChangePassword, style: const TextStyle(fontSize: 13)),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Text(l10n.peopleTitle,
                  style:  TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: FastTheme.accentGold)),
              const Spacer(),
              IconButton(
                onPressed: _load,
                icon:  Icon(Icons.refresh, color: FastTheme.textDim, size: 20),
              ),
            ],
          ),
          const SizedBox(height: 4),
          if (_loading)
             Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator(color: FastTheme.accentGold)))
          else if (_people.isEmpty)
            _sectionCard(children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Text(l10n.peopleEmpty,
                    textAlign: TextAlign.center, style:  TextStyle(color: FastTheme.textMuted, fontSize: 13, height: 1.5)),
              ),
            ])
          else
            ..._people.map((p) => _personTile(p, l10n)),
        ],
      ),
    );
  }

  Widget _sectionCard({required List<Widget> children}) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        border: Border.all(color: FastTheme.border),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(children: children),
    );
  }

  Widget _personTile(SavedPerson p, AppLocalizations l10n) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        border: Border.all(color: FastTheme.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
           Icon(Icons.person, color: FastTheme.accentGold, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(p.name, style:  TextStyle(color: FastTheme.text, fontSize: 15, fontWeight: FontWeight.w600)),
                const SizedBox(height: 2),
                Text(
                  [
                    if (p.birthDate != null && p.birthDate!.isNotEmpty) p.birthDate!,
                    if (p.city != null && p.city!.isNotEmpty) p.city!,
                    if (p.folder != null && p.folder!.isNotEmpty) p.folder!,
                  ].join(' · '),
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 12),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => _confirmDelete(p),
            icon:  Icon(Icons.delete_outline, color: FastTheme.error, size: 20),
          ),
        ],
      ),
    );
  }
}