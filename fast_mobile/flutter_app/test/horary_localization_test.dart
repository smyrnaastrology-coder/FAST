import 'package:fast_app/l10n/app_localizations_en.dart';
import 'package:fast_app/l10n/app_localizations_es.dart';
import 'package:fast_app/l10n/app_localizations_tr.dart';
import 'package:fast_app/services/horary_localization.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final en = AppLocalizationsEn();
  final es = AppLocalizationsEs();
  final tr = AppLocalizationsTr();

  test('translates signs without changing the astrological value', () {
    expect(localizeHorarySign('Yay', es), 'Sagitario');
    expect(localizeHorarySign('Yay', en), 'Sagittarius');
    expect(localizeHorarySign('Oğlak', es), 'Capricornio');
    expect(localizeHorarySign('Yay', tr), 'Yay');
    expect(localizeHoraryVerdict('YES', es), 'Sí');
    expect(localizeHoraryVerdict('UNCERTAIN', tr), 'Belirsiz');
  });

  test('translates timing units while retaining numbers and ranges', () {
    expect(localizeHoraryTiming({'text': '46 SAAT'}, es), '46 horas');
    expect(localizeHoraryTiming({'text': '1 GÜN'}, en), '1 day');
    expect(localizeHoraryTiming({'text': '2-5 AY'}, es), '2-5 meses');
    expect(localizeHoraryTiming({'text': '12 HAFTA'}, tr), '12 hafta');
    expect(localizeHoraryTiming({'text': 'unknown'}, es), isNull);
  });
}
