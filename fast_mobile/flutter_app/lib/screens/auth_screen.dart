import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../services/auth_service.dart';

/// Giriş / kayıt ekranı. [force] true ise kapanamaz (paywall akışı).
class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key, this.force = false, this.onSignedIn});

  final bool force;
  final VoidCallback? onSignedIn;

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _isSignup = false;
  bool _obscure = true;
  bool _remember = true;
  bool _busy = false;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit(AuthProvider ap) async {
    final email = _emailCtrl.text.trim();
    final pass = _passwordCtrl.text;
    if (email.isEmpty || pass.isEmpty) return;
    setState(() => _busy = true);
    final ok = _isSignup
        ? await ap.signUp(email: email, password: pass)
        : await ap.signIn(email: email, password: pass, remember: _remember);
    if (!mounted) return;
    setState(() => _busy = false);
    final l10n = AppLocalizations.of(context);
    if (ok) {
      if (!widget.force) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.loginSuccess)));
        Navigator.of(context).pop();
      }
      widget.onSignedIn?.call();
    } else {
      final msg = _friendlyError(ap.error, l10n);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
    }
  }

  String _friendlyError(String? raw, AppLocalizations l10n) {
    if (raw == null || raw.isEmpty) return l10n.loginErrorGeneric;
    final r = raw.toLowerCase();
    if (r.contains('user_already_exists') || r.contains('already_registered') || r.contains('duplicate')) {
      return l10n.loginErrorExists;
    }
    if (r.contains('invalid_credentials') || r.contains('invalidlogincredentials') || r.contains('wrong') || r.contains('authfail')) {
      return l10n.loginErrorInvalid;
    }
    return l10n.loginErrorGeneric;
  }

  Future<void> _oauth(Future<bool> Function() fn) async {
    if (!AuthService.enabled) {
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppLocalizations.of(context).loginErrorDisabled)));
      return;
    }
    final ok = await fn();
    if (!mounted) return;
    if (ok) {
      if (!widget.force) Navigator.of(context).pop();
      widget.onSignedIn?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        foregroundColor: FastTheme.text,
        elevation: 0,
        automaticallyImplyLeading: !widget.force,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(_isSignup ? l10n.signupButton : l10n.loginTitle,
                    textAlign: TextAlign.center,
                    style:  TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                const SizedBox(height: 8),
                Text(l10n.loginSubtitle,
                    textAlign: TextAlign.center, style:  TextStyle(fontSize: 13, color: FastTheme.textMuted, height: 1.5)),
                const SizedBox(height: 28),
                _emailField(l10n),
                const SizedBox(height: 12),
                _passwordField(l10n),
                if (!_isSignup) ...[
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: InkWell(
                          onTap: () => setState(() => _remember = !_remember),
                          child: Row(
                            children: [
                              Checkbox(
                                value: _remember,
                                onChanged: (v) => setState(() => _remember = v ?? true),
                                activeColor: FastTheme.accentGold,
                                checkColor: FastTheme.bg,
                              ),
                              const Text('', style: TextStyle(fontSize: 0)),
                              Expanded(child: Text(l10n.loginRemember, style:  TextStyle(fontSize: 13, color: FastTheme.textMuted))),
                            ],
                          ),
                        ),
                      ),
                      TextButton(
                        onPressed: () => _forgot(),
                        child: Text(l10n.loginForgot, style:  TextStyle(fontSize: 12, color: FastTheme.accentGold)),
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 16),
                _goldButton(_isSignup ? l10n.signupButton : l10n.loginButton, () => _submit(context.read<AuthProvider>()), busy: _busy),
                const SizedBox(height: 20),
                Row(
                  children: [
                     Expanded(child: Divider(color: FastTheme.border)),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: Text(l10n.loginOr, style:  TextStyle(fontSize: 12, color: FastTheme.textDim)),
                    ),
                     Expanded(child: Divider(color: FastTheme.border)),
                  ],
                ),
                const SizedBox(height: 20),
                _oauthButton(Icons.g_mobiledata, l10n.loginGoogle, () => _oauth(() => context.read<AuthProvider>().signInWithGoogle())),
                const SizedBox(height: 10),
                _oauthButton(Icons.facebook_outlined, l10n.loginFacebook, () => _oauth(() => context.read<AuthProvider>().signInWithFacebook())),
                const SizedBox(height: 16),
                if (!widget.force)
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: Text(l10n.loginGuest, style:  TextStyle(fontSize: 13, color: FastTheme.textMuted)),
                  ),
                const SizedBox(height: 8),
                TextButton(
                  onPressed: () => setState(() => _isSignup = !_isSignup),
                  child: Text(
                    _isSignup ? l10n.loginHaveAccount : l10n.loginNoAccount,
                    style:  TextStyle(fontSize: 13, color: FastTheme.accentGold),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _forgot() async {
    final l10n = AppLocalizations.of(context);
    final email = _emailCtrl.text.trim();
    if (email.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.loginEmailLabel)));
      return;
    }
    try {
      await AuthService.resetPasswordEmail(email);
      if (!mounted) return;
      final l10n2 = AppLocalizations.of(context);
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${l10n2.loginForgot} $email')));
    } catch (_) {}
  }

  Widget _emailField(AppLocalizations l10n) {
    return TextField(
      controller: _emailCtrl,
      keyboardType: TextInputType.emailAddress,
      autocorrect: false,
      style:  TextStyle(color: FastTheme.text),
      decoration: _decoration(
        hint: l10n.loginEmailLabel,
        icon: Icons.email_outlined,
      ),
    );
  }

  Widget _passwordField(AppLocalizations l10n) {
    return TextField(
      controller: _passwordCtrl,
      obscureText: _obscure,
      style:  TextStyle(color: FastTheme.text),
      onSubmitted: (_) => _submit(context.read<AuthProvider>()),
      decoration: _decoration(
        hint: l10n.loginPasswordLabel,
        icon: Icons.lock_outline,
        suffix: IconButton(
          icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility,
              color: FastTheme.textDim, size: 20),
          onPressed: () => setState(() => _obscure = !_obscure),
        ),
      ),
    );
  }

  InputDecoration _decoration({required String hint, required IconData icon, Widget? suffix}) {
    return InputDecoration(
      hintText: hint,
      hintStyle:  TextStyle(color: FastTheme.textDim, fontSize: 14),
      prefixIcon: Icon(icon, color: FastTheme.accentGold, size: 20),
      suffixIcon: suffix,
      filled: true,
      fillColor: FastTheme.cardBg,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide:  BorderSide(color: FastTheme.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide:  BorderSide(color: FastTheme.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide:  BorderSide(color: FastTheme.accentGold, width: 1.5),
      ),
    );
  }

  Widget _goldButton(String text, VoidCallback onTap, {bool busy = false}) {
    return GestureDetector(
      onTap: busy ? null : onTap,
      child: Container(
        height: 50,
        decoration: BoxDecoration(
          gradient:  LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Center(
          child: busy
              ?  SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: FastTheme.bg))
              : Text(text, style:  TextStyle(color: FastTheme.bg, fontSize: 16, fontWeight: FontWeight.w700)),
        ),
      ),
    );
  }

  Widget _oauthButton(IconData icon, String text, VoidCallback onTap) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, color: FastTheme.text, size: 20),
      label: Text(text, style:  TextStyle(color: FastTheme.text, fontSize: 14)),
      style: OutlinedButton.styleFrom(
        side:  BorderSide(color: FastTheme.border),
        foregroundColor: FastTheme.text,
        padding: const EdgeInsets.symmetric(vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}