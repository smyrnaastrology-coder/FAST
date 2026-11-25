import 'package:flutter/material.dart';

import '../config/theme.dart';
import 'astro_consult_screen.dart';

/// Danışmanlık dosyasının (PDF) ne içerdiğini gösteren örnek ekran.
///
/// Amaç: kullanıcı ödeme yapmadan önce ne alacağını görsün; Apple incelemesinde
/// de somut bir "ürün" olduğu anlaşılsın. İçerik örnektir, kişiye özel değildir.
class ConsultSampleScreen extends StatelessWidget {
  const ConsultSampleScreen({super.key});

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
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: IconThemeData(color: FastTheme.text),
        title: Text(
          _t(context, 'Örnek dosya', 'Sample report', 'Informe de ejemplo'),
          style: TextStyle(color: FastTheme.text, fontSize: 16),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          _cover(context),
          const SizedBox(height: 18),
          _section(
            context,
            '01',
            _t(
              context,
              'Soru özeti',
              'Question summary',
              'Resumen de la pregunta',
            ),
            _t(
              context,
              'Sorunuz kendi cümlelerinizle, konu başlığıyla birlikte dosyanın '
                  'ilk sayfasında yer alır.',
              'Your question appears on the first page in your own words, '
                  'together with its topic.',
              'Su pregunta aparece en la primera página con sus propias '
                  'palabras y el tema elegido.',
            ),
          ),
          _section(
            context,
            '02',
            _t(context, 'Doğum verileri', 'Birth data', 'Datos de nacimiento'),
            _t(
              context,
              'Tarih, saat, yer ve kullanılan saat dilimi (UTC) açıkça yazılır; '
                  'böylece harita her zaman yeniden üretilebilir.',
              'Date, time, place and the time zone (UTC) used are stated '
                  'explicitly, so the chart can always be reproduced.',
              'Se indican fecha, hora, lugar y zona horaria (UTC), de modo que '
                  'la carta siempre pueda reproducirse.',
            ),
          ),
          _section(
            context,
            '03',
            _t(
              context,
              'Harita dökümü',
              'Chart breakdown',
              'Desglose de la carta',
            ),
            _t(
              context,
              'Yükselen, Güneş, Ay, gezegen konumları ve soruyla ilgili evler '
                  'teknik olarak listelenir.',
              'Ascendant, Sun, Moon, planetary positions and the houses '
                  'relevant to the question are listed technically.',
              'Ascendente, Sol, Luna, posiciones planetarias y las casas '
                  'relevantes se listan de forma técnica.',
            ),
          ),
          _section(
            context,
            '04',
            _t(context, 'Değerlendirme', 'Assessment', 'Evaluación'),
            _t(
              context,
              'Asıl bölüm: sorunuzun cevabı, gerekçeleriyle birlikte düz '
                  'metin olarak yazılır. Şablon cümle kullanılmaz.',
              'The core section: the answer to your question, in prose, with '
                  'its reasoning. No template sentences.',
              'La sección principal: la respuesta a su pregunta, en prosa, con '
                  'su razonamiento. Sin frases de plantilla.',
            ),
          ),
          _section(
            context,
            '05',
            _t(
              context,
              'Sonuç ve öneriler',
              'Conclusion & guidance',
              'Conclusión',
            ),
            _t(
              context,
              'Kısa bir sonuç paragrafı ve uygulanabilir öneriler.'
                  'Dosya PDF olarak indirilebilir ve hesabınızda kalır.',
              'A short conclusion and actionable guidance. The file is '
                  'downloadable as PDF and stays in your account.',
              'Una conclusión breve y recomendaciones aplicables. El archivo se '
                  'descarga en PDF y queda en su cuenta.',
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: FastTheme.bgSecondary,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: FastTheme.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _t(
                    context,
                    'Örnek değerlendirme (kısaltılmış)',
                    'Sample assessment (abridged)',
                    'Evaluación de ejemplo (abreviada)',
                  ),
                  style: TextStyle(
                    color: FastTheme.accentGold,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  _t(
                    context,
                    '“Sorunuz, kariyer değişikliğinin zamanlamasına odaklanıyor. '
                        'Haritada yükselen burcun yöneticisi 10. evde güçlü; '
                        'ancak geri giden Merkür dönemi sözleşme imzası için '
                        'uygun değil. Bu nedenle ilk adımı görüşme ve hazırlık '
                        'olarak kurmanız, imzayı ise belirtilen tarih aralığından '
                        'sonraya bırakmanız önerilir.”',
                    '“Your question concerns the timing of a career change. '
                        'The ruler of your ascendant is strong in the 10th house, '
                        'but the Mercury retrograde period is not suitable for '
                        'signing a contract. Therefore, use the first step for '
                        'interviews and preparation, and postpone the signature '
                        'to after the indicated window.”',
                    '“Su pregunta se centra en el momento de un cambio laboral. '
                        'El regente de su ascendente está fuerte en la casa 10, '
                        'pero el período de Mercurio retrógrado no es adecuado '
                        'para firmar un contrato. Por eso, use el primer paso '
                        'para entrevistas y preparación, y posponga la firma.”',
                  ),
                  style: TextStyle(
                    color: FastTheme.textMuted,
                    fontSize: 12,
                    height: 1.6,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
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
                MaterialPageRoute(builder: (_) => const AstroConsultScreen()),
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

  Widget _cover(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.5)),
        color: FastTheme.cardBg,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'HOLAVON',
            style: TextStyle(
              color: FastTheme.accentGold,
              fontSize: 11,
              letterSpacing: 3,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            _t(
              context,
              'Danışmanlık Dosyası',
              'Consultation Report',
              'Informe de consulta',
            ),
            style: TextStyle(
              color: FastTheme.text,
              fontSize: 20,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            _t(
              context,
              'Fatih Asartepe · Astrolog',
              'Fatih Asartepe · Astrologer',
              'Fatih Asartepe · Astrólogo',
            ),
            style: TextStyle(color: FastTheme.textMuted, fontSize: 12),
          ),
          const SizedBox(height: 14),
          Text(
            _t(
              context,
              'PDF · soruya özel · 3–5 sayfa',
              'PDF · question-specific · 3–5 pages',
              'PDF · específico · 3–5 páginas',
            ),
            style: TextStyle(color: FastTheme.textDim, fontSize: 10),
          ),
        ],
      ),
    );
  }

  Widget _section(
    BuildContext context,
    String number,
    String title,
    String body,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            number,
            style: TextStyle(
              color: FastTheme.accentGold,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: FastTheme.text,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  body,
                  style: TextStyle(
                    color: FastTheme.textMuted,
                    fontSize: 12,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
