import 'dart:async';
import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:provider/provider.dart';
import '../models/chart_frame.dart';
import '../providers/social_provider.dart';
import '../widgets/chart_wheel.dart';
import 'auth_screen.dart';
import 'handle_claim_screen.dart';
import 'create_post_screen.dart';

class ChartExplorerScreen extends StatefulWidget {
  final ChartFrame initial;
  final DateTime initialDate;
  final ChartFrameLoader? loadFrame;
  final bool lightTheme;
  final List<ChartTimeUnit> timeUnits;
  const ChartExplorerScreen({
    super.key,
    required this.initial,
    required this.initialDate,
    this.loadFrame,
    this.lightTheme = false,
    this.timeUnits = ChartTimeUnit.values,
  });
  @override
  State<ChartExplorerScreen> createState() => _ChartExplorerScreenState();
}

class _ChartExplorerScreenState extends State<ChartExplorerScreen> {
  final _captureKey = GlobalKey();
  final _transform = TransformationController();
  final _cache = <DateTime, ChartFrame>{};
  late ChartFrame _frame;
  late DateTime _date;
  late DateTime _requested;
  late bool _light;
  ChartTimeUnit _unit = ChartTimeUnit.day;
  int _count = 1;
  int _sequence = 0;
  Timer? _debounce;
  bool _busy = false;
  bool _sharing = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _frame = widget.initial;
    _date = _requested = widget.initialDate;
    _cache[_date] = _frame;
    _light = widget.lightTheme;
    if (!widget.timeUnits.contains(_unit)) _unit = widget.timeUnits.first;
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _transform.dispose();
    super.dispose();
  }

  String _format(DateTime date) =>
      '${date.day.toString().padLeft(2, '0')}.'
      '${date.month.toString().padLeft(2, '0')}.${date.year} '
      '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';

  void _request(DateTime date) {
    final loader = widget.loadFrame;
    if (loader == null) return;
    _debounce?.cancel();
    final sequence = ++_sequence;
    final cached = _cache[date];
    if (cached != null) {
      setState(() {
        _frame = cached;
        _date = _requested = date;
        _busy = false;
        _error = null;
      });
      return;
    }
    setState(() {
      _requested = date;
      _busy = true;
      _error = null;
    });
    _debounce = Timer(const Duration(milliseconds: 180), () async {
      try {
        final frame = await loader(date);
        if (!mounted || sequence != _sequence) return;
        if (_cache.length >= 120) _cache.remove(_cache.keys.first);
        _cache[date] = frame;
        setState(() {
          _frame = frame;
          _date = date;
        });
      } catch (_) {
        if (!mounted || sequence != _sequence) return;
        setState(() {
          _requested = _date;
          _error = 'Hesaplama tamamlanamadı. Tekrar deneyin.';
        });
      } finally {
        if (mounted && sequence == _sequence) setState(() => _busy = false);
      }
    });
  }

  Future<void> _pick() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _requested,
      firstDate: DateTime(math.min(1800, _requested.year)),
      lastDate: DateTime(math.max(2300, _requested.year), 12, 31),
    );
    if (picked == null || !mounted) return;
    final clock = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_requested),
    );
    if (clock != null && mounted) {
      _request(
        DateTime(
          picked.year,
          picked.month,
          picked.day,
          clock.hour,
          clock.minute,
        ),
      );
    }
  }

  Future<void> _share() async {
    setState(() => _sharing = true);
    try {
      final social = context.read<SocialProvider>();
      if (!social.enabled) {
        throw StateError('Holavon bağlantısı kullanılamıyor.');
      }
      if (!social.signedIn) {
        await Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const AuthScreen(force: true)),
        );
      }
      if (!mounted || !social.signedIn) return;
      if (!social.hasHandle) {
        await social.refreshProfile();
        if (!mounted) return;
        if (!social.hasHandle) {
          await Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) =>
                  HandleClaimScreen(onClaimed: () => social.refreshProfile()),
            ),
          );
        }
      }
      if (!mounted || !social.hasHandle) return;
      await WidgetsBinding.instance.endOfFrame;
      if (!mounted) return;
      final boundary =
          _captureKey.currentContext!.findRenderObject()
              as RenderRepaintBoundary;
      final image = await boundary.toImage(
        pixelRatio: math.min(3, 1500 / boundary.size.width),
      );
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      image.dispose();
      if (bytes == null || !mounted) return;
      final posted = await Navigator.of(context).push<bool>(
        MaterialPageRoute(
          builder: (_) => CreatePostScreen(
            initialBytes: bytes.buffer.asUint8List(),
            isChart: true,
          ),
        ),
      );
      if (posted == true) await social.refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Harita paylaşımı açılamadı: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _sharing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bg = _light ? Colors.white : const Color(0xFF0D1017);
    final fg = _light ? Colors.black87 : Colors.white;
    final theme = _light ? ThemeData.light() : ThemeData.dark();
    return Theme(
      data: theme,
      child: Scaffold(
        backgroundColor: bg,
        appBar: AppBar(
          backgroundColor: bg,
          foregroundColor: fg,
          title: Text(_frame.title, style: const TextStyle(fontSize: 16)),
          actions: [
            IconButton(
              tooltip: 'Harita: siyah / beyaz',
              icon: Icon(_light ? Icons.dark_mode : Icons.light_mode),
              onPressed: () => setState(() => _light = !_light),
            ),
            IconButton(
              tooltip: 'Yakınlaştırmayı sıfırla',
              icon: const Icon(Icons.fit_screen),
              onPressed: () => _transform.value = Matrix4.identity(),
            ),
            IconButton(
              tooltip: 'Holavon’da paylaş',
              icon: const Icon(Icons.share_outlined),
              onPressed: _busy || _sharing ? null : _share,
            ),
          ],
        ),
        body: SafeArea(
          child: Column(
            children: [
              if (widget.loadFrame != null)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: Row(
                    children: [
                      IconButton(
                        tooltip: 'Geri',
                        icon: const Icon(Icons.chevron_left),
                        onPressed: () =>
                            _request(stepChartTime(_requested, _unit, -_count)),
                      ),
                      Expanded(
                        child: DropdownButton<int>(
                          isExpanded: true,
                          value: _count,
                          items: List.generate(
                            30,
                            (i) => DropdownMenuItem(
                              value: i + 1,
                              child: Text('${i + 1}'),
                            ),
                          ),
                          onChanged: (v) {
                            if (v != null) setState(() => _count = v);
                          },
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        flex: 2,
                        child: DropdownButton<ChartTimeUnit>(
                          isExpanded: true,
                          value: _unit,
                          items:
                              const [
                                    DropdownMenuItem(
                                      value: ChartTimeUnit.minute,
                                      child: Text('Dakika'),
                                    ),
                                    DropdownMenuItem(
                                      value: ChartTimeUnit.hour,
                                      child: Text('Saat'),
                                    ),
                                    DropdownMenuItem(
                                      value: ChartTimeUnit.day,
                                      child: Text('Gün'),
                                    ),
                                    DropdownMenuItem(
                                      value: ChartTimeUnit.month,
                                      child: Text('Ay'),
                                    ),
                                    DropdownMenuItem(
                                      value: ChartTimeUnit.year,
                                      child: Text('Yıl'),
                                    ),
                                  ]
                                  .where(
                                    (item) =>
                                        widget.timeUnits.contains(item.value),
                                  )
                                  .toList(),
                          onChanged: (v) {
                            if (v != null) setState(() => _unit = v);
                          },
                        ),
                      ),
                      IconButton(
                        tooltip: 'İleri',
                        icon: const Icon(Icons.chevron_right),
                        onPressed: () =>
                            _request(stepChartTime(_requested, _unit, _count)),
                      ),
                    ],
                  ),
                ),
              if (_busy || _sharing)
                const LinearProgressIndicator(minHeight: 2),
              if (_busy) Text('Hesaplanıyor: ${_format(_requested)}'),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.all(8),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: Colors.redAccent),
                  ),
                ),
              Expanded(
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final extent = math.min(
                      constraints.maxWidth,
                      math.max(100.0, constraints.maxHeight - 100),
                    );
                    return Center(
                      child: InteractiveViewer(
                        transformationController: _transform,
                        minScale: 0.7,
                        maxScale: 8,
                        boundaryMargin: const EdgeInsets.all(200),
                        child: RepaintBoundary(
                          key: _captureKey,
                          child: ColoredBox(
                            color: bg,
                            child: SizedBox(
                              width: extent,
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Padding(
                                    padding: const EdgeInsets.fromLTRB(
                                      12,
                                      8,
                                      12,
                                      2,
                                    ),
                                    child: Text(
                                      _frame.title,
                                      textAlign: TextAlign.center,
                                      style: TextStyle(
                                        color: fg,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                  Text(
                                    _format(_date),
                                    style: TextStyle(color: fg),
                                  ),
                                  if (_frame.subtitle.isNotEmpty)
                                    Padding(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 12,
                                      ),
                                      child: Text(
                                        _frame.subtitle,
                                        textAlign: TextAlign.center,
                                        style: TextStyle(
                                          color: fg,
                                          fontSize: 11,
                                        ),
                                      ),
                                    ),
                                  ChartWheel(
                                    data: _frame.data,
                                    outerPlanets: _frame.outerPlanets,
                                    outerHouses: _frame.outerHouses,
                                    size: extent,
                                    lightTheme: _light,
                                    showControls: false,
                                  ),
                                  Text(
                                    'HOLAVON',
                                    style: TextStyle(
                                      color: fg,
                                      fontSize: 10,
                                      letterSpacing: 3,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
              TextButton.icon(
                onPressed: widget.loadFrame == null ? null : _pick,
                icon: const Icon(Icons.edit_calendar),
                label: Text(_format(_date)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
