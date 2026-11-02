import 'chart_data.dart';
import 'sky_calendar.dart';

class EclipseNatalAspect {
  final String planet;
  final String type;
  final double orb;

  const EclipseNatalAspect({
    required this.planet,
    required this.type,
    required this.orb,
  });
}

class EclipsePersonalImpact {
  final int? house;
  final List<EclipseNatalAspect> aspects;

  const EclipsePersonalImpact({required this.house, required this.aspects});

  factory EclipsePersonalImpact.calculate(SkyEclipse eclipse, ChartData natal) {
    final longitude = eclipse.isSolar
        ? eclipse.sun.longitude
        : eclipse.moon.longitude;
    return EclipsePersonalImpact(
      house: _houseFor(longitude, natal.houses),
      aspects: _nearestAspects(longitude, natal.planets),
    );
  }

  static int? _houseFor(double longitude, List<HouseCusp> houses) {
    if (houses.length < 12) return null;
    final cusps = [...houses]..sort((a, b) => a.number.compareTo(b.number));
    for (var i = 0; i < cusps.length; i++) {
      final start = cusps[i].lon % 360;
      final end = cusps[(i + 1) % cusps.length].lon % 360;
      final width = (end - start + 360) % 360;
      final offset = (longitude - start + 360) % 360;
      if (width > 0 && offset < width) return cusps[i].number;
    }
    return null;
  }

  static List<EclipseNatalAspect> _nearestAspects(
    double longitude,
    List<PlanetPos> planets,
  ) {
    const angles = <(String, double)>[
      ('conjunction', 0),
      ('sextile', 60),
      ('square', 90),
      ('trine', 120),
      ('opposition', 180),
    ];
    final out = <EclipseNatalAspect>[];
    for (final planet in planets) {
      final raw = (longitude - planet.lon).abs() % 360;
      final separation = raw > 180 ? 360 - raw : raw;
      EclipseNatalAspect? closest;
      for (final (type, angle) in angles) {
        final orb = (separation - angle).abs();
        if (orb <= 3.0 && (closest == null || orb < closest.orb)) {
          closest = EclipseNatalAspect(
            planet: planet.name,
            type: type,
            orb: orb,
          );
        }
      }
      if (closest != null) out.add(closest);
    }
    out.sort((a, b) => a.orb.compareTo(b.orb));
    return out.take(3).toList();
  }
}
