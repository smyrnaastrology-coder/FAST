import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/theme.dart';
import 'screens/landing_screen.dart';
import 'screens/analyzer_screen.dart';
import 'providers/analysis_provider.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (_) => AnalysisProvider(),
      child: const FastApp(),
    ),
  );
}

class FastApp extends StatelessWidget {
  const FastApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FAST',
      debugShowCheckedModeBanner: false,
      theme: FastTheme.dark,
      home: const LandingScreen(),
    );
  }
}
