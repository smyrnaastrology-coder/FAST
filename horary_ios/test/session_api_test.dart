import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:horary_oracle/services/horary_api.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  test('expired session is refreshed before retrying the question', () async {
    SharedPreferences.setMockInitialValues({
      'email': 'test@example.invalid', 'pass': 'test-password', 'device_id': 'device',
    });
    var logins = 0;
    var casts = 0;
    final client = MockClient((request) async {
      if (request.url.path == '/api/auth/login') {
        logins++;
        return http.Response(jsonEncode({'ok': true, 'session_token': 'token-$logins'}), 200);
      }
      casts++;
      if (casts == 1) {
        expect(request.headers['Authorization'], 'Bearer token-1');
        return http.Response('', 401);
      }
      expect(request.headers['Authorization'], 'Bearer token-2');
      return http.Response('{"verdict":"YES"}', 200);
    });
    await HoraryApi.login(email: 'test@example.invalid', password: 'test-password', client: client);
    final result = await HoraryApi.cast(question: 'Will it work?', lat: 41, lon: 29, client: client);
    expect(result['verdict'], 'YES');
    expect(logins, 2);
    expect(casts, 2);
  });
}
