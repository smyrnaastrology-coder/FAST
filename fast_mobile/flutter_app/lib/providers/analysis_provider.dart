import 'package:flutter/foundation.dart';
import '../models/analysis_request.dart';
import '../services/api_service.dart';

enum AnalysisStatus { idle, loading, success, error }

class AnalysisProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  AnalysisStatus _status = AnalysisStatus.idle;
  Map<String, dynamic>? _result;
  Map<String, dynamic>? _detayliResult;
  Map<String, dynamic>? _simData;
  Map<String, dynamic>? _astroData;
  String? _acgMapUrl;
  String? _error;
  bool _simLoading = false;
  bool _paid = false;

  AnalysisStatus get status => _status;
  Map<String, dynamic>? get result => _result;
  Map<String, dynamic>? get detayliResult => _detayliResult;
  Map<String, dynamic>? get simData => _simData;
  Map<String, dynamic>? get astroData => _astroData;
  String? get acgMapUrl => _acgMapUrl;
  String? get error => _error;
  bool get simLoading => _simLoading;
  bool get paid => _paid;
  String? get sessionId => _result?['session_id'] as String?;

  Future<void> analizYap(AnalysisRequest req) async {
    _status = AnalysisStatus.loading;
    _error = null;
    _result = null;
    _detayliResult = null;
    _simData = null;
    _astroData = null;
    _acgMapUrl = null;
    notifyListeners();

    try {
      _result = await _api.analizYap(req);
      _status = AnalysisStatus.success;
      notifyListeners();

      // Temel uç artık tüm detayı (karmik_ev, progression, hava_durumu,
      // zaman_makinesi, yildiz_muhurleri, arap, asteroitler, astrokartografi)
      // tek yanıtta döndürüyor. Ayrı ağır /detayli çağrısı gerekmez — kuyruğu önler.
      if (req.mod == 'es_sevgili' || req.mod == 'ebeveyn_cocuk') {
        _detayliResult = _result;
        notifyListeners();
      }

      // Load simulation if applicable
      if (req.mod == 'es_sevgili' && sessionId != null) {
        _loadSim(req);
      } else if (req.mod == 'bireysel_natal' && sessionId != null) {
        _loadNatalSim(req);
      }
    } catch (e) {
      _error = e.toString();
      _status = AnalysisStatus.error;
      notifyListeners();
    }
  }

  Future<void> _loadSim(AnalysisRequest req) async {
    _simLoading = true;
    notifyListeners();
    try {
      _simData = await _api.simulasyonRadar(req);
    } catch (_) {}
    _simLoading = false;
    notifyListeners();
  }

  Future<void> _loadNatalSim(AnalysisRequest req) async {
    _simLoading = true;
    notifyListeners();
    try {
      _simData = await _api.simulasyonNatalRadar(req);
    } catch (_) {}
    _simLoading = false;
    notifyListeners();
  }

  Future<void> loadAlternatif(Map<String, dynamic> data) async {
    _status = AnalysisStatus.loading;
    notifyListeners();
    try {
      final alt = await _api.simulasyonAlternatif(data);
      if (_result != null) {
        _result = Map<String, dynamic>.from(_result!)
          ..['uyum_orani'] = alt['uyum_orani']
          ..['tork'] = alt['tork']
          ..['fraktal'] = alt['fraktal']
          ..['session_id'] = alt['session_id']
          ..['sim_sehir'] = data['sehir'];
      }
      if (_detayliResult != null) {
        _detayliResult = Map<String, dynamic>.from(_detayliResult!)
          ..['uyum_orani'] = alt['uyum_orani']
          ..['tork'] = alt['tork']
          ..['fraktal'] = alt['fraktal']
          ..['session_id'] = alt['session_id']
          ..['sim_sehir'] = data['sehir'];
      }
      _status = AnalysisStatus.success;
    } catch (e) {
      _error = e.toString();
      _status = AnalysisStatus.error;
    }
    notifyListeners();
  }

  Future<void> loadAstroScores(String sehir, String ulke, [String tarih = '', String saat = '']) async {
    try {
      final g = await _api.geocode('$sehir, $ulke');
      _astroData = await _api.astroKartografi({
        'session_id': sessionId,
        'sehir': sehir,
        'enlem': g['lat'],
        'boylam': g['lon'],
        'tarih': tarih,
        'saat': saat,
      });
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<String?> loadAcgMap() async {
    final sid = sessionId;
    if (sid == null) return null;
    try {
      _acgMapUrl = _api.getAcgHaritaUrl(sid);
      notifyListeners();
      return _acgMapUrl;
    } catch (_) {
      return null;
    }
  }

  void setPaid(bool v) {
    _paid = v;
    notifyListeners();
  }

  void reset() {
    _status = AnalysisStatus.idle;
    _result = null;
    _detayliResult = null;
    _simData = null;
    _astroData = null;
    _acgMapUrl = null;
    _error = null;
    _simLoading = false;
    _paid = false;
    notifyListeners();
  }
}
