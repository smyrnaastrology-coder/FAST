import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../config/api_config.dart';
import '../config/theme.dart';
import '../services/astro_consult_service.dart';

/// "AstroloÄŸa Sor" â€” tek soruluk danÄ±ÅŸmanlÄ±k ekranÄ±.
///
/// Faz 1: tek astrolog. Soru gÃ¶nderilir, 24 saat iÃ§inde yazÄ±lÄ± cevap gelir.
/// Ã–deme (Play IAP) henÃ¼z baÄŸlÄ± deÄŸil; sorular `pending_payment` olarak
/// oluÅŸur ve Ã¶deme doÄŸrulamasÄ± sunucuda yapÄ±lÄ±r.
class AstroConsultScreen extends StatefulWidget {
  const AstroConsultScreen({super.key});

  @override
  State<AstroConsultScreen> createState() => _AstroConsultScreenState();
}

class _AstroConsultScreenState extends State<AstroConsultScreen> {
  final _questionCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  String _topic = 'love';
  String? _astrologerId;
  Map<String, dynamic>? _astrologer;
  List<Map<String, dynamic>> _questions = const [];
  bool _loading = true;
  bool _sending = false;
  String? _error;

  static const _topics = <String, Map<String, String>>{
    'love': {
      'tr': 'AÅŸk & iliÅŸki',
      'en': 'Love & relationship',
      'es': 'Amor y relaciÃ³n',
    },
    'career': {
      'tr': 'Ä°ÅŸ & kariyer',
      'en': 'Work & career',
      'es': 'Trabajo y carrera',
    },
    'family': {'tr': 'Aile', 'en': 'Family', 'es': 'Familia'},
    'lost': {'tr': 'KayÄ±p', 'en': 'Lost item', 'es': 'Objeto perdido'},
    'health': {
      'tr': 'SaÄŸlÄ±k & iyi olma',
      'en': 'Health & wellbeing',
      'es': 'Salud y bienestar',
    },
    'other': {'tr': 'DiÄŸer', 'en': 'Other', 'es': 'Otro'},
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
          'Sorunuzu en az 20 karakterle yazÄ±n.',
          'Please write at least 20 characters.',
          'Escriba al menos 20 caracteres.',
        ),
      );
      return;
    }
    if (!ApiConfig.supabaseEnabled ||
        Supabase.instance.client.auth.currentUser == null) {
      _snack(
        _t(
          'Soru sormak iÃ§in giriÅŸ yapmalÄ±sÄ±nÄ±z.',
          'Please sign in to ask a question.',
          'Inicie sesiÃ³n para hacer una pregunta.',
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
      );
      _questionCtrl.clear();
      await _load();
      if (!mounted) return;
      _snack(
        _t(
          'Sorunuz alÄ±ndÄ±. 24 saat iÃ§inde yazÄ±lÄ± cevap gelecek.',
          'Your question is received. A written answer will arrive within 24 hours.',
          'Su pregunta fue recibida. La respuesta llegarÃ¡ en 24 horas.',
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bgSecondary,
        elevation: 0,
        title: Text(
          _t('AstroloÄŸa Sor', 'Ask an Astrologer', 'Pregunta a un AstrÃ³logo'),
          style: TextStyle(
            color: FastTheme.accentGold,
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
                      _t('SorularÄ±m', 'My questions', 'Mis preguntas'),
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
        _t('Karma Astrolog', 'Karma Astrologer', 'AstrÃ³logo KÃ¡rmico');
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
              CircleAvatar(
                radius: 26,
                backgroundColor: FastTheme.cardBg,
                backgroundImage: (photo != null && photo.isNotEmpty)
                    ? NetworkImage(photo)
                    : null,
                child: (photo == null || photo.isEmpty)
                    ? Icon(Icons.person, color: FastTheme.accentGold)
                    : null,
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
                    '24 saat iÃ§inde yazÄ±lÄ± cevap Â· cevap gelmezse Ã¼cret iadesi',
                    'Written answer within 24 hours Â· full refund if unanswered',
                    'Respuesta escrita en 24 horas Â· reembolso si no hay respuesta',
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
    final priceText = '${price.toStringAsFixed(2).replaceAll('.', ',')} â‚º';

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
        TextField(
          controller: _questionCtrl,
          maxLines: 5,
          maxLength: 2000,
          style: TextStyle(color: FastTheme.text),
          decoration: InputDecoration(
            hintText: _t(
              'Sorunuzu tek ve net biÃ§imde yazÄ±n. Ã–rnek: "Bu iliÅŸki evliliÄŸe gider mi?"',
              'Write one clear question. Example: "Will this relationship lead to marriage?"',
              'Escriba una pregunta clara. Ejemplo: "Â¿Esta relaciÃ³n llevarÃ¡ al matrimonio?"',
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
                        'Tek soru danÄ±ÅŸmanlÄ±ÄŸÄ±',
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

  Widget _questionCard(Map<String, dynamic> q) {
    final status = (q['status'] as String?) ?? 'pending_payment';
    final answer = (q['answer_text'] as String?)?.trim();
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
            if (rating == null)
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
        ],
      ),
    );
  }

  Widget _statusChip(String status) {
    final label = switch (status) {
      'open' => _t('Cevap bekliyor', 'Awaiting answer', 'Esperando respuesta'),
      'answered' => _t('CevaplandÄ±', 'Answered', 'Respondida'),
      'closed' => _t('TamamlandÄ±', 'Completed', 'Completada'),
      'refunded' => _t('Ä°ade edildi', 'Refunded', 'Reembolsada'),
      'expired' => _t('SÃ¼re doldu', 'Expired', 'Expirada'),
      _ => _t('Ã–deme bekliyor', 'Awaiting payment', 'Esperando pago'),
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
            _t('CevabÄ± puanla', 'Rate the answer', 'Califica la respuesta'),
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
                    'Not (isteÄŸe baÄŸlÄ±)',
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
              child: Text(_t('VazgeÃ§', 'Cancel', 'Cancelar')),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              style: FilledButton.styleFrom(
                backgroundColor: FastTheme.accentGold,
              ),
              child: Text(
                _t('GÃ¶nder', 'Send', 'Enviar'),
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
