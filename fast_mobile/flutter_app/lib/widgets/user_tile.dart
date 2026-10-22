import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../services/social_service.dart';
import '../screens/social_profile_screen.dart';

/// Arama listesinde tek kullanıcı satırı (takip butonlu).
class UserTile extends StatefulWidget {
  final SocialProfile profile;
  final VoidCallback? onChanged;
  const UserTile({super.key, required this.profile, this.onChanged});

  @override
  State<UserTile> createState() => _UserTileState();
}

class _UserTileState extends State<UserTile> {
  bool _following = false;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    final f = await SocialService.isFollowing(widget.profile.userId);
    if (mounted) setState(() => _following = f);
  }

  Future<void> _toggle() async {
    if (_busy) return;
    setState(() => _busy = true);
    if (_following) {
      await SocialService.unfollow(widget.profile.userId);
      setState(() => _following = false);
    } else {
      await SocialService.follow(widget.profile.userId);
      setState(() => _following = true);
    }
    if (mounted) setState(() => _busy = false);
    widget.onChanged?.call();
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.profile;
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
      onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => SocialProfileScreen(userId: p.userId))),
      leading: CircleAvatar(
        radius: 22,
        backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
        backgroundImage: (p.avatarUrl != null && p.avatarUrl!.isNotEmpty)
            ? CachedNetworkImageProvider(p.avatarUrl!)
            : null,
        child: (p.avatarUrl == null || p.avatarUrl!.isEmpty)
            ? Text(_initial(p), style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700))
            : null,
      ),
      title: Row(
        children: [
          Flexible(
            child: Text('@${p.username}', overflow: TextOverflow.ellipsis,
                style: TextStyle(color: FastTheme.text, fontWeight: FontWeight.w700, fontSize: 14)),
          ),
          if (p.sunSign != null && p.sunSign!.isNotEmpty) ...[
            const SizedBox(width: 6),
            AstroSigns.chip(p.sunSign, color: FastTheme.accentGold),
          ],
        ],
      ),
      subtitle: (p.displayName != null && p.displayName!.isNotEmpty)
          ? Text(p.displayName!, style: TextStyle(color: FastTheme.textDim, fontSize: 12))
          : null,
      trailing: GestureDetector(
        onTap: _toggle,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
          decoration: BoxDecoration(
            gradient: _following ? null : LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]),
            color: _following ? Colors.transparent : null,
            border: _following ? Border.all(color: FastTheme.border) : null,
            borderRadius: BorderRadius.circular(8),
          ),
          child: _busy
              ? SizedBox(height: 14, width: 14, child: CircularProgressIndicator(color: FastTheme.accentGold, strokeWidth: 2))
              : Text(
                  _following ? '✓' : '+',
                  style: TextStyle(color: _following ? FastTheme.accentGold : FastTheme.bg, fontWeight: FontWeight.w700, fontSize: 14),
                ),
        ),
      ),
    );
  }

  String _initial(SocialProfile p) {
    final n = p.displayName ?? p.username;
    return n.isEmpty ? '?' : n[0].toUpperCase();
  }
}
