import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:fast_app/models/chart_data.dart';
import 'package:fast_app/services/chart_service.dart';

void main() {
  test('Natal isteği cihazın güncel UTC farkını doğum saatine dayatmaz', () async {
    final service = ChartService(client: MockClient((request) async {
      final body = jsonDecode(request.body) as Map;
      expect(body.containsKey('tz'), isFalse);
      expect(body['saat'], '23:14');
      return http.Response(jsonEncode({'meta': {'tz': 2.0}}), 200);
    }));
    final result = await service.natal(tarih: '1986-10-08', saat: '23:14', lat: 40.3167, lon: 36.55);
    expect(result.meta.tz, 2.0);
  });

  test('Transit tarihsel saat dilimini sunucu çözer; progresyon hedef saati korunur', () async {
    final natal = ChartData.fromJson({'meta': {'tarih': '1986-10-08', 'saat': '23:14',
      'lat': 40.3167, 'lon': 36.55, 'tz': 2.0}});
    final service = ChartService(client: MockClient((request) async {
      final body = jsonDecode(request.body) as Map;
      if (request.url.path.endsWith('biwheel')) {
        expect(body.containsKey('tz'), isFalse);
        expect(body['natal_tz'], 2.0);
        expect(body['hedef_saat'], '23:15');
      } else {
        expect(body['target_time'], '23:15');
        expect(body['method'], 'minor');
      }
      return http.Response('{}', 200);
    }));
    await service.biwheel(natal: natal, hedefTarih: '1986-10-08', hedefSaat: '23:15');
    await service.progression(natal: natal, targetDate: '2026-10-08', targetTime: '23:15', method: 'minor');
  });
}
