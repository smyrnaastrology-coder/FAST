/// Ay'ın "boşta" (void of course) olduğu aralık.
class SkyMoonVoidWindow {
  final DateTime start;
  final DateTime end;

  /// Aralığın bittiği burç (0 = Koç).
  final int sign;

  const SkyMoonVoidWindow({
    required this.start,
    required this.end,
    required this.sign,
  });

  factory SkyMoonVoidWindow.fromJson(Map<String, dynamic> j) =>
      SkyMoonVoidWindow(
        start: _epochToDate(j['baslangic']),
        end: _epochToDate(j['bitis']),
        sign: (j['burc'] as num?)?.toInt() ?? 0,
      );
}

/// Bir eylem için uygun zaman aralığı.
class SkyMoonActivityWindow {
  final DateTime start;
  final DateTime end;

  /// Aralığın burcu (0 = Koç).
  final int sign;

  /// Büyüyen Ay mı?
  final bool waxing;

  const SkyMoonActivityWindow({
    required this.start,
    required this.end,
    required this.sign,
    required this.waxing,
  });

  factory SkyMoonActivityWindow.fromJson(Map<String, dynamic> j) =>
      SkyMoonActivityWindow(
        start: _epochToDate(j['baslangic']),
        end: _epochToDate(j['bitis']),
        sign: (j['burc'] as num?)?.toInt() ?? 0,
        waxing: j['evre'] == 'waxing',
      );
}

/// Ay boşta dönemleri ve eylemlere göre doğru zaman pencereleri.
class SkyMoonTiming {
  final DateTime fetchedAt;
  final int sign;
  final double degree;
  final bool voidNow;
  final DateTime? voidStart;
  final DateTime? voidEnd;
  final List<SkyMoonVoidWindow> voids;
  final Map<String, List<SkyMoonActivityWindow>> activities;

  const SkyMoonTiming({
    required this.fetchedAt,
    required this.sign,
    required this.degree,
    required this.voidNow,
    required this.voidStart,
    required this.voidEnd,
    required this.voids,
    required this.activities,
  });

  factory SkyMoonTiming.fromJson(Map<String, dynamic> j) {
    final moon = (j['ay'] as Map?)?.cast<String, dynamic>() ?? const {};
    final pencereler = (j['pencereler'] as Map?)?.cast<String, dynamic>() ?? {};
    return SkyMoonTiming(
      fetchedAt: _epochToDate(j['sunucu_zamani']),
      sign: (moon['burc'] as num?)?.toInt() ?? 0,
      degree: (moon['derece'] as num?)?.toDouble() ?? 0,
      voidNow: moon['bos'] == true,
      voidStart: moon['bos_baslangic'] == null
          ? null
          : _epochToDate(moon['bos_baslangic']),
      voidEnd: moon['bos_bitis'] == null
          ? null
          : _epochToDate(moon['bos_bitis']),
      voids: ((j['bosluklar'] as List?) ?? const [])
          .whereType<Map>()
          .map((e) => SkyMoonVoidWindow.fromJson(e.cast<String, dynamic>()))
          .toList(),
      activities: {
        for (final entry in pencereler.entries)
          entry.key: ((entry.value as List?) ?? const [])
              .whereType<Map>()
              .map(
                (e) => SkyMoonActivityWindow.fromJson(
                  e.cast<String, dynamic>(),
                ),
              )
              .toList(),
      },
    );
  }
}

DateTime _epochToDate(Object? value) => DateTime.fromMillisecondsSinceEpoch(
  ((value as num?)?.toInt() ?? 0) * 1000,
);
