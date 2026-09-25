import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Tema renk paleti.
///
/// Renkler mutable static'tir: [FastTheme.apply] ile koyu/açık palet arasında
/// geçilir ve tüm widget'lar (eski `FastTheme.bg` vs. okumaları) yeni değerleri
/// görür. Varsayılan: koyu tema (dark).
class FastTheme {
  // ── Dark (varsayılan) ──
  static const Color darkPrimary = Color(0xFF3D2E50);
  static const Color darkPrimaryLight = Color(0xFF5a4470);
  static const Color darkAccentGold = Color(0xFFC9A96E);
  static const Color darkAccentGoldLight = Color(0xFFe0c68a);
  static const Color darkAccentGoldGlow = Color(0x4DC9A96E);
  static const Color darkBg = Color(0xFF1a1423);
  static const Color darkBgSecondary = Color(0xFF221a30);
  static const Color darkCardBg = Color(0xFF2a1f38);
  static const Color darkCardBgHover = Color(0xFF34284a);
  static const Color darkBorder = Color(0xFF3d2e50);

  // ── Light (açık renkler) ──
  static const Color lightPrimary = Color(0xFF5a4470);
  static const Color lightPrimaryLight = Color(0xFF7a6490);
  static const Color lightAccentGold = Color(0xFFb08d3f);
  static const Color lightAccentGoldLight = Color(0xFFcfa96a);
  static const Color lightAccentGoldGlow = Color(0x33C9A96E);
  static const Color lightBg = Color(0xFFFDFAF6);
  static const Color lightBgSecondary = Color(0xFFF5EFE7);
  static const Color lightCardBg = Color(0xFFFFFFFF);
  static const Color lightCardBgHover = Color(0xFFF7F1E8);
  static const Color lightBorder = Color(0xFFE6DCCF);

  // ── Aktif renkler (dark varsayılan) ──
  static Color primary = darkPrimary;
  static Color primaryLight = darkPrimaryLight;
  static Color accentGold = darkAccentGold;
  static Color accentGoldLight = darkAccentGoldLight;
  static Color accentGoldGlow = darkAccentGoldGlow;
  static Color bg = darkBg;
  static Color bgSecondary = darkBgSecondary;
  static Color cardBg = darkCardBg;
  static Color cardBgHover = darkCardBgHover;
  static Color text = const Color(0xFFFFFFFF);
  static Color textMuted = const Color(0xFFFFFFFF);
  static Color textDim = const Color(0xFFE9E2F2);
  static Color border = darkBorder;
  static Color success = const Color(0xFF4ade80);
  static Color warning = const Color(0xFFfbbf24);
  static Color danger = const Color(0xFFf87171);
  static Color error = const Color(0xFFe57373);
  static Color textLight = const Color(0xFFFFFFFF);

  static bool get isDark => bg == darkBg;

  /// İsteğe bağlı: widget'ların aktif paleti izleyip rebuild edebilmesi.
  static ThemeMode mode = ThemeMode.dark;

  /// Aktif paleti değiştirir. Tüm statik renkler güncellenir.
  static void apply(ThemeMode newMode) {
    mode = newMode;
    if (newMode == ThemeMode.dark) {
      primary = darkPrimary;
      primaryLight = darkPrimaryLight;
      accentGold = darkAccentGold;
      accentGoldLight = darkAccentGoldLight;
      accentGoldGlow = darkAccentGoldGlow;
      bg = darkBg;
      bgSecondary = darkBgSecondary;
      cardBg = darkCardBg;
      cardBgHover = darkCardBgHover;
      border = darkBorder;
      text = const Color(0xFFFFFFFF);
      textMuted = const Color(0xFFFFFFFF);
      textDim = const Color(0xFFE9E2F2);
      success = const Color(0xFF4ade80);
      warning = const Color(0xFFfbbf24);
      danger = const Color(0xFFf87171);
      error = const Color(0xFFe57373);
      textLight = const Color(0xFFFFFFFF);
    } else {
      primary = lightPrimary;
      primaryLight = lightPrimaryLight;
      accentGold = lightAccentGold;
      accentGoldLight = lightAccentGoldLight;
      accentGoldGlow = lightAccentGoldGlow;
      bg = lightBg;
      bgSecondary = lightBgSecondary;
      cardBg = lightCardBg;
      cardBgHover = lightCardBgHover;
      border = lightBorder;
      text = const Color(0xFF2D2440);
      textMuted = const Color(0xFF4A3B5C);
      textDim = const Color(0xFF8A7A9A);
      success = const Color(0xFF16a34a);
      warning = const Color(0xFFb45309);
      danger = const Color(0xFFdc2626);
      error = const Color(0xFFdc2626);
      textLight = const Color(0xFF2D2440);
    }
  }

  // Legacy aliases (eski isimler) — uyumluluk için; aktif paletten okur.
  static Color get rose => accentGoldLight;
  static Color get accent => accentGold;
  static Color get secondary => primaryLight;
  static Color get textDark => text;

  // Light theme (original, legacy sabitler)
  static const Color ltPrimary = Color(0xFFB8A9C9);
  static const Color ltSecondary = Color(0xFF8FB8CA);
  static const Color ltAccent = Color(0xFFC9A96E);
  static const Color ltRose = Color(0xFFD4878F);
  static const Color ltTextDark = Color(0xFF4A4A4A);
  static const Color ltTextLight = Color(0xFF6B5B7B);
  static const Color ltBg = Color(0xFFFBF7F4);
  static const Color ltBorder = Color(0xFFE8E0D8);

  static ThemeData get dark {
    final colorScheme = ColorScheme.dark(
      primary: accentGold,
      secondary: primaryLight,
      surface: bg,
      error: error,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: bg,
      colorScheme: colorScheme,
      appBarTheme: AppBarTheme(
        backgroundColor: bgSecondary,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.cormorantGaramond(
          fontSize: 20, fontWeight: FontWeight.w700, color: accentGold,
        ),
        iconTheme:  IconThemeData(color: FastTheme.text),
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
          borderSide:  BorderSide(color: FastTheme.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide:  BorderSide(color: FastTheme.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: accentGold, width: 2),
        ),
        labelStyle: TextStyle(color: accentGold, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 1),
        hintStyle:  TextStyle(color: FastTheme.textDim),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      ),
      cardTheme: CardThemeData(
        color: cardBg,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side:  BorderSide(color: FastTheme.border),
        ),
      ),
      textTheme: GoogleFonts.dmSansTextTheme(ThemeData.dark().textTheme).apply(
        bodyColor: text,
        displayColor: accentGold,
      ),
      dividerTheme:  DividerThemeData(color: FastTheme.border),
      dropdownMenuTheme: DropdownMenuThemeData(
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: bg,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide:  BorderSide(color: FastTheme.border)),
        ),
      ),
    );
  }

  static ThemeData get light {
    final colorScheme = ColorScheme.light(
      primary: primary,
      secondary: primaryLight,
      surface: bg,
      error: error,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: bg,
      colorScheme: colorScheme,
      appBarTheme: AppBarTheme(
        backgroundColor: bgSecondary,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.cormorantGaramond(
          fontSize: 20, fontWeight: FontWeight.w700, color: accentGold,
        ),
        iconTheme:  IconThemeData(color: FastTheme.text),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: accentGold,
          foregroundColor: const Color(0xFFFFFFFF),
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, fontFamily: 'DM Sans'),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: cardBg,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: accentGold, width: 2),
        ),
        labelStyle: TextStyle(color: accentGold, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 1),
        hintStyle: TextStyle(color: textDim),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      ),
      cardTheme: CardThemeData(
        color: cardBg,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: border),
        ),
      ),
      textTheme: GoogleFonts.dmSansTextTheme(ThemeData.light().textTheme).apply(
        bodyColor: text,
        displayColor: accentGold,
      ),
      dividerTheme: DividerThemeData(color: border),
      dropdownMenuTheme: DropdownMenuThemeData(
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: cardBg,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide(color: border)),
        ),
      ),
    );
  }
}