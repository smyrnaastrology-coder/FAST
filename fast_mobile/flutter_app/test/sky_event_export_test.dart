import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:fast_app/models/sky_event_export.dart';

void main() {
  test(
    'Takvim aktarımı UTC kullanır; UTF-8 satırları katlar ve metni kaçırır',
    () {
      final ics = buildSkyEventIcs(
        time: DateTime.utc(2026, 11, 1, 20, 15),
        title: 'Dolunay, İkizler; ${List.filled(30, 'ğ').join()}',
        description: 'Birinci satır\nİkinci satır',
        generatedAt: DateTime.utc(2026),
      );
      expect(ics, contains('DTSTART:20261101T201500Z\r\n'));
      expect(ics, contains('DTEND:20261101T211500Z\r\n'));
      final unfolded = ics.replaceAll('\r\n ', '');
      expect(unfolded, contains(r'SUMMARY:Dolunay\, İkizler\;'));
      expect(unfolded, contains(r'DESCRIPTION:Birinci satır\nİkinci satır'));
      for (final line in ics.split('\r\n')) {
        expect(utf8.encode(line).length, lessThanOrEqualTo(75));
      }
    },
  );
}
