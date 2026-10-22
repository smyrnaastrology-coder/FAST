import 'package:flutter/material.dart';

import '../config/theme.dart';
import 'holavon_mark.dart';

class SplashLogo extends StatelessWidget {
  const SplashLogo({super.key});

  @override
  Widget build(BuildContext context) {
    return  Scaffold(
      backgroundColor: FastTheme.bg,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            HolavonLogo(size: 96, radius: 24, glow: 0.35),
            SizedBox(height: 18),
            Text('Holavon', style: TextStyle(color: FastTheme.accentGold, fontSize: 30, fontWeight: FontWeight.w700, letterSpacing: 4)),
          ],
        ),
      ),
    );
  }
}