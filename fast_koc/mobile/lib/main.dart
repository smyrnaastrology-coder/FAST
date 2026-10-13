// Fast Koç — mobil giriş (8 sekme, API'ye bağlı).
import 'package:flutter/material.dart';
import 'api_client.dart';
import 'config.dart';
import 'screens/profil_screen.dart';
import 'screens/sinav_screen.dart';
import 'screens/odev_screen.dart';
import 'screens/kitap_screen.dart';
import 'screens/takvim_screen.dart';
import 'screens/gunluk_screen.dart';
import 'screens/karne_bildirim_screen.dart';

FastKocApi get api => FastKocApi(baseUrl: fastKocBaseUrl, token: Session.token);

void main() => runApp(const FastKocApp());

class FastKocApp extends StatelessWidget {
  const FastKocApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fast Koç',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF14213D),
          primary: const Color(0xFF14213D),
          secondary: const Color(0xFFFCA311),
        ),
        useMaterial3: true,
      ),
      home: const AnaSayfa(),
    );
  }
}

class AnaSayfa extends StatefulWidget {
  const AnaSayfa({super.key});
  @override
  State<AnaSayfa> createState() => _AnaSayfaState();
}

class _AnaSayfaState extends State<AnaSayfa> {
  int _i = 0;

  @override
  Widget build(BuildContext context) {
    final sayfalar = [
      const ProfilScreen(),
      const SinavScreen(),
      const OdevScreen(),
      const KitapScreen(),
      const TakvimScreen(),
      const GunlukScreen(),
      const KarneBildirimScreen(),
    ];
    return Scaffold(
      appBar: AppBar(
        title: const Text('🚀 Fast Koç'),
        actions: [
          if (Session.ogrenciAd != null)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Center(child: Text(Session.ogrenciAd!)),
            ),
        ],
      ),
      body: sayfalar[_i],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _i,
        onDestinationSelected: (v) => setState(() => _i = v),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.person), label: 'Profil'),
          NavigationDestination(icon: Icon(Icons.edit_note), label: 'Sınav'),
          NavigationDestination(icon: Icon(Icons.assignment), label: 'Ödev'),
          NavigationDestination(icon: Icon(Icons.book), label: 'Kitap'),
          NavigationDestination(icon: Icon(Icons.calendar_month), label: 'Takvim'),
          NavigationDestination(icon: Icon(Icons.bar_chart), label: 'Günlük'),
          NavigationDestination(icon: Icon(Icons.school), label: 'Karne'),
        ],
      ),
    );
  }
}
