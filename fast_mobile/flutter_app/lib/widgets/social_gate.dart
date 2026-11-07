import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
import '../screens/auth_screen.dart';
import '../screens/handle_claim_screen.dart';
import '../screens/social_shell.dart';

/// Sosyal sütun kapısı: giriş → @handle → akış.
///
/// Profil sorgusu sonuçlanmadan "profil oluştur" ekranı gösterilmez. Giriş
/// anındaki geçici bir ağ hatası, kullanıcıyı yanlışlıkla kayıt akışına
/// düşürüyordu; artık o durumda yükleniyor, hata varsa "tekrar dene"
/// gösterilir.
class SocialGate extends StatefulWidget {
  const SocialGate({super.key});

  @override
  State<SocialGate> createState() => _SocialGateState();
}

class _SocialGateState extends State<SocialGate> {
  bool _signedIn = false;
  bool _kickScheduled = false;

  void _ensureLoaded(SocialProvider sp) {
    if (!sp.signedIn) {
      _signedIn = false;
      return;
    }
    if (!_signedIn) {
      _signedIn = true;
      _kickScheduled = false;
    }
    if (_kickScheduled || sp.profileVerified) return;
    if (sp.status != SocialStatus.idle) return;
    _kickScheduled = true;
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) {
        _kickScheduled = false;
        return;
      }
      final provider = context.read<SocialProvider>();
      if (provider.signedIn &&
          !provider.profileVerified &&
          provider.status == SocialStatus.idle) {
        await provider.init();
      }
      _kickScheduled = false;
    });
  }

  Future<void> _retry() async {
    final sp = context.read<SocialProvider>();
    await sp.refreshProfile();
    if (!mounted) return;
    if (sp.profileVerified && sp.feed.isEmpty) {
      await sp.refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final sp = context.watch<SocialProvider>();
    if (sp.enabled && sp.signedIn) _ensureLoaded(sp);
    return SocialGateView(
      enabled: sp.enabled,
      signedIn: sp.signedIn,
      profileVerified: sp.profileVerified,
      hasHandle: sp.hasHandle,
      status: sp.status,
      retryLabel: l10n.socialRetry,
      onRetry: _retry,
    );
  }
}

/// [SocialGate]'in görsel kararı — doğrudan test edilebilir.
///
/// Provider'a bağlı olmadığı için oturum/profil durumlarının her kombinasyonu
/// widget testinde kolayca denenebilir.
class SocialGateView extends StatelessWidget {
  final bool enabled;
  final bool signedIn;
  final bool profileVerified;
  final bool hasHandle;
  final SocialStatus status;
  final String retryLabel;
  final Future<void> Function()? onRetry;

  const SocialGateView({
    super.key,
    required this.enabled,
    required this.signedIn,
    required this.profileVerified,
    required this.hasHandle,
    required this.status,
    required this.retryLabel,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    if (!enabled) {
      return _SimpleMessage(
        icon: Icons.people_alt_outlined,
        title: l10n.communityLoginTitle,
        desc: l10n.communityLoginSubtitle,
      );
    }
    if (!signedIn) return const AuthScreen(force: true);
    if (profileVerified) {
      if (!hasHandle) {
        return HandleClaimScreen(
          onClaimed: () => context.read<SocialProvider>().refreshProfile(),
        );
      }
      return const SocialShell();
    }
    if (status == SocialStatus.error) {
      return SocialGateStatus(
        error: true,
        retryLabel: retryLabel,
        onRetry: onRetry,
      );
    }
    return const SocialGateStatus(error: false);
  }
}

/// Profil doğrulanana kadar gösterilen yükleniyor / hata ekranı.
class SocialGateStatus extends StatelessWidget {
  final bool error;
  final String retryLabel;
  final Future<void> Function()? onRetry;

  const SocialGateStatus({
    super.key,
    required this.error,
    this.retryLabel = 'Retry',
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bgSecondary,
        elevation: 0,
        iconTheme: IconThemeData(color: FastTheme.accentGold),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: error
              ? Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.cloud_off_outlined,
                      size: 56,
                      color: FastTheme.textDim,
                    ),
                    const SizedBox(height: 18),
                    TextButton(
                      onPressed: onRetry == null ? null : () => onRetry!(),
                      child: Text(
                        retryLabel,
                        style: TextStyle(
                          color: FastTheme.accentGold,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                )
              : SizedBox(
                  width: 30,
                  height: 30,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.4,
                    color: FastTheme.accentGold,
                  ),
                ),
        ),
      ),
    );
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
