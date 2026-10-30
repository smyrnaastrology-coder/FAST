import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:fast_app/screens/story_editor_screen.dart';
import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/services/story_draft_service.dart';
import 'package:fast_app/widgets/story_text_layer.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory dir;
  late File photo;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('story_test_');
    photo = File('${dir.path}/image.png');
    await photo.writeAsBytes(
      base64Decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/aXcAAAAASUVORK5CYII=',
      ),
    );
    SharedPreferences.setMockInitialValues({});
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/path_provider'),
          (call) async => dir.path,
        );
    GoogleFonts.config.allowRuntimeFetching = false;
  });

  tearDown(() async {
    GoogleFonts.config.allowRuntimeFetching = true;
    try {
      await dir.delete(recursive: true);
    } on FileSystemException {
      // Windows can keep a decoded image file open until the test exits.
    }
  });

  testWidgets(
    'text layer is positioned directly in stack and back asks before exiting',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          locale: const Locale('tr'),
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          home: StoryEditorScreen(imageFile: XFile(photo.path)),
        ),
      );
      await tester.tap(find.text('Metin'));
      await tester.pump();
      expect(tester.takeException(), isNull);
      expect(find.byType(StoryTextLayerWidget), findsOneWidget);
      await tester.enterText(find.byType(TextField), 'Merhaba');
      await tester.pump();
      expect(find.text('Merhaba'), findsWidgets);
      await tester.binding.handlePopRoute();
      await tester.pumpAndSettle();
      expect(find.text('Düzenlemeleri sil?'), findsOneWidget);
      await tester.tap(find.text('Düzenlemeye devam et'));
      await tester.pumpAndSettle();
      expect(find.text('Merhaba'), findsWidgets);
    },
  );

  testWidgets('draft saves editable text and restores it', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('tr'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: Builder(
          builder: (context) => TextButton(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute<void>(
                builder: (_) => StoryEditorScreen(imageFile: XFile(photo.path)),
              ),
            ),
            child: const Text('Aç'),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Aç'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Metin'));
    await tester.pump();
    await tester.enterText(find.byType(TextField), 'Taslak yazısı');
    await tester.pump();
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Taslağı kaydet'));
    await tester.pumpAndSettle();
    await tester.runAsync(() async {
      await Future<void>.delayed(const Duration(milliseconds: 100));
    });
    await tester.pumpAndSettle();
    final draft = await tester.runAsync(StoryDraftService.load);
    expect(draft, isNotNull);
    expect((draft!['texts'] as List).single['text'], 'Taslak yazısı');
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('tr'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: StoryEditorScreen(
          imageFile: XFile(draft['image'] as String),
          draft: draft,
        ),
      ),
    );
    await tester.pump();
    expect(find.text('Taslak yazısı'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  for (final example in [
    ('en', 'Discard edits?', 'Save draft', 'Keep editing'),
    ('es', '¿Descartar los cambios?', 'Guardar borrador', 'Seguir editando'),
  ]) {
    testWidgets('exit dialog uses ${example.$1} locale', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          locale: Locale(example.$1),
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          home: StoryEditorScreen(imageFile: XFile(photo.path)),
        ),
      );
      await tester.binding.handlePopRoute();
      await tester.pumpAndSettle();
      expect(find.text(example.$2), findsOneWidget);
      expect(find.text(example.$3), findsOneWidget);
      expect(find.text(example.$4), findsOneWidget);
    });
  }
}
