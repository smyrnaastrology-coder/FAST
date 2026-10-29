import 'package:flutter/material.dart';

/// Holavon "beğeni" ikonu: Venüs sembolü (♀) çizilerek üretilir.
///
/// Emoji/unicode glif yerine vektörel çizim kullanıldığı için her cihazda
/// aynı kalınlıkta, aynı oranda ve estetik görünür.
class VenusLikeIcon extends StatelessWidget {
  final double size;
  final bool liked;
  final Color color;

  const VenusLikeIcon({
    super.key,
    this.size = 22,
    this.liked = false,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _VenusPainter(
          color: color,
          liked: liked,
          strokeWidth: (size * 0.085).clamp(1.4, 3.2),
        ),
      ),
    );
  }
}

class _VenusPainter extends CustomPainter {
  final Color color;
  final bool liked;
  final double strokeWidth;

  _VenusPainter({
    required this.color,
    required this.liked,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final s = size.shortestSide;
    final circleCenter = Offset(s * 0.5, s * 0.35);
    final circleRadius = s * 0.215;

    final stroke = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    if (liked) {
      // Beğenilmiş: hafif dolgu + halka (daha dolgun ve "aktif" görünür).
      canvas.drawCircle(
        circleCenter,
        circleRadius,
        Paint()..color = color.withValues(alpha: 0.22),
      );
    }

    canvas.drawCircle(circleCenter, circleRadius, stroke);

    // Gövde
    canvas.drawLine(
      Offset(s * 0.5, circleCenter.dy + circleRadius),
      Offset(s * 0.5, s * 0.93),
      stroke,
    );

    // Yatay kol
    canvas.drawLine(
      Offset(s * 0.315, s * 0.775),
      Offset(s * 0.685, s * 0.775),
      stroke,
    );
  }

  @override
  bool shouldRepaint(covariant _VenusPainter old) =>
      old.color != color ||
      old.liked != liked ||
      old.strokeWidth != strokeWidth;
}
