const List<String> chartSignNames = [
  'Koç',
  'Boğa',
  'İkizler',
  'Yengeç',
  'Aslan',
  'Başak',
  'Terazi',
  'Akrep',
  'Yay',
  'Oğlak',
  'Kova',
  'Balık',
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

const Map<String, String> chartHouseSystemNames = {
  'P': 'Placidus',
  'W': 'Tüm Burç',
  'R': 'Regiomontanus',
  'K': 'Koch',
  'E': 'Eşit Ev',
};

String chartHouseSystemLabel(String? code) =>
    chartHouseSystemNames[(code ?? '').toUpperCase()] ?? (code ?? 'Placidus');

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

const Map<String, String> chartPlanetNamesTr = {
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
  'north_node': 'Kuzey Ay Düğümü',
  'chiron': 'Şiron',
};

String chartPlanetLabel(String key) => chartPlanetNamesTr[key] ?? key;

const Map<String, String> chartAspectNamesTr = {
  'conjunction': 'Kavuşum',
  'sextile': 'Altmışlık',
  'square': 'Kare',
  'trine': 'Üçgen',
  'opposition': 'Karşıt',
};

String chartAspectLabel(String type) =>
    chartAspectNamesTr[type.toLowerCase()] ?? type;
