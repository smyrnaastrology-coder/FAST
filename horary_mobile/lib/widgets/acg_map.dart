import 'package:flutter/material.dart';
import '../config/theme.dart';

class AcgMap extends StatelessWidget {
  final List<Map<String, dynamic>> noktalar;

  const AcgMap({super.key, required this.noktalar});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Astro-Kartografi', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            Text('D\u00fcnya haritas\u0131 \u00fczerinde gezegen \u00e7izgileri',
              style: TextStyle(fontSize: 11, color: FastTheme.textLight)),
            const SizedBox(height: 12),
            AspectRatio(
              aspectRatio: 2,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: CustomPaint(
                  painter: _AcgPainter(noktalar),
                  size: const Size(double.infinity, 200),
                ),
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 6,
              children: noktalar.map((n) => _legendItem(n)).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _legendItem(Map<String, dynamic> n) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 8, height: 8, decoration: BoxDecoration(
          color: _renk(n['tip'] ?? ''), shape: BoxShape.circle,
        )),
        const SizedBox(width: 4),
        Text('${n['gezegen'] ?? ''}: (${_formatDerece(n['enlem'] ?? 0)}, ${_formatDerece(n['boylam'] ?? 0)})',
          style: const TextStyle(fontSize: 10)),
      ],
    );
  }

  String _formatDerece(dynamic val) {
    final d = (val as num).toDouble();
    return '${d.toStringAsFixed(0)}\u00b0';
  }

  Color _renk(String tip) {
    switch (tip) {
      case 'asc': return Colors.red;
      case 'desc': return Colors.blue;
      case 'mc': return Colors.green;
      default: return FastTheme.accent;
    }
  }
}

class _AcgPainter extends CustomPainter {
  final List<Map<String, dynamic>> noktalar;

  _AcgPainter(this.noktalar);

  @override
  void paint(Canvas canvas, Size size) {
    _drawGrid(canvas, size);
    _drawLines(canvas, size);
  }

  void _drawGrid(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.grey.shade300
      ..strokeWidth = 0.5;

    for (int lat = -90; lat <= 90; lat += 30) {
      final y = (90 - lat) / 180 * size.height;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
    for (int lon = -180; lon <= 180; lon += 30) {
      final x = (lon + 180) / 360 * size.width;
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }

    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height),
      Paint()..style = PaintingStyle.stroke..color = Colors.grey.shade400..strokeWidth = 1);
  }

  void _drawLines(Canvas canvas, Size size) {
    for (final n in noktalar) {
      final gezegenTip = n['tip'] ?? '';
      final paint = Paint()
        ..color = _renk(gezegenTip).withValues(alpha: 0.4)
        ..strokeWidth = 1.5;

      final boylam = (n['boylam'] ?? 0).toDouble();
      final x = (boylam + 180) / 360 * size.width;
      final enlem1 = (n['enlem1'] ?? -90).toDouble();
      final enlem2 = (n['enlem2'] ?? 90).toDouble();
      final y1 = (90 - enlem1) / 180 * size.height;
      final y2 = (90 - enlem2) / 180 * size.height;

      canvas.drawLine(Offset(x, y1), Offset(x, y2), paint);

      canvas.drawCircle(Offset(x, (y1 + y2) / 2), 4,
        Paint()..color = _renk(gezegenTip));
    }
  }

  Color _renk(String tip) {
    switch (tip) {
      case 'asc': return Colors.red;
      case 'desc': return Colors.blue;
      case 'mc': return Colors.green;
      default: return FastTheme.accent;
    }
  }

  @override
  bool shouldRepaint(covariant _AcgPainter old) => true;
}
