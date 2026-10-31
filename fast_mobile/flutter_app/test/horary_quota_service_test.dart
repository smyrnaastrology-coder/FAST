import 'dart:convert';

import 'package:fast_app/l10n/app_localizations_en.dart';
import 'package:fast_app/l10n/app_localizations_es.dart';
import 'package:fast_app/l10n/app_localizations_tr.dart';
import 'package:fast_app/services/horary_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('quota is read from the authenticated server', () async {
    final client = MockClient((request) async {
      expect(request.url.path, '/api/holavon/quota');
      expect(request.headers['Authorization'], 'Bearer test-token');
      return http.Response(jsonEncode({'remaining': 2, 'limit': 3, 'is_pro': true}), 200);
    });
    final result = await HoraryService.quota(client: client, accessToken: 'test-token');
    expect(result.ok, isTrue);
    expect(result.data['remaining'], 2);
    expect(result.data['is_pro'], isTrue);
  });

  test('unknown quota and expired session fail closed', () async {
    final malformed = MockClient((_) async => http.Response('{"remaining":4,"limit":3,"is_pro":false}', 200));
    expect((await HoraryService.quota(client: malformed, accessToken: 'token')).ok, isFalse);
    final expired = MockClient((_) async => http.Response('', 401));
    expect((await HoraryService.quota(client: expired, accessToken: 'token')).authError, isTrue);
    expect((await HoraryService.quota(client: expired, accessToken: '')).authError, isTrue);
  });

  test('question sends a UUID and bounded history, not a user email', () async {
    final client = MockClient((request) async {
      expect(request.url.path, '/api/holavon/cast');
      expect(request.headers['Authorization'], 'Bearer test-token');
      final payload = jsonDecode(request.body) as Map<String, dynamic>;
      expect(payload.containsKey('email'), isFalse);
      expect(payload['request_id'], matches(RegExp(r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$')));
      expect((payload['history'] as List).length, 4);
      expect((payload['history'] as List).first['content'], '2');
      return http.Response(jsonEncode({'verdict': 'YES', 'remaining': 2, 'is_pro': false}), 200);
    });
    final history = List.generate(6, (i) => {'role': 'user', 'content': '$i'});
    final result = await HoraryService.cast(question: 'Will it work?', lat: 41, lon: 29,
        history: history, client: client, accessToken: 'test-token');
    expect(result.ok, isTrue);
    expect(result.data['remaining'], 2);
  });

  test('free and Pro limits are localized consistently', () {
    final tr = AppLocalizationsTr();
    final en = AppLocalizationsEn();
    final es = AppLocalizationsEs();
    expect(tr.planFreeFeat6, contains('toplam 3'));
    expect(en.planFreeFeat6, contains('3 free questions in total'));
    expect(es.planFreeFeat6, contains('3 preguntas gratis en total'));
    for (final text in [tr.horaryProLimitDesc, en.horaryProLimitDesc, es.horaryProLimitDesc]) {
      expect(text, contains('3'));
      expect(text, contains('UTC'));
    }
  });

  test('retry after an in-progress response reuses the same question ID', () async {
    final ids = <String>[];
    final client = MockClient((request) async {
      final payload = jsonDecode(request.body) as Map<String, dynamic>;
      ids.add(payload['request_id'] as String);
      if (ids.length == 1) return http.Response('', 409);
      return http.Response('{"verdict":"YES","remaining":2,"is_pro":false}', 200);
    });
    final result = await HoraryService.cast(question: 'Will this work?', lat: 41, lon: 29,
        client: client, accessToken: 'test-token');
    expect(result.ok, isTrue);
    expect(ids, hasLength(2));
    expect(ids[0], ids[1]);
  });
}
