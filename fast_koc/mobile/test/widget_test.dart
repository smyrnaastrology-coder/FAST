// Fast Koç — smoke test: uygulama açılır, 7 sekme görünür.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fast_koc/main.dart';

void main() {
  testWidgets('Fast Koc acilir', (tester) async {
    await tester.pumpWidget(const FastKocApp());
    await tester.pumpAndSettle();
    expect(find.text('🚀 Fast Koç'), findsOneWidget);
    expect(find.byType(NavigationBar), findsOneWidget);
  });
}
