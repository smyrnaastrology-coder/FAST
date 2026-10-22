import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../services/auth_service.dart';
import '../services/horary_service.dart';
import '../services/pro_service.dart';
import '../widgets/holavon_mark.dart';
import 'landing_screen.dart';

/// Horary Oracle: soru anının haritasıyla chat gibi cevap.
/// horary_mobile tam deneyiminin Holavon portu (TTS/STT hariç).
class HoraryScreen extends StatefulWidget {
  const HoraryScreen({super.key});

  @override
  State<HoraryScreen> createState() => _HoraryScreenState();
}

class _ChatMsg {
  final String role; // user | assistant
  String content;
  Map<String, dynamic>? meta;
  _ChatMsg(this.role, this.content, {this.meta});
}

class _HoraryScreenState extends State<HoraryScreen> {
  final _questionCtrl = TextEditingController();
  final _scroll = ScrollController();
  final List<_ChatMsg> _chat = [];

  String _category = 'general';
  String _asker = 'ben';
  double _lat = 38.4237; // varsayılan: İzmir
  double _lon = 27.1428;
  bool _locating = true;
  bool _busy = false;
  bool _showDetails = false;
  bool _showLanding = true;
  Map<String, dynamic>? _lastChart;
  String _lastQuestion = '';
  String? _error;

  static const _freeDailyLimit = 3;
  bool _isPro = false;
  int _usedToday = 0;
  int _creditsLeft = -1; // API credits_left (>=0 ise göster)

  @override
  void initState() {
    super.initState();
    _determinePosition();
    _loadQuota();
    WidgetsBinding.instance.addPostFrameCallback((_) => _maybeShowIntro());
  }

  @override
  void dispose() {
    _questionCtrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  String get _dayKey {
    final n = DateTime.now();
    return '${n.year}-${n.month.toString().padLeft(2, '0')}-${n.day.toString().padLeft(2, '0')}';
  }

  String get _quotaKey => 'horary_q_${AuthService.userId}_$_dayKey';

  Future<void> _loadQuota() async {
    final pro = await ProService.isPro();
    int used = 0;
    try {
      final prefs = await SharedPreferences.getInstance();
      used = prefs.getInt(_quotaKey) ?? 0;
    } catch (_) {}
    if (!mounted) return;
    setState(() {
      _isPro = pro;
      _usedToday = used;
    });
  }

  int get _remaining => (_freeDailyLimit - _usedToday).clamp(0, _freeDailyLimit);

  Future<void> _bumpQuota() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_quotaKey, _usedToday + 1);
    } catch (_) {}
    if (mounted) setState(() => _usedToday++);
  }

  void _openPaywall() {
    Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => const LandingScreen(asPaywall: true)))
        .then((_) => _loadQuota());
  }

  Future<bool> _confirmQuota(AppLocalizations l10n) async {
    if (_isPro) return true;
    if (_remaining > 0) return true;
    await _showLimitDialog(l10n);
    return false;
  }

  Future<void> _showLimitDialog(AppLocalizations l10n) async {
    if (!mounted) return;
    await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: FastTheme.bgSecondary,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18), side: BorderSide(color: FastTheme.accentGold.withValues(alpha: 0.4))),
        title: Row(children: [
          Icon(Icons.hourglass_bottom, color: FastTheme.accentGold),
          const SizedBox(width: 8),
          Expanded(child: Text(l10n.horaryLimitTitle, style: TextStyle(color: FastTheme.accentGold, fontSize: 17, fontWeight: FontWeight.w700))),
        ]),
        content: Text(l10n.horaryLimitDesc, style: TextStyle(color: FastTheme.textMuted, height: 1.4)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(l10n.horaryLimitLater, style: TextStyle(color: FastTheme.textDim))),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _openPaywall();
            },
            style: ElevatedButton.styleFrom(backgroundColor: FastTheme.accentGold),
            child: Text(l10n.proEntry, style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Future<void> _determinePosition() async {
    setState(() => _locating = true);
    try {
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied || perm == LocationPermission.deniedForever) {
        return; // varsayılan konumda kal
      }
      final pos = await Geolocator.getCurrentPosition();
      if (!mounted) return;
      setState(() {
        _lat = pos.latitude;
        _lon = pos.longitude;
      });
    } catch (_) {
      // varsayılan konum
    } finally {
      if (mounted) setState(() => _locating = false);
    }
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent + 200,
            duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
      }
    });
  }

  Future<void> _ask(AppLocalizations l10n) async {
    final q = _questionCtrl.text.trim();
    if (q.length < 2 || _busy) return;
    if (!await _confirmQuota(l10n)) return;
    setState(() {
      _chat.add(_ChatMsg('user', q));
      _lastQuestion = q;
      _busy = true;
      _error = null;
      _questionCtrl.clear();
      _showLanding = false;
    });
    _scrollDown();
    try {
      final res = await HoraryService.cast(
        question: q,
        lat: _lat,
        lon: _lon,
        lang: Localizations.localeOf(context).languageCode,
        category: _category,
        asker: _asker,
        history: _chat
            .where((m) => m.content.isNotEmpty)
            .map((m) => {'role': m.role, 'content': m.content})
            .toList(),
      );
      if (!mounted) return;
      if (!res.ok) {
        setState(() {
          _busy = false;
          _error = res.authError ? l10n.horaryAuthError : l10n.horaryError;
          _chat.add(_ChatMsg('assistant', res.authError ? l10n.horaryAuthError : l10n.horaryError));
        });
        _scrollDown();
        return;
      }
      final data = res.data;
      final credits = data['credits_left'];
      final verdict = (data['verdict'] ?? '').toString();
      if (verdict == 'NO_CREDITS') {
        setState(() {
          _busy = false;
          _creditsLeft = 0;
          _chat.add(_ChatMsg('assistant', l10n.horaryNoCredits));
        });
        _scrollDown();
        await _showLimitDialog(l10n);
        return;
      }
      final ans = (data['answer'] ?? verdict).toString();
      setState(() {
        _busy = false;
        _lastChart = data;
        if (credits is int) _creditsLeft = credits;
        _chat.add(_ChatMsg('assistant', ans, meta: data));
      });
      _scrollDown();
      await _bumpQuota();
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = l10n.horaryError;
        _chat.add(_ChatMsg('assistant', l10n.horaryError));
      });
      _scrollDown();
    }
  }

  DateTime? _timingTarget(Map<String, dynamic>? timing) {
    if (timing == null) return null;
    final txt = (timing['text'] ?? '').toString();
    final m = RegExp(r'(\d+)').firstMatch(txt);
    if (m == null) return null;
    final n = int.parse(m.group(1)!);
    final unit = (timing['unit'] ?? '').toString().toUpperCase();
    Duration? d;
    bool has(String s) => unit.contains(s) || txt.toUpperCase().contains(s);
    if (has('DAKIKA') || has('MINUTE') || has('MINUTO')) {
      d = Duration(minutes: n);
    } else if (has('SAAT') || has('HOUR') || has('HORA')) {
      d = Duration(hours: n);
    } else if (has('GÜN') || has('GUN') || has('DAY') || has('DÍA') || has('DIA')) {
      d = Duration(days: n);
    } else if (has('HAFTA') || has('WEEK') || has('SEMANA')) {
      d = Duration(days: n * 7);
    } else if (has('YIL') || has('YEAR') || has('AÑO') || has('ANO')) {
      d = Duration(days: n * 365);
    } else if (has('AY') || has('MONTH') || has('MES')) {
      d = Duration(days: n * 30);
    }
    if (d == null) return null;
    return DateTime.now().add(d);
  }

  String _dateStr(DateTime? t) {
    if (t == null) return '';
    return '${t.day.toString().padLeft(2, '0')}.${t.month.toString().padLeft(2, '0')}.${t.year}';
  }

  Color _verdictColor(String v) {
    final s = v.toLowerCase();
    if (s.contains('yes') || s == 'evet' || s.contains('sí') || s.contains('si')) return FastTheme.success;
    if (s.contains('no') || s == 'hayır' || s == 'hayir') return FastTheme.danger;
    return FastTheme.accentGold;
  }

  /// Kategoriye göre örnek sorular (FAST/Horary Oracle'daki gibi).
  List<String> _suggestions(AppLocalizations l10n) {
    final key = switch (_category) {
      'relationship' => l10n.horarySuggestRelationship,
      'job' => l10n.horarySuggestJob,
      'money' => l10n.horarySuggestMoney,
      'lost_object' => l10n.horarySuggestLostObject,
      'health' => l10n.horarySuggestHealth,
      _ => l10n.horarySuggestDefault,
    };
    return key.split('|').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
  }

  void _useSuggestion(String s) {
    setState(() {
      _showLanding = false;
      _questionCtrl.text = s;
    });
    _scrollDown();
  }

  Future<void> _copy(String txt) async {
    await Clipboard.setData(ClipboardData(text: txt));
    if (!mounted) return;
    final l10n = AppLocalizations.of(context);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${l10n.horaryCopy} ✓')));
  }

  /// "Doğru Soru Sormak" öğretisini bir kez göster.
  Future<void> _maybeShowIntro() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (prefs.getBool('holavon_horary_intro_shown') == true) return;
    } catch (_) {
      return;
    }
    if (!mounted) return;
    final l10n = AppLocalizations.of(context);
    var dontShow = false;
    await showDialog(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setS) => Dialog(
          backgroundColor: FastTheme.bgSecondary,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20), side: BorderSide(color: FastTheme.accentGold.withValues(alpha: 0.5))),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(gradient: LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]), shape: BoxShape.circle),
                    child: const Icon(Icons.auto_awesome, color: Color(0xFF1a1423), size: 28),
                  ),
                ),
                const SizedBox(height: 12),
                Center(child: Text(l10n.horaryIntroTitle, textAlign: TextAlign.center, style: TextStyle(color: FastTheme.accentGold, fontSize: 18, fontWeight: FontWeight.w700, height: 1.3))),
                const SizedBox(height: 8),
                Center(child: Text(l10n.horaryIntroSubtitle, textAlign: TextAlign.center, style: TextStyle(color: FastTheme.textMuted, fontSize: 13, fontStyle: FontStyle.italic))),
                const SizedBox(height: 16),
                Container(height: 1, color: FastTheme.border),
                const SizedBox(height: 16),
                ...[
                  l10n.horaryIntroR1,
                  l10n.horaryIntroR2,
                  l10n.horaryIntroR3,
                  l10n.horaryIntroR4,
                  l10n.horaryIntroR5,
                ].asMap().entries.map((e) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            width: 22,
                            height: 22,
                            decoration: BoxDecoration(
                              color: FastTheme.accentGold.withValues(alpha: 0.2),
                              shape: BoxShape.circle,
                              border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.4)),
                            ),
                            child: Center(child: Text('${e.key + 1}', style: TextStyle(color: FastTheme.accentGold, fontSize: 11, fontWeight: FontWeight.bold))),
                          ),
                          const SizedBox(width: 10),
                          Expanded(child: Text(e.value, style: TextStyle(color: FastTheme.textLight, fontSize: 13, height: 1.4))),
                        ],
                      ),
                    )),
                const SizedBox(height: 4),
                Center(child: Text(l10n.horaryIntroFooter, textAlign: TextAlign.center, style: TextStyle(color: FastTheme.accentGold, fontSize: 13, fontStyle: FontStyle.italic))),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Checkbox(
                      value: dontShow,
                      onChanged: (v) => setS(() => dontShow = v ?? false),
                      activeColor: FastTheme.accentGold,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                    ),
                    Expanded(child: Text(l10n.horaryIntroDontShow, style: TextStyle(color: FastTheme.textMuted, fontSize: 13))),
                  ],
                ),
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () async {
                      if (dontShow) {
                        try {
                          final prefs = await SharedPreferences.getInstance();
                          await prefs.setBool('holavon_horary_intro_shown', true);
                        } catch (_) {}
                      }
                      if (ctx.mounted) Navigator.pop(ctx);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: FastTheme.accentGold,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: Text(l10n.horaryIntroOk, style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold)),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bgSecondary,
        elevation: 0,
        iconTheme: IconThemeData(color: FastTheme.accentGold),
        title: Text(l10n.horaryTitle, style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700)),
        actions: [
          if (_creditsLeft >= 0)
            Padding(
              padding: const EdgeInsets.only(right: 4, top: 12),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: FastTheme.cardBg,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.4)),
                ),
                child: Center(child: Text('$_creditsLeft ${l10n.horaryCredits}', style: TextStyle(color: FastTheme.accentGold, fontSize: 10, fontWeight: FontWeight.bold))),
              ),
            ),
          if (_chat.isNotEmpty)
            IconButton(
              tooltip: l10n.horaryClear,
              onPressed: () => setState(() {
                _chat.clear();
                _lastChart = null;
                _showLanding = true;
                _showDetails = false;
                _lastQuestion = '';
                _questionCtrl.clear();
              }),
              icon: Icon(Icons.delete_outline, color: FastTheme.textDim),
            ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: _showLanding && _chat.isEmpty ? _landingView(l10n) : _chatView(l10n),
            ),
            _composer(l10n),
          ],
        ),
      ),
    );
  }

  // ---------- Landing (ilk açılış) ----------
  Widget _landingView(AppLocalizations l10n) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 12),
      children: [
        const SizedBox(height: 8),
        Center(
          child: Container(
            width: 84,
            height: 84,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]),
              boxShadow: [BoxShadow(color: FastTheme.accentGold.withValues(alpha: 0.3), blurRadius: 24)],
            ),
            child: HolavonLogo(size: 88, radius: 22, glow: 0.30),
          ),
        ),
        const SizedBox(height: 18),
        Text(l10n.horarySubtitle, textAlign: TextAlign.center, style: TextStyle(color: FastTheme.textMuted, fontSize: 14, height: 1.5)),
        const SizedBox(height: 22),
        _sectionLabel(l10n.horaryCategory, Icons.category_outlined),
        const SizedBox(height: 8),
        _categoryChips(l10n),
        const SizedBox(height: 16),
        _sectionLabel(l10n.horaryAsker, Icons.person_outline),
        const SizedBox(height: 8),
        _askerChips(l10n),
        const SizedBox(height: 16),
        _locationRow(l10n),
        const SizedBox(height: 18),
        Row(
          children: [
            Icon(Icons.lightbulb_outline, size: 14, color: FastTheme.accentGold),
            const SizedBox(width: 6),
            Text(l10n.horarySuggestLabel, style: TextStyle(color: FastTheme.textDim, fontSize: 12)),
          ],
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final s in _suggestions(l10n))
              ActionChip(
                label: Text(s, style: TextStyle(fontSize: 12, color: FastTheme.textLight)),
                backgroundColor: FastTheme.cardBg,
                side: BorderSide(color: FastTheme.border),
                onPressed: () => _useSuggestion(s),
              ),
          ],
        ),
        const SizedBox(height: 18),
        _quotaBadge(l10n),
      ],
    );
  }

  // ---------- Chat görünümü ----------
  Widget _chatView(AppLocalizations l10n) {
    final timing = _timingTarget(_lastChart?['timing'] is Map ? Map<String, dynamic>.from(_lastChart!['timing'] as Map) : null);
    return ListView(
      controller: _scroll,
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      children: [
        _topBar(l10n),
        // Konum uyarısı
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
          child: Row(children: [
            Icon(Icons.location_on, size: 14, color: FastTheme.warning),
            const SizedBox(width: 6),
            Expanded(child: Text(l10n.horaryLocationWarning, style: TextStyle(color: FastTheme.warning, fontSize: 11, fontStyle: FontStyle.italic))),
          ]),
        ),
        _categoryRow(l10n),
        if (_lastChart != null) _chartCard(l10n),
        if (timing != null) _timingCard(l10n, timing),
        if (_lastChart != null && _lastChart!['strictures'] is List && (_lastChart!['strictures'] as List).isNotEmpty) _detailsCard(l10n),
        const SizedBox(height: 4),
        ..._chat.map(_bubble),
        if (_busy) Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: LinearProgressIndicator(color: FastTheme.accentGold, backgroundColor: FastTheme.cardBg),
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  Widget _topBar(AppLocalizations l10n) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 4, 4, 4),
      child: Row(
        children: [
          _quotaBadge(l10n),
          const Spacer(),
          GestureDetector(
            onTap: _determinePosition,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: FastTheme.cardBg,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.4)),
              ),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.location_on, size: 14, color: FastTheme.accentGold),
                const SizedBox(width: 4),
                Text(_locating ? l10n.horaryLocationHint : '${_lat.toStringAsFixed(2)}, ${_lon.toStringAsFixed(2)}', style: TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                const SizedBox(width: 4),
                Icon(Icons.my_location, size: 12, color: FastTheme.accentGold),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _categoryRow(AppLocalizations l10n) {
    return SizedBox(
      height: 40,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 4),
        children: [
          for (final c in _cats(l10n))
            Padding(
              padding: const EdgeInsets.only(right: 6),
              child: ChoiceChip(
                label: Text(c['l']!, style: TextStyle(fontSize: 11, color: _category == c['k'] ? FastTheme.bg : FastTheme.textLight)),
                selected: _category == c['k'],
                selectedColor: FastTheme.accentGold,
                backgroundColor: FastTheme.cardBg,
                side: BorderSide(color: FastTheme.border),
                onSelected: (v) {
                  if (v) setState(() => _category = c['k']!);
                },
              ),
            ),
        ],
      ),
    );
  }

  Widget _bubble(_ChatMsg m) {
    final isUser = m.role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.82),
        decoration: BoxDecoration(
          color: isUser ? FastTheme.accentGold.withValues(alpha: 0.9) : FastTheme.cardBg,
          borderRadius: BorderRadius.circular(14),
          border: isUser ? null : Border(left: BorderSide(color: FastTheme.accentGold, width: 3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(m.content, style: TextStyle(color: isUser ? FastTheme.bg : FastTheme.textLight, height: 1.5, fontWeight: isUser ? FontWeight.bold : FontWeight.normal)),
            if (!isUser) ...[
              const SizedBox(height: 6),
              GestureDetector(
                onTap: () => _copy(m.content),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.copy, size: 14, color: FastTheme.textDim),
                  const SizedBox(width: 4),
                  Builder(builder: (ctx) => Text(AppLocalizations.of(ctx).horaryCopy, style: TextStyle(color: FastTheme.textDim, fontSize: 11))),
                ]),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _chartCard(AppLocalizations l10n) {
    final data = _lastChart!;
    final h = data['houses'] is Map ? data['houses'] as Map : const {};
    final p = data['planets'] is Map ? data['planets'] as Map : const {};
    final ascSign = (h['asc_sign'] ?? '').toString();
    final ascDeg = h['asc'] != null ? ((h['asc'] as num) % 30).toStringAsFixed(1) : '';
    final moon = p['Moon'] is Map ? p['Moon'] as Map : const {};
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: FastTheme.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: FastTheme.border),
        ),
        child: Row(
          children: [
            SizedBox(width: 72, height: 72, child: CustomPaint(painter: MiniChartPainter(data))),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${l10n.horaryAsc}: $ascSign $ascDeg°', style: TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 3),
                  Text('${l10n.horaryMoon}: ${(moon['sign'] ?? '').toString()} ${moon['deg'] != null ? (moon['deg'] as num).toStringAsFixed(1) : ''}°', style: TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                  const SizedBox(height: 3),
                  Text('${(data['verdict'] ?? '').toString()}', style: TextStyle(color: _verdictColor((data['verdict'] ?? '').toString()), fontSize: 12, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _timingCard(AppLocalizations l10n, DateTime target) {    final timingText = (_lastChart?['timing'] is Map) ? ((_lastChart!['timing'] as Map)['text'] ?? '').toString() : '';
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: FastTheme.cardBg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.5)),
        ),
        child: Row(children: [
          Icon(Icons.timer_outlined, size: 16, color: FastTheme.accentGold),
          const SizedBox(width: 8),
          Expanded(child: Text(timingText, style: TextStyle(color: FastTheme.textLight, fontSize: 11, fontWeight: FontWeight.w600))),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(color: FastTheme.accentGold, borderRadius: BorderRadius.circular(20)),
            child: Text(_dateStr(target), style: TextStyle(color: FastTheme.bg, fontSize: 11, fontWeight: FontWeight.bold)),
          ),
        ]),
      ),
    );
  }

  Widget _detailsCard(AppLocalizations l10n) {
    final strictures = (_lastChart!['strictures'] as List);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: FastTheme.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: FastTheme.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            GestureDetector(
              onTap: () => setState(() => _showDetails = !_showDetails),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(_showDetails ? Icons.expand_less : Icons.expand_more, size: 16, color: FastTheme.accentGold),
                  Text(_showDetails ? l10n.horaryDetailsHide : l10n.horaryDetailsShow, style: TextStyle(color: FastTheme.accentGold, fontSize: 11)),
                ],
              ),
            ),
            if (_showDetails)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: strictures.map((s) {
                    final m = s is Map ? s : const {};
                    final level = (m['level'] ?? '').toString();
                    final color = level == 'critical'
                        ? FastTheme.danger
                        : level == 'warning'
                            ? FastTheme.warning
                            : FastTheme.accentGold;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(width: 6, height: 6, margin: const EdgeInsets.only(top: 5, right: 6), decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
                          Expanded(child: Text('${m['meaning'] ?? ''}', style: TextStyle(color: FastTheme.textMuted, fontSize: 12, height: 1.4))),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _composer(AppLocalizations l10n) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      decoration: BoxDecoration(
        color: FastTheme.bgSecondary,
        border: Border(top: BorderSide(color: FastTheme.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _questionCtrl,
              minLines: 1,
              maxLines: 4,
              style: TextStyle(color: FastTheme.textLight, fontSize: 15),
              decoration: InputDecoration(
                hintText: l10n.horaryQuestionHint,
                hintStyle: TextStyle(color: FastTheme.textDim, fontSize: 14),
                filled: true,
                fillColor: FastTheme.cardBg,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide(color: FastTheme.border)),
                enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide(color: FastTheme.border)),
                focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide(color: FastTheme.accentGold)),
              ),
              onSubmitted: (_) => _ask(l10n),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: BoxDecoration(
              color: _busy ? FastTheme.textDim : FastTheme.accentGold,
              shape: BoxShape.circle,
            ),
            child: IconButton(
              onPressed: _busy ? null : () => _ask(l10n),
              icon: Icon(Icons.arrow_upward, color: FastTheme.bg, size: 20),
            ),
          ),
        ],
      ),
    );
  }

  // ---------- Yardımcı bileşenler ----------
  Widget _sectionLabel(String text, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 16, color: FastTheme.accentGold),
        const SizedBox(width: 6),
        Text(text, style: TextStyle(color: FastTheme.textLight, fontSize: 13, fontWeight: FontWeight.w600)),
      ],
    );
  }

  List<Map<String, String>> _cats(AppLocalizations l10n) => [
        {'k': 'general', 'l': l10n.horaryCatGeneral},
        {'k': 'relationship', 'l': l10n.horaryCatRelationship},
        {'k': 'money', 'l': l10n.horaryCatMoney},
        {'k': 'job', 'l': l10n.horaryCatJob},
        {'k': 'health', 'l': l10n.horaryCatHealth},
        {'k': 'lost_object', 'l': l10n.horaryCatLostObject},
        {'k': 'missing_person', 'l': l10n.horaryCatMissingPerson},
        {'k': 'house_property', 'l': l10n.horaryCatHouse},
        {'k': 'child', 'l': l10n.horaryCatChild},
        {'k': 'pet', 'l': l10n.horaryCatPet},
      ];

  Widget _categoryChips(AppLocalizations l10n) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final c in _cats(l10n))
          ChoiceChip(
            label: Text(c['l']!, style: TextStyle(fontSize: 12, color: _category == c['k'] ? FastTheme.bg : FastTheme.textLight)),
            selected: _category == c['k'],
            selectedColor: FastTheme.accentGold,
            backgroundColor: FastTheme.cardBg,
            side: BorderSide(color: FastTheme.border),
            onSelected: (v) {
              if (v) setState(() => _category = c['k']!);
            },
          ),
      ],
    );
  }

  Widget _askerChips(AppLocalizations l10n) {
    return Row(
      children: [
        _askerChip(l10n.horaryAskerMe, 'ben'),
        const SizedBox(width: 8),
        _askerChip(l10n.horaryAskerOther, 'baskasi'),
      ],
    );
  }

  Widget _askerChip(String label, String value) {
    final sel = _asker == value;
    return Expanded(
      child: ChoiceChip(
        label: Center(child: Text(label, style: TextStyle(fontSize: 13, color: sel ? FastTheme.bg : FastTheme.textLight))),
        selected: sel,
        selectedColor: FastTheme.accentGold,
        backgroundColor: FastTheme.cardBg,
        side: BorderSide(color: FastTheme.border),
        onSelected: (v) {
          if (v) setState(() => _asker = value);
        },
      ),
    );
  }

  Widget _locationRow(AppLocalizations l10n) {
    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: _determinePosition,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: FastTheme.cardBg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: FastTheme.border),
        ),
        child: Row(
          children: [
            Icon(Icons.location_on, size: 16, color: FastTheme.accentGold),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                _locating ? l10n.horaryLocationHint : '${_lat.toStringAsFixed(2)}, ${_lon.toStringAsFixed(2)}',
                style: TextStyle(color: FastTheme.textMuted, fontSize: 12.5),
              ),
            ),
            Icon(Icons.my_location, size: 14, color: FastTheme.textDim),
          ],
        ),
      ),
    );
  }

  Widget _quotaBadge(AppLocalizations l10n) {
    if (_isPro) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.workspace_premium, size: 14, color: FastTheme.accentGold),
          const SizedBox(width: 6),
          Text(l10n.proBenefitHorary, style: TextStyle(color: FastTheme.accentGold, fontSize: 12)),
        ],
      );
    }
    final out = _remaining <= 0;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(out ? Icons.lock_outline : Icons.timelapse, size: 14, color: out ? FastTheme.danger : FastTheme.textDim),
        const SizedBox(width: 6),
        Text('${l10n.horaryQuota} $_remaining/$_freeDailyLimit', style: TextStyle(color: out ? FastTheme.danger : FastTheme.textDim, fontSize: 12)),
        if (out) ...[
          const SizedBox(width: 6),
          GestureDetector(
            onTap: _openPaywall,
            child: Text(l10n.proEntry, style: TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w700)),
          ),
        ],
      ],
    );
  }
}

/// Mini doğum haritası (12 ev + gezegen noktaları).
class MiniChartPainter extends CustomPainter {
  final Map<String, dynamic> data;
  MiniChartPainter(this.data);
  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2, cy = size.height / 2, r = size.width / 2 - 4;
    final bg = Paint()..color = FastTheme.cardBg..style = PaintingStyle.fill;
    final border = Paint()..color = FastTheme.accentGold.withValues(alpha: 0.6)..style = PaintingStyle.stroke..strokeWidth = 1.2;
    canvas.drawCircle(Offset(cx, cy), r, bg);
    canvas.drawCircle(Offset(cx, cy), r, border);
    canvas.drawCircle(Offset(cx, cy), r * 0.62, border);
    final asc = ((data['houses'] is Map ? (data['houses'] as Map)['asc'] : 0) ?? 0).toDouble();
    for (int i = 0; i < 12; i++) {
      final ang = (asc + i * 30) * math.pi / 180 - math.pi / 2;
      final p1 = Offset(cx + r * 0.62 * math.cos(ang), cy + r * 0.62 * math.sin(ang));
      final p2 = Offset(cx + r * math.cos(ang), cy + r * math.sin(ang));
      canvas.drawLine(p1, p2, border);
    }
    final ascAng = asc * math.pi / 180 - math.pi / 2;
    canvas.drawLine(Offset(cx, cy), Offset(cx + r * math.cos(ascAng), cy + r * math.sin(ascAng)), Paint()..color = FastTheme.accentGold..strokeWidth = 2);
    final planets = data['planets'];
    if (planets is Map) {
      final colors = {
        'Sun': Colors.orange, 'Moon': Colors.white, 'Mercury': Colors.yellowAccent,
        'Venus': Colors.pinkAccent, 'Mars': Colors.redAccent, 'Jupiter': Colors.lightBlue, 'Saturn': Colors.grey,
      };
      planets.forEach((name, info) {
        if (!colors.containsKey(name) || info is! Map) return;
        final lon = (info['lon'] ?? 0).toDouble();
        final ang = lon * math.pi / 180 - math.pi / 2;
        final pr = r * 0.78;
        canvas.drawCircle(Offset(cx + pr * math.cos(ang), cy + pr * math.sin(ang)), 3, Paint()..color = colors[name]!);
      });
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
