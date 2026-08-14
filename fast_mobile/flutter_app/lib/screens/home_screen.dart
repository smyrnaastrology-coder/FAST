import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../config/theme.dart';
import 'input_form_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(height: 40),
                Container(
                  width: 120, height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: FastTheme.accent, width: 3),
                    boxShadow: [
                      BoxShadow(color: FastTheme.accent.withValues(alpha: 0.3), blurRadius: 20),
                    ],
                  ),
                  child: ClipOval(child: Image.asset('assets/logo.png', fit: BoxFit.cover)),
                ),
                const SizedBox(height: 24),
                Text('Fatih Asartepe\nSinastri Tekni\u011fi',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.cormorantGaramond(
                    fontSize: 28, fontWeight: FontWeight.w700,
                    color: const Color(0xFF3D2E50), height: 1.2,
                  ),
                ),
                const SizedBox(height: 8),
                Text('FAST \u2014 Y\u0131ld\u0131z Ba\u011f Analizi Sistemi',
                  style: TextStyle(fontSize: 13, color: FastTheme.textLight, letterSpacing: 2),
                ),
                const SizedBox(height: 6),
                Text('S\u00fcr\u00fcm 4.0', style: TextStyle(fontSize: 12, color: FastTheme.textLight)),
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: FastTheme.bgSecondary,
                    border: Border.all(color: FastTheme.border),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'Bilgilendirme: Bu \u00e7al\u0131\u015fma gelecekte olacak olaylar\u0131 \u00f6ng\u00f6rmez; kehanet, fal veya kesin yarg\u0131 de\u011fildir. '
                    'Do\u011fum an\u0131ndaki g\u00f6ky\u00fcz\u00fcn\u00fcn yery\u00fcz\u00fcne izd\u00fc\u015f\u00fcm\u00fcn\u00fc, ki\u015fisel fark\u0131ndal\u0131k ve geli\u015fim '
                    'perspektifiyle anlatan bir analiz rehberidir.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 11, color: FastTheme.textMuted, height: 1.5),
                  ),
                ),
                const SizedBox(height: 24),
                _buildModeCard(context, 'E\u015f / Sevgili', Icons.favorite, FastTheme.rose),
                const SizedBox(height: 16),
                _buildModeCard(context, 'Ebeveyn \u2013 \u00c7ocuk', Icons.family_restroom, FastTheme.secondary),
                const SizedBox(height: 16),
                _buildModeCard(context, 'Potansiyel / Yetenek', Icons.auto_awesome, FastTheme.accent),
                const SizedBox(height: 16),
                _buildModeCard(context, 'Bireysel Natal', Icons.person, FastTheme.primary),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildModeCard(BuildContext context, String title, IconData icon, Color color) {
    return SizedBox(
      width: double.infinity,
      child: Card(
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => Navigator.push(context, MaterialPageRoute(
            builder: (_) => InputFormScreen(mod: title),
          )),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(12)),
                  child: Icon(icon, color: color, size: 28),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Text(title, style: GoogleFonts.cormorantGaramond(
                    fontSize: 20, fontWeight: FontWeight.w600, color: FastTheme.textDark,
                  )),
                ),
                Icon(Icons.arrow_forward_ios, color: FastTheme.textLight, size: 16),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
