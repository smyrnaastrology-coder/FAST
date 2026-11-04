import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
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
    try {
      final added = await SocialService.addComment(widget.postId, text);
      if (!mounted) return;
      if (!added) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppLocalizations.of(context).socialErrorServer)),
        );
        return;
      }
      context.read<SocialProvider>().incrementCommentCount(widget.postId);
      _ctrl.clear();
      await _load();
      if (mounted && _scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppLocalizations.of(context).socialErrorServer)),
        );
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _editComment(CommentItem comment) async {
    final l10n = AppLocalizations.of(context);
    final controller = TextEditingController(text: comment.text);
    final value = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: FastTheme.bgSecondary,
        title: Text(l10n.commentEdit, style: TextStyle(color: FastTheme.accentGold)),
        content: TextField(
          controller: controller,
          autofocus: true,
          minLines: 2,
          maxLines: 6,
          maxLength: 300,
          style: TextStyle(color: FastTheme.text),
          decoration: InputDecoration(hintText: l10n.commentsHint),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(l10n.editCancel)),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, controller.text), child: Text(l10n.editSave)),
        ],
      ),
    );
    controller.dispose();
    if (!mounted || value == null) return;
    try {
      await SocialService.updateCommentText(comment.id, value);
      await _load();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.socialErrorServer)),
        );
      }
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
    final l10n = AppLocalizations.of(context);
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
                        AstroSigns.chip(a.sunSign, color: FastTheme.accentGold, l10n: l10n),
                      ],
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(c.text, style: TextStyle(color: FastTheme.text, fontSize: 13, height: 1.4)),
                 ],
               ),
             ),
             if (c.userId == SocialService.currentUserId)
               PopupMenuButton<String>(
                 tooltip: l10n.commentEdit,
                 color: FastTheme.cardBg,
                 icon: Icon(Icons.more_horiz, color: FastTheme.textDim, size: 19),
                 onSelected: (value) {
                   if (value == 'edit') _editComment(c);
                 },
                 itemBuilder: (_) => [
                   PopupMenuItem(
                     value: 'edit',
                     child: Row(children: [
                       Icon(Icons.edit_outlined, size: 18, color: FastTheme.accentGold),
                       const SizedBox(width: 8),
                       Text(l10n.commentEdit, style: TextStyle(color: FastTheme.text)),
                     ]),
                   ),
                 ],
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
