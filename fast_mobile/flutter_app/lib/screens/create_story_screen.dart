import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show PlatformException;
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
import '../services/social_service.dart';
import '../widgets/image_editor.dart';
import '../widgets/media_source_sheet.dart';

/// Hikâye oluşturma: 9:16 foto düzenle + isteğe bağlı kullanıcı etiketle.
class CreateStoryScreen extends StatefulWidget {
  const CreateStoryScreen({super.key});

  @override
  State<CreateStoryScreen> createState() => _CreateStoryScreenState();
}

class _CreateStoryScreenState extends State<CreateStoryScreen> {
  final _editorKey = GlobalKey<ImageEditorState>();
  Uint8List? _bytes;
  bool _busy = false;
  String? _error;
  final List<SocialProfile> _mentions = [];

  Future<void> _chooseSource() async {
    final source = await showMediaSourceSheet(context);
    if (source == null || !mounted) return;
    await _pick(source);
  }

  Future<void> _pick(ImageSource source) async {
    final l10n = AppLocalizations.of(context);
    try {
      final file = await ImagePicker().pickImage(source: source, maxWidth: 1600, imageQuality: 85);
      if (file == null) return;
      final bytes = await file.readAsBytes();
      if (!mounted) return;
      setState(() {
        _bytes = bytes;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      final denied = e is PlatformException && e.code.toLowerCase().contains('camera');
      setState(() => _error = denied ? l10n.mediaCameraDenied : l10n.mediaPickError);
    }
  }

  Future<void> _pickMention() async {
    final picked = await showModalBottomSheet<SocialProfile>(
      context: context,
      backgroundColor: FastTheme.cardBg,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) => const _MentionPicker(),
    );
    if (picked != null && mounted) {
      if (_mentions.any((m) => m.userId == picked.userId)) return;
      setState(() => _mentions.add(picked));
    }
  }

  Future<void> _share() async {
    final l10n = AppLocalizations.of(context);
    if (_bytes == null) {
      setState(() => _error = l10n.createPostNoImage);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      Uint8List out = _bytes!;
      if (_editorKey.currentState != null) out = await _editorKey.currentState!.render();
      await SocialService.uploadStory(out, mentionIds: [for (final m in _mentions) m.userId]);
      if (!mounted) return;
      context.read<SocialProvider>().refreshStories();
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      final tooBig = e is StateError && e.message == 'file_too_large';
      setState(() => _error = tooBig ? l10n.fileTooLarge : l10n.createPostError);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text(l10n.storyCreateTitle, style: TextStyle(color: FastTheme.accentGold, fontSize: 18)),
        actions: [
          TextButton(
            onPressed: _busy ? null : _share,
            child: _busy
                ? SizedBox(height: 18, width: 18, child: CircularProgressIndicator(color: FastTheme.accentGold, strokeWidth: 2))
                : Text(l10n.createPostShare, style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_bytes == null)
            GestureDetector(
              onTap: _chooseSource,
              child: Container(
                height: 360,
                decoration: BoxDecoration(
                  color: FastTheme.bgSecondary,
                  border: Border.all(color: FastTheme.border),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.auto_awesome, size: 56, color: FastTheme.accentGold),
                    const SizedBox(height: 12),
                    Text(l10n.createPostPick, style: TextStyle(color: FastTheme.textMuted, fontSize: 14)),
                  ],
                ),
              ),
            )
          else ...[
            ImageEditor(key: _editorKey, bytes: _bytes!, aspect: 9 / 16, outputWidth: 1080),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _chooseSource,
              icon: Icon(Icons.photo_camera_outlined, color: FastTheme.accentGold, size: 20),
              label: Text(l10n.mediaChange, style: TextStyle(color: FastTheme.accentGold)),
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: FastTheme.border),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ],
          const SizedBox(height: 16),
          // ── Etiketleme ──
          OutlinedButton.icon(
            onPressed: _pickMention,
            icon: Icon(Icons.alternate_email, color: FastTheme.accentGold, size: 20),
            label: Text(l10n.storyMention, style: TextStyle(color: FastTheme.accentGold)),
            style: OutlinedButton.styleFrom(
              side: BorderSide(color: FastTheme.border),
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          if (_mentions.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final m in _mentions)
                  Chip(
                    label: Text('@${m.username}', style: TextStyle(color: FastTheme.text, fontSize: 12)),
                    backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
                    deleteIconColor: FastTheme.textDim,
                    onDeleted: () => setState(() => _mentions.remove(m)),
                  ),
              ],
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: TextStyle(color: FastTheme.error, fontSize: 13)),
          ],
        ],
      ),
    );
  }
}

/// Hikâyede etiketlenecek kişiyi arayıp seç.
class _MentionPicker extends StatefulWidget {
  const _MentionPicker();

  @override
  State<_MentionPicker> createState() => _MentionPickerState();
}

class _MentionPickerState extends State<_MentionPicker> {
  final _q = TextEditingController();
  List<SocialProfile> _res = [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _search('');
    _q.addListener(() => _search(_q.text));
  }

  @override
  void dispose() {
    _q.dispose();
    super.dispose();
  }

  Future<void> _search(String q) async {
    setState(() => _loading = true);
    final r = await SocialService.searchUsers(q);
    if (mounted) setState(() {
      _res = r;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: Container(
          padding: const EdgeInsets.all(16),
          constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.6),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _q,
                style: TextStyle(color: FastTheme.text),
                decoration: InputDecoration(hintText: l10n.searchHint, prefixIcon: Icon(Icons.search, color: FastTheme.textDim)),
              ),
              const SizedBox(height: 8),
              if (_loading)
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: CircularProgressIndicator(color: FastTheme.accentGold),
                )
              else
                Flexible(
                  child: ListView.builder(
                    shrinkWrap: true,
                    itemCount: _res.length,
                    itemBuilder: (ctx, i) {
                      final p = _res[i];
                      return ListTile(
                        dense: true,
                        leading: CircleAvatar(
                          backgroundColor: FastTheme.accentGold.withValues(alpha: 0.15),
                          child: Text((p.username.isNotEmpty ? p.username[0] : '?').toUpperCase(),
                              style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.w700)),
                        ),
                        title: Text('@${p.username}', style: TextStyle(color: FastTheme.text)),
                        subtitle: p.displayName == null || p.displayName!.isEmpty
                            ? null
                            : Text(p.displayName!, style: TextStyle(color: FastTheme.textDim, fontSize: 12)),
                        onTap: () => Navigator.pop(context, p),
                      );
                    },
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
