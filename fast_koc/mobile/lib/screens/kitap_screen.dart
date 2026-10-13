// Kitap: kapaklı öneriler.
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../config.dart';
import '../main.dart';

class KitapScreen extends StatefulWidget {
  const KitapScreen({super.key});
  @override
  State<KitapScreen> createState() => _KitapScreenState();
}

class _KitapScreenState extends State<KitapScreen> {
  List<dynamic> _kitaplar = [];
  String _bilgi = '';

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
    // api_client'ta kitap endpointi: /api/kitap/oner/{id} — ham çağrı:
    setState(() => _bilgi = 'Yükleniyor...');
    try {
      final j = await api.kitapOner(id);
      setState(() { _kitaplar = j['oneriler'] as List; _bilgi = ''; });
    } catch (e) {
      setState(() => _bilgi = 'Hata: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _yukle,
      child: _kitaplar.isEmpty
          ? ListView(children: [Padding(padding: const EdgeInsets.all(16), child: Text(_bilgi))])
          : ListView.builder(
              itemCount: _kitaplar.length,
              itemBuilder: (c, i) {
                final k = _kitaplar[i];
                return Card(
                  child: ListTile(
                    leading: SizedBox(
                      width: 48,
                      child: CachedNetworkImage(
                        imageUrl: k['kapak_url'] ?? '',
                        errorWidget: (_, _, _) => const Icon(Icons.book, size: 40),
                      ),
                    ),
                    title: Text('${k['baslik']}'),
                    subtitle: Text('${k['yayin']} • ${k['tur']} • ${k['seviye']}'),
                  ),
                );
              },
            ),
    );
  }
}
