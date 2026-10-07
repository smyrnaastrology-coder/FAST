import '../l10n/app_localizations.dart';

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

  /// İlişki Skorları (Ashtakoot) modu için doğum ŞEHRİ. Kullanıcı UTC ofsetini
  /// bilmez ve bilmesi de gerekmez; sunucu şehir + doğum tarihinden ofseti
  /// hesaplar. Ofset sabit değildir (Türkiye'de 2016 öncesi kışın +2, yazın +3),
  /// bu yüzden tarih bilgisi zorunludur.
  final String p1Sehir;
  final String p2Sehir;

  /// Şehir otomatik çözülemezse kullanıcının elle verebileceği UTC ofseti.
  /// null ise sunucu şehirden hesaplar.
  final double? p1UtcOffset;
  final double? p2UtcOffset;

  AnalysisRequest({
    this.p1Isim = '',
    required this.p1Tarih,
    this.p1Saat = '',
    this.p2Isim = '',
    this.p2Tarih = '',
    this.p2Saat = '',
    this.eventTarih = '',
    this.eventSaat = '12:00',
    this.ebeveynRolu = 'anne',
    this.city = 'Istanbul',
    this.country = 'Turkey',
    required this.lat,
    required this.lon,
    this.utcOffset,
    this.p1Sehir = '',
    this.p2Sehir = '',
    this.p1UtcOffset,
    this.p2UtcOffset,
    this.mod = 'es_sevgili',
    this.lang = 'tr',
  });

  Map<String, dynamic> toJson() {
    // Saat alanı bilerek boş bırakılabilir. Ashtakoot dışındaki modlar saatin
    // dolu olmasını bekler (natal haritası saat hassasiyetlidir), dolayısıyla
    // orada öğleye düşüyoruz. Ashtakoot'ta boş saat SUNUCUDA öğleye düşer ve
    // sonuç "yaklaşık" işaretlenir — bu yüzden burada varsayılan uygulanmaz.
    String saat(String v) => v.trim().isEmpty ? '12:00' : v.trim();

    final base = <String, dynamic>{
      'sehir': city, 'ulke': country, 'enlem': lat, 'boylam': lon,
      'lang': lang,
    };
    if (utcOffset != null) base['utc_offset'] = utcOffset;
    switch (mod) {
      case 'bireysel_natal':
        base.addAll({'isim': p1Isim, 'tarih': p1Tarih, 'saat': saat(p1Saat)});
        break;
      case 'potansiyel_yetenek':
        base.addAll({'isim': p1Isim, 'tarih': p1Tarih, 'saat': saat(p1Saat)});
        break;
      case 'es_sevgili':
        base.addAll({
          'p1_isim': p1Isim, 'p1_tarih': p1Tarih, 'p1_saat': saat(p1Saat),
          'p2_isim': p2Isim, 'p2_tarih': p2Tarih, 'p2_saat': saat(p2Saat),
          'event_tarih': eventTarih, 'event_saat': eventSaat,
        });
        break;
      case 'ebeveyn_cocuk':
        base.addAll({
          'ebeveyn_isim': p1Isim, 'ebeveyn_tarih': p1Tarih,
          'ebeveyn_rolu': ebeveynRolu,
          'cocuk_isim': p2Isim, 'cocuk_tarih': p2Tarih,
          'cocuk_saat': saat(p2Saat),
        });
        break;
      case 'ashtakoot':
        // Ay konumu yalnızca doğum ANINA bağlıdır; doğum yerinin koordinatı
        // hesaba girmez. Ancak UTC ofseti yer + TARİHE bağlı olduğu için şehir
        // gönderilir ve sunucu ofseti kendisi çözer (tarihsel DST dahil).
        // Açıklama metinleri sunucuda `dil`e göre üretilir.
        base.remove('sehir');
        base.remove('ulke');
        base.remove('enlem');
        base.remove('boylam');
        base.addAll({
          'p1_isim': p1Isim, 'p1_tarih': p1Tarih,
          'p1_saat': p1Saat, 'p1_sehir': p1Sehir,
          'p2_isim': p2Isim, 'p2_tarih': p2Tarih,
          'p2_saat': p2Saat, 'p2_sehir': p2Sehir,
          'dil': lang,
        });
        // Elle ofset verilmişse gönder; verilmemişse sunucu şehirden hesaplar.
        if (p1UtcOffset != null) base['p1_utc_offset'] = p1UtcOffset;
        if (p2UtcOffset != null) base['p2_utc_offset'] = p2UtcOffset;
        break;
    }
    return base;
  }

  String modLabel(AppLocalizations l10n) {
    switch (mod) {
      case 'es_sevgili': return l10n.modeEsTitle;
      case 'ebeveyn_cocuk': return l10n.modeEbTitle;
      case 'potansiyel_yetenek': return l10n.modePyTitle;
      case 'bireysel_natal': return l10n.modeNatalTitle;
      case 'ashtakoot': return l10n.modeAshTitle;
      default: return mod;
    }
  }

  /// PDF artık uzun bir kitap: moda göre kitap adı (İlişki / Ebeveyn / El Kitabı).
  String bookLabel(AppLocalizations l10n) {
    switch (mod) {
      case 'es_sevgili': return l10n.bookIliski;
      case 'ebeveyn_cocuk': return l10n.bookEbeveyn;
      default: return l10n.bookEl;
    }
  }
}
