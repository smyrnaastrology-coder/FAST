import 'dart:math';
import 'package:flutter/material.dart';
import '../config/theme.dart';

class SituaChart extends StatelessWidget {
  final List<Map<String, dynamic>> gezegenler;
  final double yukselen;
  final double mc;

  const SituaChart({
    super.key,
    required this.gezegenler,
    this.yukselen = 0,
    this.mc = 0,
  });

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 1,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: CustomPaint(
            painter: _SituaPainter(gezegenler, yukselen, mc),
            child: const Center(child: Text('FAST', style: TextStyle(fontSize: 11, color: FastTheme.textLight))),
          ),
        ),
      ),
    );
  }
}

class _SituaPainter extends CustomPainter {
  final List<Map<String, dynamic>> gezegenler;
  final double yukselen;
  final double mc;

  _SituaPainter(this.gezegenler, this.yukselen, this.mc);

  static const _burcRenkleri = [
    Color(0xFFE57373), Color(0xFF81C784), Color(0xFFFFD54F), Color(0xFF64B5F6),
    Color(0xFFFF8A65), Color(0xFFA1887F), Color(0xFFBA68C8), Color(0xFF4DB6AC),
    Color(0xFFF06292), Color(0xFF7986CB), Color(0xFF4DD0E1), Color(0xFF9575CD),
  ];

  static const _gezegenSembolleri = {
    'G\u00fcne\u015f': '\u2609', 'Ay': '\u263d', 'Merk\u00fcr': '\u263f',
    'Ven\u00fcs': '\u2640', 'Mars': '\u2642', 'J\u00fcpiter': '\u2643',
    'Sat\u00fcrn': '\u2644', 'Uran\u00fcs': '\u2645', 'Nept\u00fcn': '\u2646',
    'Pl\u00fcton': '\u2647', 'Chiron': '\u26b7', 'Lilith': '\u2bd1',
    'Kuzey Ay D\u00fc\u011f\u00fcm\u00fc': '\u260a',
  };

  static const _gezegenRenkleri = {
    'G\u00fcne\u015f': Color(0xFFFFD700), 'Ay': Color(0xFFC0C0C0),
    'Merk\u00fcr': Color(0xFF8A9BB5), 'Ven\u00fcs': Color(0xFFF0A0B0),
    'Mars': Color(0xFFFF4444), 'J\u00fcpiter': Color(0xFFDAA520),
    'Sat\u00fcrn': Color(0xFF8B7355), 'Uran\u00fcs': Color(0xFF40E0D0),
    'Nept\u00fcn': Color(0xFF4169E1), 'Pl\u00fcton': Color(0xFF8B0000),
  };

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) / 2 - 20;
    final innerR = radius * 0.55;

    _drawZodiacRing(canvas, center, radius);
    _drawHouses(canvas, center, radius, innerR);
    _drawDegreeMarks(canvas, center, radius);
    _drawPlanets(canvas, center, innerR * 0.8);
    _drawCenter(canvas, center, innerR * 0.25);
  }

  void _drawZodiacRing(Canvas canvas, Offset center, double radius) {
    final outerR = radius;
    final innerR = radius * 0.88;
    final bandPaint = Paint()..style = PaintingStyle.fill;

    for (int i = 0; i < 12; i++) {
      final startAngle = (i * 30 - 90) * pi / 180;
      final sweep = 30 * pi / 180;
      bandPaint.color = _burcRenkleri[i].withValues(alpha: 0.15);
      canvas.drawArc(Rect.fromCircle(center: center, radius: outerR), startAngle, sweep, false, bandPaint);
      canvas.drawArc(Rect.fromCircle(center: center, radius: innerR), startAngle, sweep, false, bandPaint);

      final midAngle = startAngle + sweep / 2;
      final labelR = (outerR + innerR) / 2;
      final labelPos = Offset(center.dx + labelR * cos(midAngle), center.dy + labelR * sin(midAngle));
      _drawText(canvas, _burcSembol(i), labelPos, 13, FastTheme.text);
    }
  }

  void _drawHouses(Canvas canvas, Offset center, double radius, double innerR) {
    final housePaint = Paint()
      ..color = FastTheme.border.withValues(alpha: 0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.5;

    for (int i = 0; i < 12; i++) {
      final angle = (i * 30 - 90) * pi / 180;
      canvas.drawLine(
        Offset(center.dx + innerR * cos(angle), center.dy + innerR * sin(angle)),
        Offset(center.dx + radius * cos(angle), center.dy + radius * sin(angle)),
        housePaint,
      );

      final numAngle = (angle + 15 * pi / 180);
      final numR = radius * 0.93;
      _drawText(canvas, '${i + 1}', Offset(
        center.dx + numR * cos(numAngle), center.dy + numR * sin(numAngle),
      ), 10, FastTheme.textLight);
    }
  }

  void _drawDegreeMarks(Canvas canvas, Offset center, double radius) {
    final tickPaint = Paint()
      ..color = FastTheme.border.withValues(alpha: 0.3)
      ..strokeWidth = 0.5;

    for (int i = 0; i < 360; i += 5) {
      final angle = (i - 90) * pi / 180;
      final r1 = radius * (i % 30 == 0 ? 0.88 : 0.92);
      final r2 = radius * 0.95;
      canvas.drawLine(
        Offset(center.dx + r1 * cos(angle), center.dy + r1 * sin(angle)),
        Offset(center.dx + r2 * cos(angle), center.dy + r2 * sin(angle)),
        tickPaint,
      );
    }
  }

  void _drawPlanets(Canvas canvas, Offset center, double r) {
    for (final g in gezegenler) {
      final derece = (g['derece'] ?? 0).toDouble();
      final angle = (derece - 90) * pi / 180;
      final pos = Offset(center.dx + r * cos(angle), center.dy + r * sin(angle));
      final ad = g['ad'] ?? '';
      final sembol = _gezegenSembolleri[ad] ?? ad.substring(0, min(2, ad.length));
      final renk = _gezegenRenkleri[ad] ?? FastTheme.primary;

      canvas.drawCircle(pos, 10, Paint()..color = Colors.white..style = PaintingStyle.fill);
      canvas.drawCircle(pos, 10, Paint()..color = renk..style = PaintingStyle.stroke..strokeWidth = 2);

      _drawText(canvas, sembol, Offset(pos.dx, pos.dy + 1), 12, renk);
    }
  }

  void _drawCenter(Canvas canvas, Offset center, double r) {
    canvas.drawCircle(center, r, Paint()..color = FastTheme.bg..style = PaintingStyle.fill);
    canvas.drawCircle(center, r, Paint()..color = FastTheme.border..style = PaintingStyle.stroke..strokeWidth = 1);

    if (yukselen > 0) {
      final ascAngle = (yukselen - 90) * pi / 180;
      final ascPos = Offset(center.dx + r * 0.8 * cos(ascAngle), center.dy + r * 0.8 * sin(ascAngle));
      _drawText(canvas, 'ASC', ascPos, 10, FastTheme.accent);
    }
  }

  void _drawText(Canvas canvas, String text, Offset pos, double size, Color color) {
    final builder = TextPainter(
      text: TextSpan(text: text, style: TextStyle(color: color, fontSize: size)),
      textDirection: TextDirection.ltr,
    )..layout();
    builder.paint(canvas, Offset(pos.dx - builder.width / 2, pos.dy - builder.height / 2));
  }

  String _burcSembol(int i) {
    const semboller = ['\u2648','\u2649','\u264a','\u264b','\u264c','\u264d',
      '\u264e','\u264f','\u2650','\u2651','\u2652','\u2653'];
    return semboller[i];
  }

  @override
  bool shouldRepaint(covariant _SituaPainter old) => true;
}
