// Ödev: haftalık planı üret + listele.
import 'package:flutter/material.dart';
import '../config.dart';
import '../main.dart';
import '../models.dart';

class OdevScreen extends StatefulWidget {
  const OdevScreen({super.key});
  @override
  State<OdevScreen> createState() => _OdevScreenState();
}

class _OdevScreenState extends State<OdevScreen> {
  List<OdevGun> _plan = [];
  String _bilgi = '';

  Future<void> _uret() async {
    final id = Session.ogrenciId;
    if (id == null) {
      setState(() => _bilgi = 'Önce Profil sekmesinden öğrenci oluşturun.');
      return;
    }
    try {
      final j = await api.haftalikOdev(id);
      setState(() {
        _plan = (j['plan'] as List).map((e) => OdevGun.fromJson(e)).toList();
        _bilgi = '';
      });
    } catch (e) {
      setState(() => _bilgi = 'Önce sınav sonucu girin (web) veya hata: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: FilledButton.icon(
            onPressed: _uret,
            icon: const Icon(Icons.refresh),
            label: const Text('Bu haftanın planını üret'),
          ),
        ),
        if (_bilgi.isNotEmpty) Padding(padding: const EdgeInsets.all(8), child: Text(_bilgi)),
        Expanded(
          child: ListView.builder(
            itemCount: _plan.length,
            itemBuilder: (c, i) {
              final o = _plan[i];
              return ListTile(
                leading: CircleAvatar(child: Text(o.gun.characters.first)),
                title: Text('${o.gun} — ${o.ders}: ${o.konu}'),
                trailing: Text('${o.adet} soru'),
              );
            },
          ),
        ),
      ],
    );
  }
}
