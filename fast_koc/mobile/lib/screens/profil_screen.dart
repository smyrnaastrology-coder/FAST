// Profil: oluştur + seç (segment: LGS / ARA_9_10_11 / YKS_ESKI / YKS_MAARIF).
import 'package:flutter/material.dart';
import '../config.dart';
import '../main.dart';
import '../models.dart';

const segmentEtiket = {
  'LGS': 'LGS (8. sınıf)',
  'ARA_9_10_11': '9-10-11. sınıflar',
  'YKS_ESKI': 'YKS — 12/Mezun (Eski Sistem)',
  'YKS_MAARIF': 'YKS — Maarif (11. sınıf)',
};

class ProfilScreen extends StatefulWidget {
  const ProfilScreen({super.key});
  @override
  State<ProfilScreen> createState() => _ProfilScreenState();
}

class _ProfilScreenState extends State<ProfilScreen> {
  final _ad = TextEditingController(text: 'Öğrenci');
  String _segment = 'YKS_ESKI';
  String _seviye = 'orta';
  String _bilgi = '';

  Future<void> _olustur() async {
    try {
      final j = await api.profilOlustur({
        'ad': _ad.text, 'rol': 'ogrenci',
        'segment': _segment, 'seviye': _seviye,
      });
      final o = Ogrenci.fromJson(j);
      setState(() {
        Session.ogrenciId = o.id;
        Session.ogrenciAd = o.ad;
        Session.segment = o.segment;
        _bilgi = 'Oluşturuldu: ${o.ad} (${segmentEtiket[o.segment] ?? o.segment})';
      });
    } catch (e) {
      setState(() => _bilgi = 'Hata: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('2026-27: 12/mezun eski sistem, 9-10-11 Maarif.',
            style: TextStyle(color: Colors.grey)),
        TextField(controller: _ad, decoration: const InputDecoration(labelText: 'Ad')),
        DropdownButtonFormField<String>(
          initialValue: _segment,
          items: segmentEtiket.entries
              .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
              .toList(),
          onChanged: (v) => setState(() => _segment = v!),
          decoration: const InputDecoration(labelText: 'Segment'),
        ),
        DropdownButtonFormField<String>(
          initialValue: _seviye,
          items: const ['temel', 'orta', 'ileri']
              .map((e) => DropdownMenuItem(value: e, child: Text(e)))
              .toList(),
          onChanged: (v) => setState(() => _seviye = v!),
          decoration: const InputDecoration(labelText: 'Seviye'),
        ),
        const SizedBox(height: 12),
        FilledButton(onPressed: _olustur, child: const Text('Oluştur ve Seç')),
        if (_bilgi.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 8), child: Text(_bilgi)),
      ],
    );
  }
}
