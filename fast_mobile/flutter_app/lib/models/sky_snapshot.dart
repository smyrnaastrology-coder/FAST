class SkyAspect {
  final String planet;
  final String type;
  final double orb;
  final bool applying;

  const SkyAspect({
    required this.planet,
    required this.type,
    required this.orb,
    required this.applying,
  });

  factory SkyAspect.fromJson(Map<String, dynamic> j) => SkyAspect(
    planet: j['gezegen'] as String? ?? '',
    type: j['tip'] as String? ?? '',
    orb: (j['orb'] as num?)?.toDouble() ?? 0,
    applying: j['uygulama'] == true,
  );
}

class SkySnapshot {
  final int moonSign;
  final double moonDegree;
  final double moonLongitude;
  final double moonSpeed;
  final String speedKey;
  final String phaseKey;
  final double illumination;
  final bool waxing;
  final bool voidOfCourse;
  final bool isCombust;
  final int lunarMansionIndex;
  final DateTime? voidUntil;
  final int sunSign;
  final double sunDegree;
  final String hourRuler;
  final String nextHourRuler;
  final int hourIndex;
  final bool dayHour;
  final DateTime hourStart;
  final DateTime hourEnd;
  final List<SkyAspect> aspects;
  final List<String> retrogrades;
  final DateTime fetchedAt;

  const SkySnapshot({
    required this.moonSign,
    required this.moonDegree,
    required this.moonLongitude,
    required this.moonSpeed,
    required this.speedKey,
    required this.phaseKey,
    required this.illumination,
    required this.waxing,
    required this.voidOfCourse,
    required this.isCombust,
    required this.lunarMansionIndex,
    required this.voidUntil,
    required this.sunSign,
    required this.sunDegree,
    required this.hourRuler,
    required this.nextHourRuler,
    required this.hourIndex,
    required this.dayHour,
    required this.hourStart,
    required this.hourEnd,
    required this.aspects,
    required this.retrogrades,
    required this.fetchedAt,
  });

  factory SkySnapshot.fromJson(Map<String, dynamic> j) {
    final moon = (j['ay'] as Map?)?.cast<String, dynamic>() ?? const {};
    final sun = (j['gunes'] as Map?)?.cast<String, dynamic>() ?? const {};
    final phase = (j['faz'] as Map?)?.cast<String, dynamic>() ?? const {};
    final hour =
        (j['gezegen_saati'] as Map?)?.cast<String, dynamic>() ?? const {};
    return SkySnapshot(
      moonSign: (moon['burc'] as num?)?.toInt() ?? 0,
      moonDegree: (moon['derece'] as num?)?.toDouble() ?? 0,
      moonLongitude: (moon['mutlak'] as num?)?.toDouble() ?? 0,
      moonSpeed: (moon['hiz'] as num?)?.toDouble() ?? 0,
      speedKey: moon['hiz_durumu'] as String? ?? 'normal',
      phaseKey: phase['isim'] as String? ?? 'new',
      illumination: (phase['aydinlanma'] as num?)?.toDouble() ?? 0,
      waxing: phase['buyuyor'] == true,
      voidOfCourse: j['boslukta'] == true,
      isCombust: _isCombust(
        (moon['mutlak'] as num?)?.toDouble() ?? 0,
        ((sun['burc'] as num?)?.toInt() ?? 0) * 30.0 +
            ((sun['derece'] as num?)?.toDouble() ?? 0),
      ),
      lunarMansionIndex: (((moon['mutlak'] as num?)?.toDouble() ?? 0) % 360) ~/
          (360 / 28),
      voidUntil: _epoch(j['bosluk_biter']),
      sunSign: (sun['burc'] as num?)?.toInt() ?? 0,
      sunDegree: (sun['derece'] as num?)?.toDouble() ?? 0,
      hourRuler: hour['yonetici'] as String? ?? 'sun',
      nextHourRuler: hour['sonraki'] as String? ?? 'venus',
      hourIndex: (hour['index'] as num?)?.toInt() ?? 1,
      dayHour: hour['gunduz'] == true,
      hourStart: _epoch(hour['baslangic']) ?? DateTime.now(),
      hourEnd: _epoch(hour['bitis']) ?? DateTime.now(),
      aspects: ((j['acilar'] as List?) ?? const [])
          .whereType<Map>()
          .map((e) => SkyAspect.fromJson(e.cast<String, dynamic>()))
          .toList(),
      retrogrades: ((j['retrolar'] as List?) ?? const [])
          .whereType<String>()
          .toList(),
      fetchedAt: DateTime.now(),
    );
  }

  static bool _isCombust(double moonLon, double sunLon) {
    var d = (moonLon - sunLon).abs() % 360;
    if (d > 180) d = 360 - d;
    return d <= 8.5;
  }

  static DateTime? _epoch(dynamic v) {
    if (v is! num) return null;
    return DateTime.fromMillisecondsSinceEpoch(v.toInt() * 1000);
  }
}
