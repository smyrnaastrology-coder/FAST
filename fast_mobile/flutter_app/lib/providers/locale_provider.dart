import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LocaleProvider extends ChangeNotifier {
  static const _prefKey = 'app_language';
  static const supportedLocales = [Locale('tr'), Locale('en')];

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
      _locale = Locale(code == 'en' ? 'en' : 'tr');
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
    await setLocale(Locale(code == 'en' ? 'en' : 'tr'));
  }
}