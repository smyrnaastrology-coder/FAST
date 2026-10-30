import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

/// One editable draft, stored locally on this device.
class StoryDraftService {
  static const _key = 'story_editor_draft_v1';

  static Future<Map<String, dynamic>?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return null;
    final draft = jsonDecode(raw) as Map<String, dynamic>;
    if (!await File(draft['image'] as String).exists()) {
      throw const FileSystemException('Taslak fotoğrafı bulunamadı');
    }
    return draft;
  }

  static Future<void> save(String imagePath, Map<String, dynamic> state) async {
    final prefs = await SharedPreferences.getInstance();
    final old = prefs.getString(_key);
    final dir = await getApplicationDocumentsDirectory();
    final image = File('${dir.path}/story_draft_${const Uuid().v4()}');
    await File(imagePath).copy(image.path);
    try {
      final ok = await prefs.setString(
        _key,
        jsonEncode({...state, 'image': image.path}),
      );
      if (!ok) throw const FileSystemException('Taslak kaydedilemedi');
    } catch (_) {
      if (await image.exists()) await image.delete();
      rethrow;
    }
    if (old != null) {
      try {
        final oldPath =
            (jsonDecode(old) as Map<String, dynamic>)['image'] as String;
        if (oldPath != image.path) await File(oldPath).delete();
      } catch (_) {
        // The new draft has already been saved; an old file can be cleaned later.
      }
    }
  }

  static Future<void> delete() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return;
    final path = (jsonDecode(raw) as Map<String, dynamic>)['image'] as String;
    if (!await prefs.remove(_key)) {
      throw const FileSystemException('Taslak silinemedi');
    }
    try {
      await File(path).delete();
    } on FileSystemException {
      // The draft metadata has already been removed.
    }
  }
}
