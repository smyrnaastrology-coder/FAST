import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/locale_provider.dart';

class LanguageSwitcher extends StatelessWidget {
  const LanguageSwitcher({super.key});

  @override
  Widget build(BuildContext context) {
    final lp = context.watch<LocaleProvider>();
    return DropdownButtonHideUnderline(
      child: DropdownButton<String>(
        value: lp.locale.languageCode,
        dropdownColor: FastTheme.cardBg,
        icon: const Icon(Icons.language, size: 18, color: FastTheme.accentGold),
        style: const TextStyle(color: FastTheme.text, fontSize: 12),
        items: const [
          DropdownMenuItem(value: 'tr', child: Text('Türkçe', style: TextStyle(color: FastTheme.text, fontSize: 12))),
          DropdownMenuItem(value: 'en', child: Text('English', style: TextStyle(color: FastTheme.text, fontSize: 12))),
        ],
        onChanged: (v) {
          if (v != null) lp.setLanguage(v);
        },
      ),
    );
  }
}