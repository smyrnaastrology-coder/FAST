import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/theme.dart';

/// Bir tema paleti: kimlik, koyu/açık ve önizleme renkleri.
class ThemePalette {
  final String id;
  final bool isDark;

  /// Önizlemede gösterilecek 3 renk (zemin, kart, vurgu).
  final List<Color> colors;

  const ThemePalette({
    required this.id,
    required this.isDark,
    required this.colors,
  });
}

/// Koyu/açık + palet seçimi (Mor, Yumuşak Krem, İspanya, Arjantin).
class ThemeProvider extends ChangeNotifier {
  static const _prefKey = 'theme_mode';
  static const _paletteKey = 'theme_palette';

  /// Kullanılabilir paletler.
  static const palettes = <ThemePalette>[
    ThemePalette(
      id: 'dark',
      isDark: true,
      colors: [FastTheme.darkBg, FastTheme.darkCardBg, FastTheme.darkAccentGold],
    ),
    ThemePalette(
      id: 'light',
      isDark: false,
      colors: [FastTheme.lightBg, FastTheme.lightCardBg, FastTheme.lightAccentGold],
    ),
    ThemePalette(
      id: 'spain',
      isDark: true,
      colors: [FastTheme.spainBg, FastTheme.spainCardBg, FastTheme.spainAccentGold],
    ),
    ThemePalette(
      id: 'argentina',
      isDark: false,
      colors: [FastTheme.argBg, FastTheme.argCardBg, FastTheme.argAccentGold],
    ),
  ];

  ThemeMode _mode = ThemeMode.dark;
  String _palette = 'dark';
  bool _restored = false;

  ThemeMode get mode => _mode;
  bool get isDark => _mode == ThemeMode.dark;
  String get palette => _palette;

  ThemeProvider() {
    FastTheme.palette = _palette;
    FastTheme.apply(_mode);
  }

  Future<void> restore() async {
    if (_restored) return;
    _restored = true;
    try {
      final prefs = await SharedPreferences.getInstance();
      final storedMode = prefs.getString(_prefKey);
      _mode = storedMode == 'light' ? ThemeMode.light : ThemeMode.dark;
      final storedPalette = prefs.getString(_paletteKey);
      if (storedPalette != null && palettes.any((p) => p.id == storedPalette)) {
        _palette = storedPalette;
        _mode = palettes.firstWhere((p) => p.id == storedPalette).isDark
            ? ThemeMode.dark
            : ThemeMode.light;
      }
    } catch (_) {}
    FastTheme.palette = _palette;
    FastTheme.apply(_mode);
    notifyListeners();
  }

  Future<void> setMode(ThemeMode mode) async {
    _mode = mode;
    if (mode == ThemeMode.dark) {
      if (_palette == 'light') _palette = 'dark';
      if (_palette == 'argentina') _palette = 'spain';
    } else {
      if (_palette == 'dark') _palette = 'light';
      if (_palette == 'spain') _palette = 'argentina';
    }
    await _persist();
  }

  /// Belirli bir paleti seçer (koyu/açık modu paletin doğal haliyle eşleştirir).
  Future<void> setPalette(String id) async {
    if (!palettes.any((p) => p.id == id)) return;
    _palette = id;
    _mode = palettes.firstWhere((p) => p.id == id).isDark ? ThemeMode.dark : ThemeMode.light;
    await _persist();
  }

  Future<void> _persist() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefKey, _mode == ThemeMode.light ? 'light' : 'dark');
      await prefs.setString(_paletteKey, _palette);
    } catch (_) {}
    FastTheme.palette = _palette;
    FastTheme.apply(_mode);
    notifyListeners();
  }

  /// Koyu ↔ açık geçişi; aynı aileden diğer palete düşer.
  void toggle() {
    setMode(isDark ? ThemeMode.light : ThemeMode.dark);
  }
}
