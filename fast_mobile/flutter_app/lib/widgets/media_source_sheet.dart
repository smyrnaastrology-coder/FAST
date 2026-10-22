import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../config/theme.dart';
import '../l10n/app_localizations.dart';

/// Post/hikâye için fotoğraf kaynağı seçimi (kamera / galeri).
///
/// Seçim yapılmadan kapatılırsa `null` döner.
Future<ImageSource?> showMediaSourceSheet(BuildContext context) {
  final l10n = AppLocalizations.of(context);

  return showModalBottomSheet<ImageSource>(
    context: context,
    backgroundColor: FastTheme.cardBg,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
    builder: (ctx) {
      Widget tile(IconData icon, String label, ImageSource source) => ListTile(
            leading: Icon(icon, color: FastTheme.accentGold),
            title: Text(label, style: TextStyle(color: FastTheme.text, fontSize: 15)),
            onTap: () => Navigator.pop(ctx, source),
          );

      return SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 6),
              child: Text(
                l10n.mediaSourceTitle,
                style: TextStyle(color: FastTheme.textMuted, fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 0.4),
              ),
            ),
            tile(Icons.photo_camera_outlined, l10n.mediaCamera, ImageSource.camera),
            tile(Icons.photo_library_outlined, l10n.mediaGallery, ImageSource.gallery),
            const SizedBox(height: 6),
          ],
        ),
      );
    },
  );
}
