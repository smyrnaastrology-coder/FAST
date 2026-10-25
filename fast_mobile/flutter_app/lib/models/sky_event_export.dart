import 'dart:convert';

String _escapeIcs(String text) => text
    .replaceAll('\\', '\\\\')
    .replaceAll('\r\n', '\n')
    .replaceAll('\r', '\n')
    .replaceAll('\n', r'\n')
    .replaceAll(';', r'\;')
    .replaceAll(',', r'\,');

String _foldIcs(String line) {
  final out = StringBuffer();
  var length = 0;
  for (final rune in line.runes) {
    final char = String.fromCharCode(rune);
    final bytes = utf8.encode(char).length;
    if (length + bytes > 75) {
      out.write('\r\n ');
      length = 1;
    }
    out.write(char);
    length += bytes;
  }
  return out.toString();
}

String _icsDate(DateTime time) =>
    '${time.toUtc().toIso8601String().split('.').first.replaceAll('-', '').replaceAll(':', '')}Z';

/// UTC calendar event, importable without calendar permissions. No device-local
/// offset is baked in; the receiving calendar displays it in its own timezone.
String buildSkyEventIcs({
  required DateTime time,
  required String title,
  required String description,
  DateTime? generatedAt,
}) {
  final lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Holavon//Sky Calendar//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    'UID:sky-${time.toUtc().millisecondsSinceEpoch}-${base64Url.encode(utf8.encode(title)).replaceAll('=', '')}@holavon',
    'DTSTAMP:${_icsDate(generatedAt ?? DateTime.now())}',
    'DTSTART:${_icsDate(time)}',
    'DTEND:${_icsDate(time.add(const Duration(hours: 1)))}',
    'SUMMARY:${_escapeIcs(title)}',
    'DESCRIPTION:${_escapeIcs(description)}',
    'END:VEVENT',
    'END:VCALENDAR',
  ];
  return '${lines.map(_foldIcs).join('\r\n')}\r\n';
}
