import '../l10n/app_localizations.dart';

/// Gökyüzü ekranlarında ortak kullanılan gezegen/açı/faz adları.
///
/// Tek yerde tutulur; böylece gökyüzü şeridi, detay sayfası ve günlük
/// yorum aynı olayı farklı adlarla göstermez.

const kPhaseGlyphs = {
  'new': '🌑',
  'waxing_crescent': '🌒',
  'first_quarter': '🌓',
  'waxing_gibbous': '🌔',
  'full': '🌕',
  'waning_gibbous': '🌖',
  'last_quarter': '🌗',
  'waning_crescent': '🌘',
};

const kPlanetGlyphs = {
  'sun': '☉',
  'moon': '☾',
  'mercury': '☿',
  'venus': '♀',
  'mars': '♂',
  'jupiter': '♃',
  'saturn': '♄',
  'uranus': '♅',
  'neptune': '♆',
  'pluto': '♇',
};

const _planetTr = {
  'sun': 'Güneş',
  'moon': 'Ay',
  'mercury': 'Merkür',
  'venus': 'Venüs',
  'mars': 'Mars',
  'jupiter': 'Jüpiter',
  'saturn': 'Satürn',
  'uranus': 'Uranüs',
  'neptune': 'Neptün',
  'pluto': 'Plüton',
};

const _planetEn = {
  'sun': 'Sun',
  'moon': 'Moon',
  'mercury': 'Mercury',
  'venus': 'Venus',
  'mars': 'Mars',
  'jupiter': 'Jupiter',
  'saturn': 'Saturn',
  'uranus': 'Uranus',
  'neptune': 'Neptune',
  'pluto': 'Pluto',
};

const _planetEs = {
  'sun': 'Sol',
  'moon': 'Luna',
  'mercury': 'Mercurio',
  'venus': 'Venus',
  'mars': 'Marte',
  'jupiter': 'Júpiter',
  'saturn': 'Saturno',
  'uranus': 'Urano',
  'neptune': 'Neptuno',
  'pluto': 'Plutón',
};

const _aspectTr = {
  'conjunction': 'kavuşum',
  'sextile': 'altmışlık',
  'square': 'kare',
  'trine': 'üçgen',
  'opposition': 'karşıt',
};

const _aspectEn = {
  'conjunction': 'conjunction',
  'sextile': 'sextile',
  'square': 'square',
  'trine': 'trine',
  'opposition': 'opposition',
};

const _aspectEs = {
  'conjunction': 'conjunción',
  'sextile': 'sextil',
  'square': 'cuadratura',
  'trine': 'trígono',
  'opposition': 'oposición',
};

String planetLabel(String key, String lang) {
  final map = switch (lang) {
    'en' => _planetEn,
    'es' => _planetEs,
    _ => _planetTr,
  };
  return map[key] ?? key;
}

String aspectLabel(String key, String lang) {
  final map = switch (lang) {
    'en' => _aspectEn,
    'es' => _aspectEs,
    _ => _aspectTr,
  };
  return map[key] ?? key;
}

String phaseLabel(AppLocalizations l, String key) => switch (key) {
  'waxing_crescent' => l.skyPhaseWaxingCrescent,
  'first_quarter' => l.skyPhaseFirstQuarter,
  'waxing_gibbous' => l.skyPhaseWaxingGibbous,
  'full' => l.skyPhaseFull,
  'waning_gibbous' => l.skyPhaseWaningGibbous,
  'last_quarter' => l.skyPhaseLastQuarter,
  'waning_crescent' => l.skyPhaseWaningCrescent,
  _ => l.skyPhaseNew,
};

String speedLabel(AppLocalizations l, String key) => switch (key) {
  'slow' => l.skySpeedSlow,
  'fast' => l.skySpeedFast,
  _ => l.skySpeedNormal,
};
