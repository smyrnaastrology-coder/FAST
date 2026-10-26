import '../l10n/app_localizations.dart';

/// Burç adları (0 = Koç ... 11 = Balık), aktif dile göre.
List<String> chartSignNames(AppLocalizations l10n) => [
  l10n.chartSignAries,
  l10n.chartSignTaurus,
  l10n.chartSignGemini,
  l10n.chartSignCancer,
  l10n.chartSignLeo,
  l10n.chartSignVirgo,
  l10n.chartSignLibra,
  l10n.chartSignScorpio,
  l10n.chartSignSagittarius,
  l10n.chartSignCapricorn,
  l10n.chartSignAquarius,
  l10n.chartSignPisces,
];

const List<String> chartSignGlyphs = [
  '♈',
  '♉',
  '♊',
  '♋',
  '♌',
  '♍',
  '♎',
  '♏',
  '♐',
  '♑',
  '♒',
  '♓',
];

/// Ev sistemi kodları; sunucu P/W/R/K/E bekler.
const List<String> chartHouseSystemCodes = ['P', 'W', 'R', 'K', 'E'];

String chartHouseSystemLabel(AppLocalizations l10n, String? code) {
  switch ((code ?? 'P').toUpperCase()) {
    case 'W':
      return l10n.chartHouseWholeSign;
    case 'R':
      return l10n.chartHouseRegiomontanus;
    case 'K':
      return l10n.chartHouseKoch;
    case 'E':
      return l10n.chartHouseEqual;
    case 'P':
    default:
      return l10n.chartHousePlacidus;
  }
}

const Map<String, String> chartPlanetGlyphs = {
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
  'north_node': '☊',
  'chiron': '⚷',
};

String chartPlanetLabel(AppLocalizations l10n, String key) {
  switch (key.toLowerCase()) {
    case 'sun':
      return l10n.chartPlanetSun;
    case 'moon':
      return l10n.chartPlanetMoon;
    case 'mercury':
      return l10n.chartPlanetMercury;
    case 'venus':
      return l10n.chartPlanetVenus;
    case 'mars':
      return l10n.chartPlanetMars;
    case 'jupiter':
      return l10n.chartPlanetJupiter;
    case 'saturn':
      return l10n.chartPlanetSaturn;
    case 'uranus':
      return l10n.chartPlanetUranus;
    case 'neptune':
      return l10n.chartPlanetNeptune;
    case 'pluto':
      return l10n.chartPlanetPluto;
    case 'north_node':
      return l10n.chartPlanetNorthNode;
    case 'chiron':
      return l10n.chartPlanetChiron;
    default:
      return key;
  }
}

String chartAspectLabel(AppLocalizations l10n, String type) {
  switch (type.toLowerCase()) {
    case 'conjunction':
      return l10n.chartAspectConjunction;
    case 'sextile':
      return l10n.chartAspectSextile;
    case 'square':
      return l10n.chartAspectSquare;
    case 'trine':
      return l10n.chartAspectTrine;
    case 'opposition':
      return l10n.chartAspectOpposition;
    default:
      return type;
  }
}
