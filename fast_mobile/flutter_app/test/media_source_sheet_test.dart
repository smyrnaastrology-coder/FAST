import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker/image_picker.dart';

import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/widgets/media_source_sheet.dart';

void main() {
  testWidgets('kaynak paneli kamera ve galeri sunar, secim dogru doner', (tester) async {
    ImageSource? picked;
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      home: Builder(
        builder: (ctx) => Scaffold(
          body: Center(
            child: TextButton(
              onPressed: () async => picked = await showMediaSourceSheet(ctx),
              child: const Text('ac'),
            ),
          ),
        ),
      ),
    ));

    await tester.tap(find.text('ac'));
    await tester.pumpAndSettle();

    expect(find.text('Kamera'), findsOneWidget);
    expect(find.text('Galeri'), findsOneWidget);

    await tester.tap(find.text('Galeri'));
    await tester.pumpAndSettle();

    expect(picked, ImageSource.gallery);
    expect(find.text('Kamera'), findsNothing);
  });
}
