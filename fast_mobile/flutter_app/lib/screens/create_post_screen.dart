import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show PlatformException;
import 'package:image_picker/image_picker.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../services/social_service.dart';
import '../widgets/image_editor.dart';
import '../widgets/media_source_sheet.dart';

/// Yeni post oluşturma: galeriden foto seç (zoom/döndür ile düzenle) veya
/// [initialBytes] ile (harita paylaşımı) gelen görseli yayımla.
class CreatePostScreen extends StatefulWidget {
  final Uint8List? initialBytes;
  final bool isChart;
  const CreatePostScreen({super.key, this.initialBytes, this.isChart = false});

  @override
  State<CreatePostScreen> createState() => _CreatePostScreenState();
}

class _CreatePostScreenState extends State<CreatePostScreen> {
  final _caption = TextEditingController();
  final _editorKey = GlobalKey<ImageEditorState>();
  Uint8List? _bytes;
  bool _isChart = false;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _bytes = widget.initialBytes;
    _isChart = widget.isChart;
  }

  @override
  void dispose() {
    _caption.dispose();
    super.dispose();
  }

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
        _isChart = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      final denied = e is PlatformException && e.code.toLowerCase().contains('camera');
      setState(() => _error = denied ? l10n.mediaCameraDenied : l10n.mediaPickError);
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
      // Fotoysa editör transformunu uygula; harita ise orijinali koru.
      // Foto JPEG (q85) olarak kaydedilir — PNG 10-20 kat yer kaplar.
      Uint8List out = _bytes!;
      var ext = _isChart ? 'png' : 'jpg';
      if (!_isChart && _editorKey.currentState != null) {
        out = await _editorKey.currentState!.render();
        ext = 'jpg';
      }
      final url = await SocialService.uploadImageBytes(out, ext: ext);
      await SocialService.createPost(mediaUrl: url, caption: _caption.text.trim(), isChart: _isChart);
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
        title: Text(l10n.createPostTitle, style: TextStyle(color: FastTheme.accentGold, fontSize: 18)),
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
          // ── Görsel önizleme / düzenle ──
          if (_bytes == null)
            GestureDetector(
              onTap: _chooseSource,
              child: Container(
                height: 260,
                decoration: BoxDecoration(
                  color: FastTheme.bgSecondary,
                  border: Border.all(color: FastTheme.border),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.add_photo_alternate_outlined, size: 56, color: FastTheme.accentGold),
                    const SizedBox(height: 12),
                    Text(l10n.createPostPick, style: TextStyle(color: FastTheme.textMuted, fontSize: 14)),
                  ],
                ),
              ),
            )
          else ...[
            if (_isChart)
              // Harita: kırpma/döndürme yok, orijinal önizleme.
              ClipRRect(
                borderRadius: BorderRadius.circular(14),
                child: AspectRatio(
                  aspectRatio: 1,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      Image.memory(_bytes!, fit: BoxFit.contain, color: Colors.black, colorBlendMode: BlendMode.multiply),
                      Positioned(
                        top: 10,
                        left: 10,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(color: FastTheme.accentGold, borderRadius: BorderRadius.circular(8)),
                          child: Text(l10n.createPostChartBadge,
                              style: TextStyle(color: FastTheme.bg, fontSize: 11, fontWeight: FontWeight.w700)),
                        ),
                      ),
                    ],
                  ),
                ),
              )
            else ...[
              ImageEditor(key: _editorKey, bytes: _bytes!, aspect: 1.0, outputWidth: 1080),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.zoom_in_outlined, size: 15, color: FastTheme.textDim),
                  const SizedBox(width: 6),
                  Text(l10n.editImageHint, style: TextStyle(color: FastTheme.textDim, fontSize: 11)),
                ],
              ),
            ],
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
          TextField(
            controller: _caption,
            style: TextStyle(color: FastTheme.text),
            maxLines: 3,
            maxLength: 500,
            decoration: InputDecoration(
              hintText: l10n.createPostCaptionHint,
              counterStyle: TextStyle(color: FastTheme.textDim, fontSize: 11),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: TextStyle(color: FastTheme.error, fontSize: 13)),
          ],
        ],
      ),
    );
  }
}
