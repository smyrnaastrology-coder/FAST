import 'package:flutter_test/flutter_test.dart';
import 'package:fast_app/main.dart';

void main() {
  testWidgets('App renders home screen', (WidgetTester tester) async {
    await tester.pumpWidget(const FastApp());
    expect(find.text('FAST'), findsWidgets);
    expect(find.text('Fatih Asartepe\nSinastri Tekni\u011fi'), findsOneWidget);
  });
}
