import 'package:flutter/material.dart';

/// Harita çarkının renk paleti.
///
/// Çizim motoru yalnızca bu paleti okur; astronomik hesaplama katmanı bu
/// dosyadan habersizdir. Böylece renkleri / vurguları değiştirmek gezegen
/// konumlarını, ev başlangıçlarını veya açıları asla etkilemez.
class ChartWheelStyle {
  const ChartWheelStyle({
    required this.light,
    required this.background,
    required this.line,
    required this.lineSoft,
    required this.text,
    required this.muted,
    required this.accent,
    required this.retro,
    required this.transit,
    required this.bandTint,
    required this.transitTint,
    required this.signColors,
    required this.planetColors,
    required this.aspectColors,
    required this.transitAspectColors,
  });

  /// Açık (beyaz zeminli) tema mı?
  final bool light;

  final Color background;
  final Color line;
  final Color lineSoft;
  final Color text;
  final Color muted;
  final Color accent;
  final Color retro;
  final Color transit;
  final Color bandTint;
  final Color transitTint;

  /// 12 burç rengi (0 = Koç).
  final List<Color> signColors;

  /// Gezegen / nokta renkleri (`chartPlanetGlyphs` anahtarlarıyla).
  final Map<String, Color> planetColors;

  /// Açı renkleri (küçük harf açı adıyla).
  final Map<String, Color> aspectColors;

  /// İç (doğum) ile dış (transit) harita arasındaki açıların renkleri.
  /// Doğum haritasının kendi açılarından ayırt edilebilmeleri için ayrı tutulur.
  final Map<String, Color> transitAspectColors;

  Color signColor(int sign) => signColors[sign % 12];

  Color planetColor(String name) =>
      planetColors[name.toLowerCase()] ?? text;

  Color aspectColor(String type) =>
      aspectColors[type.toLowerCase()] ?? muted;

  Color transitAspectColor(String type) =>
      transitAspectColors[type.toLowerCase()] ?? transit;

  /// Referans haritadaki beyaz zeminli palet.
  static const lightStyle = ChartWheelStyle(
    light: true,
    background: Colors.white,
    line: Color(0xFF1F1F1F),
    lineSoft: Color(0xFF6B7280),
    text: Color(0xFF111827),
    muted: Color(0xFF4B5563),
    accent: Color(0xFF7A5C00),
    retro: Color(0xFF9D261A),
    transit: Color(0xFF005A95),
    bandTint: Color(0xFFF7F7F9),
    transitTint: Color(0xFFF1F7FE),
    signColors: [
      Color(0xFFD62828), // Koç
      Color(0xFF2E8B57), // Boğa
      Color(0xFF20B7C7), // İkizler
      Color(0xFF2864B4), // Yengeç
      Color(0xFFD62828), // Aslan
      Color(0xFF2E8B57), // Başak
      Color(0xFF20B7C7), // Terazi
      Color(0xFF2864B4), // Akrep
      Color(0xFFD62828), // Yay
      Color(0xFF2E8B57), // Oğlak
      Color(0xFF20B7C7), // Kova
      Color(0xFF2864B4), // Balık
    ],
    planetColors: {
      'sun': Color(0xFFA68A00),
      'moon': Color(0xFF9C8B20),
      'mercury': Color(0xFFB00078),
      'venus': Color(0xFF20B7C7),
      'mars': Color(0xFFD62828),
      'jupiter': Color(0xFF5545B8),
      'saturn': Color(0xFF9B3D38),
      'uranus': Color(0xFF245DA8),
      'neptune': Color(0xFF159B9B),
      'pluto': Color(0xFF7D1735),
      'chiron': Color(0xFF3C8B57),
      'north_node': Color(0xFF222222),
      'south_node': Color(0xFF222222),
      'vertex': Color(0xFF222222),
      'fortune': Color(0xFF222222),
    },
    aspectColors: {
      'trine': Color(0xFF1745C5),
      'sextile': Color(0xFF159B68),
      'square': Color(0xFFD62728),
      'opposition': Color(0xFFD62728),
      'conjunction': Color(0xFF7A5C00),
    },
    transitAspectColors: {
      'trine': Color(0xFF20B7C7),
      'sextile': Color(0xFF159B68),
      'square': Color(0xFFD62728),
      'opposition': Color(0xFFE4572E),
      'conjunction': Color(0xFF7A5C00),
    },
  );

  /// Koyu (gece) tema. Aynı paletin okunabilirlik için açılmış tonları.
  static const darkStyle = ChartWheelStyle(
    light: false,
    background: Color(0xFF0D1017),
    line: Color(0xFF8290A7),
    lineSoft: Color(0xFF4B5563),
    text: Color(0xFFE5E7EB),
    muted: Color(0xFFBBC4D4),
    accent: Color(0xFFE6C57A),
    retro: Color(0xFFFFBF80),
    transit: Color(0xFF8FD8FF),
    bandTint: Color(0xFF121721),
    transitTint: Color(0xFF152238),
    signColors: [
      Color(0xFFFF6B6B), // Koç
      Color(0xFF5FD08A), // Boğa
      Color(0xFF4DD0E1), // İkizler
      Color(0xFF6FA8FF), // Yengeç
      Color(0xFFFF6B6B), // Aslan
      Color(0xFF5FD08A), // Başak
      Color(0xFF4DD0E1), // Terazi
      Color(0xFF6FA8FF), // Akrep
      Color(0xFFFF6B6B), // Yay
      Color(0xFF5FD08A), // Oğlak
      Color(0xFF4DD0E1), // Kova
      Color(0xFF6FA8FF), // Balık
    ],
    planetColors: {
      'sun': Color(0xFFFFD54F),
      'moon': Color(0xFFE6E0A3),
      'mercury': Color(0xFFFF8FD1),
      'venus': Color(0xFF7FE7F5),
      'mars': Color(0xFFFF7B72),
      'jupiter': Color(0xFFB0A3FF),
      'saturn': Color(0xFFE0A0A0),
      'uranus': Color(0xFF8FC2FF),
      'neptune': Color(0xFF6FE0E0),
      'pluto': Color(0xFFE58AA8),
      'chiron': Color(0xFF8FD8A8),
      'north_node': Color(0xFFD1D5DB),
      'south_node': Color(0xFFD1D5DB),
      'vertex': Color(0xFFD1D5DB),
      'fortune': Color(0xFFD1D5DB),
    },
    aspectColors: {
      'trine': Color(0xFF7FA6FF),
      'sextile': Color(0xFF5FD08A),
      'square': Color(0xFFFF7B72),
      'opposition': Color(0xFFFF9B7B),
      'conjunction': Color(0xFFE6C57A),
    },
    transitAspectColors: {
      'trine': Color(0xFF6FE0E0),
      'sextile': Color(0xFF5FD08A),
      'square': Color(0xFFFF7B72),
      'opposition': Color(0xFFFFB27B),
      'conjunction': Color(0xFFE6C57A),
    },
  );

  static ChartWheelStyle of(bool light) => light ? lightStyle : darkStyle;
}
