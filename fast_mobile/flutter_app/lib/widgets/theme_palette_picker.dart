import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/theme_provider.dart';

/// Palet kimliğine göre yerelleştirilmiş ad.
String themePaletteLabel(AppLocalizations l10n, String id) {
  switch (id) {
    case 'spain':
      return l10n.themePaletteSpain;
    case 'argentina':
      return l10n.themePaletteArgentina;
    case 'light':
      return l10n.themePaletteLight;
    default:
      return l10n.themePaletteDark;
  }
}

/// 4 paletin (Mor, Yumuşak Krem, İspanya, Arjantin) seçim listesi.
///
/// Seçim yapıldığında [ThemeProvider.setPalette] çağrılır; uygulama kökü
/// yeniden kurulduğu için liste görünür olduğu ekranla birlikte kapanır.
class ThemePalettePicker extends StatelessWidget {
  const ThemePalettePicker({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final tp = context.watch<ThemeProvider>();
    return Column(
      children: [
        for (var i = 0; i < ThemeProvider.palettes.length; i++) ...[
          _PaletteTile(
            palette: ThemeProvider.palettes[i],
            label: themePaletteLabel(l10n, ThemeProvider.palettes[i].id),
            selected: tp.palette == ThemeProvider.palettes[i].id,
            onTap: () => tp.setPalette(ThemeProvider.palettes[i].id),
          ),
          if (i != ThemeProvider.palettes.length - 1) const SizedBox(height: 8),
        ],
      ],
    );
  }
}

class _PaletteTile extends StatelessWidget {
  final ThemePalette palette;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _PaletteTile({
    required this.palette,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: selected ? FastTheme.cardBgHover : FastTheme.bg,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: selected ? FastTheme.accentGold : FastTheme.border,
              width: selected ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Row(
                children: palette.colors
                    .map(
                      (c) => Container(
                        width: 18,
                        height: 18,
                        margin: const EdgeInsets.only(right: 4),
                        decoration: BoxDecoration(
                          color: c,
                          shape: BoxShape.circle,
                          border: Border.all(color: FastTheme.border),
                        ),
                      ),
                    )
                    .toList(),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                    color: FastTheme.text,
                  ),
                ),
              ),
              if (selected) Icon(Icons.check_circle, size: 18, color: FastTheme.accentGold),
            ],
          ),
        ),
      ),
    );
  }
}

/// Palet seçimini alt panelde açar (giriş ekranı, hub, profil).
Future<void> showThemePaletteSheet(BuildContext context) {
  final l10n = AppLocalizations.of(context);
  return showModalBottomSheet<void>(
    context: context,
    backgroundColor: FastTheme.cardBg,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
    ),
    builder: (ctx) => SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.themePickerTitle,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: FastTheme.text),
            ),
            const SizedBox(height: 12),
            const ThemePalettePicker(),
          ],
        ),
      ),
    ),
  );
}
