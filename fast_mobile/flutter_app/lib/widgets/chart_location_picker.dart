import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../config/country_labels.dart';

/// A country-qualified city lookup; stale responses never replace a newer city.
class ChartLocationPicker extends StatefulWidget {
  final void Function(String place, double lat, double lon) onSelected;
  final VoidCallback onPending;
  const ChartLocationPicker({
    super.key,
    required this.onSelected,
    required this.onPending,
  });
  @override
  State<ChartLocationPicker> createState() => _ChartLocationPickerState();
}

class _ChartLocationPickerState extends State<ChartLocationPicker> {
  final _api = ApiService();
  Map<String, dynamic>? _db;
  String? _country;
  String? _city;
  String? _error;
  bool _busy = false;
  int _request = 0;
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _error = null;
      _db = null;
    });
    try {
      final db = await _api.getUlkelerRaw();
      if (mounted) setState(() => _db = db);
    } catch (_) {
      if (mounted) setState(() => _error = 'Şehir listesi yüklenemedi.');
    }
  }

  Future<void> _resolve(String city) async {
    final request = ++_request;
    widget.onPending();
    setState(() {
      _city = city;
      _busy = true;
      _error = null;
    });
    try {
      final geo = await _api.geocode('$city, $_country');
      if (!mounted || request != _request) return;
      widget.onSelected(
        '$city, $_country',
        (geo['lat'] as num).toDouble(),
        (geo['lon'] as num).toDouble(),
      );
    } catch (_) {
      if (mounted && request == _request) {
        setState(() => _error = 'Şehrin konumu bulunamadı. Tekrar seçin.');
      }
    } finally {
      if (mounted && request == _request) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_db == null) {
      return _error == null
          ? const LinearProgressIndicator()
          : TextButton.icon(
              onPressed: _load,
              icon: const Icon(Icons.refresh),
              label: Text(_error!),
            );
    }
    final countries = (_db!['ulkeler'] as List).cast<String>();
    final cities =
        ((_db!['sehirler'] as Map)[_country] as List?)?.cast<String>() ??
        <String>[];
    final labels = countryLabels(Localizations.localeOf(context).languageCode);
    return Column(
      children: [
        DropdownButtonFormField<String>(
          initialValue: _country,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: 'Dönüşü yaşayacağın ülke',
          ),
          items: countries
              .map(
                (c) => DropdownMenuItem(value: c, child: Text(labels[c] ?? c)),
              )
              .toList(),
          onChanged: (v) {
            ++_request;
            widget.onPending();
            setState(() {
              _country = v;
              _city = null;
              _busy = false;
              _error = null;
            });
          },
        ),
        const SizedBox(height: 10),
        DropdownButtonFormField<String>(
          key: ValueKey(_country),
          initialValue: _city,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: 'Dönüşü yaşayacağın şehir',
          ),
          items: cities
              .map((c) => DropdownMenuItem(value: c, child: Text(c)))
              .toList(),
          onChanged: (v) {
            if (v != null) _resolve(v);
          },
        ),
        if (_busy) const LinearProgressIndicator(),
        if (_error != null)
          Text(_error!, style: const TextStyle(color: Colors.redAccent)),
      ],
    );
  }
}
