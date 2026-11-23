import 'dart:async';

import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config/api_config.dart';
import '../config/theme.dart';
import '../services/api_service.dart';
import '../services/astro_consult_service.dart';
import '../widgets/chart_location_picker.dart';

/// "Astroloğa Sor" — tek soruluk danışmanlık ekranı.
///
/// Faz 1: tek astrolog. Soru gönderilir, 24 saat içinde yazılı cevap gelir.
/// Ödeme (Play IAP) henüz bağlı değil; sorular `pending_payment` olarak
/// oluşur ve ödeme doğrulaması sunucuda yapılır.
class AstroConsultScreen extends StatefulWidget {
  const AstroConsultScreen({super.key});

  @override
  State<AstroConsultScreen> createState() => _AstroConsultScreenState();
}

class _AstroConsultScreenState extends State<AstroConsultScreen> {
  final _questionCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final _birthDateCtrl = TextEditingController();

  String _topic = 'love';
  String? _astrologerId;
  Map<String, dynamic>? _astrologer;
  List<Map<String, dynamic>> _questions = const [];
  bool _loading = true;
  bool _sending = false;
  String? _error;

  // Doğum bilgisi — astrolog haritayı bununla çıkarır.
  DateTime? _birthDate;
  TimeOfDay? _birthTime;
  String? _birthPlace;
  double? _birthLat;
  double? _birthLon;
  double _birthTz = 3.0;
  bool _timezoneLoading = false;
  bool _timezoneManualOverride = false;
  String? _timezoneError;
  int _timezoneRequest = 0;
  String? _placeError;

  static const _topics = <String, Map<String, String>>{
    'love': {
      'tr': 'Aşk & ilişki',
      'en': 'Love & relationship',
      'es': 'Amor y relación',
    },
    'career': {
      'tr': 'İş & kariyer',
      'en': 'Work & career',
      'es': 'Trabajo y carrera',
    },
    'family': {'tr': 'Aile', 'en': 'Family', 'es': 'Familia'},
    'lost': {'tr': 'Kayıp', 'en': 'Lost item', 'es': 'Objeto perdido'},
    'health': {
      'tr': 'Sağlık & iyi olma',
      'en': 'Health & wellbeing',
      'es': 'Salud y bienestar',
    },
    'other': {'tr': 'Diğer', 'en': 'Other', 'es': 'Otro'},
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _questionCtrl.dispose();
    _scrollCtrl.dispose();
    _birthDateCtrl.dispose();
    super.dispose();
  }

  String _lang() => Localizations.localeOf(context).languageCode;

  String _t(String tr, String en, String es) {
    switch (_lang()) {
      case 'en':
        return en;
      case 'es':
        return es;
      default:
        return tr;
    }
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final astrologers = await AstroConsultService.astrologers();
      final questions = await AstroConsultService.myQuestions();
      if (!mounted) return;
      setState(() {
        _astrologer = astrologers.isNotEmpty ? astrologers.first : null;
        _astrologerId = _astrologer?['id'] as String?;
        _questions = questions;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _send() async {
    final text = _questionCtrl.text.trim();
    if (text.length < 20) {
      _snack(
        _t(
          'Sorunuzu en az 20 karakterle yazın.',
          'Please write at least 20 characters.',
          'Escriba al menos 20 caracteres.',
        ),
      );
      return;
    }
    if (_birthDate == null) {
      _snack(
        _t(
          'Doğum tarihinizi GG.AA.YYYY biçiminde yazın veya takvimden seçin.',
          'Enter your birth date as DD.MM.YYYY or choose it from the calendar.',
          'Escriba su fecha como DD.MM.AAAA o selecciónela en el calendario.',
        ),
      );
      return;
    }
    if (_birthTime == null) {
      _snack(
        _t(
          'Doğum saatinizi seçin.',
          'Please select your birth time.',
          'Seleccione su hora de nacimiento.',
        ),
      );
      return;
    }
    if (_birthPlace == null || _birthPlace!.isEmpty) {
      _snack(
        _t(
          'Doğum yerinizi (ülke ve şehir) seçin.',
          'Please select your birth place (country and city).',
          'Seleccione su lugar de nacimiento (país y ciudad).',
        ),
      );
      return;
    }
    if (!ApiConfig.supabaseEnabled ||
        Supabase.instance.client.auth.currentUser == null) {
      _snack(
        _t(
          'Soru sormak için giriş yapmalısınız.',
          'Please sign in to ask a question.',
          'Inicie sesión para hacer una pregunta.',
        ),
      );
      return;
    }

    setState(() => _sending = true);
    try {
      await AstroConsultService.createQuestion(
        topic: _topic,
        question: text,
        lang: _lang(),
        astrologerId: _astrologerId,
        birthDate: _birthDate!,
        birthTime: _timeText(_birthTime!),
        birthPlace: _birthPlace!,
        birthLat: _birthLat,
        birthLon: _birthLon,
        birthTz: _birthTz,
      );
      _questionCtrl.clear();
      setState(() {
        _birthDate = null;
        _birthDateCtrl.clear();
        _birthTime = null;
        _birthPlace = null;
        _birthLat = null;
        _birthLon = null;
        _birthTz = 3.0;
        _timezoneLoading = false;
        _timezoneManualOverride = false;
        _timezoneError = null;
        _timezoneRequest++;
        _placeError = null;
      });
      await _load();
      if (!mounted) return;
      _snack(
        _t(
          'Sorunuz alındı. 24 saat içinde yazılı cevap gelecek.',
          'Your question is received. A written answer will arrive within 24 hours.',
          'Su pregunta fue recibida. La respuesta llegará en 24 horas.',
        ),
      );
    } catch (e) {
      _snack(e.toString());
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  void _snack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  String _timeText(TimeOfDay t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  String _dateText(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}.${d.month.toString().padLeft(2, '0')}.${d.year}';

  DateTime? _parseBirthDate(String value) {
    final raw = value.trim();
    if (raw.isEmpty) return null;

    int? year;
    int? month;
    int? day;

    final numeric = RegExp(
      r'^(\d{1,4})[./\-\s]+(\d{1,2})[./\-\s]+(\d{1,4})$',
    ).firstMatch(raw);
    if (numeric != null) {
      final a = int.tryParse(numeric.group(1)!);
      final b = int.tryParse(numeric.group(2)!);
      final c = int.tryParse(numeric.group(3)!);
      if (a == null || b == null || c == null) return null;
      if (numeric.group(1)!.length == 4) {
        year = a;
        month = b;
        day = c;
      } else {
        day = a;
        month = b;
        year = c;
      }
    } else {
      final words = raw
          .toLowerCase()
          .replaceAll(',', ' ')
          .split(RegExp(r'\s+'))
          .where((word) => word.isNotEmpty)
          .toList();
      if (words.length != 3) return null;
      const monthNames = <String, int>{
        'ocak': 1,
        'january': 1,
        'enero': 1,
        'şubat': 2,
        'subat': 2,
        'february': 2,
        'febrero': 2,
        'mart': 3,
        'march': 3,
        'marzo': 3,
        'nisan': 4,
        'april': 4,
        'abril': 4,
        'mayıs': 5,
        'mayis': 5,
        'may': 5,
        'mayo': 5,
        'haziran': 6,
        'june': 6,
        'junio': 6,
        'temmuz': 7,
        'july': 7,
        'julio': 7,
        'ağustos': 8,
        'agustos': 8,
        'august': 8,
        'agosto': 8,
        'eylül': 9,
        'eylul': 9,
        'september': 9,
        'septiembre': 9,
        'ekim': 10,
        'october': 10,
        'octubre': 10,
        'kasım': 11,
        'kasim': 11,
        'november': 11,
        'noviembre': 11,
        'aralık': 12,
        'aralik': 12,
        'december': 12,
        'diciembre': 12,
      };
      final firstMonth = monthNames[words[0]];
      final secondMonth = monthNames[words[1]];
      if (firstMonth != null) {
        month = firstMonth;
        day = int.tryParse(words[1]);
        year = int.tryParse(words[2]);
      } else if (secondMonth != null) {
        day = int.tryParse(words[0]);
        month = secondMonth;
        year = int.tryParse(words[2]);
      } else {
        return null;
      }
    }

    if (year == null ||
        day == null ||
        year < 1900 ||
        year > DateTime.now().year) {
      return null;
    }
    final parsed = DateTime(year, month, day);
    if (parsed.year != year ||
        parsed.month != month ||
        parsed.day != day ||
        parsed.isAfter(DateTime.now())) {
      return null;
    }
    return parsed;
  }

  void _onBirthDateChanged(String value) {
    final parsed = _parseBirthDate(value);
    setState(() {
      _birthDate = parsed;
      if (parsed != null) _timezoneManualOverride = false;
    });
    unawaited(_refreshBirthTimezone());
  }

  String _utcLabel(double v) {
    final totalMinutes = (v * 60).round();
    final sign = totalMinutes < 0 ? '-' : '+';
    final absoluteMinutes = totalMinutes.abs();
    final hours = absoluteMinutes ~/ 60;
    final minutes = absoluteMinutes % 60;
    return 'UTC$sign$hours'
        '${minutes == 0 ? '' : ':${minutes.toString().padLeft(2, '0')}'}';
  }

  Future<void> _refreshBirthTimezone() async {
    final request = ++_timezoneRequest;
    final date = _birthDate;
    final lat = _birthLat;
    final lon = _birthLon;
    if (date == null || lat == null || lon == null) {
      if (mounted) {
        setState(() {
          _timezoneLoading = false;
          _timezoneError = null;
        });
      }
      return;
    }
    if (_timezoneLoading) {
      _snack(
        _t(
          'Doğum yeriniz için UTC hesaplanıyor; lütfen bekleyin.',
          'Calculating UTC for your birth place; please wait.',
          'Calculando UTC para su lugar de nacimiento; espere.',
        ),
      );
      return;
    }
    if (_timezoneError != null && !_timezoneManualOverride) {
      _snack(_timezoneError!);
      return;
    }

    setState(() {
      _timezoneLoading = true;
      _timezoneManualOverride = false;
      _timezoneError = null;
    });
    try {
      final result = await ApiService().birthTimezone(
        lat: lat,
        lon: lon,
        birthDate: date,
        birthTime: _timeText(
          _birthTime ?? const TimeOfDay(hour: 12, minute: 0),
        ),
      );
      final offset = (result['utc_offset'] as num).toDouble();
      if (!mounted || request != _timezoneRequest) return;
      setState(() {
        _birthTz = offset;
        _timezoneLoading = false;
        _timezoneError = null;
      });
    } catch (_) {
      if (!mounted || request != _timezoneRequest) return;
      setState(() {
        _timezoneLoading = false;
        _timezoneError = _t(
          'UTC otomatik hesaplanamadı; listeden elle seçebilirsiniz.',
          'Could not detect UTC automatically; choose it from the list.',
          'No se pudo detectar UTC; selecciónelo manualmente.',
        );
      });
    }
  }

  Future<void> _pickBirthDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _birthDate ?? DateTime(now.year - 30, now.month, now.day),
      firstDate: DateTime(1900),
      lastDate: now,
      helpText: _t('Doğum tarihi', 'Birth date', 'Fecha de nacimiento'),
    );
    if (picked != null && mounted) {
      setState(() {
        _birthDate = picked;
        _birthDateCtrl.text = _dateText(picked);
        _timezoneManualOverride = false;
      });
      unawaited(_refreshBirthTimezone());
    }
  }

  Future<void> _pickBirthTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _birthTime ?? const TimeOfDay(hour: 12, minute: 0),
      helpText: _t('Doğum saati', 'Birth time', 'Hora de nacimiento'),
    );
    if (picked != null && mounted) {
      setState(() {
        _birthTime = picked;
        _timezoneManualOverride = false;
      });
      unawaited(_refreshBirthTimezone());
    }
  }

  Future<void> _openPdf(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) return;
    try {
      final ok = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!ok) _snack(url);
    } catch (_) {
      _snack(url);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bgSecondary,
        elevation: 0,
        title: Text(
          _t(
            "Astrolog Fatih Asartepe'ye Sor",
            'Ask Astrologer Fatih Asartepe',
            'Pregunta a Fatih Asartepe',
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: FastTheme.accentGold,
            fontSize: 16,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                controller: _scrollCtrl,
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 32),
                children: [
                  _introCard(),
                  const SizedBox(height: 18),
                  _form(),
                  const SizedBox(height: 26),
                  if (_questions.isNotEmpty) ...[
                    Text(
                      _t('Sorularım', 'My questions', 'Mis preguntas'),
                      style: TextStyle(
                        color: FastTheme.text,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 10),
                    ..._questions.map(_questionCard),
                  ],
                  if (_error != null) ...[
                    const SizedBox(height: 14),
                    Text(
                      _error!,
                      style: TextStyle(
                        color: FastTheme.textMuted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _introCard() {
    final name = (_astrologer?['display_name'] as String?) ?? 'Fatih Asartepe';
    final headline =
        (_astrologer?['headline'] as String?) ??
        _t('Karma Astrolog', 'Karma Astrologer', 'Astrólogo Kármico');
    final photo = _astrologer?['photo_url'] as String?;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            FastTheme.accentGold.withValues(alpha: 0.28),
            FastTheme.accentGold.withValues(alpha: 0.06),
          ],
        ),
        border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.45)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(2),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: FastTheme.accentGold.withValues(alpha: 0.8),
                    width: 1.5,
                  ),
                ),
                child: CircleAvatar(
                  radius: 31,
                  backgroundColor: FastTheme.cardBg,
                  backgroundImage: photo != null && photo.isNotEmpty
                      ? NetworkImage(photo)
                      : const AssetImage('assets/astrolog_fatih.jpeg'),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: TextStyle(
                        color: FastTheme.text,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      headline,
                      style: TextStyle(
                        color: FastTheme.textMuted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.verified, color: FastTheme.accentGold, size: 20),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Icon(Icons.schedule, size: 16, color: FastTheme.accentGold),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  _t(
                    '24 saat içinde yazılı cevap · cevap gelmezse ücret iadesi',
                    'Written answer within 24 hours · full refund if unanswered',
                    'Respuesta escrita en 24 horas · reembolso si no hay respuesta',
                  ),
                  style: TextStyle(color: FastTheme.textMuted, fontSize: 12),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _form() {
    final price = AstroConsultService.singleQuestionPrice;
    final priceText = '${price.toStringAsFixed(2).replaceAll('.', ',')} ₺';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          _t('Konu', 'Topic', 'Tema'),
          style: TextStyle(
            color: FastTheme.text,
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _topics.entries.map((entry) {
            final selected = _topic == entry.key;
            return ChoiceChip(
              label: Text(entry.value[_lang()] ?? entry.value['tr']!),
              selected: selected,
              onSelected: (_) => setState(() => _topic = entry.key),
              selectedColor: FastTheme.accentGold.withValues(alpha: 0.25),
              backgroundColor: FastTheme.cardBg,
              labelStyle: TextStyle(
                color: selected ? FastTheme.accentGold : FastTheme.textMuted,
                fontSize: 12,
                fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
              ),
              side: BorderSide(
                color: selected
                    ? FastTheme.accentGold.withValues(alpha: 0.6)
                    : FastTheme.border,
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 16),
        _birthSection(),
        const SizedBox(height: 16),
        TextField(
          controller: _questionCtrl,
          maxLines: 5,
          maxLength: 2000,
          style: TextStyle(color: FastTheme.text),
          decoration: InputDecoration(
            hintText: _t(
              'Sorunuzu tek ve net biçimde yazın. Örnek: "Bu ilişki evliliğe gider mi?"',
              'Write one clear question. Example: "Will this relationship lead to marriage?"',
              'Escriba una pregunta clara. Ejemplo: "¿Esta relación llevará al matrimonio?"',
            ),
            hintStyle: TextStyle(color: FastTheme.textMuted, fontSize: 13),
            filled: true,
            fillColor: FastTheme.cardBg,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: FastTheme.border),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: FastTheme.border),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: FastTheme.accentGold),
            ),
          ),
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: FastTheme.cardBg,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: FastTheme.border),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _t(
                        'Tek soru danışmanlığı',
                        'Single-question consultation',
                        'Consulta de una pregunta',
                      ),
                      style: TextStyle(
                        color: FastTheme.textMuted,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      priceText,
                      style: TextStyle(
                        color: FastTheme.text,
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
              FilledButton(
                onPressed: _sending ? null : _send,
                style: FilledButton.styleFrom(
                  backgroundColor: FastTheme.accentGold,
                  foregroundColor: FastTheme.bg,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 22,
                    vertical: 14,
                  ),
                ),
                child: _sending
                    ? SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: FastTheme.bg,
                        ),
                      )
                    : Text(
                        _t('Sor', 'Ask', 'Preguntar'),
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _birthSection() {
    final tzOptions = <double>{
      ...List<double>.generate(105, (i) => -12 + i * 0.25),
      _birthTz,
    }.toList()..sort();
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: FastTheme.cardBg.withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: FastTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.cake_outlined, size: 16, color: FastTheme.accentGold),
              const SizedBox(width: 6),
              Text(
                _t('Doğum Bilgileri', 'Birth details', 'Datos de nacimiento'),
                style: TextStyle(
                  color: FastTheme.text,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            _t(
              'Haritanızın doğru çıkması için gerçek doğum tarihi, saati ve yerinizi girin.',
              'For an accurate chart, enter your real birth date, time and place.',
              'Para una carta precisa, introduzca su fecha, hora y lugar reales de nacimiento.',
            ),
            style: TextStyle(color: FastTheme.textMuted, fontSize: 11),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _birthDateCtrl,
                  keyboardType: TextInputType.datetime,
                  onChanged: _onBirthDateChanged,
                  style: TextStyle(color: FastTheme.text, fontSize: 13),
                  decoration: InputDecoration(
                    labelText: _t('Doğum tarihi', 'Birth date', 'Fecha'),
                    hintText: _t('17.07.1995', '17.07.1995', '17.07.1995'),
                    errorText:
                        _birthDateCtrl.text.trim().isNotEmpty &&
                            _birthDate == null
                        ? _t(
                            'Tarihi kontrol edin',
                            'Check the date',
                            'Revise la fecha',
                          )
                        : null,
                    suffixIcon: IconButton(
                      tooltip: _t(
                        'Takvimden seç',
                        'Choose from calendar',
                        'Elegir del calendario',
                      ),
                      onPressed: _pickBirthDate,
                      icon: Icon(
                        Icons.calendar_today,
                        size: 17,
                        color: FastTheme.accentGold,
                      ),
                    ),
                    filled: true,
                    fillColor: FastTheme.cardBg,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 12,
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: FastTheme.border),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: FastTheme.border),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _fieldBox(
                  label: _t('Saat', 'Time', 'Hora'),
                  value: _birthTime == null ? null : _timeText(_birthTime!),
                  hint: _t('ss:dd', 'hh:mm', 'hh:mm'),
                  icon: Icons.access_time,
                  onTap: _pickBirthTime,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          DropdownButtonFormField<double>(
            initialValue: tzOptions.contains(_birthTz) ? _birthTz : 3.0,
            isExpanded: true,
            dropdownColor: FastTheme.cardBg,
            style: TextStyle(color: FastTheme.text, fontSize: 13),
            decoration: InputDecoration(
              labelText: _t(
                'UTC saat dilimi',
                'UTC time zone',
                'Zona horaria UTC',
              ),
              labelStyle: TextStyle(color: FastTheme.textMuted, fontSize: 12),
              filled: true,
              fillColor: FastTheme.cardBg,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 4,
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: FastTheme.border),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: FastTheme.border),
              ),
            ),
            items: tzOptions
                .map(
                  (v) => DropdownMenuItem<double>(
                    value: v,
                    child: Text(_utcLabel(v)),
                  ),
                )
                .toList(),
            onChanged: (v) {
              if (v != null) {
                setState(() {
                  _timezoneRequest++;
                  _birthTz = v;
                  _timezoneManualOverride = true;
                  _timezoneLoading = false;
                  _timezoneError = null;
                });
              }
            },
          ),
          const SizedBox(height: 4),
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              _timezoneLoading
                  ? _t(
                      'Konum ve doğum tarihine göre hesaplanıyor…',
                      'Calculating from birth place and date…',
                      'Calculando según el lugar y fecha…',
                    )
                  : _timezoneError ??
                        (_timezoneManualOverride
                            ? _t(
                                'Saat dilimini elle seçtiniz.',
                                'Time zone selected manually.',
                                'Zona horaria seleccionada manualmente.',
                              )
                            : _t(
                                'Doğum tarihi ve yeri girilince otomatik seçilir.',
                                'Detected automatically after entering date and place.',
                                'Se detecta al introducir fecha y lugar.',
                              )),
              style: TextStyle(
                color: _timezoneError == null
                    ? FastTheme.textMuted
                    : Colors.orangeAccent,
                fontSize: 10,
              ),
            ),
          ),
          const SizedBox(height: 10),
          ChartLocationPicker(
            onSelected: (place, lat, lon) {
              setState(() {
                _birthPlace = place;
                _birthLat = lat;
                _birthLon = lon;
                _timezoneManualOverride = false;
                _placeError = null;
              });
              unawaited(_refreshBirthTimezone());
            },
            onPending: () {
              setState(() {
                _birthPlace = null;
                _birthLat = null;
                _birthLon = null;
                _timezoneRequest++;
                _timezoneLoading = false;
                _timezoneError = null;
                _timezoneManualOverride = false;
              });
            },
          ),
          if (_placeError != null) ...[
            const SizedBox(height: 6),
            Text(
              _placeError!,
              style: const TextStyle(color: Colors.redAccent, fontSize: 11),
            ),
          ],
          if (_birthPlace != null &&
              _birthLat != null &&
              _birthLon != null) ...[
            const SizedBox(height: 8),
            Text(
              '${_birthPlace!} · ${_birthLat!.toStringAsFixed(4)}, '
              '${_birthLon!.toStringAsFixed(4)}',
              style: TextStyle(color: FastTheme.textMuted, fontSize: 11),
            ),
          ],
        ],
      ),
    );
  }

  Widget _fieldBox({
    required String label,
    required String hint,
    required IconData icon,
    required VoidCallback onTap,
    String? value,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          labelStyle: TextStyle(color: FastTheme.textMuted, fontSize: 12),
          prefixIcon: Icon(icon, size: 16, color: FastTheme.accentGold),
          filled: true,
          fillColor: FastTheme.cardBg,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 12,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: FastTheme.border),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: FastTheme.border),
          ),
        ),
        child: Text(
          value ?? hint,
          style: TextStyle(
            color: value == null ? FastTheme.textMuted : FastTheme.text,
            fontSize: 13,
          ),
        ),
      ),
    );
  }

  String _birthSummary(Map<String, dynamic> q) {
    final rawDate = (q['birth_date'] as String?) ?? '';
    String date = rawDate;
    final parts = rawDate.split('-');
    if (parts.length == 3) date = '${parts[2]}.${parts[1]}.${parts[0]}';
    final time = (q['birth_time'] as String?) ?? '';
    final place = (q['birth_place'] as String?) ?? '';
    return [date, time, place].where((s) => s.isNotEmpty).join(' · ');
  }

  Widget _questionCard(Map<String, dynamic> q) {
    final status = (q['status'] as String?) ?? 'pending_payment';
    final answer = (q['answer_text'] as String?)?.trim();
    final pdfUrl = (q['answer_pdf_url'] as String?)?.trim();
    final hasPdf = pdfUrl != null && pdfUrl.isNotEmpty;
    final rating = q['rating'] as int?;
    final created = DateTime.tryParse((q['created_at'] as String?) ?? '');

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: FastTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  (q['question'] as String?) ?? '',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: FastTheme.text,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              _statusChip(status),
            ],
          ),
          if (created != null) ...[
            const SizedBox(height: 6),
            Text(
              created.toLocal().toString().substring(0, 16),
              style: TextStyle(color: FastTheme.textMuted, fontSize: 11),
            ),
          ],
          if ((q['birth_date'] as String?) != null) ...[
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.cake_outlined, size: 12, color: FastTheme.textMuted),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    _birthSummary(q),
                    style: TextStyle(color: FastTheme.textMuted, fontSize: 11),
                  ),
                ),
              ],
            ),
          ],
          if (answer != null && answer.isNotEmpty) ...[
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: FastTheme.bgSecondary,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                answer,
                style: TextStyle(
                  color: FastTheme.text,
                  fontSize: 13,
                  height: 1.45,
                ),
              ),
            ),
          ],
          if (hasPdf) ...[
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () => _openPdf(pdfUrl),
              icon: Icon(
                Icons.picture_as_pdf,
                size: 18,
                color: FastTheme.accentGold,
              ),
              label: Text(
                ((q['answer_pdf_name'] as String?) ?? '').isNotEmpty
                    ? (q['answer_pdf_name'] as String)
                    : _t('PDF cevabı aç', 'Open PDF answer', 'Abrir PDF'),
                style: TextStyle(color: FastTheme.accentGold, fontSize: 12),
              ),
              style: OutlinedButton.styleFrom(
                side: BorderSide(
                  color: FastTheme.accentGold.withValues(alpha: 0.5),
                ),
              ),
            ),
          ],
          if (answer != null && answer.isNotEmpty && rating == null)
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () => _rateDialog(q['id'] as String),
                icon: Icon(
                  Icons.star_outline,
                  size: 18,
                  color: FastTheme.accentGold,
                ),
                label: Text(
                  _t('Puanla', 'Rate', 'Calificar'),
                  style: TextStyle(color: FastTheme.accentGold),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _statusChip(String status) {
    final label = switch (status) {
      'open' => _t('Cevap bekliyor', 'Awaiting answer', 'Esperando respuesta'),
      'answered' => _t('Cevaplandı', 'Answered', 'Respondida'),
      'closed' => _t('Tamamlandı', 'Completed', 'Completada'),
      'refunded' => _t('İade edildi', 'Refunded', 'Reembolsada'),
      'expired' => _t('Süre doldu', 'Expired', 'Expirada'),
      _ => _t('Ödeme bekliyor', 'Awaiting payment', 'Esperando pago'),
    };
    final color = switch (status) {
      'answered' || 'closed' => FastTheme.accentGold,
      'refunded' || 'expired' => Colors.orangeAccent,
      _ => FastTheme.textMuted,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Future<void> _rateDialog(String questionId) async {
    var stars = 5;
    final noteCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          backgroundColor: FastTheme.cardBg,
          title: Text(
            _t('Cevabı puanla', 'Rate the answer', 'Califica la respuesta'),
            style: TextStyle(color: FastTheme.text, fontSize: 16),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(5, (i) {
                  return IconButton(
                    onPressed: () => setDialogState(() => stars = i + 1),
                    icon: Icon(
                      i < stars ? Icons.star : Icons.star_border,
                      color: FastTheme.accentGold,
                    ),
                  );
                }),
              ),
              TextField(
                controller: noteCtrl,
                maxLines: 3,
                style: TextStyle(color: FastTheme.text),
                decoration: InputDecoration(
                  hintText: _t(
                    'Not (isteğe bağlı)',
                    'Note (optional)',
                    'Nota (opcional)',
                  ),
                  hintStyle: TextStyle(
                    color: FastTheme.textMuted,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: Text(_t('Vazgeç', 'Cancel', 'Cancelar')),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              style: FilledButton.styleFrom(
                backgroundColor: FastTheme.accentGold,
              ),
              child: Text(
                _t('Gönder', 'Send', 'Enviar'),
                style: TextStyle(color: FastTheme.bg),
              ),
            ),
          ],
        ),
      ),
    );
    if (ok == true) {
      try {
        await AstroConsultService.rate(
          questionId: questionId,
          rating: stars,
          note: noteCtrl.text.trim().isEmpty ? null : noteCtrl.text.trim(),
        );
        await _load();
      } catch (e) {
        _snack(e.toString());
      }
    }
    noteCtrl.dispose();
  }
}
