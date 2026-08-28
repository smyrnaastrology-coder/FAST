import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'config/theme.dart';
import 'services/horary_api.dart';
import 'widgets/lost_radar_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:flutter/services.dart';
import 'dart:math' as math;

void main() => runApp(const HoraryApp());

// i18n - tum sistem basliklari dile doner
const _t = {
  'tr': {'title':'Horary Oracle','subtitle':'EVRENLE SORU ANININ DILI','hint':'Sorunuz — muhabbet gibi yazın','send':'Gönder','loc':'Konum','clear':'Temizle','copy':'Kopyala','listen':'Dinle','chart':'Harita','asc':'Yükselen','moon':'Ay'},
  'en': {'title':'Horary Oracle','subtitle':'LANGUAGE OF THE MOMENT','hint':'Ask like chatting to a friend','send':'Send','loc':'Location','clear':'Clear','copy':'Copy','listen':'Listen','chart':'Chart','asc':'Ascendant','moon':'Moon'},
  'es': {'title':'Horary Oracle','subtitle':'LENGUAJE DEL MOMENTO','hint':'Pregunta como charlando','send':'Enviar','loc':'Ubicación','clear':'Limpiar','copy':'Copiar','listen':'Escuchar','chart':'Carta','asc':'Asc','moon':'Luna'},
  'ar': {'title':'Horary Oracle','subtitle':'لغة اللحظة','hint':'اسأل كأنك تدردش','send':'إرسال','loc':'الموقع','clear':'مسح','copy':'نسخ','listen':'استماع','chart':'الخريطة','asc':'الطالع','moon':'القمر'},
  'pt': {'title':'Horary Oracle','subtitle':'LINGUAGEM DO MOMENTO','hint':'Pergunte como conversando','send':'Enviar','loc':'Local','clear':'Limpar','copy':'Copiar','listen':'Ouvir','chart':'Mapa','asc':'Asc','moon':'Lua'},
  'fr': {'title':'Horary Oracle','subtitle':'LANGAGE DU MOMENT','hint':'Demandez en discutant','send':'Envoyer','loc':'Lieu','clear':'Effacer','copy':'Copier','listen':'Écouter','chart':'Carte','asc':'Asc','moon':'Lune'},
  'de': {'title':'Horary Oracle','subtitle':'SPRACHE DES MOMENTS','hint':'Frag wie im Gespräch','send':'Senden','loc':'Ort','clear':'Löschen','copy':'Kopieren','listen':'Anhören','chart':'Horoskop','asc':'Asz','moon':'Mond'},
  'ru': {'title':'Horary Oracle','subtitle':'ЯЗЫК МОМЕНТА','hint':'Спроси как в беседе','send':'Отправить','loc':'Место','clear':'Очистить','copy':'Копировать','listen':'Слушать','chart':'Карта','asc':'Асц','moon':'Луна'},
  'it': {'title':'Horary Oracle','subtitle':'LINGUAGGIO DEL MOMENTO','hint':'Chiedi come chiacchierando','send':'Invia','loc':'Posizione','clear':'Pulisci','copy':'Copia','listen':'Ascolta','chart':'Carta','asc':'Asc','moon':'Luna'},
  'hi': {'title':'Horary Oracle','subtitle':'क्षण की भाषा','hint':'दोस्त से बात जैसे पूछें','send':'भेजें','loc':'स्थान','clear':'साफ करें','copy':'कॉपी','listen':'सुनें','chart':'कुंडली','asc':'लग्न','moon':'चंद्र'},
};

class HoraryApp extends StatelessWidget {
  const HoraryApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Horary Oracle',
      debugShowCheckedModeBanner: false,
      theme: FastTheme.dark,
      home: const AuthGate(),
    );
  }
}

class AuthGate extends StatefulWidget { const AuthGate({super.key}); @override State<AuthGate> createState()=> _AuthGateState(); }
class _AuthGateState extends State<AuthGate> {
  bool _ok=false; bool _check=true;
  @override void initState(){ super.initState(); _load(); }
  Future<String> _deviceId() async {
    final p = await SharedPreferences.getInstance();
    var id = p.getString('device_id');
    if(id==null){ id = DateTime.now().millisecondsSinceEpoch.toString() + '_' + (1000+ (DateTime.now().microsecond%9000)).toString(); await p.setString('device_id', id); }
    return id;
  }
  Future<void> _load() async {
    try{
      final p = await SharedPreferences.getInstance();
      final e=p.getString('email'), pw=p.getString('pass');
      if(e!=null && pw!=null){
        final did = await _deviceId();
        final res = await HoraryApi.login(email:e, password:pw, deviceId: did);
        if(res['ok']==true) setState(()=> _ok=true);
      }
    }catch(_){}
    setState(()=> _check=false);
  }
  @override Widget build(BuildContext context) {
    if(_check) return const Scaffold(body: Center(child: CircularProgressIndicator(color: Color(0xFFC9A96E))));
    if(_ok) return const HoraryHome();
    return LoginScreen(onLogin: (email, pass) async {
      try {
        final did = await _deviceId();
        final res = await HoraryApi.login(email: email, password: pass, deviceId: did);
        if(res['ok']==true) {
          final p = await SharedPreferences.getInstance();
          await p.setString('email', email); await p.setString('pass', pass);
          setState(()=> _ok=true); return true;
        }
      } catch(_){ }
      return false;
    });
  }
}
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.onLogin});
  final Future<bool> Function(String,String) onLogin;
  @override State<LoginScreen> createState()=> _LoginScreenState();
}
class _LoginScreenState extends State<LoginScreen> {
  final _e=TextEditingController(), _p=TextEditingController();
  bool _loading=false; String? _err;
  @override Widget build(BuildContext context) {
    return Scaffold(backgroundColor: const Color(0xFF0F0A18), body: Center(child: ConstrainedBox(constraints: const BoxConstraints(maxWidth:400), child: Padding(padding: const EdgeInsets.all(24), child: Column(mainAxisSize: MainAxisSize.min, children: [
      const Text('ASARTEPE', style: TextStyle(color: Color(0xFFC9A96E), fontSize:28, letterSpacing:6, fontWeight: FontWeight.w700)),
      const Text('SINASTRI AKADEMISI', style: TextStyle(color: Color(0xFFa898c0), letterSpacing:2, fontSize:11)),
      const SizedBox(height:32),
      TextField(controller:_e, decoration: InputDecoration(labelText:'E-mail', filled:true, fillColor: Colors.white, border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))), style: const TextStyle(color:Colors.black)),
      const SizedBox(height:12),
      TextField(controller:_p, obscureText:true, decoration: InputDecoration(labelText:'Sifre', filled:true, fillColor: Colors.white, border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))), style: const TextStyle(color:Colors.black)),
      if(_err!=null) Padding(padding: const EdgeInsets.only(top:8), child: Text(_err!, style: const TextStyle(color:Colors.redAccent))),
      const SizedBox(height:20),
      SizedBox(width:double.infinity, child: ElevatedButton(onPressed: _loading?null:() async { setState(()=> _loading=true); final ok=await widget.onLogin(_e.text.trim(), _p.text); if(!ok) setState(()=> _err='Giris basarisiz / suresi doldu'); setState(()=> _loading=false); }, style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFC9A96E), padding: const EdgeInsets.symmetric(vertical:16)), child: _loading? const SizedBox(height:20, child: CircularProgressIndicator(strokeWidth:2)): const Text('GIRIS', style: TextStyle(color:Colors.black, fontWeight: FontWeight.bold)))),
      const SizedBox(height:12), const Text('TR kapali devre - 1 yil lisans', style: TextStyle(color: Color(0xFFa898c0), fontSize:11)),
    ]))))); }
}

class HoraryHome extends StatefulWidget {
  const HoraryHome({super.key});
  @override
  State<HoraryHome> createState() => _HoraryHomeState();
}

class _HoraryHomeState extends State<HoraryHome> {
  final _ctrl = TextEditingController();
  final List<Map<String, dynamic>> _chat = [];
  bool _loading = false;
  double lat = 38.4237, lon = 27.1428;
  String lang = 'tr';
  String _category = 'general';
  Map<String,dynamic>? _lastChart;
  final SpeechToText _speech = SpeechToText();
  bool _listening=false;
  final FlutterTts _tts = FlutterTts();
  List<Map<String,dynamic>> _historyList = []; // kalıcı geçmiş
  bool _showDetails=false;

  String tr(String k) => _t[lang]?[k] ?? _t['tr']![k]!;

  @override void initState(){ super.initState(); _loadHistory(); }

  Future<void> _loadHistory() async {
    final p=await SharedPreferences.getInstance();
    final h=p.getStringList('chat_history');
    if(h!=null && h.isNotEmpty){ try{ setState(()=> _historyList = h.reversed.take(20).map((e)=> {'q': e}).toList()); }catch(_){} }
    lang=p.getString('lang')??'tr';
    setState((){});
  }
  Future<void> _saveHistory(String q) async {
    final p=await SharedPreferences.getInstance();
    final list=p.getStringList('chat_history')??[];
    list.add('${DateTime.now().toIso8601String().substring(0,10)} | $q');
    if(list.length>30) list.removeAt(0);
    await p.setStringList('chat_history', list);
    await p.setString('lang', lang);
    setState(()=> _historyList = list.reversed.take(20).map((e)=> {'q':e}).toList());
  }
  String _timingDate(Map<String,dynamic>? timing){
    if(timing==null) return '';
    final txt=timing['text']??'';
    final m=RegExp(r'(\d+)').firstMatch(txt);
    if(m==null) return '';
    int n=int.parse(m.group(1)!);
    String unit=(timing['unit']??'').toString();
    Duration d;
    if(unit.contains('GÜN')) d=Duration(days:n);
    else if(unit.contains('HAFTA')) d=Duration(days:n*7);
    else if(unit.contains('AY')) d=Duration(days:n*30);
    else if(unit.contains('YIL')) d=Duration(days:n*365);
    else {
      if(txt.contains('GÜN')) d=Duration(days:n);
      else if(txt.contains('HAFTA')) d=Duration(days:n*7);
      else if(txt.contains('AY')) d=Duration(days:n*30);
      else return '';
    }
    final target=DateTime.now().add(d);
    return '${target.day.toString().padLeft(2,'0')}.${target.month.toString().padLeft(2,'0')}.${target.year}';
  }

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

  Future<void> _toggleMic() async {
    if(_listening){
      await _speech.stop(); setState(()=> _listening=false); return;
    }
    bool avail = await _speech.initialize();
    if(!avail) return;
    setState(()=> _listening=true);
    await _speech.listen(localeId: lang=='tr'?'tr-TR': lang=='ar'?'ar-SA': lang=='ru'?'ru-RU': lang=='hi'?'hi-IN':'en-US',
      onResult: (r){ _ctrl.text = r.recognizedWords; });
    Future.delayed(const Duration(seconds:8), () async { if(_listening){ await _speech.stop(); setState(()=> _listening=false); }});
  }

  Future<void> _ask() async {
    final q = _ctrl.text.trim();
    if (q.isEmpty) return;
    setState(() { _chat.add({'role':'user','content':q}); _loading=true; _ctrl.clear(); });
    _saveHistory(q);
    try {
      final res = await HoraryApi.cast(question: q, lat: lat, lon: lon, lang: lang, category: _category);
      final ans = res['answer'] as String? ?? '${res['verdict']}';
      setState(() {
        _lastChart = res;
        _chat.add({'role':'assistant','content': ans, 'meta': res});
      });
    } catch (e) {
      setState(() => _chat.add({'role':'assistant','content': 'Hata: $e'}));
    } finally { setState(()=> _loading=false); }
  }

  void _copy(String txt){ Clipboard.setData(ClipboardData(text: txt)); ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(tr('copy')+' ✓'))); }
  void _speak(String txt) async { await _tts.setLanguage(lang=='tr'?'tr-TR': lang=='ar'?'ar-SA':'en-US'); await _tts.speak(txt); }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: Drawer(backgroundColor: const Color(0xFF1A1423), child: SafeArea(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Padding(padding: const EdgeInsets.all(16), child: Text('Geçmiş Sorular', style: GoogleFonts.cormorantGaramond(color: const Color(0xFFC9A96E), fontSize:18, fontWeight: FontWeight.bold))),
        const Divider(color: Color(0xFF3d2e50)),
        Expanded(child: _historyList.isEmpty ? const Padding(padding: EdgeInsets.all(16), child: Text('Henüz soru yok', style: TextStyle(color: Color(0xFFa898c0)))) : ListView.builder(itemCount: _historyList.length, itemBuilder: (_,i){
          final h=_historyList[i]['q'] as String;
          return ListTile(dense:true, title: Text(h, style: const TextStyle(color: Color(0xFFe8e0f0), fontSize:12), maxLines:2, overflow: TextOverflow.ellipsis), leading: const Icon(Icons.history, size:16, color: Color(0xFFC9A96E)), onTap: (){ Navigator.pop(context); _ctrl.text = h.split('|').last.trim(); });
        })),
        Padding(padding: const EdgeInsets.all(12), child: OutlinedButton(onPressed: () async { final p=await SharedPreferences.getInstance(); await p.remove('chat_history'); setState(()=> _historyList=[]); }, child: Text(tr('clear'), style: const TextStyle(color: Color(0xFFa898c0))))),
      ]))),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1A1423),
        title: Column(children: [
          Text(tr('title'), style: GoogleFonts.cormorantGaramond(color: const Color(0xFFC9A96E), fontWeight: FontWeight.bold, letterSpacing: 3)),
          Text(tr('subtitle'), style: const TextStyle(color: Color(0xFFa898c0), fontSize: 9, letterSpacing: 2)),
        ]), centerTitle: true,
        actions: [
          IconButton(onPressed: ()=> setState(()=> _chat.clear()), icon: const Icon(Icons.delete_outline, color: Color(0xFFa898c0), size:20), tooltip: 'Clear'),
        ],
      ),
      body: Stack(children: [
        Column(children: [
          // top bar: lang + mini location chip
          Padding(padding: const EdgeInsets.fromLTRB(8,8,8,4), child: Row(children: [
            // language dropdown
            Container(padding: const EdgeInsets.symmetric(horizontal:6), decoration: BoxDecoration(color: const Color(0xFF2a1f38), borderRadius: BorderRadius.circular(8), border: Border.all(color: const Color(0xFF3d2e50))),
              child: DropdownButtonHideUnderline(child: DropdownButton<String>(
                value: lang, dropdownColor: const Color(0xFF2a1f38), style: const TextStyle(color: Color(0xFFC9A96E), fontSize: 13),
                items: langs.map((l)=> DropdownMenuItem(value: l['code'] as String, child: Text('${l['flag']} ${l['label']}'))).toList(),
                onChanged: (v){ if(v!=null) setState(()=> lang=v); },
              ))),
            const Spacer(),
            // small location chip corner
            GestureDetector(onTap: _getGPS, child: Container(padding: const EdgeInsets.symmetric(horizontal:10, vertical:6), decoration: BoxDecoration(color: const Color(0xFF2a1f38), borderRadius: BorderRadius.circular(20), border: Border.all(color: const Color(0xFFC9A96E).withOpacity(0.4))),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.location_on, size:14, color: Color(0xFFC9A96E)),
                const SizedBox(width:4),
                Text('${lat.toStringAsFixed(2)}, ${lon.toStringAsFixed(2)}', style: const TextStyle(color: Color(0xFFa898c0), fontSize:11)),
                const SizedBox(width:4), const Icon(Icons.my_location, size:12, color: Color(0xFFC9A96E)),
              ]))),
          ])),
          // konum uyarısı
          Padding(padding: const EdgeInsets.symmetric(horizontal:12, vertical:2), child: Row(children: const [
            Icon(Icons.location_on, size:14, color: Color(0xFFfbbf24)),
            SizedBox(width:6),
            Text('Soruyu sormadan önce konumunuzu seçin', style: TextStyle(color: Color(0xFFfbbf24), fontSize:11, fontStyle: FontStyle.italic)),
          ])),
          // kategori seçici (eski soru alanları geri)
          Padding(padding: const EdgeInsets.symmetric(horizontal:8, vertical:4), child: SingleChildScrollView(scrollDirection: Axis.horizontal, child: Row(children: [
            for(final c in [
              {'k':'general','l':'Otomatik'},
              {'k':'relationship','l':'İlişki/Eş'},
              {'k':'money','l':'Para'},
              {'k':'job','l':'İş/Kariyer'},
              {'k':'health','l':'Sağlık'},
              {'k':'lost_object','l':'Kayıp Eşya'},
              {'k':'missing_person','l':'Kayıp Kişi Nerede'},
              {'k':'house_property','l':'Ev/Arsa'},
              {'k':'child','l':'Çocuk'},
              {'k':'pet','l':'Evcil'},
            ]) Padding(padding: const EdgeInsets.only(right:6), child: ChoiceChip(
              label: Text(c['l']!, style: TextStyle(fontSize:11, color: _category==c['k'] ? Colors.black : const Color(0xFFe8e0f0))),
              selected: _category==c['k'],
              selectedColor: const Color(0xFFC9A96E),
              backgroundColor: const Color(0xFF2a1f38),
              onSelected: (v){ if(v) setState(()=> _category=c['k']!); },
            )),
          ]))),
          // 1) Zaman geri sayım widget'i
          if(_lastChart!=null && _lastChart!['timing']!=null && _lastChart!['timing']['text']!=null && (_lastChart!['timing']['text'] as String).isNotEmpty && !_timingDate(_lastChart!['timing']).isEmpty) Padding(
            padding: const EdgeInsets.symmetric(horizontal:12, vertical:4),
            child: Container(padding: const EdgeInsets.symmetric(horizontal:12, vertical:8), decoration: BoxDecoration(color: const Color(0xFF2a1f38), borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFFC9A96E).withOpacity(0.5))),
              child: Row(children: [
                const Icon(Icons.timer_outlined, size:16, color: Color(0xFFC9A96E)),
                const SizedBox(width:8),
                Expanded(child: Text('⏳ ${_lastChart!['timing']['text']} → ${_timingDate(_lastChart!['timing'])}', style: const TextStyle(color: Color(0xFFe8e0f0), fontSize:11, fontWeight: FontWeight.w600))),
                Container(padding: const EdgeInsets.symmetric(horizontal:8, vertical:4), decoration: BoxDecoration(color: const Color(0xFFC9A96E), borderRadius: BorderRadius.circular(20)), child: Text(_timingDate(_lastChart!['timing']), style: const TextStyle(color: Colors.black, fontSize:11, fontWeight: FontWeight.bold))),
              ])),
          ),
          // Kayıp radar (yön+mesafe ok)
          if(_lastChart!=null && _lastChart!['location']!=null && _lastChart!['location']['direction']!=null) Padding(
            padding: const EdgeInsets.symmetric(horizontal:12, vertical:4),
            child: LostRadarMap(
              lat: lat, lon: lon,
              direction: _lastChart!['location']['direction'] ?? 'BATI',
              distance: _lastChart!['location']['distance'] ?? '',
              place: _lastChart!['location']['place'] ?? '',
              house: _lastChart!['location']['house'] ?? 7,
              deg: (_lastChart!['location']['deg'] is num) ? (_lastChart!['location']['deg'] as num).toDouble() : 15,
            ),
          ),
          // 2) Derived ağaç görseli
          if(_lastChart!=null && _lastChart!['derived_info']!=null) Padding(
            padding: const EdgeInsets.symmetric(horizontal:12, vertical:4),
            child: Container(padding: const EdgeInsets.all(8), decoration: BoxDecoration(color: const Color(0xFF1A1423), borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFF6a9ae2).withOpacity(0.4))),
              child: Row(children: [
                const Icon(Icons.account_tree, size:16, color: Color(0xFF6a9ae2)),
                const SizedBox(width:8),
                Expanded(child: Text('${_lastChart!['derived_info']['base_word']} (${_lastChart!['derived_info']['base_house']}.ev) → ${_lastChart!['derived_info']['topic']} (${_lastChart!['derived_info']['offset']}.ev) = ${_lastChart!['derived_info']['derived']}.ev  •  ${_lastChart!['derived_info']['formula']}', style: const TextStyle(color: Color(0xFFa898c0), fontSize:10))),
              ])),
          ),
          // mini SolarFire chart + timing geri sayım + strictures detay
          if(_lastChart!=null) Padding(
            padding: const EdgeInsets.symmetric(horizontal:12, vertical:4),
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: const Color(0xFF1A1423), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFF3d2e50))),
              child: Column(children: [
                Row(children: [
                  SizedBox(width:72, height:72, child: CustomPaint(painter: MiniChartPainter(_lastChart!))),
                  const SizedBox(width:10),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('${tr('asc')}: ${_lastChart!['houses']?['asc_sign'] ?? ''} ${(_lastChart!['houses']?['asc']!=null? (_lastChart!['houses']['asc']%30).toStringAsFixed(1)+'°':'')}  •  ${tr('moon')}: ${_lastChart!['planets']?['Moon']?['sign'] ?? ''} ${_lastChart!['planets']?['Moon']?['deg']?.toStringAsFixed(1) ?? ''}°', style: const TextStyle(color: Color(0xFFC9A96E), fontSize:11)),
                    const SizedBox(height:2),
                    Text('${_lastChart!['verdict'] ?? ''}  •  ${_lastChart!['timing']?['text'] ?? ''}${_timingDate(_lastChart!['timing']).isNotEmpty? ' → ${_timingDate(_lastChart!['timing'])}':''}', style: const TextStyle(color: Color(0xFFa898c0), fontSize:10), maxLines:2, overflow: TextOverflow.ellipsis),
                    if(_lastChart!['timing']?['ephemeris_text']!=null) Text('Ephemeris: ${_lastChart!['timing']['ephemeris_text']}', style: const TextStyle(color: Color(0xFF6a9ae2), fontSize:10)),
                  ])),
                ]),
                const SizedBox(height:6),
                GestureDetector(onTap: ()=> setState(()=> _showDetails=!_showDetails), child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(_showDetails? Icons.expand_less: Icons.expand_more, size:16, color: const Color(0xFFC9A96E)), Text(_showDetails? ' Detayları gizle':' Detayları gör', style: const TextStyle(color: Color(0xFFC9A96E), fontSize:11))])),
                if(_showDetails) Container(margin: const EdgeInsets.only(top:6), padding: const EdgeInsets.all(8), decoration: BoxDecoration(color: const Color(0xFF2a1f38), borderRadius: BorderRadius.circular(8)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: (_lastChart!['strictures'] as List).map((s)=> Padding(padding: const EdgeInsets.only(bottom:4), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Container(width:6,height:6,margin: const EdgeInsets.only(top:5, right:6), decoration: BoxDecoration(color: s['level']=='warning'? Colors.orange: s['level']=='critical'? Colors.redAccent: const Color(0xFFC9A96E), shape: BoxShape.circle)), Expanded(child: Text('${s['code']}: ${s['meaning']??''}', style: const TextStyle(color: Color(0xFFe8e0f0), fontSize:11)))]))).toList())),
              ]),
            ),
          ),
          Expanded(child: ListView.builder(
            padding: const EdgeInsets.fromLTRB(12,8,12,100),
            itemCount: _chat.length,
            itemBuilder: (_,i){
              final m=_chat[i];
              final isUser=m['role']=='user';
              return Align(alignment: isUser? Alignment.centerRight:Alignment.centerLeft,
                child: Container(margin: const EdgeInsets.symmetric(vertical:4), padding: const EdgeInsets.all(12),
                  constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width*0.82),
                  decoration: BoxDecoration(color: isUser? const Color(0xFFC9A96E):const Color(0xFF3d2e50), borderRadius: BorderRadius.circular(14), border: Border(left: BorderSide(color: const Color(0xFFC9A96E), width: isUser?0:3))),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(m['content']!, style: TextStyle(color: isUser? Colors.black : const Color(0xFFe8e0f0), height:1.45, fontWeight: isUser? FontWeight.w600 : FontWeight.normal)),
                    if(!isUser) Padding(padding: const EdgeInsets.only(top:6), child: Row(mainAxisSize: MainAxisSize.min, children: [
                      GestureDetector(onTap: ()=> _copy(m['content']!), child: Row(children: [const Icon(Icons.copy, size:14, color: Color(0xFFa898c0)), const SizedBox(width:4), Text(tr('copy'), style: const TextStyle(color: Color(0xFFa898c0), fontSize:11))])),
                      const SizedBox(width:12),
                      GestureDetector(onTap: ()=> _speak(m['content']!), child: Row(children: [const Icon(Icons.volume_up, size:14, color: Color(0xFFa898c0)), const SizedBox(width:4), Text(tr('listen'), style: const TextStyle(color: Color(0xFFa898c0), fontSize:11))])),
                    ])),
                  ])));
            },
          )),
          if(_loading) const LinearProgressIndicator(color: Color(0xFFC9A96E)),
          const SizedBox(height: 88),
        ]),
        // centered input floating - biraz yukari alindi (secmesi kolay)
        Positioned(
          left: 0, right: 0, bottom: 32,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 640),
              child: Padding(padding: const EdgeInsets.symmetric(horizontal:12), child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Expanded(child: Container(decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(28), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius:8, offset: const Offset(0,2))]),
                    child: TextField(
                      controller: _ctrl,
                      textAlign: TextAlign.left,
                      textAlignVertical: TextAlignVertical.center,
                      decoration: InputDecoration(
                        hintText: tr('hint'),
                        hintStyle: const TextStyle(color: Colors.black54, fontSize:14),
                        filled:false, border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(horizontal:18, vertical:14),
                      ),
                      style: const TextStyle(color: Colors.black, fontSize: 15),
                      onSubmitted: (_)=> _ask(),
                    ))),
                  const SizedBox(width:8),
                  Container(decoration: BoxDecoration(color: _listening? Colors.redAccent: const Color(0xFF3d2e50), shape: BoxShape.circle), child: IconButton(onPressed: _toggleMic, icon: Icon(_listening? Icons.mic: Icons.mic_none, color: Colors.white, size:20))),
                  const SizedBox(width:8),
                  Container(decoration: const BoxDecoration(color: Color(0xFFC9A96E), shape: BoxShape.circle), child: IconButton(onPressed: _loading?null:_ask, icon: const Icon(Icons.send, color: Colors.white, size:20))),
                ],
              )),
            ),
          ),
        ),
      ]),
    );
  }
}

class MiniChartPainter extends CustomPainter {
  final Map<String,dynamic> data;
  MiniChartPainter(this.data);
  @override void paint(Canvas canvas, Size size){
    final cx=size.width/2, cy=size.height/2, r=size.width/2-4;
    final bg=Paint()..color=const Color(0xFF2a1f38)..style=PaintingStyle.fill;
    final border=Paint()..color=const Color(0xFFC9A96E).withOpacity(0.6)..style=PaintingStyle.stroke..strokeWidth=1.2;
    canvas.drawCircle(Offset(cx,cy), r, bg);
    canvas.drawCircle(Offset(cx,cy), r, border);
    canvas.drawCircle(Offset(cx,cy), r*0.62, border);
    // 12 houses lines
    final asc = (data['houses']?['asc'] ?? 0).toDouble();
    for(int i=0;i<12;i++){
      final ang = (asc + i*30)*math.pi/180 - math.pi/2;
      final p1=Offset(cx+ r*0.62*math.cos(ang), cy+ r*0.62*math.sin(ang));
      final p2=Offset(cx+ r*math.cos(ang), cy+ r*math.sin(ang));
      canvas.drawLine(p1,p2, border);
    }
    // ASC marker
    final ascAng = asc*math.pi/180 - math.pi/2;
    final ascPaint=Paint()..color=const Color(0xFFC9A96E)..strokeWidth=2;
    canvas.drawLine(Offset(cx,cy), Offset(cx+ r*math.cos(ascAng), cy+ r*math.sin(ascAng)), ascPaint);
    // planets dots
    final planets = data['planets'] as Map<String,dynamic>?;
    if(planets!=null){
      final colors={'Sun':Colors.orange,'Moon':Colors.white,'Mercury':Colors.yellowAccent,'Venus':Colors.pinkAccent,'Mars':Colors.redAccent,'Jupiter':Colors.lightBlue,'Saturn':Colors.grey};
      planets.forEach((name,info){
        if(!colors.containsKey(name)) return;
        final lon=(info['lon']??0).toDouble();
        final ang=lon*math.pi/180 - math.pi/2;
        final pr=r*0.78;
        final p=Offset(cx+ pr*math.cos(ang), cy+ pr*math.sin(ang));
        canvas.drawCircle(p, 3, Paint()..color=colors[name]!);
      });
    }
  }
  @override bool shouldRepaint(covariant CustomPainter oldDelegate)=> true;
}
