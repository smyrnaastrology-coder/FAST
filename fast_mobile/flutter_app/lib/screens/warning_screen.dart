import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/theme.dart';
import '../l10n/app_localizations.dart';

class WarningScreen extends StatefulWidget {
  final VoidCallback onAccepted;
  const WarningScreen({super.key, required this.onAccepted});

  static const prefKey = 'warning_accepted_v1';

  @override
  State<WarningScreen> createState() => _WarningScreenState();
}

class _WarningScreenState extends State<WarningScreen> {
  bool _accepted = false;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      backgroundColor: FastTheme.bg,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 72,
                    height: 72,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient:  LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]),
                      boxShadow: [BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 28)],
                    ),
                    child:  Center(child: Text('F', style: TextStyle(color: FastTheme.bg, fontSize: 34, fontWeight: FontWeight.bold))),
                  ),
                  const SizedBox(height: 20),
                  Text(l10n.warningTitle,
                    textAlign: TextAlign.center,
                    style: GoogleFonts.cormorantGaramond(fontSize: 30, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                  const SizedBox(height: 20),
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: FastTheme.cardBg,
                      border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.4)),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Column(
                      children: [
                         Icon(Icons.auto_awesome, color: FastTheme.accentGold, size: 28),
                        const SizedBox(height: 12),
                        Text(l10n.warningBody,
                          textAlign: TextAlign.justify,
                          style:  TextStyle(color: FastTheme.text, fontSize: 14, height: 1.7)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 28),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _accepted ? null : _accept,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: FastTheme.accentGold,
                        foregroundColor: FastTheme.bg,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: Text(l10n.warningAcknowledge, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 1)),
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

  Future<void> _accept() async {
    setState(() => _accepted = true);
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(WarningScreen.prefKey, true);
    } catch (_) {}
    if (!mounted) return;
    widget.onAccepted();
  }
}