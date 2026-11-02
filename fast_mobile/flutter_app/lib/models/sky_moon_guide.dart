DateTime _moonGuideEpoch(Object? value) =>
    DateTime.fromMillisecondsSinceEpoch(((value as num?)?.toInt() ?? 0) * 1000);

class SkyMansionTransition {
  final DateTime time;
  final int number;

  const SkyMansionTransition({required this.time, required this.number});

  factory SkyMansionTransition.fromJson(Map<String, dynamic> json) =>
      SkyMansionTransition(
        time: _moonGuideEpoch(json['zaman']),
        number: (json['menzil'] as num?)?.toInt() ?? 1,
      );
}

class SkyMansion {
  final int number;
  final DateTime? enteredAt;
  final DateTime? leavesAt;
  final double degree;
  final double progress;

  const SkyMansion({
    required this.number,
    required this.enteredAt,
    required this.leavesAt,
    required this.degree,
    required this.progress,
  });

  factory SkyMansion.fromJson(Map<String, dynamic> json) => SkyMansion(
    number: (json['sira'] as num?)?.toInt() ?? 1,
    enteredAt: json['baslangic'] == null
        ? null
        : _moonGuideEpoch(json['baslangic']),
    leavesAt: json['bitis'] == null ? null : _moonGuideEpoch(json['bitis']),
    degree: (json['derece'] as num?)?.toDouble() ?? 0,
    progress: (json['ilerleme'] as num?)?.toDouble() ?? 0,
  );
}

class SkyMoonPhaseGuide {
  final String phase;
  final double illumination;
  final bool waxing;
  final DateTime? startedAt;
  final DateTime? endsAt;

  const SkyMoonPhaseGuide({
    required this.phase,
    required this.illumination,
    required this.waxing,
    required this.startedAt,
    required this.endsAt,
  });

  factory SkyMoonPhaseGuide.fromJson(Map<String, dynamic> json) =>
      SkyMoonPhaseGuide(
        phase: json['faz'] as String? ?? 'new',
        illumination: (json['aydinlanma'] as num?)?.toDouble() ?? 0,
        waxing: json['buyuyor'] == true,
        startedAt: json['baslangic'] == null
            ? null
            : _moonGuideEpoch(json['baslangic']),
        endsAt: json['bitis'] == null ? null : _moonGuideEpoch(json['bitis']),
      );
}

class SkyMoonGuide {
  final DateTime fetchedAt;
  final int days;
  final SkyMansion mansion;
  final SkyMoonPhaseGuide phase;
  final List<SkyMansionTransition> transitions;

  const SkyMoonGuide({
    required this.fetchedAt,
    required this.days,
    required this.mansion,
    required this.phase,
    required this.transitions,
  });

  factory SkyMoonGuide.fromJson(Map<String, dynamic> json) => SkyMoonGuide(
    fetchedAt: _moonGuideEpoch(json['sunucu_zamani']),
    days: (json['gun'] as num?)?.toInt() ?? 30,
    mansion: SkyMansion.fromJson(
      (json['menzil'] as Map?)?.cast<String, dynamic>() ?? const {},
    ),
    phase: SkyMoonPhaseGuide.fromJson(
      (json['faz'] as Map?)?.cast<String, dynamic>() ?? const {},
    ),
    transitions: ((json['menzil_gecisleri'] as List?) ?? const [])
        .whereType<Map>()
        .map(
          (item) => SkyMansionTransition.fromJson(item.cast<String, dynamic>()),
        )
        .toList(),
  );
}
