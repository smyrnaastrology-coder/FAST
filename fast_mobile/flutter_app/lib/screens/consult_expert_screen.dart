import 'package:flutter/material.dart';

import '../config/theme.dart';
import '../services/astro_consult_service.dart';
import 'astro_consult_screen.dart';

/// Uzmanın kimliği, yöntemi ve hizmet taahhüdü.
///
/// Apple incelemesinde uygulamanın "kim tarafından, nasıl" hizmet verdiğini
/// göstermek için bu ekran kanıt setinin parçasıdır.
class ConsultExpertScreen extends StatefulWidget {
  const ConsultExpertScreen({super.key});

  @override
  State<ConsultExpertScreen> createState() => _ConsultExpertScreenState();
}

class _ConsultExpertScreenState extends State<ConsultExpertScreen> {
  Map<String, dynamic>? _expert;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final rows = await AstroConsultService.astrologers();
      if (!mounted) return;
      setState(() {
        _expert = rows.isNotEmpty ? rows.first : null;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  String _lang(BuildContext context) =>
      Localizations.localeOf(context).languageCode;

  String _t(BuildContext context, String tr, String en, String es) {
    switch (_lang(context)) {
      case 'en':
        return en;
      case 'es':
        return es;
      default:
        return tr;
    }
  }

  @override
  Widget build(BuildContext context) {
    final name =
        (_expert?['display_name'] as String?)?.trim().isNotEmpty == true
        ? (_expert!['display_name'] as String).trim()
        : 'Fatih Asartepe';
    final headline = (_expert?['headline'] as String?)?.trim() ?? '';
    final bio = (_expert?['bio'] as String?)?.trim() ?? '';
    final rating = _expert?['rating'];
    final answers = _expert?['answer_count'];

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: IconThemeData(color: FastTheme.text),
        title: Text(
          _t(context, 'Uzman', 'Expert', 'Experto'),
          style: TextStyle(color: FastTheme.text, fontSize: 16),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                Row(
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: Image.asset(
                        'assets/astrolog_fatih.jpeg',
                        width: 84,
                        height: 84,
                        fit: BoxFit.cover,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            name,
                            style: TextStyle(
                              color: FastTheme.text,
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          if (headline.isNotEmpty) ...[
                            const SizedBox(height: 4),
                            Text(
                              headline,
                              style: TextStyle(
                                color: FastTheme.textMuted,
                                fontSize: 12,
                                height: 1.4,
                              ),
                            ),
                          ],
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Icon(
                                Icons.verified,
                                size: 14,
                                color: FastTheme.accentGold,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                _t(
                                  context,
                                  'Kimliği doğrulanmış uzman',
                                  'Identity-verified expert',
                                  'Experto con identidad verificada',
                                ),
                                style: TextStyle(
                                  color: FastTheme.accentGold,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                if (rating != null || answers != null) ...[
                  Row(
                    children: [
                      if (rating != null)
                        _stat(
                          context,
                          '${(rating as num).toStringAsFixed(1)} / 5',
                          _t(context, 'Değerlendirme', 'Rating', 'Valoración'),
                        ),
                      if (rating != null && answers != null)
                        const SizedBox(width: 12),
                      if (answers != null)
                        _stat(
                          context,
                          '$answers',
                          _t(
                            context,
                            'Tamamlanan danışmanlık',
                            'Completed consultations',
                            'Consultas completadas',
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 20),
                ],
                if (bio.isNotEmpty) ...[
                  _title(context, _t(context, 'Hakkında', 'About', 'Sobre')),
                  const SizedBox(height: 8),
                  Text(
                    bio,
                    style: TextStyle(
                      color: FastTheme.textMuted,
                      fontSize: 12,
                      height: 1.6,
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
                _title(context, _t(context, 'Yöntem', 'Method', 'Método')),
                const SizedBox(height: 8),
                _bullet(
                  context,
                  _t(
                    context,
                    'Doğum haritanız, verdiğiniz tarih–saat–yer ile elle çıkarılır.',
                    'Your birth chart is cast by hand from the date, time and place you provide.',
                    'Su carta natal se calcula a mano con la fecha, hora y lugar indicados.',
                  ),
                ),
                _bullet(
                  context,
                  _t(
                    context,
                    'Sorunuz horary (soru astrolojisi) tekniğiyle ayrıca değerlendirilir.',
                    'Your question is additionally assessed with horary (question astrology).',
                    'Su pregunta se evalúa además con astrología horaria.',
                  ),
                ),
                _bullet(
                  context,
                  _t(
                    context,
                    'Cevap şablon değildir; sorunuza ve haritanıza özel yazılır.',
                    'The answer is not a template; it is written for your question and chart.',
                    'La respuesta no es una plantilla; se escribe para su pregunta y carta.',
                  ),
                ),
                const SizedBox(height: 20),
                _title(
                  context,
                  _t(
                    context,
                    'Hizmet taahhüdü',
                    'Service commitment',
                    'Compromiso',
                  ),
                ),
                const SizedBox(height: 8),
                _bullet(
                  context,
                  _t(
                    context,
                    'Ödeme sonrası 24 saat içinde yazılı cevap.',
                    'Written answer within 24 hours of payment.',
                    'Respuesta escrita en 24 horas tras el pago.',
                  ),
                ),
                _bullet(
                  context,
                  _t(
                    context,
                    'Cevap gelmezse ücret otomatik iade edilir.',
                    'If no answer arrives, the fee is refunded automatically.',
                    'Si no llega respuesta, el importe se reembolsa automáticamente.',
                  ),
                ),
                _bullet(
                  context,
                  _t(
                    context,
                    'Türkçe, İngilizce ve İspanyolca hizmet.',
                    'Service in Turkish, English and Spanish.',
                    'Servicio en turco, inglés y español.',
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor: FastTheme.accentGold,
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(vertical: 15),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => const AstroConsultScreen(),
                      ),
                    ),
                    child: Text(
                      _t(
                        context,
                        'Sorunuzu sorun',
                        'Ask your question',
                        'Haga su pregunta',
                      ),
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _title(BuildContext context, String text) {
    return Text(
      text,
      style: TextStyle(
        color: FastTheme.text,
        fontSize: 15,
        fontWeight: FontWeight.w600,
      ),
    );
  }

  Widget _bullet(BuildContext context, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.circle, size: 5, color: FastTheme.accentGold),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                color: FastTheme.textMuted,
                fontSize: 12,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _stat(BuildContext context, String value, String label) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 14),
        decoration: BoxDecoration(
          color: FastTheme.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: FastTheme.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              value,
              style: TextStyle(
                color: FastTheme.accentGold,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(color: FastTheme.textDim, fontSize: 10),
            ),
          ],
        ),
      ),
    );
  }
}
