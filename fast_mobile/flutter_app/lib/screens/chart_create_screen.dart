import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../config/country_labels.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/chart_labels.dart';
import '../providers/chart_provider.dart';
import '../services/api_service.dart';
import 'chart_detail_screen.dart';

class ChartCreateScreen extends StatefulWidget {
  const ChartCreateScreen({super.key});

  @override
  State<ChartCreateScreen> createState() => _ChartCreateScreenState();
}

class _ChartCreateScreenState extends State<ChartCreateScreen> {
  final _api = ApiService();
  final _name = TextEditingController();
  final _date = TextEditingController();
  final _time = TextEditingController(text: '12:00');
  final _lat = TextEditingController();
  final _lon = TextEditingController();
  TextEditingController? _countryCtrl;
  TextEditingController? _cityCtrl;

  String _hs = 'P';
  String _ulke = '';
  String _sehir = '';
  String? _geoHint;
  String? _formError;
  bool _dbLoading = true;
  bool _geoLoading = false;
  Map<String, dynamic>? _lokasyonDB;

  List<String> get _ulkeler =>
      (_lokasyonDB?['ulkeler'] as List?)?.cast<String>() ?? const [];
  List<String> get _sehirler =>
      (_lokasyonDB?['sehirler']?[_ulke] as List?)?.cast<String>() ?? const [];

  @override
  void initState() {
    super.initState();
    _loadDB();
  }

  @override
  void dispose() {
    _name.dispose();
    _date.dispose();
    _time.dispose();
    _lat.dispose();
    _lon.dispose();
    super.dispose();
  }

  Future<void> _loadDB() async {
    try {
      final d = await _api.getUlkelerRaw();
      _lokasyonDB = d.cast<String, dynamic>();
    } catch (_) {}
    if (mounted) setState(() => _dbLoading = false);
  }

  Future<void> _pickDate() async {
    final d = await showDatePicker(
      context: context,
      initialDate: DateTime(1990, 1, 1),
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
    );
    if (d != null) {
      _date.text =
          '${d.day.toString().padLeft(2, '0')}.${d.month.toString().padLeft(2, '0')}.${d.year.toString().padLeft(4, '0')}';
    }
  }

  String? _toIsoDate(String input) {
    final t = input.trim();
    final m = RegExp(r'^(\d{2})\.(\d{2})\.(\d{4})$').firstMatch(t);
    if (m != null) {
      return '${m.group(3)}-${m.group(2)}-${m.group(1)}';
    }
    if (RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(t)) return t;
    return null;
  }

  Future<void> _pickTime() async {
    final t = await showTimePicker(
        context: context, initialTime: const TimeOfDay(hour: 12, minute: 0));
    if (t != null) {
      _time.text =
          '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
    }
  }

  Future<void> _geocode() async {
    if (_sehir.isEmpty) return;
    setState(() => _geoLoading = true);
    try {
      final r = await _api.geocode(_sehir);
      if (!mounted) return;
      setState(() {
        _lat.text = (r['lat'] as num).toStringAsFixed(4);
        _lon.text = (r['lon'] as num).toStringAsFixed(4);
        _geoHint =
            '${r['city'] ?? _sehir}, ${r['country'] ?? _ulke} • ${_lat.text}, ${_lon.text}';
      });
    } catch (_) {
      if (!mounted) return;
      setState(
        () => _geoHint = AppLocalizations.of(context).chartErrorLocationNotFound,
      );
    } finally {
      if (mounted) setState(() => _geoLoading = false);
    }
  }

  Future<void> _create() async {
    final cp = context.read<ChartProvider>();
    final l10n = AppLocalizations.of(context);
    final cl = countryLabels(Localizations.localeOf(context).languageCode);
    final isoDate = _toIsoDate(_date.text);
    if (isoDate == null) {
      setState(() => _formError = l10n.chartErrorDateRequired);
      return;
    }
    if (_ulke.isEmpty && _countryCtrl != null) {
      final v = _countryCtrl!.text.trim().toLowerCase();
      final match = _ulkeler.firstWhere(
        (u) => (cl[u] ?? u).toLowerCase() == v || u.toLowerCase() == v,
        orElse: () => '',
      );
      if (match.isNotEmpty) _ulke = match;
    }
    if (_sehir.isEmpty && _cityCtrl != null) {
      final v = _cityCtrl!.text.trim();
      if (_sehirler.contains(v)) _sehir = v;
    }
    if (_ulke.isEmpty || _sehir.isEmpty) {
      setState(() => _formError = l10n.chartErrorCountryCity);
      return;
    }
    final lat = double.tryParse(_lat.text.replaceAll(',', '.'));
    final lon = double.tryParse(_lon.text.replaceAll(',', '.'));
    if (lat == null || lon == null) {
      setState(() => _formError = l10n.chartErrorCoordinates);
      return;
    }
    setState(() => _formError = null);
    cp.setHouseSystem(_hs);
    await cp.create(
      name: _name.text.trim(),
      date: isoDate,
      time: _time.text.trim(),
      lat: lat,
      lng: lon,
      place: _sehir,
    );
    if (mounted && cp.current != null) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const ChartDetailScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final cp = context.watch<ChartProvider>();
    final l10n = AppLocalizations.of(context);
    final cl = countryLabels(Localizations.localeOf(context).languageCode);

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text(l10n.chartCreateTitle,
            style: TextStyle(
                color: FastTheme.accentGold,
                fontSize: 18,
                fontWeight: FontWeight.w700)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _label(l10n.chartLabelNameOptional),
          TextField(
            controller: _name,
            style: TextStyle(color: FastTheme.text),
            decoration: InputDecoration(hintText: l10n.chartNameHint),
          ),
          const SizedBox(height: 14),
          _label(l10n.chartLabelBirthDate),
          TextField(
            controller: _date,
            keyboardType: TextInputType.number,
            inputFormatters: [_DateDotFormatter()],
            style: TextStyle(color: FastTheme.text),
            decoration: InputDecoration(
              hintText: 'DD.MM.YYYY',
              suffixIcon: IconButton(
                icon: const Icon(Icons.calendar_today, size: 18),
                onPressed: _pickDate,
              ),
            ),
          ),
          const SizedBox(height: 14),
          _label(l10n.chartLabelBirthTime),
          TextField(
            controller: _time,
            readOnly: true,
            onTap: _pickTime,
            style: TextStyle(color: FastTheme.text),
            decoration: const InputDecoration(
              hintText: 'HH:MM',
              suffixIcon: Icon(Icons.schedule, size: 18),
            ),
          ),
          const SizedBox(height: 18),
          _label(l10n.chartLabelBirthPlace),
          if (_dbLoading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: LinearProgressIndicator(minHeight: 2),
            )
          else ...[
            Autocomplete<String>(
              key: ValueKey('ulke-$_ulke'),
              optionsBuilder: (tev) {
                final q = tev.text.trim().toLowerCase();
                if (q.isEmpty) return _ulkeler;
                return _ulkeler.where((u) {
                  final label = (cl[u] ?? u).toLowerCase();
                  return label.contains(q) || u.toLowerCase().contains(q);
                });
              },
              displayStringForOption: (o) => cl[o] ?? o,
              onSelected: (o) {
                setState(() {
                  _ulke = o;
                  _sehir = '';
                  _geoHint = null;
                  _lat.clear();
                  _lon.clear();
                });
                if (_cityCtrl != null) _cityCtrl!.clear();
              },
              fieldViewBuilder: (context, controller, focusNode, onSubmitted) {
                _countryCtrl = controller;
                return TextField(
                  controller: controller,
                  focusNode: focusNode,
                  style: TextStyle(color: FastTheme.text),
                  decoration: InputDecoration(labelText: l10n.chartLabelCountry),
                  onChanged: (_) {
                    final v = controller.text.trim().toLowerCase();
                    final match = _ulkeler.firstWhere(
                      (u) =>
                          (cl[u] ?? u).toLowerCase() == v ||
                          u.toLowerCase() == v,
                      orElse: () => '',
                    );
                    if (match.isNotEmpty && _ulke != match) {
                      setState(() {
                        _ulke = match;
                        _sehir = '';
                        _geoHint = null;
                        _lat.clear();
                        _lon.clear();
                      });
                    }
                  },
                );
              },
            ),
            const SizedBox(height: 12),
            Autocomplete<String>(
              key: ValueKey('sehir-$_ulke'),
              optionsBuilder: (tev) {
                final q = tev.text.trim().toLowerCase();
                if (q.isEmpty) return _sehirler;
                return _sehirler.where((s) => s.toLowerCase().contains(q));
              },
              displayStringForOption: (o) => o,
              onSelected: (o) {
                setState(() => _sehir = o);
                _geocode();
              },
              fieldViewBuilder: (context, controller, focusNode, onSubmitted) {
                _cityCtrl = controller;
                return TextField(
                  controller: controller,
                  focusNode: focusNode,
                  style: TextStyle(color: FastTheme.text),
                  decoration: InputDecoration(labelText: l10n.chartLabelCity),
                  onChanged: (v) {
                    if (_sehirler.contains(v) && _sehir != v) {
                      setState(() => _sehir = v);
                    }
                  },
                  onEditingComplete: () {
                    if (_sehir.isNotEmpty) _geocode();
                  },
                );
              },
            ),
          ],
          const SizedBox(height: 10),
          if (_geoLoading)
            Row(children: [
              const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(strokeWidth: 2)),
              const SizedBox(width: 8),
              Text(l10n.chartReturnLocating,
                  style: TextStyle(color: FastTheme.textMuted)),
            ])
          else if (_geoHint != null)
            Text(_geoHint!, style: TextStyle(color: FastTheme.textMuted)),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _lat,
                  style: TextStyle(color: FastTheme.text),
                  decoration: InputDecoration(
                      labelText: l10n.chartLabelLatitude),
                  keyboardType: const TextInputType.numberWithOptions(
                      decimal: true, signed: true),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _lon,
                  style: TextStyle(color: FastTheme.text),
                  decoration: InputDecoration(
                      labelText: l10n.chartLabelLongitude),
                  keyboardType: const TextInputType.numberWithOptions(
                      decimal: true, signed: true),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _label(l10n.chartLabelHouseSystem),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: chartHouseSystemCodes.map((code) {
              final sel = _hs == code;
              return ChoiceChip(
                label: Text(chartHouseSystemLabel(l10n, code)),
                selected: sel,
                onSelected: (_) {
                  setState(() => _hs = code);
                  cp.setHouseSystem(code);
                },
                selectedColor: FastTheme.accentGold,
                labelStyle: TextStyle(
                    color: sel ? FastTheme.bg : FastTheme.text,
                    fontWeight: FontWeight.w600),
              );
            }).toList(),
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: cp.loading ? null : _create,
            style: FilledButton.styleFrom(
              backgroundColor: FastTheme.accentGold,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            child: Text(
                cp.loading ? l10n.chartCalculating : l10n.chartCreateButton,
                style: TextStyle(
                    color: FastTheme.bg,
                    fontWeight: FontWeight.w700,
                    fontSize: 15)),
          ),
          if (_formError != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Text(_formError!,
                  style: const TextStyle(color: Colors.redAccent)),
            ),
          if (cp.error != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Text(cp.error!,
                  style: const TextStyle(color: Colors.redAccent)),
            ),
        ],
      ),
    );
  }

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(text,
            style: TextStyle(
                color: FastTheme.textMuted,
                fontSize: 12,
                fontWeight: FontWeight.w600)),
      );
}

class _DateDotFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    final digits = newValue.text.replaceAll(RegExp(r'[^0-9]'), '');
    final buf = StringBuffer();
    for (var i = 0; i < digits.length && i < 8; i++) {
      if (i == 2 || i == 4) buf.write('.');
      buf.write(digits[i]);
    }
    final text = buf.toString();
    return TextEditingValue(
      text: text,
      selection: TextSelection.collapsed(offset: text.length),
    );
  }
}
