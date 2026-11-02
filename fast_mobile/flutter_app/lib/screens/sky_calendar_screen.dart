import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:share_plus/share_plus.dart';

import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/sky_calendar.dart';
import '../models/sky_moon_timing.dart';
import '../models/sky_retro_calendar.dart';
import '../models/sky_moon_guide.dart';
import '../models/chart_data.dart';
import '../models/chart_labels.dart';
import '../models/eclipse_personal_impact.dart';
import '../models/eclipse_personal_prompts.dart';
import '../models/sky_snapshot.dart';
import '../services/api_service.dart';
import '../services/chart_service.dart';
import '../services/social_service.dart';
import '../models/sky_event_export.dart';
import '../widgets/moon_timing_card.dart';
import '../widgets/pro_gate.dart';
import '../widgets/sky_daily_reading_card.dart';
import '../widgets/retro_calendar_card.dart';
import '../widgets/moon_guide_card.dart';

String _calendarText(BuildContext context, String tr, String en, String es) =>
    switch (Localizations.localeOf(context).languageCode) {
      'tr' => tr,
      'es' => es,
      _ => en,
    };

Future<void> _exportEvent(
  BuildContext context,
  DateTime time,
  String title,
  String description,
) async {
  try {
    final ics = buildSkyEventIcs(
      time: time,
      title: title,
      description: description,
    );
    final box = context.findRenderObject() as RenderBox?;
    await Share.shareXFiles(
      [
        XFile.fromData(
          utf8.encode(ics),
          mimeType: 'text/calendar',
          name: 'holavon-event.ics',
        ),
      ],
      fileNameOverrides: const ['holavon-event.ics'],
      subject: title,
      sharePositionOrigin: box == null
          ? null
          : box.localToGlobal(Offset.zero) & box.size,
    );
  } catch (_) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _calendarText(
              context,
              'Takvim dosyası paylaşılamadı.',
              'Unable to share calendar file.',
              'No se pudo compartir el calendario.',
            ),
          ),
        ),
      );
    }
  }
}

const _phaseGlyphs = {
  'new_moon': '🌑',
  'first_quarter': '🌓',
  'full_moon': '🌕',
  'last_quarter': '🌗',
};

const _eclipseGlyphs = {'solar': '☉', 'lunar': '☾'};

String _deg(double value) {
  final rounded = (value * 10).round() / 10;
  return rounded == rounded.roundToDouble()
      ? rounded.toInt().toString()
      : rounded.toStringAsFixed(1);
}

String _phaseName(AppLocalizations l, String type) => switch (type) {
  'new_moon' => l.skyPhaseNew,
  'first_quarter' => l.skyPhaseFirstQuarter,
  'full_moon' => l.skyPhaseFull,
  'last_quarter' => l.skyPhaseLastQuarter,
  _ => l.skyFullMoon,
};

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

/// Ay takvimi kartı için kısa tarih (ör. "1 Kas · 09:20").
String _shortDateLine(BuildContext context, DateTime time) {
  final local = time.toLocal();
  final date = MaterialLocalizations.of(context).formatShortMonthDay(local);
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
  /// Test/önizleme için dışarıdan servis verilebilir.
  final ApiService? api;

  /// Test/önizleme için Pro durumu dışarıdan verilebilir.
  final Future<bool> Function()? proLoader;

  const SkyCalendarScreen({super.key, this.api, this.proLoader});

  @override
  State<SkyCalendarScreen> createState() => _SkyCalendarScreenState();
}

class _SkyCalendarScreenState extends State<SkyCalendarScreen> {
  late Future<SkyCalendar> _future;
  late Future<SkyMoonCalendar?> _moon;
  late Future<SkyMoonTiming?> _timing;
  late Future<SkyRetroCalendar?> _retro;
  late Future<SkyMoonGuide?> _guide;
  late Future<SkySnapshot?> _reading;
  Timer? _readingTimer;
  String _filter = 'all';

  ApiService get _api => widget.api ?? ApiService();

  @override
  void initState() {
    super.initState();
    _future = _load();
    _moon = _loadMoon();
    _timing = _loadTiming();
    _retro = _loadRetro();
    _guide = _loadMoonGuide();
    _reading = _loadReading();
    // Yorum, Ay burcu değiştiğinde kendiliğinden tazelensin.
    _readingTimer = Timer.periodic(const Duration(minutes: 15), (_) {
      if (!mounted) return;
      setState(() => _reading = _loadReading());
    });
  }

  @override
  void dispose() {
    _readingTimer?.cancel();
    super.dispose();
  }

  Future<SkyCalendar> _load() async =>
      SkyCalendar.fromJson(await _api.skyCalendar());

  /// Ay takvimi ucu henüz yayında değilse kart gizlenir; takvim çalışmaya
  /// devam eder.
  Future<SkyMoonCalendar?> _loadMoon() async {
    try {
      return SkyMoonCalendar.fromJson(await _api.skyMoonCalendar());
    } catch (_) {
      return null;
    }
  }

  /// Günün yorumu `/api/sky`'den beslenir; hata durumunda kart gizlenir.
  Future<SkySnapshot?> _loadReading() async {
    try {
      return SkySnapshot.fromJson(await _api.sky());
    } catch (_) {
      return null;
    }
  }

  /// VOC ve doğru zaman pencereleri; uç yoksa kart gizlenir.
  Future<SkyMoonTiming?> _loadTiming() async {
    try {
      return SkyMoonTiming.fromJson(await _api.skyMoonTiming());
    } catch (_) {
      return null;
    }
  }

  /// Retro durakları ve gölge tarihleri; uç erişilemezse diğer takvim sürer.
  Future<SkyRetroCalendar?> _loadRetro() async {
    try {
      return SkyRetroCalendar.fromJson(await _api.skyRetroCalendar());
    } catch (_) {
      return null;
    }
  }

  /// Faz ve menzil rehberi; hata alırsa temel takvim görünmeye devam eder.
  Future<SkyMoonGuide?> _loadMoonGuide() async {
    try {
      return SkyMoonGuide.fromJson(await _api.skyMoonGuide());
    } catch (_) {
      return null;
    }
  }

  /// Kişisel tutulma teması yalnızca oturum sahibinin kendi private doğum
  /// kaydından, tam saat ve koordinat varsa hesaplanır. Başka kayıtlı profiller
  /// veya ChartProvider'daki son açılmış harita asla kullanılmaz.
  Future<ChartData?> _loadOwnNatalForEclipse() async {
    try {
      if (!SocialService.enabled) return null;
      final birth = await SocialService.myBirthInfo();
      final date = birth?.date;
      final time = birth?.time;
      final lat = birth?.lat;
      final lon = birth?.lon;
      if (date == null ||
          DateTime.tryParse(date) == null ||
          time == null ||
          lat == null ||
          lon == null ||
          lat.abs() > 90 ||
          lon.abs() > 180) {
        return null;
      }
      final timeMatch = RegExp(r'^\d{1,2}:\d{2}').firstMatch(time);
      if (timeMatch == null) return null;
      final place = [
        birth?.city,
        birth?.country,
      ].whereType<String>().where((part) => part.trim().isNotEmpty).join(', ');
      final chartService = ChartService();
      try {
        return await chartService.natal(
          tarih: date,
          saat: timeMatch.group(0)!,
          lat: lat,
          lon: lon,
          place: place.isEmpty ? null : place,
        );
      } finally {
        chartService.dispose();
      }
    } catch (_) {
      return null;
    }
  }

  void _reload() {
    setState(() {
      _future = _load();
      _moon = _loadMoon();
      _timing = _loadTiming();
      _retro = _loadRetro();
      _guide = _loadMoonGuide();
      _reading = _loadReading();
    });
  }

  void _reloadMoon() {
    if (mounted) setState(() => _moon = _loadMoon());
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
          final events = <(DateTime, Widget)>[
            if (_filter != 'eclipses')
              ...cal.phases.map((e) => (e.time, _PhaseTile(event: e))),
            if (_filter != 'phases')
              ...cal.eclipses.map((e) => (e.time, _EclipseTile(eclipse: e))),
          ]..sort((a, b) => a.$1.compareTo(b.$1));
          return ListView(
            padding: EdgeInsets.fromLTRB(
              20,
              12,
              20,
              32 + MediaQuery.of(context).viewPadding.bottom,
            ),
            children: [
              ProGate(
                icon: Icons.nights_stay_outlined,
                title: l.skyReadingTitle,
                body: l.proLockReadingBody,
                statusLoader: widget.proLoader,
                child: FutureBuilder<SkySnapshot?>(
                  future: _reading,
                  builder: (context, rs) {
                    final sky = rs.data;
                    if (sky == null) return const SizedBox.shrink();
                    return SkyDailyReadingCard(sky: sky);
                  },
                ),
              ),
              ProGate(
                icon: Icons.calendar_month_outlined,
                title: l.skyMoonCalendarTitle,
                body: l.proLockMoonBody,
                statusLoader: widget.proLoader,
                child: FutureBuilder<SkyMoonCalendar?>(
                  future: _moon,
                  builder: (context, ms) {
                    final moon = ms.data;
                    if (moon == null) return const SizedBox.shrink();
                    return _MoonSection(moon: moon, onElapsed: _reloadMoon);
                  },
                ),
              ),
              ProGate(
                icon: Icons.hourglass_disabled_outlined,
                title: l.skyMoonTimingTitle,
                body: l.proLockTimingBody,
                statusLoader: widget.proLoader,
                child: FutureBuilder<SkyMoonTiming?>(
                  future: _timing,
                  builder: (context, ts) {
                    final timing = ts.data;
                    if (timing == null) return const SizedBox.shrink();
                    return MoonTimingCard(
                      timing: timing,
                      onExport: (time, title, description) =>
                          _exportEvent(context, time, title, description),
                    );
                  },
                ),
              ),
              ProGate(
                icon: Icons.sync,
                title: l.skyRetroTitle,
                body: l.proLockRetroBody,
                statusLoader: widget.proLoader,
                child: FutureBuilder<SkyRetroCalendar?>(
                  future: _retro,
                  builder: (context, rs) {
                    final retro = rs.data;
                    if (retro == null) return const SizedBox.shrink();
                    return RetroCalendarCard(calendar: retro);
                  },
                ),
              ),
              ProGate(
                icon: Icons.auto_awesome_outlined,
                title: l.skyMoonGuideTitle,
                body: l.proLockMoonGuideBody,
                statusLoader: widget.proLoader,
                child: FutureBuilder<SkyMoonGuide?>(
                  future: _guide,
                  builder: (context, gs) {
                    final guide = gs.data;
                    if (guide == null) return const SizedBox.shrink();
                    return MoonGuideCard(guide: guide);
                  },
                ),
              ),
              if (cal.eclipses.isNotEmpty)
                ProGate(
                  icon: Icons.brightness_3_outlined,
                  title: l.skyEclipseGuideTitle,
                  body: l.proLockEclipseBody,
                  statusLoader: widget.proLoader,
                  child: _EclipseGuide(
                    eclipses: cal.eclipses,
                    loadOwnNatal: _loadOwnNatalForEclipse,
                  ),
                ),
              Wrap(
                spacing: 8,
                children: [
                  for (final entry in {
                    'all': _calendarText(context, 'Tümü', 'All', 'Todo'),
                    'phases': l.skyCalendarPhases,
                    'eclipses': l.skyCalendarEclipses,
                  }.entries)
                    ChoiceChip(
                      label: Text(entry.value),
                      selected: _filter == entry.key,
                      onSelected: (_) => setState(() => _filter = entry.key),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                _calendarText(
                  context,
                  'Olaylar tarih sırasıyla • Takvime eklemek için dokun',
                  'Events in date order • Tap to add to your calendar',
                  'Eventos por fecha • Toca para añadir al calendario',
                ),
                style: TextStyle(color: FastTheme.textMuted, fontSize: 12),
              ),
              const SizedBox(height: 12),
              if (events.isEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 24),
                  child: Center(
                    child: Text(
                      l.skyCalendarEmpty,
                      style: TextStyle(
                        color: FastTheme.textMuted.withValues(alpha: 0.7),
                      ),
                    ),
                  ),
                )
              else
                ...events.map((event) => event.$2),
            ],
          );
        },
      ),
    );
  }
}

class _MoonSection extends StatelessWidget {
  final SkyMoonCalendar moon;
  final VoidCallback onElapsed;

  const _MoonSection({required this.moon, required this.onElapsed});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final signIndex = (moon.sign + 3) % 12; // AstroSigns sırası: Oğlak = 0
    final signName = AstroSigns.localizedName(signIndex, l);
    final window = [
      if (moon.ingress != null) _shortDateLine(context, moon.ingress!),
      if (moon.egress != null) _shortDateLine(context, moon.egress!),
    ].join(' – ');
    final next = moon.ingresses.take(4).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: moon.egress == null
              ? null
              : () => _exportEvent(
                  context,
                  moon.egress!,
                  l.skyMoonInSign(signName),
                  '$window • Holavon',
                ),
          child: Container(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  FastTheme.accentGold.withValues(alpha: 0.18),
                  FastTheme.cardBg,
                ],
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: FastTheme.accentGold.withValues(alpha: 0.35),
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  AstroSigns.symbols[signIndex],
                  style: TextStyle(
                    fontSize: 30,
                    color: FastTheme.accentGoldLight,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        l.skyMoonCalendarTitle,
                        style: TextStyle(
                          color: FastTheme.accentGoldLight,
                          fontSize: 10,
                          letterSpacing: 1.6,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        '${l.skyMoonInSign(signName)} · ${_deg(moon.degree)}°',
                        style: TextStyle(
                          color: FastTheme.text,
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      if (window.isNotEmpty) ...[
                        const SizedBox(height: 3),
                        Text(
                          window,
                          style: TextStyle(
                            color: FastTheme.textMuted.withValues(alpha: 0.85),
                            fontSize: 12,
                            height: 1.3,
                          ),
                        ),
                      ],
                      if (moon.egress != null) ...[
                        const SizedBox(height: 6),
                        _LiveCountdown(
                          endsAt: moon.egress!,
                          onElapsed: onElapsed,
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        if (next.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(
            l.skyMoonNextChanges,
            style: TextStyle(
              color: FastTheme.textMuted,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          for (final entry in next)
            _MoonIngressTile(
              entry: entry,
              onTap: () {
                final i = (entry.sign + 3) % 12;
                final name = AstroSigns.localizedName(i, l);
                _exportEvent(
                  context,
                  entry.time,
                  l.skyMoonEnters(name),
                  '${_shortDateLine(context, entry.time)} • Holavon',
                );
              },
            ),
        ],
        const SizedBox(height: 16),
      ],
    );
  }
}

class _MoonIngressTile extends StatelessWidget {
  final SkyMoonIngress entry;
  final VoidCallback onTap;

  const _MoonIngressTile({required this.entry, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final i = (entry.sign + 3) % 12;
    final name = AstroSigns.localizedName(i, l);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: FastTheme.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: FastTheme.border.withValues(alpha: 0.5)),
        ),
        child: Row(
          children: [
            Text(
              AstroSigns.symbols[i],
              style: TextStyle(color: FastTheme.accentGoldLight, fontSize: 18),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                l.skyMoonEnters(name),
                style: TextStyle(
                  color: FastTheme.text,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              _shortDateLine(context, entry.time),
              style: TextStyle(
                color: FastTheme.textMuted.withValues(alpha: 0.8),
                fontSize: 11.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Burç değişimine kalan süre; 30 saniyede bir tazelenir.
class _LiveCountdown extends StatefulWidget {
  final DateTime endsAt;
  final VoidCallback onElapsed;

  const _LiveCountdown({required this.endsAt, required this.onElapsed});

  @override
  State<_LiveCountdown> createState() => _LiveCountdownState();
}

class _LiveCountdownState extends State<_LiveCountdown> {
  Timer? _timer;
  bool _fired = false;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (!mounted) return;
      setState(() {});
      if (!_fired && !widget.endsAt.isAfter(DateTime.now())) {
        _fired = true;
        widget.onElapsed();
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final diff = widget.endsAt.difference(DateTime.now());
    String value;
    if (diff.inMinutes < 1) {
      value = l.skyCalendarNow;
    } else if (diff.inDays > 0) {
      value = l.skyMoonDaysHours('${diff.inDays}', '${diff.inHours % 24}');
    } else if (diff.inHours > 0) {
      value = l.skyMoonHoursMinutes(
        '${diff.inHours}',
        '${diff.inMinutes % 60}',
      );
    } else {
      value = l.skyMoonMinutes('${diff.inMinutes}');
    }
    return Row(
      children: [
        Icon(
          Icons.hourglass_bottom,
          size: 14,
          color: FastTheme.accentGoldLight,
        ),
        const SizedBox(width: 5),
        Text(
          l.skyMoonRemaining(value),
          style: TextStyle(
            color: FastTheme.accentGoldLight,
            fontSize: 12.5,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _PhaseTile extends StatelessWidget {
  final SkyPhaseEvent event;

  const _PhaseTile({required this.event});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final sign = AstroSigns.localizedNameOf(
      AstroSigns.signNameFromLongitude(event.moon.longitude),
      l,
    );
    return _card(
      context,
      leading: Text(
        _phaseGlyphs[event.type] ?? '🌑',
        style: const TextStyle(fontSize: 26),
      ),
      title: '${_phaseName(l, event.type)} · ${_deg(event.moon.degree)}° $sign',
      subtitle: _dateLine(context, event.time),
      trailing: _countdown(l, event.time),
      onTap: () => _exportEvent(
        context,
        event.time,
        _phaseName(l, event.type),
        '${_deg(event.moon.degree)}° $sign • Holavon',
      ),
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
    final sign = AstroSigns.localizedNameOf(
      AstroSigns.signNameFromLongitude(body.longitude),
      l,
    );
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
      if (vis.localStart != null && vis.localEnd != null) {
        parts.add(
          l.skyEclipseLocalWindow(
            _shortDateLine(context, vis.localStart!),
            _shortDateLine(context, vis.localEnd!),
          ),
        );
      }
      if (vis.saros != null && vis.sarosMember != null) {
        parts.add(
          l.skyEclipseSaros(vis.saros.toString(), vis.sarosMember.toString()),
        );
      }
    } else {
      parts.add(l.skyEclipseNotVisible);
      final next = vis.nextVisible;
      if (next != null) {
        parts.add(l.skyEclipseNextVisible(_dateLine(context, next.time)));
        if (next.localStart != null && next.localEnd != null) {
          parts.add(
            l.skyEclipseLocalWindow(
              _shortDateLine(context, next.localStart!),
              _shortDateLine(context, next.localEnd!),
            ),
          );
        }
        if (next.saros != null && next.sarosMember != null) {
          parts.add(
            l.skyEclipseSaros(
              next.saros.toString(),
              next.sarosMember.toString(),
            ),
          );
        }
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
      onTap: () => _exportEvent(
        context,
        eclipse.time,
        title,
        '$subtitle\n${parts.join(' · ')}\nHolavon',
      ),
    );
  }
}

/// Temel tutulma tarihi/yerel görünürlüğü ücretsiz kalır. Pro kartı, yalnızca
/// mevcut oturum sahibinin kendi tam doğum kaydı varsa natal ev/açı temasını
/// ekler; yoksa başka bir kayıtlı kişinin haritasına düşmez.
class _EclipseGuide extends StatefulWidget {
  final List<SkyEclipse> eclipses;
  final Future<ChartData?> Function() loadOwnNatal;

  const _EclipseGuide({required this.eclipses, required this.loadOwnNatal});

  @override
  State<_EclipseGuide> createState() => _EclipseGuideState();
}

class _EclipseGuideState extends State<_EclipseGuide> {
  late final Future<ChartData?> _ownNatal;

  @override
  void initState() {
    super.initState();
    _ownNatal = widget.loadOwnNatal();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return FutureBuilder<ChartData?>(
      future: _ownNatal,
      builder: (context, snapshot) {
        final natal = snapshot.data;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (snapshot.connectionState == ConnectionState.waiting)
              const LinearProgressIndicator(minHeight: 2),
            for (var i = 0; i < widget.eclipses.length; i++) ...[
              if (i > 0) const SizedBox(height: 12),
              _eclipsePrompt(l, widget.eclipses[i]),
              if (natal != null) ...[
                const SizedBox(height: 6),
                _personalImpact(l, widget.eclipses[i], natal),
              ],
            ],
            if (natal == null &&
                snapshot.connectionState != ConnectionState.waiting) ...[
              const SizedBox(height: 10),
              Text(
                l.skyEclipseBirthDataNeeded,
                style: TextStyle(
                  color: FastTheme.textMuted.withValues(alpha: 0.85),
                  fontSize: 11,
                  height: 1.35,
                ),
              ),
            ],
            const SizedBox(height: 12),
            Text(
              l.skyEclipseReflectionNote,
              style: TextStyle(
                color: FastTheme.textMuted.withValues(alpha: 0.7),
                fontSize: 11,
                height: 1.35,
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _personalImpact(
    AppLocalizations l,
    SkyEclipse eclipse,
    ChartData natal,
  ) {
    final impact = EclipsePersonalImpact.calculate(eclipse, natal);
    final language = Localizations.localeOf(context).languageCode;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (impact.house != null)
          Text(
            l.skyEclipseHouseImpact(
              l.chartHouseNumber(impact.house!),
              EclipsePersonalPrompts.houseTheme(impact.house!, language),
            ),
            style: TextStyle(color: FastTheme.text, fontSize: 12, height: 1.4),
          ),
        for (final aspect in impact.aspects)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              l.skyEclipsePersonalAspectLine(
                chartAspectLabel(l, aspect.type),
                chartPlanetLabel(l, aspect.planet),
                aspect.orb.toStringAsFixed(1),
              ),
              style: TextStyle(
                color: FastTheme.accentGoldLight,
                fontSize: 11,
                height: 1.3,
              ),
            ),
          ),
      ],
    );
  }

  Widget _eclipsePrompt(AppLocalizations l, SkyEclipse eclipse) {
    final body = eclipse.isSolar ? eclipse.sun : eclipse.moon;
    final sign = AstroSigns.localizedNameOf(
      AstroSigns.signNameFromLongitude(body.longitude),
      l,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '${_eclipseName(l, eclipse.isSolar)} · ${_deg(body.degree)}° $sign',
          style: TextStyle(
            color: FastTheme.accentGoldLight,
            fontSize: 13,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          eclipse.isSolar
              ? l.skyEclipseReflectionSolar
              : l.skyEclipseReflectionLunar,
          style: TextStyle(
            color: FastTheme.textMuted,
            fontSize: 12,
            height: 1.4,
          ),
        ),
      ],
    );
  }
}

Widget _card(
  BuildContext context, {
  required Widget leading,
  required String title,
  required String subtitle,
  required String trailing,
  VoidCallback? onTap,
}) {
  return InkWell(
    onTap: onTap,
    borderRadius: BorderRadius.circular(14),
    child: Container(
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
    ),
  );
}
