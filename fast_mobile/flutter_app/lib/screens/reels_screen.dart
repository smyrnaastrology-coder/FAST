import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
import '../services/social_service.dart';
import '../screens/comments_screen.dart';
import '../screens/dm_screen.dart';
import '../screens/social_profile_screen.dart';
import '../widgets/venus_like.dart';

/// Instagram tarzı dikey "Reels" akışı.
///
/// Video desteği olmadığı için post görselleri tam ekran dikey sayfalayıcıda
/// gösterilir: yukarı/aşağı kaydır, sağda beğeni/yorum/mesaj, altta yazar.
class ReelsScreen extends StatefulWidget {
  const ReelsScreen({super.key});

  @override
  State<ReelsScreen> createState() => _ReelsScreenState();
}

class _ReelsScreenState extends State<ReelsScreen> {
  final _page = PageController();

  @override
  void dispose() {
    _page.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final sp = context.watch<SocialProvider>();

    if (sp.status == SocialStatus.loading && sp.feed.isEmpty) {
      return Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: FastTheme.accentGold)),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: sp.feed.isEmpty
          ? Center(
              child: Text(
                l10n.feedEmpty,
                style: TextStyle(color: FastTheme.textMuted, fontSize: 14),
              ),
            )
          : PageView.builder(
              controller: _page,
              scrollDirection: Axis.vertical,
              itemCount: sp.feed.length,
              itemBuilder: (context, i) => _ReelPage(post: sp.feed[i]),
            ),
    );
  }
}

class _ReelPage extends StatefulWidget {
  final PostItem post;
  const _ReelPage({required this.post});

  @override
  State<_ReelPage> createState() => _ReelPageState();
}

class _ReelPageState extends State<_ReelPage> {
  bool _busy = false;

  Future<void> _toggleLike() async {
    if (_busy) return;
    setState(() => _busy = true);
    await context.read<SocialProvider>().toggleLike(widget.post);
    if (mounted) setState(() => _busy = false);
  }

  void _openComments() {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => CommentsScreen(postId: widget.post.id),
    ));
  }

  void _openDm() {
    final p = widget.post;
    if (p.userId.isEmpty || p.author == null) return;
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => DmScreen(peerId: p.userId, peer: p.author),
    ));
  }

  void _openProfile() {
    final uid = widget.post.userId;
    if (uid.isEmpty) return;
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => SocialProfileScreen(userId: uid)));
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.post;
    final author = p.author;

    return Stack(
      fit: StackFit.expand,
      children: [
        // Görsel
        CachedNetworkImage(
          imageUrl: p.mediaUrl,
          fit: BoxFit.cover,
          placeholder: (_, __) => Container(color: FastTheme.bgSecondary),
          errorWidget: (_, __, ___) => Container(
            color: FastTheme.bgSecondary,
            child: Icon(Icons.broken_image, color: FastTheme.textDim, size: 40),
          ),
        ),

        // Alt gradyan (metin okunurluğu)
        Positioned(
          left: 0,
          right: 0,
          bottom: 0,
          height: 260,
          child: IgnorePointer(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                  colors: [Colors.black.withValues(alpha: 0.85), Colors.transparent],
                ),
              ),
            ),
          ),
        ),

        // Sağ aksiyon sütunu
        Positioned(
          right: 10,
          bottom: 90,
          child: Column(
            children: [
              _action(
                VenusLikeIcon(size: 32, liked: p.likedByMe, color: p.likedByMe ? FastTheme.rose : FastTheme.accentGold),
                '${p.likeCount}',
                FastTheme.accentGold,
                _toggleLike,
              ),
              _action(Icon(Icons.chat_bubble_outline, color: Colors.white, size: 30), '${p.commentCount}', Colors.white, _openComments),
              if (p.userId != SocialService.currentUserId)
                _action(Icon(Icons.send_outlined, color: Colors.white, size: 30), '', Colors.white, _openDm),
            ],
          ),
        ),

        // Alt bilgi: yazar + açıklama
        Positioned(
          left: 14,
          right: 80,
          bottom: 24,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              GestureDetector(
                onTap: _openProfile,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CircleAvatar(
                      radius: 14,
                      backgroundColor: FastTheme.accentGold.withValues(alpha: 0.2),
                      backgroundImage: (author?.avatarUrl != null && author!.avatarUrl!.isNotEmpty)
                          ? CachedNetworkImageProvider(author.avatarUrl!)
                          : null,
                      child: (author?.avatarUrl == null || author!.avatarUrl!.isEmpty)
                          ? Text(
                              (author?.username.isNotEmpty == true ? author!.username[0] : '?').toUpperCase(),
                              style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700, fontSize: 12),
                            )
                          : null,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '@${author?.username ?? ''}',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 14),
                    ),
                  ],
                ),
              ),
              if (p.caption != null && p.caption!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  p.caption!,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.35),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _action(Widget icon, String label, Color color, VoidCallback onTap) => GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Column(
            children: [
              icon,
              if (label.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(label, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
                ),
            ],
          ),
        ),
      );
}
