import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LocaleProvider extends ChangeNotifier {
  static const _prefKey = 'app_language';
  static const supportedLocales = [Locale('tr'), Locale('en'), Locale('es')];
  static const supportedCodes = ['tr', 'en', 'es'];

  Locale _locale = const Locale('tr');
  bool _ready = false;
  bool _hasChoice = false;
  Locale get locale => _locale;
  bool get ready => _ready;
  bool get hasChoice => _hasChoice;

  LocaleProvider() {
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _hasChoice = prefs.containsKey(_prefKey);
      final code = prefs.getString(_prefKey) ?? 'tr';
      _locale = _localeFor(code);
      _ready = true;
      notifyListeners();
    } catch (_) {
      _ready = true;
      notifyListeners();
    }
  }

  Future<void> setLocale(Locale locale) async {
    _locale = locale;
    _hasChoice = true;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefKey, locale.languageCode);
    } catch (_) {}
  }

  Future<void> setLanguage(String code) async {
    await setLocale(_localeFor(code));
  }

  Locale _localeFor(String code) {
    if (supportedCodes.contains(code)) return Locale(code);
    return const Locale('tr');
  }
}