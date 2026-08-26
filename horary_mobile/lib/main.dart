import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'services/horary_api.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() => runApp(const HoraryApp());

class HoraryApp extends StatelessWidget {
  const HoraryApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Horary Oracle',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(scaffoldBackgroundColor: const Color(0xFF0F0A18)),
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
  final List<Map<String, String>> _chat = [];
  bool _loading = false;
  double lat = 38.4237, lon = 27.1428;
  String lang = 'tr';
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
          const Text('EVRENLE SORU ANININ DILI', style: TextStyle(color: Color(0xFFa898c0), fontSize: 9, letterSpacing: 2)),
        ]), centerTitle: true,
      ),
      body: Column(children: [
        Padding(padding: const EdgeInsets.all(8), child: Row(children: [
          Expanded(child: Text('\u{1F4CD} $lat, $lon', style: const TextStyle(color: Color(0xFFa898c0), fontSize: 11))),
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
        Container(
          padding: const EdgeInsets.fromLTRB(12,8,12,12),
          alignment: Alignment.center,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 600),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Expanded(child: TextField(
                    controller: _ctrl,
                    textAlign: TextAlign.left,
                    textAlignVertical: TextAlignVertical.center,
                    decoration: InputDecoration(
                      hintText: 'Sorunuz — muhabbet gibi yaz',
                      filled:true, fillColor: Colors.white,
                      contentPadding: const EdgeInsets.symmetric(horizontal:16, vertical:14),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                    ),
                    style: const TextStyle(color: Colors.black, fontSize: 15),
                    onSubmitted: (_)=> _ask(),
                  )),
                  const SizedBox(width:10),
                  Container(
                    decoration: const BoxDecoration(color: Color(0xFFC9A96E), shape: BoxShape.circle),
                    child: IconButton(onPressed: _loading?null:_ask, icon: const Icon(Icons.send, color: Colors.white)),
                  ),
                ],
              ),
            ),
          ),
        ),
      ]),
    );
  }
}
