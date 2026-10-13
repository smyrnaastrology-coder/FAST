// Karne + Bildirimler + Cihaz (FCM token) kaydı.
import 'package:flutter/material.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import '../config.dart';
import '../main.dart';
import '../models.dart';

class KarneBildirimScreen extends StatefulWidget {
  const KarneBildirimScreen({super.key});
  @override
  State<KarneBildirimScreen> createState() => _KarneBildirimScreenState();
}

class _KarneBildirimScreenState extends State<KarneBildirimScreen> {
  List<BildirimSatir> _bils = [];
  String _bilgi = '';
  String _plan = '';

  @override
  void initState() {
    super.initState();
    _yukle();
  }

  Future<void> _yukle() async {
    final id = Session.ogrenciId;
    if (id == null) {
      setState(() => _bilgi = 'Önce Profil sekmesinden öğrenci oluşturun.');
      return;
    }
    try {
      final l = await api.bildirimler(id);
      final p = await api.plan(id);
      setState(() {
        _bils = l.map((e) => BildirimSatir.fromJson(e)).toList();
        _plan = p['plan'] as String? ?? '';
        _bilgi = '';
      });
    } catch (e) {
      setState(() => _bilgi = 'Hata: $e');
    }
  }

  Future<void> _cihazKaydet() async {
    final id = Session.ogrenciId;
    if (id == null) return;
    try {
      final t = await FirebaseMessaging.instance.getToken();
      if (t == null) {
        setState(() => _bilgi = 'FCM yapılandırması eksik (google-services dosyaları gerekli).');
        return;
      }
      await api.cihazKaydet(id, t);
      setState(() => _bilgi = 'Cihaz kaydedildi, push bildirimleri açılacak.');
    } catch (e) {
      setState(() => _bilgi = 'FCM hazır değil: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _yukle,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_plan.isNotEmpty) Chip(label: Text('Plan: $_plan')),
          FilledButton.tonal(
            onPressed: _cihazKaydet,
            child: const Text('📲 Push bildirimlerini aç (FCM)'),
          ),
          const Divider(),
          const Text('Bildirimler', style: TextStyle(fontWeight: FontWeight.bold)),
          if (_bilgi.isNotEmpty) Text(_bilgi),
          for (final b in _bils)
            ListTile(
              dense: true,
              leading: Icon(b.kanal == 'push' ? Icons.phone_android : Icons.inbox),
              title: Text(b.metin),
              subtitle: Text('${b.tip} • ${b.kanal}'),
            ),
          const Divider(),
          const Text('Karne PDF için web sürümü kullanın (mobilde yakında).',
              style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }
}
