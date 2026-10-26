import 'dart:async';

import 'package:flutter/material.dart';

import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/sky_snapshot.dart';
import '../screens/sky_calendar_screen.dart';
import '../services/api_service.dart';

const _phaseGlyphs = {
  'new': '🌑',
  'waxing_crescent': '🌒',
  'first_quarter': '🌓',
  'waxing_gibbous': '🌔',
  'full': '🌕',
  'waning_gibbous': '🌖',
  'last_quarter': '🌗',
  'waning_crescent': '🌘',
};

const _planetGlyphs = {
  'sun': '☉',
  'moon': '☾',
  'mercury': '☿',
  'venus': '♀',
  'mars': '♂',
  'jupiter': '♃',
  'saturn': '♄',
  'uranus': '♅',
  'neptune': '♆',
  'pluto': '♇',
};

const _planetTr = {
  'sun': 'Güneş',
  'moon': 'Ay',
  'mercury': 'Merkür',
  'venus': 'Venüs',
  'mars': 'Mars',
  'jupiter': 'Jüpiter',
  'saturn': 'Satürn',
  'uranus': 'Uranüs',
  'neptune': 'Neptün',
  'pluto': 'Plüton',
};

const _planetEn = {
  'sun': 'Sun',
  'moon': 'Moon',
  'mercury': 'Mercury',
  'venus': 'Venus',
  'mars': 'Mars',
  'jupiter': 'Jupiter',
  'saturn': 'Saturn',
  'uranus': 'Uranus',
  'neptune': 'Neptune',
  'pluto': 'Pluto',
};

const _planetEs = {
  'sun': 'Sol',
  'moon': 'Luna',
  'mercury': 'Mercurio',
  'venus': 'Venus',
  'mars': 'Marte',
  'jupiter': 'Júpiter',
  'saturn': 'Saturno',
  'uranus': 'Urano',
  'neptune': 'Neptuno',
  'pluto': 'Plutón',
};

const _aspectTr = {
  'conjunction': 'kavuşum',
  'sextile': 'altmışlık',
  'square': 'kare',
  'trine': 'üçgen',
  'opposition': 'karşıt',
};

const _aspectEn = {
  'conjunction': 'conjunction',
  'sextile': 'sextile',
  'square': 'square',
  'trine': 'trine',
  'opposition': 'opposition',
};

const _aspectEs = {
  'conjunction': 'conjunción',
  'sextile': 'sextil',
  'square': 'cuadratura',
  'trine': 'trígono',
  'opposition': 'oposición',
};

String _planetName(String key, String lang) {
  final map = switch (lang) {
    'en' => _planetEn,
    'es' => _planetEs,
    _ => _planetTr,
  };
  return map[key] ?? key;
}

String _aspectName(String key, String lang) {
  final map = switch (lang) {
    'en' => _aspectEn,
    'es' => _aspectEs,
    _ => _aspectTr,
  };
  return map[key] ?? key;
}

String _phaseName(AppLocalizations l, String key) => switch (key) {
  'waxing_crescent' => l.skyPhaseWaxingCrescent,
  'first_quarter' => l.skyPhaseFirstQuarter,
  'waxing_gibbous' => l.skyPhaseWaxingGibbous,
  'full' => l.skyPhaseFull,
  'waning_gibbous' => l.skyPhaseWaningGibbous,
  'last_quarter' => l.skyPhaseLastQuarter,
  'waning_crescent' => l.skyPhaseWaningCrescent,
  _ => l.skyPhaseNew,
};

String _speedName(AppLocalizations l, String key) => switch (key) {
  'slow' => l.skySpeedSlow,
  'fast' => l.skySpeedFast,
  _ => l.skySpeedNormal,
};

String _deg(double value) {
  final rounded = (value * 10).round() / 10;
  return rounded == rounded.roundToDouble()
      ? rounded.toInt().toString()
      : rounded.toStringAsFixed(1);
}

String _clock(BuildContext context, DateTime dt) {
  final local = dt.toLocal();
  return MaterialLocalizations.of(
    context,
  ).formatTimeOfDay(TimeOfDay.fromDateTime(local), alwaysUse24HourFormat: true);
}

/// Hub'ın üstünde duran ince gökyüzü şeridi. Hata durumunda tamamen gizlenir.
class SkyStrip extends StatefulWidget {
  const SkyStrip({super.key});

  @override
  State<SkyStrip> createState() => _SkyStripState();
}

class _SkyStripState extends State<SkyStrip> {
  static SkySnapshot? _cache;
  static const _refresh = Duration(minutes: 10);

  SkySnapshot? _sky;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    final cached = _cache;
    if (cached != null &&
        DateTime.now().difference(cached.fetchedAt) < _refresh) {
      _sky = cached;
    } else {
      _load();
    }
    _timer = Timer.periodic(_refresh, (_) => _load());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final json = await ApiService().sky();
      final snap = SkySnapshot.fromJson(json);
      _cache = snap;
      if (!mounted) return;
      setState(() => _sky = snap);
    } catch (_) {
      // Süs katmanı: sessizce gizlenir, hub'ı etkilemez.
    }
  }

  @override
  Widget build(BuildContext context) {
    final sky = _sky;
    if (sky == null) return const SizedBox.shrink();
    final l = AppLocalizations.of(context);
    final lang = Localizations.localeOf(context).languageCode;
    final sign = AstroSigns.localizedNameOf(AstroSigns.signNameFromLongitude(sky.moonLongitude), l);
    final phase = _phaseName(l, sky.phaseKey);
    final hour = _planetName(sky.hourRuler, lang);

    final detail = StringBuffer(phase);
    detail.write(' · ${_speedName(l, sky.speedKey)}');
    if (sky.voidOfCourse) detail.write(' · ${l.skyVoid}');
    detail.write(' · ${_planetGlyphs[sky.hourRuler] ?? ''} $hour');

    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => showModalBottomSheet<void>(
            context: context,
            isScrollControlled: true,
            backgroundColor: FastTheme.bgSecondary,
            shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            ),
            builder: (_) => SkyDetailSheet(sky: sky),
          ),
          child: Ink(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: FastTheme.accentGold.withValues(alpha: 0.2),
              ),
              gradient: LinearGradient(
                colors: [
                  FastTheme.primary.withValues(alpha: 0.22),
                  FastTheme.accentGold.withValues(alpha: 0.08),
                ],
              ),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: Row(
              children: [
                Text(
                  _phaseGlyphs[sky.phaseKey] ?? '☾',
                  style: const TextStyle(fontSize: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              l.skyMoonLine(sign, _deg(sky.moonDegree)),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                color: FastTheme.text,
                                fontSize: 13.5,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 0.1,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '%${sky.illumination.round()}',
                            style: TextStyle(
                              color: FastTheme.accentGoldLight,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        detail.toString(),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: sky.voidOfCourse
                              ? FastTheme.accentGoldLight
                              : FastTheme.textMuted.withValues(alpha: 0.7),
                          fontSize: 11.5,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 4),
                Icon(
                  Icons.keyboard_arrow_right,
                  size: 18,
                  color: FastTheme.textMuted.withValues(alpha: 0.55),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class SkyDetailSheet extends StatelessWidget {
  final SkySnapshot sky;

  const SkyDetailSheet({super.key, required this.sky});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final lang = Localizations.localeOf(context).languageCode;
    final moonSign = AstroSigns.localizedNameOf(AstroSigns.signNameFromLongitude(sky.moonLongitude), l);
    final sunSign = AstroSigns.localizedName((sky.sunSign + 3) % 12, l);
    final phase = _phaseName(l, sky.phaseKey);
    final hour = _planetName(sky.hourRuler, lang);
    final nextHour = _planetName(sky.nextHourRuler, lang);
    final period = sky.dayHour ? l.skyDayHour : l.skyNightHour;
    final range =
        '${_clock(context, sky.hourStart)}–${_clock(context, sky.hourEnd)}';
    final voidUntil = sky.voidUntil;

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(22, 12, 22, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Center(
              child: Container(
                width: 38,
                height: 4,
                decoration: BoxDecoration(
                  color: FastTheme.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 18),
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(
                  _phaseGlyphs[sky.phaseKey] ?? '☾',
                  style: const TextStyle(fontSize: 42),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        l.skyTitle,
                        style: TextStyle(
                          color: FastTheme.textMuted.withValues(alpha: 0.65),
                          fontSize: 12,
                          letterSpacing: 1.4,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        phase,
                        style: TextStyle(
                          color: FastTheme.text,
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        l.skyIllumination(sky.illumination.round().toString()),
                        style: TextStyle(
                          color: FastTheme.textMuted.withValues(alpha: 0.75),
                          fontSize: 12.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            _InfoRow(
              glyph: '☾',
              title: l.skyMoonLine(moonSign, _deg(sky.moonDegree)),
              subtitle:
                  '${l.skyPerDay(sky.moonSpeed.toStringAsFixed(2))} · ${l.skyMoonSpeed}: ${_speedName(l, sky.speedKey)}',
            ),
            _InfoRow(
              glyph: sky.voidOfCourse ? '◌' : '≈',
              title: sky.voidOfCourse ? l.skyVoid : l.skyNotVoid,
              subtitle: sky.voidOfCourse
                  ? (voidUntil == null
                        ? null
                        : l.skyVoidUntil(_clock(context, voidUntil)))
                  : null,
              highlight: sky.voidOfCourse,
            ),
            _InfoRow(
              glyph: _planetGlyphs[sky.hourRuler] ?? '♃',
              title: l.skyPlanetHour(hour),
              subtitle:
                  '${sky.hourIndex}. $period · $range\n${l.skyNextHour(nextHour)}',
            ),
            _InfoRow(
              glyph: '☉',
              title: l.skySunLine(sunSign, _deg(sky.sunDegree)),
            ),
            const SizedBox(height: 8),
            Divider(color: FastTheme.border.withValues(alpha: 0.6), height: 24),
            Text(
              l.skyAspects,
              style: TextStyle(
                color: FastTheme.textMuted.withValues(alpha: 0.65),
                fontSize: 12,
                letterSpacing: 1.1,
              ),
            ),
            const SizedBox(height: 8),
            if (sky.aspects.isEmpty)
              Text(
                l.skyNoAspects,
                style: TextStyle(
                  color: FastTheme.textMuted.withValues(alpha: 0.6),
                  fontSize: 13,
                ),
              )
            else
              ...sky.aspects.map(
                (a) => Padding(
                  padding: const EdgeInsets.only(bottom: 7),
                  child: Row(
                    children: [
                      Text(
                        _planetGlyphs[a.planet] ?? '·',
                        style: TextStyle(
                          color: FastTheme.accentGoldLight,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(width: 9),
                      Expanded(
                        child: Text(
                          '${_planetName(a.planet, lang)} · ${_aspectName(a.type, lang)} · ${a.orb.toStringAsFixed(1)}°',
                          style: TextStyle(
                            color: FastTheme.text,
                            fontSize: 13.5,
                          ),
                        ),
                      ),
                      Icon(
                        a.applying ? Icons.trending_up : Icons.trending_down,
                        size: 15,
                        color: a.applying
                            ? FastTheme.success
                            : FastTheme.textMuted.withValues(alpha: 0.45),
                      ),
                    ],
                  ),
                ),
              ),
            if (sky.retrogrades.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                '${l.skyRetro}: ${sky.retrogrades.map((p) => _planetName(p, lang)).join(', ')}',
                style: TextStyle(
                  color: FastTheme.textMuted.withValues(alpha: 0.7),
                  fontSize: 12,
                ),
              ),
            ],
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () {
                  Navigator.of(context).pop();
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => const SkyCalendarScreen(),
                    ),
                  );
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: FastTheme.accentGold,
                  side: BorderSide(
                    color: FastTheme.accentGold.withValues(alpha: 0.5),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                icon: const Icon(Icons.calendar_month_outlined, size: 18),
                label: Text(l.skyCalendarOpen),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String glyph;
  final String title;
  final String? subtitle;
  final bool highlight;

  const _InfoRow({
    required this.glyph,
    required this.title,
    this.subtitle,
    this.highlight = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 26,
            child: Text(
              glyph,
              style: TextStyle(
                color: highlight
                    ? FastTheme.accentGoldLight
                    : FastTheme.accentGold,
                fontSize: 17,
              ),
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: highlight
                        ? FastTheme.accentGoldLight
                        : FastTheme.text,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    subtitle!,
                    style: TextStyle(
                      color: FastTheme.textMuted.withValues(alpha: 0.65),
                      fontSize: 12.5,
                      height: 1.35,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
