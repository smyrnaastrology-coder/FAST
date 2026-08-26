import 'package:flutter/material.dart';
import '../config/theme.dart';

class AciGridi extends StatelessWidget {
  final List<Map<String, dynamic>> acilar;

  const AciGridi({super.key, required this.acilar});

  @override
  Widget build(BuildContext context) {
    if (acilar.isEmpty) {
      return const Card(child: Padding(
        padding: EdgeInsets.all(16),
        child: Text('A\u00e7\u0131 bilgisi bulunamad\u0131'),
      ));
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('A\u00e7\u0131 Gridi', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: DataTable(
                columnSpacing: 8,
                dataRowMinHeight: 28,
                dataRowMaxHeight: 32,
                headingRowHeight: 32,
                columns: const [
                  DataColumn(label: Text('Gezegen', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('A\u00e7\u0131', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Orb', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold))),
                ],
                rows: acilar.map((a) {
                  final tur = a['aci_turu'] ?? a['aspect'] ?? '';
                  return DataRow(cells: [
                    DataCell(Text('${a['gezegen1'] ?? ''} - ${a['gezegen2'] ?? ''}', style: const TextStyle(fontSize: 10))),
                    DataCell(Row(
                      children: [
                        Container(
                          width: 20, height: 20,
                          decoration: BoxDecoration(
                            color: _aciRenk(tur), shape: BoxShape.circle,
                          ),
                          child: Center(child: Text(_aciSembol(tur), style: const TextStyle(fontSize: 10, color: Colors.white))),
                        ),
                        const SizedBox(width: 4),
                        Expanded(child: Text(tur, style: const TextStyle(fontSize: 10))),
                      ],
                    )),
                    DataCell(Text('${(a['fark'] ?? a['orb'] ?? 0).toStringAsFixed(1)}\u00b0', style: const TextStyle(fontSize: 10))),
                  ]);
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _aciRenk(String tur) {
    switch (tur) {
      case 'Kavu\u015fum': return const Color(0xFFE53935);
      case 'Z\u0131t A\u00e7\u0131': return const Color(0xFF1E88E5);
      case '\u00dc\u00e7gen': return const Color(0xFF43A047);
      case 'Altm\u0131\u015fl\u0131k': return const Color(0xFFFB8C00);
      case 'Kare': return const Color(0xFFD81B60);
      default: return FastTheme.textLight;
    }
  }

  String _aciSembol(String tur) {
    switch (tur) {
      case 'Kavu\u015fum': return '\u260c';
      case 'Z\u0131t A\u00e7\u0131': return '\u260d';
      case '\u00dc\u00e7gen': return '\u25b3';
      case 'Altm\u0131\u015fl\u0131k': return '\u2733';
      case 'Kare': return '\u25a1';
      default: return '?';
    }
  }
}
