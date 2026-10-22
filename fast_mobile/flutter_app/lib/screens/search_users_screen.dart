import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../services/social_service.dart';
import '../widgets/user_tile.dart';

/// Kişi arama / takip etme ekranı.
class SearchUsersScreen extends StatefulWidget {
  /// Alt navigasyon cubugu icinde gosteriliyorsa geri oku gizlenir.
  final bool embedded;
  const SearchUsersScreen({super.key, this.embedded = false});

  @override
  State<SearchUsersScreen> createState() => _SearchUsersScreenState();
}

class _SearchUsersScreenState extends State<SearchUsersScreen> {
  final _ctrl = TextEditingController();
  List<SocialProfile> _results = [];
  bool _loading = false;
  bool _searched = false;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Future<void> _search(String q) async {
    if (q.trim().isEmpty) {
      setState(() {
        _results = [];
        _searched = false;
      });
      return;
    }
    setState(() => _loading = true);
    final r = await SocialService.searchUsers(q);
    if (!mounted) return;
    setState(() {
      _results = r;
      _loading = false;
      _searched = true;
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
        title: TextField(
          controller: _ctrl,
          autofocus: true,
          style: TextStyle(color: FastTheme.text),
          onChanged: _search,
          decoration: InputDecoration(
            hintText: l10n.searchHint,
            border: InputBorder.none,
            hintStyle: TextStyle(color: FastTheme.textDim),
          ),
        ),
        actions: [
          IconButton(
            onPressed: () => _search(_ctrl.text),
            icon: Icon(Icons.search, color: FastTheme.accentGold),
          ),
        ],
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator(color: FastTheme.accentGold))
          : _results.isEmpty
              ? Center(
                  child: Text(
                    _searched ? l10n.searchEmpty : l10n.searchPrompt,
                    style: TextStyle(color: FastTheme.textMuted, fontSize: 14),
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  itemCount: _results.length,
                  separatorBuilder: (_, __) => Divider(color: FastTheme.border, height: 1),
                  itemBuilder: (_, i) => UserTile(profile: _results[i]),
                ),
    );
  }
}
