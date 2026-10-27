import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../providers/social_provider.dart';
import '../services/social_service.dart';
import '../screens/comments_screen.dart';
import '../screens/dm_screen.dart';
import '../screens/social_profile_screen.dart';
import 'post_share_sheet.dart';

/// Feed'deki tek bir post kartı.
class PostCard extends StatefulWidget {
  final PostItem post;
  const PostCard({super.key, required this.post});

  @override
  State<PostCard> createState() => _PostCardState();
}

class _PostCardState extends State<PostCard> {
  bool _busy = false;
  List<CommentItem> _comments = const [];

  @override
  void initState() {
    super.initState();
    _loadComments();
  }

  Future<void> _loadComments() async {
    final list = await SocialService.fetchRecentComments(
      widget.post.id,
      limit: 3,
    );
    if (mounted) setState(() => _comments = list);
  }

  Future<void> _toggleLike() async {
    if (_busy) return;
    setState(() => _busy = true);
    await context.read<SocialProvider>().toggleLike(widget.post);
    if (mounted) setState(() => _busy = false);
  }

  Future<void> _openComments() async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => CommentsScreen(postId: widget.post.id)),
    );
    // Sayaç yalnızca başarılı yorum gönderiminde güncellenir.
    if (mounted) {
      _loadComments();
    }
  }

  void _openDm() {
    final p = widget.post;
    if (p.userId.isEmpty || p.author == null) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => DmScreen(peerId: p.userId, peer: p.author),
      ),
    );
  }

  void _openProfile() {
    final uid = widget.post.userId;
    if (uid.isEmpty) return;
    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => SocialProfileScreen(userId: uid)));
  }

  Future<void> _menu() async {
    final l10n = AppLocalizations.of(context);
    final sp = context.read<SocialProvider>();
    final ap = context.read<AuthProvider>();
    final isMine = widget.post.userId == SocialService.currentUserId;

    final choice = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: FastTheme.cardBg,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (!isMine) ...[
              ListTile(
                leading: Icon(Icons.flag_outlined, color: FastTheme.warning),
                title: Text(
                  l10n.postReport,
                  style: TextStyle(color: FastTheme.text),
                ),
                onTap: () => Navigator.pop(ctx, 'report'),
              ),
              ListTile(
                leading: Icon(Icons.block, color: FastTheme.error),
                title: Text(
                  l10n.blockUser,
                  style: TextStyle(color: FastTheme.text),
                ),
                onTap: () => Navigator.pop(ctx, 'block'),
              ),
            ],
            if (isMine)
              ListTile(
                leading: Icon(Icons.delete_outline, color: FastTheme.error),
                title: Text(
                  l10n.postDelete,
                  style: TextStyle(color: FastTheme.text),
                ),
                onTap: () => Navigator.pop(ctx, 'delete'),
              ),
            ListTile(
              leading: Icon(Icons.close, color: FastTheme.textDim),
              title: Text(
                l10n.warningBack,
                style: TextStyle(color: FastTheme.textMuted),
              ),
              onTap: () => Navigator.pop(ctx),
            ),
          ],
        ),
      ),
    );

    if (!mounted || choice == null) return;

    if (choice == 'report') {
      await SocialService.report(targetType: 'post', targetId: widget.post.id);
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(l10n.reportSent)));
    } else if (choice == 'block') {
      await SocialService.block(widget.post.userId);
      sp.setBlocked(await SocialService.blockedIds());
      sp.filterBlockedFeed();
      if (ap.isLoggedIn) await sp.refreshProfile();
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(l10n.blockDone)));
    } else if (choice == 'delete') {
      await SocialService.deletePost(widget.post.id);
      sp.removePost(widget.post.id);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final p = widget.post;
    final author = p.author;

    return Container(
      margin: const EdgeInsets.only(bottom: 18),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: FastTheme.border.withValues(alpha: 0.7)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.25),
            blurRadius: 14,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Başlık: avatar + @handle + burç + zaman + menü ──
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 12, 4, 8),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: _openProfile,
                    child: Container(
                      padding: const EdgeInsets.all(2),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          colors: [
                            FastTheme.accentGold,
                            FastTheme.accentGold.withValues(alpha: 0.3),
                          ],
                        ),
                      ),
                      child: CircleAvatar(
                        radius: 17,
                        backgroundColor: FastTheme.bgSecondary,
                        backgroundImage:
                            (author?.avatarUrl != null &&
                                author!.avatarUrl!.isNotEmpty)
                            ? CachedNetworkImageProvider(author.avatarUrl!)
                            : null,
                        child:
                            (author?.avatarUrl == null ||
                                author!.avatarUrl!.isEmpty)
                            ? Text(
                                _initial(author),
                                style: TextStyle(
                                  color: FastTheme.accentGold,
                                  fontWeight: FontWeight.w700,
                                ),
                              )
                            : null,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: GestureDetector(
                      onTap: _openProfile,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  '@${author?.username ?? ''}',
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: FastTheme.text,
                                    fontWeight: FontWeight.w700,
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                              if (author?.sunSign != null &&
                                  author!.sunSign!.isNotEmpty) ...[
                                const SizedBox(width: 6),
                                AstroSigns.chip(
                                  author.sunSign,
                                  color: FastTheme.accentGold,
                                  l10n: l10n,
                                ),
                              ],
                            ],
                          ),
                          Text(
                            _timeAgo(p.createdAt, l10n),
                            style: TextStyle(
                              color: FastTheme.textDim,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  IconButton(
                    onPressed: _menu,
                    icon: Icon(
                      Icons.more_vert,
                      color: FastTheme.textDim,
                      size: 20,
                    ),
                  ),
                ],
              ),
            ),

            // ── Görsel ──
            if (p.mediaUrl.isNotEmpty)
              Hero(
                tag: 'post-${p.id}',
                child: AspectRatio(
                  aspectRatio: 1,
                  child: CachedNetworkImage(
                    imageUrl: p.mediaUrl,
                    fit: BoxFit.cover,
                    placeholder: (_, __) => Container(
                      color: FastTheme.bgSecondary,
                      child: Center(
                        child: CircularProgressIndicator(
                          color: FastTheme.accentGold,
                        ),
                      ),
                    ),
                    errorWidget: (_, __, ___) => Container(
                      color: FastTheme.bgSecondary,
                      child: Center(
                        child: Icon(
                          Icons.broken_image_outlined,
                          color: FastTheme.textDim,
                        ),
                      ),
                    ),
                  ),
                ),
              ),

            // ── Aksiyonlar ──
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              child: Row(
                children: [
                  IconButton(
                    onPressed: _toggleLike,
                    icon: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 180),
                      transitionBuilder: (child, anim) =>
                          ScaleTransition(scale: anim, child: child),
                      child: Icon(
                        p.likedByMe ? Icons.favorite : Icons.favorite_border,
                        key: ValueKey(p.likedByMe),
                        color: p.likedByMe
                            ? FastTheme.error
                            : FastTheme.textMuted,
                      ),
                    ),
                  ),
                  Text(
                    '${p.likeCount}',
                    style: TextStyle(color: FastTheme.textMuted, fontSize: 13),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: _openComments,
                    icon: Icon(
                      Icons.chat_bubble_outline,
                      color: FastTheme.textMuted,
                      size: 21,
                    ),
                  ),
                  Text(
                    '${p.commentCount}',
                    style: TextStyle(color: FastTheme.textMuted, fontSize: 13),
                  ),
                  const SizedBox(width: 4),
                  if (p.userId != SocialService.currentUserId)
                    IconButton(
                      onPressed: _openDm,
                      icon: Icon(
                        Icons.mark_email_unread_outlined,
                        color: FastTheme.textMuted,
                        size: 20,
                      ),
                      tooltip: l10n.dmMessage,
                    ),
                  IconButton(
                    onPressed: () => showPostShareSheet(context, p),
                    icon: Icon(
                      Icons.share_outlined,
                      color: FastTheme.textMuted,
                      size: 19,
                    ),
                    tooltip: l10n.postShareTitle,
                  ),
                  const Spacer(),
                  if (p.isChart)
                    Padding(
                      padding: const EdgeInsets.only(right: 12),
                      child: Icon(
                        Icons.auto_awesome,
                        color: FastTheme.accentGold,
                        size: 16,
                      ),
                    ),
                ],
              ),
            ),

            // ── Başlık ──
            if (p.caption != null && p.caption!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
                child: RichText(
                  text: TextSpan(
                    children: [
                      TextSpan(
                        text: '@${author?.username ?? ''} ',
                        style: TextStyle(
                          color: FastTheme.accentGold,
                          fontWeight: FontWeight.w700,
                          fontSize: 13,
                        ),
                      ),
                      TextSpan(
                        text: p.caption,
                        style: TextStyle(
                          color: FastTheme.text,
                          fontSize: 13,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            // ── Yorum önizlemesi (en yeni 3) ──
            if (_comments.isNotEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 6),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (final c in _comments.reversed)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 3),
                        child: RichText(
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          text: TextSpan(
                            children: [
                              TextSpan(
                                text: '@${c.author?.username ?? ''} ',
                                style: TextStyle(
                                  color: FastTheme.text,
                                  fontWeight: FontWeight.w700,
                                  fontSize: 12,
                                ),
                              ),
                              TextSpan(
                                text: c.text,
                                style: TextStyle(
                                  color: FastTheme.textDim,
                                  fontSize: 12,
                                  height: 1.3,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              ),

            // ── "Tüm yorumları gör" ──
            if (p.commentCount > _comments.length)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                child: GestureDetector(
                  onTap: _openComments,
                  child: Text(
                    l10n.viewAllComments(p.commentCount),
                    style: TextStyle(
                      color: FastTheme.textMuted,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              )
            else
              const SizedBox(height: 10),
          ],
        ),
      ),
    );
  }

  String _initial(SocialProfile? a) {
    final n = a?.displayName ?? a?.username ?? '?';
    return n.isEmpty ? '?' : n[0].toUpperCase();
  }

  String _timeAgo(DateTime t, AppLocalizations l10n) {
    final diff = DateTime.now().difference(t);
    if (diff.inMinutes < 1) return l10n.timeJustNow;
    if (diff.inHours < 1) return l10n.timeMinutes(diff.inMinutes);
    if (diff.inDays < 1) return l10n.timeHours(diff.inHours);
    if (diff.inDays < 7) return l10n.timeDays(diff.inDays);
    return '${t.day}.${t.month}.${t.year}';
  }
}
