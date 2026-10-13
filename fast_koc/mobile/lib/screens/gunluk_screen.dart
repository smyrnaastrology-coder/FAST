// Günlük: soru girişi + kıyas yorumu.
import 'package:flutter/material.dart';
import '../config.dart';
import '../main.dart';

class GunlukScreen extends StatefulWidget {
  const GunlukScreen({super.key});
  @override
  State<GunlukScreen> createState() => _GunlukScreenState();
}

class _GunlukScreenState extends State<GunlukScreen> {
  final _soru = TextEditingController(text: '50');
  final _dk = TextEditingController(text: '90');
  String _yorum = '';

  Future<void> _kaydet() async {
    final id = Session.ogrenciId;
    if (id == null) {
      setState(() => _yorum = 'Önce Profil sekmesinden öğrenci oluşturun.');
      return;
    }
    final bugun = DateTime.now().toIso8601String().substring(0, 10);
    try {
      final j = await api.gunlukKaydet({
        'ogrenci_id': id, 'tarih': bugun,
        'cozulen_soru': int.tryParse(_soru.text) ?? 0,
        'calisilan_dk': int.tryParse(_dk.text) ?? 0,
      });
      setState(() => _yorum = j['yorum'] as String? ?? 'Kaydedildi.');
    } catch (e) {
      setState(() => _yorum = 'Hata: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('🔔 Gün sonu: bugünkü soru sayını gir.'),
        TextField(controller: _soru, keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Çözülen soru')),
        TextField(controller: _dk, keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Çalışılan dakika')),
        const SizedBox(height: 12),
        FilledButton(onPressed: _kaydet, child: const Text('Kaydet')),
        if (_yorum.isNotEmpty)
          Card(child: Padding(padding: const EdgeInsets.all(12), child: Text(_yorum))),
      ],
    );
  }
}
