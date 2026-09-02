import 'package:flutter/material.dart';

import '../config/theme.dart';

class SplashLogo extends StatelessWidget {
  const SplashLogo({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: FastTheme.bg,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 72,
              height: 72,
              child: DecoratedBox(
                decoration: BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold),
                child: Center(
                  child: Text('F', style: TextStyle(color: FastTheme.bg, fontSize: 36, fontWeight: FontWeight.bold)),
                ),
              ),
            ),
            SizedBox(height: 16),
            Text('Fast Synastry', style: TextStyle(color: FastTheme.accentGold, fontSize: 30, fontWeight: FontWeight.w700, letterSpacing: 4)),
          ],
        ),
      ),
    );
  }
}