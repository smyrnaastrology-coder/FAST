import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/social_provider.dart';
import '../widgets/social_nav_bar.dart';
import 'create_post_screen.dart';
import 'dm_inbox_screen.dart';
import 'feed_screen.dart';
import 'reels_screen.dart';
import 'search_users_screen.dart';
import 'social_profile_screen.dart';

/// Sosyal bölümün kabuğu: alt navigasyon çubuğu + sekmeler.
///
/// Sekmeler: Ana sayfa (akış) · Reels · Mesajlar · Arama · Profil
class SocialShell extends StatefulWidget {
  const SocialShell({super.key, this.initialIndex = SocialNavBar.tabHome});

  final int initialIndex;

  @override
  State<SocialShell> createState() => _SocialShellState();
}

class _SocialShellState extends State<SocialShell> {
  late int _index = widget.initialIndex;
  final Map<int, Widget> _pages = {};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FastTheme.bg,
      body: IndexedStack(
        index: _index,
        children: [
          _page(SocialNavBar.tabHome),
          _page(SocialNavBar.tabReels),
          _page(SocialNavBar.tabDm),
          _page(SocialNavBar.tabSearch),
          _page(SocialNavBar.tabProfile),
        ],
      ),
      bottomNavigationBar: SocialNavBar(
        index: _index,
        onTap: _onTab,
        onCreate: _create,
      ),
    );
  }

  Widget _page(int i) {
    return _pages.putIfAbsent(i, () {
      switch (i) {
        case SocialNavBar.tabHome:
          return const FeedScreen(embedded: true);
        case SocialNavBar.tabReels:
          return const ReelsScreen();
        case SocialNavBar.tabDm:
          return const DmInboxScreen(embedded: true);
        case SocialNavBar.tabSearch:
          return const SearchUsersScreen(embedded: true);
        default:
          return const SocialProfileScreen(embedded: true);
      }
    });
  }

  void _onTab(int i) {
    if (i == _index) return;
    setState(() => _index = i);
  }

  Future<void> _create() async {
    final created = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const CreatePostScreen()),
    );
    if (created == true && mounted) {
      context.read<SocialProvider>().refresh();
    }
  }
}
