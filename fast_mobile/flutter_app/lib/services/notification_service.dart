import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import '../main.dart';
import '../screens/horary_screen.dart';
import '../screens/analyzer_screen.dart';
import '../screens/main_shell.dart';
import '../screens/social_shell.dart';
import '../screens/dm_inbox_screen.dart';

/// Local notification service for personal natal Minor Progress readings and DMs.
class NotificationService {
  static final NotificationService instance = NotificationService._();
  NotificationService._();

  final _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;
  StreamSubscription<AuthState>? _authSubscription;

  static const int _dailyId = 1001;
  static const int _minorProgressIdStart = 2000;
  static const int _minorProgressMaxDays = 30;
  /// Kanal kimligi API/ayar uyumlulugu icin sabit tutulur; kullaniciya
  /// gosterilen ad guncellenirse kimlik degismez ( aksi halde cihazda yeni
  /// bir kanal olusur ve eskisi kalir).
  static const String _channelId = 'daily_minor_progress';
  static const String _channelName = 'Günlük Kısa Vadeli İlerleme';

  /// Routes a notification payload (used by local + FCM notifications).
  void routeTo(String payload) {
    _route(payload);
  }

  void _handleNotificationTap(NotificationResponse response) {
    _route(response.payload ?? '');
  }

  void _route(String payload) {
    final ctx = rootNavigatorKey.currentContext;
    if (ctx == null) return;
    final nav = rootNavigatorKey.currentState;
    if (nav == null) return;
    try {
      if (payload == 'horary') {
        nav.push(MaterialPageRoute(builder: (_) => const HoraryScreen()));
        return;
      }
      if (payload == 'analysis' || payload == 'synastry') {
        nav.push(MaterialPageRoute(builder: (_) => const AnalyzerScreen()));
        return;
      }
      if (payload == 'minor_progress') {
        nav.push(
          MaterialPageRoute(
            builder: (_) => const AnalyzerScreen(initialMode: 'bireysel_natal'),
          ),
        );
        return;
      }
      if (payload == 'social' || payload == 'feed') {
        nav.push(MaterialPageRoute(builder: (_) => const SocialShell()));
        return;
      }
      if (payload == 'dm') {
        nav.push(MaterialPageRoute(builder: (_) => const DmInboxScreen()));
        return;
      }
      if (payload == 'home') {
        nav.pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const MainShell()), (r) => false);
        return;
      }
    } catch (_) {}
  }

  Future<void> init() async {
    if (_initialized) return;
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidInit, iOS: DarwinInitializationSettings());
    await _plugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _handleNotificationTap,
      onDidReceiveBackgroundNotificationResponse: _notificationTapBackground,
    );
    tz.initializeTimeZones();
    try {
      final zone = await FlutterTimezone.getLocalTimezone();
      tz.setLocalLocation(tz.getLocation(zone.identifier));
    } catch (e) {
      if (kDebugMode) debugPrint('[NOTIF] local timezone unavailable: $e');
    }
    try {
      _authSubscription ??= Supabase.instance.client.auth.onAuthStateChange.listen(
        (state) {
          if (state.event == AuthChangeEvent.signedOut) {
            unawaited(cancelDaily());
          }
        },
      );
    } catch (_) {
      // Notifications still work when the optional Supabase account layer is off.
    }
    _initialized = true;
    if (kDebugMode) debugPrint('[NOTIF] init ok');
  }

  static void _notificationTapBackground(NotificationResponse response) {
    // Arka planda sadece loglama; uygulama açıldığında init ile işlenir.
    if (kDebugMode) debugPrint('[NOTIF] background tap: ${response.payload}');
  }

  Future<bool> requestPermissions() async {
    if (!_initialized) return false;
    var granted = true;
    final android = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (android != null) {
      granted = (await android.requestNotificationsPermission()) ?? false;
    }
    final ios = _plugin.resolvePlatformSpecificImplementation<
        IOSFlutterLocalNotificationsPlugin>();
    if (ios != null) {
      final appleGranted = await ios.requestPermissions(
        alert: true,
        badge: true,
        sound: true,
      );
      granted = granted && (appleGranted ?? false);
    }
    return granted;
  }

  /// Schedules personalized one-shot notifications for the supplied dates.
  /// The caller refreshes this rolling 30-day window when the app is opened.
  Future<void> scheduleMinorProgress(
    List<Map<String, dynamic>> entries, {
    required int hour,
    required int minute,
    required String title,
  }) async {
    if (!_initialized) return;
    await cancelDaily();
    final details = NotificationDetails(
      android: AndroidNotificationDetails(
        _channelId,
        _channelName,
        channelDescription: 'Kişisel günlük Minör Progress yorumları',
        importance: Importance.high,
        priority: Priority.high,
      ),
      iOS: const DarwinNotificationDetails(),
    );
    final now = tz.TZDateTime.now(tz.local);
    var scheduledCount = 0;
    for (final entry in entries.take(_minorProgressMaxDays)) {
      final date = DateTime.tryParse((entry['tarih'] ?? '').toString());
      if (date == null) continue;
      final scheduled = tz.TZDateTime(
        tz.local,
        date.year,
        date.month,
        date.day,
        hour,
        minute,
      );
      if (!scheduled.isAfter(now)) continue;
      final rawComments = entry['yorumlar'];
      final comments = rawComments is List
          ? rawComments.whereType<String>().where((s) => s.trim().isNotEmpty)
          : const <String>[];
      var body = comments.isNotEmpty
          ? comments.first.trim()
          : (entry['ortam'] ?? '').toString().trim();
      body = body.replaceAll(RegExp(r'<[^>]*>'), '').replaceAll('\n', ' ');
      if (body.length > 220) body = '${body.substring(0, 217).trimRight()}…';
      if (body.isEmpty) continue;
      await _plugin.zonedSchedule(
        _minorProgressIdStart + scheduledCount,
        title,
        body,
        scheduled,
        details,
        androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
        payload: 'minor_progress',
      );
      scheduledCount++;
    }
    if (kDebugMode) {
      debugPrint('[NOTIF] scheduled $scheduledCount personal minor-progress days');
    }
  }

  Future<void> showMessageNotification({required String title, required String body, String payload = 'dm'}) async {
    if (!_initialized) return;
    final android = AndroidNotificationDetails(
      'messages',
      'Mesaj Bildirimleri',
      channelDescription: 'Yeni mesaj bildirimleri',
      importance: Importance.high,
      priority: Priority.high,
    );
    const darwin = DarwinNotificationDetails();
    final details = NotificationDetails(android: android, iOS: darwin);
    await _plugin.show(DateTime.now().millisecondsSinceEpoch ~/ 1000, title, body, details, payload: payload);
  }

  /// Foreground display for server-sent social notifications (like/comment).
  Future<void> showSocialNotification({
    required String title,
    required String body,
    String payload = 'social',
  }) async {
    if (!_initialized) return;
    final android = AndroidNotificationDetails(
      'social_activity',
      'Sosyal Bildirimler',
      channelDescription: 'Beğeni ve yorum bildirimleri',
      importance: Importance.high,
      priority: Priority.high,
    );
    const darwin = DarwinNotificationDetails();
    final details = NotificationDetails(android: android, iOS: darwin);
    await _plugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      details,
      payload: payload,
    );
  }

  Future<void> cancelDaily() async {
    await _plugin.cancel(_dailyId);
    for (var i = 0; i < _minorProgressMaxDays; i++) {
      await _plugin.cancel(_minorProgressIdStart + i);
    }
  }
}
