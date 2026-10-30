import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/chart_data.dart';
import '../models/chart_labels.dart';
import '../models/chart_frame.dart';
import '../screens/chart_explorer_screen.dart';
import '../l10n/app_localizations.dart';

/// AstroGold tarzı çok katmanlı natal / bi-wheel çarkı.
///
/// Yükselen (ASC) her zaman sol-orta noktaya (doğu ufku) kilitlenir; burçlar
/// saat yönünün tersine ilerler. Bi-wheel modunda natal ve transit gezegenler
/// AYRI halkalarda çizilir; iki halka arasında çift çizgi (sınır) bulunur.
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
    // Dar ekranlarda taşmayı önle.
    final maxWidth = MediaQuery.of(context).size.width - 24;
    final extent = size > maxWidth && maxWidth > 100 ? maxWidth : size;
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
    if (!showControls) return drawing(extent);
    return Stack(
      alignment: Alignment.topRight,
      children: [
        InteractiveViewer(minScale: 1, maxScale: 5, child: drawing(extent)),
        if (showControls)
          IconButton(
            tooltip: AppLocalizations.of(context).chartWheelFullscreenTooltip,
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
  Color get _gold =>
      lightTheme ? const Color(0xFF795400) : const Color(0xFFE6C57A);
  Color get _border =>
      lightTheme ? const Color(0xFF545E70) : const Color(0xFF8290A7);
  Color get _muted =>
      lightTheme ? const Color(0xFF374151) : const Color(0xFFBBC4D4);
  Color get _bg => lightTheme ? Colors.white : const Color(0xFF0D1017);
  Color get _transit =>
      lightTheme ? const Color(0xFF005C99) : const Color(0xFF8FD8FF);

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

  String _degMinStr(double deg) {
    final total = (deg * 60).round();
    final d = total ~/ 60;
    final m = total % 60;
    return '$d°${m.toString().padLeft(2, '0')}′';
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
  ///
  /// [minSep] derece cinsinden minimum açısal ayrımdır; piksel bazlı
  /// hesaplandığı için sembol ve derece yazısı hiçbir zaman üst üste binmez.
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
          shadows: [
            Shadow(
              color: _bg.withValues(alpha: 0.9),
              blurRadius: 2,
              offset: const Offset(0.5, 0.5),
            ),
          ],
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

  /// Verilen halka yarıçapında, [needPx] piksel genişliğinde bir etiketin
  /// çakışmaması için gereken minimum açısal ayrım (derece).
  double _minSepDeg(double radiusPx, double needPx) {
    if (radiusPx <= 0) return 30;
    return (needPx / radiusPx) * 180 / math.pi;
  }

  /// Derece etiketlerinin en geniş olanının piksel genişliği.
  double _maxLabelWidth(List<PlanetPos> planets, double fontSize) {
    var w = 0.0;
    for (final p in planets) {
      final tp = _tp(
        _degMinStr(p.degree) + (p.retrograde ? ' R' : ''),
        _muted,
        fontSize,
      );
      if (tp.width > w) w = tp.width;
    }
    return w;
  }

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final r = size.shortestSide / 2 - 2;
    if (r < 70) return;

    final ascLon = data.asc.lon;

    // --- Halka yarıçapları (tek yerden yönetilir) ---
    // Merkez boşluğu küçük, gezegen bantları geniş: çarkın ağırlığı
    // gezegen yerleşimlerinde olsun.
    final signOuter = r;
    final signInner = r * 0.875;

    final transitOuter = r * 0.868;
    final transitInner = r * 0.742;
    final transitGlyphR = (transitOuter + transitInner) / 2 + r * 0.010;

    final separatorA = r * 0.734;
    final separatorB = r * 0.725;

    final natalOuter = r * 0.717;
    final natalInner = r * 0.545;
    final natalGlyphR = (natalOuter + natalInner) / 2 + r * 0.012;

    final aspectR = r * 0.405;
    final houseNumR = r * 0.480;
    final hubR = r * 0.072;

    final hasOuter = outerPlanets != null && outerPlanets!.isNotEmpty;
    final bool light = lightTheme;

    final circleOuter = Paint()
      ..color = _border.withValues(alpha: 0.85)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;
    final circleInner = Paint()
      ..color = _border.withValues(alpha: 0.55)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    // --- Halka zeminleri ---
    canvas.drawCircle(
      center,
      (natalOuter + natalInner) / 2,
      Paint()
        ..color = (light ? const Color(0xFFF3F5FA) : const Color(0xFF121721))
        ..style = PaintingStyle.stroke
        ..strokeWidth = natalOuter - natalInner,
    );
    if (hasOuter) {
      canvas.drawCircle(
        center,
        (transitOuter + transitInner) / 2,
        Paint()
          ..color = (light
                  ? const Color(0xFFEFF6FE)
                  : const Color(0xFF152238))
              .withValues(alpha: light ? 1 : 0.75)
          ..style = PaintingStyle.stroke
          ..strokeWidth = transitOuter - transitInner,
      );
    }

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

    // Burç sınır çizgileri
    final signDivider = Paint()
      ..color = _border.withValues(alpha: 0.35)
      ..strokeWidth = 0.8;
    for (var i = 0; i < 12; i++) {
      canvas.drawLine(
        _pos(i * 30.0, signInner, center, ascLon),
        _pos(i * 30.0, signOuter, center, ascLon),
        signDivider,
      );
    }

    // --- Derece çentikleri ---
    final tickPaint = Paint()
      ..color = _muted.withValues(alpha: 0.4)
      ..strokeWidth = 0.7;
    final tickMajor = Paint()
      ..color = _gold.withValues(alpha: 0.7)
      ..strokeWidth = 1.1;
    for (var d = 0; d < 360; d++) {
      final len = d % 30 == 0
          ? (signOuter - signInner) * 0.40
          : d % 5 == 0
          ? (signOuter - signInner) * 0.20
          : (signOuter - signInner) * 0.10;
      final p1 = _pos(d.toDouble(), signInner, center, ascLon);
      final p2 = _pos(d.toDouble(), signInner + len, center, ascLon);
      canvas.drawLine(p1, p2, d % 30 == 0 ? tickMajor : tickPaint);
    }

    // --- Burç sembolleri ---
    final signGlyphSize = (r * 0.086).clamp(13.0, 25.0);
    final signGlyphR = signInner + (signOuter - signInner) * 0.58;
    for (var i = 0; i < 12; i++) {
      _glyphAt(
        canvas,
        center,
        signGlyphR,
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
      ..color = _gold.withValues(alpha: 0.32)
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
        _gold.withValues(alpha: 0.9),
        (r * 0.040).clamp(10.0, 16.0),
        ascLon: ascLon,
        weight: FontWeight.w700,
      );
    }

    // --- Ev giriş dereceleri: EN DIŞTA (burç halkasının iç kenarı) ---
    // AstroGold'da olduğu gibi her evin giriş derecesi çarkın dışına yakın,
    // burç sembollerinin hemen altında gösterilir.
    final cuspDegSize = (r * 0.024).clamp(6.0, 9.0);
    final cuspTier0 = signInner + (signOuter - signInner) * 0.10;
    final cuspTier1 = signInner + (signOuter - signInner) * 0.26;
    final cuspSorted = [...houses]..sort((a, b) => a.lon.compareTo(b.lon));
    var prevCuspLon = double.negativeInfinity;
    var cuspTier = 0;
    for (final h in cuspSorted) {
      if (h.lon - prevCuspLon < 9.0) {
        cuspTier = 1 - cuspTier;
      } else {
        cuspTier = 0;
      }
      prevCuspLon = h.lon;
      _glyphAt(
        canvas,
        center,
        cuspTier == 0 ? cuspTier0 : cuspTier1,
        h.lon,
        _degMinStr(h.degree),
        _gold.withValues(alpha: 0.92),
        cuspDegSize,
        ascLon: ascLon,
        weight: FontWeight.w600,
      );
    }

    // --- Bi-wheel dış ev çizgileri (transit) ---
    if (hasOuter && outerHouses != null && outerHouses!.isNotEmpty) {
      final outerCusp = Paint()
        ..color = _transit.withValues(alpha: 0.22)
        ..strokeWidth = 0.8;
      for (final h in outerHouses!) {
        canvas.drawLine(
          _pos(h.lon, signInner, center, ascLon),
          _pos(h.lon, transitOuter - (r * 0.012), center, ascLon),
          outerCusp,
        );
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
        ..color = _border.withValues(alpha: 0.3)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 0.8,
    );

    // --- ASC / DSC / MC / IC eksenleri ---
    _axis(canvas, center, signInner, aspectR, ascLon + 180, ascLon);
    _axis(canvas, center, signInner, aspectR, data.mc.lon, ascLon);

    // --- Gezegen halkaları ---
    final natalGlyphSize = (r * 0.090).clamp(13.0, 24.0);
    final natalDegSize = (natalGlyphSize * 0.46).clamp(6.5, 10.0);
    final natal = _layout(
      data.planets,
      _minSepDeg(
            natalGlyphR,
            math.max(
              natalGlyphSize,
              _maxLabelWidth(data.planets, natalDegSize),
            ),
          ) *
          1.08,
    );
    for (final g in natal) {
      final color = _signColor(g.planet.sign);
      _drawLeader(
        canvas,
        center,
        ascLon,
        g,
        natalGlyphR,
        natalGlyphSize,
        color.withValues(alpha: 0.45),
      );
      _glyphAt(
        canvas,
        center,
        natalGlyphR,
        g.display,
        chartPlanetGlyphs[g.planet.name] ?? '·',
        color,
        natalGlyphSize,
        ascLon: ascLon,
        weight: FontWeight.w600,
      );
      final deg = _degMinStr(g.planet.degree) + (g.planet.retrograde ? ' R' : '');
      _glyphAt(
        canvas,
        center,
        natalGlyphR - natalGlyphSize * 0.86,
        g.display,
        deg,
        g.planet.retrograde ? _retroColor : color.withValues(alpha: 0.88),
        natalDegSize,
        ascLon: ascLon,
        weight: FontWeight.w600,
      );
    }

    if (hasOuter) {
      final transitGlyphSize = (r * 0.078).clamp(11.0, 20.0);
      final transitDegSize = (transitGlyphSize * 0.46).clamp(6.0, 9.0);
      final trans = _layout(
        outerPlanets!,
        _minSepDeg(
              transitGlyphR,
              math.max(
                transitGlyphSize,
                _maxLabelWidth(outerPlanets!, transitDegSize),
              ),
            ) *
            1.08,
      );
      for (final g in trans) {
        final color = _transit;
        _drawLeader(
          canvas,
          center,
          ascLon,
          g,
          transitGlyphR,
          transitGlyphSize,
          color.withValues(alpha: 0.35),
        );
        _glyphAt(
          canvas,
          center,
          transitGlyphR,
          g.display,
          chartPlanetGlyphs[g.planet.name] ?? '·',
          color,
          transitGlyphSize,
          ascLon: ascLon,
          weight: FontWeight.w600,
        );
        final deg =
            _degMinStr(g.planet.degree) + (g.planet.retrograde ? ' R' : '');
        _glyphAt(
          canvas,
          center,
          transitGlyphR - transitGlyphSize * 0.86,
          g.display,
          deg,
          color.withValues(alpha: 0.85),
          transitDegSize,
          ascLon: ascLon,
          weight: FontWeight.w600,
        );
      }
    }

    // --- İki halka arasındaki sınır: ÇİFT DAİRE ---
    if (hasOuter) {
      canvas.drawCircle(
        center,
        separatorA,
        Paint()
          ..color = _gold.withValues(alpha: 0.55)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.1,
      );
      canvas.drawCircle(
        center,
        separatorB,
        Paint()
          ..color = _gold.withValues(alpha: 0.32)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 0.9,
      );
    }

    // --- Açı etiketleri ---
    _angleLabel(canvas, center, signInner, data.asc.lon, 'ASC', ascLon);
    _angleLabel(canvas, center, signInner, data.asc.lon + 180, 'DSC', ascLon);
    _angleLabel(canvas, center, signInner, data.mc.lon, 'MC', ascLon);
    _angleLabel(canvas, center, signInner, data.mc.lon + 180, 'IC', ascLon);

    // merkez noktası
    canvas.drawCircle(center, 2, Paint()..color = _gold.withValues(alpha: 0.6));
  }

  Color get _retroColor =>
      lightTheme ? const Color(0xFF9D261A) : const Color(0xFFFFBF80);

  /// Gerçek konumdan kaydırılmış sembole ince kılavuz çizgisi.
  void _drawLeader(
    Canvas canvas,
    Offset center,
    double ascLon,
    _Glyph g,
    double radius,
    double glyphSize,
    Color color,
  ) {
    var drift = g.display - g.actual;
    if (drift.abs() < 1.0) return;
    final lineR = radius - glyphSize * 0.92;
    final paint = Paint()
      ..color = color
      ..strokeWidth = 0.7
      ..style = PaintingStyle.stroke;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: lineR),
      _theta(g.actual, ascLon),
      -drift * math.pi / 180.0,
      false,
      paint,
    );
    canvas.drawCircle(
      _pos(g.actual, radius, center, ascLon),
      1.3,
      Paint()..color = color,
    );
  }

  void _axis(
    Canvas canvas,
    Offset center,
    double outer,
    double inner,
    double lon,
    double ascLon,
  ) {
    final paint = Paint()
      ..color = _gold.withValues(alpha: 0.6)
      ..strokeWidth = 1.3;
    canvas.drawLine(
      _pos(lon, outer, center, ascLon),
      _pos(lon, inner, center, ascLon),
      paint,
    );
    canvas.drawLine(
      _pos(lon + 180, outer, center, ascLon),
      _pos(lon + 180, inner, center, ascLon),
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
