import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/chart_data.dart';
import '../services/chart_service.dart';

class BiwheelState {
  final Map<String, dynamic> data;
  final DateTime when;
  BiwheelState({required this.data, required this.when});
}

class ReturnState {
  final Map<String, dynamic> data;
  final String type; // solar | lunar
  final int year;
  final int? month;
  ReturnState({required this.data, required this.type, required this.year, this.month});
}

class SolarArcState {
  final Map<String, dynamic> data;
  final String targetDate;
  SolarArcState({required this.data, required this.targetDate});
}

class ChartProvider extends ChangeNotifier {
  final ChartService _service = ChartService();

  List<ChartData> _saved = [];
  ChartData? _current;
  String _houseSystem = 'P';
  bool _loading = false;
  String? _error;
  BiwheelState? _biwheel;
  bool _biLoading = false;
  String? _biError;
  Timer? _biTimer;
  final Map<String, Map<String, dynamic>> _biCache = {};
  int _biSeq = 0;

  ReturnState? _ret;
  bool _retLoading = false;
  String? _retError;

  SolarArcState? _arc;
  bool _arcLoading = false;
  String? _arcError;

  double? _returnLat;
  double? _returnLon;
  String _returnLocMode = 'natal'; // natal | device | manual

  List<ChartData> get saved => _saved;
  ChartData? get current => _current;
  String get houseSystem => _houseSystem;
  bool get loading => _loading;
  String? get error => _error;
  BiwheelState? get biwheel => _biwheel;
  bool get biLoading => _biLoading;
  String? get biError => _biError;
  ReturnState? get ret => _ret;
  bool get retLoading => _retLoading;
  String? get retError => _retError;
  SolarArcState? get arc => _arc;
  bool get arcLoading => _arcLoading;
  String? get arcError => _arcError;
  double? get returnLat => _returnLat;
  double? get returnLon => _returnLon;
  String get returnLocMode => _returnLocMode;

  @override
  void dispose() {
    _biTimer?.cancel();
    super.dispose();
  }

  Future<void> loadSaved() async {
    final local = await _service.loadLocal();
    final cloud = await _service.cloudList();
    final merged = <ChartData>[...cloud, ...local];
    final seen = <String>{};
    _saved = merged.where((e) {
      final key = '${e.meta.name}|${e.meta.date}|${e.meta.time}';
      if (seen.contains(key)) return false;
      seen.add(key);
      return true;
    }).toList();
    notifyListeners();
  }

  Future<void> delete(ChartData data) async {
    final remaining = _saved.where(
      (e) =>
          !(e.meta.name == data.meta.name &&
              e.meta.date == data.meta.date &&
              e.meta.time == data.meta.time),
    ).toList();
    _saved = remaining;
    notifyListeners();
    await _service.saveLocal(data);
    await _service.cloudDelete(data);
  }

  void setHouseSystem(String hs) {
    _houseSystem = hs;
    notifyListeners();
  }

  void open(ChartData data) {
    _current = data;
    _houseSystem = data.houseSystem;
    _biCache.clear();
    _biwheel = null;
    _biError = null;
    _ret = null;
    _retError = null;
    _returnLat = data.meta.lat;
    _returnLon = data.meta.lng;
    _returnLocMode = 'natal';
    notifyListeners();
  }

  Future<void> create({
    required String name,
    required String date,
    required String time,
    required double lat,
    required double lng,
    String? place,
    double? tz,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      final data = await _service.natal(
        tarih: date,
        saat: time,
        lat: lat,
        lon: lng,
        houseSystem: _houseSystem,
        isim: name,
        tz: tz,
        place: place,
      );
      _current = data;
      await _service.saveLocal(data);
      await loadSaved();
      unawaited(_service.cloudSave(data));
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> loadBiwheel({required DateTime when, double? lat, double? lon}) async {
    if (_current == null) return;
    final d = '${when.year.toString().padLeft(4, '0')}-${when.month.toString().padLeft(2, '0')}-${when.day.toString().padLeft(2, '0')}';
    final t = '${when.hour.toString().padLeft(2, '0')}:${when.minute.toString().padLeft(2, '0')}';
    final key = '${_current!.meta.date}|${_current!.meta.time}|'
        '${lat ?? _current!.meta.lat}|${lon ?? _current!.meta.lng}|$d|$t';

    final cached = _biCache[key];
    if (cached != null) {
      _biwheel = BiwheelState(data: cached, when: when);
      _biError = null;
      _biLoading = false;
      notifyListeners();
      return;
    }

    final seq = ++_biSeq;
    _biLoading = true;
    _biError = null;
    notifyListeners();
    try {
      final res = await _service.biwheel(
        natal: _current!,
        hedefTarih: d,
        hedefSaat: t,
        lat: lat,
        lon: lon,
      );
      if (seq != _biSeq) return;
      if (_biCache.length > 160) _biCache.clear();
      _biCache[key] = res;
      _biwheel = BiwheelState(data: res, when: when);
    } catch (e) {
      if (seq != _biSeq) return;
      _biError = e.toString();
    } finally {
      if (seq == _biSeq) {
        _biLoading = false;
        notifyListeners();
      }
    }
  }

  void setReturnLocation({required String mode, double? lat, double? lon}) {
    _returnLocMode = mode;
    if (mode == 'natal' && _current != null) {
      _returnLat = _current!.meta.lat;
      _returnLon = _current!.meta.lng;
    } else {
      _returnLat = lat;
      _returnLon = lon;
    }
    notifyListeners();
  }

  Future<void> loadSolarReturn(int year) async {
    if (_current == null) return;
    _retLoading = true;
    _retError = null;
    notifyListeners();
    try {
      final res = await _service.solarReturn(
        natal: _current!,
        year: year,
        lat: _returnLat,
        lon: _returnLon,
      );
      _ret = ReturnState(data: res, type: 'solar', year: year);
    } catch (e) {
      _retError = e.toString();
    } finally {
      _retLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadLunarReturn(int year, int month) async {
    if (_current == null) return;
    _retLoading = true;
    _retError = null;
    notifyListeners();
    try {
      final res = await _service.lunarReturn(
        natal: _current!,
        year: year,
        month: month,
        lat: _returnLat,
        lon: _returnLon,
      );
      _ret = ReturnState(data: res, type: 'lunar', year: year, month: month);
    } catch (e) {
      _retError = e.toString();
    } finally {
      _retLoading = false;
      notifyListeners();
    }
  }

  void loadBiwheelDebounced({required DateTime when, double? lat, double? lon, int ms = 200}) {
    _biTimer?.cancel();
    _biTimer = Timer(Duration(milliseconds: ms), () => loadBiwheel(when: when, lat: lat, lon: lon));
  }

  Future<void> loadSolarArc(String hedefTarih) async {
    if (_current == null) return;
    _arcLoading = true;
    _arcError = null;
    notifyListeners();
    try {
      final res = await _service.solarArc(natal: _current!, hedefTarih: hedefTarih);
      _arc = SolarArcState(data: res, targetDate: hedefTarih);
    } catch (e) {
      _arcError = e.toString();
    } finally {
      _arcLoading = false;
      notifyListeners();
    }
  }
}

