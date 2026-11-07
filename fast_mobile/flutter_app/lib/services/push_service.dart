import 'dart:async';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../config/api_config.dart';
import 'notification_service.dart';

/// Registers the device's FCM token with Supabase and routes incoming
/// social notifications (likes / comments) to the in-app UI.
///
/// The actual push is sent by fbst-api (`/api/push/social`) after a Supabase
/// trigger fires. This class only owns:
///   - token registration (RPC `register_device_token`)
///   - language updates so the server can localize the text
///   - foreground display and tap routing
class PushService {
  PushService._();
  static final PushService instance = PushService._();

  static const _prefToken = 'fcm_token';
  static const _prefLang = 'app_language';

  bool _initialized = false;
  bool _registering = false;
  String? _token;
  StreamSubscription<AuthState>? _authSub;

  Future<void> init() async {
    if (_initialized) return;
    _initialized = true;

    final messaging = FirebaseMessaging.instance;

    try {
      await messaging.requestPermission(alert: true, badge: true, sound: true);
      await messaging.setForegroundNotificationPresentationOptions(
        alert: true,
        badge: true,
        sound: true,
      );
    } catch (e) {
      if (kDebugMode) debugPrint('[PUSH] permission error: $e');
    }

    try {
      final prefs = await SharedPreferences.getInstance();
      _token = await messaging.getToken() ?? prefs.getString(_prefToken);
      if (_token != null && _token!.isNotEmpty) {
        await prefs.setString(_prefToken, _token!);
      }
    } catch (e) {
      if (kDebugMode) debugPrint('[PUSH] token error: $e');
    }

    messaging.onTokenRefresh.listen((token) {
      _token = token;
      unawaited(_storeToken(token));
      unawaited(_register());
    });

    FirebaseMessaging.onMessage.listen(_onForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_onMessageOpened);
    try {
      final initial = await messaging.getInitialMessage();
      if (initial != null) _onMessageOpened(initial);
    } catch (_) {}

    if (ApiConfig.supabaseEnabled) {
      try {
        _authSub ??= Supabase.instance.client.auth.onAuthStateChange.listen(
          (state) {
            if (state.event == AuthChangeEvent.signedOut) {
              unawaited(_unregister());
            } else if (state.session != null) {
              unawaited(_register());
            }
          },
        );
      } catch (e) {
        if (kDebugMode) debugPrint('[PUSH] auth listen error: $e');
      }
    }

    await _register();
  }

  /// Called by [LocaleProvider] so the server sends notifications in the
  /// language the user actually chose.
  Future<void> updateLanguage(String code) async {
    if (!_initialized) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefLang, code);
    } catch (_) {}
    await _register();
  }

  Future<void> _storeToken(String token) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefToken, token);
    } catch (_) {}
  }

  Future<String> _language() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final code = prefs.getString(_prefLang) ?? 'tr';
      return const {'tr', 'en', 'es'}.contains(code) ? code : 'tr';
    } catch (_) {
      return 'tr';
    }
  }

  Future<void> _register() async {
    if (_registering) return;
    if (!ApiConfig.supabaseEnabled) return;
    final token = _token;
    if (token == null || token.isEmpty) return;

    final String uid;
    try {
      uid = Supabase.instance.client.auth.currentUser?.id ?? '';
    } catch (_) {
      return;
    }
    if (uid.isEmpty) return;

    _registering = true;
    try {
      await Supabase.instance.client.rpc(
        'register_device_token',
        params: {
          'p_token': token,
          'p_platform': defaultTargetPlatform == TargetPlatform.iOS
              ? 'ios'
              : 'android',
          'p_lang': await _language(),
        },
      );
      if (kDebugMode) debugPrint('[PUSH] token registered');
    } catch (e) {
      // Missing SQL/RPC is non-fatal: local notifications still work.
      if (kDebugMode) debugPrint('[PUSH] register failed: $e');
    } finally {
      _registering = false;
    }
  }

  Future<void> _unregister() async {
    final token = _token;
    if (token == null || token.isEmpty) return;
    if (!ApiConfig.supabaseEnabled) return;
    try {
      await Supabase.instance.client.rpc(
        'unregister_device_token',
        params: {'p_token': token},
      );
    } catch (e) {
      if (kDebugMode) debugPrint('[PUSH] unregister failed: $e');
    }
  }

  void _onForegroundMessage(RemoteMessage message) {
    // Android does not show notification payloads while the app is foregrounded.
    // iOS shows them through setForegroundNotificationPresentationOptions.
    if (defaultTargetPlatform != TargetPlatform.android) return;
    final notification = message.notification;
    final title = notification?.title ?? '';
    final body = notification?.body ?? '';
    if (title.isEmpty && body.isEmpty) return;
    unawaited(
      NotificationService.instance.showSocialNotification(
        title: title,
        body: body,
        payload: 'social',
      ),
    );
  }

  void _onMessageOpened(RemoteMessage message) {
    // Likes/comments always land on the social feed; the post id stays in
    // message.data for future deep-linking.
    NotificationService.instance.routeTo('social');
  }
}
