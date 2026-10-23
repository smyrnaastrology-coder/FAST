import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../config/theme.dart';
import '../models/chart_data.dart';

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
  'north_node': '☊',
  'chiron': '⚷',
};

class ChartWheel extends StatelessWidget {
  final ChartData data;
  final double size;
  final List<PlanetPos>? outerPlanets;
  final List<HouseCusp>? outerHouses;

  const ChartWheel({
    super.key,
    required this.data,
    this.size = 320,
    this.outerPlanets,
    this.outerHouses,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _WheelPainter(
          data: data,
          outerPlanets: outerPlanets,
          outerHouses: outerHouses,
        ),
      ),
    );
  }
}

class _WheelPainter extends CustomPainter {
  final ChartData data;
  final List<PlanetPos>? outerPlanets;
  final List<HouseCusp>? outerHouses;

  _WheelPainter({required this.data, this.outerPlanets, this.outerHouses});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 14;
    final ring1 = radius - 16;
    final ring2 = radius - 36;
    final ring3 = radius - 58;

    final outer = Paint()
      ..color = FastTheme.border.withValues(alpha: 0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    final inner = Paint()
      ..color = FastTheme.border.withValues(alpha: 0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    final housePaint = Paint()
      ..color = FastTheme.accentGold.withValues(alpha: 0.4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    final housePaint2 = Paint()
      ..color = Colors.white.withValues(alpha: 0.25)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    canvas.drawCircle(center, radius, outer);
    canvas.drawCircle(center, ring1, inner);
    canvas.drawCircle(center, ring2, inner);
    if (outerPlanets != null || outerHouses != null) {
      canvas.drawCircle(center, ring3, inner);
    }

    for (int i = 0; i < 12; i++) {
      final ang = (i * 30 - 90) * math.pi / 180.0;
      final p1 = Offset(center.dx + radius * math.cos(ang), center.dy + radius * math.sin(ang));
      final p2 = Offset(center.dx + ring1 * math.cos(ang), center.dy + ring1 * math.sin(ang));
      canvas.drawLine(p1, p2, inner);
    }

    for (final h in data.houses) {
      final ang = (h.lon - 90) * math.pi / 180.0;
      final p1 = Offset(center.dx + ring1 * math.cos(ang), center.dy + ring1 * math.sin(ang));
      final p2 = Offset(center.dx + ring2 * math.cos(ang), center.dy + ring2 * math.sin(ang));
      canvas.drawLine(p1, p2, housePaint);
      _text(canvas, center, ring2 - 10, ang, TextSpan(
        text: h.number.toString(),
        style: TextStyle(color: FastTheme.accentGold.withValues(alpha: 0.8), fontSize: 9),
      ));
    }

    if (outerHouses != null) {
      for (final h in outerHouses!) {
        final ang = (h.lon - 90) * math.pi / 180.0;
        final p1 = Offset(center.dx + ring2 * math.cos(ang), center.dy + ring2 * math.sin(ang));
        final p2 = Offset(center.dx + ring3 * math.cos(ang), center.dy + ring3 * math.sin(ang));
        canvas.drawLine(p1, p2, housePaint2);
      }
    }

    for (final p in data.planets) {
      final ang = (p.lon - 90) * math.pi / 180.0;
      final pt = Offset(center.dx + ring2 * math.cos(ang), center.dy + ring2 * math.sin(ang));
      final tp = TextPainter(
        text: TextSpan(
          text: _planetGlyphs[p.name] ?? p.name.substring(0, 1),
          style: TextStyle(
            color: p.retrograde ? FastTheme.accentGoldLight : FastTheme.text,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, pt - Offset(tp.width / 2, tp.height / 2));
    }

    if (outerPlanets != null) {
      for (final p in outerPlanets!) {
        final ang = (p.lon - 90) * math.pi / 180.0;
        final pt = Offset(center.dx + ring3 * math.cos(ang), center.dy + ring3 * math.sin(ang));
        final tp = TextPainter(
          text: TextSpan(
            text: _planetGlyphs[p.name] ?? p.name.substring(0, 1),
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.9),
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
          textDirection: TextDirection.ltr,
        )..layout();
        tp.paint(canvas, pt - Offset(tp.width / 2, tp.height / 2));
      }
    }

    final ascAng = (data.asc.lon - 90) * math.pi / 180.0;
    final ascP = Offset(center.dx + radius * math.cos(ascAng), center.dy + radius * math.sin(ascAng));
    final ascLine = Paint()
      ..color = FastTheme.accentGold.withValues(alpha: 0.6)
      ..strokeWidth = 1;
    canvas.drawLine(center, ascP, ascLine);
    _text(canvas, center, radius + 4, ascAng, TextSpan(
      text: 'ASC',
      style: TextStyle(color: FastTheme.accentGold, fontSize: 9, fontWeight: FontWeight.w700),
    ));
  }

  void _text(Canvas canvas, Offset center, double r, double ang, TextSpan span) {
    final tp = TextPainter(text: span, textDirection: TextDirection.ltr)..layout();
    final pt = Offset(center.dx + r * math.cos(ang), center.dy + r * math.sin(ang));
    tp.paint(canvas, pt - Offset(tp.width / 2, tp.height / 2));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
