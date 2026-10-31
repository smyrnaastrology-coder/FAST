import '../config/api_config.dart';

/// Public landing links and their app-only profile destinations.
class ProfileLinks {
  static final _uuid = RegExp(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
  );

  static String? publicUrl(String userId) {
    if (!_uuid.hasMatch(userId)) return null;
    return '${ApiConfig.baseUrl}/u/${userId.toLowerCase()}';
  }

  static String? userIdFromUri(Uri uri) {
    if (uri.scheme != 'com.fastastrology.fast' || uri.host != 'profile' ||
        uri.pathSegments.length != 1 || uri.hasQuery || uri.hasFragment) {
      return null;
    }
    final id = uri.pathSegments.single;
    return _uuid.hasMatch(id) ? id.toLowerCase() : null;
  }
}
