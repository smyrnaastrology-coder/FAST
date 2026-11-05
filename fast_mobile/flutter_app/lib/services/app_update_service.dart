import 'dart:convert';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';

import '../config/api_config.dart';

class AppUpdateStatus {
  const AppUpdateStatus({
    required this.required,
    required this.currentBuild,
    required this.minimumBuild,
    required this.storeUrl,
  });

  final bool required;
  final int currentBuild;
  final int minimumBuild;
  final String storeUrl;
}

/// Server-driven forced-update check.
///
/// The backend keeps the minimum builds at 0 until a release is live, so this
/// check is a no-op by default and always fails open.
class AppUpdateService {
  static const String _androidStoreUrl =
      'https://play.google.com/store/apps/details?id=com.fastastrology.fast';
  static const String _iosStoreUrl =
      'https://apps.apple.com/app/id6827527304';

  static Future<AppUpdateStatus?> check({
    Duration timeout = const Duration(seconds: 8),
  }) async {
    if (kIsWeb) return null;
    final platform = Platform.isAndroid
        ? 'android'
        : Platform.isIOS
            ? 'ios'
            : null;
    if (platform == null) return null;

    try {
      final info = await PackageInfo.fromPlatform();
      final currentBuild = int.tryParse(info.buildNumber.trim()) ?? 0;
      if (currentBuild <= 0) return null;

      final response =
          await http.get(Uri.parse(ApiConfig.appVersion)).timeout(timeout);
      if (response.statusCode != 200) return null;

      final body = jsonDecode(response.body);
      if (body is! Map<String, dynamic>) return null;
      final platformData = body[platform];
      if (platformData is! Map<String, dynamic>) return null;

      final min = platformData['min_version_code'] ??
          platformData['min_build'] ??
          0;
      final minimumBuild = min is num ? min.toInt() : 0;
      if (minimumBuild <= 0) return null;

      final url = body[platform == 'android'
          ? 'android_store_url'
          : 'ios_store_url'];
      return AppUpdateStatus(
        required: currentBuild < minimumBuild,
        currentBuild: currentBuild,
        minimumBuild: minimumBuild,
        storeUrl: url is String && url.startsWith('http')
            ? url
            : platform == 'android'
                ? _androidStoreUrl
                : _iosStoreUrl,
      );
    } catch (_) {
      return null;
    }
  }
}
