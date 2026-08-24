import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.onLogin});
  final Future<bool> Function(String email, String pass) onLogin;
  @override State<LoginScreen> createState() => _LoginScreenState();
}
class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _pass = TextEditingController();
  bool _loading=false;
  String? _err;
  Future<void> _do() async {
    setState(()=> _loading=true);
    final ok = await widget.onLogin(_email.text.trim(), _pass.text);
    if(!ok) setState(()=> _err='Giris basarisiz / suresi dolmus');
    setState(()=> _loading=false);
  }
  @override Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F0A18),
      body: Center(child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 400), child: Padding(padding: const EdgeInsets.all(24), child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text('ASARTEPE', style: GoogleFonts.cormorantGaramond(color: const Color(0xFFC9A96E), fontSize: 28, letterSpacing: 6, fontWeight: FontWeight.w700)),
        const Text('SINASTRI AKADEMISI', style: TextStyle(color: Color(0xFFa898c0), letterSpacing: 2, fontSize: 11)),
        const SizedBox(height:32),
        TextField(controller: _email, decoration: InputDecoration(labelText:'E-mail', filled:true, fillColor: Colors.white, border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))), style: const TextStyle(color: Colors.black)),
        const SizedBox(height:12),
        TextField(controller: _pass, obscureText:true, decoration: InputDecoration(labelText:'Sifre', filled:true, fillColor: Colors.white, border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))), style: const TextStyle(color: Colors.black)),
        if(_err!=null) Padding(padding: const EdgeInsets.only(top:8), child: Text(_err!, style: const TextStyle(color: Colors.redAccent))),
        const SizedBox(height:20),
        SizedBox(width: double.infinity, child: ElevatedButton(onPressed: _loading?null:_do, style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFC9A96E), padding: const EdgeInsets.symmetric(vertical:16)), child: _loading? const SizedBox(height:20, child: CircularProgressIndicator(strokeWidth:2)): const Text('GIRIS', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)))),
        const SizedBox(height:12),
        const Text('TR kapali devre - 1 yil lisans', style: TextStyle(color: Color(0xFFa898c0), fontSize: 11)),
      ])))),
    );
  }
}
