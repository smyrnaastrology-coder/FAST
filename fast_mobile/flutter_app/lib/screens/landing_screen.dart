import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/locale_provider.dart';
import '../services/api_service.dart';
import '../services/revenuecat_service.dart';
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

  Future<void> _onPlanTap(Map p, AppLocalizations l10n) async {
    final productId = (p['productId'] as String?) ?? '';
    if (productId.isEmpty) {
      _startAnalysis();
      return;
    }
    final messenger = ScaffoldMessenger.of(context);
    final ok = await RevenueCatService.purchase(productId);
    if (!mounted) return;
    messenger.showSnackBar(SnackBar(
      content: Text(ok ? l10n.subscribeSuccess : l10n.subscribeCancelled),
    ));
    if (ok) _startAnalysis();
  }

  List<Map<String, dynamic>> _modes(AppLocalizations l10n) => [
    {'key': 'es_sevgili', 'title': l10n.modeEsTitle, 'desc': l10n.modeEsDesc, 'badge': l10n.modeEsBadge, 'icon': '💑'},
    {'key': 'ebeveyn_cocuk', 'title': l10n.modeEbTitle, 'desc': l10n.modeEbDesc, 'badge': l10n.modeEbBadge, 'icon': '👨‍👩‍👧‍👦'},
    {'key': 'bireysel_natal', 'title': l10n.modeNatalTitle, 'desc': l10n.modeNatalDesc, 'badge': l10n.modeNatalBadge, 'icon': '⭐'},
    {'key': 'potansiyel_yetenek', 'title': l10n.modePyTitle, 'desc': l10n.modePyDesc, 'badge': l10n.modePyBadge, 'icon': '🌟'},
  ];

  List<Map<String, String>> _features(AppLocalizations l10n) => [
    {'icon': '🔮', 'title': l10n.feature1Title, 'desc': l10n.feature1Desc},
    {'icon': '🌍', 'title': l10n.feature2Title, 'desc': l10n.feature2Desc},
    {'icon': '🌟', 'title': l10n.feature3Title, 'desc': l10n.feature3Desc},
    {'icon': '📅', 'title': l10n.feature4Title, 'desc': l10n.feature4Desc},
    {'icon': '🧬', 'title': l10n.feature5Title, 'desc': l10n.feature5Desc},
    {'icon': '👑', 'title': l10n.feature6Title, 'desc': l10n.feature6Desc},
    {'icon': '🌙', 'title': l10n.feature7Title, 'desc': l10n.feature7Desc},
    {'icon': '📄', 'title': l10n.feature8Title, 'desc': l10n.feature8Desc},
  ];

  List<Map<String, String>> _howSteps(AppLocalizations l10n) => [
    {'step': '1', 'icon': '📝', 'title': l10n.step1Title, 'desc': l10n.step1Desc},
    {'step': '2', 'icon': '🔮', 'title': l10n.step2Title, 'desc': l10n.step2Desc},
    {'step': '3', 'icon': '📥', 'title': l10n.step3Title, 'desc': l10n.step3Desc},
  ];

  List<Map<String, dynamic>> _plans(AppLocalizations l10n) => [
    {
      'name': l10n.planFreeName, 'badge': l10n.planFreeBadge, 'price': 0, 'desc': l10n.planFreeDesc,
      'features': [l10n.planFreeFeat1, l10n.planFreeFeat2, l10n.planFreeFeat3, l10n.planFreeFeat4, l10n.planFreeFeat5],
      'disabled': [l10n.planFreeDisabled1, l10n.planFreeDisabled2, l10n.planFreeDisabled3, l10n.planFreeDisabled4, l10n.planFreeDisabled5],
      'highlight': false,
    },
    {
      'name': l10n.planPremiumName, 'badge': l10n.planPremiumBadge, 'price': 7.99, 'productId': 'sub_daily', 'interval': 'month', 'desc': l10n.planPremiumDesc,
      'features': [l10n.planPremiumFeat1, l10n.planPremiumFeat2, l10n.planPremiumFeat3, l10n.planPremiumFeat4, l10n.planPremiumFeat5, l10n.planPremiumFeat6, l10n.planPremiumFeat7],
      'disabled': <String>[],
      'highlight': true,
    },
    {
      'name': l10n.planProName, 'badge': l10n.planProBadge, 'price': 49.99, 'productId': 'sub_daily_yearly', 'interval': 'year', 'desc': l10n.planProDesc,
      'features': [l10n.planProFeat1, l10n.planProFeat2, l10n.planProFeat3, l10n.planProFeat4, l10n.planProFeat5],
      'disabled': <String>[],
      'highlight': false,
    },
  ];

  List<Map<String, String>> _testimonials(AppLocalizations l10n) => [
    {'name': l10n.t1Name, 'text': l10n.t1Text},
    {'name': l10n.t2Name, 'text': l10n.t2Text},
    {'name': l10n.t3Name, 'text': l10n.t3Text},
    {'name': l10n.t4Name, 'text': l10n.t4Text},
    {'name': l10n.t5Name, 'text': l10n.t5Text},
  ];

  List<Map<String, String>> _faqs(AppLocalizations l10n) => [
    {'q': l10n.faq1Q, 'a': l10n.faq1A},
    {'q': l10n.faq2Q, 'a': l10n.faq2A},
    {'q': l10n.faq3Q, 'a': l10n.faq3A},
    {'q': l10n.faq4Q, 'a': l10n.faq4A},
    {'q': l10n.faq5Q, 'a': l10n.faq5A},
    {'q': l10n.faq6Q, 'a': l10n.faq6A},
    {'q': l10n.faq7Q, 'a': l10n.faq7A},
    {'q': l10n.faq8Q, 'a': l10n.faq8A},
  ];

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      body: SingleChildScrollView(
        controller: _scrollCtrl,
        child: Column(
          children: [
            _navbar(l10n),
            _hero(l10n),
            _modeSection(l10n),
            _featuresSection(l10n),
            _howSection(l10n),
            _pricingSection(l10n),
            _testimonialSection(l10n),
            _faqSection(l10n),
            _ctaSection(l10n),
            _footer(l10n),
          ],
        ),
      ),
    );
  }

  Widget _navbar(AppLocalizations l10n) {
    final lp = context.read<LocaleProvider>();
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
                  Text('Fast Synastry', style: GoogleFonts.cormorantGaramond(fontSize: 20, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                ],
              ),
            ),
            const SizedBox(width: 12),
            _languageDropdown(lp),
            const Spacer(),
            Flexible(child: SingleChildScrollView(scrollDirection: Axis.horizontal, child: Row(
              children: [
                _navLink(l10n.navFeatures, () => _scrollTo(900)),
                const SizedBox(width: 12),
                _navLink(l10n.navPricing, () => _scrollTo(1800)),
                const SizedBox(width: 12),
                _navLink(l10n.navFaq, () => _scrollTo(2600)),
                const SizedBox(width: 12),
                _goldBtn(l10n.navStartAnalysis, () => _startAnalysis(), height: 34, fontSize: 11),
              ],
            ))),
          ],
        ),
      ),
    );
  }

  Widget _languageDropdown(LocaleProvider lp) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: FastTheme.border),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: lp.locale.languageCode,
          dropdownColor: FastTheme.cardBg,
          icon: const Icon(Icons.language, size: 16, color: FastTheme.accentGold),
          style: const TextStyle(color: FastTheme.text, fontSize: 12),
          items: const [
            DropdownMenuItem(value: 'tr', child: Text('Türkçe', style: TextStyle(color: FastTheme.text, fontSize: 12))),
            DropdownMenuItem(value: 'en', child: Text('English', style: TextStyle(color: FastTheme.text, fontSize: 12))),
            DropdownMenuItem(value: 'es', child: Text('Español', style: TextStyle(color: FastTheme.text, fontSize: 12))),
          ],
          onChanged: (v) {
            if (v != null) lp.setLanguage(v);
          },
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

  Widget _hero(AppLocalizations l10n) {
    final stats = _stats;
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
            child: Text(l10n.heroBadge.toUpperCase(), style: const TextStyle(color: FastTheme.accentGold, fontSize: 11, letterSpacing: 1)),
          ),
          const SizedBox(height: 24),
          Text.rich(
            TextSpan(
              text: l10n.heroTitle,
              style: GoogleFonts.cormorantGaramond(fontSize: 48, fontWeight: FontWeight.w700, color: FastTheme.text, height: 1.15),
              children: [TextSpan(text: l10n.heroTitleAccent, style: const TextStyle(color: FastTheme.accentGold, shadows: [Shadow(color: FastTheme.accentGoldGlow, blurRadius: 40)]))],
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 20),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 600),
            child: Text(l10n.heroSubtitle,
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
            child: Text(l10n.heroDisclaimer,
              textAlign: TextAlign.center, style: const TextStyle(color: FastTheme.textMuted, fontSize: 11, height: 1.5)),
          ),
          const SizedBox(height: 32),
          Wrap(
            alignment: WrapAlignment.center,
            spacing: 16,
            runSpacing: 12,
            children: [
              _goldBtn(l10n.freeAnalysis, () => _startAnalysis(), height: 50, fontSize: 14),
              OutlinedButton.icon(
                onPressed: () => _scrollTo(400),
                icon: const Icon(Icons.arrow_downward, size: 18, color: FastTheme.accentGold),
                label: Text(l10n.chooseAnalysisType, style: const TextStyle(color: FastTheme.accentGold, fontSize: 14)),
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
              _stat('${stats['total_analysis']}+', l10n.statAnalysis),
              const SizedBox(width: 40),
              _stat('21', l10n.statYearCycle),
              const SizedBox(width: 40),
              _stat('${stats['total_cities']}+', l10n.statCities),
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

  Widget _modeSection(AppLocalizations l10n) {
    return _section(
      l10n.modeSectionTitle,
      l10n.modeSectionDesc,
      isAlt: true,
      child: Wrap(
        spacing: 20,
        runSpacing: 20,
        children: _modes(l10n).map((m) => _modeCard(m)).toList(),
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

  Widget _featuresSection(AppLocalizations l10n) {
    return _section(l10n.featuresTitle, l10n.featuresDesc,
      child: Wrap(
        spacing: 16,
        runSpacing: 16,
        children: _features(l10n).map((f) => Container(
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

  Widget _howSection(AppLocalizations l10n) {
    return _section(l10n.howTitle, l10n.howDesc, isAlt: true,
      child: Column(
        children: [
          Wrap(
            spacing: 24, runSpacing: 24,
            children: _howSteps(l10n).map((s) => Container(
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
          _goldBtn(l10n.howStart, () => _startAnalysis(), height: 50, fontSize: 14),
        ],
      ),
    );
  }

  Widget _pricingSection(AppLocalizations l10n) {
    return _section(l10n.pricingTitle, l10n.pricingDesc,
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              GestureDetector(
                onTap: () => setState(() => _priceYearly = false),
                child: Text(l10n.pricingMonthly, style: TextStyle(fontSize: 13, color: _priceYearly ? FastTheme.textDim : FastTheme.accentGold, fontWeight: _priceYearly ? FontWeight.normal : FontWeight.w600)),
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
                  text: '${l10n.pricingYearly} ',
                  style: TextStyle(fontSize: 13, color: _priceYearly ? FastTheme.accentGold : FastTheme.textDim, fontWeight: _priceYearly ? FontWeight.w600 : FontWeight.normal),
                  children: [TextSpan(text: l10n.pricingDiscount, style: const TextStyle(color: FastTheme.success, fontSize: 10))],
                )),
              ),
            ],
          ),
          const SizedBox(height: 32),
          Wrap(
            spacing: 20, runSpacing: 20,
            children: _plans(l10n).map((p) => _planCard(p, l10n)).toList(),
          ),
        ],
      ),
    );
  }

  String _fmt(num v) {
    if (v == v.roundToDouble() && v < 100) return v.toStringAsFixed(0);
    return v.toStringAsFixed(2).replaceFirst(RegExp(r'\.?0+$'), '');
  }

  /// Plan buton etiketi: TR'de PRO'YA BAŞLA / PREMIUM'A BAŞLA
  /// (ünlüyle biterse 'YA, ünsüzle biterse 'A). Diğer dillerde l10n şablonu.
  String _planStartLabel(String name, AppLocalizations l10n) {
    if (Localizations.localeOf(context).languageCode != 'tr') {
      return l10n.planStart(name);
    }
    final p = name.toUpperCase();
    const vowels = 'AEIOUİÖÜ';
    final last = p.isNotEmpty ? p[p.length - 1] : '';
    return '$p${vowels.contains(last) ? "'YA BAŞLA" : "'A BAŞLA"}';
  }

  Widget _planCard(Map p, AppLocalizations l10n) {
    final highlight = p['highlight'] as bool;
    final price = p['price'] as num;
    // RevenueCat'ten bölgesel fiyat: ürün ID'sine göre (örn. '7.99').
    // Yoksa eski TL kopya ile fallback.
    final productId = (p['productId'] as String?) ?? '';
    final rcPrice = RevenueCatService.priceFor(productId);
    final interval = p['interval'] as String? ?? 'month';
    final perLabel = interval == 'year' ? l10n.planPerYear : l10n.planPerMonth;
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
                  ? Text(l10n.planFree, style: GoogleFonts.cormorantGaramond(fontSize: 28, fontWeight: FontWeight.w700, color: FastTheme.accentGold))
                  : Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(rcPrice.isNotEmpty ? rcPrice : '\$${_fmt(price)}', style: GoogleFonts.cormorantGaramond(fontSize: 32, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                        Text(perLabel, style: const TextStyle(fontSize: 13, color: FastTheme.textDim)),
                      ],
                    ),
              const SizedBox(height: 16),
              ...((p['features'] as List).map((f) => _planFeat(f as String, true))),
              ...((p['disabled'] as List).map((f) => _planFeat(f as String, false))),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: highlight
                    ? _goldBtn(p['price'] == 0 ? l10n.planTrial : _planStartLabel(p['name'] as String, l10n), () => _onPlanTap(p, l10n), height: 44, fontSize: 13)
                    : OutlinedButton(
                        onPressed: () => _onPlanTap(p, l10n),
                        style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: FastTheme.border),
                          foregroundColor: FastTheme.text,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: Text(p['price'] == 0 ? l10n.planTrial : _planStartLabel(p['name'] as String, l10n), style: const TextStyle(fontSize: 13)),
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

  Widget _testimonialSection(AppLocalizations l10n) {
    final testimonials = _testimonials(l10n);
    return _section(l10n.testimonialsTitle, l10n.testimonialsDesc, isAlt: true,
      child: Column(
        children: [
          const Text('★★★★★', style: TextStyle(fontSize: 22, color: FastTheme.accentGold, letterSpacing: 4)),
          const SizedBox(height: 12),
          Text('"${testimonials[_testimonialIdx]['text']}"', textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 16, color: FastTheme.text, fontStyle: FontStyle.italic, height: 1.7)),
          const SizedBox(height: 12),
          Text('— ${testimonials[_testimonialIdx]['name']}', style: const TextStyle(fontSize: 13, color: FastTheme.accentGold, fontWeight: FontWeight.w600)),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(testimonials.length, (i) => GestureDetector(
              onTap: () => setState(() => _testimonialIdx = i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                width: _testimonialIdx == i ? 24 : 8, height: 8, margin: const EdgeInsets.symmetric(horizontal: 4),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(4),
                  color: _testimonialIdx == i ? FastTheme.accentGold : FastTheme.border,
                ),
              ),
            )),
          ),
        ],
      ),
    );
  }

  Widget _faqSection(AppLocalizations l10n) {
    final faqs = _faqs(l10n);
    return _section(l10n.faqTitle, l10n.faqDesc,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 700),
        child: Column(
          children: List.generate(faqs.length, (i) {
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
                        Expanded(child: Text(faqs[i]['q'] as String, style: TextStyle(fontSize: 14, color: open ? FastTheme.accentGold : FastTheme.text, fontWeight: FontWeight.w600))),
                        Text(open ? '▾' : '▸', style: const TextStyle(color: FastTheme.textDim, fontSize: 12)),
                      ],
                    ),
                    if (open) ...[
                      const SizedBox(height: 8),
                      Text(faqs[i]['a'] as String, style: const TextStyle(fontSize: 13, color: FastTheme.textMuted, height: 1.6)),
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

  Widget _ctaSection(AppLocalizations l10n) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 60, horizontal: 24),
      decoration: const BoxDecoration(
        gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [FastTheme.bgSecondary, FastTheme.bg]),
      ),
      child: Column(
        children: [
          Text(l10n.ctaTitle, textAlign: TextAlign.center,
            style: GoogleFonts.cormorantGaramond(fontSize: 32, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
          const SizedBox(height: 10),
          Text(l10n.ctaDesc,
            textAlign: TextAlign.center, style: const TextStyle(fontSize: 14, color: FastTheme.textDim)),
          const SizedBox(height: 24),
          Wrap(
            spacing: 12, runSpacing: 12,
            children: [
              _goldBtn(l10n.ctaCouple, () => _startAnalysis('es_sevgili'), height: 52, fontSize: 16),
              OutlinedButton.icon(
                onPressed: () => _startAnalysis('ebeveyn_cocuk'),
                icon: const Icon(Icons.family_restroom, size: 18),
                label: Text(l10n.ctaParentChild),
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
                label: Text(l10n.ctaNatal),
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
                label: Text(l10n.ctaPotential),
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

  Widget _footer(AppLocalizations l10n) {
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
                  Text(l10n.footerTagline, style: const TextStyle(fontSize: 12, color: FastTheme.textDim, height: 1.5)),
                ],
              ),
            ),
            _footerCol(l10n.footerQuickLinks, [
              _footerLink(l10n.navFeatures, () => _scrollTo(900)),
              _footerLink(l10n.navPricing, () => _scrollTo(1800)),
              _footerLink(l10n.navFaq, () => _scrollTo(2600)),
              _footerLink(l10n.navStartAnalysis, () => _startAnalysis()),
            ]),
            _footerCol(l10n.footerContact, [
              const Text('info@fatihasartepe.com', style: TextStyle(fontSize: 12, color: FastTheme.textDim)),
              const SizedBox(height: 4),
              Text(l10n.footerRights, style: const TextStyle(fontSize: 12, color: FastTheme.textDim)),
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