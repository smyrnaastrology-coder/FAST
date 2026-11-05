import 'package:shared_preferences/shared_preferences.dart';

import 'api_service.dart';
import 'notification_service.dart';
import 'pro_service.dart';
import 'social_service.dart';

enum DailyProgressReminderResult {
  scheduled,
  disabled,
  proRequired,
  natalRequired,
  permissionDenied,
  unavailable,
}

/// Refreshes up to 30 days of on-device, personal natal progress notifications.
/// The user's birth data is read from their private Supabase profile and is
/// sent only to the existing analysis API; notification text stays on-device.
class DailyMinorProgressNotifications {
  static const enabledKey = 'daily_reminder_on';
  static const hourKey = 'daily_reminder_hour';
  static const minuteKey = 'daily_reminder_minute';
  static const defaultHour = 9;
  static const defaultMinute = 0;

  static Future<DailyProgressReminderResult> refresh({
    bool requestPermission = false,
  }) async {
    try {
      return await _refresh(requestPermission: requestPermission);
    } catch (_) {
      return DailyProgressReminderResult.unavailable;
    }
  }

  static Future<DailyProgressReminderResult> _refresh({
    required bool requestPermission,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    if (!(prefs.getBool(enabledKey) ?? false)) {
      await NotificationService.instance.cancelDaily();
      return DailyProgressReminderResult.disabled;
    }

    if (!await ProService.isPro()) {
      await NotificationService.instance.cancelDaily();
      return DailyProgressReminderResult.proRequired;
    }

    if (requestPermission &&
        !await NotificationService.instance.requestPermissions()) {
      return DailyProgressReminderResult.permissionDenied;
    }

    final birth = await SocialService.myBirthInfo();
    final date = birth?.date?.trim() ?? '';
    if (date.isEmpty) {
      await prefs.setBool(enabledKey, false);
      await NotificationService.instance.cancelDaily();
      return DailyProgressReminderResult.natalRequired;
    }

    var city = birth?.city?.trim() ?? '';
    var country = birth?.country?.trim() ?? '';
    var latitude = birth?.lat;
    var longitude = birth?.lon;
    if ((latitude == null || longitude == null) && city.isNotEmpty) {
      try {
        final location = await ApiService().geocode(
          [city, country].where((part) => part.isNotEmpty).join(', '),
        );
        latitude = (location['lat'] as num?)?.toDouble();
        longitude = (location['lon'] as num?)?.toDouble();
        city = (location['city'] ?? city).toString();
        if (country.isEmpty) country = (location['country'] ?? '').toString();
      } catch (_) {
        await prefs.setBool(enabledKey, false);
        await NotificationService.instance.cancelDaily();
        return DailyProgressReminderResult.natalRequired;
      }
    }
    if (city.isEmpty || latitude == null || longitude == null) {
      await prefs.setBool(enabledKey, false);
      await NotificationService.instance.cancelDaily();
      return DailyProgressReminderResult.natalRequired;
    }

    try {
      final language = prefs.getString('app_language') ?? 'tr';
      final entries = await ApiService().minorProgressNotifications(
        date: date,
        time: birth?.time?.trim().isNotEmpty == true ? birth!.time! : '12:00',
        city: city,
        country: country.isEmpty ? 'Türkiye' : country,
        latitude: latitude,
        longitude: longitude,
        language: language,
        days: 30,
      );
      if (entries.isEmpty || entries.every((entry) => (entry['tarih'] ?? '').toString().isEmpty)) {
        return DailyProgressReminderResult.unavailable;
      }
      final hour = prefs.getInt(hourKey) ?? defaultHour;
      final minute = prefs.getInt(minuteKey) ?? defaultMinute;
      await NotificationService.instance.scheduleMinorProgress(
        entries,
        hour: hour,
        minute: minute,
        title: _title(language),
      );
      return DailyProgressReminderResult.scheduled;
    } catch (_) {
      return DailyProgressReminderResult.unavailable;
    }
  }

  static String _title(String language) => switch (language) {
        'en' => 'Your daily Minor Progress',
        'es' => 'Tu progreso menor diario',
        _ => 'Günlük Minör Progress yorumun',
      };
}
