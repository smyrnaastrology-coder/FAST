import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
import '../services/social_service.dart';

/// Tam ekran hikâye izleyici: otomatik ilerleme, sağa/sola dokunma,
/// etiket + görüntülenme sayısı. İzlenen hikâye ring'i "görüldü" yapar.
class StoryViewerScreen extends StatefulWidget {
  final List<UserStories> groups;
  final int startIndex;
  const StoryViewerScreen({super.key, required this.groups, this.startIndex = 0});

  @override
  State<StoryViewerScreen> createState() => _StoryViewerScreenState();
}

class _StoryViewerScreenState extends State<StoryViewerScreen> with SingleTickerProviderStateMixin {
  /// Her hikâye için minimum görüntüleme süresi (sn).
  static const int storySeconds = 15;

  late int _gi; // grup (kullanıcı) indeksi
  late int _si; // o kullanıcının hikâye indeksi
  late final AnimationController _prog;
  int _viewCount = 0;
  List<String> _mentions = [];

  /// groups degismez (unmodifiable) gelir; silme islemi icin kopyalanir.
  late final List<UserStories> _groups;

  UserStories get _group => _groups[_gi];
  StoryItem get _story => _group.stories[_si];

  @override
  void initState() {
    super.initState();
    _groups = List<UserStories>.from(widget.groups);
    _gi = widget.startIndex.clamp(0, _groups.length - 1);
    _si = 0;
    _prog = AnimationController(
      vsync: this,
      duration: const Duration(seconds: storySeconds),
    )..addStatusListener((s) {
        if (s == AnimationStatus.completed) _next();
      });
    _onShow();
  }

  @override
  void dispose() {
    _prog.dispose();
    super.dispose();
  }

  void _onShow() {
    _prog.duration = const Duration(seconds: storySeconds);
    _prog.forward(from: 0);
    _loadMeta();
    _markViewed();
  }

  Future<void> _markViewed() async {
    await SocialService.markStoryViewed(_story.id);
    if (mounted) context.read<SocialProvider>().markStoriesViewed(_group.profile?.userId ?? _story.userId);
  }

  Future<void> _loadMeta() async {
    final count = await SocialService.storyViewCount(_story.id);
    final mentions = await SocialService.storyMentions(_story.id);
    if (mounted) setState(() {
      _viewCount = count;
      _mentions = mentions;
    });
  }

  void _next() {
    if (_si < _group.stories.length - 1) {
      setState(() => _si++);
      _onShow();
    } else if (_gi < _groups.length - 1) {
      setState(() {
        _gi++;
        _si = 0;
      });
      _onShow();
    } else {
      Navigator.of(context).pop();
    }
  }

  void _prev() {
    if (_si > 0) {
      setState(() => _si--);
      _onShow();
    } else if (_gi > 0) {
      setState(() {
        _gi--;
        _si = _groups[_gi].stories.length - 1;
      });
      _onShow();
    }
  }

  /// Kendi hikâyesini sil (onaylayarak).
  Future<void> _confirmDelete() async {
    final l10n = AppLocalizations.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: FastTheme.cardBg,
        title: Text(l10n.storyDelete, style: TextStyle(color: FastTheme.text)),
        content: Text(l10n.storyDeleteConfirm, style: TextStyle(color: FastTheme.textMuted)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(l10n.warningBack, style: TextStyle(color: FastTheme.textMuted)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(l10n.postDelete, style: TextStyle(color: FastTheme.error)),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;

    final id = _story.id;
    final group = _group;
    final idx = _si;

    await SocialService.deleteStory(id);
    if (!mounted) return;

    // Yerel listeden de kaldır
    final stories = List<StoryItem>.from(group.stories)..removeWhere((s) => s.id == id);
    if (stories.isEmpty) {
      _groups.removeAt(_gi);
      if (_groups.isEmpty) {
        Navigator.of(context).pop();
      } else {
        setState(() {
          _gi = _gi.clamp(0, _groups.length - 1);
          _si = 0;
        });
        _onShow();
      }
    } else {
      _groups[_gi] = UserStories(profile: group.profile, stories: stories, allViewed: group.allViewed);
      setState(() {
        _si = idx.clamp(0, stories.length - 1);
      });
      _onShow();
    }

    await context.read<SocialProvider>().refreshStories();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(AppLocalizations.of(context).storyDeleteDone)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final story = _story;
    final author = _group.profile;
    final time = _timeAgo(story.createdAt, l10n);

    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTapUp: (d) {
          final w = MediaQuery.of(context).size.width;
          if (d.localPosition.dx < w * 0.3) {
            _prev();
          } else {
            _next();
          }
        },
        onLongPressStart: (_) => _prog.stop(),
        onLongPressEnd: (_) {
          if (_prog.value < 1.0) _prog.forward();
        },
        child: Stack(
          fit: StackFit.expand,
          children: [
            // ── Görsel ──
            Center(
              child: CachedNetworkImage(
                imageUrl: story.mediaUrl,
                fit: BoxFit.contain,
                placeholder: (_, __) => Center(child: CircularProgressIndicator(color: FastTheme.accentGold)),
                errorWidget: (_, __, ___) => Center(child: Icon(Icons.broken_image, color: Colors.white54, size: 40)),
              ),
            ),

            // ── Üst: ilerleme çubukları + başlık ──
            Positioned(
              top: MediaQuery.of(context).padding.top + 8,
              left: 8,
              right: 8,
              child: Column(
                children: [
                  // İlerleme çubukları (aktif olan dolu olarak dolar)
                  AnimatedBuilder(
                    animation: _prog,
                    builder: (ctx, _) => Row(
                      children: [
                        for (int i = 0; i < _group.stories.length; i++)
                          Expanded(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 2),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(2),
                                child: SizedBox(
                                  height: 3,
                                  child: Stack(
                                    fit: StackFit.expand,
                                    children: [
                                      Container(color: Colors.white24),
                                      if (i < _si)
                                        Container(color: Colors.white)
                                      else if (i == _si)
                                        FractionallySizedBox(
                                          alignment: Alignment.centerLeft,
                                          widthFactor: _prog.value,
                                          child: Container(color: FastTheme.accentGold),
                                        ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 16,
                        backgroundColor: Colors.white24,
                        backgroundImage: (author?.avatarUrl != null && author!.avatarUrl!.isNotEmpty)
                            ? CachedNetworkImageProvider(author.avatarUrl!)
                            : null,
                        child: (author?.avatarUrl == null || author!.avatarUrl!.isEmpty)
                            ? Text(_initial(author), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700))
                            : null,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '@${author?.username ?? ''} · $time',
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      IconButton(
                        onPressed: () => Navigator.of(context).pop(),
                        icon: const Icon(Icons.close, color: Colors.white, size: 26),
                      ),
                      if (story.userId == SocialService.currentUserId)
                        IconButton(
                          onPressed: _confirmDelete,
                          icon: const Icon(Icons.delete_outline, color: Colors.white, size: 24),
                          tooltip: l10n.storyDelete,
                        ),
                    ],
                  ),
                ],
              ),
            ),

            // ── Alt: etiketler + görüntülenme ──
            Positioned(
              left: 16,
              right: 16,
              bottom: MediaQuery.of(context).padding.bottom + 20,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (_mentions.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Wrap(
                        spacing: 8,
                        children: [
                          for (final m in _mentions)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                              decoration: BoxDecoration(
                                color: Colors.black54,
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: FastTheme.accentGold),
                              ),
                              child: Text('$m ${l10n.storyMentioned}',
                                  style: TextStyle(color: FastTheme.accentGold, fontSize: 12, fontWeight: FontWeight.w600)),
                            ),
                        ],
                      ),
                    ),
                  if (story.userId == SocialService.currentUserId)
                    Row(
                      children: [
                        const Icon(Icons.remove_red_eye_outlined, color: Colors.white70, size: 16),
                        const SizedBox(width: 5),
                        Text('$_viewCount', style: const TextStyle(color: Colors.white70, fontSize: 13)),
                      ],
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _initial(dynamic a) {
    final n = a?.displayName ?? a?.username ?? '?';
    return (n == null || n.isEmpty) ? '?' : n[0].toUpperCase();
  }

  String _timeAgo(DateTime t, AppLocalizations l10n) {
    final diff = DateTime.now().difference(t);
    if (diff.inMinutes < 1) return l10n.timeJustNow;
    if (diff.inHours < 1) return l10n.timeMinutes(diff.inMinutes);
    if (diff.inDays < 1) return l10n.timeHours(diff.inHours);
    return l10n.timeDays(diff.inDays);
  }
}
