import 'dart:async';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../services/social_service.dart';
import 'social_profile_screen.dart';

/// Bir kullanıcıyla birebir sohbet (DM).
class DmScreen extends StatefulWidget {
  final String peerId;
  final SocialProfile? peer;
  const DmScreen({super.key, required this.peerId, this.peer});

  @override
  State<DmScreen> createState() => _DmScreenState();
}

class _DmScreenState extends State<DmScreen> {
  final _ctrl = TextEditingController();
  final _scroll = ScrollController();
  List<DmMessage> _msgs = [];
  SocialProfile? _peer;
  bool _loading = true;
  bool _sending = false;
  Timer? _poll;

  @override
  void initState() {
    super.initState();
    _peer = widget.peer;
    _load();
    // Karşı tarafın mesajını beklemeden görmek için basit yoklama.
    _poll = Timer.periodic(const Duration(seconds: 4), (_) => _load(silent: true));
  }

  @override
  void dispose() {
    _poll?.cancel();
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _load({bool silent = false}) async {
    final list = await SocialService.fetchConversation(widget.peerId);
    if (!mounted) return;
    final grew = list.length > _msgs.length;
    setState(() {
      _msgs = list;
      _loading = false;
    });
    if (grew) _scrollDown();
    if (!silent) await SocialService.markConversationRead(widget.peerId);
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      }
    });
  }

  Future<void> _send() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() => _sending = true);
    try {
      await SocialService.sendMessage(widget.peerId, text);
      _ctrl.clear();
      await _load();
    } catch (e) {
      if (mounted) {
        final l10n = AppLocalizations.of(context);
        final blocked = e is StateError && e.message == 'blocked';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(blocked ? l10n.dmBlocked : l10n.dmSendError)),
        );
        if (blocked) await _load();
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final me = SocialService.currentUserId;
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        titleSpacing: 0,
        title: GestureDetector(
          onTap: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => SocialProfileScreen(userId: widget.peerId)),
          ),
          child: Row(
            children: [
              CircleAvatar(
                radius: 16,
                backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
                backgroundImage: (_peer?.avatarUrl != null && _peer!.avatarUrl!.isNotEmpty)
                    ? CachedNetworkImageProvider(_peer!.avatarUrl!)
                    : null,
                child: (_peer?.avatarUrl == null || _peer!.avatarUrl!.isEmpty)
                    ? Text(_initial(_peer), style: TextStyle(color: FastTheme.accentGold, fontSize: 13, fontWeight: FontWeight.w700))
                    : null,
              ),
              const SizedBox(width: 10),
              Flexible(
                child: Text(
                  _peer == null ? l10n.dmTitle : '@${_peer!.username}',
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(color: FastTheme.accentGold, fontSize: 17, fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: _loading
                ? Center(child: CircularProgressIndicator(color: FastTheme.accentGold))
                : _msgs.isEmpty
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(32),
                          child: Text(
                            l10n.dmEmpty,
                            textAlign: TextAlign.center,
                            style: TextStyle(color: FastTheme.textMuted, fontSize: 13.5, height: 1.5),
                          ),
                        ),
                      )
                    : ListView.builder(
                        controller: _scroll,
                        padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
                        itemCount: _msgs.length,
                        itemBuilder: (_, i) => _bubble(_msgs[i], mine: _msgs[i].senderId == me),
                      ),
          ),
          SafeArea(
            child: Container(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
              decoration: BoxDecoration(
                color: FastTheme.bgSecondary,
                border: Border(top: BorderSide(color: FastTheme.border)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _ctrl,
                      style: TextStyle(color: FastTheme.text),
                      maxLength: 2000,
                      minLines: 1,
                      maxLines: 5,
                      textInputAction: TextInputAction.newline,
                      decoration: InputDecoration(
                        hintText: l10n.dmHint,
                        counterText: '',
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: _sending ? null : _send,
                    icon: _sending
                        ? SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(color: FastTheme.accentGold, strokeWidth: 2))
                        : Icon(Icons.send, color: FastTheme.accentGold),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _bubble(DmMessage m, {required bool mine}) {
    final l10n = AppLocalizations.of(context);
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: const BoxConstraints(maxWidth: 320),
        decoration: BoxDecoration(
          color: mine ? FastTheme.accentGold : FastTheme.cardBg,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(mine ? 16 : 4),
            bottomRight: Radius.circular(mine ? 4 : 16),
          ),
          border: mine ? null : Border.all(color: FastTheme.border),
        ),
        child: Column(
          crossAxisAlignment: mine ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Text(
              m.text,
              style: TextStyle(
                color: mine ? FastTheme.bg : FastTheme.text,
                fontSize: 14,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              _time(m.createdAt),
              style: TextStyle(
                color: mine ? FastTheme.bg.withValues(alpha: 0.65) : FastTheme.textDim,
                fontSize: 10,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _time(DateTime t) {
    final l10n = AppLocalizations.of(context);
    final now = DateTime.now();
    final diff = now.difference(t);
    if (diff.inMinutes < 1) return l10n.timeJustNow;
    if (diff.inHours < 1) return l10n.timeMinutes(diff.inMinutes);
    final hh = t.hour.toString().padLeft(2, '0');
    final mm = t.minute.toString().padLeft(2, '0');
    return '$hh:$mm';
  }

  String _initial(SocialProfile? a) {
    final n = a?.displayName ?? a?.username ?? '?';
    return n.isEmpty ? '?' : n[0].toUpperCase();
  }
}
