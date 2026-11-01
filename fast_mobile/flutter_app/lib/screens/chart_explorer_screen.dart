import 'dart:async';
import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:provider/provider.dart';
import '../models/chart_frame.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
import '../widgets/chart_wheel.dart';
import '../widgets/chart_wheel_style.dart';
import '../widgets/chart_info_panel.dart';
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
  Timer? _timer;
  bool _busy = false;
  bool _sharing = false;
  bool _playing = false;
  double _speed = 1.0;
  String? _error;

  /// Otomatik oynatma aralığı: 1× hızda ~1.8 sn'de bir adım.
  Duration get _tickInterval =>
      Duration(milliseconds: (1800 / _speed).round());

  void _syncTimer() {
    _timer?.cancel();
    _timer = null;
    if (!_playing || widget.loadFrame == null) return;
    _timer = Timer.periodic(_tickInterval, (_) {
      if (!mounted || !_playing) return;
      // Hesaplama sürerken adım atlanır; üst üste istek birikmez.
      if (_busy) return;
      _request(stepChartTime(_requested, _unit, _count));
    });
  }

  void _togglePlay() {
    if (widget.loadFrame == null) return;
    setState(() => _playing = !_playing);
    _syncTimer();
    if (_playing && !_busy) {
      _request(stepChartTime(_requested, _unit, _count));
    }
  }

  void _setSpeed(double value) {
    if (value == _speed) return;
    setState(() => _speed = value);
    if (_playing) _syncTimer();
  }

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
    _timer?.cancel();
    _transform.dispose();
    super.dispose();
  }

  String _format(DateTime date) =>
      '${date.day.toString().padLeft(2, '0')}.'
      '${date.month.toString().padLeft(2, '0')}.${date.year} '
      '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';

  /// Birim adının yerelleştirilmiş karşılığı.
  String _unitLabel(AppLocalizations l10n, ChartTimeUnit unit) {
    switch (unit) {
      case ChartTimeUnit.minute:
        return l10n.chartUnitMinute;
      case ChartTimeUnit.hour:
        return l10n.chartUnitHour;
      case ChartTimeUnit.day:
        return l10n.chartUnitDay;
      case ChartTimeUnit.month:
        return l10n.chartUnitMonth;
      case ChartTimeUnit.year:
        return l10n.chartUnitYear;
    }
  }

  static const List<int> _countPresets = [1, 2, 3, 4, 5, 7, 10, 15, 20, 30];

  /// Adım sayısı + birim seçimini tek düğmede toplayan alt sayfa.
  Future<void> _openStepSheet() async {
    final l10n = AppLocalizations.of(context);
    final fg = _light ? Colors.black87 : Colors.white;
    final counts = ({..._countPresets, _count}.toList()..sort());
    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: _light ? Colors.white : const Color(0xFF161A23),
      showDragHandle: true,
      builder: (sheetCtx) => Theme(
        data: _light ? ThemeData.light() : ThemeData.dark(),
        child: StatefulBuilder(
          builder: (ctx, setSheetState) {
            void apply(VoidCallback change) {
              setState(change);
              setSheetState(() {});
            }

            return SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            l10n.chartExplorerTimeStep,
                            style: TextStyle(
                              color: fg,
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        TextButton(
                          onPressed: () => Navigator.of(sheetCtx).pop(),
                          child: Text(l10n.chartExplorerDone),
                        ),
                      ],
                    ),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final n in counts)
                          ChoiceChip(
                            label: Text('$n'),
                            selected: _count == n,
                            onSelected: (_) => apply(() => _count = n),
                          ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final u in ChartTimeUnit.values)
                          if (widget.timeUnits.contains(u))
                            ChoiceChip(
                              label: Text(_unitLabel(l10n, u)),
                              selected: _unit == u,
                              onSelected: (_) => apply(() => _unit = u),
                            ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

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
          _error = AppLocalizations.of(context).chartExplorerCalcError;
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
    final l10n = AppLocalizations.of(context);
    setState(() => _sharing = true);
    try {
      final social = context.read<SocialProvider>();
      if (!social.enabled) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(l10n.chartExplorerSocialUnavailable)),
          );
        }
        return;
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
          SnackBar(content: Text(l10n.chartExplorerShareError('$e'))),
        );
      }
    } finally {
      if (mounted) setState(() => _sharing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final bg = _light ? Colors.white : const Color(0xFF0D1017);
    final fg = _light ? Colors.black87 : Colors.white;
    final theme = _light ? ThemeData.light() : ThemeData.dark();
    final chartStyle = ChartWheelStyle.of(_light);
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
              tooltip: l10n.chartExplorerThemeTooltip,
              icon: Icon(_light ? Icons.dark_mode : Icons.light_mode),
              onPressed: () => setState(() => _light = !_light),
            ),
            IconButton(
              tooltip: l10n.chartExplorerResetZoom,
              icon: const Icon(Icons.fit_screen),
              onPressed: () => _transform.value = Matrix4.identity(),
            ),
            IconButton(
              tooltip: l10n.chartExplorerShare,
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
                        tooltip: l10n.chartExplorerBack,
                        icon: const Icon(Icons.chevron_left),
                        onPressed: () =>
                            _request(stepChartTime(_requested, _unit, -_count)),
                      ),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: _busy ? null : _openStepSheet,
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 4,
                            ),
                            minimumSize: const Size(0, 38),
                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            visualDensity: VisualDensity.compact,
                            foregroundColor: fg,
                            side: BorderSide(
                              color: fg.withValues(alpha: 0.28),
                            ),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Flexible(
                                child: Text(
                                  '$_count × ${_unitLabel(l10n, _unit)}',
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontSize: 12),
                                ),
                              ),
                              const Icon(Icons.expand_more, size: 16),
                            ],
                          ),
                        ),
                      ),
                      IconButton(
                        tooltip: l10n.chartExplorerForward,
                        icon: const Icon(Icons.chevron_right),
                        onPressed: () =>
                            _request(stepChartTime(_requested, _unit, _count)),
                      ),
                      IconButton(
                        tooltip: _playing
                            ? l10n.chartExplorerPause
                            : l10n.chartExplorerPlay,
                        icon: Icon(
                          _playing
                              ? Icons.pause_circle_filled
                              : Icons.play_circle_filled,
                        ),
                        color: _playing ? Colors.amberAccent : null,
                        onPressed: _togglePlay,
                      ),
                    ],
                  ),
                ),
              if (widget.loadFrame != null)
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 12, 0),
                  child: Row(
                    children: [
                      Text(
                        l10n.chartExplorerSpeed,
                        style: TextStyle(fontSize: 11, color: fg),
                      ),
                      Expanded(
                        child: Slider(
                          value: _speed,
                          min: 0.5,
                          max: 4,
                          divisions: 7,
                          label: '${_speed.toStringAsFixed(1)}×',
                          onChanged: _setSpeed,
                        ),
                      ),
                      SizedBox(
                        width: 38,
                        child: Text(
                          '${_speed.toStringAsFixed(1)}×',
                          textAlign: TextAlign.right,
                          style: TextStyle(fontSize: 11, color: fg),
                        ),
                      ),
                    ],
                  ),
                ),
              if (_busy || _sharing)
                const LinearProgressIndicator(minHeight: 2),
              if (_busy) Text(l10n.chartExplorerCalculating(_format(_requested))),
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
                    // Bilgi paneli + alt marka satırı için pay bırakılır;
                    // aksi halde sütun taşar.
                    final extent = math.min(
                      constraints.maxWidth,
                      math.max(100.0, constraints.maxHeight - 150),
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
                                      10,
                                      8,
                                      10,
                                      4,
                                    ),
                                    child: Row(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Expanded(
                                          child: Align(
                                            alignment: Alignment.topLeft,
                                            child: ChartInfoPanel(
                                              data: _frame.data,
                                              style: chartStyle,
                                              title: _frame.isBiWheel
                                                  ? (_frame.data.meta.name ??
                                                        '')
                                                  : _frame.title,
                                              subtitle: _frame.isBiWheel
                                                  ? _frame.data.meta.place
                                                  : _frame.subtitle,
                                              fontSize: 9,
                                            ),
                                          ),
                                        ),
                                        if (_frame.outerData != null)
                                          const SizedBox(width: 12),
                                        if (_frame.outerData != null)
                                          Expanded(
                                            child: Align(
                                              alignment: Alignment.topRight,
                                              child: ChartInfoPanel(
                                                data: _frame.outerData!,
                                                style: chartStyle,
                                                title: _frame.outerTitle,
                                                subtitle: _frame.outerSubtitle,
                                                fontSize: 9,
                                                alignEnd: true,
                                              ),
                                            ),
                                          ),
                                      ],
                                    ),
                                  ),
                                  ChartWheel(
                                    data: _frame.data,
                                    outerPlanets: _frame.outerPlanets,
                                    outerHouses: _frame.outerHouses,
                                    outerData: _frame.outerData,
                                    size: extent,
                                    lightTheme: _light,
                                    style: chartStyle,
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
