import 'package:flutter/material.dart';

import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/sky_retro_calendar.dart';

String _planetName(AppLocalizations l, String key) => switch (key) {
  'mercury' => l.chartPlanetMercury,
  'venus' => l.chartPlanetVenus,
  'mars' => l.chartPlanetMars,
  'jupiter' => l.chartPlanetJupiter,
  'saturn' => l.chartPlanetSaturn,
  'uranus' => l.chartPlanetUranus,
  'neptune' => l.chartPlanetNeptune,
  'pluto' => l.chartPlanetPluto,
  _ => key,
};

String _reviewPrompt(AppLocalizations l, String key) => switch (key) {
  'mercury' => l.skyRetroReviewMercury,
  'venus' => l.skyRetroReviewVenus,
  'mars' => l.skyRetroReviewMars,
  'jupiter' => l.skyRetroReviewJupiter,
  'saturn' => l.skyRetroReviewSaturn,
  'uranus' => l.skyRetroReviewUranus,
  'neptune' => l.skyRetroReviewNeptune,
  'pluto' => l.skyRetroReviewPluto,
  _ => l.skyRetroReviewDefault,
};

String _localDateTime(BuildContext context, DateTime value) {
  final local = value.toLocal();
  final date = MaterialLocalizations.of(context).formatMediumDate(local);
  final time = MaterialLocalizations.of(
    context,
  ).formatTimeOfDay(TimeOfDay.fromDateTime(local), alwaysUse24HourFormat: true);
  return '$date · $time';
}

class RetroCalendarCard extends StatelessWidget {
  final SkyRetroCalendar calendar;

  const RetroCalendarCard({super.key, required this.calendar});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    if (calendar.periods.isEmpty) {
      return _shell(
        context,
        child: Text(
          l.skyRetroEmpty,
          style: TextStyle(color: FastTheme.textMuted, fontSize: 13),
        ),
      );
    }
    return _shell(
      context,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (var i = 0; i < calendar.periods.length; i++) ...[
            if (i > 0) Divider(color: FastTheme.border.withValues(alpha: 0.55)),
            _period(context, calendar.periods[i]),
          ],
          const SizedBox(height: 8),
          Text(
            l.skyRetroNote,
            style: TextStyle(
              color: FastTheme.textMuted.withValues(alpha: 0.75),
              fontSize: 11,
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }

  Widget _period(BuildContext context, SkyRetroPeriod period) {
    final l = AppLocalizations.of(context);
    final sign = AstroSigns.localizedNameOf(
      AstroSigns.signNameFromLongitude(period.sign * 30 + period.degree),
      l,
    );
    final status = period.active
        ? l.skyRetroActive
        : period.inShadow
        ? l.skyRetroShadowActive
        : l.skyRetroUpcoming;
    final statusColor = period.active
        ? FastTheme.accentGoldLight
        : FastTheme.textMuted;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  _planetName(l, period.planet),
                  style: TextStyle(
                    color: FastTheme.text,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  status,
                  style: TextStyle(
                    color: statusColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 5),
          if (period.shadowStart != null)
            _dateLine(context, l.skyRetroShadowStart, period.shadowStart!),
          _dateLine(context, l.skyRetroStarts, period.retroStart),
          _dateLine(context, l.skyRetroDirectStation, period.directStation),
          if (period.shadowEnd != null)
            _dateLine(context, l.skyRetroShadowEnd, period.shadowEnd!),
          const SizedBox(height: 5),
          Text(
            l.skyRetroStationInSign(period.degree.toStringAsFixed(1), sign),
            style: TextStyle(color: FastTheme.accentGoldLight, fontSize: 11),
          ),
          const SizedBox(height: 4),
          Text(
            _reviewPrompt(l, period.planet),
            style: TextStyle(
              color: FastTheme.textMuted,
              fontSize: 12,
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }

  Widget _dateLine(BuildContext context, String label, DateTime time) =>
      Padding(
        padding: const EdgeInsets.only(top: 2),
        child: Text(
          '$label · ${_localDateTime(context, time)}',
          style: TextStyle(
            color: FastTheme.textMuted.withValues(alpha: 0.85),
            fontSize: 11,
          ),
        ),
      );

  Widget _shell(BuildContext context, {required Widget child}) => Container(
    margin: const EdgeInsets.only(bottom: 16),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: FastTheme.cardBg,
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: FastTheme.border.withValues(alpha: 0.7)),
    ),
    child: child,
  );
}
