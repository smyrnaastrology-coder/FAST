import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';
import '../config/astro_signs.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';
import '../providers/social_provider.dart';
import '../providers/locale_provider.dart';
import '../services/social_service.dart';
import '../services/translation_service.dart';
import '../widgets/planet_strip.dart';
import '../widgets/post_card.dart';
import '../widgets/pro_badge.dart';
import '../widgets/story_bar.dart';
import 'auth_screen.dart';
import 'dm_screen.dart';
import 'edit_social_profile_screen.dart';
import 'follow_list_screen.dart';

/// Bir kullanıcının @handle profil sayfası (kendi profili de buradan yönetilir).
///
/// [userId]  → profili görüntülenecek kullanıcı (boşsa kendi profili).
/// [embedded]→ alt navigasyon çubuğu içinde gösteriliyorsa geri oku gizlenir.
class SocialProfileScreen extends StatefulWidget {
  final String? userId;
  final bool embedded;
  const SocialProfileScreen({super.key, this.userId, this.embedded = false});

  @override
  State<SocialProfileScreen> createState() => _SocialProfileScreenState();
}

class _SocialProfileScreenState extends State<SocialProfileScreen> {
  SocialProfile? _profile;
  List<PostItem> _posts = [];
  List<PlanetPos> _planets = [];
  int _followers = 0;
  int _following = 0;
  bool _isFollowing = false;
  bool _loading = true;
  bool _busy = false;
  int _tab = 0; // 0 = gönderiler, 1 = reels

  String get _uid => (widget.userId ?? '').isNotEmpty
      ? widget.userId!
      : SocialService.currentUserId;

  bool get _isMe => _uid.isNotEmpty && _uid == SocialService.currentUserId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final uid = _uid;
    if (uid.isEmpty) {
      if (mounted) setState(() => _loading = false);
      return;
    }
    setState(() => _loading = true);
    if (_isMe) await SocialService.syncProStatus();
    final prof = await SocialService.profileByUser(uid);
    final posts = await SocialService.fetchUserPosts(uid);
    final planets = await SocialService.fetchPlanets(uid);
    final fc = await SocialService.followerCount(uid);
    final ig = await SocialService.followingCount(uid);
    final fol = _isMe ? false : await SocialService.isFollowing(uid);
    if (!mounted) return;
    setState(() {
      _profile = prof;
      _posts = posts;
      _planets = planets;
      _followers = fc;
      _following = ig;
      _isFollowing = fol;
      _loading = false;
    });
  }

  Future<void> _toggleFollow() async {
    final ap = context.read<AuthProvider>();
    if (!ap.isLoggedIn) {
      Navigator.of(
        context,
      ).push(MaterialPageRoute(builder: (_) => const AuthScreen()));
      return;
    }
    setState(() => _busy = true);
    if (_isFollowing) {
      await SocialService.unfollow(_uid);
      setState(() {
        _isFollowing = false;
        _followers = (_followers - 1).clamp(0, 1 << 31);
      });
    } else {
      await SocialService.follow(_uid);
      setState(() {
        _isFollowing = true;
        _followers += 1;
      });
    }
    if (mounted) setState(() => _busy = false);
  }

  Future<void> _menu() async {
    final l10n = AppLocalizations.of(context);
    final sp = context.read<SocialProvider>();
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
            if (!_isMe) ...[
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
      await SocialService.report(targetType: 'user', targetId: _uid);
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(l10n.reportSent)));
    } else if (choice == 'block') {
      await SocialService.block(_uid);
      sp.setBlocked(await SocialService.blockedIds());
      sp.filterBlockedFeed();
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(l10n.blockDone)));
        Navigator.of(context).pop();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final p = _profile;

    // Kendi profilimiz (userId verilmedi) → giriş zorunlu.
    final isOwn = (widget.userId ?? '').isEmpty;
    if (isOwn && !context.watch<AuthProvider>().isLoggedIn) {
      return Scaffold(
        backgroundColor: FastTheme.bg,
        appBar: AppBar(
          backgroundColor: FastTheme.bg,
          automaticallyImplyLeading: !widget.embedded,
          title: Text(
            l10n.profileTabPosts,
            style: TextStyle(
              color: FastTheme.accentGold,
              fontSize: 18,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.person_outline,
                  size: 64,
                  color: FastTheme.accentGold.withValues(alpha: 0.6),
                ),
                const SizedBox(height: 16),
                Text(
                  l10n.profileLoginNeeded,
                  textAlign: TextAlign.center,
                  style: TextStyle(color: FastTheme.textMuted, fontSize: 14),
                ),
                const SizedBox(height: 20),
                GestureDetector(
                  onTap: () => Navigator.of(
                    context,
                  ).push(MaterialPageRoute(builder: (_) => const AuthScreen())),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 28,
                      vertical: 13,
                    ),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          FastTheme.accentGold,
                          FastTheme.accentGoldLight,
                        ],
                      ),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      l10n.loginTitle,
                      style: TextStyle(
                        color: FastTheme.bg,
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        automaticallyImplyLeading: !widget.embedded,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Flexible(
              child: Text(
                '@${p?.username ?? ''}',
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: FastTheme.accentGold,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            if (p?.isPro == true) ...[
              const SizedBox(width: 6),
              ProBadge(size: 15, glow: false, tooltip: l10n.proBadgeTooltip),
            ],
          ],
        ),
        actions: [
          if (!_isMe && p != null)
            IconButton(
              onPressed: _menu,
              icon: Icon(Icons.more_vert, color: FastTheme.textDim),
            ),
        ],
      ),
      body: _loading
          ? Center(
              child: CircularProgressIndicator(color: FastTheme.accentGold),
            )
          : RefreshIndicator(
              color: FastTheme.accentGold,
              backgroundColor: FastTheme.cardBg,
              onRefresh: _load,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.only(bottom: 24),
                children: [
                  _header(l10n, p),
                  if (_isMe) ...[const StoryBar(), const SizedBox(height: 8)],
                  _tabs(l10n),
                  _grid(l10n),
                ],
              ),
            ),
    );
  }

  // ── Instagram tarzı header ────────────────────────────────────────
  Widget _header(AppLocalizations l10n, SocialProfile? p) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Avatar (hikâye halkası ile)
              Container(
                padding: const EdgeInsets.all(3),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: FastTheme.accentGold, width: 2),
                ),
                child: CircleAvatar(
                  radius: 42,
                  backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
                  backgroundImage:
                      (p?.avatarUrl != null && p!.avatarUrl!.isNotEmpty)
                      ? CachedNetworkImageProvider(p.avatarUrl!)
                      : null,
                  child: (p?.avatarUrl == null || p!.avatarUrl!.isEmpty)
                      ? Text(
                          _initial(p),
                          style: TextStyle(
                            color: FastTheme.accentGold,
                            fontSize: 30,
                            fontWeight: FontWeight.w700,
                          ),
                        )
                      : null,
                ),
              ),
              const SizedBox(width: 20),
              // İstatistikler
              Expanded(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _stat(l10n.profilePosts, _posts.length),
                    _stat(l10n.profileFollowers, _followers),
                    _stat(l10n.profileFollowing, _following),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // İsim + Pro rozeti
          Row(
            children: [
              if (p?.displayName != null && p!.displayName!.isNotEmpty)
                Flexible(
                  child: Text(
                    p.displayName!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: FastTheme.text,
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              if (p?.isPro == true) ...[
                const SizedBox(width: 5),
                ProBadge(size: 19, tooltip: l10n.proBadgeTooltip),
              ],
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '@${p?.username ?? ''}',
            style: TextStyle(color: FastTheme.textDim, fontSize: 13),
          ),
          if ((p?.sunSign ?? '').isNotEmpty ||
              (p?.moonSign ?? '').isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                if ((p?.sunSign ?? '').isNotEmpty)
                  AstroSigns.chip(
                    p!.sunSign,
                    color: FastTheme.accentGold,
                    degree: p.sunDeg,
                    degreeKnown: p.birthTimeSet,
                    l10n: l10n,
                  ),
                if ((p?.moonSign ?? '').isNotEmpty)
                  AstroSigns.chip(
                    p!.moonSign,
                    color: FastTheme.accentGold,
                    degree: p.moonDeg,
                    degreeKnown: p.birthTimeSet,
                    planetSymbol: '☽',
                    l10n: l10n,
                  ),
              ],
            ),
          ],
          if (p?.isAstrologer == true) ...[
            const SizedBox(height: 6),
            Text(
              (p?.astroFields.isNotEmpty == true)
                  ? '${l10n.kunyeRoleAstrolog} · ${p!.astroFields.join(', ')}'
                  : ((p?.astroField ?? '').isEmpty
                      ? l10n.kunyeRoleAstrolog
                      : '${l10n.kunyeRoleAstrolog} · ${p!.astroField}'),
              style: TextStyle(
                color: FastTheme.accentGold,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
          if (p?.bio != null && p!.bio!.isNotEmpty) ...[
            const SizedBox(height: 8),
            _BioWithTranslate(bio: p.bio!),
          ],
          const SizedBox(height: 14),

          // Aksiyon butonları
          if (_isMe)
            Row(
              children: [
                Expanded(
                  child: _goldButton(l10n.profileEdit, () async {
                    final changed = await Navigator.of(context).push<bool>(
                      MaterialPageRoute(
                        builder: (_) => const EditSocialProfileScreen(),
                      ),
                    );
                    if (changed == true) _load();
                  }),
                ),
                const SizedBox(width: 8),
                OutlinedButton(
                  onPressed: () => _shareProfile(l10n, p),
                  style: OutlinedButton.styleFrom(
                    side: BorderSide(color: FastTheme.accentGold),
                    padding: const EdgeInsets.symmetric(
                      vertical: 13,
                      horizontal: 16,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: Icon(
                    Icons.ios_share,
                    color: FastTheme.accentGold,
                    size: 20,
                  ),
                ),
              ],
            )
          else
            Row(
              children: [
                Expanded(
                  child: _goldButton(
                    _busy
                        ? '...'
                        : (_isFollowing
                              ? l10n.profileFollowingBtn
                              : l10n.profileFollow),
                    _toggleFollow,
                    outline: _isFollowing,
                  ),
                ),
                const SizedBox(width: 8),
                _messageButton(l10n, p),
              ],
            ),

          // Holavon'a özel: doğum haritası
          if (_planets.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(
              l10n.profilePlanets,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: FastTheme.accentGold,
              ),
            ),
            const SizedBox(height: 6),
            PlanetStrip(planets: _planets),
          ],
        ],
      ),
    );
  }

  void _shareProfile(AppLocalizations l10n, SocialProfile? p) {
    final handle = p?.username ?? '';
    final text = l10n.shareProfileMessage(handle);
    Share.share(text, subject: l10n.profileShare);
  }

  /// Karşı tarafa birebir mesaj gönderme düğmesi.
  Widget _messageButton(AppLocalizations l10n, SocialProfile? p) {
    return OutlinedButton.icon(
      onPressed: (p == null || p.userId.isEmpty)
          ? null
          : () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => DmScreen(peerId: p.userId, peer: p),
              ),
            ),
      icon: Icon(
        Icons.chat_bubble_outline,
        color: FastTheme.accentGold,
        size: 20,
      ),
      label: Text(
        l10n.dmMessage,
        style: TextStyle(
          color: FastTheme.accentGold,
          fontWeight: FontWeight.w600,
        ),
      ),
      style: OutlinedButton.styleFrom(
        side: BorderSide(color: FastTheme.accentGold),
        padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  Widget _stat(String label, int value) {
    final isFollowStat = label == AppLocalizations.of(context).profileFollowers || label == AppLocalizations.of(context).profileFollowing;
    return GestureDetector(
      onTap: isFollowStat
          ? () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => FollowListScreen(
                    userId: _uid,
                    showFollowers: label == AppLocalizations.of(context).profileFollowers,
                  ),
                ),
              );
            }
          : null,
      behavior: HitTestBehavior.opaque,
      child: Column(
        children: [
          Text(
            '$value',
            style: TextStyle(
              color: FastTheme.text,
              fontSize: 18,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 2),
          Text(label, style: TextStyle(color: FastTheme.textDim, fontSize: 11)),
        ],
      ),
    );
  }

  /// Instagram tarzı sekme çubuğu (Gönderiler / Reels).
  Widget _tabs(AppLocalizations l10n) {
    return Container(
      margin: const EdgeInsets.only(top: 6),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)),
        ),
      ),
      child: Row(
        children: [
          _tabItem(Icons.grid_on, l10n.profileTabPosts, 0),
          _tabItem(Icons.play_circle_outline, l10n.profileTabReels, 1),
        ],
      ),
    );
  }

  Widget _tabItem(IconData icon, String label, int index) {
    final selected = _tab == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _tab = index),
        behavior: HitTestBehavior.opaque,
        child: Container(
          height: 44,
          decoration: BoxDecoration(
            border: Border(
              bottom: BorderSide(
                color: selected ? FastTheme.accentGold : Colors.transparent,
                width: 2,
              ),
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 22,
                color: selected ? FastTheme.text : FastTheme.textDim,
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.6,
                  color: selected ? FastTheme.text : FastTheme.textDim,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _grid(AppLocalizations l10n) {
    if (_posts.isEmpty) {
      return Padding(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: Text(
            _isMe ? l10n.profileNoPostsMe : l10n.profileNoPosts,
            textAlign: TextAlign.center,
            style: TextStyle(color: FastTheme.textMuted, fontSize: 13),
          ),
        ),
      );
    }
    final reels = _tab == 1;
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.only(top: 2),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        mainAxisSpacing: 2,
        crossAxisSpacing: 2,
        childAspectRatio: 1,
      ),
      itemCount: _posts.length,
      itemBuilder: (context, i) {
        final post = _posts[i];
        return GestureDetector(
          onTap: () => Navigator.of(
            context,
          ).push(MaterialPageRoute(builder: (_) => _PostDetail(post: post))),
          child: Stack(
            fit: StackFit.expand,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: CachedNetworkImage(
                  imageUrl: post.mediaUrl,
                  fit: BoxFit.cover,
                  placeholder: (_, __) =>
                      Container(color: FastTheme.bgSecondary),
                  errorWidget: (_, __, ___) => Container(
                    color: FastTheme.bgSecondary,
                    child: Icon(
                      Icons.broken_image,
                      color: FastTheme.textDim,
                      size: 20,
                    ),
                  ),
                ),
              ),
              if (reels)
                Positioned(
                  right: 6,
                  bottom: 6,
                  child: Icon(
                    Icons.play_circle_fill,
                    color: Colors.white.withValues(alpha: 0.85),
                    size: 18,
                  ),
                ),
              if (post.likeCount > 0)
                Positioned(
                  left: 6,
                  top: 6,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 6,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.45),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '♀',
                          style: TextStyle(
                            color: FastTheme.accentGold,
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(width: 3),
                        Text(
                          '${post.likeCount}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _goldButton(String label, VoidCallback onTap, {bool outline = false}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 42,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          gradient: outline
              ? null
              : LinearGradient(
                  colors: [FastTheme.accentGold, FastTheme.accentGoldLight],
                ),
          color: outline ? Colors.transparent : null,
          border: outline ? Border.all(color: FastTheme.border) : null,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: outline ? FastTheme.accentGold : FastTheme.bg,
            fontWeight: FontWeight.w700,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  String _initial(SocialProfile? p) {
    final n = p?.displayName ?? p?.username ?? '?';
    return n.isEmpty ? '?' : n[0].toUpperCase();
  }
}

/// Tek post detayı (grid'den tıklayınca).
class _PostDetail extends StatelessWidget {
  final PostItem post;
  const _PostDetail({required this.post});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: const SizedBox.shrink(),
      ),
      body: ListView(children: [PostCard(post: post)]),
    );
  }
}

class _BioWithTranslate extends StatefulWidget {
  final String bio;
  const _BioWithTranslate({required this.bio});

  @override
  State<_BioWithTranslate> createState() => _BioWithTranslateState();
}

class _BioWithTranslateState extends State<_BioWithTranslate> {
  bool _translating = false;
  bool _showTranslated = false;
  String _translated = '';

  Future<void> _translate() async {
    if (_showTranslated) {
      setState(() => _showTranslated = false);
      return;
    }
    setState(() => _translating = true);
    try {
      final locale = context.read<LocaleProvider>().locale;
      final res = await TranslationService.instance.translate(text: widget.bio, targetLanguageCode: locale.languageCode);
      if (mounted) {
        setState(() {
          _translated = res;
          _showTranslated = true;
          _translating = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _translating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          Text(
            _showTranslated ? _translated : widget.bio,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: FastTheme.textMuted,
              fontSize: 13,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 4),
          GestureDetector(
            onTap: _translating ? null : _translate,
            child: Text(
              _translating ? 'Çeviriliyor...' : (_showTranslated ? 'Orijinali göster' : 'Çevir'),
              style: TextStyle(color: FastTheme.accentGold, fontSize: 11, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
