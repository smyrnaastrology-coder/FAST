import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:open_file/open_file.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config/theme.dart';
import '../config/country_labels.dart';
import '../l10n/app_localizations.dart';
import '../models/analysis_request.dart';
import '../providers/analysis_provider.dart';
import '../providers/auth_provider.dart';
import '../providers/locale_provider.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../services/play_integrity_service.dart';
import '../services/revenuecat_service.dart';
import '../widgets/language_switcher.dart';
import '../widgets/section_card.dart' as w;
import 'auth_screen.dart';

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
  // Saat bilerek BOŞ başlar: kullanıcı doğum saatini girmeyebilir. Boş
  // bırakıldığında sunucu öğleyi (12:00) varsayıp sonucu "yaklaşık" işaretler.
  final _p1SaatCtrl = TextEditingController();
  final _p2IsimCtrl = TextEditingController();
  final _p2TarihCtrl = TextEditingController();
  final _p2SaatCtrl = TextEditingController();
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

  // İlişki Skorları (Ashtakoot): Ay'ın konumu doğum ANINA bağlıdır, doğum
  // yerinin koordinatına değil. Buna karşılık UTC ofseti yer + TARİHE bağlıdır
  // (Türkiye'de 2016 öncesi kışın +2, yazın +3). Bu yüzden kullanıcıdan UTC
  // ofseti değil, doğum ŞEHRİ sorulur; ofseti sunucu tarihsel DST ile hesaplar.
  // _p1OfsetCtrl/_p2OfsetCtrl yalnızca şehir çözülemezse elle geçersiz kılma
  // amaçlıdır ve varsayılan olarak boştur.
  final _p1OfsetCtrl = TextEditingController();
  final _p2OfsetCtrl = TextEditingController();
  bool _ashShowManualOffset = false;

  // Koota kartlarında teknik ayrıntı (koota adı, ipucu, nakşatra) varsayılan
  // gizlidir; kullanıcı doğal dil açıklamayı okuduktan sonra isterse açar.
  final Set<String> _ashDetayAcik = <String>{};

  void _ashDetayDegistir(String koota) {
    setState(() {
      if (!_ashDetayAcik.remove(koota)) _ashDetayAcik.add(koota);
    });
  }

  // Ashtakoot doğum YERİ: diğer modlarla aynı ülke + şehir seçimi. Serbest
  // metin yerine liste kullanılır; böylece aynı adlı şehirlerde (Berlin gibi)
  // saat/ülke belirsizliği oluşmaz.
  String _ash1Ulke = 'Türkiye';
  String _ash1Sehir = 'İstanbul';
  String _ash2Ulke = 'Türkiye';
  String _ash2Sehir = 'İstanbul';

  // Astrocartography selector
  String _astroUlke = '';
  String _astroSehir = '';

  // Wikipedia
  Map<String, String> _wikiPages = {};

  // UI state
  int _expandedHayat = -1;
  bool _menuOpen = false;
  String _chartTab = 'situa_a';
  bool _pdfLoading = false;
  Map<String, dynamic>? _prevSimData;

  // Kayıtlı kişiler (Madde 5)
  List<SavedPerson> _savedPeople = [];
  bool _peopleLoading = false;

  String get _modKey {
    if (_mode == 'es_sevgili') return 'es_sevgili';
    if (_mode == 'ebeveyn_cocuk') return 'ebeveyn_cocuk';
    if (_mode == 'potansiyel_yetenek') return 'potansiyel_yetenek';
    if (_mode == 'ashtakoot') return 'ashtakoot';
    return 'bireysel_natal';
  }

  bool get _ikinciKisiGerekli =>
      _modKey == 'es_sevgili' || _modKey == 'ebeveyn_cocuk' || _modKey == 'ashtakoot';
  bool get _eventGerekli => _modKey == 'es_sevgili';
  bool get _ebeveynMod => _modKey == 'ebeveyn_cocuk';
  bool get _natalMod => _modKey == 'bireysel_natal';
  bool get _potansiyelMod => _modKey == 'potansiyel_yetenek';
  bool get _tekKisiMod => _natalMod || _potansiyelMod;
  bool get _isAsh => _mode == 'ashtakoot';
  bool get _isNatal => _mode == 'bireysel_natal';
  bool get _isEs => _mode == 'es_sevgili';
  bool get _isEb => _mode == 'ebeveyn_cocuk';
  bool get _isPy => _mode == 'potansiyel_yetenek';

  @override
  void initState() {
    super.initState();
    _mode = widget.initialMode;
    _loadDB();
    _loadPeople();
  }

  Future<void> _loadPeople() async {
    if (_peopleLoading || !AuthService.isLoggedIn) return;
    setState(() => _peopleLoading = true);
    final r = await AuthService.listPeople();
    if (!mounted) return;
    setState(() {
      _savedPeople = r;
      _peopleLoading = false;
    });
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
    // Ashtakoot ülke/şehir seçimi de aynı listeden beslenir; DB'de yoksa
    // ilk geçerli değere düşürülür ki dropdown boş kalmasın.
    final ashUlkeler = _ashUlkeler;
    if (ashUlkeler.isNotEmpty) {
      if (!ashUlkeler.contains(_ash1Ulke)) _ash1Ulke = ashUlkeler.first;
      if (!ashUlkeler.contains(_ash2Ulke)) _ash2Ulke = ashUlkeler.first;
    }
    for (var slot = 1; slot <= 2; slot++) {
      final liste = _ashSehirler(slot == 1 ? _ash1Ulke : _ash2Ulke);
      if (liste.isEmpty) continue;
      final mevcut = slot == 1 ? _ash1Sehir : _ash2Sehir;
      if (!liste.contains(mevcut)) {
        if (slot == 1) {
          _ash1Sehir = liste.first;
        } else {
          _ash2Sehir = liste.first;
        }
      }
    }
    _dbLoading = false;
    if (mounted) setState(() {});
  }

  List<String>? get _ulkeler => (_lokasyonDB?['ulkeler'] as List?)?.cast<String>();
  List<String>? get _sehirler => (_lokasyonDB?['sehirler']?[_seciliUlke] as List?)?.cast<String>();
  List<String>? get _astroSehirler => _astroUlke.isNotEmpty ? (_lokasyonDB?['sehirler']?[_astroUlke] as List?)?.cast<String>() : null;

  /// Ashtakoot ülke listesi (diğer modlarla aynı kaynak, alfabetik).
  List<String> get _ashUlkeler {
    final map = _lokasyonDB?['sehirler'] as Map?;
    if (map == null) return const <String>[];
    final liste = map.keys.map((e) => e.toString()).toList()..sort();
    return liste;
  }

  /// Verilen ülkenin şehir listesi.
  List<String> _ashSehirler(String ulke) =>
      ((_lokasyonDB?['sehirler']?[ulke] as List?)?.cast<String>()
          ?? const <String>[]);

  String _formatDate(DateTime d) {
    return '${d.day.toString().padLeft(2, '0')}.${d.month.toString().padLeft(2, '0')}.${d.year}';
  }

  DateTime? _parseDate(String text) {
    try {
      final parts = text.trim().split(' ');
      if (parts.length == 3) {
        final gun = int.tryParse(parts[0]);
        const aylarTr = ['ocak', 'şubat', 'mart', 'nisan', 'mayıs', 'haziran', 'temmuz', 'ağustos', 'eylül', 'ekim', 'kasım', 'aralık'];
        const aylarEn = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'];
        const aylarEs = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
        final ayAdi = parts[1].toLowerCase();
        var ay = aylarTr.indexOf(ayAdi);
        if (ay < 0) ay = aylarEn.indexOf(ayAdi);
        if (ay < 0) ay = aylarEs.indexOf(ayAdi);
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

    // İlişki Skorları: UTC ofseti kullanıcıdan değil şehirden hesaplanır.
    // Şehir zorunludur; elle ofset girilmişse o slot şehirden bağımsızdır.
    if (_isAsh) {
      final ofset1 = double.tryParse(_p1OfsetCtrl.text.trim());
      final ofset2 = double.tryParse(_p2OfsetCtrl.text.trim());
      if (_ash1Sehir.trim().isEmpty && ofset1 == null) { _snack(l10n.ashCityRequired1); return; }
      if (_ikinciKisiGerekli && _ash2Sehir.trim().isEmpty && ofset2 == null) { _snack(l10n.ashCityRequired2); return; }
      if (ofset1 != null && (ofset1 < -12 || ofset1 > 14)) { _snack(l10n.ashOffsetRange); return; }
      if (ofset2 != null && (ofset2 < -12 || ofset2 > 14)) { _snack(l10n.ashOffsetRange); return; }
    }

    final lp = context.read<LocaleProvider>();
    final req = AnalysisRequest(
      p1Isim: _p1IsimCtrl.text,
      p1Tarih: _normalizeDate(_p1TarihCtrl.text),
      p1Saat: _p1SaatCtrl.text.trim(),
      p2Isim: _p2IsimCtrl.text,
      p2Tarih: _ikinciKisiGerekli ? _normalizeDate(_p2TarihCtrl.text) : _normalizeDate(_p1TarihCtrl.text),
      p2Saat: _p2SaatCtrl.text.trim(),
      eventTarih: _eventGerekli ? _normalizeDate(_eventTarihCtrl.text) : '',
      eventSaat: _eventSaatCtrl.text,
      ebeveynRolu: _ebeveynRolu,
      city: _seciliSehir,
      country: _seciliUlke,
      lat: double.tryParse(_latCtrl.text) ?? 41.0082,
      lon: double.tryParse(_lonCtrl.text) ?? 28.9784,
      p1Sehir: _isAsh ? _ash1Sehir.trim() : '',
      p2Sehir: _isAsh ? _ash2Sehir.trim() : '',
      p1UtcOffset: double.tryParse(_p1OfsetCtrl.text.trim()),
      p2UtcOffset: double.tryParse(_p2OfsetCtrl.text.trim()),
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
            title: Text('${l10n.appTitle} — ${_modeLabel(l10n)}'),
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
      case 'ashtakoot': return l10n.modeAshTitle;
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
         VerticalDivider(width: 1, color: FastTheme.border),
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
              child: Text(provider.error!, style:  TextStyle(color: FastTheme.danger, fontSize: 13)),
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
            Container(width: 32, height: 32, decoration:  BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold, boxShadow: [BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 16)]),
              child:  Center(child: Text('F', style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold, fontSize: 16)))),
            const SizedBox(width: 8),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(l10n.appTitle, style: GoogleFonts.cormorantGaramond(fontSize: 16, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
              Text(l10n.analyzerSimulationSelect, style:  TextStyle(color: FastTheme.textDim, fontSize: 9)),
            ]),
          ]),
          const SizedBox(height: 8),
          ..._modeCards(l10n),
          const SizedBox(height: 4),
          if (_isEs) _esForm(l10n),
          if (_isEb) _ebForm(l10n),
          if (_isPy) _pyForm(l10n),
          if (_isNatal) _natalForm(l10n),
          if (_isAsh) _ashForm(l10n),
          const SizedBox(height: 4),
          // Ashtakoot'ta doğum YERİ önemsizdir (Ay konumu doğum anına bağlı),
          // bu yüzden şehir formu gizlenir; yerine UTC ofseti seçilir.
          if (!_isAsh) _locationForm(l10n),
          const SizedBox(height: 8),
          _peopleSection(l10n),
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
              Container(width: 72, height: 72, decoration:  BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold, boxShadow: [BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 24)]),
                child:  Center(child: Text('F', style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold, fontSize: 32)))),
              const SizedBox(height: 8),
              Text(l10n.homeTitle, textAlign: TextAlign.center,
                style: GoogleFonts.cormorantGaramond(fontSize: 18, fontWeight: FontWeight.w700, color: FastTheme.accentGold, height: 1.3)),
              Text(l10n.analyzerSidebarTagline, style:  TextStyle(color: FastTheme.textMuted, fontSize: 10, letterSpacing: 2)),
              Text(l10n.analyzerSidebarVersion, style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
            ],
          ),
        ),
        const SizedBox(height: 16),
         Divider(color: FastTheme.border),
        const SizedBox(height: 8),

        // Mode cards
        ..._modeCards(l10n),

        const SizedBox(height: 8),

        // Forms based on mode
        if (_isEs) _esForm(l10n),
        if (_isEb) _ebForm(l10n),
        if (_isPy) _pyForm(l10n),
        if (_isNatal) _natalForm(l10n),
        if (_isAsh) _ashForm(l10n),

        const SizedBox(height: 8),

        // Location — Ashtakoot'ta doğum yeri önemsiz (Ay konumu doğum anına bağlı).
        if (!_isAsh) _locationForm(l10n),

        // Kayıtlı kişiler (Madde 5)
        _peopleSection(l10n),

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
      {'key': 'ashtakoot', 'title': l10n.modeAshTitle, 'desc': l10n.analyzerModeAshDesc, 'img': 'assets/askahoot.png'},
    ];
    return modes.map((m) {
      final key = m['key'] as String;
      final active = _mode == key;
      return GestureDetector(
        onTap: () => setState(() {
          _mode = key; _menuOpen = false;
          context.read<AnalysisProvider>().reset();
          _p1IsimCtrl.clear(); _p1TarihCtrl.clear(); _p1SaatCtrl.clear();
          _p2IsimCtrl.clear(); _p2TarihCtrl.clear(); _p2SaatCtrl.clear();
          _eventTarihCtrl.clear(); _eventSaatCtrl.text = '12:00';
          // Şehir alanları modlar arası korunur; kullanıcı her seferinde
          // aynı şehri yeniden yazmak zorunda kalmamalı.
        }),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          margin: const EdgeInsets.only(bottom: 6),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: active ? FastTheme.cardBgHover : FastTheme.cardBg,
            border: Border.all(color: active ? FastTheme.accentGold : FastTheme.border),
            borderRadius: BorderRadius.circular(12),
            boxShadow: active ? [ BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 12)] : null,
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
                child: m['img'] == null
                    ? Icon(Icons.auto_awesome,
                        size: 20, color: active ? FastTheme.accentGold : FastTheme.textDim)
                    : Image.asset(m['img'] as String, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const SizedBox.shrink()),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(m['title'] as String, style: GoogleFonts.cormorantGaramond(fontSize: 13, fontWeight: FontWeight.w700, color: active ? FastTheme.accentGold : FastTheme.textMuted)),
                    Text(m['desc'] as String, style:  TextStyle(fontSize: 10, color: FastTheme.textDim)),
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

  Widget _formField(String label, TextEditingController ctrl, {IconData? icon, TextInputType? keyboardType, String? hint}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TextField(
        controller: ctrl,
        keyboardType: keyboardType,
        style:  TextStyle(color: FastTheme.text, fontSize: 13),
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          hintStyle: TextStyle(color: FastTheme.textDim, fontSize: 12),
          labelStyle:  TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1),
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
        style:  TextStyle(color: FastTheme.text, fontSize: 13),
        decoration: InputDecoration(
          labelText: zorunlu ? label : '$label (${l10n.analyzerOptional})',
          hintText: l10n.analyzerBirthDateHint,
          hintStyle:  TextStyle(color: FastTheme.textDim, fontSize: 11),
          labelStyle:  TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1),
          prefixIcon:  Icon(Icons.calendar_today, size: 18, color: FastTheme.accentGold),
          suffixIcon: IconButton(icon:  Icon(Icons.date_range, size: 18, color: FastTheme.accentGold), onPressed: () => _pickDate(ctrl)),
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
        style:  TextStyle(color: FastTheme.text, fontSize: 13),
        decoration: InputDecoration(
          labelText: label,
          labelStyle:  TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1),
          prefixIcon:  Icon(Icons.access_time, size: 18, color: FastTheme.accentGold),
          suffixIcon: IconButton(icon:  Icon(Icons.schedule, size: 18, color: FastTheme.accentGold), onPressed: () => _pickTime(ctrl)),
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
          labelStyle:  TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1),
        ),
        dropdownColor: FastTheme.cardBg,
        style:  TextStyle(color: FastTheme.text, fontSize: 13),
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

  /// İlişki Skorları — iki kişinin Ay nakṣatra uyumu.
  ///
  /// Doğum YERİNİN koordinatı hesaba girmez (Ay'ın görünen konumu yalnızca
  /// doğum anına bağlıdır); ancak UTC ofseti yer + tarihe bağlı olduğu için
  /// doğum şehri sorulur ve ofset sunucuda tarihsel DST ile hesaplanır. Kullanıcı
  /// saat dilimini bilmek zorunda değildir. Saat de isteğe bağlıdır: bilinmiyorsa
  /// boş bırakılır, sunucu öğleyi varsayıp yaklaşık işaretler.
  Widget _ashForm(AppLocalizations l10n) {
    Widget saatNotu() => Padding(
          padding: const EdgeInsets.only(bottom: 6, left: 2),
          child: Text(l10n.ashTimeOptional,
              style: TextStyle(fontSize: 11, color: FastTheme.accentGold, height: 1.3)),
        );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(l10n.ashExplainer, style: TextStyle(fontSize: 11, color: FastTheme.textDim)),
        const SizedBox(height: 10),
        _sectionTitle(l10n.analyzerPerson1),
        _formField(l10n.analyzerName, _p1IsimCtrl, icon: Icons.person),
        _dateField(l10n.analyzerBirthDate, _p1TarihCtrl, l10n),
        _timeField(l10n.analyzerBirthTime, _p1SaatCtrl),
        saatNotu(),
        _ashCityField(l10n, 1),
        const SizedBox(height: 14),
        _sectionTitle(l10n.analyzerPerson2),
        _formField(l10n.analyzerName, _p2IsimCtrl, icon: Icons.person_outline),
        _dateField(l10n.analyzerBirthDate, _p2TarihCtrl, l10n),
        _timeField(l10n.analyzerBirthTime, _p2SaatCtrl),
        saatNotu(),
        _ashCityField(l10n, 2),
        const SizedBox(height: 4),
        _ashManualOffsetSection(l10n),
      ],
    );
  }

  /// Kişi başına doğum YERİ (slot 1 veya 2): ülke + şehir seçimi.
  ///
  /// Diğer modlarla aynı veri kaynağını ve aynı düzeni kullanır; serbest
  /// metin yoktur. Böylece "Berlin" gibi birden çok ülkede bulunan adlar
  /// belirsiz kalmaz ve kullanıcının yazım hatası ihtimali ortadan kalkar.
  Widget _ashCityField(AppLocalizations l10n, int slot) {
    final ulke = slot == 1 ? _ash1Ulke : _ash2Ulke;
    final sehir = slot == 1 ? _ash1Sehir : _ash2Sehir;
    final ulkeler = _ashUlkeler;
    final sehirler = _ashSehirler(ulke);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(slot == 1 ? l10n.ashBirthCity1 : l10n.ashBirthCity2,
            style: TextStyle(
                fontSize: 11, fontWeight: FontWeight.w700,
                color: FastTheme.accentGold, letterSpacing: 1)),
        const SizedBox(height: 6),
        _dropdownField(l10n.analyzerCountry, ulkeler, ulke, (v) {
          if (v == null) return;
          setState(() {
            if (slot == 1) {
              _ash1Ulke = v;
              // Ülke değişince şehir geçersiz kalır; ilk şehre düşürülür.
              _ash1Sehir = _ashSehirler(v).isEmpty ? '' : _ashSehirler(v).first;
            } else {
              _ash2Ulke = v;
              _ash2Sehir = _ashSehirler(v).isEmpty ? '' : _ashSehirler(v).first;
            }
          });
        }),
        _dropdownField(l10n.analyzerCity, sehirler, sehir, (v) {
          if (v == null) return;
          setState(() {
            if (slot == 1) {
              _ash1Sehir = v;
            } else {
              _ash2Sehir = v;
            }
          });
        }),
        if (sehirler.isEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Text(l10n.ashCityNotInList,
                style: TextStyle(fontSize: 10.5, color: FastTheme.textDim)),
          ),
      ],
    );
  }

  /// Şehir çözülemezse kullanılacak elle UTC ofseti. Varsayılan kapalıdır ki
  /// normal kullanıcıyı korkutmasın; çözüm şehirden otomatik yapılır.
  Widget _ashManualOffsetSection(AppLocalizations l10n) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () => setState(() => _ashShowManualOffset = !_ashShowManualOffset),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Row(
              children: [
                Icon(_ashShowManualOffset ? Icons.expand_less : Icons.expand_more,
                    size: 16, color: FastTheme.textDim),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(l10n.ashManualOffset,
                      style: TextStyle(fontSize: 11, color: FastTheme.textDim)),
                ),
              ],
            ),
          ),
        ),
        if (_ashShowManualOffset) ...[
          Padding(
            padding: const EdgeInsets.only(bottom: 6, left: 2),
            child: Text(l10n.ashManualOffsetHint,
                style: TextStyle(fontSize: 10, color: FastTheme.textDim, height: 1.3)),
          ),
          Row(
            children: [
              Expanded(
                child: _formField(l10n.ashManualOffset1, _p1OfsetCtrl, icon: Icons.schedule,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true)),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _formField(l10n.ashManualOffset2, _p2OfsetCtrl, icon: Icons.schedule_outlined,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true)),
              ),
            ],
          ),
        ],
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
          }, labels: countryLabels(Localizations.localeOf(context).languageCode)),
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
        Text(_geoHint ?? l10n.analyzerSearchHint, style:  TextStyle(color: FastTheme.textDim, fontSize: 9)),
        const SizedBox(height: 6),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => _geoCode(_seciliSehir),
            icon: const Icon(Icons.search, size: 16),
            label: Text(l10n.analyzerSearchLocation, style: const TextStyle(fontSize: 12)),
            style: OutlinedButton.styleFrom(
              side:  BorderSide(color: FastTheme.border),
              foregroundColor: FastTheme.accentGold,
              padding: const EdgeInsets.symmetric(vertical: 10),
            ),
          ),
        ),
      ],
    );
  }

  // Kayıtlı kişiler: seçim çipleri + "Kişiyi Kaydet" (Madde 5)
  Widget _peopleSection(AppLocalizations l10n) {
    final ap = context.watch<AuthProvider>();
    if (!ap.enabled) return const SizedBox.shrink();

    Widget child;
    if (!ap.isLoggedIn) {
      child = OutlinedButton.icon(
        onPressed: () async {
          await Navigator.push(context, MaterialPageRoute(builder: (_) => const AuthScreen()));
          _loadPeople();
        },
        icon: const Icon(Icons.person_add, size: 16),
        label: Text(l10n.loginNav, style: const TextStyle(fontSize: 12)),
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: FastTheme.border),
          foregroundColor: FastTheme.accentGold,
          padding: const EdgeInsets.symmetric(vertical: 10),
        ),
      );
    } else {
      final saveCls = OutlinedButton.styleFrom(
        side: BorderSide(color: FastTheme.border),
        foregroundColor: FastTheme.accentGold,
        padding: const EdgeInsets.symmetric(vertical: 10),
      );
      child = Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_savedPeople.isNotEmpty) ...[
            _sectionTitle(l10n.peopleSelect),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _savedPeople.map((p) => _personChip(p, l10n)).toList(),
            ),
            const SizedBox(height: 8),
          ],
          if (_ikinciKisiGerekli)
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _saveCurrentPerson(l10n, slot: 1),
                    icon: const Icon(Icons.bookmark_add, size: 16),
                    label: Text(l10n.peopleSave1, style: const TextStyle(fontSize: 12)),
                    style: saveCls,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _saveCurrentPerson(l10n, slot: 2),
                    icon: const Icon(Icons.bookmark_add, size: 16),
                    label: Text(l10n.peopleSave2, style: const TextStyle(fontSize: 12)),
                    style: saveCls,
                  ),
                ),
              ],
            )
          else
            OutlinedButton.icon(
              onPressed: () => _saveCurrentPerson(l10n, slot: 1),
              icon: const Icon(Icons.bookmark_add, size: 16),
              label: Text(l10n.peopleSave, style: const TextStyle(fontSize: 12)),
              style: saveCls,
            ),
        ],
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_peopleLoading)
          const LinearProgressIndicator()
        else
          child,
      ],
    );
  }

  Widget _personChip(SavedPerson p, AppLocalizations l10n) {
    final active = p.name == _p1IsimCtrl.text || (_ikinciKisiGerekli && p.name == _p2IsimCtrl.text);
    return GestureDetector(
      onTap: () async {
        if (!_ikinciKisiGerekli) {
          _applyPerson(p, 1);
          return;
        }
        // İki kişilik modda kişinin 1. ya da 2. alana uygulanacağını sor.
        final secim = await showDialog<int>(
          context: context,
          builder: (ctx) => SimpleDialog(
            backgroundColor: FastTheme.cardBg,
            title: Text(l10n.peopleApplyTo, style: TextStyle(color: FastTheme.accentGold, fontSize: 16)),
            children: [
              SimpleDialogOption(
                onPressed: () => Navigator.of(ctx).pop(1),
                child: Text(l10n.peopleApplyPerson1, style: TextStyle(color: FastTheme.text)),
              ),
              SimpleDialogOption(
                onPressed: () => Navigator.of(ctx).pop(2),
                child: Text(l10n.peopleApplyPerson2, style: TextStyle(color: FastTheme.text)),
              ),
            ],
          ),
        );
        if (secim == null || !mounted) return;
        _applyPerson(p, secim);
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: active ? FastTheme.accentGold.withValues(alpha: 0.15) : FastTheme.cardBg,
          border: Border.all(color: active ? FastTheme.accentGold : FastTheme.border),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
             Icon(Icons.person, size: 14, color: FastTheme.accentGold),
            const SizedBox(width: 4),
            Text(p.name, style: TextStyle(fontSize: 11, color: active ? FastTheme.accentGold : FastTheme.textMuted)),
          ],
        ),
      ),
    );
  }

  Future<void> _saveCurrentPerson(AppLocalizations l10n, {int slot = 1}) async {
    final ap = context.read<AuthProvider>();
    if (!ap.isLoggedIn) {
      await Navigator.push(context, MaterialPageRoute(builder: (_) => const AuthScreen()));
      _loadPeople();
      return;
    }

    final isimCtrl = TextEditingController(text: slot == 2 ? _p2IsimCtrl.text : _p1IsimCtrl.text);
    final tarihCtrl = TextEditingController(text: slot == 2 ? _p2TarihCtrl.text : _p1TarihCtrl.text);
    final saatCtrl = TextEditingController(
        text: (slot == 2 ? _p2SaatCtrl.text : _p1SaatCtrl.text).isEmpty ? '12:00' : (slot == 2 ? _p2SaatCtrl.text : _p1SaatCtrl.text));
    final latCtrl = TextEditingController(text: _latCtrl.text);
    final lonCtrl = TextEditingController(text: _lonCtrl.text);
    final yeniKlasorCtrl = TextEditingController();
    var ulke = (_ulkeler?.contains(_seciliUlke) ?? false) ? _seciliUlke
        : (_ulkeler?.isNotEmpty == true ? _ulkeler!.first : '');
    var sehir = (_sehirler?.contains(_seciliSehir) ?? false) ? _seciliSehir
        : (_sehirler?.isNotEmpty == true ? _sehirler!.first : '');
    var folderKey = 'ailem';
    var yeniKlasorModu = false;

    void geo(sehirAdi) {
      _api.geocode(sehirAdi).then((g) {
        if (!context.mounted) return;
        setState(() {
          latCtrl.text = g['lat'].toStringAsFixed(4);
          lonCtrl.text = g['lon'].toStringAsFixed(4);
        });
      }).catchError((_) {});
    }

    final saved = await showDialog<SavedPerson>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlg) {
          final sehirListesi = ulke.isNotEmpty
              ? ((_lokasyonDB?['sehirler']?[ulke] as List?)?.cast<String>() ?? <String>[])
              : <String>[];
          final formFieldStyle = TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.w600, letterSpacing: 1);
          return AlertDialog(
            backgroundColor: FastTheme.cardBg,
            title: Text(slot == 2 ? l10n.peopleSave2 : l10n.peopleSave,
                style: TextStyle(color: FastTheme.accentGold, fontSize: 17, fontWeight: FontWeight.w600)),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: isimCtrl,
                    style: TextStyle(color: FastTheme.text, fontSize: 13),
                    decoration: InputDecoration(
                      labelText: l10n.analyzerName,
                      labelStyle: formFieldStyle,
                      prefixIcon: Icon(Icons.person, size: 18, color: FastTheme.accentGold),
                    ),
                  ),
                  const SizedBox(height: 10),
                  _dateField(l10n.analyzerBirthDate, tarihCtrl, l10n),
                  _timeField(l10n.analyzerBirthTime, saatCtrl),
                  _dropdownField(l10n.analyzerCountry, _ulkeler ?? [], ulke, (v) {
                    setDlg(() { ulke = v!; sehir = sehirListesi.isNotEmpty ? sehirListesi.first : ''; });
                  }),
                  _dropdownField(l10n.analyzerCity, sehirListesi, sehir, (v) {
                    setDlg(() { sehir = v!; });
                    geo(v);
                  }),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: latCtrl,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          style: TextStyle(color: FastTheme.text, fontSize: 13),
                          decoration: InputDecoration(
                            labelText: l10n.analyzerLatitude,
                            labelStyle: formFieldStyle,
                            prefixIcon: Icon(Icons.explore, size: 18, color: FastTheme.accentGold),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextField(
                          controller: lonCtrl,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          style: TextStyle(color: FastTheme.text, fontSize: 13),
                          decoration: InputDecoration(
                            labelText: l10n.analyzerLongitude,
                            labelStyle: formFieldStyle,
                            prefixIcon: Icon(Icons.explore, size: 18, color: FastTheme.accentGold),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _dropdownField(
                    l10n.peopleFolderLabel,
                    ['ailem', 'arkadaslarim', '__yeni__'],
                    folderKey,
                    (v) => setDlg(() { folderKey = v!; yeniKlasorModu = v == '__yeni__'; }),
                    labels: {
                      'ailem': l10n.peopleFolderFamily,
                      'arkadaslarim': l10n.peopleFolderFriends,
                      '__yeni__': l10n.peopleNewFolder,
                    },
                  ),
                  if (yeniKlasorModu)
                    TextField(
                      controller: yeniKlasorCtrl,
                      style: TextStyle(color: FastTheme.text, fontSize: 13),
                      decoration: InputDecoration(
                        labelText: l10n.peopleFolderNameHint,
                        labelStyle: formFieldStyle,
                        prefixIcon: Icon(Icons.create_new_folder, size: 18, color: FastTheme.accentGold),
                      ),
                    ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: Text(l10n.peopleCancel, style: TextStyle(color: FastTheme.textMuted)),
              ),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: FastTheme.accentGold, foregroundColor: FastTheme.bg),
                onPressed: () async {
                  final isim = isimCtrl.text.trim();
                  if (isim.isEmpty) { _snack(l10n.peopleNameRequired); return; }
                  if (tarihCtrl.text.trim().isEmpty) { _snack(l10n.peopleBirthDateRequired); return; }
                  if (saatCtrl.text.trim().isEmpty) { _snack(l10n.peopleBirthTimeRequired); return; }
                  String? folder;
                  if (yeniKlasorModu) {
                    folder = yeniKlasorCtrl.text.trim();
                    if (folder.isEmpty) { _snack(l10n.peopleFolderRequired); return; }
                  } else {
                    folder = folderKey;
                  }
                  final p = SavedPerson(
                    id: 0,
                    name: isim,
                    birthDate: tarihCtrl.text.isNotEmpty ? _normalizeDate(tarihCtrl.text) : null,
                    birthTime: saatCtrl.text.trim(),
                    city: sehir.isNotEmpty ? sehir : null,
                    country: ulke.isNotEmpty ? ulke : null,
                    lat: double.tryParse(latCtrl.text),
                    lon: double.tryParse(lonCtrl.text),
                    folder: folder,
                  );
                  final created = await AuthService.createPerson(p);
                  if (!context.mounted) return;
                  if (created != null) {
                    Navigator.of(ctx).pop(created);
                  } else {
                    _snack(l10n.loginErrorGeneric);
                  }
                },
                child: Text(l10n.peopleSave),
              ),
            ],
          );
        },
      ),
    );
    if (saved == null || !mounted) return;
    _snack(l10n.peopleSaved);
    setState(() => _savedPeople = [..._savedPeople, saved]);
    _applyPerson(saved, slot);
  }

  void _applyPerson(SavedPerson p, int slot) {
    setState(() {
      if (slot == 2) {
        _p2IsimCtrl.text = p.name;
        if (p.birthDate != null && p.birthDate!.isNotEmpty) _p2TarihCtrl.text = p.birthDate!;
        if (p.birthTime != null && p.birthTime!.isNotEmpty) _p2SaatCtrl.text = p.birthTime!;
      } else {
        _p1IsimCtrl.text = p.name;
        if (p.birthDate != null && p.birthDate!.isNotEmpty) _p1TarihCtrl.text = p.birthDate!;
        if (p.birthTime != null && p.birthTime!.isNotEmpty) _p1SaatCtrl.text = p.birthTime!;
      }
      if (p.city != null && p.city!.isNotEmpty && _sehirler?.contains(p.city) == true) _seciliSehir = p.city!;
      if (p.country != null && p.country!.isNotEmpty && _ulkeler?.contains(p.country) == true) _seciliUlke = p.country!;
      if (p.lat != null) _latCtrl.text = p.lat!.toStringAsFixed(4);
      if (p.lon != null) _lonCtrl.text = p.lon!.toStringAsFixed(4);
    });
    if (p.city != null && p.city!.isNotEmpty) _geoCode(p.city!);
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
                  child: Text(provider.error!, style:  TextStyle(color: FastTheme.danger, fontSize: 13)),
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
          Container(width: 72, height: 72, decoration:  BoxDecoration(shape: BoxShape.circle, color: FastTheme.accentGold, boxShadow: [BoxShadow(color: FastTheme.accentGoldGlow, blurRadius: 24)]),
            child:  Center(child: Text('F', style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold, fontSize: 32)))),
          const SizedBox(height: 12),
          Text(l10n.homeTitle.replaceAll('\n', ' '), style: GoogleFonts.cormorantGaramond(fontSize: 32, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
          Text('${l10n.appTitle} — ${l10n.appSlogan}', style:  TextStyle(color: FastTheme.textMuted, fontSize: 13, letterSpacing: 2)),
          const SizedBox(height: 8),
          Text(l10n.analyzerHeaderDesc,
            style:  TextStyle(color: FastTheme.textDim, fontSize: 11), textAlign: TextAlign.center),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: FastTheme.cardBg,
              border: Border.all(color: FastTheme.border),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(l10n.heroDisclaimer,
              textAlign: TextAlign.center, style:  TextStyle(color: FastTheme.textMuted, fontSize: 10, height: 1.5)),
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
          ]) : _mode == 'ashtakoot' ? _featureList([
            l10n.analyzerFeaturesAsh1,
            l10n.analyzerFeaturesAsh2,
            l10n.analyzerFeaturesAsh3,
            l10n.analyzerFeaturesAsh4,
            l10n.analyzerFeaturesAsh5,
            l10n.analyzerFeaturesAsh6,
            l10n.analyzerFeaturesAsh7,
            l10n.analyzerFeaturesAsh8,
            l10n.analyzerFeaturesAsh9,
          ]) : _featureList([
            l10n.analyzerFeaturesPy1,
            l10n.analyzerFeaturesPy2,
            l10n.analyzerFeaturesPy3,
            l10n.analyzerFeaturesPy4,
            l10n.analyzerFeaturesPy5,
            l10n.analyzerFeaturesPy6,
            l10n.analyzerFeaturesPy7,
            l10n.analyzerFeaturesPy8,
            l10n.analyzerFeaturesPy9,
            l10n.analyzerFeaturesPy10,
            l10n.analyzerFeaturesPy11,
          ])),
        ],
      ),
    );
  }

  List<Widget> _featureList(List<String> items) {
    return items.map((f) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 6, right: 8),
            child: Container(
              width: 5,
              height: 5,
              decoration:  BoxDecoration(color: FastTheme.accentGold, shape: BoxShape.circle),
            ),
          ),
          Expanded(child: Text(f, style:  TextStyle(color: FastTheme.textMuted, fontSize: 12, height: 1.45))),
        ],
      ),
    )).toList();
  }

  Widget _loadingSection(AppLocalizations l10n) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 60),
      child: Column(
        children: [
           SizedBox(width: 48, height: 48, child: CircularProgressIndicator(color: FastTheme.accentGold)),
          const SizedBox(height: 16),
          Text(l10n.loadingSky, style:  TextStyle(color: FastTheme.textMuted, fontSize: 14)),
        ],
      ),
    );
  }

  // ========== RESULTS SECTION ==========
  Widget _resultsSection(AnalysisProvider provider, AppLocalizations l10n) {
    final r = provider.detayliResult ?? provider.result!;
    // Ashtakoot'un kendi sunucusu, harita/PDF/simülasyon oturumu yok; genel
    // sonuç düzeni ona uymuyor.
    if (_isAsh) return _ashResults(r, l10n);
    final sessionId = provider.sessionId ?? '';
    final simData = provider.simData;
    if (simData != _prevSimData) {
      _prevSimData = simData;
      WidgetsBinding.instance.addPostFrameCallback((_) => _loadWikiPages(simData));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(l10n.analyzerResultsTitle, style:  TextStyle(color: FastTheme.textMuted, fontSize: 14, letterSpacing: 1)),
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

        const SizedBox(height: 8),

        // Exit / actions
        _exitSection(l10n),

        const SizedBox(height: 24),
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
              textAlign: TextAlign.center, style:  TextStyle(color: FastTheme.accentGold, fontSize: 13)),
          ),
      ],
    );
  }

  /// Sunucuda üretilen doğal dil paragrafı.
  Widget _metinKarti(String baslik, String metin, {String? ipucu}) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        border: Border.all(color: FastTheme.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(baslik,
              style: TextStyle(
                  color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          Text(metin,
              style: TextStyle(color: FastTheme.textMuted, fontSize: 13, height: 1.45)),
          if (ipucu != null && ipucu.isNotEmpty) ...[
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.lightbulb_outline, size: 13, color: FastTheme.accentGold),
                const SizedBox(width: 5),
                Expanded(
                  child: Text(ipucu,
                      style: TextStyle(color: FastTheme.textDim, fontSize: 11, height: 1.35)),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  /// Hangi şehir ve UTC ofsetinin kullanıldığını gösteren şeffaflık kutusu.
  /// Backend anahtarları: offset, yontem, sehir, ulke, tz, belirsiz, saat_biliyor.
  Widget _utcKarti(AppLocalizations l10n, Map<String, dynamic> utc, String notu) {
    String _ofsetMetni(dynamic ofset) {
      if (ofset is! num) return '?';
      final d = ofset.toDouble();
      final isaret = d >= 0 ? '+' : '-';
      final mutlak = d.abs();
      final saat = mutlak.floor();
      final dakika = ((mutlak - saat) * 60).round();
      return 'UTC$isaret$saat${dakika == 0 ? '' : ':${dakika.toString().padLeft(2, '0')}'}';
    }

    String _satir(String etiket, Map<String, dynamic>? k) {
      if (k == null) return '';
      final sehir = (k['sehir'] ?? '').toString();
      final ulke = (k['ulke'] ?? '').toString();
      final yer = sehir.isEmpty
          ? ''
          : (ulke.isEmpty || ulke == sehir ? sehir : '$sehir, $ulke');
      final parcalar = <String>[];
      if (yer.isNotEmpty) parcalar.add(yer);
      parcalar.add(_ofsetMetni(k['offset']));
      // Yöntem şeffaflığı: 'timezonefinder' = kesin, 'boylam' = ±30 dk tahmin,
      // 'manuel' = kullanıcı girdi.
      final yontem = (k['yontem'] ?? '').toString();
      if (yontem == 'boylam') parcalar.add('≈ ${l10n.ashOffsetApprox}');
      if (yontem == 'manuel') parcalar.add(l10n.ashOffsetManual);
      if (k['yaklasik_ofset'] == true && yontem != 'boylam') {
        parcalar.add('≈ ${l10n.ashOffsetApprox}');
      }
      if (k['saat_belirsiz'] == true) parcalar.add(l10n.ashTimeAmbiguous);
      if (k['saat_biliyor'] == false) parcalar.add(l10n.ashApproximate);
      return '$etiket: ${parcalar.join('  ·  ')}';
    }

    final satirlar = <String>[
      _satir(l10n.ashPersonAMoon, (utc['p1'] as Map?)?.cast<String, dynamic>()),
      _satir(l10n.ashPersonBMoon, (utc['p2'] as Map?)?.cast<String, dynamic>()),
    ].where((s) => s.isNotEmpty).toList();

    if (satirlar.isEmpty && notu.isEmpty) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        border: Border.all(color: FastTheme.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.public, size: 14, color: FastTheme.textDim),
              const SizedBox(width: 6),
              Text(l10n.ashResolvedUtc,
                  style: TextStyle(
                      color: FastTheme.textDim, fontSize: 11, fontWeight: FontWeight.w700)),
            ],
          ),
          const SizedBox(height: 6),
          ...satirlar.map((s) => Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Text(s,
                    style: TextStyle(color: FastTheme.textDim, fontSize: 11, height: 1.3)),
              )),
          if (notu.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(notu,
                  style: TextStyle(color: FastTheme.textDim, fontSize: 10, height: 1.3)),
            ),
        ],
      ),
    );
  }

  /// Nadi Dosha kartı.
  ///
  /// Ashtakoot'un tek sıfır puanlı kalemi olduğu için ayrı bir kart olarak,
  /// kootalar listesinden hemen önce gösterilir. Metinlerin tamamı
  /// backend'de dile çevrildiği için (TR/EN/ES) burada yalnızca sunum
  /// yapılır; ham koota puanı bu kartta değiştirilmez.
  Widget _nadiDosyaKarti(Map<String, dynamic> n) {
    final ozet = (n['ozet'] as Map?)?.cast<String, dynamic>() ?? const {};
    final kosullar = ((n['kosullar'] as List?) ?? const [])
        .map((e) => (e as Map).cast<String, dynamic>())
        .toList();
    final kapsamDisi = ((n['kapsam_disi'] as List?) ?? const [])
        .map((e) => (e as Map).cast<String, dynamic>())
        .toList();
    final baslik = (n['baslik'] ?? '').toString();
    final baslikSeviye = (n['baslik_seviye'] ?? '').toString();
    final aciklama = (n['aciklama'] ?? '').toString();
    final ipucu = (n['ipucu'] ?? '').toString();
    final puanNotu = (n['puan_notu'] ?? '').toString();
    final kapsamBaslik = (n['kapsam_disi_baslik'] ?? '').toString();
    final kapsamNotu = (n['kapsam_disi_notu'] ?? '').toString();
    // Şiddet koduna göre vurgu rengi; "yok" hiçbir zaman gönderilmez çünkü
    // backend dosha yoksa bu bloğu tamamen çıkarır.
    final seviye = (n['seviye'] ?? '').toString();
    final renk = seviye == 'belirgin'
        ? FastTheme.danger
        : (seviye == 'hafif' ? FastTheme.warning : FastTheme.accentGold);

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        border: Border.all(color: renk.withValues(alpha: 0.55)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.balance, size: 16, color: renk),
              const SizedBox(width: 8),
              Expanded(
                child: Text(baslik,
                    style: TextStyle(
                        color: FastTheme.textMuted,
                        fontSize: 13,
                        fontWeight: FontWeight.w700)),
              ),
              if (baslikSeviye.isNotEmpty)
                Text(baslikSeviye,
                    style: TextStyle(
                        color: renk, fontSize: 11, fontWeight: FontWeight.w700)),
            ],
          ),
          if (aciklama.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(aciklama,
                style:
                    TextStyle(color: FastTheme.text, fontSize: 12.5, height: 1.6)),
          ],
          if (ozet.isNotEmpty) ...[
            const SizedBox(height: 10),
            // Özet: etiket/değer çiftleri iki sütuna sarılır.
            ...ozet.entries.map((e) => Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(e.key.toString(),
                            style: TextStyle(
                                color: FastTheme.textDim, fontSize: 11.5)),
                      ),
                      Text(e.value.toString(),
                          style: GoogleFonts.cormorantGaramond(
                              fontSize: 12.5,
                              fontWeight: FontWeight.w700,
                              color: FastTheme.textLight)),
                    ],
                  ),
                )),
          ],
          for (final k in kosullar) ...[
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                    (k['tur'] ?? '') == 'taraka'
                        ? Icons.priority_high
                        : Icons.check_circle_outline,
                    size: 14,
                    color: (k['tur'] ?? '') == 'taraka'
                        ? FastTheme.warning
                        : FastTheme.success),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                          '${k['tur_etiket'] ?? ''} ${k['baslik'] ?? ''}'
                              .trimRight(),
                          style: TextStyle(
                              color: FastTheme.textLight,
                              fontSize: 12,
                              fontWeight: FontWeight.w600)),
                      const SizedBox(height: 2),
                      Text(k['detay']?.toString() ?? '',
                          style: TextStyle(
                              color: FastTheme.textDim,
                              fontSize: 11.5,
                              height: 1.5)),
                    ],
                  ),
                ),
              ],
            ),
          ],
          if (ipucu.isNotEmpty) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: FastTheme.bgSecondary,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: FastTheme.border),
              ),
              child: Text(ipucu,
                  style: TextStyle(
                      color: FastTheme.textDim, fontSize: 11.5, height: 1.5)),
            ),
          ],
          if (puanNotu.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(puanNotu,
                style: TextStyle(color: FastTheme.textDim, fontSize: 11)),
          ],
          // Bu motor yalnızca Ay konumundan hesapladığı için klasik
          // kürdürme (kendra/dusthana) kuralları burada bilinçli olarak
          // uygulanmaz; hangilerinin atlandığı kullanıcıya açıkça söylenir.
          if (kapsamDisi.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(kapsamBaslik,
                style: TextStyle(
                    color: FastTheme.textDim,
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700)),
            if (kapsamNotu.isNotEmpty) ...[
              const SizedBox(height: 3),
              Text(kapsamNotu,
                  style: TextStyle(
                      color: FastTheme.textDim, fontSize: 11, height: 1.5)),
            ],
            const SizedBox(height: 4),
            ...kapsamDisi.map((k) => Padding(
                  padding: const EdgeInsets.only(bottom: 2),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('·  ',
                          style: TextStyle(color: FastTheme.textDim)),
                      Expanded(
                        child: Text(k['ad']?.toString() ?? '',
                            style: TextStyle(
                                color: FastTheme.textDim, fontSize: 11)),
                      ),
                    ],
                  ),
                )),
          ],
        ],
      ),
    );
  }

  /// İlişki Skorları sonuç ekranı: toplam puan, iki Ay profili ve 8 koota satırı.
  Widget _ashResults(Map<String, dynamic> r, AppLocalizations l10n) {
    final t = (r['ashtakoot'] as Map?)?.cast<String, dynamic>() ?? r;
    final kootalar = (t['kootalar'] as List?) ?? const [];
    final a = (t['a'] as Map?)?.cast<String, dynamic>();
    final b = (t['b'] as Map?)?.cast<String, dynamic>();
    final toplam = (t['toplam'] ?? r['toplam'] ?? 0) as int;
    final azami = (t['azami'] ?? r['azami'] ?? 36) as int;
    final yuzde = (t['yuzde'] ?? r['yuzde'] ?? 0.0).toDouble();
    final seviye = (t['seviye'] ?? r['seviye'] ?? '') as String;
    final uyari = (t['uyari'] as List?)?.cast<String>() ?? const [];
    final dil = Localizations.localeOf(context).languageCode;
    // Backend yanitinda aciklama ve utc ust seviyede gelir; ic ice gomulmus
    // surum icin t[] de korunur. Once ust seviye denenir, boylece sozlesme
    // degisse de okuma sessizce bos kalmaz.
    final aciklama = ((r['aciklama'] ?? t['aciklama']) as Map?)
        ?.cast<String, dynamic>();
    final aciklamaKootalar = ((aciklama?['kootalar'] as List?) ?? const [])
        .map((e) => (e as Map).cast<String, dynamic>())
        .toList();
    final aciklamaToplam = (aciklama?['toplam'] as Map?)?.cast<String, dynamic>();
    final utc = ((r['utc'] ?? t['utc']) as Map?)?.cast<String, dynamic>();
    final utcNotu = ((r['utc_notu'] ?? t['utc_notu'] ?? '') as String).trim();

    // Sunucu her koota için ham puanı (t.kootalar) ve açıklamayı
    // (aciklama.kootalar) ayrı döner; ekranda tek kartta birleştiriyoruz.
    Map<String, dynamic>? _aciklamaKota(String ad) {
      for (final k in aciklamaKootalar) {
        if (k['ad'] == ad) return k;
      }
      return null;
    }

    String _ad(Map k) {
      if (dil == 'en') return (k['ad_en'] ?? k['ad'] ?? '').toString();
      if (dil == 'es') return (k['ad_es'] ?? k['ad'] ?? '').toString();
      return (k['ad_tr'] ?? k['ad'] ?? '').toString();
    }

    String _seviyeMetni() {
      switch (seviye) {
        case 'cok_dusuk': return l10n.ashLevelVeryLow;
        case 'dusuk': return l10n.ashLevelLow;
        case 'yuksek': return l10n.ashLevelHigh;
        default: return l10n.ashLevelMedium;
      }
    }

    Widget _ayKarti(Map? m, String baslik) {
      if (m == null) return const SizedBox.shrink();
      return Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: FastTheme.cardBg,
          border: Border.all(color: FastTheme.border),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(baslik,
                style: TextStyle(
                    color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w700)),
            const SizedBox(height: 4),
            Text(
              '${m['nakshatra']} · ${m['pada']}. pada · ${m['burc']}',
              style: TextStyle(color: FastTheme.textMuted, fontSize: 13),
            ),
            Text(
              'Lord: ${m['lord']}  ·  ${m['tanri']}',
              style: TextStyle(color: FastTheme.textDim, fontSize: 11),
            ),
            Text(
              '${l10n.ashVarna}: ${m['varna']}  ·  ${l10n.ashGana}: ${m['gana']}  ·  ${l10n.ashNadi}: ${m['nadi']}',
              style: TextStyle(color: FastTheme.textDim, fontSize: 11),
            ),
            if (m['yaklasik'] == true)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(l10n.ashApproximate,
                    style: TextStyle(color: FastTheme.accentGold, fontSize: 11)),
              ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(l10n.analyzerResultsTitle,
            style: TextStyle(color: FastTheme.textMuted, fontSize: 14, letterSpacing: 1)),
        const SizedBox(height: 16),

        // Toplam puan
        _scoreCard(
          l10n.ashTotalScore,
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('$toplam / $azami',
                  style: GoogleFonts.cormorantGaramond(
                      fontSize: 34, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
              Text('${yuzde.toStringAsFixed(1)}%  ·  ${_seviyeMetni()}',
                  style: TextStyle(color: FastTheme.textDim, fontSize: 12)),
            ],
          ),
        ),
        const SizedBox(height: 24),

        // Genel yorum (doğal dil, sunucuda üretildi)
        if ((aciklamaToplam?['aciklama'] ?? '').toString().isNotEmpty) ...[
          _metinKarti(
            (aciklamaToplam?['baslik'] ?? l10n.ashOverallReading).toString(),
            aciklamaToplam!['aciklama'].toString(),
            ipucu: (aciklamaToplam['ipucu'] ?? '').toString(),
          ),
          const SizedBox(height: 16),
        ],

        // UTC çözümü şeffaflığı: kullanıcı hangi şehir/ofsetin kullanıldığını
        // görebilmeli; skor bu tek değere dayandığı için kritik.
        if (utc != null) ...[
          _utcKarti(l10n, utc, utcNotu),
          const SizedBox(height: 16),
        ],

        _sectionTitle(l10n.ashMoonProfiles),
        _ayKarti(a, l10n.ashPersonAMoon),
        _ayKarti(b, l10n.ashPersonBMoon),
        const SizedBox(height: 16),

        // Nadi Dosha, Ashtakoot'un tek sifir puanli kalemi oldugu icin
        // kootalar listesinden hemen once ayri bir kart olarak gosterilir.
        // Backend metinleri tam olarak yerellestirdigi icin burada ek bir
        // ceviri zinciri yoktur; yalnizca sunum yapilir.
        if (aciklama?['nadi_dosha'] != null) ...[
          _nadiDosyaKarti(
              (aciklama!['nadi_dosha'] as Map).cast<String, dynamic>()),
          const SizedBox(height: 16),
        ],

        _sectionTitle(l10n.ashKootalar),
        ...kootalar.map((k) {
          final kk = (k as Map).cast<String, dynamic>();
          final p = (kk['puan'] ?? 0) as int;
          final m = (kk['azami'] ?? 1) as int;
          final oran = m == 0 ? 0.0 : (p / m).clamp(0.0, 1.0);
          // Ham puan (t.kootalar) + açıklama (aciklama.kootalar) birleştirilir.
          final ak = _aciklamaKota((kk['ad'] ?? '').toString()) ?? const {};
          // Backend'in JARGONSUZ adi onceliklidir (orn. "Ic dunya ve
          // mahremiyet"); ham koota verisinde eksikse _ad() teknik ada duser.
          final baslik = (ak['baslik'] ?? '').toString();
          final gorunecekAd = baslik.isNotEmpty ? baslik : _ad(kk);
          // Ana metin: 3+ satirlik dogral dil yorumu (sunucu her istekte
          // vaat/anlati/simge acilarindan birini rastgele secer).
          final yorum = (ak['aciklama'] ?? '').toString();
          // Kisisel satir: gercek yerlesim adlari (her ciftte farkli).
          final kisisel = (ak['kisisel'] ?? '').toString();
          // Teknik icerik varsayilan gizli; kullanici "Detayi goster" ile acar.
          final konu = (ak['konu'] ?? '').toString();
          final soru = (ak['soru'] ?? '').toString();
          final ipucu = (ak['ipucu'] ?? '').toString();
          final notMetni = (kk['not'] ?? '').toString();
          final detay = (ak['detay'] as Map?)?.cast<String, dynamic>() ?? const {};
          final detayVar = konu.isNotEmpty ||
              soru.isNotEmpty ||
              ipucu.isNotEmpty ||
              notMetni.isNotEmpty ||
              detay.isNotEmpty;
          final detayAcik =
              detayVar && _ashDetayAcik.contains((kk['ad'] ?? '').toString());
          return Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: FastTheme.cardBg,
              border: Border.all(
                  color: oran >= 0.99 ? FastTheme.accentGold : FastTheme.border),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(gorunecekAd,
                          style: TextStyle(
                              color: FastTheme.textMuted,
                              fontSize: 13,
                              fontWeight: FontWeight.w700)),
                    ),
                    Text('$p / $m',
                        style: GoogleFonts.cormorantGaramond(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                            color: oran >= 0.99 ? FastTheme.accentGold : FastTheme.textDim)),
                  ],
                ),
                if (oran > 0) ...[
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: oran,
                      minHeight: 4,
                      backgroundColor: FastTheme.bg,
                      valueColor: AlwaysStoppedAnimation(
                          oran >= 0.99 ? FastTheme.accentGold : FastTheme.textDim),
                    ),
                  ),
                ],
                if (yorum.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(yorum,
                      style: TextStyle(
                          color: FastTheme.textMuted, fontSize: 12.5, height: 1.45)),
                ],
                if (kisisel.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Text(kisisel,
                      style: TextStyle(
                          color: FastTheme.accentGold,
                          fontSize: 11.5,
                          height: 1.4,
                          fontStyle: FontStyle.italic)),
                ],
                if (detayVar) ...[
                  const SizedBox(height: 6),
                  InkWell(
                    onTap: () => _ashDetayDegistir((kk['ad'] ?? '').toString()),
                    borderRadius: BorderRadius.circular(6),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 2),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                              detayAcik
                                  ? Icons.expand_less
                                  : Icons.expand_more,
                              size: 14,
                              color: FastTheme.textDim),
                          const SizedBox(width: 3),
                          Text(detayAcik ? l10n.ashHideDetail : l10n.ashShowDetail,
                              style: TextStyle(
                                  color: FastTheme.textDim,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                  ),
                ],
                if (detayAcik) ...[
                  if (konu.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(konu,
                          style: TextStyle(
                              color: FastTheme.accentGold, fontSize: 11, height: 1.3)),
                    ),
                  if (soru.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(soru,
                          style: TextStyle(
                              color: FastTheme.textDim,
                              fontSize: 11,
                              height: 1.35,
                              fontStyle: FontStyle.italic)),
                    ),
                  if (notMetni.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(notMetni,
                          style: TextStyle(
                              color: FastTheme.textDim, fontSize: 11, height: 1.35)),
                    ),
                  if (detay.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        '${detay['a'] ?? ''}  ↔  ${detay['b'] ?? ''}',
                        style: TextStyle(color: FastTheme.textDim, fontSize: 11),
                      ),
                    ),
                  if (ipucu.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.lightbulb_outline,
                              size: 13, color: FastTheme.accentGold),
                          const SizedBox(width: 5),
                          Expanded(
                            child: Text(ipucu,
                                style: TextStyle(
                                    color: FastTheme.textDim,
                                    fontSize: 11,
                                    height: 1.35)),
                          ),
                        ],
                      ),
                    ),
                ],
              ],
            ),
          );
        }),
        const SizedBox(height: 16),

        if (uyari.isNotEmpty) ...[
          _sectionTitle(l10n.ashWarnings),
          ...uyari.map((u) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.info_outline, size: 14, color: FastTheme.accentGold),
                    const SizedBox(width: 6),
                    Expanded(
                        child: Text(u,
                            style: TextStyle(
                                color: FastTheme.textDim, fontSize: 11, height: 1.35))),
                  ],
                ),
              )),
        ],
      ],
    );
  }

  Widget _scoreCards(Map<String, dynamic> r, AppLocalizations l10n) {
    if (_tekKisiMod) {
      // bireysel/potansiyel modda uyum kartlarını tamamen gizle
      return const SizedBox.shrink();
    }
    final uyum = r['uyum_orani']?.toString() ?? '';
    final tork = r['tork']?.toString() ?? '';
    final fraktal = r['fraktal']?.toString() ?? '';
    final torkMetin = r['tork_metin']?.toString() ?? '';
    final fraktalMetin = r['fraktal_metin']?.toString() ?? '';
    // Skor üçlüsü yan yana kompakt kartlar halinde.
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (uyum.isNotEmpty)
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: _scoreCard(
                    l10n.scoreGoldenSeal,
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Φ', style: GoogleFonts.cormorantGaramond(fontSize: 28, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                        const SizedBox(height: 4),
                        Text('1.618', style:  TextStyle(color: FastTheme.textLight, fontSize: 11)),
                      ],
                    ),
                    compact: true,
                  ),
                ),
              ),
            if (tork.isNotEmpty)
              Expanded(
                child: Padding(
                  padding: EdgeInsets.only(right: fraktal.isNotEmpty ? 8 : 0),
                  child: _scoreCard(
                    l10n.scoreVitality,
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('$tork', style: GoogleFonts.cormorantGaramond(fontSize: 28, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                        const SizedBox(height: 4),
                        Text('/10', style:  TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                      ],
                    ),
                    compact: true,
                  ),
                ),
              ),
            if (fraktal.isNotEmpty)
              Expanded(
                child: _scoreCard(
                  l10n.scoreFlow,
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('$fraktal', style: GoogleFonts.cormorantGaramond(fontSize: 28, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
                      const SizedBox(height: 4),
                      Text('%', style:  TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                    ],
                  ),
                  compact: true,
                ),
              ),
          ],
        ),
        const SizedBox(height: 8),
        // Tam açıklamalar
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            gradient:  LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [FastTheme.cardBg, FastTheme.bgSecondary]),
            border: Border.all(color: FastTheme.border),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.scoreDetailTitle, style:  TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: 1)),
              const SizedBox(height: 8),
              if (uyum.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.spa, color: FastTheme.rose, size: 16),
                      const SizedBox(width: 8),
                      Expanded(child: Text(uyum, style:  TextStyle(color: FastTheme.text, fontSize: 12.5, height: 1.6))),
                    ],
                  ),
                ),
              if (tork.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.bolt, color: FastTheme.secondary, size: 16),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text('$tork/10 · ${torkMetin.isNotEmpty ? torkMetin : _torkSub(r['tork'], l10n)}',
                            style:  TextStyle(color: FastTheme.text, fontSize: 12.5, height: 1.6)),
                      ),
                    ],
                  ),
                ),
              if (fraktal.isNotEmpty)
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.waves, color: FastTheme.accent, size: 16),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text('$fraktal% · ${fraktalMetin.isNotEmpty ? fraktalMetin : _fraktalSub(r['fraktal'], l10n)}',
                          style:  TextStyle(color: FastTheme.text, fontSize: 12.5, height: 1.6)),
                    ),
                  ],
                ),
            ],
          ),
        ),
      ],
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

  Widget _scoreCard(String label, Widget valueWidget, {String? sub, bool compact = false}) {
    return Container(
      padding: EdgeInsets.all(compact ? 12 : 20),
      decoration: BoxDecoration(
        gradient:  LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [FastTheme.cardBg, FastTheme.bgSecondary]),
        border: Border.all(color: FastTheme.border),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: compact ? CrossAxisAlignment.start : CrossAxisAlignment.center,
        children: [
          Text(label.toUpperCase(), style:  TextStyle(color: FastTheme.textDim, fontSize: compact ? 9 : 10, letterSpacing: 1)),
          const SizedBox(height: 4),
          valueWidget,
          if (sub != null) ...[
            const SizedBox(height: 4),
            Text(sub, style:  TextStyle(color: FastTheme.textMuted, fontSize: 11), textAlign: TextAlign.center),
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
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 4),
                Text(l10n.analyzerPotentialTop5Hint,
                  style:  TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                ...((r['potansiyel_alanlar'] as List).take(5).map((p) => Container(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('✨ ${p['alan'] ?? ''}', style:  TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: FastTheme.text)),
                      Text(l10n.analyzerAspectOrb(p['aci'] ?? '', p['orb'] ?? '', p['aci_turu'] ?? ''),
                        style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
                      if (p['metin'] != null) Text(p['metin'].toString(), style:  TextStyle(color: FastTheme.textMuted, fontSize: 11, height: 1.4)),
                    ],
                  ),
                ))),
                const SizedBox(height: 8),
                Text(l10n.analyzerPotentialAllPdf,
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
              ],
            )),

        // Meslek Önerileri
        if ((_isEb || _isPy) && r['meslek_onerileri'] is List && (r['meslek_onerileri'] as List).isNotEmpty)
          _sectionCard('🎯', l10n.analyzerSectionProfession, defaultOpen: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_isEb ? l10n.analyzerProfessionChildDesc : l10n.analyzerProfessionSelfDesc,
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 4),
                Text(l10n.analyzerProfessionFullRanking, style:  TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                ...((r['meslek_onerileri'] as List).map((m) => Container(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${(r['meslek_onerileri'] as List).indexOf(m) + 1}. ${m['alan'] ?? ''}',
                        style:  TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: FastTheme.text)),
                      Text(l10n.analyzerScorePoints(m['yuzde'] ?? '', m['puan']?.toStringAsFixed(1) ?? ''),
                        style:  TextStyle(color: FastTheme.accentGold, fontSize: 11)),
                      if (m['meslekler'] is List) ...((m['meslekler'] as List).map((j) => Padding(
                        padding: const EdgeInsets.only(left: 12, top: 2),
                        child: Text('🧑‍💼 ${j['meslek'] ?? ''} — ${j['aciklama'] ?? ''}',
                          style:  TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                      ))),
                    ],
                  ),
                ))),
                Text(l10n.analyzerProfessionScoringNote,
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
                Text(l10n.analyzerProfessionPdfHint, style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
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
                      Text('${p['kisi'] ?? p['baslik'] ?? ''}', style:  TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w600)),
                    if ((p['ilerleme_yili'] ?? 0) > 0)
                      Text(l10n.analyzerProgressionYear((p['ilerleme_yili'] as num).toStringAsFixed(1)), style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
                    if (p['ay_burcu'] != null)
                      Text('${l10n.analyzerMoon}: ${p['ay_burcu']} | ${l10n.analyzerSun}: ${p['gunes_burcu'] ?? ''}', style:  TextStyle(color: FastTheme.textMuted, fontSize: 11)),
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
                          border:  Border(left: BorderSide(color: FastTheme.accentGold, width: 3)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(aci['baslik'] ?? '', style:  TextStyle(color: FastTheme.accentGold, fontSize: 11, fontWeight: FontWeight.w600)),
                            Text(aci['yorum'] ?? '', style:  TextStyle(color: FastTheme.textMuted, fontSize: 11, height: 1.5)),
                            Text('${aci['aci_turu'] ?? ''} · ${aci['etki'] ?? ''} · ${aci['donem'] ?? ''}',
                              style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
                          ],
                        ),
                      ))),
                    if ((p['toplam_aci'] ?? 0) > 0)
                      Text(l10n.analyzerTotalAspects(p['toplam_aci']),
                        style:  TextStyle(color: FastTheme.textDim, fontSize: 10, fontStyle: FontStyle.italic)),
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
                   mainAxisAlignment: MainAxisAlignment.start,
                   children: [
                     Align(
                       alignment: Alignment.centerLeft,
                       child: Text('🗓️ ${a['tarih'] ?? ''} (${a['gun_ad'] ?? ''})',
                           style:  TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w600)),
                     ),
                     if (_isNatal && a['ortam'] != null) ...[
                      Text('🌙 Ay ${a['ay_burc'] ?? ''} — ${a['ay_ev'] ?? ''}. Ev (${a['ay_derece'] ?? ''}°)',
                        style:  TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                      Text(a['ortam'].toString(), style:  TextStyle(color: FastTheme.textDim, fontSize: 11, fontStyle: FontStyle.italic)),
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
                    Text(m['baslik'] ?? '', style:  TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w600)),
                    Text(m['icerik'] ?? '', style:  TextStyle(color: FastTheme.textMuted, fontSize: 12)),
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
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 4),
                Text(l10n.analyzerArabicPdfHint, style:  TextStyle(color: FastTheme.accentGold, fontSize: 10)),
                ...((r['arap_noktalari'] as Map).entries.map((e) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('🔮 ${e.key}', style:  TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w600)),
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
                            style:  TextStyle(fontSize: 10, color: FastTheme.textMuted)),
                        )).toList(),
                      ),
                    ],
                  ),
                ))),
                if (r['arap_sinastri'] is List && (r['arap_sinastri'] as List).isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text('🔗 ${l10n.analyzerSectionArabicBonds}', style:  TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w600)),
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
                          style:  TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                        if (b['yorum'] != null)
                          Text(b['yorum'].toString(), style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
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
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 12)),
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
                                    style:  TextStyle(color: FastTheme.accentGold, fontSize: 14, fontWeight: FontWeight.w500)),
                                  const SizedBox(height: 8),
                                  if (h['yorum'] != null)
                                    Text(h['yorum'].toString(), style:  TextStyle(color: FastTheme.textMuted, fontSize: 12, height: 1.6)),
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
                                          child: Text('💡 ${o['metin'] ?? ''}', style:  TextStyle(color: FastTheme.textMuted, fontSize: 10)),
                                        );
                                      }).toList(),
                                    ),
                                  ],
                                  const SizedBox(height: 6),
                                  Center(child: Text(l10n.analyzerCloseHint, style:  TextStyle(color: FastTheme.textDim, fontSize: 9))),
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
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 12)),
                const SizedBox(height: 8),
                ...((r['sabianlar'] as List).map((s) => Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: FastTheme.cardBg,
                    borderRadius: BorderRadius.circular(6),
                    border:  Border(left: BorderSide(color: FastTheme.accentGold, width: 3)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${s['gezegen'] ?? ''} (${s['derece_str'] ?? '${s['derece']}°'})',
                        style:  TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w600)),
                      Text(s['sembol'] ?? '', style:  TextStyle(color: FastTheme.textMuted, fontSize: 11, height: 1.5)),
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
                        style:  TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w600)),
                      Text(l10n.analyzerMoonSunHouse(p['ay_ev'] ?? '', p['ay_burc'] ?? '', p['gunes_burc'] ?? ''),
                        style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
                      if (p['ortam'] != null)
                        Text(p['ortam'].toString(), style:  TextStyle(color: FastTheme.textDim, fontSize: 10, fontStyle: FontStyle.italic)),
                      if (p['yorumlar'] is List) ...((p['yorumlar'] as List).map((y) => Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text('🔹 $y', style:  TextStyle(color: FastTheme.textMuted, fontSize: 11)),
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
                      style:  TextStyle(color: FastTheme.textDim, fontSize: 10, fontStyle: FontStyle.italic)),
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
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 8),
                Text(r['chart_yorumu'].toString(), style:  TextStyle(color: FastTheme.text, fontSize: 12, height: 1.8)),
              ],
            )),

        // Sifa Receteleri (Natal)
        if (_isNatal && r['sifa_receteleri'] != null)
          _sectionCard('💊', l10n.analyzerSectionHealing, defaultOpen: true,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerHealingIntro,
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
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
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 8),
                ...((r['sifa_receteleri_detay'] as List).map((rct) => Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: FastTheme.cardBg, border: Border.all(color: FastTheme.border), borderRadius: BorderRadius.circular(8)),
                  child: Text(rct.toString(), style:  TextStyle(color: FastTheme.textMuted, fontSize: 12, height: 1.6)),
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
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 4),
                Text(l10n.analyzerAsteroidsOrbHint, style:  TextStyle(color: FastTheme.accentGold, fontSize: 10)),
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
                          Text(a['yorum'].toString(), style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
                      ],
                    ),
                  );
                })),
                const SizedBox(height: 4),
                Text(l10n.analyzerAsteroidsAllPdf,
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
              ],
            )),

        // Astrokartografi
        if (r['astrokartografi'] != null || sessionId.isNotEmpty)
          _sectionCard('🌍', l10n.analyzerSectionAlternateUniverse,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.analyzerAstroHint,
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
                const SizedBox(height: 8),

                // Astro location selector
                Row(
                  children: [
                    Expanded(
                      child: _dropdownField(l10n.analyzerCountry, ((_lokasyonDB?['sehirler'] as Map? ?? {}).keys.toList()..sort()).cast<String>(), _astroUlke, (v) {
                        setState(() { _astroUlke = v ?? ''; _astroSehir = ''; provider.resetAstro(); });
                      }, labels: countryLabels(Localizations.localeOf(context).languageCode)),
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
                  style:  TextStyle(color: FastTheme.textDim, fontSize: 11)),
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
                   Center(child: Padding(
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
                  style:  TextStyle(color: FastTheme.accentGold, fontSize: 10)),
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
                                          style:  TextStyle(color: FastTheme.accentGold, fontSize: 11, fontWeight: FontWeight.w600)),
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
              textAlign: TextAlign.center, style:  TextStyle(color: FastTheme.accentGold, fontSize: 13)),
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
              SizedBox(width: 80, child: Text(c['l'] as String, style:  TextStyle(fontSize: 12, color: FastTheme.textMuted))),
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
              SizedBox(width: 24, child: Text('${skor[c['k']] ?? 0}', style:  TextStyle(color: FastTheme.text, fontSize: 12, fontWeight: FontWeight.w600))),
            ],
          ),
        )),
        if (skor['etkiler'] is List && (skor['etkiler'] as List).isNotEmpty)
          ...((skor['etkiler'] as List).map((e) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 1),
            child: Text('• $e', style:  TextStyle(color: FastTheme.textDim, fontSize: 10)),
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
                      gradient: active ?  LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]) : null,
                      color: active ? null : FastTheme.cardBg,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: active ? FastTheme.accentGold : FastTheme.border),
                    ),
                     child: Text(_chartTabLabel(t.toString(), l10n), style: TextStyle(
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
                return  SizedBox(height: 300, child: Center(child: CircularProgressIndicator(color: FastTheme.accentGold)));
              },
              errorBuilder: (_, __, ___) => Container(
                height: 100,
                decoration: BoxDecoration(color: FastTheme.cardBg, borderRadius: BorderRadius.circular(12)),
                child: Center(child: Text(l10n.analyzerChartNotReady, style:  TextStyle(color: FastTheme.textDim, fontSize: 13))),
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
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
      child: Column(
        children: [
          const SizedBox(height: 8),
          Text('📄 ${l10n.analyzerReportTitle}', style: GoogleFonts.cormorantGaramond(fontSize: 18, fontWeight: FontWeight.w700, color: FastTheme.accentGold)),
          const SizedBox(height: 16),
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 360),
              child: Wrap(
                spacing: 12, runSpacing: 12, alignment: WrapAlignment.center,
                children: _pdfLinks(sessionId, l10n).map((link) => SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: _pdfLoading ? null : () => _downloadPdf(sessionId, link['tip'], l10n),
                    icon: _pdfLoading ?  SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: FastTheme.bg)) : const Icon(Icons.download, size: 20),
                    label: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      child: Text(_pdfLoading ? l10n.analyzerPdfPreparing : '📥 ${link['label']}', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: FastTheme.accentGold,
                      foregroundColor: FastTheme.bg,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 4,
                    ),
                  ),
                )).toList(),
              ),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
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
    if (_pdfLoading) return;
    setState(() => _pdfLoading = true);
    try {
      final url = await _api.getPdfUrl(sessionId, tip ?? 'rapor');
      final integrityToken = await PlayIntegrityService().requestToken();
      final headers = <String, String>{
        if (integrityToken != null) 'X-Play-Integrity-Token': integrityToken,
      };
      var resp = await http.get(Uri.parse(url), headers: headers).timeout(const Duration(seconds: 240));
      if (!mounted) return;
      if (resp.statusCode == 402) {
        // Tek PDF ($19.99) satın alma; webhook hakkı sunucuya yazsın diye kısa
        // bekleme + her durumda bir kez daha dene (zaten alınmışsa bile).
        await RevenueCatService.purchase('pdf_single');
        await Future.delayed(const Duration(seconds: 3));
        resp = await http.get(Uri.parse(url), headers: headers).timeout(const Duration(seconds: 240));
        if (!mounted) return;
        if (resp.statusCode == 402) {
          setState(() => _pdfLoading = false);
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.pdfPaymentRequired)));
          return;
        }
      }
      if (resp.statusCode != 200) {
        setState(() => _pdfLoading = false);
        throw Exception(l10n.analyzerPdfNotFound('${resp.statusCode}'));
      }
      final dir = await getApplicationDocumentsDirectory();
      final dosya = File('${dir.path}/${sessionId}_${tip ?? 'rapor'}.pdf');
      await dosya.writeAsBytes(resp.bodyBytes, flush: true);
      final sonuc = await OpenFile.open(dosya.path);
      if (!mounted) return;
      setState(() => _pdfLoading = false);
      final msg = sonuc.type == ResultType.done
          ? l10n.analyzerPdfDownloaded(dosya.path)
          : l10n.analyzerPdfSuccess;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
    } catch (e) {
      if (!mounted) return;
      setState(() => _pdfLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.analyzerPdfError('$e'))));
    }
  }

  // ========== EXIT / ACTIONS ==========
  Widget _exitSection(AppLocalizations l10n) {
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 360),
      child: Column(
        children: [
          ElevatedButton.icon(
            onPressed: () {
              Navigator.of(context, rootNavigator: true).popUntil((r) => r.isFirst);
            },
            icon: const Icon(Icons.home_outlined, size: 20),
            label: Padding(
              padding: const EdgeInsets.symmetric(vertical: 10),
              child: Text(l10n.exitToMenu, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: FastTheme.accent,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 4,
            ),
          ),
          const SizedBox(height: 12),
           OutlinedButton(
             onPressed: _analizdenCik,
             style: OutlinedButton.styleFrom(
               side:  BorderSide(color: FastTheme.border),
               foregroundColor: FastTheme.text,
               shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
             ),
             child: Padding(
               padding: const EdgeInsets.symmetric(vertical: 10),
               child: Text(l10n.exitFromAnalysis, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
             ),
           ),
        ],
      ),
    );
  }

  /// "Analizden Çık": analizi tamamen kapatır ve simülasyon ekranına döner.
  ///
  /// Yukarıdaki "menüye dön" butonundan farklıdır; o rota yığınını
  /// kapatıp ana ekrana çıkar. Burada uygulama açık kalır, yalnızca
  /// biten analizin sonucu, hatası ve o sonuca bağlı yerel UI durumu
  /// temizlenir; `_mainContent` `_beforeAnalysis` (simülasyon seçim
  /// ekranını) göstermeye devam eder.
  void _analizdenCik() {
    context.read<AnalysisProvider>().reset();
    setState(() {
      _expandedHayat = -1;
      _chartTab = 'situa_a';
      _menuOpen = false;
      _prevSimData = null;
      _wikiPages = {};
      _ashShowManualOffset = false;
      _p1OfsetCtrl.clear();
      _p2OfsetCtrl.clear();
      _geoHint = null;
      _astroUlke = '';
      _astroSehir = '';
    });
  }

  // ========== HELPERS ==========
  Widget _sectionCard(String icon, String title, {required Widget child, bool defaultOpen = false}) {
    return w.SectionCard(icon: Icons.star, title: '$icon $title', child: child);
  }

  String _chartTabLabel(String key, AppLocalizations l10n) {
    switch (key) {
      case 'situa_a': return l10n.chartTabSituaA;
      case 'situa_b': return l10n.chartTabSituaB;
      case 'frekans': return l10n.chartTabFrekans;
      case 'composite': return l10n.chartTabComposite;
      case 'aci_gridi': return l10n.chartTabAciGridi;
      case 'arap_noktalari': return l10n.chartTabArapNoktalari;
      default: return key;
    }
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
