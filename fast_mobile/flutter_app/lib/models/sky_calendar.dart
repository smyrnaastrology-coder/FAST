class SkyBody {
  final double longitude;
  final int sign;
  final double degree;

  const SkyBody({
    required this.longitude,
    required this.sign,
    required this.degree,
  });

  factory SkyBody.fromJson(Map<String, dynamic> j) => SkyBody(
    longitude: (j['mutlak'] as num?)?.toDouble() ?? 0,
    sign: (j['burc'] as num?)?.toInt() ?? 0,
    degree: (j['derece'] as num?)?.toDouble() ?? 0,
  );
}

class SkyPhaseEvent {
  final String type;
  final DateTime time;
  final SkyBody moon;
  final SkyBody sun;

  const SkyPhaseEvent({
    required this.type,
    required this.time,
    required this.moon,
    required this.sun,
  });

  bool get isNewMoon => type == 'new_moon';

  factory SkyPhaseEvent.fromJson(Map<String, dynamic> j) => SkyPhaseEvent(
    type: j['tip'] as String? ?? 'new_moon',
    time: DateTime.fromMillisecondsSinceEpoch(
      ((j['zaman'] as num?)?.toInt() ?? 0) * 1000,
    ),
    moon: SkyBody.fromJson(
      (j['ay'] as Map?)?.cast<String, dynamic>() ?? const {},
    ),
    sun: SkyBody.fromJson(
      (j['gunes'] as Map?)?.cast<String, dynamic>() ?? const {},
    ),
  );
}

class SkyVisibleEclipse {
  final DateTime time;
  final String type;
  final String variant;
  final double? obscuration;
  final double? magnitude;
  final DateTime? localStart;
  final DateTime? localMaximum;
  final DateTime? localEnd;
  final int? saros;
  final int? sarosMember;

  const SkyVisibleEclipse({
    required this.time,
    required this.type,
    required this.variant,
    required this.obscuration,
    required this.magnitude,
    required this.localStart,
    required this.localMaximum,
    required this.localEnd,
    required this.saros,
    required this.sarosMember,
  });

  factory SkyVisibleEclipse.fromJson(Map<String, dynamic> j) =>
      SkyVisibleEclipse(
        time: DateTime.fromMillisecondsSinceEpoch(
          ((j['zaman'] as num?)?.toInt() ?? 0) * 1000,
        ),
        type: j['tip'] as String? ?? 'solar',
        variant: j['alt_tip'] as String? ?? 'partial',
        obscuration: (j['ortulme'] as num?)?.toDouble(),
        magnitude: (j['buyukluk'] as num?)?.toDouble(),
        localStart: j['yerel_baslangic'] == null
            ? null
            : DateTime.fromMillisecondsSinceEpoch(
                (j['yerel_baslangic'] as num).toInt() * 1000,
              ),
        localMaximum: j['yerel_maksimum'] == null
            ? null
            : DateTime.fromMillisecondsSinceEpoch(
                (j['yerel_maksimum'] as num).toInt() * 1000,
              ),
        localEnd: j['yerel_bitis'] == null
            ? null
            : DateTime.fromMillisecondsSinceEpoch(
                (j['yerel_bitis'] as num).toInt() * 1000,
              ),
        saros: (j['saros'] as num?)?.toInt(),
        sarosMember: (j['saros_uyesi'] as num?)?.toInt(),
      );
}

class SkyVisibility {
  final bool visible;
  final String? localVariant;
  final double? obscuration;
  final double? magnitude;
  final SkyVisibleEclipse? nextVisible;
  final DateTime? localStart;
  final DateTime? localMaximum;
  final DateTime? localEnd;
  final int? saros;
  final int? sarosMember;

  const SkyVisibility({
    required this.visible,
    required this.localVariant,
    required this.obscuration,
    required this.magnitude,
    required this.nextVisible,
    required this.localStart,
    required this.localMaximum,
    required this.localEnd,
    required this.saros,
    required this.sarosMember,
  });

  factory SkyVisibility.fromJson(Map<String, dynamic> j) {
    final next = (j['sonraki_gorunur'] as Map?)?.cast<String, dynamic>();
    return SkyVisibility(
      visible: j['gorunur'] == true,
      localVariant: j['yerel_tip'] as String?,
      obscuration: (j['ortulme'] as num?)?.toDouble(),
      magnitude: (j['buyukluk'] as num?)?.toDouble(),
      nextVisible: next == null ? null : SkyVisibleEclipse.fromJson(next),
      localStart: j['yerel_baslangic'] == null
          ? null
          : DateTime.fromMillisecondsSinceEpoch(
              (j['yerel_baslangic'] as num).toInt() * 1000,
            ),
      localMaximum: j['yerel_maksimum'] == null
          ? null
          : DateTime.fromMillisecondsSinceEpoch(
              (j['yerel_maksimum'] as num).toInt() * 1000,
            ),
      localEnd: j['yerel_bitis'] == null
          ? null
          : DateTime.fromMillisecondsSinceEpoch(
              (j['yerel_bitis'] as num).toInt() * 1000,
            ),
      saros: (j['saros'] as num?)?.toInt(),
      sarosMember: (j['saros_uyesi'] as num?)?.toInt(),
    );
  }
}

class SkyEclipse {
  final String type;
  final String variant;
  final DateTime time;
  final SkyBody moon;
  final SkyBody sun;
  final SkyVisibility visibility;

  const SkyEclipse({
    required this.type,
    required this.variant,
    required this.time,
    required this.moon,
    required this.sun,
    required this.visibility,
  });

  bool get isSolar => type == 'solar';

  factory SkyEclipse.fromJson(Map<String, dynamic> j) => SkyEclipse(
    type: j['tip'] as String? ?? 'solar',
    variant: j['alt_tip'] as String? ?? 'partial',
    time: DateTime.fromMillisecondsSinceEpoch(
      ((j['zaman'] as num?)?.toInt() ?? 0) * 1000,
    ),
    moon: SkyBody.fromJson(
      (j['ay'] as Map?)?.cast<String, dynamic>() ?? const {},
    ),
    sun: SkyBody.fromJson(
      (j['gunes'] as Map?)?.cast<String, dynamic>() ?? const {},
    ),
    visibility: SkyVisibility.fromJson(
      (j['gorunurluk'] as Map?)?.cast<String, dynamic>() ?? const {},
    ),
  );
}

class SkyCalendar {
  final List<SkyPhaseEvent> phases;
  final List<SkyEclipse> eclipses;

  const SkyCalendar({required this.phases, required this.eclipses});

  factory SkyCalendar.fromJson(Map<String, dynamic> j) => SkyCalendar(
    phases: ((j['fazlar'] as List?) ?? const [])
        .whereType<Map>()
        .map((e) => SkyPhaseEvent.fromJson(e.cast<String, dynamic>()))
        .toList(),
    eclipses: ((j['tutulmalar'] as List?) ?? const [])
        .whereType<Map>()
        .map((e) => SkyEclipse.fromJson(e.cast<String, dynamic>()))
        .toList(),
  );
}

/// Ay'ın bir burca giriş anı.
class SkyMoonIngress {
  final DateTime time;

  /// 0 = Koç (mutlak ekliptik).
  final int sign;
  final double degree;

  const SkyMoonIngress({
    required this.time,
    required this.sign,
    required this.degree,
  });

  factory SkyMoonIngress.fromJson(Map<String, dynamic> j) => SkyMoonIngress(
    time: _epochToDate(j['zaman']),
    sign: (j['burc'] as num?)?.toInt() ?? 0,
    degree: (j['derece'] as num?)?.toDouble() ?? 0,
  );
}

/// Ay takvimi: şu anki burç penceresi ve yaklaşan geçişler.
class SkyMoonCalendar {
  final DateTime fetchedAt;
  final int sign;
  final double degree;
  final DateTime? ingress;
  final DateTime? egress;
  final List<SkyMoonIngress> ingresses;

  const SkyMoonCalendar({
    required this.fetchedAt,
    required this.sign,
    required this.degree,
    required this.ingress,
    required this.egress,
    required this.ingresses,
  });

  factory SkyMoonCalendar.fromJson(Map<String, dynamic> j) {
    final moon = (j['ay'] as Map?)?.cast<String, dynamic>() ?? const {};
    return SkyMoonCalendar(
      fetchedAt: _epochToDate(j['sunucu_zamani']),
      sign: (moon['burc'] as num?)?.toInt() ?? 0,
      degree: (moon['derece'] as num?)?.toDouble() ?? 0,
      ingress: moon['giris'] == null ? null : _epochToDate(moon['giris']),
      egress: moon['cikis'] == null ? null : _epochToDate(moon['cikis']),
      ingresses: ((j['girisler'] as List?) ?? const [])
          .whereType<Map>()
          .map((e) => SkyMoonIngress.fromJson(e.cast<String, dynamic>()))
          .toList(),
    );
  }
}

DateTime _epochToDate(Object? value) =>
    DateTime.fromMillisecondsSinceEpoch(((value as num?)?.toInt() ?? 0) * 1000);
