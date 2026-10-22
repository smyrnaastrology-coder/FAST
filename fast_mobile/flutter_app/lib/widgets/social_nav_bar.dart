import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/social_provider.dart';
import '../services/social_service.dart';

/// Sosyal bölümün Instagram tarzı alt navigasyon çubuğu.
///
/// [index]    → seçili sekme
/// [onTap]   → sekme değiştirme callback'i
/// [onCreate]→ ortadaki "+" (paylaş) butonu
class SocialNavBar extends StatelessWidget {
  final int index;
  final ValueChanged<int> onTap;
  final VoidCallback onCreate;

  const SocialNavBar({
    super.key,
    required this.index,
    required this.onTap,
    required this.onCreate,
  });

  static const int tabHome = 0;
  static const int tabReels = 1;
  static const int tabDm = 2;
  static const int tabSearch = 3;
  static const int tabProfile = 4;

  @override
  Widget build(BuildContext context) {
    final my = context.watch<SocialProvider>().myProfile;
    return Container(
      decoration: BoxDecoration(
        color: FastTheme.bgSecondary,
        border: Border(top: BorderSide(color: FastTheme.border.withValues(alpha: 0.6))),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 58,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _item(Icons.home_outlined, Icons.home, index == tabHome, () => onTap(tabHome)),
              _item(Icons.play_circle_outline, Icons.play_circle, index == tabReels, () => onTap(tabReels)),
              _create(onCreate),
              _item(Icons.chat_bubble_outline, Icons.chat_bubble, index == tabDm, () => onTap(tabDm)),
              _item(Icons.search, Icons.search, index == tabSearch, () => onTap(tabSearch)),
              _avatar(my, index == tabProfile, () => onTap(tabProfile)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _item(IconData icon, IconData activeIcon, bool selected, VoidCallback onTap) {
    return IconButton(
      onPressed: onTap,
      icon: Icon(selected ? activeIcon : icon, color: selected ? FastTheme.accentGold : FastTheme.textDim, size: 26),
    );
  }

  Widget _create(VoidCallback onTap) => GestureDetector(
        onTap: onTap,
        child: Container(
          width: 42,
          height: 30,
          decoration: BoxDecoration(
            color: FastTheme.accentGold,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(Icons.add, color: FastTheme.bg, size: 24),
        ),
      );

  Widget _avatar(SocialProfile? p, bool selected, VoidCallback onTap) {
    final url = p?.avatarUrl;
    final hasImage = url != null && url.isNotEmpty;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(2),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: selected ? FastTheme.accentGold : Colors.transparent,
            width: 2,
          ),
        ),
        child: CircleAvatar(
          radius: 17,
          backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
          backgroundImage: hasImage ? CachedNetworkImageProvider(url) : null,
          child: hasImage
              ? null
              : Text(
                  (p?.username.isNotEmpty == true ? p!.username[0] : '?').toUpperCase(),
                  style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700, fontSize: 14),
                ),
        ),
      ),
    );
  }
}
