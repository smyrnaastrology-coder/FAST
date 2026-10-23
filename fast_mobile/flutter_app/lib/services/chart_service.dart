import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/api_config.dart';
import '../models/chart_data.dart';

class ChartService {
  final http.Client _client;

  ChartService({http.Client? client}) : _client = client ?? http.Client();

  Future<ChartData> natal({
    required String tarih,
    required String saat,
    required double lat,
    required double lon,
    String houseSystem = 'P',
    String? isim,
    double? tz,
  }) async {
    final offset = tz ?? DateTime.now().timeZoneOffset.inMinutes / 60.0;
    final body = <String, dynamic>{
      'tarih': tarih,
      'saat': saat,
      'lat': lat,
      'lon': lon,
      'house_system': houseSystem,
      if (isim != null && isim.isNotEmpty) 'isim': isim,
      'tz': offset,
    };
    final r = await _client
        .post(
          Uri.parse(ApiConfig.chartsNatal),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(ApiConfig.timeout);
    if (r.statusCode != 200) {
      throw Exception('HTTP ${r.statusCode}');
    }
    final json = jsonDecode(r.body) as Map<String, dynamic>;
    final meta = Map<String, dynamic>.from(json['meta'] as Map? ?? const {});
    if (isim != null && isim.isNotEmpty) meta['isim'] = isim;
    meta['tarih'] = tarih;
    meta['saat'] = saat;
    meta['lat'] = lat;
    meta['lon'] = lon;
    meta['tz'] = offset;
    final merged = Map<String, dynamic>.from(json)..['meta'] = meta;
    return ChartData.fromJson(merged);
  }

  Future<Map<String, dynamic>> biwheel({
    required ChartData natal,
    required String hedefTarih,
    required String hedefSaat,
    double? lat,
    double? lon,
    double? tz,
  }) async {
    final offset = tz ?? DateTime.now().timeZoneOffset.inMinutes / 60.0;
    final body = <String, dynamic>{
      if (natal.meta.name != null && natal.meta.name!.isNotEmpty) 'isim': natal.meta.name,
      'natal_tarih': natal.meta.date,
      'natal_saat': natal.meta.time,
      'natal_lat': natal.meta.lat,
      'natal_lon': natal.meta.lng,
      if (natal.meta.tz != null) 'natal_tz': natal.meta.tz,
      'hedef_tarih': hedefTarih,
      'hedef_saat': hedefSaat,
      'lat': lat ?? natal.meta.lat,
      'lon': lon ?? natal.meta.lng,
      'tz': offset,
      'house_system': natal.houseSystem,
    };
    final r = await _client
        .post(
          Uri.parse(ApiConfig.chartsBiwheel),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(ApiConfig.timeout);
    if (r.statusCode != 200) {
      throw Exception('HTTP ${r.statusCode}');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> solarReturn({
    required ChartData natal,
    required int year,
    double? lat,
    double? lon,
    double? tz,
  }) async {
    final offset = tz ?? DateTime.now().timeZoneOffset.inMinutes / 60.0;
    final body = <String, dynamic>{
      if (natal.meta.name != null && natal.meta.name!.isNotEmpty) 'isim': natal.meta.name,
      'natal_tarih': natal.meta.date,
      'natal_saat': natal.meta.time,
      'natal_lat': natal.meta.lat,
      'natal_lon': natal.meta.lng,
      if (natal.meta.tz != null) 'natal_tz': natal.meta.tz,
      'yil': year,
      'lat': lat ?? natal.meta.lat,
      'lon': lon ?? natal.meta.lng,
      'tz': offset,
      'house_system': natal.houseSystem,
    };
    final r = await _client
        .post(
          Uri.parse(ApiConfig.chartsSolarReturn),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(ApiConfig.timeout);
    if (r.statusCode != 200) {
      throw Exception('HTTP ${r.statusCode}');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> lunarReturn({
    required ChartData natal,
    required int year,
    required int month,
    double? lat,
    double? lon,
    double? tz,
  }) async {
    final offset = tz ?? DateTime.now().timeZoneOffset.inMinutes / 60.0;
    final body = <String, dynamic>{
      if (natal.meta.name != null && natal.meta.name!.isNotEmpty) 'isim': natal.meta.name,
      'natal_tarih': natal.meta.date,
      'natal_saat': natal.meta.time,
      'natal_lat': natal.meta.lat,
      'natal_lon': natal.meta.lng,
      if (natal.meta.tz != null) 'natal_tz': natal.meta.tz,
      'yil': year,
      'ay': month,
      'lat': lat ?? natal.meta.lat,
      'lon': lon ?? natal.meta.lng,
      'tz': offset,
      'house_system': natal.houseSystem,
    };
    final r = await _client
        .post(
          Uri.parse(ApiConfig.chartsLunarReturn),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(ApiConfig.timeout);
    if (r.statusCode != 200) {
      throw Exception('HTTP ${r.statusCode}');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  static const _key = 'holavon_charts_list_v1';

  Future<List<ChartData>> loadLocal() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List;
      return list
          .whereType<Map>()
          .map((e) => ChartData.fromJson(e.cast<String, dynamic>()))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> saveLocal(ChartData data) async {
    final list = await loadLocal();
    final merged = [
      data,
      ...list.where((e) =>
          !(e.meta.date == data.meta.date &&
              e.meta.time == data.meta.time &&
              e.meta.name == data.meta.name)),
    ];
    final prefs = await SharedPreferences.getInstance();
    final encoded = jsonEncode(merged.map((e) => _toJson(e)).toList());
    await prefs.setString(_key, encoded);
  }

  Map<String, dynamic> _toJson(ChartData c) => {
        'house_system': c.houseSystem,
        'julian_day_ut': c.julianDay,
        'asc': {'lon': c.asc.lon, 'burc': c.asc.sign, 'derece': c.asc.degree},
        'mc': {'lon': c.mc.lon, 'burc': c.mc.sign, 'derece': c.mc.degree},
        'gezegenler': c.planets
            .map((p) => {
                  'ad': p.name,
                  'lon': p.lon,
                  'burc': p.sign,
                  'derece': p.degree,
                  'ev': p.house,
                  'hiz': p.speed,
                  'retro': p.retrograde,
                })
            .toList(),
        'evler': c.houses
            .map((h) => {
                  'no': h.number,
                  'lon': h.lon,
                  'burc': h.sign,
                  'derece': h.degree
                })
            .toList(),
        'acilar': c.aspects
            .map((a) => {'p1': a.p1, 'p2': a.p2, 'tip': a.type, 'orb': a.orb})
            .toList(),
        'meta': {
          if (c.meta.name != null && c.meta.name!.isNotEmpty) 'isim': c.meta.name,
          'tarih': c.meta.date,
          'saat': c.meta.time,
          'lat': c.meta.lat,
          'lon': c.meta.lng,
          if (c.meta.tz != null) 'tz': c.meta.tz,
          if (c.meta.place.isNotEmpty) 'sehir': c.meta.place,
        },
      };
}
