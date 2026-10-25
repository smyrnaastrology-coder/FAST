import 'package:flutter_test/flutter_test.dart';
import 'dart:async';
import 'package:fast_app/models/chart_data.dart';
import 'package:fast_app/providers/chart_provider.dart';
import 'package:fast_app/services/chart_service.dart';

class MemoryCharts extends ChartService {
  final rows = <ChartData>[];
  int cloudWrites = 0;
  final returnRequests =
      <(double?, double?, Completer<Map<String, dynamic>>)>[];
  @override
  Future<Map<String, dynamic>> solarReturn({
    required ChartData natal,
    required int year,
    double? lat,
    double? lon,
    double? tz,
  }) {
    final completer = Completer<Map<String, dynamic>>();
    returnRequests.add((lat, lon, completer));
    return completer.future;
  }

  @override
  Future<ChartData> natal({
    required String tarih,
    required String saat,
    required double lat,
    required double lon,
    String houseSystem = 'P',
    String? isim,
    double? tz,
    String? place,
  }) async => ChartData.fromJson({
    'meta': {
      'isim': isim,
      'tarih': tarih,
      'saat': saat,
      'lat': lat,
      'lon': lon,
      'tz': 2.0,
    },
  });
  @override
  Future<void> saveLocal(ChartData data) async {
    rows.add(data);
  }

  @override
  Future<void> deleteLocal(ChartData data) async {
    rows.remove(data);
  }

  @override
  Future<List<ChartData>> loadLocal() async => [...rows];
  @override
  Future<List<ChartData>> cloudList() async => [];
  @override
  Future<void> cloudSave(ChartData data) async {
    cloudWrites++;
  }

  @override
  Future<void> cloudDelete(ChartData data) async {}
}

void main() {
  test(
    'Dönüş konumu doğrulanmadan hesaplanmaz; konum değişirse eski yanıt atılır',
    () async {
      final service = MemoryCharts();
      final provider = ChartProvider(service: service);
      await provider.create(
        name: 'Test',
        date: '1986-10-08',
        time: '23:14',
        lat: 40.3167,
        lng: 36.55,
      );
      await provider.loadSolarReturn(2026);
      expect(service.returnRequests, isEmpty);
      provider.setReturnLocation(
        mode: 'city',
        place: 'New York, ABD',
        lat: 40.7128,
        lon: -74.006,
      );
      final loading = provider.loadSolarReturn(2026);
      expect(service.returnRequests.single.$1, 40.7128);
      expect(service.returnRequests.single.$2, -74.006);
      provider.invalidateReturnLocation();
      service.returnRequests.single.$3.complete({'ok': true});
      await loading;
      expect(provider.ret, isNull);
      expect(provider.returnLocationConfirmed, isFalse);
      provider.setReturnLocation(
        mode: 'city',
        place: 'Tokat, Türkiye',
        lat: 40.3167,
        lon: 36.55,
      );
      final latest = provider.loadSolarReturn(2026);
      service.returnRequests.last.$3.complete({'ok': true});
      await latest;
      expect(provider.ret, isNotNull);
      expect(provider.returnPlace, 'Tokat, Türkiye');
      provider.dispose();
    },
  );
  test('Hesaplama kaydetmez; Kaydet ekler, Sil yerel kaydı kaldırır', () async {
    final service = MemoryCharts();
    final provider = ChartProvider(service: service);
    await provider.create(
      name: 'Test',
      date: '1986-10-08',
      time: '23:14',
      lat: 40.3167,
      lng: 36.55,
    );
    expect(provider.current, isNotNull);
    expect(service.rows, isEmpty);
    expect(service.cloudWrites, 0);
    await provider.saveCurrent();
    expect(provider.saved, hasLength(1));
    expect(service.cloudWrites, 1);
    await provider.delete(provider.current!);
    await provider.loadSaved();
    expect(provider.saved, isEmpty);
    expect(service.rows, isEmpty);
    provider.dispose();
  });
}
