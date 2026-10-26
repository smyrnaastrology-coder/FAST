import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fast_app/config/theme.dart';
import 'package:fast_app/l10n/app_localizations.dart';
import 'package:fast_app/models/chart_data.dart';
import 'package:fast_app/models/chart_frame.dart';
import 'package:fast_app/screens/chart_explorer_screen.dart';

void main() {
  test('Ay/yıl adımları ay sonunu, artık yılı ve saati korur', () {
    expect(
      stepChartTime(DateTime(2024, 1, 31, 23, 14), ChartTimeUnit.month, 1),
      DateTime(2024, 2, 29, 23, 14),
    );
    expect(
      stepChartTime(DateTime(2024, 2, 29, 23, 14), ChartTimeUnit.year, 1),
      DateTime(2025, 2, 28, 23, 14),
    );
    expect(
      stepChartTime(DateTime(2026, 1, 31), ChartTimeUnit.month, -2),
      DateTime(2025, 11, 30),
    );
    expect(
      stepChartTime(DateTime(1986, 10, 8, 23, 14), ChartTimeUnit.year, 30),
      DateTime(2016, 10, 8, 23, 14),
    );
    expect(
      stepChartTime(
        DateTime.utc(2024, 12, 31, 23, 59),
        ChartTimeUnit.minute,
        2,
      ),
      DateTime.utc(2025, 1, 1, 0, 1),
    );
  });

  testWidgets(
    'Tam ekran kapanmadan ileri/geri hesaplanır; tema uygulamayı değiştirmez',
    (tester) async {
      final data = ChartData.fromJson({
        'meta': {'tarih': '1986-10-08', 'saat': '23:14'},
      });
      final requests = <DateTime>[];
      final appBg = FastTheme.bg;
      await tester.pumpWidget(
        MaterialApp(
          locale: const Locale('tr'),
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: AppLocalizations.supportedLocales,
          home: ChartExplorerScreen(
            initial: ChartFrame(data: data, title: 'Natal'),
            initialDate: DateTime(2024, 1, 31),
            loadFrame: (date) async {
              requests.add(date);
              return ChartFrame(data: data, title: 'Güncellendi');
            },
          ),
        ),
      );
      await tester.tap(find.byTooltip('İleri'));
      await tester.pump(const Duration(milliseconds: 200));
      await tester.pumpAndSettle();
      expect(requests.last, DateTime(2024, 2, 1));
      expect(find.byType(ChartExplorerScreen), findsOneWidget);
      await tester.tap(find.byTooltip('Geri'));
      await tester.pump(const Duration(milliseconds: 200));
      await tester.pumpAndSettle();
      expect(requests, hasLength(1)); // Back to a cached frame is immediate.
      expect(find.text('31.01.2024 00:00'), findsWidgets);
      await tester.tap(find.byTooltip('Harita: siyah / beyaz'));
      await tester.pumpAndSettle();
      expect(
        tester.widget<Scaffold>(find.byType(Scaffold)).backgroundColor,
        Colors.white,
      );
      expect(FastTheme.bg, appBg);
      expect(tester.takeException(), isNull);
    },
  );
}
