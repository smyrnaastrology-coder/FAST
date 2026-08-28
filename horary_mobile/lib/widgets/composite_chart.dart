import 'package:flutter/material.dart';
import '../config/theme.dart';

class CompositeChart extends StatelessWidget {
  final Map<String, double> arapNoktalari;
  final String? baslik;

  const CompositeChart({super.key, required this.arapNoktalari, this.baslik});

  @override
  Widget build(BuildContext context) {
    if (arapNoktalari.isEmpty) return const SizedBox();

    final items = arapNoktalari.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    final maxVal = items.first.value;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(baslik ?? 'Arap Noktalar\u0131 / \u00d6zel Puanlar',
              style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 16),
            ...items.map((e) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: Row(
                children: [
                  SizedBox(width: 120, child: Text(e.key, style: const TextStyle(fontSize: 11))),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: maxVal > 0 ? e.value / maxVal : 0,
                        minHeight: 14,
                        backgroundColor: FastTheme.border,
                        valueColor: AlwaysStoppedAnimation(
                          e.value >= 0 ? FastTheme.primary : FastTheme.rose,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  SizedBox(width: 40, child: Text(e.value.toStringAsFixed(0),
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                    textAlign: TextAlign.right,
                  )),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }
}
