import 'dart:math';
import 'package:flutter/material.dart';

class FrekansChart extends StatelessWidget {
  final Map<String, double> frekanslar;

  const FrekansChart({super.key, required this.frekanslar});

  static const _renkPaleti = [
    Color(0xFFE57373), Color(0xFFF06292), Color(0xFFBA68C8),
    Color(0xFF64B5F6), Color(0xFF4DB6AC), Color(0xFF81C784),
    Color(0xFFFFD54F), Color(0xFFFF8A65), Color(0xFFA1887F),
    Color(0xFF90A4AE),
  ];

  @override
  Widget build(BuildContext context) {
    final items = frekanslar.entries.toList();
    if (items.isEmpty) return const SizedBox();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Frekans Da\u011f\u0131l\u0131m\u0131',
              style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 16),
            SizedBox(
              height: 250,
              child: CustomPaint(
                size: const Size(double.infinity, 250),
                painter: _FrekansPainter(items),
              ),
            ),
            const SizedBox(height: 8),
            ...items.asMap().entries.map((e) => _legendItem(e.key, e.value.key, e.value.value)),
          ],
        ),
      ),
    );
  }

  Widget _legendItem(int idx, String label, double val) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 1),
      child: Row(
        children: [
          Container(width: 10, height: 10, decoration: BoxDecoration(
            color: _renkPaleti[idx % _renkPaleti.length], shape: BoxShape.circle,
          )),
          const SizedBox(width: 6),
          Expanded(child: Text(label, style: const TextStyle(fontSize: 11))),
          Text(val.toStringAsFixed(0), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}

class _FrekansPainter extends CustomPainter {
  final List<MapEntry<String, double>> items;

  _FrekansPainter(this.items);

  @override
  void paint(Canvas canvas, Size size) {
    if (items.isEmpty) return;
    final maxVal = items.map((e) => e.value).reduce(max);
    final barW = size.width / (items.length * 1.5);
    final gap = barW * 0.4;

    for (int i = 0; i < items.length; i++) {
      final h = (items[i].value / maxVal) * (size.height - 40);
      final x = i * (barW + gap) + gap;
      final y = size.height - 30 - h;

      final paint = Paint()
        ..shader = LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [
            FrekansChart._renkPaleti[i % FrekansChart._renkPaleti.length].withValues(alpha: 0.6),
            FrekansChart._renkPaleti[i % FrekansChart._renkPaleti.length],
          ],
        ).createShader(Rect.fromLTWH(x, y, barW, h));

      canvas.drawRRect(RRect.fromRectAndRadius(
        Rect.fromLTWH(x, y, barW, h), const Radius.circular(4),
      ), paint);
    }
  }

  @override
  bool shouldRepaint(covariant _FrekansPainter old) => true;
}
