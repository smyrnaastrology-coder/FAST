import 'dart:math' as math;
import 'package:flutter/material.dart';

/// Renkli Google "G" logosu (CustomPaint — harici asset gerektirmez).
class GoogleLogo extends StatelessWidget {
  final double size;
  const GoogleLogo({super.key, this.size = 20});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _GooglePainter()),
    );
  }
}

class _GooglePainter extends CustomPainter {
  static const _blue = Color(0xFF4285F4);
  static const _green = Color(0xFF34A853);
  static const _yellow = Color(0xFFFBBC05);
  static const _red = Color(0xFFEA4335);

  @override
  void paint(Canvas canvas, Size size) {
    final s = size.width;
    final w = s * 0.17;
    final r = s / 2 - w / 2;
    final c = Offset(s / 2, s / 2);
    final rect = Rect.fromCircle(center: c, radius: r);

    Paint arc(Color col) => Paint()
      ..color = col
      ..style = PaintingStyle.stroke
      ..strokeWidth = w
      ..strokeCap = StrokeCap.butt;

    const d = math.pi / 180;
    // Saat yönünde: kırmızı (sol-üst) → mavi (sağ) → yeşil (alt) → sarı (sol-alt)
    canvas.drawArc(rect, 189 * d, 100 * d, false, arc(_red));
    canvas.drawArc(rect, 289 * d, 120 * d, false, arc(_blue));
    canvas.drawArc(rect, 49 * d, 105 * d, false, arc(_green));
    canvas.drawArc(rect, 154 * d, 35 * d, false, arc(_yellow));
    // Mavi yatay bar: merkezden sağ kenara
    canvas.drawRect(
      Rect.fromLTRB(c.dx, c.dy - w / 2, c.dx + r + w / 2, c.dy + w / 2),
      Paint()..color = _blue,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Instagram logosu: degrade zemin + beyaz kamera (asset gerektirmez).
class InstagramLogo extends StatelessWidget {
  final double size;
  const InstagramLogo({super.key, this.size = 20});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _InstagramPainter()),
    );
  }
}

class _InstagramPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final s = size.width;
    // Degrade zemin
    final bg = RRect.fromRectAndRadius(
      Offset.zero & Size(s, s),
      Radius.circular(s * 0.25),
    );
    canvas.drawRRect(
      bg,
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.bottomLeft,
          end: Alignment.topRight,
          colors: [
            Color(0xFFFEDA75),
            Color(0xFFFA7E1E),
            Color(0xFFD62976),
            Color(0xFF962FBF),
            Color(0xFF4F5BD5),
          ],
        ).createShader(Offset.zero & Size(s, s)),
    );
    // Beyaz kamera
    final white = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = s * 0.075;
    final cam = RRect.fromRectAndRadius(
      Rect.fromLTWH(s * 0.26, s * 0.26, s * 0.48, s * 0.48),
      Radius.circular(s * 0.13),
    );
    canvas.drawRRect(cam, white);
    canvas.drawCircle(Offset(s / 2, s / 2), s * 0.11, white);
    canvas.drawCircle(
      Offset(s * 0.63, s * 0.37),
      s * 0.045,
      Paint()..color = Colors.white,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
