import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fast_app/config/astro_signs.dart';
import 'package:fast_app/services/social_service.dart';

void main() {
  test('mutlak boylam Aries-first burca cevrilir', () {
    expect(AstroSigns.signNameFromLongitude(0), 'Koç');
    expect(AstroSigns.signNameFromLongitude(179.99), 'Başak');
    expect(AstroSigns.signNameFromLongitude(180), 'Terazi');
    expect(AstroSigns.signNameFromLongitude(359.9), 'Balık');
    expect(AstroSigns.signNameFromLongitude(372), 'Koç');
  });

  test('SocialProfile kunye kolonlarini okur', () {
    final p = SocialProfile.fromMap({
      'user_id': 'u1',
      'username': 'ada',
      'sun_sign': 'Terazi',
      'moon_sign': 'Başak',
      'sun_deg': 0.02,
      'moon_deg': 22,
      'birth_time_set': true,
      'is_astrologer': true,
      'astro_field': 'Vedik',
      'is_pro': true,
    });
    expect(p.sunSign, 'Terazi');
    expect(p.moonSign, 'Başak');
    expect(p.sunDeg, closeTo(0.02, 0.001));
    expect(p.moonDeg, 22);
    expect(p.birthTimeSet, isTrue);
    expect(p.isAstrologer, isTrue);
    expect(p.astroField, 'Vedik');
    expect(p.isPro, isTrue);
  });

  test('SocialProfile eski satirlara toleransli (kolonlar yok)', () {
    final p = SocialProfile.fromMap({'user_id': 'u1', 'username': 'ada', 'sun_sign': 'Aslan'});
    expect(p.moonSign, isNull);
    expect(p.sunDeg, isNull);
    expect(p.birthTimeSet, isFalse);
    expect(p.isAstrologer, isFalse);
    expect(p.isPro, isFalse);
  });

  testWidgets('rozet dereceyi yalnizca saat bilinirse gosterir', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: Column(
          children: [
            AstroSigns.chip('Terazi', degree: 12.4, degreeKnown: true),
            AstroSigns.chip('Başak', degree: 3.1, degreeKnown: false, planetSymbol: '☽'),
          ],
        ),
      ),
    ));
    expect(find.text('☉ ♎ Terazi 12.4°'), findsOneWidget);
    expect(find.text('☽ ♍ Başak'), findsOneWidget);
  });
}
