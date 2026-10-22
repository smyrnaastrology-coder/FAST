import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../services/social_service.dart';
import 'dm_screen.dart';

/// Gelen kutusu: birebir mesaj konuşmaları.
class DmInboxScreen extends StatefulWidget {
  /// Alt navigasyon cubugu icinde gosteriliyorsa geri oku gizlenir.
  final bool embedded;
  const DmInboxScreen({super.key, this.embedded = false});

  @override
  State<DmInboxScreen> createState() => _DmInboxScreenState();
}

class _DmInboxScreenState extends State<DmInboxScreen> {
  List<DmConversation> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final r = await SocialService.fetchInbox();
    if (!mounted) return;
    setState(() {
      _items = r;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        automaticallyImplyLeading: !widget.embedded,
        title: Text(l10n.dmInboxTitle, style: TextStyle(color: FastTheme.accentGold, fontSize: 18)),
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator(color: FastTheme.accentGold))
          : _items.isEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Text(
                      l10n.dmInboxEmpty,
                      textAlign: TextAlign.center,
                      style: TextStyle(color: FastTheme.textMuted, fontSize: 13.5, height: 1.5),
                    ),
                  ),
                )
              : RefreshIndicator(
                  color: FastTheme.accentGold,
                  backgroundColor: FastTheme.bgSecondary,
                  onRefresh: _load,
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    itemCount: _items.length,
                    separatorBuilder: (_, __) => Divider(height: 1, color: FastTheme.border),
                    itemBuilder: (_, i) => _tile(_items[i]),
                  ),
                ),
    );
  }

  Widget _tile(DmConversation c) {
    final l10n = AppLocalizations.of(context);
    final p = c.peer;
    return ListTile(
      onTap: () async {
        await Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => DmScreen(peerId: c.peerId, peer: p)),
        );
        if (mounted) _load();
      },
      leading: Stack(
        clipBehavior: Clip.none,
        children: [
          CircleAvatar(
            radius: 24,
            backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
            backgroundImage: (p?.avatarUrl != null && p!.avatarUrl!.isNotEmpty)
                ? CachedNetworkImageProvider(p.avatarUrl!)
                : null,
            child: (p?.avatarUrl == null || p!.avatarUrl!.isEmpty)
                ? Text(_initial(p), style: TextStyle(color: FastTheme.accentGold, fontSize: 18, fontWeight: FontWeight.w700))
                : null,
          ),
          if (c.unread > 0)
            Positioned(
              right: -4,
              top: -4,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                constraints: const BoxConstraints(minWidth: 20),
                decoration: BoxDecoration(
                  color: FastTheme.accentGold,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  c.unread > 99 ? '99+' : '${c.unread}',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: FastTheme.bg, fontSize: 11, fontWeight: FontWeight.w700),
                ),
              ),
            ),
        ],
      ),
      title: Text(
        '@${p?.username ?? '?'}',
        style: TextStyle(
          color: c.unread > 0 ? FastTheme.accentGold : FastTheme.text,
          fontSize: 14.5,
          fontWeight: c.unread > 0 ? FontWeight.w700 : FontWeight.w600,
        ),
      ),
      subtitle: Text(
        c.lastText,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(color: FastTheme.textMuted, fontSize: 13),
      ),
      trailing: Text(
        _ago(c.lastAt),
        style: TextStyle(color: FastTheme.textDim, fontSize: 11),
      ),
    );
  }

  String _ago(DateTime t) {
    final l10n = AppLocalizations.of(context);
    final diff = DateTime.now().difference(t);
    if (diff.inMinutes < 1) return l10n.timeJustNow;
    if (diff.inHours < 1) return l10n.timeMinutes(diff.inMinutes);
    if (diff.inDays < 1) return l10n.timeHours(diff.inHours);
    return l10n.timeDays(diff.inDays);
  }

  String _initial(SocialProfile? a) {
    final n = a?.displayName ?? a?.username ?? '?';
    return n.isEmpty ? '?' : n[0].toUpperCase();
  }
}
