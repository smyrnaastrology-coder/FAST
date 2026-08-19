import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:open_file/open_file.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/analysis_request.dart';
import '../providers/analysis_provider.dart';
import '../providers/locale_provider.dart';
import '../services/api_service.dart';
import '../widgets/language_switcher.dart';
import '../widgets/section_card.dart' as w;

class AnalyzerScreen extends StatefulWidget {
  final String initialMode;
  const AnalyzerScreen({super.key, this.initialMode = 'es_sevgili'});

  @override
  State<AnalyzerScreen> createState() => _AnalyzerScreenState();
}

class _AnalyzerScreenState extends State<AnalyzerScreen> {
  final _api = ApiService();

  // Mode
  String _mode = 'es_sevgili';

  // Form controllers
  final _p1IsimCtrl = TextEditingController();
  final _p1TarihCtrl = TextEditingController();
  final _p1SaatCtrl = TextEditingController(text: '12:00');
  final _p2IsimCtrl = TextEditingController();
  final _p2TarihCtrl = TextEditingController();
  final _p2SaatCtrl = TextEditingController(text: '12:00');
  final _eventTarihCtrl = TextEditingController();
  final _eventSaatCtrl = TextEditingController(text: '12:00');

  // Location
  String _seciliUlke = 'Türkiye';
  String _seciliSehir = 'İstanbul';
  final _latCtrl = TextEditingController(text: '41.0082');
  final _lonCtrl = TextEditingController(text: '28.9784');
  String? _geoHint;
  Map<String, dynamic>? _lokasyonDB;
  bool _dbLoading = true;

  // Ebeveyn
  String _ebeveynRolu = 'anne';

  // Astrocartography selector
  String _astroUlke = '';
  String _astroSehir = '';

  // Wikipedia
  Map<String, String> _wikiPages = {};

  // UI state
  int _expandedHayat = -1;
  bool _menuOpen = false;
  String _chartTab = 'situa_a';
  Map<String, dynamic>? _prevSimData;

  String get _modKey {
    if (_mode == 'es_sevgili') return 'es_sevgili';
    if (_mode == 'ebeveyn_cocuk') return 'ebeveyn_cocuk';
    if (_mode == 'potansiyel_yetenek') return 'potansiyel_yetenek';
    return 'bireysel_natal';
  }

  bool get _ikinciKisiGerekli => _modKey == 'es_sevgili' || _modKey == 'ebeveyn_cocuk';
  bool get _eventGerekli => _modKey == 'es_sevgili';
  bool get _ebeveynMod => _modKey == 'ebeveyn_cocuk';
  bool get _natalMod => _modKey == 'bireysel_natal';
  bool get _potansiyelMod => _modKey == 'potansiyel_yetenek';
  bool get _tekKisiMod => _natalMod || _potansiyelMod;
  bool get _isNatal => _mode == 'bireysel_natal';
  bool get _isEs => _mode == 'es_sevgili';
  bool get _isEb => _mode == 'ebeveyn_cocuk';
  bool get _isPy => _mode == 'potansiyel_yetenek';

  @override
  void initState() {
    super.initState();
    _mode = widget.initialMode;
    _loadDB();
  }

  static const Map<String, dynamic> _fallbackDB = {
    'ulkeler': ['Türkiye', 'Almanya', 'Fransa', 'İngiltere', 'ABD', 'Rusya', 'İtalya', 'İspanya', 'Hollanda', 'Belçika', 'Avusturya', 'İsviçre', 'Yunanistan', 'Mısır', 'Brezilya', 'Kanada', 'Avustralya', 'Japonya', 'Çin', 'Hindistan'],
    'sehirler': {
      'Türkiye': ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Adana', 'Mersin', 'Konya', 'Gaziantep', 'Diyarbakır', 'Eskişehir', 'Samsun', 'Trabzon', 'Erzurum', 'Malatya', 'Kayseri', 'Van', 'Şanlıurfa', 'Tekirdağ', 'Muğla', 'Aydın', 'Balıkesir', 'Denizli', 'Hatay', 'Sakarya', 'Manisa'],
      'Almanya': ['Berlin', 'Münih', 'Hamburg', 'Frankfurt', 'Köln', 'Stuttgart', 'Düsseldorf', 'Bremen', 'Hannover', 'Nürnberg'],
      'Fransa': ['Paris', 'Marsilya', 'Lyon', 'Toulouse', 'Nice', 'Bordeaux', 'Lille', 'Strazburg'],
      'İngiltere': ['Londra', 'Manchester', 'Birmingham', 'Liverpool', 'Oxford', 'Cambridge', 'Edinburgh'],
      'ABD': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Francisco'],
      'Rusya': ['Moskova', 'Sankt-Peterburg', 'Novosibirsk', 'Yekaterinburg', 'Kazan'],
      'İtalya': ['Roma', 'Milano', 'Napoli', 'Torino', 'Floransa', 'Venedik', 'Bologna'],
      'İspanya': ['Madrid', 'Barselona', 'Valensiya', 'Sevilla', 'Bilbao', 'Malaga'],
      'Hollanda': ['Amsterdam', 'Rotterdam', 'Lahey', 'Utrecht', 'Eindhoven'],
      'Belçika': ['Brüksel', 'Anvers', 'Gent', 'Brugge', 'Liège'],
    }
  };

  Future<void> _loadDB() async {
    try {
      final d = await _api.getUlkelerRaw();
      if (d is Map) {
        _lokasyonDB = d.cast<String, dynamic>();
      }
    } catch (_) {
      _lokasyonDB = Map<String, dynamic>.from(_fallbackDB);
    }
    if (_ulkeler != null && _ulkeler!.isNotEmpty && !_ulkeler!.contains(_seciliUlke)) {
      _seciliUlke = _ulkeler!.first;
    }
    if (_sehirler != null && _sehirler!.isNotEmpty && !_sehirler!.contains(_seciliSehir)) {
      _seciliSehir = _sehirler!.first;
    }
    _dbLoading = false;
    if (mounted) setState(() {});
  }

  List<String>? get _ulkeler => (_lokasyonDB?['ulkeler'] as List?)?.cast<String>();
  List<String>? get _sehirler => (_lokasyonDB?['sehirler']?[_seciliUlke] as List?)?.cast<String>();
  List<String>? get _astroSehirler => _astroUlke.isNotEmpty ? (_lokasyonDB?['sehirler']?[_astroUlke] as List?)?.cast<String>() : null;

  String _formatDate(DateTime d) {
    return '${d.day.toString().padLeft(2, '0')}.${d.month.toString().padLeft(2, '0')}.${d.year}';
  }

  DateTime? _parseDate(String text) {
    try {
      final parts = text.trim().split(' ');
      if (parts.length == 3) {
        final gun = int.tryParse(parts[0]);
        const aylar = ['ocak', 'şubat', 'mart', 'nisan', 'mayıs', 'haziran', 'temmuz', 'ağustos', 'eylül', 'ekim', 'kasım', 'aralık'];
        final ay = aylar.indexOf(parts[1].toLowerCase());
        final yil = int.tryParse(parts[2]);
        if (gun != null && ay >= 0 && yil != null) return DateTime(yil, ay + 1, gun);
      }
      final f = text.trim().split('-');
      if (f.length == 3) {
        return DateTime(int.tryParse(f[0]) ?? 0, int.tryParse(f[1]) ?? 0, int.tryParse(f[2]) ?? 0);
      }
      final g = text.trim().split('.');
      if (g.length == 3) {
        return DateTime(int.tryParse(g[2]) ?? 0, int.tryParse(g[1]) ?? 0, int.tryParse(g[0]) ?? 0);
      }
    } catch (_) {}
    return null;
  }

  Future<void> _pickDate(TextEditingController ctrl) async {
    final baslangic = _parseDate(ctrl.text) ?? DateTime.now();
    final d = await showDatePicker(
      context: context,
      initialDate: baslangic,
      firstDate: DateTime(1900),
      lastDate: DateTime(2100),
    );
    if (d != null) {
      ctrl.text = _formatDate(d);
    }
  }

  Future<void> _pickTime(TextEditingController ctrl) async {
    final t = await showTimePicker(context: context, initialTime: TimeOfDay.now());
    if (t != null) {
      ctrl.text = '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
    }
  }

  Future<void> _geoCode(String sehir) async {
    if (sehir.length < 3) return;
    try {
      final r = await _api.geocode(sehir);
      setState(() {
        _latCtrl.text = r['lat'].toStringAsFixed(4);
        _lonCtrl.text = r['lon'].toStringAsFixed(4);
        _seciliSehir = r['city'] ?? sehir;
        _geoHint = '${r['city']}, ${r['country'] ?? '—'} (${r['lat'].toStringAsFixed(4)}, ${r['lon'].toStringAsFixed(4)})';
      });
    } catch (_) {
      setState(() => _geoHint = AppLocalizations.of(context).analyzerCityNotFound);
    }
  }

  String _normalizeDate(String text) {
    final parsed = _parseDate(text);
    if (parsed != null) return '${parsed.year}-${parsed.month.toString().padLeft(2, '0')}-${parsed.day.toString().padLeft(2, '0')}';
    return text;
  }

  void _submit() {
    final l10n = AppLocalizations.of(context);
    if (_p1TarihCtrl.text.isEmpty) { _snack(l10n.analyzerDateRequired); return; }
    if (_ikinciKisiGerekli && _p2TarihCtrl.text.isEmpty) { _snack(l10n.analyzerDate2Required); return; }
    if (_tekKisiMod && _p1IsimCtrl.text.trim().isEmpty) { _snack(l10n.analyzerNameRequired); return; }

    final lp = context.read<LocaleProvider>();
    final req = AnalysisRequest(
      p1Isim: _p1IsimCtrl.text,
      p1Tarih: _normalizeDate(_p1TarihCtrl.text),
      p1Saat: _p1SaatCtrl.text,
      p2Isim: _p2IsimCtrl.text,
      p2Tarih: _ikinciKisiGerekli ? _normalizeDate(_p2TarihCtrl.text) : _normalizeDate(_p1TarihCtrl.text),
      p2Saat: _p2SaatCtrl.text,
      eventTarih: _eventGerekli ? _normalizeDate(_eventTarihCtrl.text) : '',
      eventSaat: _eventSaatCtrl.text,
      ebeveynRolu: _ebeveynRolu,
      city: _seciliSehir,
      country: _seciliUlke,
      lat: double.tryParse(_latCtrl.text) ?? 41.0082,
      lon: double.tryParse(_lonCtrl.text) ?? 28.9784,
      mod: _modKey,
      lang: lp.locale.languageCode,
    );

    context.read<AnalysisProvider>().reset();
    context.read<AnalysisProvider>().analizYap(req);
    setState(() => _menuOpen = false);
  }

  void _snack(String msg) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));

  Future<void> _openUrl(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  void _loadWikiPages(Map<String, dynamic>? simData) async {
    if (simData == null) return;
    final top = simData['top_sehirler'] as Map?;
    if (top == null) return;
    final sehirler = <String>{};
    for (final katList in top.values) {
      for (final c in (katList as List?)?.take(5) ?? []) {
        final s = (c['sehir']?.toString() ?? '').split(',')[0].trim();
        if (s.isNotEmpty) sehirler.add(s);
      }
    }
    for (final s in sehirler) {
      if (_wikiPages.containsKey(s)) continue;
      try {
        final r = await _api.getSehirBilgi(s);
        if (r['page'] != null && mounted) {
          setState(() => _wikiPages[s] = r['page'].toString());
        }
      } catch (_) {}
    }
  }

  @override
  void dispose() {
    _p1IsimCtrl.dispose();
    _p1TarihCtrl.dispose();
    _p1SaatCtrl.dispose();
    _p2IsimCtrl.dispose();
    _p2TarihCtrl.dispose();
    _p2SaatCtrl.dispose();
    _eventTarihCtrl.dispose();
    _eventSaatCtrl.dispose();
    _latCtrl.dispose();
    _lonCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Consumer<AnalysisProvider>(
      builder: (context, provider, _) {
        return Scaffold(
          backgroundColor: FastTheme.bg,
          appBar: _isWide(context) ? null : AppBar(
            leading: Builder(builder: (ctx) => IconButton(
              icon: const Icon(Icons.menu),
              onPressed: () => Scaffold.of(ctx).openDrawer(),
            )),
            title: Text('FAST — ${_modeLabel(l10n)}'),
            actions: [
              const LanguageSwitcher(),
              IconButton(
                icon: const Icon(Icons.home),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          drawer: _isWide(context) ? null : _buildDrawer(provider, l10n),
          body: _isWide(context) ? _buildWideLayout(provider, l10n) : _buildNarrowLayout(provider, l10n),
        );
      },
    );
  }

  bool _isWide(BuildContext context) => MediaQuery.of(context).size.width > 768;

  String _modeLabel(AppLocalizations l10n) {
    switch (_mode) {
      case 'es_sevgili': return l10n.modeEsTitle;
      case 'ebeveyn_cocuk': return l10n.modeEbTitle;
      case 'potansiyel_yetenek': return l10n.modePyTitle;
      case 'bireysel_natal': return l10n.modeNatalTitle;
      default: return _mode;
    }
  }

  Widget _buildWideLayout(AnalysisProvider provider, AppLocalizations l10n) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 280,
          child: Material(
            color: FastTheme.bgSecondary,
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: _sidebarContent(provider, l10n),
            ),
          ),
        ),
        const VerticalDivider(width: 1, color: FastTheme.border),
        Expanded(
          child: _mainContent(provider, l10n),
        ),
      ],
    );
  }

  Widget _buildNarrowLayout(AnalysisProvider provider, AppLocalizations l10n) {
    if (provider.status == AnalysisStatus.success && provider.result != null) {
      return _mainContent(provider, l10n);
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          _narrowSidebar(provider, l10n),
          if (provider.status == AnalysisStatus.error && provider.error != null)
            Container(
              width: double.infinity, margin: const EdgeInsets.only(bottom: 16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: FastTheme.danger.withValues(alpha: 0.1),
                border: Border.all(color: FastTheme.danger),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(provider.error!, style: const TextStyle(color: FastTheme.danger, fontSize: 13)),
            ),
          if (provider.status == AnalysisStatus.loading)
            _loadingSection(l10n),
        ],
      ),
    );
  }

  // Inline sidebar for narrow screens (shown inside main content before results)
  Widget _narrowSidebar(AnalysisProvider provider, AppLocalizations l10n) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        border: Border.all(color: FastTheme.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Container(width: 32, height: 32, decoration: const BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold, boxShadow: [BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 16)]),
              child: const Center(child: Text('F', style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold, fontSize: 16)))),
            const SizedBox(width: 8),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('FAST', style: GoogleFonts.cormorantGaramond(fontSize: 16, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
              Text(l10n.analyzerSimulationSelect, style: const TextStyle(color: FastTheme.textDim, fontSize: 9)),
            ]),
          ]),
          const SizedBox(height: 8),
          ..._modeCards(l10n),
          const SizedBox(height: 4),
          if (_isEs) _esForm(l10n),
          if (_isEb) _ebForm(l10n),
          if (_isPy) _pyForm(l10n),
          if (_isNatal) _natalForm(l10n),
          const SizedBox(height: 4),
          _locationForm(l10n),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: provider.status == AnalysisStatus.loading ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: FastTheme.accentGold,
                foregroundColor: FastTheme.bg,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: Text(provider.status == AnalysisStatus.loading ? l10n.analyzerLoading : l10n.analyzerStart,
                  style: const TextStyle(fontWeight: FontWeight.w700, letterSpacing: 1)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDrawer(AnalysisProvider provider, AppLocalizations l10n) {
    return Drawer(
      backgroundColor: FastTheme.bgSecondary,
      width: 280,
      child: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: _sidebarContent(provider, l10n),
        ),
      ),
    );
  }

  // ========== SIDEBAR ==========
  Widget _sidebarContent(AnalysisProvider provider, AppLocalizations l10n) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Logo
        Center(
          child: Column(
            children: [
              Container(width: 72, height: 72, decoration: const BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold, boxShadow: [BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 24)]),
                child: const Center(child: Text('F', style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold, fontSize: 32)))),
              const SizedBox(height: 8),
              Text(l10n.homeTitle, textAlign: TextAlign.center,
                style: GoogleFonts.cormorantGaramond(fontSize: 18, fontWeight: FontWeight.w700, color: FastTheme.accentGold, height: 1.3)),
              Text(l10n.analyzerSidebarTagline, style: const TextStyle(color: FastTheme.textMuted, fontSize: 10, letterSpacing: 2)),
              Text(l10n.analyzerSidebarVersion, style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
            ],
          ),
        ),
        const SizedBox(height: 16),
        const Divider(color: FastTheme.border),
        const SizedBox(height: 8),

        // Mode cards
        ..._modeCards(l10n),

        const SizedBox(height: 8),

        // Forms based on mode
        if (_isEs) _esForm(l10n),
        if (_isEb) _ebForm(l10n),
        if (_isPy) _pyForm(l10n),
        if (_isNatal) _natalForm(l10n),

        const SizedBox(height: 8),

        // Location
        _locationForm(l10n),

        const SizedBox(height: 16),

        // Submit button
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: provider.status == AnalysisStatus.loading ? null : _submit,
            style: ElevatedButton.styleFrom(
              backgroundColor: FastTheme.accentGold,
              foregroundColor: FastTheme.bg,
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: Text(provider.status == AnalysisStatus.loading ? l10n.analyzerLoading : l10n.analyzerStart,
                style: const TextStyle(fontWeight: FontWeight.w700, letterSpacing: 1)),
          ),
        ),
      ],
    );
  }

  List<Widget> _modeCards(AppLocalizations l10n) {
    final modes = [
      {'key': 'es_sevgili', 'title': l10n.modeEsTitle, 'desc': l10n.analyzerModeEsDesc, 'img': 'assets/cift.png'},
      {'key': 'ebeveyn_cocuk', 'title': l10n.modeEbTitle, 'desc': l10n.analyzerModeEbDesc, 'img': 'assets/ebeveyn_cocuk.png'},
      {'key': 'bireysel_natal', 'title': l10n.modeNatalTitle, 'desc': l10n.analyzerModeNatalDesc, 'img': 'assets/natal.png'},
      {'key': 'potansiyel_yetenek', 'title': l10n.modePyTitle, 'desc': l10n.analyzerModePyDesc, 'img': 'assets/potansiyel_yetenek.png'},
    ];
    return modes.map((m) {
      final key = m['key'] as String;
      final active = _mode == key;
      return GestureDetector(
        onTap: () => setState(() {
          _mode = key; _menuOpen = false;
          context.read<AnalysisProvider>().reset();
          _p1IsimCtrl.clear(); _p1TarihCtrl.clear(); _p1SaatCtrl.text = '12:00';
          _p2IsimCtrl.clear(); _p2TarihCtrl.clear(); _p2SaatCtrl.text = '12:00';
          _eventTarihCtrl.clear(); _eventSaatCtrl.text = '12:00';
        }),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          margin: const EdgeInsets.only(bottom: 6),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: active ? FastTheme.cardBgHover : FastTheme.cardBg,
            border: Border.all(color: active ? FastTheme.accentGold : FastTheme.border),
            borderRadius: BorderRadius.circular(12),
            boxShadow: active ? [const BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 12)] : null,
          ),
          child: Row(
            children: [
              Container(
                width: 40, height: 40,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: active ? FastTheme.accentGold : FastTheme.border),
                ),
                clipBehavior: Clip.antiAlias,
                child: Image.asset(m['img'] as String, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const SizedBox.shrink()),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(m['title'] as String, style: GoogleFonts.cormorantGaramond(fontSize: 13, fontWeight: FontWeight.w700, color: active ? FastTheme.accentGold : FastTheme.textMuted)),
                    Text(m['desc'] as String, style: const TextStyle(fontSize: 10, color: FastTheme.textDim)),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }).toList();
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 12, bottom: 6),
      child: Text(title, style: GoogleFonts.cormorantGaramond(fontSize: 14, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
    );
  }

  Widget _formField(String label, TextEditingController ctrl, {IconData? icon, TextInputType? keyboardType}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TextField(
        controller: ctrl,
        keyboardType: keyboardType,
        style: const TextStyle(color: FastTheme.text, fontSize: 13),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1),
          prefixIcon: icon != null ? Icon(icon, size: 18, color: FastTheme.accentGold) : null,
        ),
      ),
    );
  }

  void _applyDateMask(TextEditingController ctrl) {
    final t = ctrl.text;
    if (t.contains(RegExp(r'[a-zA-ZğüşıöçĞÜŞİÖÇ]'))) return;
    final digits = t.replaceAll(RegExp(r'\D'), '');
    final sb = StringBuffer();
    for (var i = 0; i < digits.length && i < 8; i++) {
      if (i == 2 || i == 4) sb.write('.');
      sb.write(digits[i]);
    }
    final fmt = sb.toString();
    if (fmt != t) {
      ctrl.text = fmt;
      ctrl.selection = TextSelection.collapsed(offset: fmt.length);
    }
  }

  void _applyTimeMask(TextEditingController ctrl) {
    final t = ctrl.text;
    if (t.contains(RegExp(r'[a-zA-Z]'))) return;
    final digits = t.replaceAll(RegExp(r'\D'), '');
    final sb = StringBuffer();
    for (var i = 0; i < digits.length && i < 4; i++) {
      if (i == 2) sb.write(':');
      sb.write(digits[i]);
    }
    final fmt = sb.toString();
    if (fmt != t) {
      ctrl.text = fmt;
      ctrl.selection = TextSelection.collapsed(offset: fmt.length);
    }
  }

  Widget _dateField(String label, TextEditingController ctrl, AppLocalizations l10n, {bool zorunlu = true}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TextField(
        controller: ctrl,
        readOnly: false,
        keyboardType: TextInputType.number,
        style: const TextStyle(color: FastTheme.text, fontSize: 13),
        decoration: InputDecoration(
          labelText: zorunlu ? label : '$label (${l10n.analyzerOptional})',
          hintText: l10n.analyzerBirthDateHint,
          hintStyle: const TextStyle(color: FastTheme.textDim, fontSize: 11),
          labelStyle: const TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1),
          prefixIcon: const Icon(Icons.calendar_today, size: 18, color: FastTheme.accentGold),
          suffixIcon: IconButton(icon: const Icon(Icons.date_range, size: 18, color: FastTheme.accentGold), onPressed: () => _pickDate(ctrl)),
        ),
        onChanged: (_) => _applyDateMask(ctrl),
      ),
    );
  }

  Widget _timeField(String label, TextEditingController ctrl) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TextField(
        controller: ctrl,
        readOnly: false,
        keyboardType: TextInputType.number,
        style: const TextStyle(color: FastTheme.text, fontSize: 13),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1),
          prefixIcon: const Icon(Icons.access_time, size: 18, color: FastTheme.accentGold),
          suffixIcon: IconButton(icon: const Icon(Icons.schedule, size: 18, color: FastTheme.accentGold), onPressed: () => _pickTime(ctrl)),
        ),
        onTap: () => _pickTime(ctrl),
        onChanged: (_) => _applyTimeMask(ctrl),
      ),
    );
  }

  Widget _dropdownField(String label, List<String> items, String value, ValueChanged<String?> onChanged, {Map<String, String>? labels}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: DropdownButtonFormField<String>(
        value: items.contains(value) ? value : (items.isNotEmpty ? items.first : null),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1),
        ),
        dropdownColor: FastTheme.cardBg,
        style: const TextStyle(color: FastTheme.text, fontSize: 13),
        items: items.map((e) => DropdownMenuItem(value: e, child: Text(labels?[e] ?? e))).toList(),
        onChanged: onChanged,
      ),
    );
  }

  Widget _esForm(AppLocalizations l10n) {
    return Column(
      children: [
        _sectionTitle(l10n.analyzerPerson1),
        _formField(l10n.analyzerName, _p1IsimCtrl, icon: Icons.person),
        _dateField(l10n.analyzerBirthDate, _p1TarihCtrl, l10n),
        _sectionTitle(l10n.analyzerPerson2),
        _formField(l10n.analyzerName, _p2IsimCtrl, icon: Icons.person_outline),
        _dateField(l10n.analyzerBirthDate, _p2TarihCtrl, l10n),
        _sectionTitle(l10n.analyzerMeetingMarriage),
        _dateField(l10n.analyzerDate, _eventTarihCtrl, l10n, zorunlu: false),
        _timeField(l10n.analyzerTime, _eventSaatCtrl),
      ],
    );
  }

  Widget _ebForm(AppLocalizations l10n) {
    return Column(
      children: [
        _sectionTitle(l10n.analyzerParent),
        _formField(l10n.analyzerName, _p1IsimCtrl, icon: Icons.family_restroom),
        _dateField(l10n.analyzerBirthDate, _p1TarihCtrl, l10n),
        _dropdownField(l10n.analyzerRole, ['anne', 'baba'], _ebeveynRolu, (v) => setState(() => _ebeveynRolu = v!),
          labels: {'anne': l10n.analyzerMother, 'baba': l10n.analyzerFather}),
        _sectionTitle(l10n.analyzerChild),
        _formField(l10n.analyzerName, _p2IsimCtrl, icon: Icons.child_care),
        _dateField(l10n.analyzerBirthDate, _p2TarihCtrl, l10n),
        _timeField(l10n.analyzerBirthTime, _p2SaatCtrl),
      ],
    );
  }

  Widget _pyForm(AppLocalizations l10n) {
    return Column(
      children: [
        _sectionTitle(l10n.analyzerPersonalInfo),
        _formField(l10n.analyzerName, _p1IsimCtrl, icon: Icons.person),
        _dateField(l10n.analyzerBirthDate, _p1TarihCtrl, l10n),
        _timeField(l10n.analyzerBirthTime, _p1SaatCtrl),
      ],
    );
  }

  Widget _natalForm(AppLocalizations l10n) {
    return Column(
      children: [
        _sectionTitle(l10n.analyzerPersonalInfo),
        _formField(l10n.analyzerName, _p1IsimCtrl, icon: Icons.person),
        _dateField(l10n.analyzerBirthDate, _p1TarihCtrl, l10n),
        _timeField(l10n.analyzerBirthTime, _p1SaatCtrl),
      ],
    );
  }

  Widget _locationForm(AppLocalizations l10n) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _sectionTitle(l10n.analyzerLocation),
        if (_dbLoading)
          const LinearProgressIndicator()
        else ...[
          _dropdownField(l10n.analyzerCountry, _ulkeler ?? [], _seciliUlke, (v) {
            setState(() { _seciliUlke = v!; _seciliSehir = ''; _geoHint = l10n.analyzerSelectCity; });
          }),
          if (_sehirler != null)
            _dropdownField(l10n.analyzerCity, _sehirler!, _seciliSehir, (v) { setState(() => _seciliSehir = v!); _geoCode(v!); }),
        ],
        Row(
          children: [
            Expanded(child: _formField(l10n.analyzerLatitude, _latCtrl, icon: Icons.explore, keyboardType: TextInputType.numberWithOptions(decimal: true))),
            const SizedBox(width: 8),
            Expanded(child: _formField(l10n.analyzerLongitude, _lonCtrl, icon: Icons.explore, keyboardType: TextInputType.numberWithOptions(decimal: true))),
          ],
        ),
        Text(_geoHint ?? l10n.analyzerSearchHint, style: const TextStyle(color: FastTheme.textDim, fontSize: 9)),
        const SizedBox(height: 6),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => _geoCode(_seciliSehir),
            icon: const Icon(Icons.search, size: 16),
            label: Text(l10n.analyzerSearchLocation, style: const TextStyle(fontSize: 12)),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: FastTheme.border),
              foregroundColor: FastTheme.accentGold,
              padding: const EdgeInsets.symmetric(vertical: 10),
            ),
          ),
        ),
      ],
    );
  }

  // ========== MAIN CONTENT ==========
  Widget _mainContent(AnalysisProvider provider, AppLocalizations l10n) {
    return LayoutBuilder(
      builder: (context, constraints) => SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: BoxConstraints(minWidth: constraints.maxWidth - 48, maxWidth: 1000),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              _header(l10n),

              // Error
              if (provider.status == AnalysisStatus.error && provider.error != null)
                Container(
                  width: double.infinity, margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: FastTheme.danger.withValues(alpha: 0.1),
                    border: Border.all(color: FastTheme.danger),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(provider.error!, style: const TextStyle(color: FastTheme.danger, fontSize: 13)),
                ),

              // Before analysis
              if (provider.status != AnalysisStatus.success && provider.status != AnalysisStatus.loading)
                _beforeAnalysis(l10n),

              // Loading
              if (provider.status == AnalysisStatus.loading)
                _loadingSection(l10n),

              // Results
              if (provider.status == AnalysisStatus.success && provider.result != null)
                _resultsSection(provider, l10n),
            ],
          ),
        ),
      ),
    );
  }

  Widget _header(AppLocalizations l10n) {
    return Container(
      margin: const EdgeInsets.only(bottom: 32),
      child: Column(
        children: [
          Container(width: 72, height: 72, decoration: const BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold, boxShadow: [BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 24)]),
            child: const Center(child: Text('F', style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold, fontSize: 32)))),
          const SizedBox(height: 12),
          Text(l10n.homeTitle.replaceAll('\n', ' '), style: GoogleFonts.cormorantGaramond(fontSize: 32, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
          Text('FAST — ${l10n.appSlogan}', style: const TextStyle(color: FastTheme.textMuted, fontSize: 13, letterSpacing: 2)),
          const SizedBox(height: 8),
          Text(l10n.analyzerHeaderDesc,
            style: const TextStyle(color: FastTheme.textDim, fontSize: 11), textAlign: TextAlign.center),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: FastTheme.cardBg,
              border: Border.all(color: FastTheme.border),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(l10n.heroDisclaimer,
              textAlign: TextAlign.center, style: const TextStyle(color: FastTheme.textMuted, fontSize: 10, height: 1.5)),
          ),
        ],
      ),
    );
  }

  Widget _beforeAnalysis(AppLocalizations l10n) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(color: FastTheme.cardBg, border: Border.all(color: FastTheme.border), borderRadius: BorderRadius.circular(16)),
      child: Column(
        children: [
          Text(_mode == 'es_sevgili' ? '💑' : _mode == 'ebeveyn_cocuk' ? '👨‍👩‍👧‍👦' : _mode == 'bireysel_natal' ? '⭐' : '🌟',
            style: const TextStyle(fontSize: 48)),
          const SizedBox(height: 16),
          ...(_mode == 'es_sevgili' ? _featureList([
            l10n.analyzerFeaturesEs1,
            l10n.analyzerFeaturesEs2,
            l10n.analyzerFeaturesEs3,
            l10n.analyzerFeaturesEs4,
            l10n.analyzerFeaturesEs5,
            l10n.analyzerFeaturesEs6,
            l10n.analyzerFeaturesEs7,
            l10n.analyzerFeaturesEs8,
            l10n.analyzerFeaturesEs9,
            l10n.analyzerFeaturesEs10,
          ]) : _mode == 'ebeveyn_cocuk' ? _featureList([
            l10n.analyzerFeaturesEb1,
            l10n.analyzerFeaturesEb2,
            l10n.analyzerFeaturesEb3,
            l10n.analyzerFeaturesEb4,
            l10n.analyzerFeaturesEb5,
            l10n.analyzerFeaturesEb6,
            l10n.analyzerFeaturesEb7,
            l10n.analyzerFeaturesEb8,
            l10n.analyzerFeaturesEb9,
            l10n.analyzerFeaturesEb10,
            l10n.analyzerFeaturesEb11,
          ]) : _featureList([
            l10n.analyzerFeaturesPy1,
            l10n.analyzerFeaturesPy2,
            l10n.analyzerFeaturesPy3,
          ])),
        ],
      ),
    );
  }

  List<Widget> _featureList(List<String> items) {
    return items.map((f) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          const SizedBox(width: 8),
          Expanded(child: Text(f, style: const TextStyle(color: FastTheme.textMuted, fontSize: 12, height: 1.6))),
        ],
      ),
    )).toList();
  }

  Widget _loadingSection(AppLocalizations l10n) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 60),
      child: Column(
        children: [
          const SizedBox(width: 48, height: 48, child: CircularProgressIndicator(color: FastTheme.accentGold)),
          const SizedBox(height: 16),
          Text(l10n.loadingSky, style: const TextStyle(color: FastTheme.textMuted, fontSize: 14)),
        ],
      ),
    );
  }

  // ========== RESULTS SECTION ==========
  Widget _resultsSection(AnalysisProvider provider, AppLocalizations l10n) {
    final r = provider.detayliResult ?? provider.result!;
    final sessionId = provider.sessionId ?? '';
    final simData = provider.simData;
    if (simData != _prevSimData) {
      _prevSimData = simData;
      WidgetsBinding.instance.addPostFrameCallback((_) => _loadWikiPages(simData));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(l10n.analyzerResultsTitle, style: const TextStyle(color: FastTheme.textMuted, fontSize: 14, letterSpacing: 1)),
        const SizedBox(height: 16),

        // Score cards
        _scoreCards(r, l10n),

        const SizedBox(height: 24),

        // Results sections
        _buildAllSections(provider, r, sessionId, simData, l10n),

        const SizedBox(height: 24),

        // Charts
        _chartsSection(r, sessionId, l10n),

        const SizedBox(height: 24),

        // PDF
        _pdfSection(provider, r, sessionId, l10n),

        // Sim notification
        if (r['sim_sehir'] != null)
          Container(
            margin: const EdgeInsets.only(top: 16),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: FastTheme.accentGold.withValues(alpha: 0.1),
              border: Border.all(color: FastTheme.accentGold),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(l10n.analyzerSimulationRenewed(r['sim_sehir'].toString()),
              textAlign: TextAlign.center, style: const TextStyle(color: FastTheme.accentGold, fontSize: 13)),
          ),
      ],
    );
  }

  Widget _scoreCards(Map<String, dynamic> r, AppLocalizations l10n) {
    final isPy = _mode == 'potansiyel_yetenek';
    return LayoutBuilder(
      builder: (context, constraints) {
        final cardWidth = (constraints.maxWidth - 12) / (isPy ? 2 : 3);
        return Wrap(
          spacing: 12, runSpacing: 12,
          children: [
            SizedBox(width: cardWidth, child: _scoreCard(l10n.scoreCompatibility,
              r['uyum_orani'] is String
                  ? Column(children: [
                      Text(l10n.scoreGoldenSeal, style: const TextStyle(color: FastTheme.accentGold, fontSize: 14, fontWeight: FontWeight.w700, fontFamily: 'DM Sans')),
                      const SizedBox(height: 4),
                      SizedBox(
                        width: cardWidth - 40,
                        height: 150,
                        child: SingleChildScrollView(
                          child: Text(r['uyum_orani'].toString(), style: const TextStyle(color: FastTheme.textMuted, fontSize: 11),),
                        ),
                      ),
                    ])
                  : Text('${r['uyum_orani'] ?? ''}', style: GoogleFonts.cormorantGaramond(fontSize: 24, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
            )),
            if (!isPy) SizedBox(width: cardWidth, child: _scoreCard(l10n.scoreVitality, Text('${r['tork'] ?? 0}', style: GoogleFonts.cormorantGaramond(fontSize: 24, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
              sub: _torkSub(r['tork'] ?? 0, l10n))),
            if (!isPy) SizedBox(width: cardWidth, child: _scoreCard(l10n.scoreFlow, Text('${r['fraktal'] ?? 0}', style: GoogleFonts.cormorantGaramond(fontSize: 24, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
              sub: _fraktalSub(r['fraktal'] ?? 0, l10n))),
            if (isPy) ...[
              SizedBox(width: cardWidth, child: _scoreCard(l10n.scorePotentialArea, Text('${r['potansiyel_alan_sayisi'] ?? ''}', style: GoogleFonts.cormorantGaramond(fontSize: 24, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                sub: l10n.scoreDetectedArea)),
              SizedBox(width: cardWidth, child: _scoreCard(l10n.scoreAnalysisType, Text(l10n.scoreBirthChart, style: const TextStyle(color: FastTheme.accentGold, fontSize: 14, fontFamily: 'DM Sans')),
                sub: l10n.scorePotentialTalent)),
            ],
          ],
        );
      },
    );
  }

  String _torkSub(dynamic t, AppLocalizations l10n) {
    final v = (t is num) ? t.toDouble() : 0;
    if (v < 3) return l10n.torkLow;
    if (v < 6) return l10n.torkMid;
    return l10n.torkHigh;
  }

  String _fraktalSub(dynamic f, AppLocalizations l10n) {
    final v = (f is num) ? f.toDouble() : 0;
    if (v < 3) return l10n.fraktalLow;
    if (v < 6) return l10n.fraktalMid;
    return l10n.fraktalHigh;
  }

  Widget _scoreCard(String label, Widget valueWidget, {String? sub}) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [FastTheme.cardBg, FastTheme.bgSecondary]),
        border: Border.all(color: FastTheme.border),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Text(label.toUpperCase(), style: const TextStyle(color: FastTheme.textDim, fontSize: 10, letterSpacing: 1)),
          const SizedBox(height: 4),
          valueWidget,
          if (sub != null) ...[
            const SizedBox(height: 4),
            Text(sub, style: const TextStyle(color: FastTheme.textMuted, fontSize: 11), textAlign: TextAlign.center),
          ],
        ],
      ),
    );
  }

  Widget _buildAllSections(AnalysisProvider provider, Map<String, dynamic> r, String sessionId, Map<String, dynamic>? simData, AppLocalizations l10n) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Potansiyel Alanlar
        if ((_isEb || _isPy) && r['potansiyel_alanlar'] is List && (r['potansiyel_alanlar'] as List).isNotEmpty)
          _sectionCard('✨', l10n.analyzerSectionPotential(_isPy ? ' (${l10n.scoreBirthChart})' : ''), defaultOpen: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_isEb ? l10n.analyzerPotentialChildDesc : l10n.analyzerPotentialSelfDesc,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 4),
                Text(l10n.analyzerPotentialTop5Hint,
                  style: const TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                ...((r['potansiyel_alanlar'] as List).take(5).map((p) => Container(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('✨ ${p['alan'] ?? ''}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: FastTheme.text)),
                      Text(l10n.analyzerAspectOrb(p['aci'] ?? '', p['orb'] ?? '', p['aci_turu'] ?? ''),
                        style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                      if (p['metin'] != null) Text(p['metin'].toString(), style: const TextStyle(color: FastTheme.textMuted, fontSize: 11, height: 1.4)),
                    ],
                  ),
                ))),
                const SizedBox(height: 8),
                Text(l10n.analyzerPotentialAllPdf,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
              ],
            )),

        // Meslek Önerileri
        if ((_isEb || _isPy) && r['meslek_onerileri'] is List && (r['meslek_onerileri'] as List).isNotEmpty)
          _sectionCard('🎯', l10n.analyzerSectionProfession, defaultOpen: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_isEb ? l10n.analyzerProfessionChildDesc : l10n.analyzerProfessionSelfDesc,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 4),
                Text(l10n.analyzerProfessionFullRanking, style: const TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                ...((r['meslek_onerileri'] as List).map((m) => Container(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${(r['meslek_onerileri'] as List).indexOf(m) + 1}. ${m['alan'] ?? ''}',
                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: FastTheme.text)),
                      Text(l10n.analyzerScorePoints(m['yuzde'] ?? '', m['puan']?.toStringAsFixed(1) ?? ''),
                        style: const TextStyle(color: FastTheme.accentGold, fontSize: 11)),
                      if (m['meslekler'] is List) ...((m['meslekler'] as List).map((j) => Padding(
                        padding: const EdgeInsets.only(left: 12, top: 2),
                        child: Text('🧑‍💼 ${j['meslek'] ?? ''} — ${j['aciklama'] ?? ''}',
                          style: const TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                      ))),
                    ],
                  ),
                ))),
                Text(l10n.analyzerProfessionScoringNote,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
                Text(l10n.analyzerProfessionPdfHint, style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
              ],
            )),

        // Karmik Ev
        if (r['karmik_ev'] is Map && ((r['karmik_ev']['rapor_a'] as List?)?.isNotEmpty == true))
          _sectionCard('🏛️', l10n.analyzerSectionKarmikHouse,
            child: Column(children: [
              ...((r['karmik_ev']['rapor_a'] as List).map((h) => w.HtmlRender(h.toString()))),
              if (!_isNatal && r['karmik_ev']['rapor_b'] is List)
                ...((r['karmik_ev']['rapor_b'] as List).map((h) => w.HtmlRender(h.toString()))),
            ])),

        // Bagil Iklim
        if (r['bagil_iklim'] != null && r['bagil_iklim'].toString().isNotEmpty)
          _sectionCard('⏳', l10n.analyzerSectionRelativeClimate,
            child: w.HtmlRender(r['bagil_iklim'].toString())),

        // Progression
        if (r['progression'] is List && (r['progression'] as List).isNotEmpty)
          _sectionCard('🔮', _isNatal ? l10n.analyzerSectionProgressionNatal : l10n.analyzerSectionProgressionRelation,
            child: Column(
              children: (r['progression'] as List).map((p) => Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (p['kisi'] != null || p['baslik'] != null)
                      Text('${p['kisi'] ?? p['baslik'] ?? ''}', style: const TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w600)),
                    if ((p['ilerleme_yili'] ?? 0) > 0)
                      Text(l10n.analyzerProgressionYear((p['ilerleme_yili'] as num).toStringAsFixed(1)), style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                    if (p['ay_burcu'] != null)
                      Text('${l10n.analyzerMoon}: ${p['ay_burcu']} | ${l10n.analyzerSun}: ${p['gunes_burcu'] ?? ''}', style: const TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                    if (p['genel_yorum'] != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: w.HtmlRender(p['genel_yorum'].toString()),
                      ),
                    if (p['ay_aci_yorumlari'] is List)
                      ...((p['ay_aci_yorumlari'] as List).map((aci) => Container(
                        margin: const EdgeInsets.only(top: 6),
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: FastTheme.bg,
                          borderRadius: BorderRadius.circular(6),
                          border: const Border(left: BorderSide(color: FastTheme.accentGold, width: 3)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(aci['baslik'] ?? '', style: const TextStyle(color: FastTheme.accentGold, fontSize: 11, fontWeight: FontWeight.w600)),
                            Text(aci['yorum'] ?? '', style: const TextStyle(color: FastTheme.textMuted, fontSize: 11, height: 1.5)),
                            Text('${aci['aci_turu'] ?? ''} · ${aci['etki'] ?? ''} · ${aci['donem'] ?? ''}',
                              style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
                          ],
                        ),
                      ))),
                    if ((p['toplam_aci'] ?? 0) > 0)
                      Text(l10n.analyzerTotalAspects(p['toplam_aci']),
                        style: const TextStyle(color: FastTheme.textDim, fontSize: 10, fontStyle: FontStyle.italic)),
                  ],
                ),
              )).toList(),
            )),

        // Hava Durumu
        if (r['hava_durumu'] is List && (r['hava_durumu'] as List).isNotEmpty)
          _sectionCard('📅', _isNatal ? l10n.analyzerSectionWeatherNatal : l10n.analyzerSectionWeather,
            child: Column(
              children: (r['hava_durumu'] as List).map((a) => Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('🗓️ ${a['tarih'] ?? ''} (${a['gun_ad'] ?? ''})', style: const TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w600)),
                    if (_isNatal && a['ortam'] != null) ...[
                      Text('🌙 Ay ${a['ay_burc'] ?? ''} — ${a['ay_ev'] ?? ''}. Ev (${a['ay_derece'] ?? ''}°)',
                        style: const TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                      Text(a['ortam'].toString(), style: const TextStyle(color: FastTheme.textDim, fontSize: 11, fontStyle: FontStyle.italic)),
                      Padding(padding: const EdgeInsets.only(top: 4), child: w.HtmlRender(a['yorum'].toString())),
                    ] else if (a['mesajlar'] is List)
                      ...((a['mesajlar'] as List).map((m) => w.HtmlRender(m.toString()))),
                  ],
                ),
              )).toList(),
            )),

        // Zaman Makinesi
        if (r['zaman_makinesi'] is List && (r['zaman_makinesi'] as List).isNotEmpty)
          _sectionCard('🔮', l10n.analyzerSectionTimeMachine,
            child: Column(
              children: (r['zaman_makinesi'] as List).map((k) => Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
                child: w.HtmlRender(k.toString()),
              )).toList(),
            )),

        // Yildiz Muhurleri
        if (r['yildiz_muhurleri'] is List && (r['yildiz_muhurleri'] as List).isNotEmpty)
          _sectionCard('🌟', l10n.analyzerSectionSeals,
            child: Column(
              children: (r['yildiz_muhurleri'] as List).map((m) => Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.only(bottom: 8),
                decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(m['baslik'] ?? '', style: const TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w600)),
                    Text(m['icerik'] ?? '', style: const TextStyle(color: FastTheme.textMuted, fontSize: 12)),
                  ],
                ),
              )).toList(),
            )),

        // Arap Noktalari
        if (r['arap_noktalari'] is Map && (r['arap_noktalari'] as Map).isNotEmpty)
          _sectionCard('🌙', l10n.analyzerSectionArabic,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerArabicIntro,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 4),
                Text(l10n.analyzerArabicPdfHint, style: const TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                ...((r['arap_noktalari'] as Map).entries.map((e) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('🔮 ${e.key}', style: const TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w600)),
                      Wrap(
                        spacing: 4, runSpacing: 4,
                        children: (e.value as Map).entries.map((n) => Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: FastTheme.cardBg,
                            border: Border.all(color: FastTheme.border),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text('${n.key}: ${(n.value['derece'] ?? 0).toStringAsFixed(1)}° ${n.value['burc'] ?? ''} (${n.value['ev'] ?? ''}. Ev)',
                            style: const TextStyle(fontSize: 10, color: FastTheme.textMuted)),
                        )).toList(),
                      ),
                    ],
                  ),
                ))),
                if (r['arap_sinastri'] is List && (r['arap_sinastri'] as List).isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text('🔗 ${l10n.analyzerSectionArabicBonds}', style: const TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w600)),
                  ...((r['arap_sinastri'] as List).take(6).map((b) => Container(
                    margin: const EdgeInsets.only(bottom: 4),
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(color: FastTheme.cardBg, border: Border.all(color: FastTheme.border), borderRadius: BorderRadius.circular(6)),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          b['tip'] == 'nokta_nokta' ? '🌙 ${b['nokta']}: ${b['fark']}° orb' :
                          b['tip'] == 'capraz_nokta' ? '🔄 ${b['nokta_a']} ↔ ${b['nokta_b']}: ${b['fark']}°' :
                          '⭐ ${b['nokta']} → ${b['gezegen']}: ${b['fark']}° (${b['kaynak']} → ${b['hedef']})',
                          style: const TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                        if (b['yorum'] != null)
                          Text(b['yorum'].toString(), style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
                      ],
                    ),
                  ))),
                ],
              ],
            )),

        // Hayat Alanlari (Natal)
        if (_isNatal && r['hayat_alanlari'] is List && (r['hayat_alanlari'] as List).isNotEmpty)
          _sectionCard('🌐', l10n.analyzerSectionLifeAreas, defaultOpen: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerLifeAreasIntro,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 12)),
                const SizedBox(height: 12),
                ...((r['hayat_alanlari'] as List).asMap().entries.map((entry) {
                  final i = entry.key;
                  final h = entry.value as Map;
                  final skor = (h['skor'] ?? 0).toDouble();
                  final barColor = skor >= 70 ? FastTheme.accentGold : skor >= 40 ? const Color(0xFFf0c040) : const Color(0xFFe0756d);
                  final isOpen = _expandedHayat == i;
                  return GestureDetector(
                    onTap: () => setState(() => _expandedHayat = isOpen ? -1 : i),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      margin: const EdgeInsets.only(bottom: 8),
                      decoration: BoxDecoration(
                        color: FastTheme.cardBg,
                        border: Border.all(color: FastTheme.border),
                        borderRadius: BorderRadius.circular(12),
                        boxShadow: isOpen ? [const BoxShadow(color: Colors.black38, blurRadius: 12)] : null,
                      ),
                      child: Column(
                        children: [
                          ClipRRect(
                            borderRadius: const BorderRadius.vertical(top: Radius.circular(11)),
                            child: Container(
                              height: isOpen ? 120 : 160,
                              decoration: h['image'] != null && h['image'].toString().isNotEmpty
                                ? BoxDecoration(
                                    image: DecorationImage(image: NetworkImage(h['image'].toString()), fit: BoxFit.cover),
                                  )
                                : BoxDecoration(
                                    gradient: LinearGradient(
                                      colors: [FastTheme.primaryLight.withValues(alpha: 0.3), FastTheme.bg],
                                      begin: Alignment.topLeft, end: Alignment.bottomRight,
                                    ),
                                  ),
                              child: Stack(
                                children: [
                                  Positioned(
                                    bottom: 0, left: 0, right: 0,
                                    child: Container(
                                      padding: const EdgeInsets.fromLTRB(10, 20, 10, 10),
                                      decoration: BoxDecoration(
                                        gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter,
                                          colors: [Colors.transparent, Colors.black.withValues(alpha: 0.75)]),
                                      ),
                                      child: Row(
                                        children: [
                                          Text(h['icon'] ?? '', style: const TextStyle(fontSize: 20)),
                                          const SizedBox(width: 6),
                                          Expanded(child: Text(h['etiket'] ?? '',
                                            style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600, shadows: [Shadow(color: Colors.black87, blurRadius: 3)]))),
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                            decoration: BoxDecoration(color: Colors.black38, borderRadius: BorderRadius.circular(8)),
                                            child: Row(
                                              mainAxisSize: MainAxisSize.min,
                                              children: [
                                                SizedBox(
                                                  width: 30, height: 4,
                                                  child: ClipRRect(
                                                    borderRadius: BorderRadius.circular(2),
                                                    child: LinearProgressIndicator(
                                                      value: skor / 100,
                                                      backgroundColor: FastTheme.bg,
                                                      valueColor: AlwaysStoppedAnimation(barColor),
                                                    ),
                                                  ),
                                                ),
                                                const SizedBox(width: 4),
                                                Text('${skor.toInt()}', style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600)),
                                              ],
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                  if (!isOpen)
                                    Positioned(top: 8, right: 8, child: Text(l10n.analyzerClick, style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600))),
                                ],
                              ),
                            ),
                          ),
                          if (isOpen)
                            Container(
                              padding: const EdgeInsets.all(14),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('${h['icon'] ?? ''} ${h['etiket'] ?? ''}',
                                    style: const TextStyle(color: FastTheme.accentGold, fontSize: 14, fontWeight: FontWeight.w500)),
                                  const SizedBox(height: 8),
                                  if (h['yorum'] != null)
                                    Text(h['yorum'].toString(), style: const TextStyle(color: FastTheme.textMuted, fontSize: 12, height: 1.6)),
                                  if (h['oneriler'] is List && (h['oneriler'] as List).isNotEmpty) ...[
                                    const SizedBox(height: 8),
                                    Wrap(
                                      spacing: 6, runSpacing: 6,
                                      children: (h['oneriler'] as List).map((o) {
                                        final tur = o['tur'] ?? '';
                                        final turColor = tur == 'saglik' ? const Color(0x26C83C3C) : tur == 'spor' ? const Color(0x263C96C8) : tur == 'sanat' ? const Color(0x26C864C8) : const Color(0x26C9A96E);
                                        return Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: turColor,
                                            border: Border.all(color: FastTheme.border),
                                            borderRadius: BorderRadius.circular(14),
                                          ),
                                          child: Text('💡 ${o['metin'] ?? ''}', style: const TextStyle(color: FastTheme.textMuted, fontSize: 10)),
                                        );
                                      }).toList(),
                                    ),
                                  ],
                                  const SizedBox(height: 6),
                                  Center(child: Text(l10n.analyzerCloseHint, style: const TextStyle(color: FastTheme.textDim, fontSize: 9))),
                                ],
                              ),
                            ),
                        ],
                      ),
                    ),
                  );
                })),
              ],
            )),

        // Sabianlar
        if (_isNatal && r['sabianlar'] is List && (r['sabianlar'] as List).isNotEmpty)
          _sectionCard('⭐', l10n.analyzerSectionSabian, defaultOpen: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerSabianIntro,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 12)),
                const SizedBox(height: 8),
                ...((r['sabianlar'] as List).map((s) => Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: FastTheme.cardBg,
                    borderRadius: BorderRadius.circular(6),
                    border: const Border(left: BorderSide(color: FastTheme.accentGold, width: 3)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${s['gezegen'] ?? ''} (${s['derece_str'] ?? '${s['derece']}°'})',
                        style: const TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w600)),
                      Text(s['sembol'] ?? '', style: const TextStyle(color: FastTheme.textMuted, fontSize: 11, height: 1.5)),
                    ],
                  ),
                ))),
              ],
            )),

        // Solar Return (Natal)
        if (_isNatal && r['solar_return'] != null)
          _sectionCard('☀️', l10n.analyzerSectionSolarReturn,
            child: w.HtmlRender(r['solar_return'].toString())),

        // Lunar Return (Natal)
        if (_isNatal && r['lunar_return'] != null)
          _sectionCard('🌙', l10n.analyzerSectionLunarReturn,
            child: w.HtmlRender(r['lunar_return'].toString())),

        // Minor Progress (Natal)
        if (_isNatal && r['minor_progress'] is List && (r['minor_progress'] as List).isNotEmpty)
          _sectionCard('📈', l10n.analyzerSectionMinorProgress,
            child: Column(
              children: [
                ...((r['minor_progress'] as List).map((p) => Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: FastTheme.cardBg, border: Border.all(color: FastTheme.border), borderRadius: BorderRadius.circular(8)),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(p['tarih'] != null ? '📅 ${p['tarih']} (${p['gun_ad'] ?? ''})' : '📅 ${l10n.analyzerProgressionYear(p['yil'] ?? '')}',
                        style: const TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w600)),
                      Text(l10n.analyzerMoonSunHouse(p['ay_ev'] ?? '', p['ay_burc'] ?? '', p['gunes_burc'] ?? ''),
                        style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
                      if (p['ortam'] != null)
                        Text(p['ortam'].toString(), style: const TextStyle(color: FastTheme.textDim, fontSize: 10, fontStyle: FontStyle.italic)),
                      if (p['yorumlar'] is List) ...((p['yorumlar'] as List).map((y) => Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text('🔹 $y', style: const TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                      ))),
                    ],
                  ),
                ))),
                if (r['minor_progress_6month'] != null)
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: FastTheme.cardBg,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: FastTheme.accentGold, width: 1, style: BorderStyle.solid),
                    ),
                    child: Text(l10n.analyzerMinorProgress6Month,
                      style: const TextStyle(color: FastTheme.textDim, fontSize: 10, fontStyle: FontStyle.italic)),
                  ),
              ],
            )),

        // Chart Yorumu (Natal)
        if (_isNatal && r['chart_yorumu'] != null)
          _sectionCard('📜', l10n.analyzerSectionChartComment, defaultOpen: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerChartCommentIntro,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 8),
                Text(r['chart_yorumu'].toString(), style: const TextStyle(color: FastTheme.text, fontSize: 12, height: 1.8)),
              ],
            )),

        // Sifa Receteleri (Natal)
        if (_isNatal && r['sifa_receteleri'] != null)
          _sectionCard('💊', l10n.analyzerSectionHealing, defaultOpen: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerHealingIntro,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 8),
                w.HtmlRender(r['sifa_receteleri'].toString()),
              ],
            )),

        // Sifa Receteleri Detay (Natal)
        if (_isNatal && r['sifa_receteleri_detay'] is List && (r['sifa_receteleri_detay'] as List).isNotEmpty)
          _sectionCard('🌿', l10n.analyzerSectionHealingDetail, defaultOpen: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerHealingDetailIntro,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 8),
                ...((r['sifa_receteleri_detay'] as List).map((rct) => Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: FastTheme.cardBg, border: Border.all(color: FastTheme.border), borderRadius: BorderRadius.circular(8)),
                  child: Text(rct.toString(), style: const TextStyle(color: FastTheme.textMuted, fontSize: 12, height: 1.6)),
                ))),
              ],
            )),

        // Asteroitler
        if (r['asteroitler'] is List && (r['asteroitler'] as List).isNotEmpty)
          _sectionCard('👑', l10n.analyzerSectionAsteroids,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerAsteroidsIntro,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 4),
                Text(l10n.analyzerAsteroidsOrbHint, style: const TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                const SizedBox(height: 4),
                ...((r['asteroitler'] as List).take(12).map((a) {
                  final etki = a['etki'] ?? '';
                  final leftColor = etki == 'aşk' ? const Color(0xFFD4878F) : etki == 'tutku' ? const Color(0xFFFF5722) : etki == 'bağlılık' ? const Color(0xFF8FB8CA) : FastTheme.accentGold;
                  return Container(
                    margin: const EdgeInsets.only(bottom: 4),
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: FastTheme.cardBg,
                      border: Border.all(color: FastTheme.border),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          decoration: BoxDecoration(
                            border: Border(left: BorderSide(color: leftColor, width: 4)),
                          ),
                          padding: const EdgeInsets.only(left: 8),
                          child: Text('${a['asteroit'] ?? ''} (${etki}) — ${a['kaynak'] ?? ''} → ${a['hedef'] ?? ''}: ${a['gezegen'] ?? ''} (${a['fark'] ?? ''}°)',
                            style: TextStyle(color: leftColor, fontSize: 11, fontWeight: FontWeight.w600)),
                        ),
                        if (a['yorum'] != null)
                          Text(a['yorum'].toString(), style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
                      ],
                    ),
                  );
                })),
                const SizedBox(height: 4),
                Text(l10n.analyzerAsteroidsAllPdf,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
              ],
            )),

        // Astrokartografi
        if (r['astrokartografi'] != null || sessionId.isNotEmpty)
          _sectionCard('🌍', l10n.analyzerSectionAlternateUniverse,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerAstroHint,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 8),

                // Astro location selector
                Row(
                  children: [
                    Expanded(
                      child: _dropdownField(l10n.analyzerCountry, ((_lokasyonDB?['sehirler'] as Map? ?? {}).keys.toList()..sort()).cast<String>(), _astroUlke, (v) {
                        setState(() { _astroUlke = v ?? ''; _astroSehir = ''; provider.reset(); });
                      }),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _dropdownField(l10n.analyzerCity, _astroSehirler ?? [], _astroSehir, (v) {
                        setState(() => _astroSehir = v ?? '');
                      }),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _astroSehir.isNotEmpty && _astroUlke.isNotEmpty
                        ? () => provider.loadAstroScores(_astroSehir, _astroUlke)
                        : null,
                    icon: const Icon(Icons.public, size: 16),
                    label: Text('🌍 ${l10n.analyzerCalc}'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),

                // Astro scores
                if (provider.astroData != null || r['astrokartografi'] is Map) ...[
                  const SizedBox(height: 12),
                  _astroScores(provider.astroData, r['astrokartografi'] as Map?, l10n),
                ],
              ],
            )),

        // Simulation / ACG Map
        if ((_isEs || _isNatal) && simData != null)
          _sectionCard('🌍', l10n.analyzerSectionAcg,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerAcgGlobalIntro,
                  style: const TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 8),

                // ACG Map
                if (provider.acgMapUrl == null && !provider.simLoading)
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () => provider.loadAcgMap(),
                      icon: const Icon(Icons.map, size: 16),
                      label: Text('🌍 ${l10n.analyzerLoadWorldMap}'),
                      style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 12)),
                    ),
                  ),
                if (provider.simLoading)
                  const Center(child: Padding(
                    padding: EdgeInsets.all(8),
                    child: SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2, color: FastTheme.accentGold)),
                  )),
                if (provider.acgMapUrl != null) ...[
                  const SizedBox(height: 8),
                  GestureDetector(
                    onTap: () => _showFullImage(provider.acgMapUrl!),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.network(provider.acgMapUrl!, fit: BoxFit.contain),
                    ),
                  ),
                ],

                const SizedBox(height: 8),
                Text(l10n.analyzerSimulationScan,
                  style: const TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                const SizedBox(height: 8),

                // Sim cards
                ...List.generate(_simKategoriler(l10n).length, (i) {
                  final kat = _simKategoriler(l10n)[i];
                  final katKey = kat['key'] as String;
                  final katIcon = kat['icon'] as String;
                  final katLabel = kat['label'] as String;
                  final katColor = _simKatColor(katKey);
                  final items = ((simData['top_sehirler']?[katKey] as List?)?.take(5) ?? []).toList();
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(children: [
                          Text(katIcon, style: TextStyle(fontSize: 16, color: katColor, shadows: [Shadow(color: katColor.withValues(alpha: 0.6), blurRadius: 12)])),
                          const SizedBox(width: 6),
                          Text(katLabel, style: GoogleFonts.cormorantGaramond(fontSize: 14, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                        ]),
                        const SizedBox(height: 6),
                        Wrap(
                          spacing: 8, runSpacing: 8,
                          children: items.map((c) {
                            final sehirFull = c['sehir']?.toString() ?? '';
                            final sehirAdi = sehirFull.split(',')[0].trim();
                            final wikiUrl = _wikiPages[sehirAdi];
                            return Container(
                              width: 180,
                              decoration: BoxDecoration(
                                color: FastTheme.cardBg,
                                border: Border.all(color: FastTheme.border),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Column(
                                children: [
                                  // City photo with Wikipedia link
                                  GestureDetector(
                                    onTap: wikiUrl != null ? () => _openUrl(wikiUrl) : null,
                                    child: Container(
                                      height: 90,
                                      decoration: BoxDecoration(
                                        gradient: RadialGradient(
                                          colors: [katColor.withValues(alpha: 0.12), FastTheme.bg],
                                        ),
                                        borderRadius: const BorderRadius.vertical(top: Radius.circular(11)),
                                      ),
                                      child: Stack(
                                        children: [
                                          ClipRRect(
                                            borderRadius: const BorderRadius.vertical(top: Radius.circular(11)),
                                            child: Image.network(
                                              _api.getSehirGorselUrl(sehirAdi),
                                              errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                                              fit: BoxFit.cover,
                                              width: double.infinity,
                                              height: double.infinity,
                                            ),
                                          ),
                                          Positioned.fill(
                                            child: Container(color: Colors.black.withValues(alpha: 0.35)),
                                          ),
                                          Center(
                                            child: Text(katIcon,
                                              style: TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: katColor,
                                                shadows: [Shadow(color: katColor.withValues(alpha: 0.6), blurRadius: 20)])),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                  Padding(
                                    padding: const EdgeInsets.fromLTRB(10, 6, 10, 8),
                                    child: Column(
                                      children: [
                                        Text(sehirAdi.length > 28 ? '${sehirAdi.substring(0, 28)}...' : sehirAdi,
                                          style: const TextStyle(color: FastTheme.accentGold, fontSize: 11, fontWeight: FontWeight.w600)),
                                        const SizedBox(height: 4),
                                        Row(
                                          children: [
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: katColor.withValues(alpha: 0.2),
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text('${c['skor'] ?? ''}',
                                                style: TextStyle(color: katColor, fontSize: 9, fontWeight: FontWeight.w600)),
                                            ),
                                            const Spacer(),
                                            GestureDetector(
                                              onTap: () => _handleSimClick(provider, c),
                                              child: Container(
                                                padding: const EdgeInsets.all(2),
                                                child: const Text('🔄', style: TextStyle(fontSize: 13)),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                  );
                }),
              ],
            )),

        // Sim notification
        if (r['sim_sehir'] != null)
          Container(
            margin: const EdgeInsets.only(bottom: 16),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: FastTheme.accentGold.withValues(alpha: 0.1),
              border: Border.all(color: FastTheme.accentGold),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text('🔄 ${l10n.analyzerSimulationRenewed(r['sim_sehir'])}',
              textAlign: TextAlign.center, style: const TextStyle(color: FastTheme.accentGold, fontSize: 13)),
          ),
      ],
    );
  }

  List<Map<String, String>> _simKategoriler(AppLocalizations l10n) {
    return [
      {'key': 'para', 'icon': '♃', 'label': l10n.simCatWealth},
      {'key': 'huzur', 'icon': '☽', 'label': l10n.simCatPeace},
      {'key': 'tutku', 'icon': '♂', 'label': l10n.simCatPassion},
      {'key': 'kriz', 'icon': '♄', 'label': l10n.simCatCrisis},
    ];
  }

  Color _simKatColor(String? key) {
    switch (key) {
      case 'para': return FastTheme.success;
      case 'huzur': return const Color(0xFF60a5fa);
      case 'tutku': return FastTheme.warning;
      case 'kriz': return FastTheme.danger;
      default: return FastTheme.accentGold;
    }
  }

  void _handleSimClick(AnalysisProvider provider, Map c) {
    final sehir = c['sehir']?.toString() ?? '';
    if (sehir.isEmpty) return;
    final lat = (c['lat'] ?? 0).toDouble();
    final lon = (c['lon'] ?? 0).toDouble();
    if (lat == 0 && lon == 0) {
      _api.geocode(sehir).then((g) {
        provider.loadAlternatif({'session_id': provider.sessionId, 'sehir': sehir, 'enlem': g['lat'], 'boylam': g['lon']});
      }).catchError((_) {});
    } else {
      provider.loadAlternatif({'session_id': provider.sessionId, 'sehir': sehir, 'enlem': lat, 'boylam': lon});
    }
  }

  Widget _astroScores(Map<String, dynamic>? astroData, Map? akData, AppLocalizations l10n) {
    final skor = astroData?['skor'] ?? akData?['skor'];
    if (skor == null) return const SizedBox.shrink();
    final cats = [
      {'k': 'para', 'l': l10n.astroScoreMoney, 'c': const Color(0xFF4caf50)},
      {'k': 'huzur', 'l': l10n.astroScorePeace, 'c': const Color(0xFF2196f3)},
      {'k': 'tutku', 'l': l10n.astroScorePassion, 'c': const Color(0xFFff5722)},
      {'k': 'kriz', 'l': l10n.astroScoreCrisis, 'c': const Color(0xFFe91e63)},
    ];
    return Column(
      children: [
        ...cats.map((c) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(
            children: [
              SizedBox(width: 80, child: Text(c['l'] as String, style: const TextStyle(fontSize: 12, color: FastTheme.textMuted))),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: ((skor[c['k']] ?? 0) as num).toDouble() / 100,
                    backgroundColor: FastTheme.border,
                    valueColor: AlwaysStoppedAnimation(c['c'] as Color),
                    minHeight: 10,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(width: 24, child: Text('${skor[c['k']] ?? 0}', style: const TextStyle(color: FastTheme.text, fontSize: 12, fontWeight: FontWeight.w600))),
            ],
          ),
        )),
        if (skor['etkiler'] is List && (skor['etkiler'] as List).isNotEmpty)
          ...((skor['etkiler'] as List).map((e) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 1),
            child: Text('• $e', style: const TextStyle(color: FastTheme.textDim, fontSize: 10)),
          ))),
      ],
    );
  }

  // ========== CHARTS SECTION ==========
  Widget _chartsSection(Map<String, dynamic> r, String sessionId, AppLocalizations l10n) {
    if (sessionId.isEmpty) return const SizedBox.shrink();
    final chartTabs = r['chartlar'] as List? ??
        (_mode != 'potansiyel_yetenek' && !_isNatal ? ['situa_a', 'situa_b'] : ['situa_a']);

    return Column(
      children: [
        Text('🧭 ${l10n.analyzerChartsTitle}', style: GoogleFonts.cormorantGaramond(fontSize: 18, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
        const SizedBox(height: 12),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: chartTabs.map((t) {
              final active = _chartTab == t;
              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: GestureDetector(
                  onTap: () => setState(() => _chartTab = t),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                    decoration: BoxDecoration(
                      gradient: active ? const LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]) : null,
                      color: active ? null : FastTheme.cardBg,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: active ? FastTheme.accentGold : FastTheme.border),
                    ),
                    child: Text(t, style: TextStyle(
                      fontSize: 11, fontWeight: FontWeight.w600,
                      color: active ? FastTheme.bg : FastTheme.textMuted,
                    )),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 12),
        GestureDetector(
          onTap: () => _showFullImage(_api.getGorselUrl(sessionId, _chartTab)),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.network(
              _api.getGorselUrl(sessionId, _chartTab),
              fit: BoxFit.contain,
              loadingBuilder: (_, child, progress) {
                if (progress == null) return child;
                return const SizedBox(height: 300, child: Center(child: CircularProgressIndicator(color: FastTheme.accentGold)));
              },
              errorBuilder: (_, __, ___) => Container(
                height: 100,
                decoration: BoxDecoration(color: FastTheme.cardBg, borderRadius: BorderRadius.circular(12)),
                child: Center(child: Text(l10n.analyzerChartNotReady, style: const TextStyle(color: FastTheme.textDim, fontSize: 13))),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ========== PDF SECTION ==========
  Widget _pdfSection(AnalysisProvider provider, Map<String, dynamic> r, String sessionId, AppLocalizations l10n) {
    if (sessionId.isEmpty) return const SizedBox.shrink();
    return Column(
      children: [
        const SizedBox(height: 24),
        Text('📄 ${l10n.analyzerReportTitle}', style: GoogleFonts.cormorantGaramond(fontSize: 18, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          children: _pdfLinks(sessionId, l10n).map((link) => ElevatedButton.icon(
            onPressed: () => _downloadPdf(sessionId, link['tip'], l10n),
            icon: const Icon(Icons.download, size: 16),
            label: Text('📥 ${link['label']}'),
            style: ElevatedButton.styleFrom(
              backgroundColor: FastTheme.accentGold,
              foregroundColor: FastTheme.bg,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          )).toList(),
        ),
      ],
    );
  }

  List<Map<String, String>> _pdfLinks(String sessionId, AppLocalizations l10n) {
    switch (_mode) {
      case 'es_sevgili': return [{'tip': 'rapor', 'label': l10n.analyzerPdfReport}];
      case 'potansiyel_yetenek': return [{'tip': 'potansiyel', 'label': l10n.analyzerPdfPotential}];
      case 'ebeveyn_cocuk': return [{'tip': 'rapor', 'label': l10n.analyzerPdfReport}];
      case 'bireysel_natal': return [{'tip': 'natal', 'label': l10n.analyzerPdfNatal}];
      default: return [];
    }
  }

  Future<void> _downloadPdf(String sessionId, String? tip, AppLocalizations l10n) async {
    final url = _api.getPdfUrl(sessionId, tip ?? 'rapor');
    try {
      final resp = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 90));
      if (resp.statusCode != 200) {
        throw Exception(l10n.analyzerPdfNotFound('${resp.statusCode}'));
      }
      final dir = await getApplicationDocumentsDirectory();
      final dosya = File('${dir.path}/${sessionId}_${tip ?? 'rapor'}.pdf');
      await dosya.writeAsBytes(resp.bodyBytes, flush: true);
      final sonuc = await OpenFile.open(dosya.path);
      if (!mounted) return;
      if (sonuc.type == ResultType.done) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.analyzerPdfDownloaded(dosya.path))));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.analyzerPdfDownloaded(dosya.path))));
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.analyzerPdfError('$e'))));
    }
  }

  // ========== HELPERS ==========
  Widget _sectionCard(String icon, String title, {required Widget child, bool defaultOpen = false}) {
    return w.SectionCard(icon: Icons.star, title: '$icon $title', child: child);
  }

  void _showFullImage(String url) {
    showDialog(
      context: context,
      builder: (ctx) => GestureDetector(
        onTap: () => Navigator.pop(ctx),
        child: Scaffold(
          backgroundColor: Colors.black.withValues(alpha: 0.92),
          body: Center(
            child: GestureDetector(
              onTap: () {}, // prevent close on image tap
              child: InteractiveViewer(
                child: Image.network(url, fit: BoxFit.contain,
                  errorBuilder: (_, __, ___) => Text(AppLocalizations.of(context).imageLoadError, style: const TextStyle(color: Colors.white)),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
