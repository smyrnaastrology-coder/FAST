import 'dart:async';

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

  ReturnState? _ret;
  bool _retLoading = false;
  String? _retError;

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
  double? get returnLat => _returnLat;
  double? get returnLon => _returnLon;
  String get returnLocMode => _returnLocMode;

  @override
  void dispose() {
    _biTimer?.cancel();
    super.dispose();
  }

  Future<void> loadSaved() async {
    _saved = await _service.loadLocal();
    notifyListeners();
  }

  void setHouseSystem(String hs) {
    _houseSystem = hs;
    notifyListeners();
  }

  void open(ChartData data) {
    _current = data;
    _houseSystem = data.houseSystem;
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
      );
      _current = data;
      await _service.saveLocal(data);
      await loadSaved();
    } catch (e) {
      _error = e.toString();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> loadBiwheel({required DateTime when, double? lat, double? lon}) async {
    if (_current == null) return;
    _biLoading = true;
    _biError = null;
    notifyListeners();
    try {
      final d = '${when.year.toString().padLeft(4, '0')}-${when.month.toString().padLeft(2, '0')}-${when.day.toString().padLeft(2, '0')}';
      final t = '${when.hour.toString().padLeft(2, '0')}:${when.minute.toString().padLeft(2, '0')}';
      final res = await _service.biwheel(
        natal: _current!,
        hedefTarih: d,
        hedefSaat: t,
        lat: lat,
        lon: lon,
      );
      _biwheel = BiwheelState(data: res, when: when);
    } catch (e) {
      _biError = e.toString();
    } finally {
      _biLoading = false;
      notifyListeners();
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
}

