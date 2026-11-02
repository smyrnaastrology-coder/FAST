import 'package:flutter/material.dart';

import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../screens/landing_screen.dart';
import '../services/pro_service.dart';
import 'section_card.dart';

/// İçeriği yalnızca Pro abonelere gösterir; abone değilse kilitli tanıtım
/// kartı çizer ve Pro satın alma ekranına yönlendirir.
///
/// [section] true ise kilit, [SectionCard] başlığı altında gösterilir
/// (analiz sonuç ekranı). false ise bağımsız kart olarak çizilir
/// (gökyüzü takvimi gibi ekranlar).
class ProGate extends StatefulWidget {
  final Widget child;
  final IconData icon;

  /// Kilitliyken gösterilecek başlık (aynı zamanda bölüm başlığı).
  final String title;

  /// Kilitliyken gösterilecek açıklama.
  final String body;

  final bool section;

  /// Testlerde Pro durumunu dışarıdan vermek için.
  final Future<bool> Function()? statusLoader;

  /// Testlerde paywall dönüşünü/satın alma sonucunu taklit etmek için.
  final Future<bool?> Function()? paywallOpener;

  const ProGate({
    super.key,
    required this.child,
    required this.icon,
    required this.title,
    required this.body,
    this.section = false,
    this.statusLoader,
    this.paywallOpener,
  });

  @override
  State<ProGate> createState() => _ProGateState();
}

class _ProGateState extends State<ProGate> {
  bool? _pro;
  int _checkVersion = 0;

  @override
  void initState() {
    super.initState();
    ProService.revision.addListener(_onProInvalidated);
    _check();
  }

  @override
  void dispose() {
    ProService.revision.removeListener(_onProInvalidated);
    super.dispose();
  }

  void _onProInvalidated() {
    if (!mounted) return;
    setState(() => _pro = null);
    _check();
  }

  Future<void> _check({bool refresh = false}) async {
    final request = ++_checkVersion;
    final loader = widget.statusLoader;
    bool pro;
    try {
      pro = loader != null
          ? await loader()
          : await ProService.isPro(refresh: refresh);
    } catch (_) {
      pro = false;
    }
    if (mounted && request == _checkVersion) setState(() => _pro = pro);
  }

  Future<void> _openPaywall() async {
    final purchased = widget.paywallOpener != null
        ? await widget.paywallOpener!()
        : await Navigator.of(context).push<bool>(
            MaterialPageRoute(
              builder: (_) => const LandingScreen(asPaywall: true),
            ),
          );
    if (!mounted) return;
    // Geri/iptal dönüşü hiçbir zaman içeriği açmamalı. Paywall yalnızca
    // doğrulanmış Pro satın alımında true döndürür.
    if (purchased != true) {
      setState(() => _pro = false);
      return;
    }
    // Satın alma paywall içinde tamamlandı; yetkiyi mağazadan yeniden doğrula.
    ProService.invalidate(notify: false);
    await _check(refresh: true);
  }

  @override
  Widget build(BuildContext context) {
    final pro = _pro;
    if (pro == null) return const SizedBox.shrink();
    if (pro) return widget.child;

    if (widget.section) {
      return SectionCard(
        title: widget.title,
        icon: widget.icon,
        child: _ProLockBody(body: widget.body, onSubscribe: _openPaywall),
      );
    }
    return _ProLockCard(
      icon: widget.icon,
      title: widget.title,
      body: widget.body,
      onSubscribe: _openPaywall,
    );
  }
}

/// Kilit gövdesi: açıklama + "Pro'ya Geç" düğmesi + bilgi notu.
class _ProLockBody extends StatelessWidget {
  final String body;
  final VoidCallback onSubscribe;

  const _ProLockBody({required this.body, required this.onSubscribe});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.lock_outline, size: 20, color: FastTheme.accentGold),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                body,
                style: TextStyle(
                  color: FastTheme.textMuted,
                  fontSize: 13,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          child: FilledButton.icon(
            onPressed: onSubscribe,
            icon: const Icon(Icons.workspace_premium_outlined, size: 18),
            label: Text(l.proLockCta),
            style: FilledButton.styleFrom(
              backgroundColor: FastTheme.accentGold,
              foregroundColor: Colors.black87,
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          l.proLockNote,
          style: TextStyle(
            color: FastTheme.textMuted.withValues(alpha: 0.7),
            fontSize: 11,
            height: 1.35,
          ),
        ),
      ],
    );
  }
}

/// Bağımsız (bölüm dışı) kilit kartı.
class _ProLockCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;
  final VoidCallback onSubscribe;

  const _ProLockCard({
    required this.icon,
    required this.title,
    required this.body,
    required this.onSubscribe,
  });

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            FastTheme.accentGold.withValues(alpha: 0.16),
            FastTheme.cardBg,
          ],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: FastTheme.accentGold.withValues(alpha: 0.38),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 22, color: FastTheme.accentGoldLight),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    color: FastTheme.accentGoldLight,
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.4,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: FastTheme.accentGold.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  l.proLockBadge,
                  style: TextStyle(
                    color: FastTheme.accentGoldLight,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          _ProLockBody(body: body, onSubscribe: onSubscribe),
        ],
      ),
    );
  }
}
