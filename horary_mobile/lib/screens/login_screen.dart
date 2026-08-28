import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../config/theme.dart';

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
      backgroundColor: FastTheme.bg,
      body: Center(child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 400), child: Padding(padding: const EdgeInsets.all(24), child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text('ASARTEPE', style: GoogleFonts.cormorantGaramond(color: FastTheme.accentGold, fontSize: 28, letterSpacing: 6, fontWeight: FontWeight.w700)),
        const Text('SINASTRI AKADEMISI', style: TextStyle(color: FastTheme.textMuted, letterSpacing: 2, fontSize: 11)),
        const SizedBox(height:32),
        TextField(controller: _email, decoration: const InputDecoration(labelText:'E-mail')),
        const SizedBox(height:12),
        TextField(controller: _pass, obscureText:true, decoration: const InputDecoration(labelText:'Sifre')),
        if(_err!=null) Padding(padding: const EdgeInsets.only(top:8), child: Text(_err!, style: const TextStyle(color: FastTheme.error))),
        const SizedBox(height:20),
        SizedBox(width: double.infinity, child: ElevatedButton(onPressed: _loading?null:_do, style: ElevatedButton.styleFrom(backgroundColor: FastTheme.accentGold, foregroundColor: FastTheme.bg, padding: const EdgeInsets.symmetric(vertical:16)), child: _loading? const SizedBox(height:20, child: CircularProgressIndicator(strokeWidth:2)): const Text('GIRIS', style: TextStyle(fontWeight: FontWeight.bold)))),
        const SizedBox(height:12),
        const Text('TR kapali devre - 1 yil lisans', style: TextStyle(color: FastTheme.textMuted, fontSize: 11)),
      ])))),
    );
  }
}
