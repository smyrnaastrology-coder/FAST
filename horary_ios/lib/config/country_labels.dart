// Ülke adları görüntü etiketleri.
// Backend Türkçe ülke adları bekler (şehir/UTC sorguları), bu yüzden dropdown
// DEĞERLERİ Türkçe kalır; yalnızca görüntülenen etiket dile göre çevrilir.

const Map<String, String> _countryLabelsEn = {
  'Türkiye': 'Turkey', 'Almanya': 'Germany', 'İngiltere': 'United Kingdom',
  'Fransa': 'France', 'İtalya': 'Italy', 'İspanya': 'Spain',
  'Portekiz': 'Portugal', 'Yunanistan': 'Greece', 'Hollanda': 'Netherlands',
  'Belçika': 'Belgium', 'İsviçre': 'Switzerland', 'Avusturya': 'Austria',
  'İsveç': 'Sweden', 'Norveç': 'Norway', 'Danimarka': 'Denmark',
  'Finlandiya': 'Finland', 'İrlanda': 'Ireland', 'Polonya': 'Poland',
  'Çekya': 'Czechia', 'Macaristan': 'Hungary', 'Romanya': 'Romania',
  'Bulgaristan': 'Bulgaria', 'Sırbistan': 'Serbia', 'Hırvatistan': 'Croatia',
  'Slovenya': 'Slovenia', 'ABD': 'USA', 'Kanada': 'Canada',
  'Meksika': 'Mexico', 'Brezilya': 'Brazil', 'Arjantin': 'Argentina',
  'Şili': 'Chile', 'Kolombiya': 'Colombia', 'Peru': 'Peru',
  'Japonya': 'Japan', 'Çin': 'China', 'Güney Kore': 'South Korea',
  'Tayland': 'Thailand', 'Vietnam': 'Vietnam', 'Endonezya': 'Indonesia',
  'Malezya': 'Malaysia', 'Singapur': 'Singapore', 'Hindistan': 'India',
  'Nepal': 'Nepal', 'Sri Lanka': 'Sri Lanka', 'İsrail': 'Israel',
  'BAE': 'UAE', 'Suudi Arabistan': 'Saudi Arabia', 'Katar': 'Qatar',
  'Mısır': 'Egypt', 'Fas': 'Morocco', 'Güney Afrika': 'South Africa',
  'Tanzanya': 'Tanzania', 'Kenya': 'Kenya', 'Avustralya': 'Australia',
  'Yeni Zelanda': 'New Zealand', 'Rusya': 'Russia', 'Ukrayna': 'Ukraine',
  'Gürcistan': 'Georgia', 'Azerbaycan': 'Azerbaijan', 'Ermenistan': 'Armenia',
  'Kıbrıs': 'Cyprus', 'İzlanda': 'Iceland', 'Lüksemburg': 'Luxembourg',
  'Malta': 'Malta', 'Monako': 'Monaco', 'Vatikan': 'Vatican',
  'Andorra': 'Andorra', 'Liechtenstein': 'Liechtenstein', 'San Marino': 'San Marino',
  'Küba': 'Cuba', 'Dominik Cumhuriyeti': 'Dominican Republic', 'Jamaika': 'Jamaica',
  'Kosta Rika': 'Costa Rica', 'Panama': 'Panama', 'Guatemala': 'Guatemala',
  'Ekvador': 'Ecuador', 'Bolivya': 'Bolivia', 'Paraguay': 'Paraguay',
  'Uruguay': 'Uruguay', 'Diğer (Serbest Arama)': 'Other (Free Search)',
};

const Map<String, String> _countryLabelsEs = {
  'Türkiye': 'Turquía', 'Almanya': 'Alemania', 'İngiltere': 'Reino Unido',
  'Fransa': 'Francia', 'İtalya': 'Italia', 'İspanya': 'España',
  'Portekiz': 'Portugal', 'Yunanistan': 'Grecia', 'Hollanda': 'Países Bajos',
  'Belçika': 'Bélgica', 'İsviçre': 'Suiza', 'Avusturya': 'Austria',
  'İsveç': 'Suecia', 'Norveç': 'Noruega', 'Danimarka': 'Dinamarca',
  'Finlandiya': 'Finlandia', 'İrlanda': 'Irlanda', 'Polonya': 'Polonia',
  'Çekya': 'Chequia', 'Macaristan': 'Hungría', 'Romanya': 'Rumanía',
  'Bulgaristan': 'Bulgaria', 'Sırbistan': 'Serbia', 'Hırvatistan': 'Croacia',
  'Slovenya': 'Eslovenia', 'ABD': 'EE. UU.', 'Kanada': 'Canadá',
  'Meksika': 'México', 'Brezilya': 'Brasil', 'Arjantin': 'Argentina',
  'Şili': 'Chile', 'Kolombiya': 'Colombia', 'Peru': 'Perú',
  'Japonya': 'Japón', 'Çin': 'China', 'Güney Kore': 'Corea del Sur',
  'Tayland': 'Tailandia', 'Vietnam': 'Vietnam', 'Endonezya': 'Indonesia',
  'Malezya': 'Malasia', 'Singapur': 'Singapur', 'Hindistan': 'India',
  'Nepal': 'Nepal', 'Sri Lanka': 'Sri Lanka', 'İsrail': 'Israel',
  'BAE': 'EAU', 'Suudi Arabistan': 'Arabia Saudita', 'Katar': 'Catar',
  'Mısır': 'Egipto', 'Fas': 'Marruecos', 'Güney Afrika': 'Sudáfrica',
  'Tanzanya': 'Tanzania', 'Kenya': 'Kenia', 'Avustralya': 'Australia',
  'Yeni Zelanda': 'Nueva Zelanda', 'Rusya': 'Rusia', 'Ukrayna': 'Ucrania',
  'Gürcistan': 'Georgia', 'Azerbaycan': 'Azerbaiyán', 'Ermenistan': 'Armenia',
  'Kıbrıs': 'Chipre', 'İzlanda': 'Islandia', 'Lüksemburg': 'Luxemburgo',
  'Malta': 'Malta', 'Monako': 'Mónaco', 'Vatikan': 'Vaticano',
  'Andorra': 'Andorra', 'Liechtenstein': 'Liechtenstein', 'San Marino': 'San Marino',
  'Küba': 'Cuba', 'Dominik Cumhuriyeti': 'República Dominicana', 'Jamaika': 'Jamaica',
  'Kosta Rika': 'Costa Rica', 'Panama': 'Panamá', 'Guatemala': 'Guatemala',
  'Ekvador': 'Ecuador', 'Bolivya': 'Bolivia', 'Paraguay': 'Paraguay',
  'Uruguay': 'Uruguay', 'Diğer (Serbest Arama)': 'Otro (Búsqueda Libre)',
};

/// Dile göre ülke görüntü etiketleri döndürür.
/// TR için boş harita döner (adlar zaten Türkçe).
Map<String, String> countryLabels(String langCode) {
  switch (langCode) {
    case 'en':
      return _countryLabelsEn;
    case 'es':
      return _countryLabelsEs;
    default:
      return const {};
  }
}
