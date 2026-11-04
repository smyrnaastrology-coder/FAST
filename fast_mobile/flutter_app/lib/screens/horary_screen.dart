import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../services/horary_service.dart';
import '../services/horary_localization.dart';
import '../services/revenuecat_service.dart';
import '../widgets/holavon_mark.dart';
import '../widgets/horary_localized_detail.dart';
import 'landing_screen.dart';

/// Horary Oracle: soru anının haritasıyla chat gibi cevap.
/// horary_mobile tam deneyiminin Holavon portu (TTS/STT hariç).
class HoraryScreen extends StatefulWidget {
  const HoraryScreen({super.key, this.quotaLoader});

  /// Optional quota source for isolated widget tests.
  @visibleForTesting
  final Future<HoraryResult> Function()? quotaLoader;

  @override
  State<HoraryScreen> createState() => _HoraryScreenState();
}

class _ChatMsg {
  final String role; // user | assistant
  String content;
  Map<String, dynamic>? meta;
  _ChatMsg(this.role, this.content, {this.meta});
}

class _HoraryScreenState extends State<HoraryScreen> with WidgetsBindingObserver {
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

  bool _isPro = false;
  bool _quotaReady = false;
  bool _quotaError = false;
  int _remaining = 0;
  int _quotaLimit = 3;
  int _credits = 0;
  DateTime? _resetAt;
  int _quotaLoadVersion = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _determinePosition();
    _loadQuota();
    _loadChat();
    WidgetsBinding.instance.addPostFrameCallback((_) => _maybeShowIntro());
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _questionCtrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _loadQuota(refresh: true);
  }

  Future<HoraryResult> _loadQuota({bool refresh = false}) async {
    final version = ++_quotaLoadVersion;
    final result = await (widget.quotaLoader?.call() ?? HoraryService.quota());
    if (mounted && version == _quotaLoadVersion) {
      setState(() {
        _quotaReady = result.ok;
        _quotaError = !result.ok;
        if (result.ok) {
          _isPro = result.data['is_pro'] as bool;
          _remaining = result.data['remaining'] as int;
          _quotaLimit = result.data['limit'] as int;
          _credits = (result.data['credits'] as int?) ?? 0;
          _resetAt = DateTime.tryParse((result.data['reset_at'] ?? '').toString());
        }
      });
    }
    return result;
  }

  void _openPaywall() {
    Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => const LandingScreen(asPaywall: true)))
        .then((_) => _loadQuota());
  }

  Future<bool> _confirmQuota(AppLocalizations l10n) async {
    final quota = await _loadQuota(refresh: true);
    if (!mounted) return false;
    if (!quota.ok) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(quota.authError ? l10n.horaryAuthError : l10n.horaryQuotaUnavailable),
      ));
      return false;
    }
    final remaining = quota.data['remaining'] as int;
    final credits = (quota.data['credits'] as int?) ?? 0;
    if (remaining + credits > 0) return true;
    await _showLimitDialog(l10n);
    return false;
  }

  String? _resetLabel() {
    final at = _resetAt;
    if (at == null) return null;
    var diff = at.difference(DateTime.now().toUtc());
    if (diff.isNegative) diff = Duration.zero;
    final hours = diff.inHours.toString().padLeft(2, '0');
    final minutes = (diff.inMinutes % 60).toString().padLeft(2, '0');
    return '$hours:$minutes';
  }

  Widget _dialogStat(IconData icon, String text, {bool danger = false}) {
    return Row(
      children: [
        Icon(icon, size: 16, color: danger ? FastTheme.danger : FastTheme.accentGold),
        const SizedBox(width: 8),
        Expanded(
          child: Text(text,
              style: TextStyle(
                  color: danger ? FastTheme.danger : FastTheme.textMuted,
                  fontSize: 13)),
        ),
      ],
    );
  }

  Future<void> _showLimitDialog(AppLocalizations l10n) async {
    if (!mounted) return;
    final reset = _isPro ? _resetLabel() : null;
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
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _isPro ? l10n.horaryProCreditDialogDesc : l10n.horaryCreditDialogDesc,
              style: TextStyle(color: FastTheme.textMuted, height: 1.4),
            ),
            const SizedBox(height: 14),
            _dialogStat(Icons.timelapse,
                '${_isPro ? l10n.horaryQuotaPro : l10n.horaryQuotaFree} $_remaining/$_quotaLimit',
                danger: true),
            const SizedBox(height: 6),
            _dialogStat(Icons.confirmation_number_outlined,
                l10n.horaryCreditBalance(_credits)),
            if (reset != null) ...[
              const SizedBox(height: 6),
              _dialogStat(Icons.schedule, l10n.horaryResetIn(reset)),
            ],
          ],
        ),
        actionsOverflowDirection: VerticalDirection.down,
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text(_isPro ? l10n.horaryCreditContinueTomorrow : l10n.horaryLimitLater,
                style: TextStyle(color: FastTheme.textDim)),
          ),
          if (!_isPro)
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                _openPaywall();
              },
              child: Text(l10n.proEntry, style: TextStyle(color: FastTheme.accentGold)),
            ),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.pop(ctx);
              _showCreditSheet(l10n);
            },
            style: ElevatedButton.styleFrom(backgroundColor: FastTheme.accentGold),
            icon: const Icon(Icons.add_card, size: 18),
            label: Text(l10n.horaryCreditBuy,
                style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Future<void> _showCreditSheet(AppLocalizations l10n) async {
    if (!mounted) return;
    await showModalBottomSheet(
      context: context,
      backgroundColor: FastTheme.bgSecondary,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                Icon(Icons.add_card, color: FastTheme.accentGold),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(l10n.horaryCreditSheetTitle,
                      style: TextStyle(
                          color: FastTheme.accentGold,
                          fontSize: 17,
                          fontWeight: FontWeight.w700)),
                ),
              ]),
              const SizedBox(height: 8),
              Text(l10n.horaryCreditSheetDesc,
                  style: TextStyle(color: FastTheme.textMuted, height: 1.35)),
              const SizedBox(height: 12),
              for (final pack in HoraryCreditPack.all)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: CircleAvatar(
                    backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
                    child: Icon(Icons.confirmation_number,
                        color: FastTheme.accentGold, size: 20),
                  ),
                  title: Text(l10n.horaryCreditPackLabel(pack.credits),
                      style: TextStyle(
                          color: FastTheme.text,
                          fontWeight: FontWeight.w600)),
                  subtitle: Text(l10n.horaryCreditSheetDesc,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: FastTheme.textDim, fontSize: 11)),
                  trailing: Text(
                    RevenueCatService.priceFor(pack.productId,
                        fallback: pack.fallbackPrice),
                    style: TextStyle(
                        color: FastTheme.text,
                        fontWeight: FontWeight.bold,
                        fontSize: 15),
                  ),
                  onTap: () {
                    Navigator.pop(ctx);
                    _buyCredits(pack, l10n);
                  },
                ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _buyCredits(HoraryCreditPack pack, AppLocalizations l10n) async {
    final messenger = ScaffoldMessenger.of(context);
    final ok = await RevenueCatService.purchaseConsumable(pack.productId);
    if (!mounted) return;
    if (!ok) {
      messenger.showSnackBar(SnackBar(
        content: Text(l10n.horaryCreditPurchaseFailed),
      ));
      return;
    }
    messenger.showSnackBar(SnackBar(
      content: Text(l10n.horaryCreditPending),
    ));
    // The webhook may still be in flight; sync the verified purchase and retry.
    for (var attempt = 0; attempt < 4; attempt++) {
      final sync = await HoraryService.syncCredits();
      if (!mounted) return;
      if (sync.ok) {
        final added = (sync.data['credits_added'] as int?) ?? 0;
        final balance = sync.data['credits'] as int?;
        if (balance != null) setState(() => _credits = balance);
        await _loadQuota(refresh: true);
        if (!mounted) return;
        messenger.showSnackBar(SnackBar(
          content: Text(added > 0
              ? l10n.horaryCreditAdded(added)
              : l10n.horaryCreditAdded(pack.credits)),
        ));
        return;
      }
      await Future.delayed(const Duration(seconds: 2));
    }
    if (!mounted) return;
    await _loadQuota(refresh: true);
    if (!mounted) return;
    messenger.showSnackBar(SnackBar(
      content: Text(l10n.horaryCreditSyncFailed),
    ));
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
    setState(() => _busy = true);
    if (!await _confirmQuota(l10n)) {
      if (mounted) setState(() => _busy = false);
      return;
    }
    if (!mounted) return;
    setState(() {
      _chat.add(_ChatMsg('user', q));
      _persistChat();
      _lastQuestion = q;
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
          _persistChat();
        });
        _scrollDown();
        return;
      }
      final data = res.data;
      final verdict = (data['verdict'] ?? '').toString();
      if (verdict == 'NO_QUOTA') {
        setState(() {
          _busy = false;
          _remaining = data['remaining'] is int ? data['remaining'] as int : 0;
          _credits = data['credits'] is int ? data['credits'] as int : 0;
          if (data['is_pro'] is bool) _isPro = data['is_pro'] as bool;
          _resetAt = DateTime.tryParse((data['reset_at'] ?? '').toString());
          if (_chat.isNotEmpty && _chat.last.role == 'user') _chat.removeLast();
          _questionCtrl.text = q;
          _persistChat();
        });
        await _showLimitDialog(l10n);
        return;
      }
      final ans = (data['answer'] ?? verdict).toString();
      setState(() {
        if (data['remaining'] is int) _remaining = data['remaining'] as int;
        if (data['credits'] is int) _credits = data['credits'] as int;
        if (data['is_pro'] is bool) _isPro = data['is_pro'] as bool;
        if (data['houses'] is Map && (data['houses'] as Map).isNotEmpty) {
          _lastChart = data;
        }
        _chat.add(_ChatMsg('assistant', ans, meta: data));
        _persistChat();
      });
      _scrollDown();
      if (mounted) setState(() => _busy = false);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = l10n.horaryError;
        _chat.add(_ChatMsg('assistant', l10n.horaryError));
        _persistChat();
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

  Future<void> _persistChat() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final list = _chat.map((m) => {'role': m.role, 'content': m.content}).toList();
      await prefs.setString('horary_chat_history', jsonEncode(list));
    } catch (_) {}
  }

  Future<void> _loadChat() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString('horary_chat_history');
      if (raw == null || raw.isEmpty) return;
      final list = jsonDecode(raw) as List;
      if (!mounted) return;
      setState(() {
        _chat.clear();
        for (final e in list) {
          _chat.add(_ChatMsg((e['role'] ?? 'assistant').toString(), (e['content'] ?? '').toString()));
        }
        _showLanding = _chat.isEmpty;
      });
    } catch (_) {}
  }

  Future<void> _shareText(String text) async {
    if (text.trim().isEmpty) return;
    await Share.share(text);
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
          if (_chat.isNotEmpty)
            IconButton(
              tooltip: l10n.horaryClear,
              onPressed: () {
                setState(() {
                  _chat.clear();
                  _lastChart = null;
                  _showLanding = true;
                  _showDetails = false;
                  _lastQuestion = '';
                  _questionCtrl.clear();
                });
                SharedPreferences.getInstance().then((p) => p.remove('horary_chat_history'));
              },
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
          Expanded(child: _quotaBadge(l10n)),
          const SizedBox(width: 6),
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
            const SizedBox(height: 6),
            Row(mainAxisSize: MainAxisSize.min, children: [
              GestureDetector(
                onTap: () => _copy(m.content),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.copy, size: 14, color: FastTheme.textDim),
                  const SizedBox(width: 4),
                  Builder(builder: (ctx) => Text(AppLocalizations.of(ctx).horaryCopy, style: TextStyle(color: FastTheme.textDim, fontSize: 11))),
                ]),
              ),
              const SizedBox(width: 12),
              GestureDetector(
                onTap: () => _shareText(m.content),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.share_outlined, size: 14, color: FastTheme.textDim),
                  const SizedBox(width: 4),
                  Text(AppLocalizations.of(context).createPostShare, style: TextStyle(color: FastTheme.textDim, fontSize: 11)),
                ]),
              ),
            ]),
          ],
        ),
      ),
    );
  }

  Widget _chartCard(AppLocalizations l10n) {
    final data = _lastChart!;
    final h = data['houses'] is Map ? data['houses'] as Map : const {};
    final p = data['planets'] is Map ? data['planets'] as Map : const {};
    final ascSign = localizeHorarySign((h['asc_sign'] ?? '').toString(), l10n);
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
                  Text('${l10n.horaryMoon}: ${localizeHorarySign((moon['sign'] ?? '').toString(), l10n)} ${moon['deg'] != null ? (moon['deg'] as num).toStringAsFixed(1) : ''}°', style: TextStyle(color: FastTheme.textMuted, fontSize: 11)),
                  const SizedBox(height: 3),
                  Text(localizeHoraryVerdict((data['verdict'] ?? '').toString(), l10n), style: TextStyle(color: _verdictColor((data['verdict'] ?? '').toString()), fontSize: 12, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _timingCard(AppLocalizations l10n, DateTime target) {
    final timing = (_lastChart!['timing'] as Map);
    final timingText = (timing['text'] ?? '').toString();
    final localizedTiming = localizeHoraryTiming(timing, l10n);
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
          Expanded(child: localizedTiming != null
              ? Text(localizedTiming, style: TextStyle(color: FastTheme.textLight, fontSize: 11, fontWeight: FontWeight.w600))
              : HoraryLocalizedDetail(text: timingText, style: TextStyle(color: FastTheme.textLight, fontSize: 11, fontWeight: FontWeight.w600))),
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
                          Expanded(child: HoraryLocalizedDetail(text: '${m['meaning'] ?? ''}', style: TextStyle(color: FastTheme.textMuted, fontSize: 12, height: 1.4))),
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
    if (!_quotaReady) {
      return Text(_quotaError ? l10n.horaryQuotaUnavailable : l10n.horaryQuotaLoading,
          style: TextStyle(color: FastTheme.textDim, fontSize: 12));
    }
    final out = _remaining <= 0 && _credits <= 0;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(out ? Icons.lock_outline : Icons.timelapse, size: 14, color: out ? FastTheme.danger : FastTheme.textDim),
        const SizedBox(width: 6),
        Flexible(child: Text('$_remaining/$_quotaLimit', overflow: TextOverflow.ellipsis, style: TextStyle(color: out ? FastTheme.danger : FastTheme.textDim, fontSize: 12))),
        if (_credits > 0) ...[
          const SizedBox(width: 5),
          Icon(Icons.confirmation_number_outlined, size: 13, color: FastTheme.accentGold),
          const SizedBox(width: 2),
          Text('$_credits', style: TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w700)),
        ],
        if (out) ...[
          const SizedBox(width: 6),
          GestureDetector(
            onTap: () => _showCreditSheet(l10n),
            child: Text(l10n.horaryCreditBuy, style: TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w700)),
          ),
        ],
        if (out && !_isPro) ...[
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

