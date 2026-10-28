import 'package:flutter/foundation.dart';
import 'package:google_mlkit_language_id/google_mlkit_language_id.dart';
import 'package:google_mlkit_translation/google_mlkit_translation.dart';

class TranslationService {
  static final TranslationService instance = TranslationService._();
  TranslationService._();

  final _languageIdentifier = LanguageIdentifier(confidenceThreshold: 0.5);
  final Map<String, OnDeviceTranslator> _translators = {};
  final Map<String, String> _cache = {};

  Future<String> translate({
    required String text,
    required String targetLanguageCode,
    String? sourceLanguageCode,
  }) async {
    if (text.trim().isEmpty) return text;
    final key = '$sourceLanguageCode|$targetLanguageCode|$text';
    if (_cache.containsKey(key)) return _cache[key]!;

    try {
      String source = sourceLanguageCode ?? 'en';
      if (sourceLanguageCode == null || sourceLanguageCode.isEmpty) {
        try {
          source = await _languageIdentifier.identifyLanguage(text);
          if (source == 'und') source = 'en';
        } catch (_) {
          source = 'en';
        }
      }

      if (source == targetLanguageCode) {
        _cache[key] = text;
        return text;
      }

      final sourceLanguage = BCP47Code.fromRawValue(source);
      final targetLanguage = BCP47Code.fromRawValue(targetLanguageCode);
      if (sourceLanguage == null || targetLanguage == null) return text;

      final translatorKey = '$source-$targetLanguageCode';
      if (!_translators.containsKey(translatorKey)) {
        final modelManager = OnDeviceTranslatorModelManager();
        await modelManager.downloadModel(source);
        await modelManager.downloadModel(targetLanguageCode);
        _translators[translatorKey] = OnDeviceTranslator(
          sourceLanguage: sourceLanguage,
          targetLanguage: targetLanguage,
        );
      }

      final translated = await _translators[translatorKey]!.translateText(text);
      _cache[key] = translated;
      return translated;
    } catch (e) {
      if (kDebugMode) debugPrint('[TRANSLATE] error: $e');
      return text;
    }
  }

  void clearCache() {
    _cache.clear();
  }

  Future<void> dispose() async {
    for (final t in _translators.values) {
      await t.close();
    }
    _translators.clear();
    await _languageIdentifier.close();
  }
}
