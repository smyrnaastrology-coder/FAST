import '../l10n/app_localizations.dart';

String localizeHoraryVerdict(String verdict, AppLocalizations l10n) {
  return switch (verdict.trim().toUpperCase()) {
    'YES' || 'EVET' => l10n.horaryVerdictYes,
    'NO' || 'HAYIR' => l10n.horaryVerdictNo,
    'UNCERTAIN' || 'BELIRSIZ' || 'BELİRSİZ' => l10n.horaryVerdictUncertain,
    _ => verdict,
  };
}

String localizeHorarySign(String sign, AppLocalizations l10n) {
  final signs = {
    'koç': l10n.chartSignAries,
    'aries': l10n.chartSignAries,
    'boğa': l10n.chartSignTaurus,
    'taurus': l10n.chartSignTaurus,
    'ikizler': l10n.chartSignGemini,
    'gemini': l10n.chartSignGemini,
    'yengeç': l10n.chartSignCancer,
    'cancer': l10n.chartSignCancer,
    'aslan': l10n.chartSignLeo,
    'leo': l10n.chartSignLeo,
    'başak': l10n.chartSignVirgo,
    'virgo': l10n.chartSignVirgo,
    'terazi': l10n.chartSignLibra,
    'libra': l10n.chartSignLibra,
    'akrep': l10n.chartSignScorpio,
    'scorpio': l10n.chartSignScorpio,
    'yay': l10n.chartSignSagittarius,
    'sagittarius': l10n.chartSignSagittarius,
    'oğlak': l10n.chartSignCapricorn,
    'capricorn': l10n.chartSignCapricorn,
    'kova': l10n.chartSignAquarius,
    'aquarius': l10n.chartSignAquarius,
    'balık': l10n.chartSignPisces,
    'pisces': l10n.chartSignPisces,
  };
  return signs[sign.trim().toLowerCase()] ?? sign;
}

/// Format the engine's numeric timing without altering the value or range.
String? localizeHoraryTiming(Map timing, AppLocalizations l10n) {
  final text = (timing['text'] ?? '').toString().trim();
  final match = RegExp(
    r'^(\d+(?:[.,]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?)\s*([\p{L}]+)\s*$',
    unicode: true,
  ).firstMatch(text);
  if (match == null) return null;
  final unit = match.group(2)!.toLowerCase();
  final String? translated = switch (unit) {
    'dakika' ||
    'minute' ||
    'minutes' ||
    'minuto' ||
    'minutos' => l10n.horaryMinute,
    'saat' || 'hour' || 'hours' || 'hora' || 'horas' => l10n.horaryHour,
    'gün' ||
    'gun' ||
    'day' ||
    'days' ||
    'día' ||
    'días' ||
    'dia' ||
    'dias' => l10n.horaryDay,
    'hafta' || 'week' || 'weeks' || 'semana' || 'semanas' => l10n.horaryWeek,
    'ay' || 'month' || 'months' || 'mes' || 'meses' => l10n.horaryMonth,
    'yıl' || 'yil' || 'year' || 'years' || 'año' || 'años' => l10n.horaryYear,
    _ => null,
  };
  if (translated == null) return null;
  final value = match.group(1)!;
  final plural =
      !l10n.localeName.startsWith('tr') &&
      (value.contains(RegExp(r'[-–]')) ||
          double.tryParse(value.replaceAll(',', '.')) != 1);
  final suffix = !plural
      ? ''
      : (l10n.localeName.startsWith('es') && translated == 'mes' ? 'es' : 's');
  return '$value $translated$suffix';
}
