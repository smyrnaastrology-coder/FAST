import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../l10n/app_localizations.dart';
import '../models/analysis_request.dart';
import '../config/theme.dart';
import '../config/country_labels.dart';
import '../services/api_service.dart';
import '../providers/locale_provider.dart';
import '../widgets/language_switcher.dart';
import 'results_screen.dart';

class InputFormScreen extends StatefulWidget {
  final String mod;
  const InputFormScreen({super.key, required this.mod});

  @override
  State<InputFormScreen> createState() => _InputFormScreenState();
}

class _InputFormScreenState extends State<InputFormScreen> {
  final _api = ApiService();

  // Person 1
  final _p1IsimCtrl = TextEditingController();
  final _p1TarihCtrl = TextEditingController();
  final _p1SaatCtrl = TextEditingController(text: '12:00');

  // Person 2
  final _p2IsimCtrl = TextEditingController();
  final _p2TarihCtrl = TextEditingController();
  final _p2SaatCtrl = TextEditingController(text: '12:00');

  // Event
  final _eventTarihCtrl = TextEditingController();
  final _eventSaatCtrl = TextEditingController(text: '12:00');

  // Location
  String _seciliUlke = 'Türkiye';
  String _seciliSehir = 'İstanbul';
  final _latCtrl = TextEditingController(text: '41.0082');
  final _lonCtrl = TextEditingController(text: '28.9784');
  String? _geoHint;

  // Ebeveyn
  String _ebeveynRolu = 'anne';

  // DB
  Map<String, dynamic>? _lokasyonDB;
  bool _dbLoading = true;
  bool _geoLoading = false;

  String get _modKey => widget.mod;

  bool get _ikinciKisiGerekli => _modKey == 'es_sevgili' || _modKey == 'ebeveyn_cocuk';
  bool get _eventGerekli => _modKey == 'es_sevgili';
  bool get _ebeveynMod => _modKey == 'ebeveyn_cocuk';
  bool get _natalMod => _modKey == 'bireysel_natal';
  bool get _potansiyelMod => _modKey == 'potansiyel_yetenek';
  bool get _tekKisiMod => _natalMod || _potansiyelMod;

  @override
  void initState() {
    super.initState();
    _loadDB();
  }

  Future<void> _loadDB() async {
    try {
      final d = await _api.getUlkeler();
      if (d.isNotEmpty && d[0] is Map) {
        _lokasyonDB = d[0] as Map<String, dynamic>;
      }
    } catch (_) {}
    _dbLoading = false;
    if (mounted) setState(() {});
  }

  Future<void> _pickDate(TextEditingController ctrl) async {
    final d = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(1900),
      lastDate: DateTime(2100),
    );
    if (d != null) {
      ctrl.text = '${d.day.toString().padLeft(2, '0')}.${d.month.toString().padLeft(2, '0')}.${d.year}';
    }
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

  Future<void> _pickTime(TextEditingController ctrl) async {
    final t = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (t != null) {
      ctrl.text = '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
    }
  }

  Future<void> _geoCode(String sehir) async {
    if (sehir.length < 3) return;
    setState(() => _geoLoading = true);
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
    setState(() => _geoLoading = false);
  }

  void _submit() {
    final l10n = AppLocalizations.of(context);
    if (_p1TarihCtrl.text.isEmpty) {
      _snack(l10n.analyzerDateRequired);
      return;
    }
    if (_ikinciKisiGerekli && _p2TarihCtrl.text.isEmpty) {
      _snack(l10n.analyzerDate2Required);
      return;
    }
    if (_tekKisiMod && _p1IsimCtrl.text.trim().isEmpty) {
      _snack(l10n.analyzerNameRequired);
      return;
    }
    if (_ebeveynMod && _p1IsimCtrl.text.trim().isEmpty) {
      _snack(l10n.analyzerParentNameRequired);
      return;
    }

    final req = AnalysisRequest(
      p1Isim: _p1IsimCtrl.text,
      p1Tarih: _p1TarihCtrl.text,
      p1Saat: _p1SaatCtrl.text,
      p2Isim: _p2IsimCtrl.text,
      p2Tarih: _ikinciKisiGerekli ? _p2TarihCtrl.text : _p1TarihCtrl.text,
      p2Saat: _p2SaatCtrl.text,
      eventTarih: _eventGerekli ? _eventTarihCtrl.text : '',
      eventSaat: _eventSaatCtrl.text,
      ebeveynRolu: _ebeveynRolu,
      city: _seciliSehir,
      country: _seciliUlke,
      lat: double.tryParse(_latCtrl.text) ?? 41.0082,
      lon: double.tryParse(_lonCtrl.text) ?? 28.9784,
      mod: _modKey,
      lang: context.read<LocaleProvider>().locale.languageCode,
    );

    Navigator.push(context, MaterialPageRoute(
      builder: (_) => ResultsScreen(request: req),
    ));
  }

  void _snack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  List<String>? get _ulkeler => (_lokasyonDB?['ulkeler'] as List?)?.cast<String>();
  List<String>? get _sehirler => (_lokasyonDB?['sehirler']?[_seciliUlke] as List?)?.cast<String>();

  String _modeTitle(AppLocalizations l10n) {
    switch (widget.mod) {
      case 'es_sevgili': return l10n.modeEsTitle;
      case 'ebeveyn_cocuk': return l10n.modeEbTitle;
      case 'potansiyel_yetenek': return l10n.modePyTitle;
      case 'bireysel_natal': return l10n.modeNatalTitle;
      default: return widget.mod;
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
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.of(context).maybePop()),
        title: Text(_modeTitle(l10n)), actions: const [LanguageSwitcher()]),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ---- PERSON 1 ----
            if (_ebeveynMod) _sectionBaslik(l10n.analyzerParent, Icons.family_restroom, FastTheme.secondary)
            else if (_tekKisiMod) _sectionBaslik(l10n.analyzerPersonalInfo, Icons.person, FastTheme.primary)
            else _sectionBaslik(l10n.analyzerPerson1, Icons.person, FastTheme.rose),

            if (_ebeveynMod) ...[
              _dropdownField(l10n.analyzerParentRole, ['anne', 'baba'], _ebeveynRolu, (v) => _ebeveynRolu = v!,
                labels: {'anne': l10n.analyzerMother, 'baba': l10n.analyzerFather}),
              const SizedBox(height: 12),
            ],
            if (_tekKisiMod || _ebeveynMod || _modKey == 'es_sevgili')
              _textField(l10n.analyzerName, _p1IsimCtrl, icon: Icons.person),
            if (_tekKisiMod || _ebeveynMod || _modKey == 'es_sevgili')
              const SizedBox(height: 12),
            _dateField(l10n.analyzerBirthDate, _p1TarihCtrl, l10n),
            const SizedBox(height: 12),
            if (!_ebeveynMod)
              _timeField(l10n.analyzerBirthTime, _p1SaatCtrl),

            const SizedBox(height: 24),

            // ---- PERSON 2 (es/eb only) ----
            if (_ikinciKisiGerekli) ...[
              if (_ebeveynMod) _sectionBaslik(l10n.analyzerChild, Icons.child_care, FastTheme.secondary)
              else _sectionBaslik(l10n.analyzerPerson2, Icons.person_outline, FastTheme.rose),
              if (!_ebeveynMod) ...[
                _textField(l10n.analyzerName, _p2IsimCtrl, icon: Icons.person_outline),
                const SizedBox(height: 12),
              ],
              _dateField(l10n.analyzerBirthDate, _p2TarihCtrl, l10n),
              const SizedBox(height: 12),
              if (_ebeveynMod)
                _timeField(l10n.analyzerBirthTime, _p2SaatCtrl),
              const SizedBox(height: 24),
            ],

            // ---- EVENT (es only) ----
            if (_eventGerekli) ...[
              _sectionBaslik(l10n.analyzerMeetingMarriage, Icons.favorite, FastTheme.rose),
              _dateField(l10n.analyzerDate, _eventTarihCtrl, l10n, zorunlu: false),
              const SizedBox(height: 12),
              _timeField(l10n.analyzerTime, _eventSaatCtrl),
              const SizedBox(height: 24),
            ],

            // ---- LOCATION ----
            _sectionBaslik(l10n.analyzerLocation, Icons.location_on, FastTheme.accent),
            const SizedBox(height: 12),

            if (_dbLoading)
              const LinearProgressIndicator()
            else ...[
              _dropdownField(l10n.analyzerCountry, _ulkeler ?? [], _seciliUlke, (v) {
                setState(() {
                  _seciliUlke = v!;
                  _seciliSehir = '';
                  _geoHint = l10n.analyzerSelectCity;
                });
              }, labels: countryLabels(Localizations.localeOf(context).languageCode)),
              const SizedBox(height: 12),
              if (_sehirler != null)
                _dropdownField(l10n.analyzerCity, _sehirler!, _seciliSehir, (v) {
                  setState(() => _seciliSehir = v!);
                  _geoCode(v!);
                }),
            ],

            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(child: _textField(l10n.analyzerLatitude, _latCtrl, icon: Icons.explore, keyboardType: TextInputType.numberWithOptions(decimal: true))),
                const SizedBox(width: 12),
                Expanded(child: _textField(l10n.analyzerLongitude, _lonCtrl, icon: Icons.explore, keyboardType: TextInputType.numberWithOptions(decimal: true))),
              ],
            ),
            const SizedBox(height: 8),
            if (_geoLoading)
              Row(children: [const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)), const SizedBox(width: 8), Text(l10n.analyzerLocationLoading)])
            else
              Text(_geoHint ?? l10n.analyzerSearchHint, style: TextStyle(fontSize: 12, color: FastTheme.textLight)),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () => _geoCode(_seciliSehir),
                icon: const Icon(Icons.search, size: 18),
                label: Text(l10n.analyzerSearchLocation),
              ),
            ),

            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _submit,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: FastTheme.primary,
                  foregroundColor: Colors.white,
                ),
                child: Text(l10n.analyzerStart),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _sectionBaslik(String title, IconData icon, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(8)),
            child: Icon(icon, color: color, size: 18),
          ),
          const SizedBox(width: 10),
          Text(title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: FastTheme.text)),
        ],
      ),
    );
  }

  Widget _textField(String label, TextEditingController ctrl, {IconData? icon, TextInputType? keyboardType}) {
    return TextField(
      controller: ctrl,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: icon != null ? Icon(icon, size: 20) : null,
      ),
    );
  }

  Widget _dateField(String label, TextEditingController ctrl, AppLocalizations l10n, {bool zorunlu = true}) {
    return TextField(
      controller: ctrl,
      readOnly: false,
      keyboardType: TextInputType.number,
      style: const TextStyle(fontSize: 14),
      decoration: InputDecoration(
        labelText: zorunlu ? label : '$label (${l10n.analyzerOptional})',
        hintText: '08.10.1986',
        prefixIcon: const Icon(Icons.calendar_today, size: 20),
        suffixIcon: IconButton(
          icon: const Icon(Icons.date_range, size: 20),
          onPressed: () => _pickDate(ctrl),
        ),
      ),
      onChanged: (_) => _applyDateMask(ctrl),
    );
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

  Widget _timeField(String label, TextEditingController ctrl) {
    return TextField(
      controller: ctrl,
      readOnly: false,
      keyboardType: TextInputType.number,
      style: const TextStyle(fontSize: 14),
      decoration: InputDecoration(
        labelText: label,
        hintText: '14:30',
        prefixIcon: const Icon(Icons.access_time, size: 20),
        suffixIcon: IconButton(
          icon: const Icon(Icons.schedule, size: 20),
          onPressed: () => _pickTime(ctrl),
        ),
      ),
      onChanged: (_) => _applyTimeMask(ctrl),
    );
  }

  Widget _dropdownField(String label, List<String> items, String value, ValueChanged<String?> onChanged, {Map<String, String>? labels}) {
    return DropdownButtonFormField<String>(
      value: items.contains(value) ? value : (items.isNotEmpty ? items.first : null),
      decoration: InputDecoration(labelText: label),
      items: items.map((e) => DropdownMenuItem(value: e, child: Text(labels?[e] ?? e))).toList(),
      onChanged: onChanged,
    );
  }
}
