import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fast_app/services/social_service.dart';
import 'package:fast_app/widgets/pro_badge.dart';

void main() {
  testWidgets('ProBadge çizilir ve erişilebilirlik etiketi taşır', (tester) async {
    final handle = tester.ensureSemantics();
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(
        body: Center(child: ProBadge(size: 24, tooltip: 'Holavon Pro üyesi')),
      ),
    ));
    expect(find.byType(ProBadge), findsOneWidget);
    expect(find.bySemanticsLabel('Holavon Pro üyesi'), findsWidgets);
    handle.dispose();
  });

  test('SocialProfile is_pro bayrağını okur (kolon yoksa false)', () {
    final pro = SocialProfile.fromMap({'user_id': 'u1', 'username': 'ay', 'is_pro': true});
    expect(pro.isPro, isTrue);

    final free = SocialProfile.fromMap({'user_id': 'u2', 'username': 'gunes'});
    expect(free.isPro, isFalse);
  });
}
