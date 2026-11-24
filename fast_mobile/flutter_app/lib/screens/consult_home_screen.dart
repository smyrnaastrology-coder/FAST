import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config/theme.dart';
import '../services/astro_consult_service.dart';
import '../services/revenuecat_service.dart';
import 'astro_consult_screen.dart';
import 'consult_account_screen.dart';

/// Danışmanlık odaklı iOS sürümünün ana ekranı.
///
/// Bu sürümde günlük burç, harita, sosyal akış yoktur. Amaç, Apple'ın
/// 4.3(b) değerlendirmesinde uygulamanın "astroloji içeriği" değil
/// "uzman danışmanlığı hizmeti" olarak okunmasını sağlamaktır.
class ConsultHomeScreen extends StatelessWidget {
  const ConsultHomeScreen({super.key});

  static const _astrologerPhoto = 'assets/astrolog_fatih.jpeg';

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
    final priceText = RevenueCatService.priceFor(
      AstroConsultService.singleQuestionProductId,
      fallback: '2.399,99 ₺',
    );

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
          children: [
            _header(context),
            const SizedBox(height: 20),
            _expertCard(context),
            const SizedBox(height: 16),
            _priceCard(context, priceText),
            const SizedBox(height: 24),
            _sectionTitle(
              context,
              _t(context, 'Nasıl işliyor?', 'How it works', 'Cómo funciona'),
            ),
            const SizedBox(height: 12),
            _steps(context),
            const SizedBox(height: 24),
            _sectionTitle(
              context,
              _t(context, 'Ne alıyorsunuz?', 'What you get', 'Qué recibe'),
            ),
            const SizedBox(height: 12),
            _deliverables(context),
            const SizedBox(height: 24),
            _sectionTitle(
              context,
              _t(context, 'Sık sorulanlar', 'FAQ', 'Preguntas frecuentes'),
            ),
            const SizedBox(height: 8),
            _faq(context),
            const SizedBox(height: 24),
            _legal(context),
          ],
        ),
      ),
    );
  }

  Widget _header(BuildContext context) {
    return Row(
      children: [
        Text(
          'HOLAVON',
          style: TextStyle(
            color: FastTheme.accentGold,
            fontSize: 13,
            letterSpacing: 4,
            fontWeight: FontWeight.w600,
          ),
        ),
        const Spacer(),
        IconButton(
          tooltip: _t(context, 'Hesap', 'Account', 'Cuenta'),
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const ConsultAccountScreen()),
          ),
          icon: Icon(Icons.person_outline, color: FastTheme.textMuted),
        ),
      ],
    );
  }

  Widget _expertCard(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: FastTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(14),
                child: Image.asset(
                  _astrologerPhoto,
                  width: 72,
                  height: 72,
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Fatih Asartepe',
                      style: TextStyle(
                        color: FastTheme.text,
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _t(
                        context,
                        'Astrolog · Birebir yazılı danışmanlık',
                        'Astrologer · One-to-one written consultation',
                        'Astrólogo · Consulta escrita individual',
                      ),
                      style: TextStyle(
                        color: FastTheme.textMuted,
                        fontSize: 12,
                      ),
                    ),
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
                            'Verified expert',
                            'Experto verificado',
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
          const SizedBox(height: 14),
          Text(
            _t(
              context,
              'Sorunuzu yazın; doğum bilgilerinizle haritanızı çıkarıp '
                  '24 saat içinde yazılı cevap ve PDF rapor hazırlıyorum.',
              'Send your question; I cast your chart from your birth details '
                  'and deliver a written answer and PDF report within 24 hours.',
              'Envíe su pregunta; calculo su carta con sus datos de nacimiento '
                  'y entrego respuesta escrita e informe PDF en 24 horas.',
            ),
            style: TextStyle(
              color: FastTheme.textMuted,
              fontSize: 12,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _priceCard(BuildContext context, String priceText) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: FastTheme.bgSecondary,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                priceText,
                style: TextStyle(
                  color: FastTheme.accentGold,
                  fontSize: 26,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(width: 8),
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  _t(context, 'tek soru', 'per question', 'por pregunta'),
                  style: TextStyle(color: FastTheme.textMuted, fontSize: 12),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            _t(
              context,
              'Abonelik yok · tek seferlik ödeme',
              'No subscription · one-time payment',
              'Sin suscripción · pago único',
            ),
            style: TextStyle(color: FastTheme.textDim, fontSize: 11),
          ),
          const SizedBox(height: 16),
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
          const SizedBox(height: 12),
          _trustRow(
            context,
            Icons.schedule,
            _t(
              context,
              '24 saat içinde yazılı cevap',
              'Written answer within 24 hours',
              'Respuesta escrita en 24 horas',
            ),
          ),
          const SizedBox(height: 6),
          _trustRow(
            context,
            Icons.assignment_return_outlined,
            _t(
              context,
              'Cevap gelmezse tam iade',
              'Full refund if unanswered',
              'Reembolso completo si no hay respuesta',
            ),
          ),
          const SizedBox(height: 6),
          _trustRow(
            context,
            Icons.picture_as_pdf_outlined,
            _t(
              context,
              'Kalıcı PDF danışmanlık dosyası',
              'Permanent PDF consultation file',
              'Archivo PDF permanente de la consulta',
            ),
          ),
        ],
      ),
    );
  }

  Widget _trustRow(BuildContext context, IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, size: 15, color: FastTheme.accentGold),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: TextStyle(color: FastTheme.textMuted, fontSize: 11),
          ),
        ),
      ],
    );
  }

  Widget _sectionTitle(BuildContext context, String title) {
    return Text(
      title,
      style: TextStyle(
        color: FastTheme.text,
        fontSize: 16,
        fontWeight: FontWeight.w600,
      ),
    );
  }

  Widget _steps(BuildContext context) {
    final steps = [
      (
        '1',
        _t(
          context,
          'Sorunuzu ve doğum bilgilerinizi girin',
          'Enter your question and birth details',
          'Introduzca su pregunta y datos de nacimiento',
        ),
      ),
      (
        '2',
        _t(
          context,
          'Ödemeyi tamamlayın; süre başlar',
          'Complete the payment; the clock starts',
          'Complete el pago; comienza el plazo',
        ),
      ),
      (
        '3',
        _t(
          context,
          'Haritanız çıkarılır, cevap yazılır',
          'Your chart is cast and the answer written',
          'Se calcula su carta y se escribe la respuesta',
        ),
      ),
      (
        '4',
        _t(
          context,
          'Yazılı cevap ve PDF hesabınıza düşer',
          'Written answer and PDF arrive in your account',
          'La respuesta y el PDF llegan a su cuenta',
        ),
      ),
    ];
    return Column(
      children: [
        for (final step in steps)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 24,
                  height: 24,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: FastTheme.accentGold),
                  ),
                  child: Text(
                    step.$1,
                    style: TextStyle(
                      color: FastTheme.accentGold,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    step.$2,
                    style: TextStyle(
                      color: FastTheme.textMuted,
                      fontSize: 12,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _deliverables(BuildContext context) {
    final items = [
      _t(
        context,
        'Sorunuza özel, şablon olmayan yazılı cevap',
        'A written answer specific to your question, not a template',
        'Una respuesta escrita específica, no una plantilla',
      ),
      _t(
        context,
        'Doğum haritanızın teknik dökümü',
        'Technical breakdown of your birth chart',
        'Desglose técnico de su carta natal',
      ),
      _t(
        context,
        'İndirilebilir PDF danışmanlık dosyası',
        'Downloadable PDF consultation file',
        'Archivo PDF descargable de la consulta',
      ),
      _t(
        context,
        'Cevap gelmezse otomatik iade',
        'Automatic refund if no answer arrives',
        'Reembolso automático si no hay respuesta',
      ),
    ];
    return Column(
      children: [
        for (final item in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.check, size: 15, color: FastTheme.accentGold),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    item,
                    style: TextStyle(
                      color: FastTheme.textMuted,
                      fontSize: 12,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _faq(BuildContext context) {
    final items = [
      (
        _t(
          context,
          'Cevabı nerede göreceğim?',
          'Where will I see the answer?',
          '¿Dónde veré la respuesta?',
        ),
        _t(
          context,
          '“Sorularım ve Cevaplarım” bölümünde. Cevap geldiğinde bildirim de alırsınız.',
          'In the “My Questions & Answers” section. You also get a notification when it arrives.',
          'En la sección “Mis preguntas y respuestas”. También recibirá una notificación.',
        ),
      ),
      (
        _t(
          context,
          'Cevap gelmezse ne olur?',
          'What if no answer arrives?',
          '¿Y si no llega la respuesta?',
        ),
        _t(
          context,
          '24 saat dolduğunda ücret otomatik olarak iade edilir; talep açmanız gerekmez.',
          'After 24 hours the fee is refunded automatically; you do not need to request it.',
          'Tras 24 horas el importe se reembolsa automáticamente.',
        ),
      ),
      (
        _t(
          context,
          'Sorduğum soru başkalarına gösterilir mi?',
          'Is my question shown to others?',
          '¿Mi pregunta es visible para otros?',
        ),
        _t(
          context,
          'Hayır. Sorunuz yalnızca sizinle astrolog arasındadır ve hesabınızda saklanır.',
          'No. It stays between you and the astrologer, stored in your account.',
          'No. Queda entre usted y el astrólogo, guardada en su cuenta.',
        ),
      ),
    ];
    return Column(
      children: [
        for (final item in items)
          Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              tilePadding: EdgeInsets.zero,
              childrenPadding: const EdgeInsets.only(bottom: 10),
              iconColor: FastTheme.accentGold,
              collapsedIconColor: FastTheme.textDim,
              title: Text(
                item.$1,
                style: TextStyle(color: FastTheme.text, fontSize: 13),
              ),
              children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    item.$2,
                    style: TextStyle(
                      color: FastTheme.textMuted,
                      fontSize: 12,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _legal(BuildContext context) {
    return Column(
      children: [
        Wrap(
          alignment: WrapAlignment.center,
          spacing: 16,
          children: [
            _link(
              _t(context, 'Gizlilik', 'Privacy', 'Privacidad'),
              'https://holavon.com/gizlilik',
            ),
            _link(
              _t(context, 'Kullanım şartları', 'Terms', 'Términos'),
              'https://holavon.com/sartlar',
            ),
            _link(
              _t(context, 'Destek', 'Support', 'Soporte'),
              'https://holavon.com/destek',
            ),
          ],
        ),
        const SizedBox(height: 12),
        Text(
          _t(
            context,
            'Holavon · Birebir uzman danışmanlığı',
            'Holavon · One-to-one expert consultation',
            'Holavon · Consulta experta individual',
          ),
          textAlign: TextAlign.center,
          style: TextStyle(color: FastTheme.textDim, fontSize: 10),
        ),
      ],
    );
  }

  Widget _link(String text, String url) {
    return InkWell(
      onTap: () =>
          launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication),
      child: Text(
        text,
        style: TextStyle(color: FastTheme.accentGold, fontSize: 11),
      ),
    );
  }
}
