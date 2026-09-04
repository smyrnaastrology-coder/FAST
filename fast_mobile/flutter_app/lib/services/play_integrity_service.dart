import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Google Play Integrity token uretici (kendi native kanalimiz).
///
/// Kanal: `com.fastastrology.fast/play_integrity` -> `requestToken`
/// (`MainActivity.kt`, Standard Integrity API).
///
/// `cloudProjectNumber` yalnizca `--dart-define PLAY_CLOUD_PROJECT_NUMBER=...`
/// ile gecilirse dolu olur. Dolu degilse (veya Android disi platformda)
/// `requestToken()` `null` doner (baska islem bozulmaz).
class PlayIntegrityService {
  PlayIntegrityService() : _cloudProjectNumber = const String.fromEnvironment('PLAY_CLOUD_PROJECT_NUMBER');

  static const _channel = MethodChannel('com.fastastrology.fast/play_integrity');

  final String _cloudProjectNumber;

  bool get isConfigured => _cloudProjectNumber.isNotEmpty;

  /// Integrity token alir. Yapilandirilmamissa veya alinamazsa `null`.
  Future<String?> requestToken() async {
    if (!isConfigured) return null;
    try {
      final rand = Random.secure();
      final bytes = List<int>.generate(32, (_) => rand.nextInt(256));
      final nonce = base64Url.encode(bytes);
      final token = await _channel.invokeMethod<String>('requestToken', {
        'cloudProjectNumber': _cloudProjectNumber,
        'requestHash': nonce,
      });
      return token;
    } catch (e) {
      if (kDebugMode) print('[integrity] token err $e');
      return null;
    }
  }
}
