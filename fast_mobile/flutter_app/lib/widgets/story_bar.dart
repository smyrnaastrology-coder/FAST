import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
import '../screens/create_story_screen.dart';
import '../screens/story_viewer_screen.dart';
import '../services/social_service.dart';

/// Feed/profil üstündeki yatay hikâye şeridi.
/// İlk eleman kendi hikâyesi (yoksa "+"); görülmemiş hikâyeler altın halka.
class StoryBar extends StatelessWidget {
  final bool showAdd;
  const StoryBar({super.key, this.showAdd = true});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final sp = context.watch<SocialProvider>();
    final groups = sp.stories;
    final myId = SocialService.currentUserId;
    final myIndex = groups.indexWhere((g) => g.profile?.userId == myId);
    final hasMine = myIndex >= 0;

    if (!hasMine && groups.isEmpty && !showAdd) return const SizedBox.shrink();

    return SizedBox(
      height: 96,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        children: [
          // ── Kendi hikâyesi ──
          if (showAdd)
            _Item(
              label: hasMine ? l10n.storyMine : l10n.storyAdd,
              seen: hasMine ? groups[myIndex].allViewed : true,
              add: !hasMine,
              avatarUrl: sp.myProfile?.avatarUrl,
              username: sp.myProfile?.username,
              onTap: () async {
                if (hasMine) {
                  await _open(context, groups, myIndex);
                } else {
                  await Navigator.of(context).push(MaterialPageRoute(builder: (_) => const CreateStoryScreen()));
                  if (context.mounted) context.read<SocialProvider>().refreshStories();
                }
              },
            ),

          // ── Diğer kullanıcılar ──
          for (int i = 0; i < groups.length; i++)
            if (groups[i].profile?.userId != myId)
              _Item(
                label: groups[i].profile?.username ?? '',
                seen: groups[i].allViewed,
                avatarUrl: groups[i].profile?.avatarUrl,
                username: groups[i].profile?.username,
                onTap: () => _open(context, groups, i),
              ),
        ],
      ),
    );
  }

  Future<void> _open(BuildContext context, List<UserStories> groups, int index) async {
    await Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => StoryViewerScreen(groups: groups, startIndex: index),
    ));
    if (context.mounted) context.read<SocialProvider>().refreshStories();
  }
}

class _Item extends StatelessWidget {
  final String label;
  final bool seen;
  final bool add;
  final String? avatarUrl;
  final String? username;
  final VoidCallback onTap;

  const _Item({
    required this.label,
    required this.seen,
    required this.onTap,
    this.add = false,
    this.avatarUrl,
    this.username,
  });

  @override
  Widget build(BuildContext context) {
    final ring = seen
        ? [FastTheme.textDim, FastTheme.textDim]
        : [FastTheme.accentGold, FastTheme.accentGoldLight];

    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 74,
        margin: const EdgeInsets.symmetric(horizontal: 5),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(3),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(colors: ring, begin: Alignment.topRight, end: Alignment.bottomLeft),
              ),
              child: Container(
                padding: const EdgeInsets.all(2.5),
                decoration: BoxDecoration(color: FastTheme.bg, shape: BoxShape.circle),
                child: CircleAvatar(
                  radius: 28,
                  backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
                  backgroundImage: (avatarUrl != null && avatarUrl!.isNotEmpty)
                      ? CachedNetworkImageProvider(avatarUrl!)
                      : null,
                  child: add
                      ? Icon(Icons.add, color: FastTheme.accentGold, size: 26)
                      : (avatarUrl == null || avatarUrl!.isEmpty)
                          ? Text((username?.isNotEmpty ?? false) ? username![0].toUpperCase() : '?',
                              style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700, fontSize: 18))
                          : null,
                ),
              ),
            ),
            const SizedBox(height: 5),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: FastTheme.textDim, fontSize: 10.5),
            ),
          ],
        ),
      ),
    );
  }
}
