import 'package:flutter_play_integrity_wrapper/flutter_play_integrity_wrapper.dart';

/// Google Play Integrity token uretici.
///
/// `cloudProjectNumber` yalnizca `--dart-define PLAY_CLOUD_PROJECT_NUMBER=...`
/// ile gecilirse dolu olur. Dolu degilse Play Integrity henuz aktif degildir
/// ve `requestToken()` `null` doner (baska islem bozulmaz).
class PlayIntegrityService {
  PlayIntegrityService() : _cloudProjectNumber = const String.fromEnvironment('PLAY_CLOUD_PROJECT_NUMBER');

  final String _cloudProjectNumber;
  final FlutterPlayIntegrityWrapper _wrapper = FlutterPlayIntegrityWrapper();

  bool get isConfigured => _cloudProjectNumber.isNotEmpty;

  /// Integrity token alir. Yapilandirilmamissa veya alinamazsa `null`.
  Future<String?> requestToken() async {
    if (!isConfigured) return null;
    try {
      final token = await _wrapper.requestIntegrityToken(
        cloudProjectNumber: _cloudProjectNumber,
      );
      return token;
    } catch (_) {
      return null;
    }
  }
}
