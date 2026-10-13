// Sınav: son analizi göster (D/Y/B girişi web'den; mobilde özet + net grafiği).
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../config.dart';
import '../main.dart';

class SinavScreen extends StatefulWidget {
  const SinavScreen({super.key});
  @override
  State<SinavScreen> createState() => _SinavScreenState();
}

class _SinavScreenState extends State<SinavScreen> {
  Map<String, dynamic>? _analiz;
  String _bilgi = '';

  Future<void> _yukle() async {
    final id = Session.ogrenciId;
    if (id == null) {
      setState(() => _bilgi = 'Önce Profil sekmesinden öğrenci oluşturun.');
      return;
    }
    try {
      final j = await api.analiz(id);
      setState(() { _analiz = j; _bilgi = ''; });
    } catch (e) {
      setState(() => _bilgi = 'Sınav sonucu yok veya hata: $e');
    }
  }

  @override
  void initState() {
    super.initState();
    _yukle();
  }

  @override
  Widget build(BuildContext context) {
    final a = _analiz;
    return RefreshIndicator(
      onRefresh: _yukle,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_bilgi.isNotEmpty) Text(_bilgi),
          if (a != null) ...[
            Card(
              child: ListTile(
                title: Text('Genel başarı %${a['genel_basari']} • Net ${a['net'] ?? '-'}'),
                subtitle: Text('${a['sinav_sayisi'] ?? 1} sınav • Kritik ${a['kritik_sayisi']} konu'),
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 220,
              child: BarChart(
                BarChartData(
                  barGroups: [
                    for (int i = 0; i < (a['konular'] as List).length && i < 8; i++)
                      BarChartGroupData(x: i, barRods: [
                        BarChartRodData(
                          toY: ((a['konular'][i]['basari'] ?? 0) as num).toDouble(),
                          color: Colors.orange,
                        ),
                      ]),
                  ],
                  titlesData: const FlTitlesData(show: false),
                  borderData: FlBorderData(show: false),
                  gridData: const FlGridData(show: false),
                ),
              ),
            ),
            for (final k in (a['konular'] as List).take(10))
              ListTile(
                dense: true,
                title: Text('${k['baslik'] ?? k['kod']}'),
                trailing: Text('%${k['basari']} (${k['durum']})'),
              ),
          ],
        ],
      ),
    );
  }
}
