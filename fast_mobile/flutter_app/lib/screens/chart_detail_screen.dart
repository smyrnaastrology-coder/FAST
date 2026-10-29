import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:geolocator/geolocator.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:uuid/uuid.dart';

import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/chart_data.dart';
import '../models/chart_frame.dart';
import '../models/chart_labels.dart';
import '../providers/chart_provider.dart';
import '../widgets/chart_wheel.dart';
import '../widgets/time_machine_bar.dart';
import '../widgets/chart_location_picker.dart';
import '../services/chart_service.dart';
import 'chart_create_screen.dart';

class ChartDetailScreen extends StatefulWidget {
  const ChartDetailScreen({super.key});

  @override
  State<ChartDetailScreen> createState() => _ChartDetailScreenState();
}

class _ChartDetailScreenState extends State<ChartDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tab;
  final GlobalKey _shareKey = GlobalKey();
  DateTime _now = DateTime.now();
  bool _twoCharts = false;
  int _bottomNavIndex = 1; // 0=Charts,1=View,2=Reports,3=Settings,4=Info
  final _latCtrl = TextEditingController();
  final _lonCtrl = TextEditingController();
  bool _locating = false;
  DateTime _arcDate = DateTime.now();
  String _progressionMethod = 'secondary';
  int _returnYear = DateTime.now().year;
  int _returnMonth = DateTime.now().month;
  final _charts = ChartService();

  // ── 2 harita (bi-wheel) modu ────────────────────────────────────────────
  // İç ve dış harita BİRBİRİNDEN BAĞIMSIZ seçilir: natal + transit,
  // natal + solar return, natal + progress, iki natal... Yerleri değiştirilir.
  String _innerSource = 'current';
  ChartData? _innerChart;
  String _innerLabel = '';
  String _outerSource = 'transit';
  ChartData? _outerChart;
  String _outerLabel = '';

  ChartData? _parseChart(Map<String, dynamic>? j, {String? houseSystem}) {
    if (j == null) return null;
    try {
      final m = Map<String, dynamic>.from(j);
      m['house_system'] = m['house_system'] ?? houseSystem ?? 'P';
      return ChartData.fromJson(m);
    } catch (_) {
      return null;
    }
  }

  ChartData? _resolveChart(
    String source,
    ChartData? data,
    ChartProvider cp,
    ChartData c,
  ) {
    switch (source) {
      case 'current':
        return c;
      case 'transit':
        return _parseChart(
          (cp.biwheel?.data['transit'] as Map?)?.cast<String, dynamic>(),
          houseSystem: c.houseSystem,
        );
      case 'return':
        return _parseChart(cp.ret?.data, houseSystem: c.houseSystem);
      case 'arc':
        return _parseChart(cp.arc?.data, houseSystem: c.houseSystem);
      default:
        return data;
    }
  }

  String _sourceLabel(
    String source,
    ChartProvider cp,
    ChartData c, {
    String fallback = 'Harita',
  }) {
    switch (source) {
      case 'current':
        final n = c.meta.name;
        return n != null && n.isNotEmpty ? n : _l10n.chartDefaultName;
      case 'transit':
        return 'Transit';
      case 'return':
        final r = cp.ret;
        if (r == null) return 'Return';
        return r.type == 'solar'
            ? 'Solar Return ${r.year}'
            : 'Lunar Return ${r.year}/${r.month.toString().padLeft(2, '0')}';
      case 'arc':
        final a = cp.arc;
        final method = '${a?.data['progression']?['method'] ?? 'secondary'}';
        final label = method == 'minor'
            ? _l10n.chartMinorProgress
            : _l10n.chartSecondaryProgress;
        return a == null ? label : '$label • ${a.targetDate}';
      default:
        return fallback;
    }
  }

  String _dateText(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
  String _clockText(DateTime d) =>
      '${d.hour.toString().padLeft(2, '0')}:'
      '${d.minute.toString().padLeft(2, '0')}';

  ChartFrame _transitFrame(ChartData natal, Map<String, dynamic> response) {
    final transit = ChartData.fromJson(
      Map<String, dynamic>.from(response['transit'] as Map),
    );
    return ChartFrame(
      data: natal,
      outerPlanets: transit.planets,
      outerHouses: transit.houses,
      title: _l10n.chartNatalTransitTitle,
      subtitle: '${natal.meta.name ?? ''} • ${natal.meta.place}',
    );
  }

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: 4, vsync: this)..addListener(_onTabChanged);
  }

  void _onTabChanged() {
    if (!mounted || _tab.indexIsChanging) return;
    if (_tab.index == 1) {
      final cp = context.read<ChartProvider>();
      if (cp.biwheel == null && !cp.biLoading) {
        cp.loadBiwheel(when: _now);
      }
    }
    setState(() {});
  }

  Widget _chartCountBtn(String label, bool active, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        decoration: BoxDecoration(
          color: active ? FastTheme.accentGold : FastTheme.cardBg,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: FastTheme.border),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: active ? FastTheme.bg : FastTheme.text,
            fontWeight: FontWeight.w600,
            fontSize: 12,
          ),
        ),
      ),
    );
  }

  // ── 2 harita modu yardımcıları ──────────────────────────────────────────
  void _setTwoCharts(ChartData c, ChartProvider cp) {
    setState(() {
      _twoCharts = true;
      _innerLabel = _sourceLabel(_innerSource, cp, c, fallback: _innerLabel);
      _outerLabel = _sourceLabel(_outerSource, cp, c, fallback: _outerLabel);
    });
    if ((_innerSource == 'transit' || _outerSource == 'transit') &&
        cp.biwheel == null &&
        !cp.biLoading) {
      cp.loadBiwheel(when: _now);
    }
  }

  void _swapCharts(ChartData c, ChartProvider cp) {
    setState(() {
      final src = _innerSource;
      final chart = _innerChart;
      final label = _innerLabel;
      _innerSource = _outerSource;
      _innerChart = _outerChart;
      _innerLabel = _outerLabel;
      _outerSource = src;
      _outerChart = chart;
      _outerLabel = label;
      _innerLabel = _sourceLabel(_innerSource, cp, c, fallback: _innerLabel);
      _outerLabel = _sourceLabel(_outerSource, cp, c, fallback: _outerLabel);
    });
  }

  Future<void> _refreshTwoCharts(ChartProvider cp) async {
    Future<void> refresh(String source) async {
      switch (source) {
        case 'transit':
          await cp.loadBiwheel(when: DateTime.now());
          break;
        case 'return':
          final r = cp.ret;
          if (r == null) return;
          if (r.type == 'solar') {
            await cp.loadSolarReturn(r.year);
          } else if (r.month != null) {
            await cp.loadLunarReturn(r.year, r.month!);
          }
          break;
        case 'arc':
          final a = cp.arc;
          if (a == null) return;
          await cp.loadSolarArc(
            a.targetDate,
            method: '${a.data['progression']?['method'] ?? 'secondary'}',
          );
          break;
      }
    }

    await refresh(_innerSource);
    await refresh(_outerSource);
    if (mounted) {
      setState(() => _now = DateTime.now());
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Haritalar yenilendi')),
      );
    }
  }

  void _applySlot(
    bool innerSlot,
    String source,
    ChartData? chart,
    String label,
  ) {
    setState(() {
      if (innerSlot) {
        _innerSource = source;
        _innerChart = chart;
        _innerLabel = label;
      } else {
        _outerSource = source;
        _outerChart = chart;
        _outerLabel = label;
      }
    });
    final cp = context.read<ChartProvider>();
    if (source == 'transit' && cp.biwheel == null && !cp.biLoading) {
      cp.loadBiwheel(when: _now);
    }
  }

  void _pickSlot(ChartData c, ChartProvider cp, bool innerSlot) {
    final l10n = _l10n;
    final currentName = c.meta.name?.isNotEmpty == true
        ? c.meta.name!
        : l10n.chartDefaultName;
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: FastTheme.bgSecondary,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: ConstrainedBox(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.of(ctx).size.height * 0.72,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(height: 8),
              Container(
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: FastTheme.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 6),
                child: Row(
                  children: [
                    Icon(
                      innerSlot ? Icons.filter_1 : Icons.filter_2,
                      color: FastTheme.accentGold,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      innerSlot ? 'İç harita seç' : 'Dış harita seç',
                      style: TextStyle(
                        color: FastTheme.accentGold,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    ListTile(
                      leading: Icon(
                        Icons.my_location,
                        color: FastTheme.accentGold,
                      ),
                      title: Text(
                        'Geçerli harita',
                        style: TextStyle(color: FastTheme.text),
                      ),
                      subtitle: Text(
                        currentName,
                        style: TextStyle(color: FastTheme.textMuted),
                      ),
                      onTap: () {
                        Navigator.pop(ctx);
                        _applySlot(innerSlot, 'current', null, currentName);
                      },
                    ),
                    ListTile(
                      leading: Icon(Icons.autorenew, color: FastTheme.accentGold),
                      title: Text(
                        'Transit (şimdi)',
                        style: TextStyle(color: FastTheme.text),
                      ),
                      subtitle: Text(
                        _now.toString().substring(0, 16),
                        style: TextStyle(color: FastTheme.textMuted),
                      ),
                      onTap: () {
                        Navigator.pop(ctx);
                        _applySlot(innerSlot, 'transit', null, 'Transit');
                      },
                    ),
                    if (cp.ret != null)
                      ListTile(
                        leading: Icon(
                          Icons.wb_sunny_outlined,
                          color: FastTheme.accentGold,
                        ),
                        title: Text(
                          'Hesaplanan Return',
                          style: TextStyle(color: FastTheme.text),
                        ),
                        subtitle: Text(
                          _sourceLabel('return', cp, c),
                          style: TextStyle(color: FastTheme.textMuted),
                        ),
                        onTap: () {
                          Navigator.pop(ctx);
                          _applySlot(
                            innerSlot,
                            'return',
                            null,
                            _sourceLabel('return', cp, c),
                          );
                        },
                      ),
                    if (cp.arc != null)
                      ListTile(
                        leading: Icon(
                          Icons.trending_up,
                          color: FastTheme.accentGold,
                        ),
                        title: Text(
                          'Hesaplanan Progress',
                          style: TextStyle(color: FastTheme.text),
                        ),
                        subtitle: Text(
                          _sourceLabel('arc', cp, c),
                          style: TextStyle(color: FastTheme.textMuted),
                        ),
                        onTap: () {
                          Navigator.pop(ctx);
                          _applySlot(
                            innerSlot,
                            'arc',
                            null,
                            _sourceLabel('arc', cp, c),
                          );
                        },
                      ),
                    if (cp.saved.isNotEmpty) ...[
                      const Divider(height: 1),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 10, 20, 4),
                        child: Text(
                          'Kayıtlı haritalar',
                          style: TextStyle(
                            color: FastTheme.textMuted,
                            fontSize: 12,
                          ),
                        ),
                      ),
                      ...cp.saved.map((s) {
                        final nm = s.meta.name?.isNotEmpty == true
                            ? s.meta.name!
                            : l10n.chartDefaultName;
                        return ListTile(
                          leading: Icon(
                            Icons.auto_awesome_outlined,
                            color: FastTheme.textMuted,
                          ),
                          title: Text(nm, style: TextStyle(color: FastTheme.text)),
                          subtitle: Text(
                            '${s.meta.date} • ${s.meta.time}',
                            style: TextStyle(color: FastTheme.textMuted),
                          ),
                          onTap: () {
                            Navigator.pop(ctx);
                            _applySlot(innerSlot, 'saved', s, nm);
                          },
                        );
                      }),
                    ],
                    const Divider(height: 1),
                    ListTile(
                      leading: Icon(Icons.add, color: FastTheme.accentGold),
                      title: Text(
                        'Yeni harita oluştur',
                        style: TextStyle(
                          color: FastTheme.accentGold,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      onTap: () {
                        Navigator.pop(ctx);
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => const ChartCreateScreen(),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _slotCard(String title, String value, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: FastTheme.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: FastTheme.border.withValues(alpha: 0.6)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              title,
              style: TextStyle(color: FastTheme.textMuted, fontSize: 10),
            ),
            const SizedBox(height: 2),
            Row(
              children: [
                Expanded(
                  child: Text(
                    value,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: FastTheme.text,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Icon(Icons.expand_more, size: 16, color: FastTheme.accentGold),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _showSubsidiary() {
    final cp = context.read<ChartProvider>();
    final c = cp.current;
    if (c == null) return;
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: FastTheme.bgSecondary,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            Container(width: 36, height: 4, decoration: BoxDecoration(color: FastTheme.border, borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 12),
            ListTile(
              leading: Icon(Icons.trending_up, color: FastTheme.accentGold),
              title: Text('Secondary Progress', style: TextStyle(color: FastTheme.text)),
              onTap: () { Navigator.pop(ctx); _tab.animateTo(3); },
            ),
            ListTile(
              leading: Icon(Icons.trending_flat, color: FastTheme.accentGold),
              title: Text('Minor Progress', style: TextStyle(color: FastTheme.text)),
              onTap: () { Navigator.pop(ctx); _tab.animateTo(3); },
            ),
            ListTile(
              leading: Icon(Icons.wb_sunny_outlined, color: FastTheme.accentGold),
              title: Text('Solar Return', style: TextStyle(color: FastTheme.text)),
              onTap: () { Navigator.pop(ctx); _tab.animateTo(2); },
            ),
            ListTile(
              leading: Icon(Icons.nightlight_outlined, color: FastTheme.accentGold),
              title: Text('Lunar Return', style: TextStyle(color: FastTheme.text)),
              onTap: () { Navigator.pop(ctx); _tab.animateTo(2); },
            ),
            ListTile(
              leading: Icon(Icons.merge_type, color: FastTheme.accentGold),
              title: Text('Combined', style: TextStyle(color: FastTheme.text)),
              onTap: () {
                Navigator.pop(ctx);
                if (!_twoCharts) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Combined için 2 harita seçmelisiniz.')),
                  );
                  return;
                }
                _showCombined();
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showCombined() {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: FastTheme.bgSecondary,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            Container(width: 36, height: 4, decoration: BoxDecoration(color: FastTheme.border, borderRadius: BorderRadius.circular(2))),
            const SizedBox(height: 12),
            ListTile(
              leading: Icon(Icons.center_focus_strong, color: FastTheme.accentGold),
              title: Text('Composite (Midpoint)', style: TextStyle(color: FastTheme.text)),
              onTap: () => Navigator.pop(ctx),
            ),
            ListTile(
              leading: Icon(Icons.people, color: FastTheme.accentGold),
              title: Text('Relationship (Davison)', style: TextStyle(color: FastTheme.text)),
              onTap: () => Navigator.pop(ctx),
            ),
          ],
        ),
      ),
    );
  }

  void _showSettings() {
    final cp = context.read<ChartProvider>();
    final c = cp.current;
    if (c == null) return;
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: FastTheme.bgSecondary,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Ayarlar', style: TextStyle(color: FastTheme.accentGold, fontSize: 18, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              Text('Ev sistemi: ${c.houseSystem}', style: TextStyle(color: FastTheme.text)),
              Text('Zaman dilimi: UTC ${c.meta.tz ?? "?"}', style: TextStyle(color: FastTheme.text)),
              Text('Konum: ${c.meta.place}', style: TextStyle(color: FastTheme.text)),
              const SizedBox(height: 16),
              OutlinedButton(
                onPressed: () => Navigator.pop(ctx),
                child: Text('Kapat', style: TextStyle(color: FastTheme.accentGold)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showInfo() {
    final cp = context.read<ChartProvider>();
    final c = cp.current;
    if (c == null) return;
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: FastTheme.bgSecondary,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Bilgi', style: TextStyle(color: FastTheme.accentGold, fontSize: 18, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              Text('Ad: ${c.meta.name ?? "—"}', style: TextStyle(color: FastTheme.text)),
              Text('Tarih: ${c.meta.date} ${c.meta.time}', style: TextStyle(color: FastTheme.text)),
              Text('Yer: ${c.meta.place}', style: TextStyle(color: FastTheme.text)),
              Text('Koordinatlar: ${c.meta.lat.toStringAsFixed(4)}, ${c.meta.lng.toStringAsFixed(4)}', style: TextStyle(color: FastTheme.text)),
              const SizedBox(height: 16),
              OutlinedButton(
                onPressed: () => Navigator.pop(ctx),
                child: Text('Kapat', style: TextStyle(color: FastTheme.accentGold)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _shareChart() async {
    try {
      final boundary = _shareKey.currentContext?.findRenderObject() as RenderRepaintBoundary?;
      if (boundary == null) return;
      final image = await boundary.toImage(pixelRatio: 2.0);
      final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
      if (byteData == null) return;
      final bytes = byteData.buffer.asUint8List();
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/chart_${const Uuid().v4()}.png');
      await file.writeAsBytes(bytes);
      await Share.shareXFiles([XFile(file.path)], text: 'Holavon astroloji haritam');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Paylaşım hatası: $e')));
      }
    }
  }

  @override
  void dispose() {
    _tab.removeListener(_onTabChanged);
    _tab.dispose();
    _latCtrl.dispose();
    _lonCtrl.dispose();
    super.dispose();
  }

  String _sign(int i) {
    if (i < 0 || i > 11) return '-';
    return chartSignNames(_l10n)[i];
  }

  /// Ondalık dereceyi D°MM' biçiminde gösterir (örn. 15.29° → 15°17').
  String _degMin(double deg) {
    final total = (deg * 60).round();
    final d = total ~/ 60;
    final m = total % 60;
    return '$d°${m.toString().padLeft(2, '0')}′';
  }

  AppLocalizations get _l10n => AppLocalizations.of(context);

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
            _l10n.chartNotFound,
            style: TextStyle(color: FastTheme.textMuted),
          ),
        ),
      );
    }

    final name = c.meta.name?.isNotEmpty == true
        ? c.meta.name!
        : _l10n.chartDefaultName;

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        actions: [
          IconButton(
            tooltip: 'Yeni harita',
            icon: Icon(Icons.add, color: FastTheme.accentGold),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ChartCreateScreen()),
            ),
          ),
          IconButton(
            tooltip: 'Paylaş',
            icon: const Icon(Icons.share_outlined),
            onPressed: _shareChart,
          ),
          IconButton(
            tooltip: 'Subsidiary',
            icon: const Icon(Icons.account_tree_outlined),
            onPressed: _showSubsidiary,
          ),
          TextButton.icon(
            icon: const Icon(Icons.save_outlined),
            label: Text(_l10n.chartSave),
            onPressed: () async {
              await cp.saveCurrent();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(_l10n.chartSaved)),
                );
              }
            },
          ),
          IconButton(
            tooltip: _l10n.chartDelete,
            icon: const Icon(Icons.delete_outline),
            onPressed: () async {
              await cp.delete(c);
              if (context.mounted) Navigator.of(context).pop();
            },
          ),
        ],
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
          isScrollable: true,
          tabs: [
            Tab(text: _l10n.chartTabNatal),
            Tab(text: _l10n.chartTabTimeMachine),
            Tab(text: _l10n.chartTabReturns),
            Tab(text: _l10n.chartTabProgressions),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _bottomNavIndex,
        onTap: (i) {
          if (i == 0) {
            Navigator.of(context).pop();
            return;
          }
          if (i == 2) {
            _showSettings();
            return;
          }
          if (i == 3) {
            _showInfo();
            return;
          }
          setState(() => _bottomNavIndex = i);
        },
        backgroundColor: FastTheme.bgSecondary,
        selectedItemColor: FastTheme.accentGold,
        unselectedItemColor: FastTheme.textMuted,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.list), label: 'Charts'),
          BottomNavigationBarItem(icon: Icon(Icons.visibility), label: 'View'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Settings'),
          BottomNavigationBarItem(icon: Icon(Icons.info_outline), label: 'Info'),
        ],
      ),
      body: RepaintBoundary(
        key: _shareKey,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _chartCountBtn('1 Chart', !_twoCharts, () => setState(() => _twoCharts = false)),
                  const SizedBox(width: 8),
                  _chartCountBtn('2 Charts', _twoCharts, () {
                    if (!_twoCharts) {
                      _setTwoCharts(c, cp);
                    } else {
                      setState(() => _twoCharts = false);
                    }
                  }),
                  if (_twoCharts) ...[
                    const Spacer(),
                    IconButton(
                      tooltip: 'Haritaları yer değiştir',
                      visualDensity: VisualDensity.compact,
                      icon: Icon(Icons.swap_horiz, color: FastTheme.accentGold),
                      onPressed: () => _swapCharts(c, cp),
                    ),
                    IconButton(
                      tooltip: 'Haritaları yenile',
                      visualDensity: VisualDensity.compact,
                      icon: Icon(Icons.refresh, color: FastTheme.accentGold),
                      onPressed: cp.biLoading || cp.retLoading || cp.arcLoading
                          ? null
                          : () => _refreshTwoCharts(cp),
                    ),
                  ],
                ],
              ),
            ),
            Expanded(child: TabBarView(
        controller: _tab,
        children: [
          _natalTab(c),
          _timeMachineTab(cp, c),
          _returnsTab(cp, c),
          _solarArcTab(cp, c),
        ],
      ),
      ),
    ],
  ),
  ),
)
;
  }
  Widget _natalTab(ChartData c) {
    final l10n = _l10n;
    final cp = context.read<ChartProvider>();
    if (_twoCharts) {
      return _twoChartView(cp, c);
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
      children: [
        Center(
          child: ChartWheel(
            data: c,
            size: 340,
            title: l10n.chartNatalWithName(c.meta.name ?? ''),
            subtitle: c.meta.place,
            loadFrame: (date) async => ChartFrame(
              data: await _charts.natal(
                tarih: _dateText(date),
                saat: _clockText(date),
                lat: c.meta.lat,
                lon: c.meta.lng,
                houseSystem: c.houseSystem,
                isim: c.meta.name,
                place: c.meta.place,
              ),
              title: l10n.chartNatalWithName(c.meta.name ?? ''),
              subtitle: c.meta.place,
            ),
          ),
        ),
        const SizedBox(height: 16),
        _section(l10n.chartSectionInfo, [
          _row(l10n.chartLabelDateTime, '${c.meta.date} • ${c.meta.time}'),
          _row(
            l10n.chartLabelHistoricalTz,
            c.meta.tz == null
                ? l10n.chartTzUnknown
                : 'UTC ${c.meta.tz! >= 0 ? '+' : ''}${c.meta.tz}',
          ),
          TextButton.icon(
            icon: const Icon(Icons.refresh),
            label: Text(l10n.chartRecalculateTz),
            onPressed: () => context.read<ChartProvider>().create(
              name: c.meta.name ?? '',
              date: c.meta.date,
              time: c.meta.time,
              lat: c.meta.lat,
              lng: c.meta.lng,
              place: c.meta.place,
            ),
          ),
          _row(
            l10n.chartLabelHouseSystem,
            chartHouseSystemLabel(l10n, c.houseSystem),
          ),
          if (c.meta.place.isNotEmpty) _row(l10n.chartLabelPlace, c.meta.place),
        ]),
        const SizedBox(height: 14),
        _section(l10n.chartSectionPlanets, [
          for (final p in c.planets)
            _row(
              chartPlanetLabel(l10n, p.name),
              '${_sign(p.sign)} ${_degMin(p.degree)} '
              '${p.retrograde ? 'R' : ''} • ${l10n.chartHouseNumber(p.house)}',
            ),
        ]),
        const SizedBox(height: 14),
        _section(l10n.chartSectionHouses, [
          for (final h in c.houses)
            _row(
              l10n.chartHouseNumber(h.number),
              '${_sign(h.sign)} ${_degMin(h.degree)}',
            ),
        ]),
        if (c.aspects.isNotEmpty) ...[
          const SizedBox(height: 14),
          _section(l10n.chartSectionAspects, [
            for (final a in c.aspects)
              _row(
                '${chartPlanetLabel(l10n, a.p1)} – ${chartPlanetLabel(l10n, a.p2)}',
                '${chartAspectLabel(l10n, a.type)} • '
                    '${l10n.chartOrb(a.orb.toStringAsFixed(2))}',
              ),
          ]),
        ],
      ],
    );
  }

  Widget _twoChartView(ChartProvider cp, ChartData c) {
    final inner = _resolveChart(_innerSource, _innerChart, cp, c) ?? c;
    final outer = _resolveChart(_outerSource, _outerChart, cp, c);
    final innerLabel = _sourceLabel(_innerSource, cp, c, fallback: _innerLabel);
    final outerLabel = _sourceLabel(_outerSource, cp, c, fallback: _outerLabel);
    final loading = cp.biLoading || cp.retLoading || cp.arcLoading;

    return ListView(
      padding: const EdgeInsets.fromLTRB(12, 6, 12, 28),
      children: [
        Row(
          children: [
            Expanded(
              child: _slotCard(
                'İç harita',
                innerLabel,
                () => _pickSlot(c, cp, true),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2),
              child: IconButton(
                tooltip: 'Yer değiştir',
                visualDensity: VisualDensity.compact,
                icon: Icon(Icons.swap_horiz, color: FastTheme.accentGold),
                onPressed: () => _swapCharts(c, cp),
              ),
            ),
            Expanded(
              child: _slotCard(
                'Dış harita',
                outer == null ? 'Seç…' : outerLabel,
                () => _pickSlot(c, cp, false),
              ),
            ),
          ],
        ),
        if (loading)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: LinearProgressIndicator(
              minHeight: 2,
              color: FastTheme.accentGold,
              backgroundColor: FastTheme.border.withValues(alpha: 0.3),
            ),
          ),
        const SizedBox(height: 6),
        if (outer == null)
          _section('Dış harita', [
            Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Dış haritayı seçin: Transit (şimdi), hesaplanmış Solar/Lunar Return, '
                    'Progress veya kayıtlı bir harita.',
                    style: TextStyle(color: FastTheme.textMuted, height: 1.4),
                  ),
                  const SizedBox(height: 10),
                  FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: FastTheme.accentGold,
                    ),
                    onPressed: () => _pickSlot(c, cp, false),
                    icon: const Icon(Icons.addchart),
                    label: const Text('Harita seç'),
                  ),
                ],
              ),
            ),
          ])
        else
          Center(
            child: ChartWheel(
              data: inner,
              outerPlanets: outer.planets,
              outerHouses: outer.houses,
              size: 360,
              title: '$innerLabel • $outerLabel',
              subtitle: c.meta.place,
            ),
          ),
        if (outer != null) ...[
          const SizedBox(height: 6),
          Center(
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _legendDot(FastTheme.text, 'İç: $innerLabel'),
                const SizedBox(width: 14),
                _legendDot(const Color(0xFF8FD8FF), 'Dış: $outerLabel'),
              ],
            ),
          ),
          const SizedBox(height: 10),
          _section('Dış harita gezegenleri', [
            for (final p in outer.planets)
              _row(
                chartPlanetLabel(_l10n, p.name),
                '${_sign(p.sign)} ${_degMin(p.degree)} '
                '${p.retrograde ? 'R' : ''} • ${_l10n.chartHouseNumber(p.house)}',
              ),
          ]),
        ],
      ],
    );
  }

  Widget _timeMachineTab(ChartProvider cp, ChartData c) {
    final l10n = _l10n;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
      children: [
        TimeMachineBar(
          initial: _now,
          onChanged: (dt) {
            setState(() => _now = dt);
            cp.loadBiwheelDebounced(when: dt, ms: 180);
          },
        ),
        const SizedBox(height: 8),
        if (cp.biLoading)
          LinearProgressIndicator(
            minHeight: 2,
            color: FastTheme.accentGold,
            backgroundColor: FastTheme.border.withValues(alpha: 0.3),
          ),
        const SizedBox(height: 10),
        Center(child: _biwheel(cp, c)),
        const SizedBox(height: 10),
        Center(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _legendDot(FastTheme.text, l10n.chartNatalInner),
              const SizedBox(width: 14),
              _legendDot(const Color(0xFF8FD8FF), l10n.chartTransitOuter),
            ],
          ),
        ),
        if (cp.biError != null)
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text(
              cp.biError!,
              style: const TextStyle(color: Colors.redAccent),
            ),
          ),
        const SizedBox(height: 10),
        if (cp.biwheel != null)
          _section(l10n.chartSectionNatalTransitAspects, [
            ...((cp.biwheel!.data['acilar_arasi'] as List?) ?? []).take(40).map((
              a,
            ) {
              final m = (a as Map).cast<String, dynamic>();
              return _row(
                '${chartPlanetLabel(l10n, '${m['p1']}')} – '
                '${chartPlanetLabel(l10n, '${m['p2']}')}',
                '${chartAspectLabel(l10n, '${m['tip']}')} • '
                    '${l10n.chartOrb('${m['orb']}')}',
              );
            }),
            if (((cp.biwheel!.data['acilar_arasi'] as List?) ?? []).isEmpty)
              _row(l10n.chartNoAspects, '—'),
          ]),
      ],
    );
  }

  Widget _legendDot(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 5),
        Text(label, style: TextStyle(color: FastTheme.textMuted, fontSize: 11)),
      ],
    );
  }

  Widget _biwheel(ChartProvider cp, ChartData c) {
    if (cp.biwheel == null) {
      return SizedBox(
        width: 340,
        height: 340,
        child: Center(
          child: Text(
            _l10n.chartTimeMachineHint,
            textAlign: TextAlign.center,
            style: TextStyle(color: FastTheme.textMuted),
          ),
        ),
      );
    }
    final bw = cp.biwheel!.data;
    final transit =
        (bw['transit'] as Map?)?.cast<String, dynamic>() ?? const {};
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
      size: 340,
      outerPlanets: outerP,
      outerHouses: outerH,
      title: _l10n.chartNatalTransitTitle,
      subtitle: '${c.meta.name ?? ''} • ${c.meta.place}',
      initialDate: cp.biwheel!.when,
      loadFrame: (date) async => _transitFrame(
        c,
        await _charts.biwheel(
          natal: c,
          hedefTarih: _dateText(date),
          hedefSaat: _clockText(date),
        ),
      ),
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
    final l10n = _l10n;
    if (_latCtrl.text.isEmpty) {
      _latCtrl.text = (cp.returnLat ?? c.meta.lat).toStringAsFixed(4);
      _lonCtrl.text = (cp.returnLon ?? c.meta.lng).toStringAsFixed(4);
    }
    return _section(l10n.chartSectionReturnLocation, [
      Padding(
        padding: const EdgeInsets.all(12),
        child: ChartLocationPicker(
          onPending: cp.invalidateReturnLocation,
          onSelected: (place, lat, lon) {
            _latCtrl.text = lat.toStringAsFixed(5);
            _lonCtrl.text = lon.toStringAsFixed(5);
            cp.setReturnLocation(
              mode: 'city',
              lat: lat,
              lon: lon,
              place: place,
            );
          },
        ),
      ),
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14),
        child: Text(
          cp.returnLocationConfirmed
              ? l10n.chartReturnLocationSelected(
                  cp.returnPlace,
                  cp.returnLat!.toStringAsFixed(4),
                  cp.returnLon!.toStringAsFixed(4),
                )
              : l10n.chartReturnLocationPrompt,
          style: TextStyle(color: FastTheme.text),
        ),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 4),
        child: Wrap(
          spacing: 8,
          runSpacing: 6,
          children: [
            ChoiceChip(
              label: Text(l10n.chartReturnNatalPlace),
              selected: cp.returnLocMode == 'natal',
              onSelected: (_) {
                _latCtrl.text = c.meta.lat.toStringAsFixed(4);
                _lonCtrl.text = c.meta.lng.toStringAsFixed(4);
                cp.setReturnLocation(mode: 'natal');
              },
            ),
            ChoiceChip(
              label: Text(
                _locating
                    ? l10n.chartReturnLocating
                    : l10n.chartReturnDeviceLocation,
              ),
              selected: cp.returnLocMode == 'device',
              onSelected: (_) => _useDeviceLocation(),
            ),
            ChoiceChip(
              label: Text(l10n.chartReturnManual),
              selected: cp.returnLocMode == 'manual',
              onSelected: (_) => cp.setReturnLocation(
                mode: 'manual',
                lat: _returnLat(),
                lon: _returnLon(),
              ),
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
                  decimal: true,
                  signed: true,
                ),
                style: TextStyle(color: FastTheme.text),
                decoration: InputDecoration(
                  labelText: l10n.chartLabelLatitude,
                  labelStyle: TextStyle(color: FastTheme.textMuted),
                  isDense: true,
                ),
                onSubmitted: (_) => _applyManual(cp),
                onChanged: (_) => cp.invalidateReturnLocation(),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: TextField(
                controller: _lonCtrl,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                  signed: true,
                ),
                style: TextStyle(color: FastTheme.text),
                decoration: InputDecoration(
                  labelText: l10n.chartLabelLongitude,
                  labelStyle: TextStyle(color: FastTheme.textMuted),
                  isDense: true,
                ),
                onSubmitted: (_) => _applyManual(cp),
                onChanged: (_) => cp.invalidateReturnLocation(),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: Icon(
                Icons.check_circle_outline,
                color: FastTheme.accentGold,
              ),
              onPressed: () => _applyManual(cp),
            ),
          ],
        ),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
        child: Text(
          l10n.chartReturnLocationExplainer,
          style: TextStyle(
            color: FastTheme.textMuted.withValues(alpha: 0.8),
            fontSize: 12,
          ),
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
    final l10n = _l10n;
    final returnLat = cp.returnLat;
    final returnLon = cp.returnLon;
    final returnPlace = cp.returnPlace;
    final ret = cp.ret;
    ChartData? retChart;
    if (ret != null) {
      try {
        final j = Map<String, dynamic>.from(ret.data)
          ..['house_system'] = ret.data['house_system'] ?? c.houseSystem;
        retChart = ChartData.fromJson(j);
      } catch (_) {}
    }

    return _section(l10n.chartSectionSolarLunarReturn, [
      Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<int>(
                initialValue: _returnYear,
                decoration: InputDecoration(labelText: l10n.chartLabelYear),
                items: List.generate(201, (i) => DateTime.now().year - 100 + i)
                    .map((y) => DropdownMenuItem(value: y, child: Text('$y')))
                    .toList(),
                onChanged: (v) {
                  if (v != null) setState(() => _returnYear = v);
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: DropdownButtonFormField<int>(
                initialValue: _returnMonth,
                decoration: InputDecoration(labelText: l10n.chartLabelLunarMonth),
                items: List.generate(
                  12,
                  (i) =>
                      DropdownMenuItem(value: i + 1, child: Text('${i + 1}')),
                ),
                onChanged: (v) {
                  if (v != null) setState(() => _returnMonth = v);
                },
              ),
            ),
          ],
        ),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 8),
        child: Wrap(
          spacing: 8,
          runSpacing: 6,
          children: [
            FilledButton(
              onPressed: cp.retLoading || !cp.returnLocationConfirmed
                  ? null
                  : () => cp.loadSolarReturn(_returnYear),
              style: FilledButton.styleFrom(
                backgroundColor: FastTheme.accentGold,
              ),
              child: Text(l10n.chartSolarReturnYear(_returnYear)),
            ),
            FilledButton(
              onPressed: cp.retLoading || !cp.returnLocationConfirmed
                  ? null
                  : () => cp.loadLunarReturn(_returnYear, _returnMonth),
              style: FilledButton.styleFrom(
                backgroundColor: FastTheme.accentGoldLight,
              ),
              child: Text(
                l10n.chartLunarReturnYm(
                  _returnYear,
                  _returnMonth.toString().padLeft(2, '0'),
                ),
              ),
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
          child: Text(
            cp.retError!,
            style: const TextStyle(color: Colors.redAccent),
          ),
        ),
      if (retChart != null) ...[
        const Divider(height: 1),
        const SizedBox(height: 12),
        Center(
          child: ChartWheel(
            data: retChart,
            size: 320,
            title: ret!.type == 'solar'
                ? l10n.chartSolarReturn
                : l10n.chartLunarReturn,
            subtitle: cp.returnPlace,
            initialDate: DateTime(ret.year, ret.month ?? 1, 1),
            timeUnits: ret.type == 'solar'
                ? const [ChartTimeUnit.year]
                : const [ChartTimeUnit.month, ChartTimeUnit.year],
            loadFrame: (date) async => ChartFrame(
              data: ChartData.fromJson(
                ret.type == 'solar'
                    ? await _charts.solarReturn(
                        natal: c,
                        year: date.year,
                        lat: returnLat,
                        lon: returnLon,
                      )
                    : await _charts.lunarReturn(
                        natal: c,
                        year: date.year,
                        month: date.month,
                        lat: returnLat,
                        lon: returnLon,
                      ),
              ),
              title: ret.type == 'solar'
                  ? l10n.chartSolarReturn
                  : l10n.chartLunarReturn,
              subtitle: returnPlace,
            ),
          ),
        ),
        const SizedBox(height: 8),
        Center(
          child: Text(
            ret.type == 'solar'
                ? l10n.chartSolarReturnYear(ret.year)
                : l10n.chartLunarReturnYm(
                    ret.year,
                    ret.month.toString().padLeft(2, '0'),
                  ),
            style: TextStyle(
              color: FastTheme.text,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        const SizedBox(height: 4),
        Center(
          child: Text(
            'ASC ${_sign(retChart.asc.sign)} ${_degMin(retChart.asc.degree)} • '
            'MC ${_sign(retChart.mc.sign)} ${_degMin(retChart.mc.degree)}',
            style: TextStyle(color: FastTheme.textMuted),
          ),
        ),
        const SizedBox(height: 12),
        ...retChart.planets.map(
          (p) => _row(
            chartPlanetLabel(l10n, p.name),
            '${_sign(p.sign)} ${p.degree.toStringAsFixed(2)}° '
            '${p.retrograde ? 'R' : ''} • ${l10n.chartHouseNumber(p.house)}',
          ),
        ),
      ],
      if (retChart == null && !cp.retLoading)
        Padding(
          padding: const EdgeInsets.all(16),
          child: Center(
            child: Text(
              l10n.chartReturnPrompt,
              style: TextStyle(color: FastTheme.textMuted),
            ),
          ),
        ),
    ]);
  }

  Widget _solarArcTab(ChartProvider cp, ChartData c) {
    final l10n = _l10n;
    final now = DateTime.now();
    final arc = cp.arc;
    ChartData? arcChart;
    if (arc != null) {
      try {
        final j = Map<String, dynamic>.from(arc.data)
          ..['house_system'] = arc.data['house_system'] ?? c.houseSystem;
        arcChart = ChartData.fromJson(j);
      } catch (_) {}
    }

    String fmt(DateTime d) =>
        '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

    final bool isMinor = _progressionMethod == 'minor';
    String methodLabel(String? method) => method == 'minor'
        ? l10n.chartMinorProgress
        : l10n.chartSecondaryProgress;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
      children: [
        _section(l10n.chartSectionProgressions, [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Wrap(
              spacing: 8,
              children: [
                ChoiceChip(
                  label: Text(l10n.chartSecondaryProgress),
                  selected: _progressionMethod == 'secondary',
                  onSelected: (_) =>
                      setState(() => _progressionMethod = 'secondary'),
                ),
                ChoiceChip(
                  label: Text(l10n.chartMinorProgress),
                  selected: isMinor,
                  onSelected: (_) =>
                      setState(() => _progressionMethod = 'minor'),
                ),
                Text(l10n.chartProgressHelp),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    l10n.chartTargetDate(fmt(_arcDate)),
                    style: TextStyle(color: FastTheme.text),
                  ),
                ),
                OutlinedButton(
                  onPressed: () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: _arcDate,
                      firstDate: DateTime(
                        c.meta.date.isNotEmpty && c.meta.date.contains('-')
                            ? int.tryParse(c.meta.date.split('-')[0]) ??
                                  now.year - 100
                            : now.year - 100,
                      ),
                      lastDate: DateTime(now.year + 60),
                    );
                    if (picked != null) {
                      setState(() => _arcDate = picked);
                    }
                  },
                  child: Text(l10n.chartPickDate),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  onPressed: cp.arcLoading
                      ? null
                      : () => cp.loadSolarArc(
                          fmt(_arcDate),
                          method: _progressionMethod,
                        ),
                  style: FilledButton.styleFrom(
                    backgroundColor: FastTheme.accentGold,
                  ),
                  child: Text(l10n.chartCalculate),
                ),
              ],
            ),
          ),
          if (cp.arcLoading)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Center(
                child: CircularProgressIndicator(color: FastTheme.accentGold),
              ),
            ),
          if (cp.arcError != null)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Text(
                cp.arcError!,
                style: const TextStyle(color: Colors.redAccent),
              ),
            ),
          if (arcChart != null) ...[
            const Divider(height: 1),
            const SizedBox(height: 12),
            Center(
              child: ChartWheel(
                data: arcChart,
                size: 320,
                title: methodLabel(
                  '${arc!.data['progression']?['method']}',
                ),
                subtitle: c.meta.place,
                initialDate: DateTime.parse(arc.targetDate),
                loadFrame: (date) async => ChartFrame(
                  data: ChartData.fromJson(
                    await _charts.progression(
                      natal: c,
                      targetDate: _dateText(date),
                      targetTime: _clockText(date),
                      method:
                          '${arc.data['progression']?['method'] ?? 'secondary'}',
                    ),
                  ),
                  title: methodLabel(
                    '${arc.data['progression']?['method']}',
                  ),
                  subtitle: c.meta.place,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Center(
              child: Text(
                l10n.chartProgressTitleWithDate(
                  methodLabel('${arc.data['progression']?['method']}'),
                  arc.targetDate,
                ),
                style: TextStyle(
                  color: FastTheme.text,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(height: 12),
            ...arcChart.planets.map(
              (p) => _row(
                chartPlanetLabel(l10n, p.name),
                '${_sign(p.sign)} ${_degMin(p.degree)} '
                '${p.retrograde ? 'R' : ''} • ${l10n.chartHouseNumber(p.house)}',
              ),
            ),
          ],
          if (arcChart == null && !cp.arcLoading)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Center(
                child: Text(
                  l10n.chartProgressHint,
                  style: TextStyle(color: FastTheme.textMuted),
                ),
              ),
            ),
        ]),
      ],
    );
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
                color: FastTheme.accentGold,
                fontWeight: FontWeight.w700,
              ),
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
          Expanded(
            child: Text(left, style: TextStyle(color: FastTheme.text)),
          ),
          const SizedBox(width: 10),
          Flexible(
            child: Text(
              right,
              textAlign: TextAlign.end,
              style: TextStyle(color: FastTheme.textMuted),
            ),
          ),
        ],
      ),
    );
  }
}
