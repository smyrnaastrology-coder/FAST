import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/chart_data.dart';
import '../models/chart_labels.dart';
import '../models/chart_frame.dart';
import '../screens/chart_explorer_screen.dart';
import '../l10n/app_localizations.dart';
import 'chart_wheel_geometry.dart';
import 'chart_wheel_style.dart';

/// AstroGold tarzı çok katmanlı natal / bi-wheel çarkı.
///
/// Yükselen (ASC) her zaman sol-orta noktaya (doğu ufku) kilitlenir; burçlar
/// saat yönünün tersine ilerler.
///
/// - Tek harita modunda ([outerPlanets] boş) tek zodyak kuşağı, tek gezegen
///   halkası ve natal açı çizgileri çizilir.
/// - Çift harita (bi-wheel) modunda dış haritanın ayrı bir zodyak kuşağı ve
///   gezegen halkası bulunur; merkezde geniş beyaz bir daire kalır ve iki
///   harita arasındaki transit açıları gösterilir.
///
/// Tüm astronomik veri [ChartData] üzerinden gelir. Bu dosya yalnızca çizim
/// yapar; gezegen boylamı, ev başlangıcı ve açı hesaplamaz. Renkler
/// [ChartWheelStyle] üzerinden değiştirilebilir.
class ChartWheel extends StatelessWidget {
  final ChartData data;
  final double size;
  final List<PlanetPos>? outerPlanets;
  final List<HouseCusp>? outerHouses;

  /// Dış (transit / olay) haritasının tam verisi. Sağ üstteki bilgi paneli ve
  /// dış haritanın eksenleri bu kayıttan üretilir. Verilmezse dış harita
  /// bilgi paneli çizilmez.
  final ChartData? outerData;

  final bool showAspectLines;
  final bool showTransitAspects;
  final bool lightTheme;
  final bool showControls;
  final DateTime? initialDate;
  final ChartFrameLoader? loadFrame;
  final String title;
  final String subtitle;
  final List<ChartTimeUnit> timeUnits;

  /// Renk paletini dışarıdan geçersiz kılmak için. `null` ise [lightTheme]
  /// değerine göre [ChartWheelStyle.of] kullanılır.
  final ChartWheelStyle? style;

  const ChartWheel({
    super.key,
    required this.data,
    this.size = 320,
    this.outerPlanets,
    this.outerHouses,
    this.outerData,
    this.showAspectLines = true,
    this.showTransitAspects = true,
    this.lightTheme = false,
    this.showControls = true,
    this.initialDate,
    this.loadFrame,
    this.title = 'Natal',
    this.subtitle = '',
    this.timeUnits = ChartTimeUnit.values,
    this.style,
  });

  @override
  Widget build(BuildContext context) {
    final palette = style ?? ChartWheelStyle.of(lightTheme);
    // Dar ekranlarda taşmayı önle.
    final maxWidth = MediaQuery.of(context).size.width - 24;
    final extent = size > maxWidth && maxWidth > 100 ? maxWidth : size;
    Widget drawing(double extent) => SizedBox(
      width: extent,
      height: extent,
      child: ColoredBox(
        color: palette.background,
        child: CustomPaint(
          painter: _WheelPainter(
            data: data,
            outerPlanets: outerPlanets,
            outerHouses: outerHouses,
            outerData: outerData,
            showAspectLines: showAspectLines,
            showTransitAspects: showTransitAspects,
            style: palette,
          ),
        ),
      ),
    );
    if (!showControls) return drawing(extent);
    return Stack(
      alignment: Alignment.topRight,
      children: [
        InteractiveViewer(minScale: 1, maxScale: 5, child: drawing(extent)),
        if (showControls)
          IconButton(
            tooltip: AppLocalizations.of(context).chartWheelFullscreenTooltip,
            icon: Icon(
              Icons.fullscreen,
              color: palette.light ? Colors.black : Colors.white,
            ),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => ChartExplorerScreen(
                    initial: ChartFrame(
                      data: data,
                      outerPlanets: outerPlanets,
                      outerHouses: outerHouses,
                      outerData: outerData,
                      title: title,
                      subtitle: subtitle,
                    ),
                    initialDate:
                        initialDate ??
                        DateTime.tryParse(
                          '${data.meta.date} ${data.meta.time}',
                        ) ??
                        DateTime.now(),
                    loadFrame: loadFrame,
                    lightTheme: lightTheme,
                    timeUnits: timeUnits,
                  ),
                ),
              );
            },
          ),
      ],
    );
  }
}

class _Glyph {
  final PlanetPos planet;
  final double actual;
  double display;
  _Glyph(this.planet, this.actual) : display = actual;
}

class _WheelPainter extends CustomPainter {
  final ChartData data;
  final List<PlanetPos>? outerPlanets;
  final List<HouseCusp>? outerHouses;
  final ChartData? outerData;
  final bool showAspectLines;
  final bool showTransitAspects;
  final ChartWheelStyle style;

  _WheelPainter({
    required this.data,
    this.outerPlanets,
    this.outerHouses,
    this.outerData,
    this.showAspectLines = true,
    this.showTransitAspects = true,
    required this.style,
  });

  /// Transit açılarında kabul edilen maksimum sapma (derece).
  /// Bilinçli olarak dar tutulur: 12×12 gezegen çiftinde geniş orb, merkezde
  /// okunamaz bir çizgi ağı üretiyordu.
  static const double transitOrb = 2.0;

  /// Desteklenen açılar ve tam açı değerleri.
  static const Map<String, double> _aspectAngles = {
    'conjunction': 0,
    'sextile': 60,
    'square': 90,
    'trine': 120,
    'opposition': 180,
  };

  Color get _gold => style.accent;
  Color get _border => style.line;
  Color get _muted => style.muted;
  Color get _bg => style.background;
  Color get _transit => style.transit;
  Color get _retroColor => style.retro;

  Color _signColor(int sign) => style.signColor(sign);
  Color _planetColor(String name) => style.planetColor(name);
  Color _aspectColor(String type) => style.aspectColor(type);
  Color _transitAspectColor(String type) => style.transitAspectColor(type);

  double _theta(double lon, double ascLon) {
    // 180° = sol (ASC). Zodiac boylamı arttıkça saat yönünün tersine gider.
    return math.pi + (ascLon - lon) * math.pi / 180.0;
  }

  Offset _pos(double lon, double r, Offset c, double ascLon) {
    final a = _theta(lon, ascLon);
    return Offset(c.dx + r * math.cos(a), c.dy + r * math.sin(a));
  }

  /// Gezegenleri çakışmayacak şekilde en büyük boşluktan başlayarak açar.
  ///
  /// [minSep] derece cinsinden minimum açısal ayrımdır; piksel bazlı
  /// hesaplandığı için sembol ve derece yazısı hiçbir zaman üst üste binmez.
  /// Yalnızca etiket konumu kaydırılır, gezegenin gerçek boylamı korunur.
  List<_Glyph> _layout(List<PlanetPos> planets, double minSep) {
    if (planets.isEmpty) return const [];
    final items = planets.map((p) => _Glyph(p, p.lon)).toList()
      ..sort((a, b) => a.actual.compareTo(b.actual));
    final n = items.length;
    int gapIdx = 0;
    double gap = -1;
    for (var i = 0; i < n; i++) {
      final next = i == n - 1 ? items[0].actual + 360 : items[i + 1].actual;
      final g = next - items[i].actual;
      if (g > gap) {
        gap = g;
        gapIdx = i;
      }
    }
    final ordered = <_Glyph>[];
    for (var k = 1; k <= n; k++) {
      ordered.add(items[(gapIdx + k) % n]);
    }
    final base = ordered.first.actual;
    var prev = double.negativeInfinity;
    for (final it in ordered) {
      var l = it.actual;
      while (l < base) {
        l += 360;
      }
      if (l < prev + minSep) l = prev + minSep;
      it.display = l;
      prev = l;
    }
    return ordered;
  }

  TextStyle _baseStyle(Color color, double fontSize) => TextStyle(
    color: color,
    fontSize: fontSize,
    fontWeight: FontWeight.w600,
    height: 1.0,
  );

  TextPainter _tp(
    String text,
    Color color,
    double fontSize, {
    FontWeight weight = FontWeight.w600,
    double letterSpacing = 0,
  }) {
    return TextPainter(
      text: TextSpan(
        text: text,
        style: _baseStyle(color, fontSize).copyWith(
          fontWeight: weight,
          letterSpacing: letterSpacing,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
  }

  /// Gezegen etiketi: tek satırda `DD°MM′`, retro ise kırmızı `R`.
  ///
  /// Burç sembolü etikete eklenmez; gezegenin hangi burçta olduğu zodyak
  /// kuşağındaki konumundan okunur. Bu, halkadaki yazı yoğunluğunu yarıya
  /// indirir ve haritanın okunabilirliğini artırır.
  TextPainter _planetLabel(PlanetPos p, double fontSize) {
    final valueColor = p.retrograde ? _retroColor : _muted;
    final total = (p.degree * 60).round();
    final d = total ~/ 60;
    final m = total % 60;
    return TextPainter(
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
      text: TextSpan(
        style: _baseStyle(valueColor, fontSize),
        children: [
          TextSpan(
            text:
                '${d.toString().padLeft(2, '0')}°'
                '${m.toString().padLeft(2, '0')}′',
          ),
          if (p.retrograde)
            TextSpan(
              text: ' R',
              style: TextStyle(
                color: _retroColor,
                fontSize: fontSize,
                fontWeight: FontWeight.w800,
              ),
            ),
        ],
      ),
    )..layout();
  }

  void _glyphAt(
    Canvas canvas,
    Offset center,
    double radius,
    double lon,
    String text,
    Color color,
    double size, {
    double ascLon = 0,
    FontWeight weight = FontWeight.w600,
  }) {
    final tp = _tp(text, color, size, weight: weight);
    final p = _pos(lon, radius, center, ascLon);
    tp.paint(canvas, p - Offset(tp.width / 2, tp.height / 2));
  }

  /// Verilen halka yarıçapında, [needPx] piksel genişliğinde bir etiketin
  /// çakışmaması için gereken minimum açısal ayrım (derece).
  double _minSepDeg(double radiusPx, double needPx) {
    if (radiusPx <= 0) return 30;
    return (needPx / radiusPx) * 180 / math.pi;
  }

  /// Derece etiketlerinin en geniş olanının piksel genişliği.
  double _maxLabelWidth(List<PlanetPos> planets, double fontSize) {
    var w = 0.0;
    for (final p in planets) {
      final tp = _planetLabel(p, fontSize);
      if (tp.width > w) w = tp.width;
    }
    return w;
  }

  /// Burç kuşağını (zemin + sınırlar + semboller) çizer.
  ///
  /// Derece çentikleri bilinçli olarak çizilmez: 360 adet çizgi haritayı
  /// karıştırıyordu. Yalnızca 30° burç ayırıcıları ve semboller kalır.
  void _drawZodiacBand(
    Canvas canvas,
    Offset center,
    double ascLon,
    double outer,
    double inner, {
    required double glyphSize,
    required double unit,
  }) {
    for (var i = 0; i < 12; i++) {
      final rect = Rect.fromCircle(
        center: center,
        radius: (outer + inner) / 2,
      );
      final paint = Paint()
        ..color = _signColor(i).withValues(alpha: style.light ? 0.07 : 0.10)
        ..style = PaintingStyle.stroke
        ..strokeWidth = outer - inner;
      canvas.drawArc(
        rect,
        _theta(i * 30.0, ascLon),
        -30 * math.pi / 180.0,
        false,
        paint,
      );
    }

    final ringPaint = Paint()
      ..color = _border.withValues(alpha: 0.85)
      ..style = PaintingStyle.stroke
      ..strokeWidth = (unit * 0.0075).clamp(0.9, 1.6);
    canvas.drawCircle(center, outer, ringPaint);
    canvas.drawCircle(
      center,
      inner,
      Paint()
        ..color = _border.withValues(alpha: 0.45)
        ..style = PaintingStyle.stroke
        ..strokeWidth = (unit * 0.0060).clamp(0.7, 1.3),
    );

    final divider = Paint()
      ..color = _border.withValues(alpha: 0.30)
      ..strokeWidth = (unit * 0.0055).clamp(0.7, 1.2);
    for (var i = 0; i < 12; i++) {
      canvas.drawLine(
        _pos(i * 30.0, inner, center, ascLon),
        _pos(i * 30.0, outer, center, ascLon),
        divider,
      );
    }

    final glyphR = (outer + inner) / 2;
    for (var i = 0; i < 12; i++) {
      _glyphAt(
        canvas,
        center,
        glyphR,
        i * 30.0 + 15,
        chartSignGlyphs[i],
        _signColor(i),
        glyphSize,
        ascLon: ascLon,
        weight: FontWeight.w400,
      );
    }
  }

  /// İç ve dış harita gezegenleri arasındaki transit açılarını çizer.
  void _drawTransitAspects(
    Canvas canvas,
    Offset center,
    double ascLon,
    double aspectR,
    double stroke,
  ) {
    final outer = outerPlanets;
    if (outer == null || outer.isEmpty) return;
    final base = stroke * 0.8;
    for (final o in outer) {
      for (final i in data.planets) {
        var diff = (o.lon - i.lon).abs() % 360;
        if (diff > 180) diff = 360 - diff;
        for (final entry in _aspectAngles.entries) {
          if (entry.key == 'conjunction') continue;
          final delta = (diff - entry.value).abs();
          if (delta > transitOrb) continue;
          final color = _transitAspectColor(entry.key);
          final alpha = (0.34 - delta * 0.11).clamp(0.08, 0.34);
          final paint = Paint()
            ..color = color.withValues(alpha: alpha)
            ..strokeWidth =
                (entry.key == 'trine' || entry.key == 'opposition')
                ? base * 1.35
                : base;
          canvas.drawLine(
            _pos(i.lon, aspectR, center, ascLon),
            _pos(o.lon, aspectR, center, ascLon),
            paint,
          );
        }
      }
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final r = size.shortestSide / 2 - 2;
    if (r < 70) return;

    final ascLon = data.asc.lon;
    final hasOuter = outerPlanets != null && outerPlanets!.isNotEmpty;
    final unit = r;
    final g = ChartWheelGeometry(r, biWheel: hasOuter);

    // --- Oranlı halka yarıçapları ---
    // Hepsi tek bir R üzerinden türetilir; harita büyüyüp küçüldüğünde
    // katmanlar birbirine göre orantılı kalır (bkz. ChartWheelGeometry).
    final signOuter = g.signOuter;
    final signInner = g.signInner;
    final outerGlyphR = g.outerGlyphR;
    final outerLabelR = g.outerLabelR;
    final outerBandOuter = g.outerBandOuter;
    final outerBandInner = g.outerBandInner;
    final innerSignOuter = g.innerSignOuter;
    final innerSignInner = g.innerSignInner;
    final natalGlyphR = g.natalGlyphR;
    final natalLabelR = g.natalLabelR;
    final natalBandOuter = g.natalBandOuter;
    final natalBandInner = g.natalBandInner;
    final aspectR = g.aspectR;
    final houseNumR = g.houseNumR;
    final hubR = g.hubR;
    final cuspOuterR = g.cuspOuterR;
    final cuspInnerR = g.cuspInnerR;
    final houseNumSize = g.houseNumSize;
    // --- Gezegen bantlarının zeminleri ---
    canvas.drawCircle(
      center,
      (natalBandOuter + natalBandInner) / 2,
      Paint()
        ..color = style.bandTint
        ..style = PaintingStyle.stroke
        ..strokeWidth = natalBandOuter - natalBandInner,
    );
    if (hasOuter) {
      canvas.drawCircle(
        center,
        (outerBandOuter + outerBandInner) / 2,
        Paint()
          ..color = style.transitTint.withValues(alpha: style.light ? 1 : 0.75)
          ..style = PaintingStyle.stroke
          ..strokeWidth = outerBandOuter - outerBandInner,
      );
    }

    // --- Zodyak kuşakları ---
    _drawZodiacBand(
      canvas,
      center,
      ascLon,
      signOuter,
      signInner,
      glyphSize: g.signGlyphSize,
      unit: unit,
    );
    if (hasOuter) {
      _drawZodiacBand(
        canvas,
        center,
        ascLon,
        innerSignOuter,
        innerSignInner,
        glyphSize: g.innerSignGlyphSize,
        unit: unit,
      );
      // İki harita arasındaki ayırıcı çizgi.
      canvas.drawCircle(
        center,
        innerSignOuter,
        Paint()
          ..color = _gold.withValues(alpha: 0.35)
          ..style = PaintingStyle.stroke
          ..strokeWidth = (unit * 0.0065).clamp(0.8, 1.4),
      );
    }

    // --- Ev çizgileri ve numaraları ---
    // Ev giriş dereceleri artık yazılmaz: 12 ek metin haritayı
    // kalabalıklaştırıyordu; dereceler bilgi panelinde yer alır.
    final cuspPaint = Paint()
      ..color = _gold.withValues(alpha: 0.18)
      ..strokeWidth = (unit * 0.0045).clamp(0.6, 1.1);
    final houses = [...data.houses]
      ..sort((a, b) => a.number.compareTo(b.number));
    for (var i = 0; i < houses.length; i++) {
      final h = houses[i];
      canvas.drawLine(
        _pos(h.lon, cuspOuterR, center, ascLon),
        _pos(h.lon, cuspInnerR, center, ascLon),
        cuspPaint,
      );

      final next = houses[(i + 1) % houses.length];
      var delta = next.lon - h.lon;
      while (delta <= 0) {
        delta += 360;
      }
      final mid = h.lon + delta / 2;
      _glyphAt(
        canvas,
        center,
        houseNumR,
        mid,
        h.number.toString(),
        _gold.withValues(alpha: 0.75),
        houseNumSize,
        ascLon: ascLon,
        weight: FontWeight.w700,
      );
    }

    // --- Dış harita ev çizgileri (transit): gezegen bandında ince çentikler ---
    if (hasOuter && outerHouses != null && outerHouses!.isNotEmpty) {
      final outerCusp = Paint()
        ..color = _transit.withValues(alpha: 0.16)
        ..strokeWidth = (unit * 0.0045).clamp(0.6, 1.1);
      for (final h in outerHouses!) {
        canvas.drawLine(
          _pos(h.lon, outerBandInner, center, ascLon),
          _pos(h.lon, outerBandOuter, center, ascLon),
          outerCusp,
        );
      }
    }

    // --- Açı çizgileri (gezegen sembollerinin arkasında kalır) ---
    if (hasOuter) {
      if (showTransitAspects) {
        _drawTransitAspects(canvas, center, ascLon, aspectR, g.aspectStroke);
      }
    } else if (showAspectLines) {
      final byName = <String, double>{
        for (final p in data.planets) p.name: p.lon,
      };
      final base = g.aspectStroke;
      for (final a in data.aspects) {
        final l1 = byName[a.p1];
        final l2 = byName[a.p2];
        if (l1 == null || l2 == null) continue;
        final type = a.type.toLowerCase();
        if (type == 'conjunction') continue;
        final color = _aspectColor(a.type);
        final alpha = (0.45 - a.orb * 0.030).clamp(0.14, 0.45);
        final paint = Paint()
          ..color = color.withValues(alpha: alpha)
          ..strokeWidth = (type == 'trine' || type == 'opposition')
              ? base * 1.35
              : base;
        canvas.drawLine(
          _pos(l1, aspectR, center, ascLon),
          _pos(l2, aspectR, center, ascLon),
          paint,
        );
      }
    }

    canvas.drawCircle(
      center,
      aspectR,
      Paint()
        ..color = _border.withValues(alpha: 0.35)
        ..style = PaintingStyle.stroke
        ..strokeWidth = (unit * 0.0050).clamp(0.7, 1.2),
    );

    // --- Merkezdeki boş daire ---
    canvas.drawCircle(
      center,
      hubR,
      Paint()
        ..color = _bg
        ..style = PaintingStyle.fill,
    );
    canvas.drawCircle(
      center,
      hubR,
      Paint()
        ..color = _border.withValues(alpha: 0.5)
        ..style = PaintingStyle.stroke
        ..strokeWidth = (unit * 0.0060).clamp(0.8, 1.3),
    );

    // --- ASC / DSC / MC / IC eksenleri ---
    _axis(canvas, center, cuspOuterR, hubR, ascLon + 180, ascLon, unit);
    _axis(canvas, center, cuspOuterR, hubR, data.mc.lon, ascLon, unit);

    // --- Gezegen halkaları ---
    final natalGlyphSize = g.natalGlyphSize;
    final natalLabelSize = g.natalLabelSize;
    final natal = _layout(
      data.planets,
      _minSepDeg(
            natalGlyphR,
            math.max(
              natalGlyphSize,
              _maxLabelWidth(data.planets, natalLabelSize),
            ),
          ) *
          1.06,
    );
    for (final g in natal) {
      final color = _planetColor(g.planet.name);
      _drawLeader(
        canvas,
        center,
        ascLon,
        g,
        natalGlyphR,
        natalGlyphSize,
        color.withValues(alpha: 0.40),
        unit,
      );
      _glyphAt(
        canvas,
        center,
        natalGlyphR,
        g.display,
        chartPlanetGlyphs[g.planet.name] ?? '·',
        color,
        natalGlyphSize,
        ascLon: ascLon,
        weight: FontWeight.w600,
      );
      final tp = _planetLabel(g.planet, natalLabelSize);
      final p = _pos(g.display, natalLabelR, center, ascLon);
      tp.paint(canvas, p - Offset(tp.width / 2, tp.height / 2));
    }

    if (hasOuter) {
      final transitGlyphSize = g.outerGlyphSize;
      final transitLabelSize = g.outerLabelSize;
      final trans = _layout(
        outerPlanets!,
        _minSepDeg(
              outerGlyphR,
              math.max(
                transitGlyphSize,
                _maxLabelWidth(outerPlanets!, transitLabelSize),
              ),
            ) *
            1.06,
      );
      for (final g in trans) {
        final color = _transit;
        _drawLeader(
          canvas,
          center,
          ascLon,
          g,
          outerGlyphR,
          transitGlyphSize,
          color.withValues(alpha: 0.30),
          unit,
        );
        _glyphAt(
          canvas,
          center,
          outerGlyphR,
          g.display,
          chartPlanetGlyphs[g.planet.name] ?? '·',
          color,
          transitGlyphSize,
          ascLon: ascLon,
          weight: FontWeight.w600,
        );
        final tp = _planetLabel(g.planet, transitLabelSize);
        final p = _pos(g.display, outerLabelR, center, ascLon);
        tp.paint(canvas, p - Offset(tp.width / 2, tp.height / 2));
      }
    }

    // --- Açı etiketleri ---
    // Okunaklılık için merkeze yakın, eksenlerin üzerinde çizilir.
    final angleLabelR = g.angleLabelR;
    _angleLabel(canvas, center, angleLabelR, data.asc.lon, 'ASC', ascLon, unit);
    _angleLabel(
      canvas,
      center,
      angleLabelR,
      data.asc.lon + 180,
      'DSC',
      ascLon,
      unit,
    );
    _angleLabel(canvas, center, angleLabelR, data.mc.lon, 'MC', ascLon, unit);
    _angleLabel(
      canvas,
      center,
      angleLabelR,
      data.mc.lon + 180,
      'IC',
      ascLon,
      unit,
    );

    // merkez noktası
    canvas.drawCircle(
      center,
      1.6,
      Paint()..color = _gold.withValues(alpha: 0.5),
    );
  }

  /// Gerçek konumdan kaydırılmış sembole ince kılavuz çizgisi.
  void _drawLeader(
    Canvas canvas,
    Offset center,
    double ascLon,
    _Glyph g,
    double radius,
    double glyphSize,
    Color color,
    double unit,
  ) {
    var drift = g.display - g.actual;
    if (drift.abs() < 1.5) return;
    final lineR = radius - glyphSize * 0.95;
    final paint = Paint()
      ..color = color
      ..strokeWidth = (unit * 0.0040).clamp(0.6, 0.9)
      ..style = PaintingStyle.stroke;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: lineR),
      _theta(g.actual, ascLon),
      -drift * math.pi / 180.0,
      false,
      paint,
    );
    canvas.drawCircle(
      _pos(g.actual, radius, center, ascLon),
      math.max(1.0, unit * 0.008),
      Paint()..color = color,
    );
  }

  void _axis(
    Canvas canvas,
    Offset center,
    double outer,
    double inner,
    double lon,
    double ascLon,
    double unit,
  ) {
    final paint = Paint()
      ..color = _gold.withValues(alpha: 0.55)
      ..strokeWidth = (unit * 0.0090).clamp(1.1, 2.2);
    canvas.drawLine(
      _pos(lon, outer, center, ascLon),
      _pos(lon, inner, center, ascLon),
      paint,
    );
    canvas.drawLine(
      _pos(lon + 180, outer, center, ascLon),
      _pos(lon + 180, inner, center, ascLon),
      paint,
    );
  }

  void _angleLabel(
    Canvas canvas,
    Offset center,
    double radius,
    double lon,
    String label,
    double ascLon,
    double unit,
  ) {
    final tp = _tp(
      label,
      _gold,
      (unit * 0.030).clamp(8.0, 13.0),
      weight: FontWeight.w700,
    );
    final p = _pos(lon, radius, center, ascLon);
    final origin = p - Offset(tp.width / 2, tp.height / 2);
    final bg = Rect.fromLTWH(
      origin.dx - 3,
      origin.dy - 1.5,
      tp.width + 6,
      tp.height + 3,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(bg, const Radius.circular(3)),
      Paint()..color = _bg.withValues(alpha: 0.88),
    );
    tp.paint(canvas, origin);
  }

  @override
  bool shouldRepaint(covariant _WheelPainter old) =>
      old.style != style ||
      old.showAspectLines != showAspectLines ||
      old.showTransitAspects != showTransitAspects ||
      old.data != data ||
      old.outerPlanets != outerPlanets ||
      old.outerHouses != outerHouses ||
      old.outerData != outerData;
}
