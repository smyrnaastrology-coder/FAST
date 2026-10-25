import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/chart_data.dart';
import '../models/chart_labels.dart';
import '../models/chart_frame.dart';
import '../screens/chart_explorer_screen.dart';

/// SolarFire tarzı çok katmanlı natal / bi-wheel çarkı.
///
/// Yükselen (ASC) her zaman sol-orta noktaya (doğu ufku) kilitlenir; burçlar
/// saat yönünün tersine ilerler. Dış halkada burç sembolleri, içeride natal
/// gezegenler, bi-wheel modunda transit gezegenler natalın DIŞINDA çizilir.
class ChartWheel extends StatelessWidget {
  final ChartData data;
  final double size;
  final List<PlanetPos>? outerPlanets;
  final List<HouseCusp>? outerHouses;
  final bool showAspectLines;
  final bool lightTheme;
  final bool showControls;
  final DateTime? initialDate;
  final ChartFrameLoader? loadFrame;
  final String title;
  final String subtitle;
  final List<ChartTimeUnit> timeUnits;

  const ChartWheel({
    super.key,
    required this.data,
    this.size = 320,
    this.outerPlanets,
    this.outerHouses,
    this.showAspectLines = true,
    this.lightTheme = false,
    this.showControls = true,
    this.initialDate,
    this.loadFrame,
    this.title = 'Natal',
    this.subtitle = '',
    this.timeUnits = ChartTimeUnit.values,
  });

  @override
  Widget build(BuildContext context) {
    Widget drawing(double extent) => SizedBox(
      width: extent,
      height: extent,
      child: ColoredBox(
        color: lightTheme ? Colors.white : const Color(0xFF0D1017),
        child: CustomPaint(
          painter: _WheelPainter(
            data: data,
            outerPlanets: outerPlanets,
            outerHouses: outerHouses,
            showAspectLines: showAspectLines,
            lightTheme: lightTheme,
          ),
        ),
      ),
    );
    if (!showControls) return drawing(size);
    return Stack(
      alignment: Alignment.topRight,
      children: [
        InteractiveViewer(minScale: 1, maxScale: 5, child: drawing(size)),
        if (showControls)
          IconButton(
            tooltip: 'Tam ekran • zaman / tema / paylaş',
            icon: Icon(
              Icons.fullscreen,
              color: lightTheme ? Colors.black : Colors.white,
            ),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => ChartExplorerScreen(
                    initial: ChartFrame(
                      data: data,
                      outerPlanets: outerPlanets,
                      outerHouses: outerHouses,
                      title: title,
                      subtitle: subtitle,
                    ),
                    initialDate:
                        initialDate ??
                        DateTime.tryParse(
                          '${data.meta.date} ${data.meta.time}',
                        ) ??
                        DateTime.now(),
                    loadFrame: loadFrame,
                    lightTheme: lightTheme,
                    timeUnits: timeUnits,
                  ),
                ),
              );
            },
          ),
      ],
    );
  }
}

class _Glyph {
  final PlanetPos planet;
  final double actual;
  double display;
  _Glyph(this.planet, this.actual) : display = actual;
}

class _WheelPainter extends CustomPainter {
  final ChartData data;
  final List<PlanetPos>? outerPlanets;
  final List<HouseCusp>? outerHouses;
  final bool showAspectLines;
  final bool lightTheme;
  Color get _ink =>
      lightTheme ? const Color(0xFF131722) : const Color(0xFFF2F4FA);
  Color get _gold =>
      lightTheme ? const Color(0xFF795400) : const Color(0xFFE6C57A);
  Color get _border =>
      lightTheme ? const Color(0xFF545E70) : const Color(0xFF8290A7);
  Color get _muted =>
      lightTheme ? const Color(0xFF374151) : const Color(0xFFBBC4D4);
  Color get _bg => lightTheme ? Colors.white : const Color(0xFF0D1017);
  Color get _retro =>
      lightTheme ? const Color(0xFF9D261A) : const Color(0xFFFFBF80);

  _WheelPainter({
    required this.data,
    this.outerPlanets,
    this.outerHouses,
    this.showAspectLines = true,
    this.lightTheme = false,
  });

  static const _fire = Color(0xFFFF8A65);
  static const _earth = Color(0xFF81C784);
  static const _air = Color(0xFFFFD54F);
  static const _water = Color(0xFF4FC3F7);

  Color _signColor(int sign) {
    if (lightTheme) {
      return const [
        Color(0xFFB0371B),
        Color(0xFF286B30),
        Color(0xFF826200),
        Color(0xFF005A95),
      ][sign % 4];
    }
    switch (sign % 12) {
      case 0:
      case 4:
      case 8:
        return _fire;
      case 1:
      case 5:
      case 9:
        return _earth;
      case 2:
      case 6:
      case 10:
        return _air;
      default:
        return _water;
    }
  }

  Color _aspectColor(String type) {
    switch (type.toLowerCase()) {
      case 'trine':
        return const Color(0xFF81C784);
      case 'sextile':
        return const Color(0xFF4DD0E1);
      case 'square':
        return const Color(0xFFE57373);
      case 'opposition':
        return const Color(0xFFFF8A65);
      case 'conjunction':
        return _gold;
      default:
        return Colors.white70;
    }
  }

  double _theta(double lon, double ascLon) {
    // 180° = sol (ASC). Zodiac boylamı arttıkça saat yönünün tersine gider.
    return math.pi + (ascLon - lon) * math.pi / 180.0;
  }

  Offset _pos(double lon, double r, Offset c, double ascLon) {
    final a = _theta(lon, ascLon);
    return Offset(c.dx + r * math.cos(a), c.dy + r * math.sin(a));
  }

  /// Gezegenleri çakışmayacak şekilde en büyük boşluktan başlayarak açar.
  List<_Glyph> _layout(List<PlanetPos> planets, double minSep) {
    if (planets.isEmpty) return const [];
    final items = planets.map((p) => _Glyph(p, p.lon)).toList()
      ..sort((a, b) => a.actual.compareTo(b.actual));
    final n = items.length;
    int gapIdx = 0;
    double gap = -1;
    for (var i = 0; i < n; i++) {
      final next = i == n - 1 ? items[0].actual + 360 : items[i + 1].actual;
      final g = next - items[i].actual;
      if (g > gap) {
        gap = g;
        gapIdx = i;
      }
    }
    final ordered = <_Glyph>[];
    for (var k = 1; k <= n; k++) {
      ordered.add(items[(gapIdx + k) % n]);
    }
    final base = ordered.first.actual;
    var prev = double.negativeInfinity;
    for (final it in ordered) {
      var l = it.actual;
      while (l < base) {
        l += 360;
      }
      if (l < prev + minSep) l = prev + minSep;
      it.display = l;
      prev = l;
    }
    return ordered;
  }

  TextPainter _tp(
    String text,
    Color color,
    double fontSize, {
    FontWeight weight = FontWeight.w600,
    double letterSpacing = 0,
  }) {
    return TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          color: color,
          fontSize: fontSize,
          fontWeight: weight,
          letterSpacing: letterSpacing,
          height: 1.0,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
  }

  void _glyphAt(
    Canvas canvas,
    Offset center,
    double radius,
    double lon,
    String text,
    Color color,
    double size, {
    double ascLon = 0,
    FontWeight weight = FontWeight.w600,
  }) {
    final tp = _tp(text, color, size, weight: weight);
    final p = _pos(lon, radius, center, ascLon);
    tp.paint(canvas, p - Offset(tp.width / 2, tp.height / 2));
  }

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final r = size.shortestSide / 2 - 2;
    if (r < 70) return;

    final ascLon = data.asc.lon;

    final signOuter = r;
    final signInner = r * 0.86;
    final transitR = r * 0.755;
    final natalR = r * 0.575;
    final houseNumR = r * 0.455;
    final aspectR = r * 0.40;
    final hubR = r * 0.14;

    final circleOuter = Paint()
      ..color = _border.withValues(alpha: 0.85)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;
    final circleInner = Paint()
      ..color = _border.withValues(alpha: 0.55)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    // --- Burç halkası zemin ---
    for (var i = 0; i < 12; i++) {
      final start = i * 30.0;
      final rect = Rect.fromCircle(
        center: center,
        radius: (signOuter + signInner) / 2,
      );
      final paint = Paint()
        ..color = _signColor(i).withValues(alpha: 0.10)
        ..style = PaintingStyle.stroke
        ..strokeWidth = signOuter - signInner;
      canvas.drawArc(
        rect,
        _theta(start, ascLon),
        -30 * math.pi / 180.0,
        false,
        paint,
      );
    }

    canvas.drawCircle(center, signOuter, circleOuter);
    canvas.drawCircle(center, signInner, circleInner);

    // --- Derece çentikleri ---
    final tickPaint = Paint()
      ..color = _muted.withValues(alpha: 0.55)
      ..strokeWidth = 0.7;
    final tickMajor = Paint()
      ..color = _gold.withValues(alpha: 0.75)
      ..strokeWidth = 1.1;
    for (var d = 0; d < 360; d++) {
      final len = d % 30 == 0
          ? (signOuter - signInner) * 0.55
          : d % 5 == 0
          ? (signOuter - signInner) * 0.32
          : (signOuter - signInner) * 0.16;
      final p1 = _pos(d.toDouble(), signInner, center, ascLon);
      final p2 = _pos(d.toDouble(), signInner + len, center, ascLon);
      canvas.drawLine(p1, p2, d % 30 == 0 ? tickMajor : tickPaint);
    }

    // --- Burç sembolleri ---
    final signGlyphSize = (r * 0.085).clamp(12.0, 24.0);
    for (var i = 0; i < 12; i++) {
      _glyphAt(
        canvas,
        center,
        (signOuter + signInner) / 2,
        i * 30.0 + 15,
        chartSignGlyphs[i],
        _signColor(i),
        signGlyphSize,
        ascLon: ascLon,
        weight: FontWeight.w400,
      );
    }

    // --- Ev çizgileri ve numaraları ---
    final cuspPaint = Paint()
      ..color = _gold.withValues(alpha: 0.35)
      ..strokeWidth = 1;
    final houses = [...data.houses]
      ..sort((a, b) => a.number.compareTo(b.number));
    for (var i = 0; i < houses.length; i++) {
      final h = houses[i];
      final p1 = _pos(h.lon, signInner, center, ascLon);
      final p2 = _pos(h.lon, aspectR, center, ascLon);
      canvas.drawLine(p1, p2, cuspPaint);

      final next = houses[(i + 1) % houses.length];
      var delta = next.lon - h.lon;
      while (delta <= 0) {
        delta += 360;
      }
      final mid = h.lon + delta / 2;
      _glyphAt(
        canvas,
        center,
        houseNumR,
        mid,
        h.number.toString(),
        _gold.withValues(alpha: 0.85),
        (r * 0.036).clamp(9.0, 14.0),
        ascLon: ascLon,
        weight: FontWeight.w700,
      );
    }

    // --- Bi-wheel dış ev çizgileri (transit) ---
    if (outerHouses != null && outerHouses!.isNotEmpty) {
      final outerCusp = Paint()
        ..color = _muted.withValues(alpha: 0.30)
        ..strokeWidth = 0.8;
      for (final h in outerHouses!) {
        final p1 = _pos(h.lon, signInner, center, ascLon);
        final p2 = _pos(h.lon, transitR - (r * 0.05), center, ascLon);
        canvas.drawLine(p1, p2, outerCusp);
      }
    }

    // --- Açı çizgileri (natal) ---
    if (showAspectLines) {
      final byName = <String, double>{};
      for (final p in data.planets) {
        byName[p.name] = p.lon;
      }
      for (final a in data.aspects) {
        final l1 = byName[a.p1];
        final l2 = byName[a.p2];
        if (l1 == null || l2 == null) continue;
        if (a.type.toLowerCase() == 'conjunction') continue;
        final color = _aspectColor(a.type);
        final alpha = (0.45 - a.orb * 0.035).clamp(0.12, 0.45);
        final paint = Paint()
          ..color = color.withValues(alpha: alpha)
          ..strokeWidth =
              a.type.toLowerCase() == 'trine' ||
                  a.type.toLowerCase() == 'opposition'
              ? 1.2
              : 0.9;
        canvas.drawLine(
          _pos(l1, aspectR, center, ascLon),
          _pos(l2, aspectR, center, ascLon),
          paint,
        );
      }
    }

    canvas.drawCircle(
      center,
      aspectR,
      Paint()
        ..color = _border.withValues(alpha: 0.5)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 0.8,
    );
    canvas.drawCircle(
      center,
      hubR,
      Paint()
        ..color = _border.withValues(alpha: 0.35)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 0.8,
    );

    // --- ASC / DSC / MC / IC eksenleri ---
    _axis(canvas, center, signInner, aspectR, ascLon, ascLon + 180, ascLon);
    _axis(
      canvas,
      center,
      signInner,
      aspectR,
      data.mc.lon,
      data.mc.lon + 180,
      ascLon,
    );

    // --- Gezegen halkaları ---
    final natalGlyphSize = (r * 0.078).clamp(12.0, 22.0);
    final natal = _layout(data.planets, 8.0);
    for (final g in natal) {
      final color = g.planet.retrograde ? _retro : _ink;
      // gerçek konum işareti
      canvas.drawCircle(
        _pos(g.actual, natalR + natalGlyphSize * 0.9, center, ascLon),
        1.2,
        Paint()..color = color.withValues(alpha: 0.7),
      );
      _glyphAt(
        canvas,
        center,
        natalR,
        g.display,
        chartPlanetGlyphs[g.planet.name] ?? '·',
        color,
        natalGlyphSize,
        ascLon: ascLon,
        weight: FontWeight.w500,
      );
      if (g.planet.retrograde) {
        _glyphAt(
          canvas,
          center,
          natalR - natalGlyphSize * 0.85,
          g.display,
          'R',
          _retro,
          (nativeSmall(natalGlyphSize)),
          ascLon: ascLon,
          weight: FontWeight.w700,
        );
      }
    }

    if (outerPlanets != null && outerPlanets!.isNotEmpty) {
      final transitGlyphSize = (r * 0.062).clamp(10.0, 18.0);
      final trans = _layout(outerPlanets!, 7.0);
      for (final g in trans) {
        final color = lightTheme
            ? const Color(0xFF005C99)
            : const Color(0xFF8FD8FF);
        canvas.drawCircle(
          _pos(g.actual, transitR + transitGlyphSize * 0.9, center, ascLon),
          1.1,
          Paint()..color = color.withValues(alpha: 0.8),
        );
        _glyphAt(
          canvas,
          center,
          transitR,
          g.display,
          chartPlanetGlyphs[g.planet.name] ?? '·',
          color,
          transitGlyphSize,
          ascLon: ascLon,
          weight: FontWeight.w500,
        );
        if (g.planet.retrograde) {
          _glyphAt(
            canvas,
            center,
            transitR - transitGlyphSize * 0.85,
            g.display,
            'R',
            color,
            nativeSmall(transitGlyphSize),
            ascLon: ascLon,
            weight: FontWeight.w700,
          );
        }
      }
    }

    // --- Açı etiketleri ---
    _angleLabel(canvas, center, signInner, data.asc.lon, 'ASC', ascLon);
    _angleLabel(canvas, center, signInner, data.asc.lon + 180, 'DSC', ascLon);
    _angleLabel(canvas, center, signInner, data.mc.lon, 'MC', ascLon);
    _angleLabel(canvas, center, signInner, data.mc.lon + 180, 'IC', ascLon);

    // merkez noktası
    canvas.drawCircle(center, 2, Paint()..color = _gold.withValues(alpha: 0.6));
  }

  double nativeSmall(double base) => (base * 0.62).clamp(6.0, 11.0);

  void _axis(
    Canvas canvas,
    Offset center,
    double outer,
    double inner,
    double lon1,
    double lon2,
    double ascLon,
  ) {
    final paint = Paint()
      ..color = _gold.withValues(alpha: 0.55)
      ..strokeWidth = 1.3;
    canvas.drawLine(
      _pos(lon1, outer, center, ascLon),
      _pos(lon1, inner, center, ascLon),
      paint,
    );
    canvas.drawLine(
      _pos(lon2, outer, center, ascLon),
      _pos(lon2, inner, center, ascLon),
      paint,
    );
  }

  void _angleLabel(
    Canvas canvas,
    Offset center,
    double radius,
    double lon,
    String label,
    double ascLon,
  ) {
    final tp = _tp(label, _gold, 9, weight: FontWeight.w700);
    final p = _pos(lon, radius - 10, center, ascLon);
    final origin = p - Offset(tp.width / 2, tp.height / 2);
    final bg = Rect.fromLTWH(
      origin.dx - 2,
      origin.dy - 1,
      tp.width + 4,
      tp.height + 2,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(bg, const Radius.circular(3)),
      Paint()..color = _bg.withValues(alpha: 0.85),
    );
    tp.paint(canvas, origin);
  }

  @override
  bool shouldRepaint(covariant _WheelPainter old) =>
      old.lightTheme != lightTheme ||
      old.showAspectLines != showAspectLines ||
      old.data != data ||
      old.outerPlanets != outerPlanets ||
      old.outerHouses != outerHouses;
}
