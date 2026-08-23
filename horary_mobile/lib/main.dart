import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'services/horary_api.dart';
import 'package:geolocator/geolocator.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'config/theme.dart';

void main() => runApp(const HoraryApp());

class HoraryApp extends StatelessWidget {
  const HoraryApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Horary Oracle',
      debugShowCheckedModeBanner: false,
      theme: FastTheme.light,
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
  final _scroll = ScrollController();
  final List<Map<String, String>> _chat = [];
  bool _loading = false;
  double lat = 38.4237, lon = 27.1428;
  String lang = 'tr';
  final _tts = FlutterTts();
  final langs = const [
    {'code':'tr','label':'TR','flag':'🇹🇷'},
    {'code':'en','label':'EN','flag':'🇬🇧'},
    {'code':'es','label':'ES','flag':'🇪🇸'},
    {'code':'ar','label':'AR','flag':'🇸🇦'},
    {'code':'pt','label':'PT','flag':'🇧🇷'},
    {'code':'fr','label':'FR','flag':'🇫🇷'},
    {'code':'de','label':'DE','flag':'🇩🇪'},
    {'code':'ru','label':'RU','flag':'🇷🇺'},
    {'code':'it','label':'IT','flag':'🇮🇹'},
    {'code':'hi','label':'HI','flag':'🇮🇳'},
  ];

  Future<void> _getGPS() async {
    var perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) perm = await Geolocator.requestPermission();
    if (perm == LocationPermission.deniedForever || perm == LocationPermission.denied) return;
    final pos = await Geolocator.getCurrentPosition();
    setState(() { lat = pos.latitude; lon = pos.longitude; });
  }

  Future<void> _speak(String t) async {
    await _tts.setLanguage(lang == 'tr' ? 'tr-TR' : lang == 'ar' ? 'ar-SA' : lang == 'es' ? 'es-ES' : lang == 'fr' ? 'fr-FR' : lang == 'de' ? 'de-DE' : lang == 'ru' ? 'ru-RU' : lang == 'it' ? 'it-IT' : lang == 'pt' ? 'pt-BR' : 'en-US');
    await _tts.setSpeechRate(0.45); await _tts.setPitch(1.0);
    await _tts.speak(t);
  }

  void _jumpTop() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) _scroll.animateTo(0, duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
    });
  }

  Future<void> _ask() async {
    final q = _ctrl.text.trim();
    if (q.isEmpty) return;
    setState(() { _chat.insert(0, {'role':'user','content':q}); _loading=true; _ctrl.clear(); });
    _jumpTop();
    try {
      final hist = _chat.reversed.map((m)=> {'role':m['role'],'content':m['content']}).toList();
      final res = await HoraryApi.cast(question: q, lat: lat, lon: lon, lang: lang, history: hist);
      final ans = res['answer'] as String? ?? '${res['verdict']}';
      final meta = '${res['location']?['direction'] ?? ''} ${res['location']?['distance'] ?? ''} | ${res['timing']?['text'] ?? ''}';
      setState(() => _chat.insert(0, {'role':'assistant','content': '$ans\n\n$meta'}));
      _jumpTop();
    } catch (e) {
      setState(() => _chat.insert(0, {'role':'assistant','content': 'Hata: $e'}));
      _jumpTop();
    } finally { setState(()=> _loading=false); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FastTheme.ltBg,
      body: Container(
        decoration: const BoxDecoration(
          color: FastTheme.ltBg,
        ),
        child: SafeArea(
          child: Column(children: [
            // Web header birebir: horary_app.py:30 style
            Container(
              padding: const EdgeInsets.symmetric(vertical:10),
              child: Column(children: [
                Text('HORARY ORACLE', style: GoogleFonts.cormorantGaramond(color: FastTheme.accentGold, fontSize: 13, letterSpacing: 4.2, fontWeight: FontWeight.w700)),
                const SizedBox(height:2),
                Text('ASARTEPE SİNASTRİ AKADEMİSİ', style: GoogleFonts.dmSans(color: FastTheme.ltTextLight, fontSize: 11, letterSpacing: 1.4)),
                const SizedBox(height:8),
                Container(height:1, margin: const EdgeInsets.symmetric(horizontal:80), decoration: BoxDecoration(gradient: LinearGradient(colors: [Colors.transparent, const Color(0xFFC9A96E).withOpacity(0.5), Colors.transparent]))),
              ]),
            ),
            Padding(padding: const EdgeInsets.symmetric(horizontal:12, vertical:4), child: Row(children: [
              Container(padding: const EdgeInsets.symmetric(horizontal:8, vertical:4), decoration: BoxDecoration(color: const Color(0xFF2a1f38).withOpacity(0.9), borderRadius: BorderRadius.circular(20), border: Border.all(color: const Color(0xFF3d2e50))),
                child: Row(children: [const Icon(Icons.location_on, size:14, color: Color(0xFFC9A96E)), const SizedBox(width:4), Text('${lat.toStringAsFixed(4)}, ${lon.toStringAsFixed(4)}', style: GoogleFonts.dmSans(color: const Color(0xFFa898c0), fontSize: 11))])),
              const Spacer(),
              Container(padding: const EdgeInsets.symmetric(horizontal:6), decoration: BoxDecoration(color: const Color(0xFF2a1f38), borderRadius: BorderRadius.circular(20), border: Border.all(color: const Color(0xFF3d2e50))),
                child: DropdownButtonHideUnderline(child: DropdownButton<String>(
                  value: lang, dropdownColor: const Color(0xFF2a1f38), style: GoogleFonts.dmSans(color: const Color(0xFFC9A96E), fontSize: 13, fontWeight: FontWeight.w500),
                  items: langs.map((l)=> DropdownMenuItem(value: l['code'] as String, child: Text('${l['flag']} ${l['label']}', style: GoogleFonts.dmSans(fontSize:13)))).toList(),
                  onChanged: (v){ if(v!=null) setState(()=> lang=v); }, icon: const Icon(Icons.expand_more, size:16, color: Color(0xFFC9A96E)),
                ))),
              const SizedBox(width:6),
              ElevatedButton.icon(onPressed: _getGPS, icon: const Icon(Icons.my_location, size:14), label: Text('GPS', style: GoogleFonts.dmSans(fontSize:12, fontWeight: FontWeight.w700)),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFC9A96E), foregroundColor: const Color(0xFF1a1423), padding: const EdgeInsets.symmetric(horizontal:10, vertical:6), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)), elevation: 8, shadowColor: const Color(0xFFC9A96E).withOpacity(0.4))),
            ])),
            // Input üste alındı - cevaplar altta kalmasın
            Container(
              margin: const EdgeInsets.fromLTRB(12,8,12,4),
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16), border: Border.all(color: const Color(0xFF3d2e50)), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.4), blurRadius: 30, offset: const Offset(0,8))]),
              child: Row(children: [
                Expanded(child: TextField(
                  controller: _ctrl,
                  minLines: 1, maxLines: 3,
                  style: GoogleFonts.dmSans(color: Colors.black, fontSize: 15),
                  decoration: InputDecoration(
                    hintText: 'Sorunuz — muhabbet gibi yaz, örn: babam nerede?',
                    hintStyle: GoogleFonts.dmSans(color: const Color(0xFF666666), fontSize:13),
                    filled: false, border: InputBorder.none, contentPadding: const EdgeInsets.symmetric(horizontal:12, vertical:8),
                  ),
                  onSubmitted: (_)=> _ask(),
                )),
                Container(decoration: BoxDecoration(color: const Color(0xFFC9A96E), borderRadius: BorderRadius.circular(12)), child: IconButton(onPressed: _loading?null:_ask, icon: const Icon(Icons.arrow_upward_rounded, color: Color(0xFF1a1423)))),
              ]),
            ),
            Expanded(child: _chat.isEmpty
              ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.auto_awesome, size:48, color: const Color(0xFFC9A96E).withOpacity(0.6)),
                  const SizedBox(height:12),
                  Text('Aklındaki tek ve önemli soruyu sor', style: GoogleFonts.cormorantGaramond(color: const Color(0xFFe8e0f0), fontSize:18, fontWeight: FontWeight.w600)),
                  const SizedBox(height:6),
                  Text('örn: babam nerede? • bu işe girecek miyim?', style: GoogleFonts.dmSans(color: const Color(0xFFa898c0), fontSize:13)),
                ]))
              : ListView.builder(
              controller: _scroll,
              padding: const EdgeInsets.symmetric(horizontal:12, vertical:8),
              itemCount: _chat.length,
              itemBuilder: (_,i){
                final m=_chat[i];
                final isUser=m['role']=='user';
                return Align(
                  alignment: isUser? Alignment.centerRight:Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical:5),
                    padding: const EdgeInsets.symmetric(horizontal:14, vertical:10),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width*0.82),
                    decoration: BoxDecoration(
                      color: isUser ? const Color(0xFF2a1f38).withOpacity(0.95) : const Color(0xFF1e162b).withOpacity(0.95),
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(16), topRight: const Radius.circular(16),
                        bottomLeft: Radius.circular(isUser?16:4), bottomRight: Radius.circular(isUser?4:16),
                      ),
                      border: Border.all(color: isUser? const Color(0xFF3d2e50): const Color(0xFF3d2e50).withOpacity(0.8)),
                      boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.35), blurRadius: 12, offset: const Offset(0,4))],
                    ),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        if(!isUser) Container(width:3, height: 40, margin: const EdgeInsets.only(right:10, top:2), decoration: BoxDecoration(color: const Color(0xFFC9A96E), borderRadius: BorderRadius.circular(2))),
                        Expanded(child: Text(m['content']!, style: GoogleFonts.dmSans(color: const Color(0xFFe8e0f0), fontSize:14, height:1.45))),
                      ]),
                      if(!isUser) Align(alignment: Alignment.centerRight, child: TextButton.icon(onPressed: ()=> _speak(m['content']!), icon: const Icon(Icons.volume_up_rounded, size:16, color: Color(0xFFC9A96E)), label: Text('Sesli Dinle', style: GoogleFonts.dmSans(color: Color(0xFFC9A96E), fontSize:12)), style: TextButton.styleFrom(padding: const EdgeInsets.only(top:6), minimumSize: Size.zero, tapTargetSize: MaterialTapTargetSize.shrinkWrap))),
                    ]),
                  ),
                );
              },
            )),
            if(_loading) Padding(padding: const EdgeInsets.symmetric(horizontal:12), child: LinearProgressIndicator(color: const Color(0xFFC9A96E), backgroundColor: const Color(0xFF3d2e50), minHeight: 2)),
          ]),
        ),
      ),
    );
  }
}
