import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../services/translation_service.dart';

/// Translate engine-produced Turkish explanations without displaying them in
/// the wrong language if the offline translation model is unavailable.
class HoraryLocalizedDetail extends StatefulWidget {
  const HoraryLocalizedDetail({
    super.key,
    required this.text,
    required this.style,
  });

  final String text;
  final TextStyle style;

  @override
  State<HoraryLocalizedDetail> createState() => _HoraryLocalizedDetailState();
}

class _HoraryLocalizedDetailState extends State<HoraryLocalizedDetail> {
  String? _language;
  Future<String>? _translation;

  void _start(String language) {
    _language = language;
    _translation = language == 'tr'
        ? Future.value(widget.text)
        : TranslationService.instance.translate(
            text: widget.text,
            sourceLanguageCode: 'tr',
            targetLanguageCode: language,
          );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final language = Localizations.localeOf(context).languageCode;
    if (_language != language) _start(language);
  }

  @override
  void didUpdateWidget(HoraryLocalizedDetail oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.text != widget.text && _language != null) _start(_language!);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    if (widget.text.trim().isEmpty) return const SizedBox.shrink();
    return FutureBuilder<String>(
      future: _translation,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return Text(l10n.horaryTranslating, style: widget.style);
        }
        final result = snapshot.data;
        if (snapshot.hasError ||
            result == null ||
            result.trim().isEmpty ||
            (_language != 'tr' && result.trim() == widget.text.trim())) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.horaryTranslationUnavailable, style: widget.style),
              TextButton(
                onPressed: () => setState(() => _start(_language!)),
                child: Text(l10n.horaryTranslationRetry),
              ),
            ],
          );
        }
        return Text(result, style: widget.style);
      },
    );
  }
}
