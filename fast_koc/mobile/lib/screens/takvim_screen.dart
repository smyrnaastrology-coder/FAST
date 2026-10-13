// Takvim: TG listesi + erken uyarı rozeti + yayıncı linki.
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config.dart';
import '../main.dart';

class TakvimScreen extends StatefulWidget {
  const TakvimScreen({super.key});
  @override
  State<TakvimScreen> createState() => _TakvimScreenState();
}

class _TakvimScreenState extends State<TakvimScreen> {
  List<dynamic> _liste = [];
  String _bilgi = '';

  @override
  void initState() {
    super.initState();
    _yukle();
  }

  Future<void> _yukle() async {
    try {
      final l = await api.takvim(Session.segment);
      setState(() { _liste = l; _bilgi = ''; });
    } catch (e) {
      setState(() => _bilgi = 'Hata: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _yukle,
      child: _liste.isEmpty
          ? ListView(children: [Padding(padding: const EdgeInsets.all(16), child: Text(_bilgi))])
          : ListView.builder(
              itemCount: _liste.length,
              itemBuilder: (c, i) {
                final d = _liste[i];
                final kalan = (d['kalan_gun'] ?? 999) as int;
                final dogrulama = (d['dogrulama_durumu'] ?? '') as String;
                final rozet = dogrulama.startsWith('dogrulandi')
                    ? '✅ MEB resmi'
                    : dogrulama.startsWith('duyuru')
                        ? '📌 Duyuru (teyit edin)'
                        : '⚠️ Taslak';
                final bitis = d['bitis'];
                final aralik = bitis != null && bitis != d['tarih']
                    ? '${d['tarih']} – $bitis'
                    : '${d['tarih']}';
                return Card(
                  color: (kalan >= 0 && kalan <= 7) ? Colors.red.shade50 : null,
                  child: ListTile(
                    title: Text('${d['ad']}'),
                    subtitle: Text('$aralik • $kalan gün • $rozet'),
                    trailing: (d['kaynak_url'] != null && d['kaynak_url'] != '-')
                        ? IconButton(
                            icon: const Icon(Icons.link),
                            onPressed: () => launchUrl(
                              Uri.parse(d['kaynak_url'] as String),
                              mode: LaunchMode.externalApplication,
                            ),
                          )
                        : null,
                  ),
                );
              },
            ),
    );
  }
}
