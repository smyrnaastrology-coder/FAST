import 'chart_data.dart';

class ChartFrame {
  final ChartData data;
  final List<PlanetPos>? outerPlanets;
  final List<HouseCusp>? outerHouses;
  final String title;
  final String subtitle;
  const ChartFrame({
    required this.data,
    this.outerPlanets,
    this.outerHouses,
    required this.title,
    this.subtitle = '',
  });
}

typedef ChartFrameLoader = Future<ChartFrame> Function(DateTime date);

enum ChartTimeUnit { minute, hour, day, month, year }

/// Calendar month/year stepping preserves time and clamps the last day of month.
DateTime stepChartTime(DateTime value, ChartTimeUnit unit, int count) {
  DateTime wallDate(
    int y,
    int m,
    int d,
    int h,
    int min,
    int sec,
    int ms,
    int us,
  ) => value.isUtc
      ? DateTime.utc(y, m, d, h, min, sec, ms, us)
      : DateTime(y, m, d, h, min, sec, ms, us);
  if (unit == ChartTimeUnit.month || unit == ChartTimeUnit.year) {
    final months = unit == ChartTimeUnit.year ? count * 12 : count;
    final first = DateTime.utc(value.year, value.month + months);
    final lastDay = DateTime.utc(first.year, first.month + 1, 0).day;
    return wallDate(
      first.year,
      first.month,
      value.day > lastDay ? lastDay : value.day,
      value.hour,
      value.minute,
      value.second,
      value.millisecond,
      value.microsecond,
    );
  }
  // Wall-clock stepping: do not let the device's DST change the requested hour.
  final wall = DateTime.utc(
    value.year,
    value.month,
    value.day,
    value.hour,
    value.minute,
    value.second,
    value.millisecond,
    value.microsecond,
  );
  final duration = switch (unit) {
    ChartTimeUnit.minute => Duration(minutes: count),
    ChartTimeUnit.hour => Duration(hours: count),
    _ => Duration(days: count),
  };
  final result = wall.add(duration);
  return wallDate(
    result.year,
    result.month,
    result.day,
    result.hour,
    result.minute,
    result.second,
    result.millisecond,
    result.microsecond,
  );
}
