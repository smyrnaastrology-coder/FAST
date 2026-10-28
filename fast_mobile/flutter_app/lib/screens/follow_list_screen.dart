import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../services/social_service.dart';
import 'social_profile_screen.dart';

class FollowListScreen extends StatefulWidget {
  final String userId;
  final bool showFollowers; // true = followers, false = following
  const FollowListScreen({super.key, required this.userId, required this.showFollowers});

  @override
  State<FollowListScreen> createState() => _FollowListScreenState();
}

class _FollowListScreenState extends State<FollowListScreen> {
  List<SocialProfile> _list = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final res = widget.showFollowers
        ? await SocialService.fetchFollowers(widget.userId)
        : await SocialService.fetchFollowing(widget.userId);
    if (mounted) {
      setState(() {
        _list = res;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final title = widget.showFollowers ? l10n.profileFollowers : l10n.profileFollowing;
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text(
          title,
          style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700),
        ),
        iconTheme: IconThemeData(color: FastTheme.accentGold),
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator(color: FastTheme.accentGold))
          : _list.isEmpty
              ? Center(
                  child: Text(
                    l10n.profileNoPosts,
                    style: TextStyle(color: FastTheme.textMuted),
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: _list.length,
                  separatorBuilder: (_, __) => Divider(color: FastTheme.border, height: 1),
                  itemBuilder: (context, i) {
                    final p = _list[i];
                    return ListTile(
                      leading: CircleAvatar(
                        backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
                        backgroundImage: (p.avatarUrl != null && p.avatarUrl!.isNotEmpty)
                            ? CachedNetworkImageProvider(p.avatarUrl!)
                            : null,
                        child: (p.avatarUrl == null || p.avatarUrl!.isEmpty)
                            ? Text(
                                (p.displayName?.isNotEmpty == true ? p.displayName![0] : p.username[0]).toUpperCase(),
                                style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700),
                              )
                            : null,
                      ),
                      title: Text(p.displayName?.isNotEmpty == true ? p.displayName! : '@${p.username}', style: TextStyle(color: FastTheme.text)),
                      subtitle: Text('@${p.username}', style: TextStyle(color: FastTheme.textDim)),
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => SocialProfileScreen(userId: p.userId)),
                        );
                      },
                    );
                  },
                ),
    );
  }
}
