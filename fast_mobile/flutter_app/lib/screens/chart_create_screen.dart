import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/country_labels.dart';
import '../config/theme.dart';
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
          '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    }
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
      setState(() => _geoHint = 'Konum bulunamadı, farklı bir şehir deneyin.');
    } finally {
      if (mounted) setState(() => _geoLoading = false);
    }
  }

  Future<void> _create() async {
    final cp = context.read<ChartProvider>();
    if (_date.text.trim().isEmpty) {
      setState(() => _formError = 'Doğum tarihi gerekli.');
      return;
    }
    if (_ulke.isEmpty || _sehir.isEmpty) {
      setState(() => _formError =
          'Ülke ve şehir seçmeden harita doğru hesaplanamaz.');
      return;
    }
    final lat = double.tryParse(_lat.text.replaceAll(',', '.'));
    final lon = double.tryParse(_lon.text.replaceAll(',', '.'));
    if (lat == null || lon == null) {
      setState(() => _formError = 'Konum koordinatları alınamadı.');
      return;
    }
    setState(() => _formError = null);
    cp.setHouseSystem(_hs);
    await cp.create(
      name: _name.text.trim(),
      date: _date.text.trim(),
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
    final cl = countryLabels(Localizations.localeOf(context).languageCode);

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text('Yeni Harita',
            style: TextStyle(
                color: FastTheme.accentGold,
                fontSize: 18,
                fontWeight: FontWeight.w700)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _label('İsim (opsiyonel)'),
          TextField(
            controller: _name,
            style: TextStyle(color: FastTheme.text),
            decoration: const InputDecoration(hintText: 'Örn. Ali'),
          ),
          const SizedBox(height: 14),
          _label('Doğum Tarihi'),
          TextField(
            controller: _date,
            readOnly: true,
            onTap: _pickDate,
            style: TextStyle(color: FastTheme.text),
            decoration: const InputDecoration(
              hintText: 'YYYY-MM-DD',
              suffixIcon: Icon(Icons.calendar_today, size: 18),
            ),
          ),
          const SizedBox(height: 14),
          _label('Doğum Saati'),
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
          _label('Doğum Yeri'),
          if (_dbLoading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: LinearProgressIndicator(minHeight: 2),
            )
          else ...[
            DropdownButtonFormField<String>(
              key: ValueKey('ulke-$_ulke'),
              initialValue: _ulke.isEmpty ? null : _ulke,
              isExpanded: true,
              dropdownColor: FastTheme.cardBg,
              style: TextStyle(color: FastTheme.text),
              decoration: const InputDecoration(labelText: 'Ülke'),
              items: _ulkeler
                  .map((u) => DropdownMenuItem(
                        value: u,
                        child: Text(cl[u] ?? u,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(color: FastTheme.text)),
                      ))
                  .toList(),
              onChanged: (v) {
                setState(() {
                  _ulke = v ?? '';
                  _sehir = '';
                  _geoHint = null;
                  _lat.clear();
                  _lon.clear();
                });
              },
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              key: ValueKey('sehir-$_ulke-$_sehir'),
              initialValue: _sehir.isEmpty ? null : _sehir,
              isExpanded: true,
              dropdownColor: FastTheme.cardBg,
              style: TextStyle(color: FastTheme.text),
              decoration: const InputDecoration(labelText: 'Şehir'),
              items: _sehirler
                  .map((s) => DropdownMenuItem(
                        value: s,
                        child: Text(s,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(color: FastTheme.text)),
                      ))
                  .toList(),
              onChanged: _ulke.isEmpty
                  ? null
                  : (v) {
                      setState(() => _sehir = v ?? '');
                      _geocode();
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
              Text('Konum alınıyor...',
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
                  decoration: const InputDecoration(labelText: 'Enlem'),
                  keyboardType: const TextInputType.numberWithOptions(
                      decimal: true, signed: true),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _lon,
                  style: TextStyle(color: FastTheme.text),
                  decoration: const InputDecoration(labelText: 'Boylam'),
                  keyboardType: const TextInputType.numberWithOptions(
                      decimal: true, signed: true),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _label('Ev Sistemi'),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: chartHouseSystemNames.entries.map((e) {
              final sel = _hs == e.key;
              return ChoiceChip(
                label: Text(e.value),
                selected: sel,
                onSelected: (_) {
                  setState(() => _hs = e.key);
                  cp.setHouseSystem(e.key);
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
            child: Text(cp.loading ? 'Hesaplanıyor...' : 'Haritayı Oluştur',
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
