import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Holavon Pro rozeti: altın mühür (rozet) biçiminde onay tik'i.
///
/// [size] rozetin kenar uzunluğu (dp). [glow] arka planda yumuşak altın
/// ışıma ekler (koyu zeminlerde daha iyi görünür). [tooltip] verilirse uzun
/// basınca gösterilir ve erişilebilirlik etiketi olarak da kullanılır.
class ProBadge extends StatelessWidget {
  final double size;
  final bool glow;
  final String? tooltip;

  const ProBadge({super.key, this.size = 20, this.glow = true, this.tooltip});

  @override
  Widget build(BuildContext context) {
    final mark = Semantics(
      label: tooltip ?? 'Holavon Pro',
      container: true,
      child: SizedBox(
        width: size,
        height: size,
        child: CustomPaint(
          painter: _SealPainter(glow: glow),
          isComplex: false,
        ),
      ),
    );
    if (tooltip == null) return mark;
    return Tooltip(message: tooltip!, child: mark);
  }
}

const _goldTop = Color(0xFFFFE7A6);
const _goldMid = Color(0xFFF2C55C);
const _goldLow = Color(0xFFC8952F);
const _goldEdge = Color(0xFF7A5712);
const _checkInk = Color(0xFFFFFDF5);

class _SealPainter extends CustomPainter {
  final bool glow;
  const _SealPainter({required this.glow});

  /// 14 yapraklı mühür: dış/iç yarıçap dönüşümlü köşeler.
  /// Küçük boyutlarda yaprak sayısı azaltılır (bulanıklaşmasın).
  static Path _seal(Offset c, double outer, double inner, int points) {
    final path = Path();
    for (var i = 0; i < points * 2; i++) {
      final angle = -math.pi / 2 + i * math.pi / points;
      final r = i.isEven ? outer : inner;
      final p = Offset(c.dx + math.cos(angle) * r, c.dy + math.sin(angle) * r);
      if (i == 0) {
        path.moveTo(p.dx, p.dy);
      } else {
        path.lineTo(p.dx, p.dy);
      }
    }
    return path..close();
  }

  @override
  void paint(Canvas canvas, Size size) {
    final s = size.shortestSide;
    if (s <= 0) return;
    final c = Offset(size.width / 2, size.height / 2);
    final rim = s * 0.07;
    final outer = s / 2 - rim;
    final points = s < 26 ? 10 : 14;
    final seal = _seal(c, outer, outer * 0.80, points);

    if (glow) {
      canvas.drawCircle(
        c,
        outer * 0.98,
        Paint()
          ..color = _goldMid.withValues(alpha: 0.28)
          ..maskFilter = MaskFilter.blur(BlurStyle.normal, s * 0.17),
      );
    }

    canvas.save();
    canvas.translate(0, s * 0.035);
    canvas.drawPath(
      seal,
      Paint()
        ..color = Colors.black.withValues(alpha: 0.35)
        ..maskFilter = MaskFilter.blur(BlurStyle.normal, s * 0.07),
    );
    canvas.restore();

    final shader = const LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [_goldTop, _goldMid, _goldLow],
      stops: [0.0, 0.52, 1.0],
    ).createShader(Rect.fromCircle(center: c, radius: outer));

    final body = Paint()..shader = shader;
    canvas.drawPath(seal, body);
    canvas.drawPath(
      seal,
      Paint()
        ..shader = shader
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.10
        ..strokeJoin = StrokeJoin.round,
    );

    canvas.drawPath(
      seal,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.035
        ..strokeJoin = StrokeJoin.round
        ..color = _goldEdge.withValues(alpha: 0.5),
    );

    if (s >= 26) {
      canvas.drawCircle(
        c,
        outer * 0.775,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = s * 0.03
          ..color = Colors.white.withValues(alpha: 0.30),
      );
    }

    final check = Path()
      ..moveTo(c.dx - outer * 0.40, c.dy + outer * 0.03)
      ..lineTo(c.dx - outer * 0.11, c.dy + outer * 0.32)
      ..lineTo(c.dx + outer * 0.41, c.dy - outer * 0.30);

    canvas.drawPath(
      check,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.19
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round
        ..color = _goldEdge.withValues(alpha: 0.45),
    );
    canvas.drawPath(
      check,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = s * 0.14
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round
        ..color = _checkInk,
    );
  }

  @override
  bool shouldRepaint(_SealPainter oldDelegate) => oldDelegate.glow != glow;
}
