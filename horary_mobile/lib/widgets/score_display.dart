import 'dart:math';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';

class ScoreDisplay extends StatelessWidget {
  final double skor;
  const ScoreDisplay({super.key, required this.skor});

  @override
  Widget build(BuildContext context) {
    final normalized = (skor / 100).clamp(0.0, 1.0);
    final color = skor >= 70 ? FastTheme.rose
        : skor >= 50 ? FastTheme.accent
        : skor >= 30 ? FastTheme.secondary
        : FastTheme.textLight;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Text(AppLocalizations.of(context).scoreBondLabel, style: GoogleFonts.cormorantGaramond(
              fontSize: 18, fontWeight: FontWeight.w600, color: FastTheme.textLight,
            )),
            const SizedBox(height: 16),
            SizedBox(
              width: 180, height: 180,
              child: CustomPaint(
                painter: _ArcPainter(normalized, color),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(skor.toStringAsFixed(0), style: GoogleFonts.cormorantGaramond(
                        fontSize: 48, fontWeight: FontWeight.w700, color: color,
                      )),
                      Text('/ 100', style: TextStyle(fontSize: 14, color: FastTheme.textLight)),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
            Text(_seviye(skor), style: TextStyle(
              fontSize: 16, fontWeight: FontWeight.w600, color: color,
            )),
          ],
        ),
      ),
    );
  }

  String _seviye(double s) {
    if (s >= 80) return '\u2705 Y\u0131ld\u0131z Ba\u011f \u00c7ok G\u00fc\u00e7l\u00fc';
    if (s >= 60) return '\u2705 Y\u0131ld\u0131z Ba\u011f Mevcut';
    if (s >= 40) return '\u26a0ef8f8 Orta D\u00fczey Ba\u011f';
    if (s >= 20) return '\u26a0ef8f8 Zay\u0131f Ba\u011f';
    return '\u274c Belirgin Ba\u011f Yok';
  }
}

class _ArcPainter extends CustomPainter {
  final double value;
  final Color color;
  _ArcPainter(this.value, this.color);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) / 2 - 16;

    final bgPaint = Paint()
      ..color = FastTheme.border.withValues(alpha: 0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 16
      ..strokeCap = StrokeCap.round;

    final fgPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 16
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(Rect.fromCircle(center: center, radius: radius), -pi * 0.75, pi * 1.5, false, bgPaint);
    canvas.drawArc(Rect.fromCircle(center: center, radius: radius), -pi * 0.75, pi * 1.5 * value, false, fgPaint);
  }

  @override
  bool shouldRepaint(covariant _ArcPainter old) => old.value != value;
}
