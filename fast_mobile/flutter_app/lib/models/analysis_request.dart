class AnalysisRequest {
  final String p1Isim;
  final String p1Tarih;
  final String p1Saat;
  final String p2Isim;
  final String p2Tarih;
  final String p2Saat;
  final String eventTarih;
  final String eventSaat;
  final String ebeveynRolu;
  final String city;
  final String country;
  final double lat;
  final double lon;
  final double? utcOffset;
  final String mod;
  final String lang;

  AnalysisRequest({
    this.p1Isim = '',
    required this.p1Tarih,
    this.p1Saat = '12:00',
    this.p2Isim = '',
    this.p2Tarih = '',
    this.p2Saat = '12:00',
    this.eventTarih = '',
    this.eventSaat = '12:00',
    this.ebeveynRolu = 'anne',
    this.city = 'Istanbul',
    this.country = 'Turkey',
    required this.lat,
    required this.lon,
    this.utcOffset,
    this.mod = 'es_sevgili',
    this.lang = 'tr',
  });

  Map<String, dynamic> toJson() {
    final base = <String, dynamic>{
      'sehir': city, 'ulke': country, 'enlem': lat, 'boylam': lon,
      'lang': lang,
    };
    if (utcOffset != null) base['utc_offset'] = utcOffset;
    switch (mod) {
      case 'bireysel_natal':
        base.addAll({'isim': p1Isim, 'tarih': p1Tarih, 'saat': p1Saat});
        break;
      case 'potansiyel_yetenek':
        base.addAll({'isim': p1Isim, 'tarih': p1Tarih, 'saat': p1Saat});
        break;
      case 'es_sevgili':
        base.addAll({
          'p1_isim': p1Isim, 'p1_tarih': p1Tarih,
          'p2_isim': p2Isim, 'p2_tarih': p2Tarih,
          'event_tarih': eventTarih, 'event_saat': eventSaat,
        });
        break;
      case 'ebeveyn_cocuk':
        base.addAll({
          'ebeveyn_isim': p1Isim, 'ebeveyn_tarih': p1Tarih,
          'ebeveyn_rolu': ebeveynRolu,
          'cocuk_isim': p2Isim, 'cocuk_tarih': p2Tarih,
          'cocuk_saat': p2Saat,
        });
        break;
    }
    return base;
  }

  String get modLabel {
    switch (mod) {
      case 'es_sevgili': return 'Eş / Sevgili';
      case 'ebeveyn_cocuk': return 'Ebeveyn – Çocuk';
      case 'potansiyel_yetenek': return 'Potansiyel / Yetenek';
      case 'bireysel_natal': return 'Bireysel Natal';
      default: return mod;
    }
  }
}
