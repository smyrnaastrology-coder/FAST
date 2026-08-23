class GezegenKonum {
  final String ad;
  final double derece;
  final int burcIndex;
  final double burcDerece;
  final bool retro;
  final double ev;

  GezegenKonum({
    required this.ad, required this.derece, required this.burcIndex,
    required this.burcDerece, this.retro = false, this.ev = 1,
  });

  factory GezegenKonum.fromJson(Map<String, dynamic> json) {
    return GezegenKonum(
      ad: json['ad'] ?? json['isim'] ?? '',
      derece: (json['derece'] ?? json['derece_absolute'] ?? 0).toDouble(),
      burcIndex: _burcIndex(json['burc'] ?? ''),
      burcDerece: (json['burc_derece'] ?? json['derece_burc'] ?? 0).toDouble(),
      retro: json['retro'] == true || json['retro'] == 1,
      ev: (json['ev'] ?? 1).toDouble(),
    );
  }

  static int _burcIndex(String burc) {
    const burclar = ['Ko\u00e7','Bo\u011fa','\u0130kizler','Yenge\u00e7','Aslan','Ba\u015fak',
      'Terazi','Akrep','Yay','O\u011flak','Kova','Bal\u0131k'];
    return burclar.indexOf(burc);
  }
}

class AciBilgisi {
  final String gezegen1;
  final String gezegen2;
  final String aciTuru;
  final double fark;
  final String durum;

  AciBilgisi({
    required this.gezegen1, required this.gezegen2,
    required this.aciTuru, required this.fark, this.durum = '',
  });

  factory AciBilgisi.fromJson(Map<String, dynamic> json) {
    return AciBilgisi(
      gezegen1: json['gezegen1'] ?? json['p1'] ?? '',
      gezegen2: json['gezegen2'] ?? json['p2'] ?? '',
      aciTuru: json['aci_turu'] ?? json['aspect'] ?? '',
      fark: (json['fark'] ?? json['orb'] ?? 0).toDouble(),
      durum: json['durum'] ?? '',
    );
  }
}

class AstrolojiHarita {
  final List<GezegenKonum> gezegenler;
  final List<double> evKuspidleri;
  final List<AciBilgisi> acilar;
  final double yukselen;
  final double mc;

  AstrolojiHarita({
    required this.gezegenler, this.evKuspidleri = const [],
    this.acilar = const [], this.yukselen = 0, this.mc = 0,
  });

  factory AstrolojiHarita.fromJson(Map<String, dynamic> json) {
    final gezList = <GezegenKonum>[];
    if (json['gezegenler'] != null) {
      for (final g in json['gezegenler'] as List) {
        gezList.add(GezegenKonum.fromJson(g as Map<String, dynamic>));
      }
    }
    final aciList = <AciBilgisi>[];
    if (json['acilar'] != null) {
      for (final a in json['acilar'] as List) {
        aciList.add(AciBilgisi.fromJson(a as Map<String, dynamic>));
      }
    }
    return AstrolojiHarita(
      gezegenler: gezList,
      evKuspidleri: (json['ev_kuspidleri'] as List?)?.map((e) => (e as num).toDouble()).toList() ?? [],
      acilar: aciList,
      yukselen: (json['yukselen'] ?? json['asc'] ?? 0).toDouble(),
      mc: (json['mc'] ?? 0).toDouble(),
    );
  }
}
