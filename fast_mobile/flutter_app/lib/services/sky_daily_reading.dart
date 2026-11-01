import '../config/astro_lexicon.dart';
import '../config/astro_signs.dart';
import '../l10n/app_localizations.dart';
import '../models/sky_snapshot.dart';

/// Günün astrolojik yorumu — tek astronomik kaynaktan (`/api/sky`) üretilir.
///
/// Yorum; Ay burcu, Ay fazı, en güçlü Ay açısı, Ay'ın boşlukta olması, hızı
/// ve retro gezegenlerden derlenir. Metinler ARB dosyalarında tutulur; bu
/// sınıf yalnızca doğru sırayı ve seçimi yapar. Böylece aynı veriyi gösteren
/// tüm ekranlar aynı dili konuşur.
class SkyDailyReading {
  /// Ay burcunun ekliptik indeksi (0 = Koç).
  final int signIndex;

  /// Kart başlığı, ör. "Ay Aslan'da: görünür olma zamanı".
  final String headline;

  /// Yorum cümleleri (2–5 arası).
  final List<String> body;

  /// Kısa etiketler: burç, faz, en güçlü açı, boşluk.
  final List<String> chips;

  /// Faz sembolü (🌕 gibi).
  final String glyph;

  /// En güçlü Ay açısı; yoksa null.
  final SkyAspect? strongestAspect;

  const SkyDailyReading({
    required this.signIndex,
    required this.headline,
    required this.body,
    required this.chips,
    required this.glyph,
    required this.strongestAspect,
  });
}

/// Orbı en küçük olan açı "günün en güçlü" açısıdır.
SkyAspect? strongestAspect(List<SkyAspect> aspects) {
  if (aspects.isEmpty) return null;
  return aspects.reduce((a, b) => b.orb < a.orb ? b : a);
}

SkyDailyReading buildSkyDailyReading({
  required SkySnapshot sky,
  required AppLocalizations l,
  required String lang,
}) {
  final signIndex = ((sky.moonLongitude % 360) ~/ 30) % 12; // 0 = Koç
  final signName = AstroSigns.localizedName((signIndex + 3) % 12, l);
  final mood = _mood(l, signIndex);
  final aspect = strongestAspect(sky.aspects);

  final body = <String>[
    _signText(l, signIndex),
    _phaseText(l, sky.phaseKey),
    if (aspect != null)
      l.skyReadingAspectLine(
        planetLabel(aspect.planet, lang),
        aspectLabel(aspect.type, lang),
        _aspectText(l, aspect.type),
      ),
    if (sky.voidOfCourse) l.skyReadingVoidNote,
    if (sky.speedKey == 'slow') l.skyReadingSlowNote,
    if (sky.speedKey == 'fast') l.skyReadingFastNote,
    if (sky.retrogrades.isNotEmpty)
      l.skyReadingRetroLine(
        sky.retrogrades.map((p) => planetLabel(p, lang)).join(', '),
      ),
  ];

  final chips = <String>[
    signName,
    phaseLabel(l, sky.phaseKey),
    if (aspect != null) aspectLabel(aspect.type, lang),
    if (sky.voidOfCourse) l.skyVoid,
  ];

  return SkyDailyReading(
    signIndex: signIndex,
    headline: l.skyReadingHeadline(signName, mood),
    body: List.unmodifiable(body),
    chips: List.unmodifiable(chips),
    glyph: kPhaseGlyphs[sky.phaseKey] ?? '☾',
    strongestAspect: aspect,
  );
}

String _mood(AppLocalizations l, int index) => switch (index) {
  0 => l.skyReadingMoodAries,
  1 => l.skyReadingMoodTaurus,
  2 => l.skyReadingMoodGemini,
  3 => l.skyReadingMoodCancer,
  4 => l.skyReadingMoodLeo,
  5 => l.skyReadingMoodVirgo,
  6 => l.skyReadingMoodLibra,
  7 => l.skyReadingMoodScorpio,
  8 => l.skyReadingMoodSagittarius,
  9 => l.skyReadingMoodCapricorn,
  10 => l.skyReadingMoodAquarius,
  _ => l.skyReadingMoodPisces,
};

String _signText(AppLocalizations l, int index) => switch (index) {
  0 => l.skyReadingSignAries,
  1 => l.skyReadingSignTaurus,
  2 => l.skyReadingSignGemini,
  3 => l.skyReadingSignCancer,
  4 => l.skyReadingSignLeo,
  5 => l.skyReadingSignVirgo,
  6 => l.skyReadingSignLibra,
  7 => l.skyReadingSignScorpio,
  8 => l.skyReadingSignSagittarius,
  9 => l.skyReadingSignCapricorn,
  10 => l.skyReadingSignAquarius,
  _ => l.skyReadingSignPisces,
};

String _phaseText(AppLocalizations l, String key) => switch (key) {
  'waxing_crescent' => l.skyReadingPhaseWaxingCrescent,
  'first_quarter' => l.skyReadingPhaseFirstQuarter,
  'waxing_gibbous' => l.skyReadingPhaseWaxingGibbous,
  'full' => l.skyReadingPhaseFull,
  'waning_gibbous' => l.skyReadingPhaseWaningGibbous,
  'last_quarter' => l.skyReadingPhaseLastQuarter,
  'waning_crescent' => l.skyReadingPhaseWaningCrescent,
  _ => l.skyReadingPhaseNew,
};

String _aspectText(AppLocalizations l, String key) => switch (key) {
  'conjunction' => l.skyReadingAspectConjunction,
  'sextile' => l.skyReadingAspectSextile,
  'square' => l.skyReadingAspectSquare,
  'trine' => l.skyReadingAspectTrine,
  _ => l.skyReadingAspectOpposition,
};
