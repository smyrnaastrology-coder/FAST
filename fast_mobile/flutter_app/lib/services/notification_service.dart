import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

/// Günlük zamanlanmış bildirim servisi (yerel, backend gerektirmez).
/// Abonelere günlük minör progress hatırlatması gönderir.
class NotificationService {
  static final NotificationService instance = NotificationService._();
  NotificationService._();

  final _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  static const int _dailyId = 1001;
  static const String _channelId = 'daily_minor_progress';
  static const String _channelName = 'Günlük Minör Progress';

  Future<void> init() async {
    if (_initialized) return;
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidInit, iOS: DarwinInitializationSettings());
    await _plugin.initialize(initSettings);
    tz.initializeTimeZones();
    _initialized = true;
    if (kDebugMode) debugPrint('[NOTIF] init ok');
  }

  /// Her gün [hour]:[minute]'te bildirim zamanlar.
  Future<void> scheduleDaily(int hour, int minute, {String title = 'Fast Synastry', String body = 'Bugünün minör ilerleme akışını keşfet'}) async {
    if (!_initialized) return;
    final android = AndroidNotificationDetails(
      _channelId,
      _channelName,
      channelDescription: 'Günlük minör progress hatırlatması',
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
    );
    if (kDebugMode) debugPrint('[NOTIF] günlük bildirim zamanlandı: $scheduled');
  }

  Future<void> cancelDaily() async {
    await _plugin.cancel(_dailyId);
  }
}
