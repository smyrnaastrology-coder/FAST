import 'package:flutter/material.dart';
import 'dart:math' as math;
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../config/theme.dart';

class LostRadarMap extends StatelessWidget {
  final double lat;
  final double lon;
  final String direction; // DOĞU, BATI vb.
  final String distance; // 41m / 1.2km
  final String place;
  final int house;
  final double deg;

  const LostRadarMap({super.key, required this.lat, required this.lon, required this.direction, required this.distance, required this.place, required this.house, this.deg = 15});

  double get _bearing {
    const map = {
      "DOĞU": 90.0, "BATI": 270.0, "KUZEY": 0.0, "GÜNEY": 180.0,
      "KUZEYDOĞU": 45.0, "KUZEY DOĞU":45.0, "DOĞU KUZEY-DOĞU":67.5, "KUZEY KUZEY-DOĞU":22.5,
      "KUZEYBATI":315.0, "KUZEY BATI":315.0, "BATI KUZEYBATI":292.5, "KUZEY KUZEY-BATI":337.5,
      "GÜNEYDOĞU":135.0, "GÜNEY DOĞU":135.0, "GÜNEY GÜNEY-DOĞU":157.5, "DOĞU GÜNEY-DOĞU":112.5,
      "GÜNEYBATI":225.0, "GÜNEY BATI":225.0, "GÜNEY GÜNEY-BATI":202.5, "BATI GÜNEY-BATI":247.5,
    };
    final base = (map[direction] ?? 0).toDouble();
    // gezegen derecesine göre ince sapma: 15° merkez, ±12° max (0°→ -12°, 30°→ +12°)
    final fine = (deg - 15) * 0.8;
    return (base + fine) % 360;
  }

  double get _distMeters {
    final v = double.tryParse(distance.replaceAll(RegExp(r'[^0-9.]'), '')) ?? 0;
    if (distance.contains('km')) return v * 1000;
    return v;
  }

  LatLng get _target {
    // haversine destination
    final R = 6371000.0;
    final d = _distMeters / R;
    final br = _bearing * math.pi / 180;
    final lat1 = lat * math.pi / 180;
    final lon1 = lon * math.pi / 180;
    final lat2 = math.asin(math.sin(lat1)*math.cos(d) + math.cos(lat1)*math.sin(d)*math.cos(br));
    final lon2 = lon1 + math.atan2(math.sin(br)*math.sin(d)*math.cos(lat1), math.cos(d)-math.sin(lat1)*math.sin(lat2));
    return LatLng(lat2*180/math.pi, lon2*180/math.pi);
  }

  @override
  Widget build(BuildContext context) {
    final target = _target;
    final center = LatLng((lat+target.latitude)/2, (lon+target.longitude)/2);
    // zoom: mesafeye göre
    double zoom = 18;
    if (_distMeters > 500) zoom = 16;
    if (_distMeters > 2000) zoom = 14;
    if (_distMeters > 10000) zoom = 12;
    return Card(
      color: const Color(0xFF1A1423),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: const BorderSide(color: Color(0xFFC9A96E), width:1)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.satellite_alt, size:16, color: Color(0xFFC9A96E)),
            const SizedBox(width:6),
            const Text('Uydu Radar', style: TextStyle(color: Color(0xFFC9A96E), fontWeight: FontWeight.bold, fontSize:12)),
            const Spacer(),
            Text('$direction • $distance • Ev$house', style: const TextStyle(color: Color(0xFFa898c0), fontSize:10)),
          ]),
          const SizedBox(height:4),
          Container(padding: const EdgeInsets.symmetric(horizontal:8, vertical:6), decoration: BoxDecoration(color: const Color(0xFF2a1f38), borderRadius: BorderRadius.circular(8), border: Border.all(color: const Color(0xFFC9A96E).withOpacity(0.3))),
            child: Row(children: [
              const Icon(Icons.explore, size:12, color: Color(0xFFC9A96E)),
              const SizedBox(width:6),
              Flexible(child: Text('Milyem: ${_bearing.toStringAsFixed(1)}° = ${(_bearing*6400/360).round()} milyem', style: const TextStyle(color: Color(0xFFe8e0f0), fontSize:10, fontFamily: 'monospace'))),
              const SizedBox(width:6),
              const Text('K:0 D:1600 G:3200 B:4800', style: TextStyle(color: Color(0xFFa898c0), fontSize:8)),
            ])),
          const SizedBox(height:8),
          Text(place, style: const TextStyle(color: Color(0xFFe8e0f0), fontSize:11)),
          const SizedBox(height:12),
          ClipRRect(borderRadius: BorderRadius.circular(8), child: SizedBox(height: 220, child: FlutterMap(
            options: MapOptions(initialCenter: center, initialZoom: zoom),
            children: [
              TileLayer(urlTemplate: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', userAgentPackageName: 'com.horaryoracle.app'),
              PolylineLayer(polylines: [Polyline(points: [LatLng(lat, lon), target], color: const Color(0xFFC9A96E), strokeWidth: 3)]),
              MarkerLayer(markers: [
                Marker(point: LatLng(lat, lon), width: 30, height: 30, child: const Icon(Icons.my_location, color: Colors.blueAccent, size:28)),
                Marker(point: target, width: 30, height: 30, child: const Icon(Icons.location_on, color: Colors.redAccent, size:30)),
              ]),
            ],
          ))),
          const SizedBox(height:6),
          Text('Mavi sensin → kırmızı hedef ~$distance $direction', style: const TextStyle(color: Color(0xFFa898c0), fontSize:10)),
        ]),
      ),
    );
  }
}

class _RadarPainter extends CustomPainter {
  final double bearing;
  final double distMeters;
  _RadarPainter({required this.bearing, required this.distMeters});

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width/2, cy = size.height/2;
    final r = math.min(cx, cy) - 10;
    // bg
    canvas.drawCircle(Offset(cx,cy), r, Paint()..color=const Color(0xFF2a1f38));
    canvas.drawCircle(Offset(cx,cy), r, Paint()..color=const Color(0xFFC9A96E).withOpacity(0.3)..style=PaintingStyle.stroke..strokeWidth=1);
    // grid
    for(int i=1;i<=3;i++){
      canvas.drawCircle(Offset(cx,cy), r*i/3, Paint()..color=Colors.white.withOpacity(0.08)..style=PaintingStyle.stroke..strokeWidth=0.5);
    }
    // N
    const dirs = ['K','D','G','B'];
    for(int i=0;i<4;i++){
      final ang = i*90*math.pi/180;
      final x = cx + r*0.92*math.sin(ang);
      final y = cy - r*0.92*math.cos(ang);
      final tp = TextPainter(text: TextSpan(text: dirs[i], style: const TextStyle(color: Color(0xFFa898c0), fontSize:10)), textDirection: TextDirection.ltr)..layout();
      tp.paint(canvas, Offset(x-tp.width/2, y-tp.height/2));
    }
    // you
    canvas.drawCircle(Offset(cx,cy), 5, Paint()..color=const Color(0xFF6a9ae2));
    canvas.drawCircle(Offset(cx,cy), 5, Paint()..color=Colors.white..style=PaintingStyle.stroke..strokeWidth=1.5);
    // arrow
    final ang = bearing*math.pi/180;
    // scale distance: max radius = ~500m, beyond clamp
    final maxM = 500.0;
    final norm = (distMeters.clamp(0, maxM))/maxM;
    final len = r*0.15 + norm*(r*0.75);
    final ex = cx + len*math.sin(ang);
    final ey = cy - len*math.cos(ang);
    final paint = Paint()..color=const Color(0xFFC9A96E)..strokeWidth=3..strokeCap=StrokeCap.round;
    canvas.drawLine(Offset(cx,cy), Offset(ex,ey), paint);
    // arrow head
    final headLen = 10.0;
    final leftAng = ang + 150*math.pi/180;
    final rightAng = ang - 150*math.pi/180;
    canvas.drawLine(Offset(ex,ey), Offset(ex+headLen*math.sin(leftAng), ey-headLen*math.cos(leftAng)), paint);
    canvas.drawLine(Offset(ex,ey), Offset(ex+headLen*math.sin(rightAng), ey-headLen*math.cos(rightAng)), paint);
    // target dot
    canvas.drawCircle(Offset(ex,ey), 6, Paint()..color=Colors.redAccent);
    canvas.drawCircle(Offset(ex,ey), 6, Paint()..color=Colors.white..style=PaintingStyle.stroke..strokeWidth=1);
  }
  @override bool shouldRepaint(covariant CustomPainter old) => true;
}
