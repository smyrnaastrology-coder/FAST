import 'package:flutter/material.dart';

import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/sky_calendar.dart';
import '../services/api_service.dart';

const _phaseGlyphs = {'new_moon': '🌑', 'full_moon': '🌕'};

const _eclipseGlyphs = {'solar': '☉', 'lunar': '☾'};

String _deg(double value) {
  final rounded = (value * 10).round() / 10;
  return rounded == rounded.roundToDouble()
      ? rounded.toInt().toString()
      : rounded.toStringAsFixed(1);
}

String _phaseName(AppLocalizations l, String type) =>
    type == 'full_moon' ? l.skyFullMoon : l.skyNewMoon;

String _eclipseName(AppLocalizations l, bool solar) =>
    solar ? l.skyEclipseSolar : l.skyEclipseLunar;

String _eclipseVariant(AppLocalizations l, String variant) => switch (variant) {
  'total' => l.skyEclipseTotal,
  'annular' => l.skyEclipseAnnular,
  'hybrid' => l.skyEclipseHybrid,
  'penumbral' => l.skyEclipsePenumbral,
  _ => l.skyEclipsePartial,
};

String _dateLine(BuildContext context, DateTime time) {
  final local = time.toLocal();
  final date = MaterialLocalizations.of(context).formatMediumDate(local);
  final clock = MaterialLocalizations.of(
    context,
  ).formatTimeOfDay(TimeOfDay.fromDateTime(local), alwaysUse24HourFormat: true);
  return '$date · $clock';
}

String _countdown(AppLocalizations l, DateTime time) {
  final diff = time.toLocal().difference(DateTime.now());
  if (diff.isNegative) return l.skyCalendarNow;
  if (diff.inDays >= 2) return l.skyCalendarInDays(diff.inDays.toString());
  if (diff.inDays == 1) return l.skyCalendarTomorrow;
  if (diff.inHours >= 1) return l.skyCalendarInHours(diff.inHours.toString());
  return l.skyCalendarToday;
}

class SkyCalendarScreen extends StatefulWidget {
  const SkyCalendarScreen({super.key});

  @override
  State<SkyCalendarScreen> createState() => _SkyCalendarScreenState();
}

class _SkyCalendarScreenState extends State<SkyCalendarScreen> {
  late Future<SkyCalendar> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<SkyCalendar> _load() async =>
      SkyCalendar.fromJson(await ApiService().skyCalendar());

  void _reload() {
    setState(() => _future = _load());
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text(
          l.skyCalendarTitle,
          style: TextStyle(
            color: FastTheme.accentGold,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      body: FutureBuilder<SkyCalendar>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return Center(
              child: CircularProgressIndicator(color: FastTheme.accentGold),
            );
          }
          if (snap.hasError || !snap.hasData) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      l.socialErrorServer,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: FastTheme.textMuted.withValues(alpha: 0.8),
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 14),
                    FilledButton(
                      onPressed: _reload,
                      style: FilledButton.styleFrom(
                        backgroundColor: FastTheme.accentGold,
                      ),
                      child: Text(l.socialRetry),
                    ),
                  ],
                ),
              ),
            );
          }
          final cal = snap.data!;
          if (cal.phases.isEmpty && cal.eclipses.isEmpty) {
            return Center(
              child: Text(
                l.skyCalendarEmpty,
                style: TextStyle(
                  color: FastTheme.textMuted.withValues(alpha: 0.7),
                ),
              ),
            );
          }
          return ListView(
            padding: EdgeInsets.fromLTRB(
              20,
              12,
              20,
              32 + MediaQuery.of(context).viewPadding.bottom,
            ),
            children: [
              if (cal.phases.isNotEmpty) ...[
                _section(l.skyCalendarPhases),
                ...cal.phases.map((e) => _PhaseTile(event: e)),
                const SizedBox(height: 12),
              ],
              if (cal.eclipses.isNotEmpty) ...[
                _section(l.skyCalendarEclipses),
                ...cal.eclipses.map((e) => _EclipseTile(eclipse: e)),
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _section(String title) => Padding(
    padding: const EdgeInsets.only(bottom: 10, top: 4),
    child: Text(
      title.toUpperCase(),
      style: TextStyle(
        color: FastTheme.accentGold.withValues(alpha: 0.85),
        fontSize: 11.5,
        letterSpacing: 1.4,
        fontWeight: FontWeight.w700,
      ),
    ),
  );
}

class _PhaseTile extends StatelessWidget {
  final SkyPhaseEvent event;

  const _PhaseTile({required this.event});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final sign = AstroSigns.signNameFromLongitude(event.moon.longitude);
    return _card(
      context,
      leading: Text(
        _phaseGlyphs[event.type] ?? '🌑',
        style: const TextStyle(fontSize: 26),
      ),
      title: '${_phaseName(l, event.type)} · ${_deg(event.moon.degree)}° $sign',
      subtitle: _dateLine(context, event.time),
      trailing: _countdown(l, event.time),
    );
  }
}

class _EclipseTile extends StatelessWidget {
  final SkyEclipse eclipse;

  const _EclipseTile({required this.eclipse});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final body = eclipse.isSolar ? eclipse.sun : eclipse.moon;
    final sign = AstroSigns.signNameFromLongitude(body.longitude);
    final title =
        '${_eclipseName(l, eclipse.isSolar)} · ${_eclipseVariant(l, eclipse.variant)}';
    final subtitle =
        '${_deg(body.degree)}° $sign · ${_dateLine(context, eclipse.time)}';

    final parts = <String>[];
    final vis = eclipse.visibility;
    if (vis.visible) {
      parts.add(l.skyEclipseVisibleHere);
      if (vis.obscuration != null) {
        parts.add(l.skyEclipseObscuration(vis.obscuration!.round().toString()));
      }
    } else {
      parts.add(l.skyEclipseNotVisible);
      final next = vis.nextVisible;
      if (next != null) {
        parts.add(l.skyEclipseNextVisible(_dateLine(context, next.time)));
      }
    }

    return _card(
      context,
      leading: Text(
        _eclipseGlyphs[eclipse.type] ?? '☉',
        style: TextStyle(fontSize: 24, color: FastTheme.accentGoldLight),
      ),
      title: title,
      subtitle: '$subtitle\n${parts.join(' · ')}',
      trailing: _countdown(l, eclipse.time),
    );
  }
}

Widget _card(
  BuildContext context, {
  required Widget leading,
  required String title,
  required String subtitle,
  required String trailing,
}) {
  return Container(
    margin: const EdgeInsets.only(bottom: 10),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    decoration: BoxDecoration(
      color: FastTheme.cardBg,
      borderRadius: BorderRadius.circular(14),
      border: Border.all(color: FastTheme.border.withValues(alpha: 0.5)),
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        SizedBox(width: 34, child: Center(child: leading)),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  color: FastTheme.text,
                  fontSize: 14.5,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: TextStyle(
                  color: FastTheme.textMuted.withValues(alpha: 0.7),
                  fontSize: 12.5,
                  height: 1.35,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Text(
          trailing,
          style: TextStyle(
            color: FastTheme.accentGoldLight,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    ),
  );
}
