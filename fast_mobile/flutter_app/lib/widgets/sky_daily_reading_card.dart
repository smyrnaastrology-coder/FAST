import 'package:flutter/material.dart';

import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/sky_snapshot.dart';
import '../services/sky_daily_reading.dart';

/// Gökyüzü Takvimi'nin en üstündeki "Bugünün Gökyüzü" kartı.
///
/// Tüm metin `/api/sky` anlık görüntüsünden üretilir; yorum motoru tek
/// kaynaktır. Veri yoksa kart hiç çizilmez.
class SkyDailyReadingCard extends StatelessWidget {
  final SkySnapshot sky;

  const SkyDailyReadingCard({super.key, required this.sky});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final lang = Localizations.localeOf(context).languageCode;
    final reading = buildSkyDailyReading(sky: sky, l: l, lang: lang);
    final signIndex = (reading.signIndex + 3) % 12; // AstroSigns: Oğlak = 0

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            FastTheme.primary.withValues(alpha: 0.26),
            FastTheme.cardBg,
          ],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: FastTheme.accentGold.withValues(alpha: 0.38),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(reading.glyph, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  l.skyReadingTitle,
                  style: TextStyle(
                    color: FastTheme.accentGoldLight,
                    fontSize: 10.5,
                    letterSpacing: 1.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Text(
                AstroSigns.symbols[signIndex],
                style: TextStyle(
                  color: FastTheme.accentGoldLight.withValues(alpha: 0.7),
                  fontSize: 18,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            reading.headline,
            style: TextStyle(
              color: FastTheme.text,
              fontSize: 17,
              height: 1.3,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          for (final sentence in reading.body)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text(
                sentence,
                style: TextStyle(
                  color: FastTheme.textMuted.withValues(alpha: 0.95),
                  fontSize: 13,
                  height: 1.45,
                ),
              ),
            ),
          const SizedBox(height: 4),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final chip in reading.chips)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 9,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: FastTheme.accentGold.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: FastTheme.accentGold.withValues(alpha: 0.25),
                    ),
                  ),
                  child: Text(
                    chip,
                    style: TextStyle(
                      color: FastTheme.accentGoldLight,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
