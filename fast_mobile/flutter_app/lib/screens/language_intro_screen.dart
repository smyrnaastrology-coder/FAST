import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/locale_provider.dart';

class LanguageIntroScreen extends StatelessWidget {
  const LanguageIntroScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final lp = context.read<LocaleProvider>();
    return Scaffold(
      backgroundColor: FastTheme.bg,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const SizedBox(
                width: 72,
                height: 72,
                child: DecoratedBox(
                  decoration: BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold),
                  child: Center(
                    child: Text('F', style: TextStyle(color: FastTheme.bg, fontSize: 36, fontWeight: FontWeight.bold)),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text('FAST', style: TextStyle(color: FastTheme.accentGold, fontSize: 30, fontWeight: FontWeight.w700, letterSpacing: 4)),
              const SizedBox(height: 40),
              const Text('Dilinizi seçin', style: TextStyle(color: FastTheme.text, fontSize: 18)),
              const Text('Choose your language', style: TextStyle(color: FastTheme.textMuted, fontSize: 14)),
              const SizedBox(height: 24),
              _langBtn(lp, 'tr', 'Türkçe'),
              const SizedBox(height: 12),
              _langBtn(lp, 'en', 'English'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _langBtn(LocaleProvider lp, String code, String label) {
    return SizedBox(
      width: 240,
      height: 52,
      child: OutlinedButton(
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: FastTheme.accentGold),
          foregroundColor: FastTheme.accentGold,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
        onPressed: () => lp.setLanguage(code),
        child: Text(label, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
      ),
    );
  }
}