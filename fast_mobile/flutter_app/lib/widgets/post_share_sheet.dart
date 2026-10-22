import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image/image.dart' as img;
import 'package:share_plus/share_plus.dart';

import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../services/social_service.dart';

/// Gönderi paylaşım menüsü: DM ile gönder, hikâyeye ekle, sistem paylaşımı.
Future<void> showPostShareSheet(BuildContext context, PostItem post) async {
  final l10n = AppLocalizations.of(context);
  await showModalBottomSheet<void>(
    context: context,
    backgroundColor: FastTheme.bgSecondary,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (ctx) => SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 8),
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: FastTheme.textDim,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            l10n.postShareTitle,
            style: TextStyle(
              color: FastTheme.text,
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          ListTile(
            leading: Icon(Icons.send_outlined, color: FastTheme.accentGold),
            title: Text(
              l10n.postShareSend,
              style: TextStyle(color: FastTheme.text, fontSize: 14),
            ),
            onTap: () {
              Navigator.pop(ctx);
              _pickRecipient(context, post);
            },
          ),
          ListTile(
            leading: Icon(
              Icons.add_circle_outline,
              color: FastTheme.accentGold,
            ),
            title: Text(
              l10n.postShareStory,
              style: TextStyle(color: FastTheme.text, fontSize: 14),
            ),
            onTap: () {
              Navigator.pop(ctx);
              _repostToStory(context, post);
            },
          ),
          ListTile(
            leading: Icon(Icons.ios_share, color: FastTheme.accentGold),
            title: Text(
              l10n.postShareSystem,
              style: TextStyle(color: FastTheme.text, fontSize: 14),
            ),
            onTap: () {
              Navigator.pop(ctx);
              Share.share(_shareText(post), subject: l10n.postShareTitle);
            },
          ),
          const SizedBox(height: 12),
        ],
      ),
    ),
  );
}

String _shareText(PostItem post) {
  final cap = (post.caption ?? '').trim();
  return cap.isEmpty ? post.mediaUrl : '$cap\n${post.mediaUrl}';
}

Future<void> _pickRecipient(BuildContext context, PostItem post) async {
  final l10n = AppLocalizations.of(context);
  final messenger = ScaffoldMessenger.of(context);
  List<SocialProfile> people;
  try {
    people = await SocialService.followingProfiles();
  } catch (_) {
    people = const [];
  }
  if (!context.mounted) return;
  await showModalBottomSheet<void>(
    context: context,
    backgroundColor: FastTheme.bgSecondary,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (ctx) => SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
            child: Text(
              l10n.shareToTitle,
              style: TextStyle(
                color: FastTheme.text,
                fontSize: 15,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          if (people.isEmpty)
            Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                l10n.shareNoFollowing,
                style: TextStyle(color: FastTheme.textMuted),
              ),
            )
          else
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: people.length,
                itemBuilder: (_, i) {
                  final p = people[i];
                  return ListTile(
                    leading: CircleAvatar(
                      backgroundColor: FastTheme.cardBg,
                      backgroundImage: (p.avatarUrl ?? '').isEmpty
                          ? null
                          : NetworkImage(p.avatarUrl!),
                      child: (p.avatarUrl ?? '').isEmpty
                          ? Icon(Icons.person, color: FastTheme.textDim)
                          : null,
                    ),
                    title: Text(
                      p.displayName?.isNotEmpty == true
                          ? p.displayName!
                          : '@${p.username}',
                      style: TextStyle(color: FastTheme.text, fontSize: 14),
                    ),
                    subtitle: Text(
                      '@${p.username}',
                      style: TextStyle(color: FastTheme.textDim, fontSize: 12),
                    ),
                    onTap: () async {
                      Navigator.pop(ctx);
                      try {
                        await SocialService.sendMessage(
                          p.userId,
                          _shareText(post),
                        );
                        messenger.showSnackBar(
                          SnackBar(content: Text(l10n.shareSent)),
                        );
                      } catch (_) {
                        messenger.showSnackBar(
                          SnackBar(content: Text(l10n.shareFailed)),
                        );
                      }
                    },
                  );
                },
              ),
            ),
          const SizedBox(height: 12),
        ],
      ),
    ),
  );
}

Future<void> _repostToStory(BuildContext context, PostItem post) async {
  final l10n = AppLocalizations.of(context);
  final messenger = ScaffoldMessenger.of(context);
  showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (_) =>
        Center(child: CircularProgressIndicator(color: FastTheme.accentGold)),
  );
  try {
    final bytes = await _renderRepost(post);
    await SocialService.uploadStory(
      bytes,
      mentionIds: post.author == null ? const [] : [post.author!.userId],
    );
    if (!context.mounted) return;
    Navigator.of(context, rootNavigator: true).pop();
    messenger.showSnackBar(SnackBar(content: Text(l10n.storyRepostAdded)));
  } catch (_) {
    if (!context.mounted) return;
    Navigator.of(context, rootNavigator: true).pop();
    messenger.showSnackBar(SnackBar(content: Text(l10n.storyRepostFailed)));
  }
}

/// Gönderi görselini indirir, altına "via @kullanıcı" şeridi ekler ve JPEG döner.
Future<Uint8List> _renderRepost(PostItem post) async {
  final res = await http.get(Uri.parse(post.mediaUrl));
  if (res.statusCode != 200) throw StateError('download_failed');
  var decoded = img.decodeImage(res.bodyBytes);
  if (decoded == null) throw StateError('decode_failed');
  decoded = img.bakeOrientation(decoded);
  if (decoded.width > 1080) {
    decoded = img.copyResize(decoded, width: 1080);
  }
  final h = decoded.height;
  final w = decoded.width;
  final strip = (h * 0.12).clamp(90, 160).toInt();
  img.fillRect(
    decoded,
    x1: 0,
    y1: h - strip,
    x2: w,
    y2: h,
    color: img.ColorRgba8(0, 0, 0, 130),
  );
  final handle = post.author?.username ?? '';
  final label = handle.isEmpty ? 'Holavon' : 'via @$handle';
  img.drawString(
    decoded,
    label,
    font: img.arial24,
    x: 28,
    y: h - strip ~/ 2 - 8,
    color: img.ColorRgba8(255, 255, 255, 255),
  );
  return Uint8List.fromList(img.encodeJpg(decoded, quality: 90));
}
