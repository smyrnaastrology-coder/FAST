import 'dart:math' as math;
import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';

/// Vector emblem: zodiac rim, horizon and aspect triangle. Sharp at every size.
class ChartMark extends StatelessWidget {
  final double size;
  const ChartMark({super.key, this.size = 52});
  @override
  Widget build(BuildContext context) => Semantics(
    label: AppLocalizations.of(context).chartMarkSemantics,
    image: true,
    child: SizedBox.square(
      dimension: size,
      child: CustomPaint(painter: _ChartMarkPainter()),
    ),
  );
}

class _ChartMarkPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final c = size.center(Offset.zero);
    final r = size.shortestSide * .45;
    canvas.drawCircle(
      c,
      size.shortestSide / 2,
      Paint()..color = const Color(0xFF111B30),
    );
    final gold = Paint()
      ..color = const Color(0xFFE9CA80)
      ..style = PaintingStyle.stroke
      ..strokeWidth = size.width * .025;
    canvas.drawCircle(c, r, gold);
    canvas.drawCircle(c, r * .76, gold);
    Offset point(double angle, double radius) =>
        c + Offset(math.cos(angle), math.sin(angle)) * radius;
    for (var i = 0; i < 12; i++) {
      final angle = i * math.pi / 6;
      canvas.drawLine(point(angle, r * .78), point(angle, r), gold);
    }
    final path = Path()
      ..moveTo(point(-math.pi / 2, r * .6).dx, point(-math.pi / 2, r * .6).dy);
    for (final angle in [math.pi / 6, math.pi * 5 / 6]) {
      final p = point(angle, r * .6);
      path.lineTo(p.dx, p.dy);
    }
    path.close();
    canvas.drawPath(path, gold);
    canvas.drawLine(point(0, r * .7), point(math.pi, r * .7), gold);
    canvas.drawCircle(c, r * .1, Paint()..color = const Color(0xFFE9CA80));
  }

  @override
  bool shouldRepaint(covariant _ChartMarkPainter oldDelegate) => false;
}
