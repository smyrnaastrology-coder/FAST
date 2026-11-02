import 'package:flutter/material.dart';

import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/sky_moon_timing.dart';

String _signName(AppLocalizations l, int sign) =>
    AstroSigns.localizedName((sign + 3) % 12, l);

String _signSymbol(int sign) => AstroSigns.symbols[(sign + 3) % 12];

String _time(BuildContext context, DateTime time) =>
    MaterialLocalizations.of(
      context,
    ).formatTimeOfDay(
      TimeOfDay.fromDateTime(time.toLocal()),
      alwaysUse24HourFormat: true,
    );

String _day(BuildContext context, DateTime time) => MaterialLocalizations.of(
  context,
).formatShortMonthDay(time.toLocal());

String _range(BuildContext context, DateTime start, DateTime end) {
  final a = start.toLocal();
  final b = end.toLocal();
  final sameDay = a.year == b.year && a.month == b.month && a.day == b.day;
  if (sameDay) return '${_day(context, a)} · ${_time(context, a)} – ${_time(context, b)}';
  return '${_day(context, a)} · ${_time(context, a)} – ${_day(context, b)} · ${_time(context, b)}';
}

const _activityKeys = [
  'hair_growth',
  'hair_thicken',
  'trade',
  'education',
  'contract',
  'wedding',
  'moving',
  'planting',
];

String _activityLabel(AppLocalizations l, String key) => switch (key) {
  'hair_thicken' => l.skyActivityHairThicken,
  'trade' => l.skyActivityTrade,
  'education' => l.skyActivityEducation,
  'contract' => l.skyActivityContract,
  'wedding' => l.skyActivityWedding,
  'moving' => l.skyActivityMoving,
  'planting' => l.skyActivityPlanting,
  _ => l.skyActivityHairGrowth,
};

String _activityAbout(AppLocalizations l, String key) => switch (key) {
  'hair_thicken' => l.skyActivityAboutHairThicken,
  'trade' => l.skyActivityAboutTrade,
  'education' => l.skyActivityAboutEducation,
  'contract' => l.skyActivityAboutContract,
  'wedding' => l.skyActivityAboutWedding,
  'moving' => l.skyActivityAboutMoving,
  'planting' => l.skyActivityAboutPlanting,
  _ => l.skyActivityAboutHairGrowth,
};

String _activityRule(AppLocalizations l, String key) => switch (key) {
  'hair_thicken' => l.skyActivityRuleHairThicken,
  'trade' => l.skyActivityRuleTrade,
  'education' => l.skyActivityRuleEducation,
  'contract' => l.skyActivityRuleContract,
  'wedding' => l.skyActivityRuleWedding,
  'moving' => l.skyActivityRuleMoving,
  'planting' => l.skyActivityRulePlanting,
  _ => l.skyActivityRuleHairGrowth,
};

/// Ay boşta (VOC) dönemleri ve eylemlere göre doğru zaman pencereleri.
///
/// Yalnızca sunucudan gelen astronomik veriyi gösterir; hesap yapmaz.
class MoonTimingCard extends StatefulWidget {
  final SkyMoonTiming timing;
  final Future<void> Function(
    DateTime time,
    String title,
    String description,
  ) onExport;

  const MoonTimingCard({
    super.key,
    required this.timing,
    required this.onExport,
  });

  @override
  State<MoonTimingCard> createState() => _MoonTimingCardState();
}

class _MoonTimingCardState extends State<MoonTimingCard> {
  String _selected = _activityKeys.first;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final timing = widget.timing;
    final windows = timing.activities[_selected] ?? const [];

    return Container(
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: FastTheme.accentGold.withValues(alpha: 0.28),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.hourglass_disabled_outlined,
                size: 18,
                color: FastTheme.accentGoldLight,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  l.skyMoonTimingTitle,
                  style: TextStyle(
                    color: FastTheme.accentGoldLight,
                    fontSize: 12,
                    letterSpacing: 1.4,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          if (timing.voidNow && timing.voidEnd != null)
            _statusChip(
              l.skyMoonTimingActive(_time(context, timing.voidEnd!)),
              active: true,
            )
          else
            _statusChip(
              '${l.skyMoonInSign(_signName(l, timing.sign))} · '
              '${timing.degree.toStringAsFixed(1)}°',
              active: false,
            ),
          const SizedBox(height: 8),
          Text(
            timing.voidNow
                ? l.skyMoonTimingVoidHint
                : l.skyMoonTimingClearHint,
            style: TextStyle(
              color: FastTheme.textMuted.withValues(alpha: 0.9),
              fontSize: 12,
              height: 1.35,
            ),
          ),
          const SizedBox(height: 14),
          if (timing.voids.isEmpty)
            Text(
              l.skyMoonTimingNone,
              style: TextStyle(color: FastTheme.textMuted, fontSize: 12.5),
            )
          else ...[
            _sectionLabel(l.skyMoonTimingNext),
            const SizedBox(height: 6),
            for (final v in timing.voids.take(4))
              _windowTile(
                context: context,
                title: '${l.skyMoonTimingTitle} · ${_signName(l, v.sign)}',
                symbol: _signSymbol(v.sign),
                range: _range(context, v.start, v.end),
                time: v.start,
                subtitle: _signName(l, v.sign),
              ),
          ],
          const SizedBox(height: 16),
          Divider(color: FastTheme.border.withValues(alpha: 0.6), height: 1),
          const SizedBox(height: 14),
          _sectionLabel(l.skyActivityTitle),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final key in _activityKeys)
                ChoiceChip(
                  label: Text(_activityLabel(l, key)),
                  selected: _selected == key,
                  onSelected: (_) => setState(() => _selected = key),
                  visualDensity: VisualDensity.compact,
                ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            _activityAbout(l, _selected),
            style: TextStyle(
              color: FastTheme.textMuted.withValues(alpha: 0.95),
              fontSize: 12,
              height: 1.35,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            _activityRule(l, _selected),
            style: TextStyle(
              color: FastTheme.textMuted.withValues(alpha: 0.6),
              fontSize: 10.5,
            ),
          ),
          const SizedBox(height: 8),
          if (windows.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Text(
                l.skyActivityEmpty,
                style: TextStyle(color: FastTheme.textMuted, fontSize: 12.5),
              ),
            )
          else
            for (final w in windows.take(4))
              _windowTile(
                context: context,
                title: _activityLabel(l, _selected),
                symbol: _signSymbol(w.sign),
                range: _range(context, w.start, w.end),
                time: w.start,
                subtitle: _signName(l, w.sign),
              ),
          const SizedBox(height: 10),
          Row(
            children: [
              Icon(
                Icons.event_available_outlined,
                size: 13,
                color: FastTheme.textMuted.withValues(alpha: 0.7),
              ),
              const SizedBox(width: 5),
              Expanded(
                child: Text(
                  l.skyActivityTapHint,
                  style: TextStyle(
                    color: FastTheme.textMuted.withValues(alpha: 0.7),
                    fontSize: 10.5,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            l.skyMoonTimingNote,
            style: TextStyle(
              color: FastTheme.textMuted.withValues(alpha: 0.7),
              fontSize: 11,
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }

  Widget _statusChip(String text, {required bool active}) {
    final color = active ? FastTheme.accentGoldLight : FastTheme.textMuted;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 12.5,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _sectionLabel(String text) => Text(
    text,
    style: TextStyle(
      color: FastTheme.textMuted,
      fontSize: 12,
      fontWeight: FontWeight.w600,
    ),
  );

  Widget _windowTile({
    required BuildContext context,
    required String title,
    required String symbol,
    required String range,
    required DateTime time,
    required String subtitle,
  }) {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () => widget.onExport(
        time,
        title,
        '$range • $subtitle • Holavon',
      ),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: FastTheme.bg.withValues(alpha: 0.35),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: FastTheme.border.withValues(alpha: 0.45)),
        ),
        child: Row(
          children: [
            Text(
              symbol,
              style: TextStyle(
                color: FastTheme.accentGoldLight,
                fontSize: 17,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                range,
                style: TextStyle(
                  color: FastTheme.text,
                  fontSize: 12.5,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Icon(
              Icons.event_available_outlined,
              size: 16,
              color: FastTheme.textMuted.withValues(alpha: 0.8),
            ),
          ],
        ),
      ),
    );
  }
}
