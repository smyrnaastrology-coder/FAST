import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/services/social_service.dart';

void main() {
  test('birthKey doğum verisini normalize eder', () {
    expect(
      SocialService.birthKey(date: ' 1990-01-01 ', time: ''),
      '1990-01-01|12:00',
    );
    expect(
      SocialService.birthKey(date: '1990-01-01', time: ' 07:45 '),
      '1990-01-01|07:45',
    );
    expect(
      SocialService.birthKey(date: null, time: null),
      '|12:00',
    );
  });

  test('farklı kişilerin anahtarları eşleşmez', () {
    final owner = SocialService.birthKey(
      date: '1990-01-01',
      time: '12:00',
    );
    final savedPerson = SocialService.birthKey(
      date: '1985-06-12',
      time: '12:00',
    );
    expect(owner == savedPerson, isFalse);
  });
}
