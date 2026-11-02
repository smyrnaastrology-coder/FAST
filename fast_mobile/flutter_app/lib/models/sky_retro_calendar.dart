DateTime _retroEpoch(Object? value) =>
    DateTime.fromMillisecondsSinceEpoch(((value as num?)?.toInt() ?? 0) * 1000);

class SkyRetroPeriod {
  final String planet;
  final DateTime? shadowStart;
  final DateTime retroStart;
  final DateTime directStation;
  final DateTime? shadowEnd;
  final int sign;
  final double degree;
  final bool active;
  final bool inShadow;

  const SkyRetroPeriod({
    required this.planet,
    required this.shadowStart,
    required this.retroStart,
    required this.directStation,
    required this.shadowEnd,
    required this.sign,
    required this.degree,
    required this.active,
    required this.inShadow,
  });

  factory SkyRetroPeriod.fromJson(Map<String, dynamic> json) => SkyRetroPeriod(
    planet: json['gezegen'] as String? ?? '',
    shadowStart: json['golge_baslangic'] == null
        ? null
        : _retroEpoch(json['golge_baslangic']),
    retroStart: _retroEpoch(json['retro_baslangic']),
    directStation: _retroEpoch(json['direkt_durak']),
    shadowEnd: json['golge_bitis'] == null
        ? null
        : _retroEpoch(json['golge_bitis']),
    sign: (json['retro_burcu'] as num?)?.toInt() ?? 0,
    degree: (json['retro_derece'] as num?)?.toDouble() ?? 0,
    active: json['aktif'] == true,
    inShadow: json['golgede'] == true,
  );
}

class SkyRetroCalendar {
  final DateTime fetchedAt;
  final int days;
  final List<SkyRetroPeriod> periods;

  const SkyRetroCalendar({
    required this.fetchedAt,
    required this.days,
    required this.periods,
  });

  factory SkyRetroCalendar.fromJson(Map<String, dynamic> json) =>
      SkyRetroCalendar(
        fetchedAt: _retroEpoch(json['sunucu_zamani']),
        days: (json['gun'] as num?)?.toInt() ?? 365,
        periods: ((json['donemler'] as List?) ?? const [])
            .whereType<Map>()
            .map(
              (entry) => SkyRetroPeriod.fromJson(entry.cast<String, dynamic>()),
            )
            .toList(),
      );
}
