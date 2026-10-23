class ChartBody {
  final String? name;
  final String date;
  final String time;
  final double lat;
  final double lng;
  final double? tz;
  final String place;

  const ChartBody({
    this.name,
    required this.date,
    required this.time,
    required this.lat,
    required this.lng,
    this.tz,
    this.place = '',
  });

  Map<String, dynamic> toJson() => {
        if (name != null && name!.isNotEmpty) 'isim': name,
        'tarih': date,
        'saat': time,
        'lat': lat,
        'lon': lng,
        if (tz != null) 'tz': tz,
        if (place.isNotEmpty) 'sehir': place,
      };

  factory ChartBody.fromJson(Map<String, dynamic> j) => ChartBody(
        name: j['isim'] as String?,
        date: j['tarih'] as String? ?? '',
        time: j['saat'] as String? ?? '12:00',
        lat: (j['lat'] as num?)?.toDouble() ?? 41.0082,
        lng: (j['lon'] as num?)?.toDouble() ?? 28.9784,
        tz: (j['tz'] as num?)?.toDouble(),
        place: j['sehir'] as String? ?? '',
      );
}

class PlanetPos {
  final String name;
  final double lon;
  final int sign;
  final double degree;
  final int house;
  final double speed;
  final bool retrograde;

  const PlanetPos({
    required this.name,
    required this.lon,
    required this.sign,
    required this.degree,
    required this.house,
    required this.speed,
    required this.retrograde,
  });

  factory PlanetPos.fromJson(Map<String, dynamic> j) => PlanetPos(
        name: j['ad'] as String? ?? '',
        lon: (j['lon'] as num?)?.toDouble() ?? 0,
        sign: (j['burc'] as num?)?.toInt() ?? 0,
        degree: (j['derece'] as num?)?.toDouble() ?? 0,
        house: (j['ev'] as num?)?.toInt() ?? 1,
        speed: (j['hiz'] as num?)?.toDouble() ?? 0,
        retrograde: j['retro'] == true,
      );
}

class HouseCusp {
  final int number;
  final double lon;
  final int sign;
  final double degree;

  const HouseCusp({
    required this.number,
    required this.lon,
    required this.sign,
    required this.degree,
  });

  factory HouseCusp.fromJson(Map<String, dynamic> j) => HouseCusp(
        number: (j['no'] as num?)?.toInt() ?? 1,
        lon: (j['lon'] as num?)?.toDouble() ?? 0,
        sign: (j['burc'] as num?)?.toInt() ?? 0,
        degree: (j['derece'] as num?)?.toDouble() ?? 0,
      );
}

class ChartAspect {
  final String p1;
  final String p2;
  final String type;
  final double orb;

  const ChartAspect({
    required this.p1,
    required this.p2,
    required this.type,
    required this.orb,
  });

  factory ChartAspect.fromJson(Map<String, dynamic> j) => ChartAspect(
        p1: j['p1'] as String? ?? '',
        p2: j['p2'] as String? ?? '',
        type: j['tip'] as String? ?? '',
        orb: (j['orb'] as num?)?.toDouble() ?? 0,
      );
}

class ChartAngle {
  final double lon;
  final int sign;
  final double degree;

  const ChartAngle({required this.lon, required this.sign, required this.degree});

  factory ChartAngle.fromJson(Map<String, dynamic> j) => ChartAngle(
        lon: (j['lon'] as num?)?.toDouble() ?? 0,
        sign: (j['burc'] as num?)?.toInt() ?? 0,
        degree: (j['derece'] as num?)?.toDouble() ?? 0,
      );
}

class ChartData {
  final String houseSystem;
  final double julianDay;
  final ChartAngle asc;
  final ChartAngle mc;
  final List<PlanetPos> planets;
  final List<HouseCusp> houses;
  final List<ChartAspect> aspects;
  final ChartBody meta;

  const ChartData({
    required this.houseSystem,
    required this.julianDay,
    required this.asc,
    required this.mc,
    required this.planets,
    required this.houses,
    required this.aspects,
    required this.meta,
  });

  factory ChartData.fromJson(Map<String, dynamic> j) => ChartData(
        houseSystem: j['house_system'] as String? ?? 'P',
        julianDay: (j['julian_day_ut'] as num?)?.toDouble() ?? 0,
        asc: ChartAngle.fromJson(
            (j['asc'] as Map?)?.cast<String, dynamic>() ?? const {}),
        mc: ChartAngle.fromJson(
            (j['mc'] as Map?)?.cast<String, dynamic>() ?? const {}),
        planets: ((j['gezegenler'] as List?) ?? const [])
            .whereType<Map>()
            .map((e) => PlanetPos.fromJson(e.cast<String, dynamic>()))
            .toList(),
        houses: ((j['evler'] as List?) ?? const [])
            .whereType<Map>()
            .map((e) => HouseCusp.fromJson(e.cast<String, dynamic>()))
            .toList(),
        aspects: ((j['acilar'] as List?) ?? const [])
            .whereType<Map>()
            .map((e) => ChartAspect.fromJson(e.cast<String, dynamic>()))
            .toList(),
        meta: ChartBody.fromJson(
            (j['meta'] as Map?)?.cast<String, dynamic>() ?? const {}),
      );
}
