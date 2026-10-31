import 'package:fast_app/widgets/place_suggest_field.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final query in ['Priştine', 'Pristina', 'Prishtina', 'Prishtinë', 'Phriştine']) {
    testWidgets('city picker finds Priştine with $query', (tester) async {
      String? selected;
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: PlaceSuggestField(
        label: 'City', options: const ['Priştine'], displayOf: (s) => s,
        onSelected: (value) => selected = value,
      ))));
      await tester.enterText(find.byType(TextField), query);
      await tester.pump();
      await tester.tap(find.text('Priştine').last);
      expect(selected, 'Priştine');
    });
  }
}
