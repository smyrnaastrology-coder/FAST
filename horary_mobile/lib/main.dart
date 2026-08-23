import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'services/horary_api.dart';
import 'package:geolocator/geolocator.dart';

void main() => runApp(const HoraryApp());

class HoraryApp extends StatelessWidget {
  const HoraryApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Horary Oracle',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(scaffoldBackgroundColor: const Color(0xFF0F0A18)),
      home: const HoraryHome(),
    );
  }
}

class HoraryHome extends StatefulWidget {
  const HoraryHome({super.key});
  @override
  State<HoraryHome> createState() => _HoraryHomeState();
}

class _HoraryHomeState extends State<HoraryHome> {
  final _ctrl = TextEditingController();
  final List<Map<String, String>> _chat = [];
  bool _loading = false;
  double lat = 38.4237, lon = 27.1428;
  String lang = 'tr';
  final langs = const [
    {'code':'tr','label':'TR','flag':'­şç╣­şçÀ'},
    {'code':'en','label':'EN','flag':'­şç¼­şçğ'},
    {'code':'es','label':'ES','flag':'­şç¬­şç©'},
    {'code':'ar','label':'AR','flag':'­şç©­şçĞ'},
    {'code':'pt','label':'PT','flag':'­şçğ­şçÀ'},
    {'code':'fr','label':'FR','flag':'­şç½­şçÀ'},
    {'code':'de','label':'DE','flag':'­şç®­şç¬'},
    {'code':'ru','label':'RU','flag':'­şçÀ­şç║'},
    {'code':'it','label':'IT','flag':'­şç«­şç╣'},
    {'code':'hi','label':'HI','flag':'­şç«­şç│'},
  ];

  Future<void> _getGPS() async {
    var perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) perm = await Geolocator.requestPermission();
    if (perm == LocationPermission.deniedForever || perm == LocationPermission.denied) return;
    final pos = await Geolocator.getCurrentPosition();
    setState(() { lat = pos.latitude; lon = pos.longitude; });
  }

  Future<void> _ask() async {
    final q = _ctrl.text.trim();
    if (q.isEmpty) return;
    setState(() { _chat.add({'role':'user','content':q}); _loading=true; _ctrl.clear(); });
    try {
      final res = await HoraryApi.cast(question: q, lat: lat, lon: lon, lang: lang);
      final ans = res['answer'] as String? ?? '${res['verdict']}';
      final meta = '${res['location']?['direction'] ?? ''} ${res['location']?['distance'] ?? ''} | ${res['timing']?['text'] ?? ''}';
      setState(() => _chat.add({'role':'assistant','content': '$ans\n\n$meta'}));
    } catch (e) {
      setState(() => _chat.add({'role':'assistant','content': 'Hata: $e'}));
    } finally { setState(()=> _loading=false); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF1A1423),
        title: Column(children: [
          Text('Horary Oracle', style: GoogleFonts.cormorantGaramond(color: const Color(0xFFC9A96E), fontWeight: FontWeight.bold, letterSpacing: 3)),
          const Text('EVRENLE SORU ANININ D─░L─░', style: TextStyle(color: Color(0xFFa898c0), fontSize: 9, letterSpacing: 2)),
        ]), centerTitle: true,
      ),
      body: Column(children: [
        Padding(padding: const EdgeInsets.all(8), child: Row(children: [
          Expanded(child: Text('­şôı $lat, $lon', style: const TextStyle(color: Color(0xFFa898c0), fontSize: 11))),
          Container(padding: const EdgeInsets.symmetric(horizontal:6), decoration: BoxDecoration(color: const Color(0xFF2a1f38), borderRadius: BorderRadius.circular(8), border: Border.all(color: const Color(0xFF3d2e50))),
            child: DropdownButtonHideUnderline(child: DropdownButton<String>(
              value: lang, dropdownColor: const Color(0xFF2a1f38), style: const TextStyle(color: Color(0xFFC9A96E), fontSize: 13),
              items: langs.map((l)=> DropdownMenuItem(value: l['code'] as String, child: Text('${l['flag']} ${l['label']}'))).toList(),
              onChanged: (v){ if(v!=null) setState(()=> lang=v); },
            ))),
          const SizedBox(width:4),
          TextButton(onPressed: _getGPS, child: const Text('GPS', style: TextStyle(color: Color(0xFFC9A96E)))),
        ])),
        Expanded(child: ListView.builder(
          padding: const EdgeInsets.all(12),
          itemCount: _chat.length,
          itemBuilder: (_,i){
            final m=_chat[i];
            final isUser=m['role']=='user';
            return Align(alignment: isUser? Alignment.centerRight:Alignment.centerLeft,
              child: Container(margin: const EdgeInsets.symmetric(vertical:4), padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: isUser? const Color(0xFF2a1f38):const Color(0xFF3d2e50), borderRadius: BorderRadius.circular(14), border: Border(left: BorderSide(color: const Color(0xFFC9A96E), width: isUser?0:3))),
                child: Text(m['content']!, style: const TextStyle(color: Color(0xFFe8e0f0))),));
          },
        )),
        if(_loading) const LinearProgressIndicator(color: Color(0xFFC9A96E)),
        Padding(padding: const EdgeInsets.all(8), child: Row(children: [
          Expanded(child: TextField(controller: _ctrl, decoration: InputDecoration(hintText: 'Sorunuz ÔÇö muhabbet gibi yaz', filled:true, fillColor: Colors.white, border: OutlineInputBorder(borderRadius: BorderRadius.circular(14))), style: const TextStyle(color: Colors.black), onSubmitted: (_)=> _ask())),
          const SizedBox(width:8),
          IconButton(onPressed: _loading?null:_ask, icon: const Icon(Icons.send, color: Color(0xFFC9A96E))),
        ])),
      ]),
    );
  }
}
