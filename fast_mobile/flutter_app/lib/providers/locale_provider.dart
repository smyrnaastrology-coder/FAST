import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LocaleProvider extends ChangeNotifier {
  static const _prefKey = 'app_language';
  static const supportedLocales = [Locale('tr'), Locale('en')];

  Locale _locale = const Locale('tr');
  Locale get locale => _locale;

  LocaleProvider() {
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final code = prefs.getString(_prefKey) ?? 'tr';
      _locale = Locale(code == 'en' ? 'en' : 'tr');
      notifyListeners();
    } catch (_) {}
  }

  Future<void> setLocale(Locale locale) async {
    _locale = locale;
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