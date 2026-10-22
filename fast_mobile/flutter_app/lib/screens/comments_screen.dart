import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../services/social_service.dart';
import 'social_profile_screen.dart';

/// Bir postun yorumları.
class CommentsScreen extends StatefulWidget {
  final String postId;
  const CommentsScreen({super.key, required this.postId});

  @override
  State<CommentsScreen> createState() => _CommentsScreenState();
}

class _CommentsScreenState extends State<CommentsScreen> {
  final _ctrl = TextEditingController();
  final _scroll = ScrollController();
  List<CommentItem> _comments = [];
  bool _loading = true;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final c = await SocialService.fetchComments(widget.postId);
    if (!mounted) return;
    setState(() {
      _comments = c;
      _loading = false;
    });
  }

  Future<void> _send() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() => _sending = true);
    await SocialService.addComment(widget.postId, text);
    _ctrl.clear();
    await _load();
    if (mounted) setState(() => _sending = false);
    if (mounted && _scroll.hasClients) {
      _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text(l10n.commentsTitle, style: TextStyle(color: FastTheme.accentGold, fontSize: 18)),
      ),
      body: Column(
        children: [
          Expanded(
            child: _loading
                ? Center(child: CircularProgressIndicator(color: FastTheme.accentGold))
                : _comments.isEmpty
                    ? Center(child: Text(l10n.commentsEmpty, style: TextStyle(color: FastTheme.textMuted)))
                    : ListView.builder(
                        controller: _scroll,
                        padding: const EdgeInsets.all(12),
                        itemCount: _comments.length,
                        itemBuilder: (_, i) => _tile(_comments[i]),
                      ),
          ),
          SafeArea(
            child: Container(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
              decoration: BoxDecoration(color: FastTheme.bgSecondary, border: Border(top: BorderSide(color: FastTheme.border))),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _ctrl,
                      style: TextStyle(color: FastTheme.text),
                      maxLength: 300,
                      decoration: InputDecoration(hintText: l10n.commentsHint, counterText: ''),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: _sending ? null : _send,
                    icon: _sending
                        ? SizedBox(height: 18, width: 18, child: CircularProgressIndicator(color: FastTheme.accentGold, strokeWidth: 2))
                        : Icon(Icons.send, color: FastTheme.accentGold),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _tile(CommentItem c) {
    final a = c.author;
    return GestureDetector(
      onTap: () {
        if (c.userId.isNotEmpty) {
          Navigator.of(context).push(MaterialPageRoute(builder: (_) => SocialProfileScreen(userId: c.userId)));
        }
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
              backgroundImage: (a?.avatarUrl != null && a!.avatarUrl!.isNotEmpty)
                  ? CachedNetworkImageProvider(a.avatarUrl!)
                  : null,
              child: (a?.avatarUrl == null || a!.avatarUrl!.isEmpty)
                  ? Text(_initial(a), style: TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w700))
                  : null,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text('@${a?.username ?? ''}',
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700, fontSize: 12)),
                      ),
                      if (a?.sunSign != null && a!.sunSign!.isNotEmpty) ...[
                        const SizedBox(width: 6),
                        AstroSigns.chip(a.sunSign, color: FastTheme.accentGold),
                      ],
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(c.text, style: TextStyle(color: FastTheme.text, fontSize: 13, height: 1.4)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _initial(SocialProfile? a) {
    final n = a?.displayName ?? a?.username ?? '?';
    return n.isEmpty ? '?' : n[0].toUpperCase();
  }
}
