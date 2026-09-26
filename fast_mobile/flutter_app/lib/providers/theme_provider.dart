import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/theme.dart';

/// Koyu/açık + palet seçimi (Mor koyu, Krem açık, İspanya koyu, Arjantin açık).
class ThemeProvider extends ChangeNotifier {
  static const _prefKey = 'theme_mode';
  static const _paletteKey = 'theme_palette';

  /// Kullanılabilir paletler: (kimlik, koyu mu, görünen ad).
  static const palettes = <MapEntry<String, bool>>[
    MapEntry('dark', true),
    MapEntry('light', false),
    MapEntry('spain', true),
    MapEntry('argentina', false),
  ];

  ThemeMode _mode = ThemeMode.dark;
  String _palette = 'dark';

  ThemeMode get mode => _mode;
  bool get isDark => _mode == ThemeMode.dark;
  String get palette => _palette;

  ThemeProvider() {
    FastTheme.palette = _palette;
    FastTheme.apply(_mode);
  }

  Future<void> restore() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final storedMode = prefs.getString(_prefKey);
      _mode = storedMode == 'light' ? ThemeMode.light : ThemeMode.dark;
      final storedPalette = prefs.getString(_paletteKey);
      if (storedPalette != null && palettes.any((p) => p.key == storedPalette)) {
        _palette = storedPalette;
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
    if (!palettes.any((p) => p.key == id)) return;
    _palette = id;
    _mode = palettes.firstWhere((p) => p.key == id).value ? ThemeMode.dark : ThemeMode.light;
    await _persist();
  }

  Future<void> _persist() async {
    FastTheme.palette = _palette;
    FastTheme.apply(_mode);
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefKey, _mode == ThemeMode.light ? 'light' : 'dark');
      await prefs.setString(_paletteKey, _palette);
    } catch (_) {}
  }

  /// Koyu ↔ açık geçişi; aynı aileden diğer palete düşer.
  void toggle() {
    setMode(isDark ? ThemeMode.light : ThemeMode.dark);
  }
}
