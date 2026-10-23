import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../models/chart_data.dart';
import '../providers/chart_provider.dart';
import '../widgets/chart_wheel.dart';
import '../widgets/time_machine_bar.dart';

const _signNames = [
  'Koç',
  'Boğa',
  'İkizler',
  'Yengeç',
  'Aslan',
  'Başak',
  'Terazi',
  'Akrep',
  'Yay',
  'Oğlak',
  'Kova',
  'Balık',
];

class ChartDetailScreen extends StatefulWidget {
  const ChartDetailScreen({super.key});

  @override
  State<ChartDetailScreen> createState() => _ChartDetailScreenState();
}

class _ChartDetailScreenState extends State<ChartDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tab;
  DateTime _now = DateTime.now();
  final _latCtrl = TextEditingController();
  final _lonCtrl = TextEditingController();
  bool _locating = false;

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tab.dispose();
    _latCtrl.dispose();
    _lonCtrl.dispose();
    super.dispose();
  }

  String _sign(int i) {
    if (i < 0 || i > 11) return '-';
    return _signNames[i];
  }

  Future<void> _useDeviceLocation() async {
    final cp = context.read<ChartProvider>();
    setState(() => _locating = true);
    try {
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied ||
          perm == LocationPermission.deniedForever) {
        return;
      }
      final pos = await Geolocator.getCurrentPosition();
      if (!mounted) return;
      _latCtrl.text = pos.latitude.toStringAsFixed(5);
      _lonCtrl.text = pos.longitude.toStringAsFixed(5);
      cp.setReturnLocation(
        mode: 'device',
        lat: pos.latitude,
        lon: pos.longitude,
      );
    } catch (_) {
      // varsayılan konumda kal
    } finally {
      if (mounted) setState(() => _locating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cp = context.watch<ChartProvider>();
    final c = cp.current;
    if (c == null) {
      return Scaffold(
        backgroundColor: FastTheme.bg,
        appBar: AppBar(backgroundColor: FastTheme.bg),
        body: Center(
          child: Text(
            'Harita bulunamadı',
            style: TextStyle(color: FastTheme.textMuted),
          ),
        ),
      );
    }

    final name =
        c.meta.name?.isNotEmpty == true ? c.meta.name! : 'Natal Haritası';

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text(
          name,
          style: TextStyle(
            color: FastTheme.accentGold,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
        bottom: TabBar(
          controller: _tab,
          indicatorColor: FastTheme.accentGold,
          labelColor: FastTheme.accentGold,
          unselectedLabelColor: FastTheme.textMuted,
          tabs: const [
            Tab(text: 'Natal'),
            Tab(text: 'Zaman Makinesi'),
            Tab(text: 'Dönüşler'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tab,
        children: [
          _natalTab(c),
          _timeMachineTab(cp, c),
          _returnsTab(cp, c),
        ],
      ),
    );
  }

  Widget _natalTab(ChartData c) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
      children: [
        Center(child: ChartWheel(data: c, size: 320)),
        const SizedBox(height: 16),
        _section('Bilgiler', [
          _row('Tarih / Saat', '${c.meta.date} • ${c.meta.time}'),
          _row('Ev Sistemi', c.houseSystem),
          if (c.meta.place.isNotEmpty) _row('Yer', c.meta.place),
        ]),
        const SizedBox(height: 14),
        _section('Gezegenler', [
          for (final p in c.planets)
            _row(
              p.name,
              '${_sign(p.sign)} ${p.degree.toStringAsFixed(2)}° ${p.retrograde ? 'R' : ''} • Ev ${p.house}',
            ),
        ]),
        const SizedBox(height: 14),
        _section('Evler', [
          for (final h in c.houses)
            _row('Ev ${h.number}', '${_sign(h.sign)} ${h.degree.toStringAsFixed(2)}°'),
        ]),
        if (c.aspects.isNotEmpty) ...[
          const SizedBox(height: 14),
          _section('Açılar', [
            for (final a in c.aspects)
              _row('${a.p1} - ${a.p2}',
                  '${a.type} • orb ${a.orb.toStringAsFixed(2)}'),
          ]),
        ],
      ],
    );
  }

  Widget _timeMachineTab(ChartProvider cp, ChartData c) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
      children: [
        TimeMachineBar(
          initial: _now,
          onChanged: (dt) {
            setState(() => _now = dt);
            cp.loadBiwheelDebounced(when: dt);
          },
        ),
        const SizedBox(height: 14),
        if (cp.biLoading)
          Padding(
            padding: const EdgeInsets.all(20),
            child: Center(
              child: CircularProgressIndicator(color: FastTheme.accentGold),
            ),
          ),
        if (cp.biError != null)
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text(cp.biError!,
                style: const TextStyle(color: Colors.redAccent)),
          ),
        if (cp.biwheel != null) ...[
          Center(child: _biwheel(cp, c)),
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Center(
              child: Text(
                'Natal (iç) + Transit (dış) • Bi-Wheel',
                style: TextStyle(color: FastTheme.textMuted),
              ),
            ),
          ),
          const SizedBox(height: 6),
          _section('Natal-Transit Açılar', [
            ...((cp.biwheel!.data['acilar_arasi'] as List?) ?? [])
                .take(40)
                .map((a) {
              final m = (a as Map).cast<String, dynamic>();
              return _row(
                  '${m['p1']} - ${m['p2']}', '${m['tip']} • orb ${m['orb']}');
            }),
          ]),
        ],
        if (cp.biwheel == null && !cp.biLoading)
          Padding(
            padding: const EdgeInsets.all(20),
            child: Center(
              child: Text(
                'Zamanı değiştirerek transit haritasını gör',
                style: TextStyle(color: FastTheme.textMuted),
              ),
            ),
          ),
      ],
    );
  }

  Widget _biwheel(ChartProvider cp, ChartData c) {
    final bw = cp.biwheel!.data;
    final transit = (bw['transit'] as Map?)?.cast<String, dynamic>() ?? const {};
    List<PlanetPos> outerP = [];
    List<HouseCusp> outerH = [];
    try {
      outerP = ((transit['gezegenler'] as List?) ?? [])
          .whereType<Map>()
          .map((e) => PlanetPos.fromJson(e.cast<String, dynamic>()))
          .toList();
      outerH = ((transit['evler'] as List?) ?? [])
          .whereType<Map>()
          .map((e) => HouseCusp.fromJson(e.cast<String, dynamic>()))
          .toList();
    } catch (_) {}
    return ChartWheel(
      data: c,
      size: 320,
      outerPlanets: outerP,
      outerHouses: outerH,
    );
  }

  Widget _returnsTab(ChartProvider cp, ChartData c) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
      children: [
        _returnLocationCard(cp, c),
        const SizedBox(height: 12),
        _returnPanel(cp, c),
      ],
    );
  }

  Widget _returnLocationCard(ChartProvider cp, ChartData c) {
    if (_latCtrl.text.isEmpty) {
      _latCtrl.text = (cp.returnLat ?? c.meta.lat).toStringAsFixed(4);
      _lonCtrl.text = (cp.returnLon ?? c.meta.lng).toStringAsFixed(4);
    }
    return _section('Hesaplama Yeri', [
      Padding(
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 4),
        child: Wrap(
          spacing: 8,
          runSpacing: 6,
          children: [
            ChoiceChip(
              label: const Text('Natal Yeri'),
              selected: cp.returnLocMode == 'natal',
              onSelected: (_) {
                _latCtrl.text = c.meta.lat.toStringAsFixed(4);
                _lonCtrl.text = c.meta.lng.toStringAsFixed(4);
                cp.setReturnLocation(mode: 'natal');
              },
            ),
            ChoiceChip(
              label: Text(_locating ? 'Konum alınıyor...' : 'Cihaz Konumu'),
              selected: cp.returnLocMode == 'device',
              onSelected: (_) => _useDeviceLocation(),
            ),
            ChoiceChip(
              label: const Text('Manuel'),
              selected: cp.returnLocMode == 'manual',
              onSelected: (_) =>
                  cp.setReturnLocation(mode: 'manual', lat: _returnLat(), lon: _returnLon()),
            ),
          ],
        ),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _latCtrl,
                keyboardType: const TextInputType.numberWithOptions(
                    decimal: true, signed: true),
                style: TextStyle(color: FastTheme.text),
                decoration: InputDecoration(
                  labelText: 'Enlem',
                  labelStyle: TextStyle(color: FastTheme.textMuted),
                  isDense: true,
                ),
                onSubmitted: (_) => _applyManual(cp),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: TextField(
                controller: _lonCtrl,
                keyboardType: const TextInputType.numberWithOptions(
                    decimal: true, signed: true),
                style: TextStyle(color: FastTheme.text),
                decoration: InputDecoration(
                  labelText: 'Boylam',
                  labelStyle: TextStyle(color: FastTheme.textMuted),
                  isDense: true,
                ),
                onSubmitted: (_) => _applyManual(cp),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: Icon(Icons.check_circle_outline,
                  color: FastTheme.accentGold),
              onPressed: () => _applyManual(cp),
            ),
          ],
        ),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
        child: Text(
          'Dönüş haritasında mekan; ASC/MC, ev yerleşimleri ve yöneticileri belirler. '
          'Güneş/Ay dönüşünü yaşadığın şehri seçmen en doğru sonucu verir.',
          style: TextStyle(
              color: FastTheme.textMuted.withValues(alpha: 0.8), fontSize: 12),
        ),
      ),
    ]);
  }

  double? _returnLat() => double.tryParse(_latCtrl.text.replaceAll(',', '.'));
  double? _returnLon() => double.tryParse(_lonCtrl.text.replaceAll(',', '.'));

  void _applyManual(ChartProvider cp) {
    final lat = _returnLat();
    final lon = _returnLon();
    if (lat != null && lon != null) {
      cp.setReturnLocation(mode: 'manual', lat: lat, lon: lon);
    }
  }

  Widget _returnPanel(ChartProvider cp, ChartData c) {
    final now = DateTime.now();
    final ret = cp.ret;
    ChartData? retChart;
    if (ret != null) {
      try {
        final j = Map<String, dynamic>.from(ret.data)
          ..['house_system'] = ret.data['house_system'] ?? c.houseSystem;
        retChart = ChartData.fromJson(j);
      } catch (_) {}
    }

    return _section('Solar / Lunar Return', [
      Padding(
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 8),
        child: Wrap(
          spacing: 8,
          runSpacing: 6,
          children: [
            FilledButton(
              onPressed: cp.retLoading
                  ? null
                  : () => cp.loadSolarReturn(now.year),
              style:
                  FilledButton.styleFrom(backgroundColor: FastTheme.accentGold),
              child: Text('Solar Return ${now.year}'),
            ),
            FilledButton(
              onPressed: cp.retLoading
                  ? null
                  : () => cp.loadLunarReturn(now.year, now.month),
              style: FilledButton.styleFrom(
                  backgroundColor: FastTheme.accentGoldLight),
              child: Text(
                  'Lunar Return ${now.year}-${now.month.toString().padLeft(2, '0')}'),
            ),
          ],
        ),
      ),
      if (cp.retLoading)
        Padding(
          padding: const EdgeInsets.all(16),
          child: Center(
            child: CircularProgressIndicator(color: FastTheme.accentGold),
          ),
        ),
      if (cp.retError != null)
        Padding(
          padding: const EdgeInsets.all(12),
          child: Text(cp.retError!,
              style: const TextStyle(color: Colors.redAccent)),
        ),
      if (retChart != null) ...[
        const Divider(height: 1),
        const SizedBox(height: 12),
        Center(child: ChartWheel(data: retChart, size: 300)),
        const SizedBox(height: 8),
        Center(
          child: Text(
            ret!.type == 'solar'
                ? 'Solar Return ${ret.year}'
                : 'Lunar Return ${ret.year}-${ret.month.toString().padLeft(2, '0')}',
            style: TextStyle(
                color: FastTheme.text, fontWeight: FontWeight.w600),
          ),
        ),
        const SizedBox(height: 4),
        Center(
          child: Text(
            'ASC ${_sign(retChart.asc.sign)} ${retChart.asc.degree.toStringAsFixed(2)}° • '
            'MC ${_sign(retChart.mc.sign)} ${retChart.mc.degree.toStringAsFixed(2)}°',
            style: TextStyle(color: FastTheme.textMuted),
          ),
        ),
        const SizedBox(height: 12),
        ...retChart.planets.map((p) => _row(
              p.name,
              '${_sign(p.sign)} ${p.degree.toStringAsFixed(2)}° ${p.retrograde ? 'R' : ''} • Ev ${p.house}',
            )),
      ],
      if (retChart == null && !cp.retLoading)
        Padding(
          padding: const EdgeInsets.all(16),
          child: Center(
            child: Text(
              'Yıllık dönüş haritanı hesaplamak için bir dönüş seç.',
              style: TextStyle(color: FastTheme.textMuted),
            ),
          ),
        ),
    ]);
  }

  Widget _section(String title, List<Widget> children) {
    return Container(
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: FastTheme.border.withValues(alpha: 0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 8),
            child: Text(
              title,
              style: TextStyle(
                  color: FastTheme.accentGold, fontWeight: FontWeight.w700),
            ),
          ),
          const Divider(height: 1),
          ...children,
        ],
      ),
    );
  }

  Widget _row(String left, String right) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(left, style: TextStyle(color: FastTheme.text)),
          Text(right, style: TextStyle(color: FastTheme.textMuted)),
        ],
      ),
    );
  }
}
