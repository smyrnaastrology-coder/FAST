import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
import '../widgets/post_card.dart';
import '../widgets/story_bar.dart';
import 'create_post_screen.dart';

/// Topluluk akışı: yatay yenile + sonsuz kaydırma + oluştur butonu.
class FeedScreen extends StatefulWidget {
  /// Alt navigasyon cubugu icinde gosteriliyorsa geri oku gizlenir.
  final bool embedded;
  const FeedScreen({super.key, this.embedded = false});

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  final _scroll = ScrollController();

  @override
  void initState() {
    super.initState();
    _scroll.addListener(_onScroll);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final sp = context.read<SocialProvider>();
      if (sp.feed.isEmpty && sp.status != SocialStatus.loading) sp.refresh();
    });
  }

  void _onScroll() {
    if (_scroll.position.pixels > _scroll.position.maxScrollExtent - 400) {
      context.read<SocialProvider>().loadMore();
    }
  }

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final sp = context.watch<SocialProvider>();

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        automaticallyImplyLeading: !widget.embedded,
        title: Text(
          l10n.navCommunity,
          style: TextStyle(
            color: FastTheme.accentGold,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(44),
          child: Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: SegmentedButton<bool>(
              segments: [
                ButtonSegment(value: true, label: Text(l10n.feedFollowingTab)),
                ButtonSegment(value: false, label: Text(l10n.feedDiscoverTab)),
              ],
              selected: {sp.followingOnly},
              showSelectedIcon: false,
              style: ButtonStyle(
                visualDensity: VisualDensity.compact,
                textStyle: WidgetStatePropertyAll(
                  TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                ),
              ),
              onSelectionChanged: (v) =>
                  context.read<SocialProvider>().setFollowingOnly(v.first),
            ),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final created = await Navigator.of(context).push<bool>(
            MaterialPageRoute(builder: (_) => const CreatePostScreen()),
          );
          if (created == true) context.read<SocialProvider>().refresh();
        },
        backgroundColor: FastTheme.accentGold,
        child: Icon(Icons.add_a_photo, color: FastTheme.bg),
      ),
      body: _body(sp, l10n),
    );
  }

  Widget _body(SocialProvider sp, AppLocalizations l10n) {
    if (sp.status == SocialStatus.loading && sp.feed.isEmpty) {
      return Center(
        child: CircularProgressIndicator(color: FastTheme.accentGold),
      );
    }
    // Gerçek hata durumu: "boş feed" gibi gösterilmez, tekrar denenebilir.
    if (sp.status == SocialStatus.error && sp.feed.isEmpty) {
      return _errorState(sp, l10n);
    }
    if (sp.feed.isEmpty) {
      return RefreshIndicator(
        color: FastTheme.accentGold,
        backgroundColor: FastTheme.cardBg,
        onRefresh: sp.refresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            const StoryBar(),
            const SizedBox(height: 60),
            Icon(Icons.people_outline, size: 64, color: FastTheme.textDim),
            const SizedBox(height: 16),
            Text(
              sp.followingOnly ? l10n.feedFollowingEmpty : l10n.feedEmpty,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 15, color: FastTheme.textMuted),
            ),
            const SizedBox(height: 8),
            Text(
              l10n.feedEmptyHint,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                color: FastTheme.textDim,
                height: 1.4,
              ),
            ),
            if (sp.followingOnly) ...[
              const SizedBox(height: 20),
              TextButton(
                onPressed: () =>
                    context.read<SocialProvider>().setFollowingOnly(false),
                child: Text(
                  l10n.feedDiscoverCta,
                  style: TextStyle(
                    color: FastTheme.accentGold,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ],
        ),
      );
    }
    return RefreshIndicator(
      color: FastTheme.accentGold,
      backgroundColor: FastTheme.cardBg,
      onRefresh: sp.refresh,
      child: ListView.builder(
        controller: _scroll,
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 90),
        itemCount: sp.feed.length + 1 + (sp.loadingMore ? 1 : 0),
        itemBuilder: (context, i) {
          if (i == 0) return const StoryBar();
          if (i > sp.feed.length) {
            return Padding(
              padding: const EdgeInsets.all(16),
              child: Center(
                child: CircularProgressIndicator(color: FastTheme.accentGold),
              ),
            );
          }
          return PostCard(post: sp.feed[i - 1]);
        },
      ),
    );
  }

  /// Bağlantı / sunucu hatası ekranı — "tekrar dene" butonu ile.
  Widget _errorState(SocialProvider sp, AppLocalizations l10n) {
    final isNet = sp.error == 'net';
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isNet ? Icons.wifi_off_rounded : Icons.cloud_off_rounded,
              size: 60,
              color: FastTheme.accentGold.withValues(alpha: 0.65),
            ),
            const SizedBox(height: 16),
            Text(
              isNet ? l10n.socialErrorNetwork : l10n.socialErrorServer,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: FastTheme.text,
                fontSize: 15,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              l10n.socialErrorHint,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: FastTheme.textMuted,
                fontSize: 12.5,
                height: 1.45,
              ),
            ),
            const SizedBox(height: 22),
            GestureDetector(
              onTap: () => sp.refresh(),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 26,
                  vertical: 13,
                ),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [FastTheme.accentGold, FastTheme.accentGoldLight],
                  ),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.refresh, color: FastTheme.bg, size: 18),
                    const SizedBox(width: 8),
                    Text(
                      l10n.socialRetry,
                      style: TextStyle(
                        color: FastTheme.bg,
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
