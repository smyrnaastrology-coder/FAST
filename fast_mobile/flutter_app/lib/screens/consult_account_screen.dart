import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config/theme.dart';
import '../providers/auth_provider.dart';
import '../providers/locale_provider.dart';
import '../providers/theme_provider.dart';
import '../services/auth_service.dart';

/// Danışmanlık sürümünün hesap ekranı.
///
/// Apple 5.1.1(v): hesap oluşturulabiliyorsa uygulama içinden silinebilmeli.
class ConsultAccountScreen extends StatefulWidget {
  const ConsultAccountScreen({super.key});

  @override
  State<ConsultAccountScreen> createState() => _ConsultAccountScreenState();
}

class _ConsultAccountScreenState extends State<ConsultAccountScreen> {
  bool _busy = false;

  String _lang(BuildContext context) =>
      Localizations.localeOf(context).languageCode;

  String _t(BuildContext context, String tr, String en, String es) {
    switch (_lang(context)) {
      case 'en':
        return en;
      case 'es':
        return es;
      default:
        return tr;
    }
  }

  Future<void> _signOut() async {
    setState(() => _busy = true);
    try {
      await AuthService.signOut();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _deleteAccount() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: FastTheme.cardBg,
        title: Text(
          _t(context, 'Hesabı sil', 'Delete account', 'Eliminar cuenta'),
          style: TextStyle(color: FastTheme.text),
        ),
        content: Text(
          _t(
            context,
            'Hesabınız, sorularınız ve cevaplarınız kalıcı olarak silinir. '
                'Bu işlem geri alınamaz.',
            'Your account, questions and answers are permanently deleted. '
                'This cannot be undone.',
            'Su cuenta, preguntas y respuestas se eliminan de forma '
                'permanente. No se puede deshacer.',
          ),
          style: TextStyle(color: FastTheme.textMuted, height: 1.4),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(
              _t(context, 'Vazgeç', 'Cancel', 'Cancelar'),
              style: TextStyle(color: FastTheme.textMuted),
            ),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.redAccent),
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(_t(context, 'Sil', 'Delete', 'Eliminar')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _busy = true);
    try {
      await AuthService.deleteAccount();
      await AuthService.signOut();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _t(
              context,
              'Hesap silinemedi. Lütfen tekrar deneyin.',
              'Could not delete the account. Please try again.',
              'No se pudo eliminar la cuenta. Inténtelo de nuevo.',
            ),
          ),
        ),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _open(String url) {
    launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    final ap = context.watch<AuthProvider>();
    final lp = context.watch<LocaleProvider>();
    final tp = context.watch<ThemeProvider>();

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: IconThemeData(color: FastTheme.text),
        title: Text(
          _t(context, 'Hesap', 'Account', 'Cuenta'),
          style: TextStyle(color: FastTheme.text, fontSize: 16),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          _row(
            icon: Icons.mail_outline,
            title: ap.email.isEmpty
                ? _t(context, 'E-posta yok', 'No email', 'Sin correo')
                : ap.email,
            subtitle: _t(context, 'Hesap', 'Account', 'Cuenta'),
          ),
          const SizedBox(height: 18),
          Text(
            _t(context, 'Dil', 'Language', 'Idioma'),
            style: TextStyle(color: FastTheme.textDim, fontSize: 11),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              for (final code in LocaleProvider.supportedCodes)
                ChoiceChip(
                  label: Text(code.toUpperCase()),
                  selected: lp.locale.languageCode == code,
                  selectedColor: FastTheme.accentGold,
                  labelStyle: TextStyle(
                    color: lp.locale.languageCode == code
                        ? Colors.black
                        : FastTheme.textMuted,
                    fontSize: 12,
                  ),
                  backgroundColor: FastTheme.cardBg,
                  side: BorderSide(color: FastTheme.border),
                  onSelected: (_) => lp.setLanguage(code),
                ),
            ],
          ),
          const SizedBox(height: 18),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: tp.isDark,
            activeThumbColor: FastTheme.accentGold,
            title: Text(
              _t(context, 'Koyu tema', 'Dark theme', 'Tema oscuro'),
              style: TextStyle(color: FastTheme.text, fontSize: 13),
            ),
            onChanged: (_) => tp.toggle(),
          ),
          Divider(color: FastTheme.border, height: 24),
          _row(
            icon: Icons.privacy_tip_outlined,
            title: _t(
              context,
              'Gizlilik politikası',
              'Privacy policy',
              'Privacidad',
            ),
            subtitle: 'holavon.com/gizlilik',
            onTap: () => _open('https://holavon.com/gizlilik'),
          ),
          _row(
            icon: Icons.description_outlined,
            title: _t(context, 'Kullanım şartları', 'Terms of use', 'Términos'),
            subtitle: 'holavon.com/sartlar',
            onTap: () => _open('https://holavon.com/sartlar'),
          ),
          _row(
            icon: Icons.support_agent,
            title: _t(context, 'Destek', 'Support', 'Soporte'),
            subtitle: 'destek@holavon.com',
            onTap: () => _open('mailto:destek@holavon.com'),
          ),
          Divider(color: FastTheme.border, height: 24),
          _row(
            icon: Icons.logout,
            title: _t(context, 'Çıkış yap', 'Sign out', 'Cerrar sesión'),
            onTap: _busy ? null : _signOut,
          ),
          _row(
            icon: Icons.delete_outline,
            title: _t(
              context,
              'Hesabı sil',
              'Delete account',
              'Eliminar cuenta',
            ),
            danger: true,
            onTap: _busy ? null : _deleteAccount,
          ),
        ],
      ),
    );
  }

  Widget _row({
    required IconData icon,
    required String title,
    String? subtitle,
    bool danger = false,
    VoidCallback? onTap,
  }) {
    final color = danger ? Colors.redAccent : FastTheme.text;
    return ListTile(
      contentPadding: EdgeInsets.zero,
      onTap: onTap,
      leading: Icon(
        icon,
        color: danger ? Colors.redAccent : FastTheme.accentGold,
        size: 20,
      ),
      title: Text(title, style: TextStyle(color: color, fontSize: 13)),
      subtitle: subtitle == null
          ? null
          : Text(
              subtitle,
              style: TextStyle(color: FastTheme.textDim, fontSize: 11),
            ),
      trailing: onTap == null
          ? null
          : Icon(Icons.chevron_right, color: FastTheme.textDim, size: 18),
    );
  }
}
