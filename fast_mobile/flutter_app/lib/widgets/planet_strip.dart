import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../services/social_service.dart';

/// Gezegen sembolleri (Güneş→Mars).
const Map<String, String> _planetGlyph = {
  'Güneş': '☉',
  'Ay': '☽',
  'Merkür': '☿',
  'Venüs': '♀',
  'Mars': '♂',
};

/// Profil rozeti: Güneş/Ay/Merkür/Venüs/Mars burç + derece şeridi.
///
/// Veri yoksa (kullanıcı natal analiz yapmadıysa) boş döner.
class PlanetStrip extends StatelessWidget {
  final List<PlanetPos> planets;
  final bool compact;
  const PlanetStrip({super.key, required this.planets, this.compact = false});

  @override
  Widget build(BuildContext context) {
    if (planets.isEmpty) return const SizedBox.shrink();
    final size = compact ? 10.5 : 12.0;
    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: [
        for (final p in planets)
          Container(
            padding: EdgeInsets.symmetric(horizontal: compact ? 6 : 8, vertical: compact ? 3 : 4),
            decoration: BoxDecoration(
              color: FastTheme.accentGold.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.25)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _planetGlyph[p.planet] ?? '✧',
                  style: TextStyle(color: FastTheme.accentGold, fontSize: size + 2, fontWeight: FontWeight.w700),
                ),
                const SizedBox(width: 3),
                Text(
                  p.degree == null ? '' : '${p.degree!.toStringAsFixed(1)}°',
                  style: TextStyle(color: FastTheme.text, fontSize: size, fontWeight: FontWeight.w600),
                ),
                Text(
                  p.symbol ?? '',
                  style: TextStyle(color: FastTheme.textDim, fontSize: size + 2),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
