import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import 'input_form_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
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
                Text(l10n.homeTitle,
                  textAlign: TextAlign.center,
                  style: GoogleFonts.cormorantGaramond(
                    fontSize: 28, fontWeight: FontWeight.w700,
                    color: const Color(0xFF3D2E50), height: 1.2,
                  ),
                ),
                const SizedBox(height: 8),
                Text(l10n.homeSubtitle,
                  style: const TextStyle(fontSize: 13, color: FastTheme.textLight, letterSpacing: 2),
                ),
                const SizedBox(height: 6),
                Text(l10n.homeVersion, style: const TextStyle(fontSize: 12, color: FastTheme.textLight)),
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: FastTheme.bgSecondary,
                    border: Border.all(color: FastTheme.border),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    l10n.heroDisclaimer,
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 11, color: FastTheme.textMuted, height: 1.5),
                  ),
                ),
                const SizedBox(height: 24),
                _buildModeCard(context, 'es_sevgili', l10n.modeEsTitle, Icons.favorite, FastTheme.rose),
                const SizedBox(height: 16),
                _buildModeCard(context, 'ebeveyn_cocuk', l10n.modeEbTitle, Icons.family_restroom, FastTheme.secondary),
                const SizedBox(height: 16),
                _buildModeCard(context, 'potansiyel_yetenek', l10n.modePyTitle, Icons.auto_awesome, FastTheme.accent),
                const SizedBox(height: 16),
                _buildModeCard(context, 'bireysel_natal', l10n.modeNatalTitle, Icons.person, FastTheme.primary),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildModeCard(BuildContext context, String modKey, String title, IconData icon, Color color) {
    return SizedBox(
      width: double.infinity,
      child: Card(
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => Navigator.push(context, MaterialPageRoute(
            builder: (_) => InputFormScreen(mod: modKey),
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
                    fontSize: 20, fontWeight: FontWeight.w600, color: FastTheme.text,
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