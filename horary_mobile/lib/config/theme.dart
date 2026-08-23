import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class FastTheme {
  // CSS :root değişkenleriyle birebir uyumlu
  static const Color primary = Color(0xFF3D2E50);
  static const Color primaryLight = Color(0xFF5a4470);
  static const Color accentGold = Color(0xFFC9A96E);
  static const Color accentGoldLight = Color(0xFFe0c68a);
  static const Color accentGoldGlow = Color(0x4DC9A96E);
  static const Color bg = Color(0xFF1a1423);
  static const Color bgSecondary = Color(0xFF221a30);
  static const Color cardBg = Color(0xFF2a1f38);
  static const Color cardBgHover = Color(0xFF34284a);
  static const Color text = Color(0xFFe8e0f0);
  static const Color textMuted = Color(0xFFa898c0);
  static const Color textDim = Color(0xFF7a6a92);
  static const Color border = Color(0xFF3d2e50);
  static const Color success = Color(0xFF4ade80);
  static const Color warning = Color(0xFFfbbf24);
  static const Color danger = Color(0xFFf87171);
  static const Color error = Color(0xFFe57373);

  // Legacy aliases (old light theme names) — kept for backward compat
  static const Color rose = ltRose;
  static const Color accent = ltAccent;
  static const Color secondary = ltSecondary;
  static const Color textDark = ltTextDark;
  static const Color textLight = ltTextLight;

  // Light theme - Asartepe Sinastri Akademisi (altın pusula)
  static const Color ltPrimary = Color(0xFFC9A96E); // altın
  static const Color ltSecondary = Color(0xFFB89A4F); // koyu altın
  static const Color ltAccent = Color(0xFFC9A96E);
  static const Color ltRose = Color(0xFFD4AF37); // altın gül
  static const Color ltTextDark = Color(0xFF3D2E14); // koyu kahve
  static const Color ltTextLight = Color(0xFF8C7A3A);
  static const Color ltBg = Color(0xFFFFFEFB); // beyaz-altın krem
  static const Color ltBorder = Color(0xFFE8DCC0); // altın çizgi

  static ThemeData get dark {
    final colorScheme = ColorScheme.dark(
      primary: accentGold,
      secondary: primaryLight,
      surface: bg,
      error: error,
    );

    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: bg,
      colorScheme: colorScheme,
      appBarTheme: AppBarTheme(
        backgroundColor: bgSecondary,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.cormorantGaramond(
          fontSize: 20, fontWeight: FontWeight.w700, color: accentGold,
        ),
        iconTheme: const IconThemeData(color: text),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: accentGold,
          foregroundColor: bg,
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, fontFamily: 'DM Sans'),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: bg,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: accentGold, width: 2),
        ),
        labelStyle: const TextStyle(color: accentGold, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 1),
        hintStyle: const TextStyle(color: textDim),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      ),
      cardTheme: CardThemeData(
        color: cardBg,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: border),
        ),
      ),
      textTheme: GoogleFonts.dmSansTextTheme(ThemeData.dark().textTheme).apply(
        bodyColor: text,
        displayColor: accentGold,
      ),
      dividerTheme: const DividerThemeData(color: border),
      dropdownMenuTheme: DropdownMenuThemeData(
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: bg,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: border)),
        ),
      ),
    );
  }

  static ThemeData get light {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: ltBg,
      colorScheme: ColorScheme.light(
        primary: ltPrimary,
        secondary: ltSecondary,
        surface: ltBg,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.cormorantGaramond(
          fontSize: 22, fontWeight: FontWeight.w700, color: const Color(0xFF3D2E50),
        ),
        iconTheme: const IconThemeData(color: ltTextDark),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: ltPrimary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: ltBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: ltBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: ltPrimary, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );
  }
}
