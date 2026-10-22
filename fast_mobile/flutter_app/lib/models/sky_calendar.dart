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

  const SkyVisibleEclipse({
    required this.time,
    required this.type,
    required this.variant,
    required this.obscuration,
    required this.magnitude,
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
      );
}

class SkyVisibility {
  final bool visible;
  final String? localVariant;
  final double? obscuration;
  final double? magnitude;
  final SkyVisibleEclipse? nextVisible;

  const SkyVisibility({
    required this.visible,
    required this.localVariant,
    required this.obscuration,
    required this.magnitude,
    required this.nextVisible,
  });

  factory SkyVisibility.fromJson(Map<String, dynamic> j) {
    final next = (j['sonraki_gorunur'] as Map?)?.cast<String, dynamic>();
    return SkyVisibility(
      visible: j['gorunur'] == true,
      localVariant: j['yerel_tip'] as String?,
      obscuration: (j['ortulme'] as num?)?.toDouble(),
      magnitude: (j['buyukluk'] as num?)?.toDouble(),
      nextVisible: next == null ? null : SkyVisibleEclipse.fromJson(next),
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
