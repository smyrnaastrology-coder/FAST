import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import '../main.dart';
import '../screens/horary_screen.dart';
import '../screens/analyzer_screen.dart';
import '../screens/main_shell.dart';
import '../screens/social_shell.dart';
import '../screens/dm_inbox_screen.dart';

/// Günlük zamanlanmış bildirim servisi (yerel, backend gerektirmez).
/// Abonelere günlük minör progress hatırlatması gönderir.
class NotificationService {
  static final NotificationService instance = NotificationService._();
  NotificationService._();

  final _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  static const int _dailyId = 1001;
  /// Kanal kimligi API/ayar uyumlulugu icin sabit tutulur; kullaniciya
  /// gosterilen ad guncellenirse kimlik degismez ( aksi halde cihazda yeni
  /// bir kanal olusur ve eskisi kalir).
  static const String _channelId = 'daily_minor_progress';
  static const String _channelName = 'Günlük Kısa Vadeli İlerleme';

  void _handleNotificationTap(NotificationResponse response) {
    final payload = response.payload ?? '';
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
    _initialized = true;
    if (kDebugMode) debugPrint('[NOTIF] init ok');
  }

  static void _notificationTapBackground(NotificationResponse response) {
    // Arka planda sadece loglama; uygulama açıldığında init ile işlenir.
    if (kDebugMode) debugPrint('[NOTIF] background tap: ${response.payload}');
  }

  /// Her gün [hour]:[minute]'te bildirim zamanlar.
  Future<void> scheduleDaily(int hour, int minute, {String title = 'Holavon', String body = 'Bugünün kısa vadeli ilerleme akışını keşfet'}) async {
    if (!_initialized) return;
    final android = AndroidNotificationDetails(
      _channelId,
      _channelName,
      channelDescription: 'Günlük kısa vadeli ilerleme hatırlatması',
      importance: Importance.high,
      priority: Priority.high,
    );
    const darwin = DarwinNotificationDetails();
    final details = NotificationDetails(android: android, iOS: darwin);

    var now = tz.TZDateTime.now(tz.local);
    var scheduled = tz.TZDateTime(tz.local, now.year, now.month, now.day, hour, minute);
    if (!scheduled.isAfter(now)) {
      scheduled = scheduled.add(const Duration(days: 1));
    }

    await _plugin.zonedSchedule(
      _dailyId,
      title,
      body,
      scheduled,
      details,
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      matchDateTimeComponents: DateTimeComponents.time,
      payload: 'analysis',
    );
    if (kDebugMode) debugPrint('[NOTIF] günlük bildirim zamanlandı: $scheduled');
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

  Future<void> cancelDaily() async {
    await _plugin.cancel(_dailyId);
  }
}
