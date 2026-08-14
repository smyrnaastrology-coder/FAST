import 'dart:math';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../config/theme.dart';
import '../services/api_service.dart';
import 'analyzer_screen.dart';

class LandingScreen extends StatefulWidget {
  const LandingScreen({super.key});

  @override
  State<LandingScreen> createState() => _LandingScreenState();
}

class _LandingScreenState extends State<LandingScreen> {
  final _api = ApiService();
  final _scrollCtrl = ScrollController();
  int _faqOpen = -1;
  int _testimonialIdx = 0;
  bool _priceYearly = false;
  Map<String, dynamic> _stats = {'total_analysis': 1247, 'total_cities': 15000};

  @override
  void initState() {
    super.initState();
    _api.getStats().then((d) => setState(() => _stats = d)).catchError((_) {});
    _startTestimonialTimer();
  }

  void _startTestimonialTimer() {
    Future.delayed(const Duration(seconds: 5), () {
      if (!mounted) return;
      setState(() => _testimonialIdx = (_testimonialIdx + 1) % 5);
      _startTestimonialTimer();
    });
  }

  void _scrollTo(double offset) {
    _scrollCtrl.animateTo(offset.clamp(0, _scrollCtrl.position.maxScrollExtent),
        duration: const Duration(milliseconds: 500), curve: Curves.easeInOut);
  }

  void _startAnalysis([String? mode]) {
    Navigator.push(context, MaterialPageRoute(
      builder: (_) => AnalyzerScreen(initialMode: mode ?? 'es_sevgili'),
    ));
  }

  static const _modes = [
    {'key': 'es_sevgili', 'title': 'Eş / Sevgili', 'desc': '6 aylık gökyüzü akışı ile çiftler arası bağ analizi', 'badge': 'Çift', 'icon': '💑'},
    {'key': 'ebeveyn_cocuk', 'title': 'Ebeveyn / Çocuk', 'desc': 'Nesiller arası bağ, çocuk gelişimi ve potansiyel tespiti', 'badge': 'Aile', 'icon': '👨‍👩‍👧‍👦'},
    {'key': 'bireysel_natal', 'title': 'Bireysel Natal', 'desc': 'Kişisel doğum haritasıyla hayatın tüm alanları için derin analiz', 'badge': 'Kişisel', 'icon': '⭐'},
    {'key': 'potansiyel_yetenek', 'title': 'Potansiyel / Yetenek', 'desc': 'Doğum haritası ile meslek yönlendirme ve yetenek keşfi', 'badge': 'Bireysel', 'icon': '🌟'},
  ];

  static const _features = [
    {'icon': '🔮', 'title': 'Sinastri Analizi', 'desc': 'Çift, ebeveyn-çocuk, bireysel natal veya potansiyel harita ile gezegen konumlarınızın derin analizi.'},
    {'icon': '🌍', 'title': 'Astrocartography', 'desc': '15.000+ şehirde yıldız uyumu haritanız; gezegenlerin dünya üzerindeki izdüşümlerini keşfedin.'},
    {'icon': '🌟', 'title': 'Yıldız Mühürleri', 'desc': '21 yıllık göksel döngüde gezegen mühürleriniz ve göksel kontrat analizi.'},
    {'icon': '📅', 'title': 'Gökyüzü Zaman Akışı', 'desc': 'Günlük, aylık ve yıllık gökyüzü akışlarıyla ilişki, gelişim ve fırsat pencereleri.'},
    {'icon': '🧬', 'title': 'Potansiyel & Yetenek', 'desc': '7 farklı alanda doğal yetenek tespiti ve meslek yönlendirme önerileri.'},
    {'icon': '👑', 'title': 'Asteroit Etkileşimleri', 'desc': 'Juno, Ceres, Pallas, Vesta, Eros, Psyche — 8 asteroidin çapraz temasları.'},
    {'icon': '🌙', 'title': 'Arap Noktaları', 'desc': 'Kozmik noktaların sinastri bağları ve ev konumlarıyla analizi.'},
    {'icon': '📄', 'title': 'PDF Raporu', 'desc': 'Tüm analizler profesyonel PDF raporunda; sınırsız indirme ve e-posta teslimi.'},
  ];

  static const _howSteps = [
    {'step': '1', 'icon': '📝', 'title': 'Analiz Türünü Seçin', 'desc': 'Çift, ebeveyn-çocuk, bireysel natal veya potansiyel analizi — size uygun olanı seçin.'},
    {'step': '2', 'icon': '🔮', 'title': 'Bilgileri Girin', 'desc': 'İsim, doğum tarihi ve konum bilgilerinizle 21 yıllık analiz saniyeler içinde hazır.'},
    {'step': '3', 'icon': '📥', 'title': 'PDF Raporu Alın', 'desc': 'Detaylı raporunuzu PDF olarak indirin, dilediğinizce saklayın veya e-posta ile alın.'},
  ];

  static const _plans = [
    {
      'name': 'Temel', 'badge': 'Ücretsiz', 'price': 0, 'desc': 'Analizi deneyimleyin',
      'features': ['Tüm analiz sonuçları ekranda', '2 harita görüntüleme', 'Temel uyum skorları', 'Gökyüzü akışı', 'Sınırlı asteroid verisi'],
      'disabled': ['PDF Raporu', 'Astrocartography', 'Yıldız Mühürleri', 'Arap Noktaları', 'E-posta PDF'],
      'highlight': false,
    },
    {
      'name': 'Premium', 'badge': 'En Popüler', 'price': 129, 'desc': 'Profesyonel analiz paketi',
      'features': ['Temeldeki her şey', 'PDF Raporu (sınırsız indirme)', 'Astrocartography dünya haritası', 'Yıldız Mühürleri tam liste', 'Arap Noktaları + sinastri', 'Tüm haritalar SVG (7+ grafik)', 'E-posta ile PDF teslimi'],
      'disabled': <String>[],
      'highlight': true,
    },
    {
      'name': 'Pro', 'badge': 'VIP', 'price': 249, 'desc': 'Kişisel danışmanlık dahil',
      'features': ['Premiumdaki her şey', 'Kişisel astroloji yorumu', '30 dakika WhatsApp danışmanlık', '1 yıl güncelleme hakkı', 'Öncelikli destek'],
      'disabled': <String>[],
      'highlight': false,
    },
  ];

  static const _testimonials = [
    {'name': 'Zeynep K.', 'text': 'Eşimle aramızdaki bağı çok farklı bir perspektiften görmemi sağladı. PDF raporu inanılmaz detaylıydı.'},
    {'name': 'Ahmet T.', 'text': 'Astrocartography özelliği sayesinde taşınmamız gereken şehri bulduk. Şu anda çok mutluyuz.'},
    {'name': 'Selin A.', 'text': 'Yıldız haritamız sayesinde ilişkimizdeki zorlu dönemlerin dinamiklerini anladık ve iletişimimizi güçlendirdik.'},
    {'name': 'Mehmet B.', 'text': 'Oğlumun yeteneklerini keşfetmek için kullandım. Meslek yönlendirme önerileri çok isabetli.'},
    {'name': 'Ayşe K.', 'text': 'Kendim için potansiyel analizi yaptırdım. Daha önce fark etmediğim yetenek alanlarımı keşfettim. Kariyer değişikliği yapmama vesile oldu.'},
  ];

  static const _faqs = [
    {'q': 'Analiz nasıl çalışır?', 'a': 'Doğum tarihi, saati ve konum bilgilerinizle astrolojik haritanız çıkarılır. FAST tekniği ile bağıl haritalar hesaplanır ve 21 yıllık göksel döngü analiz edilir.'},
    {'q': 'Hangi analiz türünü seçmeliyim?', 'a': 'Evli veya sevgili iseniz "Eş/Sevgili" modu, çocuğunuzun yeteneklerini keşfetmek için "Ebeveyn/Çocuk" modunu kullanabilirsiniz.'},
    {'q': 'Doğum saatini bilmiyorum, ne yapmalıyım?', 'a': 'Doğum saati olmadan da analiz yapılabilir ancak ev haritası ve bazı detaylı hesaplamalar için saat gereklidir. Saat yoksa 12:00 varsayılan olarak kullanılır.'},
    {'q': 'PDF raporu nasıl alırım?', 'a': 'Premium veya Pro paket satın alarak PDF raporunuzu sınırsız şekilde indirebilirsiniz. Rapor e-posta ile de teslim edilir.'},
    {'q': 'Ödeme yöntemleri nelerdir?', 'a': 'Kredi kartı, banka kartı ve havale/EFT seçenekleri mevcuttur. Tüm ödemeler 256-bit SSL ile korunur.'},
    {'q': 'Para iade garantiniz var mı?', 'a': 'Evet, 14 gün içinde koşulsuz para iade garantisi sunuyoruz. Memnun kalmazsanız ücretiniz iade edilir.'},
    {'q': 'Astrocartography nedir?', 'a': 'Doğum haritanızdaki gezegenlerin dünya üzerinde en güçlü etkiye sahip olduğu şehirleri bulur.'},
    {'q': 'Potansiyel analizi nasıl çalışır?', 'a': 'Doğum haritanızdaki gezegen açıları taranarak 7 farklı alanda doğal yetenekleriniz tespit edilir.'},
  ];

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SingleChildScrollView(
        controller: _scrollCtrl,
        child: Column(
          children: [
            _navbar(),
            _hero(),
            _modeSection(),
            _featuresSection(),
            _howSection(),
            _pricingSection(),
            _testimonialSection(),
            _faqSection(),
            _ctaSection(),
            _footer(),
          ],
        ),
      ),
    );
  }

  Widget _navbar() {
    return Container(
      padding: EdgeInsets.only(top: MediaQuery.of(context).padding.top),
      decoration: BoxDecoration(
        color: FastTheme.bg.withValues(alpha: 0.85),
        border: const Border(bottom: BorderSide(color: FastTheme.border)),
      ),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        constraints: const BoxConstraints(maxWidth: 1200),
        child: Row(
          children: [
            GestureDetector(
              onTap: () => _scrollCtrl.animateTo(0, duration: const Duration(milliseconds: 500), curve: Curves.easeInOut),
              child: Row(
                children: [
                  Container(width: 32, height: 32, decoration: const BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold), child: const Center(child: Text('F', style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold, fontSize: 16)))),
                  const SizedBox(width: 6),
                  Text('FAST', style: GoogleFonts.cormorantGaramond(fontSize: 20, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                ],
              ),
            ),
            const Spacer(),
            Flexible(child: SingleChildScrollView(scrollDirection: Axis.horizontal, child: Row(
              children: [
                _navLink('Özellikler', () => _scrollTo(900)),
                const SizedBox(width: 12),
                _navLink('Fiyatlandırma', () => _scrollTo(1800)),
                const SizedBox(width: 12),
                _navLink('SSS', () => _scrollTo(2600)),
                const SizedBox(width: 12),
                _goldBtn('Analiz Başlat', () => _startAnalysis(), height: 34, fontSize: 11),
              ],
            ))),
          ],
        ),
      ),
    );
  }

  Widget _navLink(String text, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Text(text, style: const TextStyle(color: FastTheme.textMuted, fontSize: 13)),
    );
  }

  Widget _goldBtn(String text, VoidCallback onTap, {double height = 44, double fontSize = 13}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 20, vertical: (height - fontSize - 4) / 2),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(text, style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.w700, fontSize: fontSize, letterSpacing: 0.5)),
      ),
    );
  }

  Widget _hero() {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 80, 24, 60),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter, end: Alignment.bottomCenter,
          colors: [FastTheme.bg, FastTheme.bgSecondary],
        ),
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            decoration: BoxDecoration(
              color: FastTheme.accentGold.withValues(alpha: 0.12),
              border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.3)),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Text('YILDIZLARIN YERY\u00dcZ\u00dcNE \u0130ZD\u00dc\u015e\u00dcM\u00dc', style: TextStyle(color: FastTheme.accentGold, fontSize: 11, letterSpacing: 1)),
          ),
          const SizedBox(height: 24),
          Text.rich(
            TextSpan(
              text: 'Ba\u011f\u0131n\u0131z\u0131n G\u00f6ksel\n',
              style: GoogleFonts.cormorantGaramond(fontSize: 48, fontWeight: FontWeight.w700, color: FastTheme.text, height: 1.15),
              children: [TextSpan(text: 'Haritas\u0131n\u0131 Ke\u015ffedin', style: TextStyle(color: FastTheme.accentGold, shadows: [Shadow(color: FastTheme.accentGoldGlow, blurRadius: 40)]))],
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 20),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 600),
            child: Text('Fatih Asartepe Sinastri Tekniği (FAST) ile ilişkinizin derinliklerini, çocuğunuzun potansiyelini veya kendi yeteneklerinizi keşfedin.',
              textAlign: TextAlign.center, style: const TextStyle(color: FastTheme.textMuted, fontSize: 16, height: 1.6)),
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: FastTheme.cardBg,
              border: Border.all(color: FastTheme.border),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text('Bilgilendirme: Bu \u00e7al\u0131\u015fma gelecekte olacak olaylar\u0131 \u00f6ng\u00f6rmez; kehanet, fal veya kesin yarg\u0131 de\u011fildir. '
              'Do\u011fum an\u0131ndaki g\u00f6ky\u00fcz\u00fcn\u00fcn yery\u00fcz\u00fcne izd\u00fc\u015f\u00fcm\u00fcn\u00fc, ki\u015fisel fark\u0131ndal\u0131k ve geli\u015fim perspektifiyle anlatan bir analiz rehberidir.',
              textAlign: TextAlign.center, style: TextStyle(color: FastTheme.textMuted, fontSize: 11, height: 1.5)),
          ),
          const SizedBox(height: 32),
          Wrap(
            alignment: WrapAlignment.center,
            spacing: 16,
            runSpacing: 12,
            children: [
              _goldBtn('🔮 Ücretsiz Analiz Başlat', () => _startAnalysis(), height: 50, fontSize: 14),
              OutlinedButton.icon(
                onPressed: () => _scrollTo(400),
                icon: const Icon(Icons.arrow_downward, size: 18, color: FastTheme.accentGold),
                label: const Text('Analiz Türünü Seç', style: TextStyle(color: FastTheme.accentGold, fontSize: 14)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: FastTheme.accentGold, width: 2),
                  padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 48),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _stat('${_stats['total_analysis']}+', 'Analiz'),
              const SizedBox(width: 40),
              _stat('21', 'Yıllık Döngü'),
              const SizedBox(width: 40),
              _stat('${_stats['total_cities']}+', 'Şehir'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _stat(String num, String label) {
    return Column(
      children: [
        Text(num, style: GoogleFonts.cormorantGaramond(fontSize: 32, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
        Text(label, style: const TextStyle(fontSize: 10, color: FastTheme.textDim, letterSpacing: 1)),
      ],
    );
  }

  Widget _modeSection() {
    return _section(
      'Analiz Türünüzü Seçin',
      'Size en uygun analizi başlatın',
      isAlt: true,
      child: Wrap(
        spacing: 20,
        runSpacing: 20,
        children: _modes.map((m) => _modeCard(m)).toList(),
      ),
    );
  }

  Widget _modeCard(Map m) {
    return GestureDetector(
      onTap: () => _startAnalysis(m['key'] as String),
      child: Container(
        width: 240,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: FastTheme.cardBg,
          border: Border.all(color: FastTheme.border),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Positioned(top: -10, left: 0, right: 0, child: Center(child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 3),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(m['badge'] as String, style: const TextStyle(color: FastTheme.bg, fontSize: 9, fontWeight: FontWeight.w700, letterSpacing: 1)),
            ))),
            const SizedBox(height: 16),
            Column(
              children: [
                const SizedBox(height: 8),
                Text(m['icon'] as String, style: const TextStyle(fontSize: 48)),
                const SizedBox(height: 12),
                Text(m['title'] as String, style: GoogleFonts.cormorantGaramond(fontSize: 18, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                const SizedBox(height: 8),
                Text(m['desc'] as String, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: FastTheme.textMuted, height: 1.5)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _featuresSection() {
    return _section('Neler Sunuyoruz?', 'FAST ile astrolojik analizlerin her boyutunu keşfedin',
      child: Wrap(
        spacing: 16,
        runSpacing: 16,
        children: _features.map((f) => Container(
          width: 240,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: FastTheme.cardBg,
            border: Border.all(color: FastTheme.border),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Text(f['icon'] as String, style: const TextStyle(fontSize: 32)),
              const SizedBox(height: 8),
              Text(f['title'] as String, style: GoogleFonts.cormorantGaramond(fontSize: 16, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
              const SizedBox(height: 6),
              Text(f['desc'] as String, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: FastTheme.textMuted, height: 1.5)),
            ],
          ),
        )).toList(),
      ),
    );
  }

  Widget _howSection() {
    return _section('Nasıl Çalışır?', '3 adımda yıldız bağı analiziniz', isAlt: true,
      child: Column(
        children: [
          Wrap(
            spacing: 24, runSpacing: 24,
            children: _howSteps.map((s) => Container(
              width: 260,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(color: FastTheme.cardBg, border: Border.all(color: FastTheme.border), borderRadius: BorderRadius.circular(12)),
              child: Column(
                children: [
                  Container(width: 36, height: 36, decoration: const BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold),
                    child: Center(child: Text(s['step'] as String, style: const TextStyle(color: FastTheme.bg, fontWeight: FontWeight.w700)))),
                  const SizedBox(height: 12),
                  Text(s['icon'] as String, style: const TextStyle(fontSize: 28)),
                  const SizedBox(height: 8),
                  Text(s['title'] as String, style: GoogleFonts.cormorantGaramond(fontSize: 16, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                  const SizedBox(height: 6),
                  Text(s['desc'] as String, textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: FastTheme.textMuted, height: 1.5)),
                ],
              ),
            )).toList(),
          ),
          const SizedBox(height: 32),
          _goldBtn('🔮 Hemen Analiz Başlat', () => _startAnalysis(), height: 50, fontSize: 14),
        ],
      ),
    );
  }

  Widget _pricingSection() {
    return _section('Fiyatlandırma', 'Size en uygun paketi seçin',
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              GestureDetector(
                onTap: () => setState(() => _priceYearly = false),
                child: Text('Aylık', style: TextStyle(fontSize: 13, color: _priceYearly ? FastTheme.textDim : FastTheme.accentGold, fontWeight: _priceYearly ? FontWeight.normal : FontWeight.w600)),
              ),
              const SizedBox(width: 12),
              GestureDetector(
                onTap: () => setState(() => _priceYearly = !_priceYearly),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  width: 48, height: 26,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(13),
                    color: _priceYearly ? FastTheme.accentGold : FastTheme.cardBg,
                    border: Border.all(color: _priceYearly ? FastTheme.accentGold : FastTheme.border),
                  ),
                  child: AnimatedAlign(
                    duration: const Duration(milliseconds: 300),
                    alignment: _priceYearly ? Alignment.centerRight : Alignment.centerLeft,
                    child: Container(
                      width: 20, height: 20, margin: const EdgeInsets.all(2),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _priceYearly ? FastTheme.bg : FastTheme.text,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              GestureDetector(
                onTap: () => setState(() => _priceYearly = true),
                child: Text.rich(TextSpan(
                  text: 'Yıllık ',
                  style: TextStyle(fontSize: 13, color: _priceYearly ? FastTheme.accentGold : FastTheme.textDim, fontWeight: _priceYearly ? FontWeight.w600 : FontWeight.normal),
                  children: [TextSpan(text: '%20 indirim', style: const TextStyle(color: FastTheme.success, fontSize: 10))],
                )),
              ),
            ],
          ),
          const SizedBox(height: 32),
          Wrap(
            spacing: 20, runSpacing: 20,
            children: _plans.map((p) => _planCard(p)).toList(),
          ),
        ],
      ),
    );
  }

  Widget _planCard(Map p) {
    final highlight = p['highlight'] as bool;
    final price = p['price'] as int;
    final discPrice = _priceYearly ? (price * 10 * 0.8).round() : price;
    return Container(
      width: 280,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: highlight ? const LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [FastTheme.cardBgHover, FastTheme.cardBg]) : null,
        color: highlight ? null : FastTheme.cardBg,
        border: Border.all(color: highlight ? FastTheme.accentGold : FastTheme.border),
        borderRadius: BorderRadius.circular(16),
        boxShadow: highlight ? [const BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 24)] : null,
      ),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          if (p['badge'] != null && (p['badge'] as String).isNotEmpty)
            Positioned(top: -12, left: 0, right: 0, child: Center(child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(p['badge'] as String, style: const TextStyle(color: FastTheme.bg, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1)),
            ))),
          const SizedBox(height: 8),
          Column(
            children: [
              const SizedBox(height: 8),
              Text(p['name'] as String, style: GoogleFonts.cormorantGaramond(fontSize: 22, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
              Text(p['desc'] as String, style: const TextStyle(fontSize: 11, color: FastTheme.textDim)),
              const SizedBox(height: 16),
              price == 0
                  ? Text('Ücretsiz', style: GoogleFonts.cormorantGaramond(fontSize: 28, fontWeight: FontWeight.w700, color: FastTheme.accentGold))
                  : Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('₺$discPrice', style: GoogleFonts.cormorantGaramond(fontSize: 32, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                        Text('/${_priceYearly ? 'yıl' : 'ay'}', style: const TextStyle(fontSize: 13, color: FastTheme.textDim)),
                      ],
                    ),
              const SizedBox(height: 16),
              ...((p['features'] as List).map((f) => _planFeat(f as String, true))),
              ...((p['disabled'] as List).map((f) => _planFeat(f as String, false))),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: highlight
                    ? _goldBtn(p['price'] == 0 ? 'Ücretsiz Dene' : '${p['name']}a Başla', () => _startAnalysis(), height: 44, fontSize: 13)
                    : OutlinedButton(
                        onPressed: () => _startAnalysis(),
                        style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: FastTheme.border),
                          foregroundColor: FastTheme.text,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: Text(p['price'] == 0 ? 'Ücretsiz Dene' : '${p['name']}a Başla', style: const TextStyle(fontSize: 13)),
                      ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _planFeat(String text, bool included) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          Text(included ? '✓' : '✗', style: TextStyle(fontSize: 12, color: included ? FastTheme.textMuted : FastTheme.textDim)),
          const SizedBox(width: 6),
          Text(text, style: TextStyle(fontSize: 12, color: included ? FastTheme.textMuted : FastTheme.textDim,
              decoration: included ? null : TextDecoration.lineThrough)),
        ],
      ),
    );
  }

  Widget _testimonialSection() {
    return _section('Kullanıcı Yorumları', 'Gerçek kullanıcı deneyimleri', isAlt: true,
      child: Column(
        children: [
          Text('★' * _testimonials[_testimonialIdx]['rating'].toString().length, style: const TextStyle(fontSize: 22, color: FastTheme.accentGold, letterSpacing: 4)),
          const SizedBox(height: 12),
          Text('"${_testimonials[_testimonialIdx]['text']}"', textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 16, color: FastTheme.text, fontStyle: FontStyle.italic, height: 1.7)),
          const SizedBox(height: 12),
          Text('— ${_testimonials[_testimonialIdx]['name']}', style: const TextStyle(fontSize: 13, color: FastTheme.accentGold, fontWeight: FontWeight.w600)),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(_testimonials.length, (i) => GestureDetector(
              onTap: () => setState(() => _testimonialIdx = i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                width: _testimonialIdx == i ? 24 : 8, height: 8, margin: const EdgeInsets.symmetric(horizontal: 4),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(_testimonialIdx == i ? 4 : 4),
                  color: _testimonialIdx == i ? FastTheme.accentGold : FastTheme.border,
                ),
              ),
            )),
          ),
        ],
      ),
    );
  }

  Widget _faqSection() {
    return _section('Sıkça Sorulan Sorular', 'Merak ettikleriniz',
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 700),
        child: Column(
          children: List.generate(_faqs.length, (i) {
            final open = _faqOpen == i;
            return GestureDetector(
              onTap: () => setState(() => _faqOpen = open ? -1 : i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: FastTheme.cardBg,
                  border: Border.all(color: open ? FastTheme.accentGold : FastTheme.border),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(child: Text(_faqs[i]['q'] as String, style: TextStyle(fontSize: 14, color: open ? FastTheme.accentGold : FastTheme.text, fontWeight: FontWeight.w600))),
                        Text(open ? '▾' : '▸', style: const TextStyle(color: FastTheme.textDim, fontSize: 12)),
                      ],
                    ),
                    if (open) ...[
                      const SizedBox(height: 8),
                      Text(_faqs[i]['a'] as String, style: const TextStyle(fontSize: 13, color: FastTheme.textMuted, height: 1.6)),
                    ],
                  ],
                ),
              ),
            );
          }),
        ),
      ),
    );
  }

  Widget _ctaSection() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 60, horizontal: 24),
      decoration: const BoxDecoration(
        gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [FastTheme.bgSecondary, FastTheme.bg]),
      ),
      child: Column(
        children: [
          Text('Yıldız Haritanızı Keşfetmeye Hazır Mısınız?', textAlign: TextAlign.center,
            style: GoogleFonts.cormorantGaramond(fontSize: 32, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
          const SizedBox(height: 10),
          Text('İlişki, aile, bireysel natal veya potansiyel analizi — 21 yıllık göksel döngünüzü keşfetmek için hemen başlatın.',
            textAlign: TextAlign.center, style: const TextStyle(fontSize: 14, color: FastTheme.textDim)),
          const SizedBox(height: 24),
          Wrap(
            spacing: 12, runSpacing: 12,
            children: [
              _goldBtn('🔮 Çift Analizi Başlat', () => _startAnalysis('es_sevgili'), height: 52, fontSize: 16),
              OutlinedButton.icon(
                onPressed: () => _startAnalysis('ebeveyn_cocuk'),
                icon: const Icon(Icons.family_restroom, size: 18),
                label: const Text('👨‍👩‍👧‍👦 Ebeveyn-Çocuk'),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: FastTheme.accentGold, width: 2),
                  foregroundColor: FastTheme.accentGold,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  textStyle: const TextStyle(fontSize: 16),
                ),
              ),
              OutlinedButton.icon(
                onPressed: () => _startAnalysis('bireysel_natal'),
                icon: const Icon(Icons.person, size: 18),
                label: const Text('⭐ Bireysel Natal'),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: FastTheme.accentGold, width: 2),
                  foregroundColor: FastTheme.accentGold,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  textStyle: const TextStyle(fontSize: 16),
                ),
              ),
              OutlinedButton.icon(
                onPressed: () => _startAnalysis('potansiyel_yetenek'),
                icon: const Icon(Icons.auto_awesome, size: 18),
                label: const Text('🌟 Potansiyel Analizi'),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: FastTheme.accentGold, width: 2),
                  foregroundColor: FastTheme.accentGold,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  textStyle: const TextStyle(fontSize: 16),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _footer() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(24, 48, 24, 48),
      decoration: const BoxDecoration(border: Border(top: BorderSide(color: FastTheme.border))),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1100),
        child: Wrap(
          spacing: 48, runSpacing: 32,
          children: [
            SizedBox(
              width: 260,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(width: 40, height: 40, decoration: const BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold),
                    child: const Center(child: Text('F', style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold, fontSize: 18)))),
                  const SizedBox(height: 8),
                  const Text('Fatih Asartepe Sinastri Tekniği (FAST) ile yıldız bağı analizi.', style: TextStyle(fontSize: 12, color: FastTheme.textDim, height: 1.5)),
                ],
              ),
            ),
            _footerCol('Hızlı Linkler', [
              _footerLink('Özellikler', () => _scrollTo(900)),
              _footerLink('Fiyatlandırma', () => _scrollTo(1800)),
              _footerLink('SSS', () => _scrollTo(2600)),
              _footerLink('Analiz Başlat', () => _startAnalysis()),
            ]),
            _footerCol('İletişim', [
              const Text('info@fatihasartepe.com', style: TextStyle(fontSize: 12, color: FastTheme.textDim)),
              const SizedBox(height: 4),
              const Text('© 2024 FAST. Tüm hakları saklıdır.', style: TextStyle(fontSize: 12, color: FastTheme.textDim)),
            ]),
          ],
        ),
      ),
    );
  }

  Widget _footerCol(String title, List<Widget> children) {
    return SizedBox(
      width: 200,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: GoogleFonts.cormorantGaramond(fontSize: 16, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
          const SizedBox(height: 8),
          ...children,
        ],
      ),
    );
  }

  Widget _footerLink(String text, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(text, style: const TextStyle(fontSize: 12, color: FastTheme.textMuted)),
      ),
    );
  }

  Widget _section(String title, String desc, {required Widget child, bool isAlt = false}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 60, horizontal: 24),
      color: isAlt ? FastTheme.bgSecondary : null,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1100),
        child: Column(
          children: [
            Text(title, textAlign: TextAlign.center, style: GoogleFonts.cormorantGaramond(fontSize: 32, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
            const SizedBox(height: 8),
            Text(desc, textAlign: TextAlign.center, style: const TextStyle(fontSize: 14, color: FastTheme.textDim)),
            const SizedBox(height: 40),
            child,
          ],
        ),
      ),
    );
  }
}
