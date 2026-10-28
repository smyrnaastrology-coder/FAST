import 'dart:typed_data';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
import '../services/social_service.dart';

/// Sosyal profil düzenleme: ad, bio, avatar, doğum tarihi (burç).
class EditSocialProfileScreen extends StatefulWidget {
  const EditSocialProfileScreen({super.key});

  @override
  State<EditSocialProfileScreen> createState() =>
      _EditSocialProfileScreenState();
}

class _EditSocialProfileScreenState extends State<EditSocialProfileScreen> {
  final _displayName = TextEditingController();
  final _bio = TextEditingController();
  final _city = TextEditingController();
  DateTime? _birthDate;
  TimeOfDay? _birthTime;
  double? _lat;
  double? _lon;
  String? _country;
  String? _cityQuery;
  bool _isAstrologer = false;
  String? _astroField;
  String? _avatarUrl;
  Uint8List? _avatarBytes;
  bool _busy = false;
  bool _loading = true;

  static const _fields = [
    'Karma',
    'Vedik',
    'Uranyen',
    'Klasik',
    'Modern / Batı',
    'Horary',
    'İslami Astroloji',
    'Kabala',
    'Numeroloji',
    'Tarot',
    'Ruhsal Danışmanlık',
    'Diğer',
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final prof = await SocialService.myProfile();
    final info = await SocialService.myBirthInfo();
    if (!mounted) return;
    setState(() {
      _displayName.text = prof?.displayName ?? '';
      _bio.text = prof?.bio ?? '';
      _avatarUrl = prof?.avatarUrl;
      _isAstrologer = prof?.isAstrologer ?? false;
      _astroField = prof?.astroField;
      final bd = info?.date;
      if (bd != null && bd.isNotEmpty) _birthDate = DateTime.tryParse(bd);
      final bt = info?.time;
      if (bt != null && bt.contains(':')) {
        final parts = bt.split(':');
        final h = int.tryParse(parts[0]);
        final m = int.tryParse(parts.length > 1 ? parts[1] : '0');
        if (h != null && m != null) _birthTime = TimeOfDay(hour: h, minute: m);
      }
      _city.text = info?.city ?? '';
      _cityQuery = info?.city;
      _lat = info?.lat;
      _lon = info?.lon;
      _country = info?.country;
      _loading = false;
    });
  }

  @override
  void dispose() {
    _displayName.dispose();
    _bio.dispose();
    _city.dispose();
    super.dispose();
  }

  Future<void> _pickAvatar() async {
    final file = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      maxWidth: 400,
      imageQuality: 80,
    );
    if (file == null) return;
    final bytes = await file.readAsBytes();
    if (!mounted) return;
    setState(() => _avatarBytes = bytes);
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final d = await showDatePicker(
      context: context,
      initialDate: _birthDate ?? DateTime(now.year - 25, now.month, now.day),
      firstDate: DateTime(1920),
      lastDate: now,
    );
    if (d != null) setState(() => _birthDate = d);
  }

  Future<void> _pickTime() async {
    final t = await showTimePicker(
      context: context,
      initialTime: _birthTime ?? const TimeOfDay(hour: 12, minute: 0),
      helpText: AppLocalizations.of(context).kunyeBirthTime,
    );
    if (t != null) setState(() => _birthTime = t);
  }

  String get _timeText => _birthTime == null
      ? ''
      : '${_birthTime!.hour.toString().padLeft(2, '0')}:${_birthTime!.minute.toString().padLeft(2, '0')}';

  Future<void> _save() async {
    final l10n = AppLocalizations.of(context);
    setState(() => _busy = true);
    try {
      String? avatar = _avatarUrl;
      if (_avatarBytes != null) {
        avatar = await SocialService.uploadAvatar(
          XFile.fromData(_avatarBytes!, name: 'avatar.jpg'),
        );
      }
      final cityText = _city.text.trim();
      double? lat;
      double? lon;
      String? city;
      String? country;
      if (cityText.isNotEmpty) {
        if (cityText != _cityQuery) {
          final geo = await SocialService.geocodeCity(cityText);
          if (geo == null) {
            if (mounted) {
              ScaffoldMessenger.of(
                context,
              ).showSnackBar(SnackBar(content: Text(l10n.kunyeCityNotFound)));
            }
            return;
          }
          lat = (geo['lat'] as num?)?.toDouble();
          lon = (geo['lon'] as num?)?.toDouble();
          city = geo['city']?.toString() ?? cityText;
          country = geo['country']?.toString();
        } else {
          lat = _lat;
          lon = _lon;
          city = _cityQuery;
          country = _country;
        }
      }
      await SocialService.updateMyProfile(
        displayName: _displayName.text.trim(),
        bio: _bio.text.trim(),
        birthDate: _birthDate?.toIso8601String().split('T').first,
        birthTime: _timeText.isEmpty ? null : _timeText,
        birthCity: city,
        birthCountry: country,
        lat: lat,
        lon: lon,
        isAstrologer: _isAstrologer,
        astroField: _astroField,
        avatarUrl: avatar,
      );
      if (!mounted) return;
      await context.read<SocialProvider>().refreshProfile();
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (_) {
      if (mounted)
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(l10n.createPostError)));
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
        title: Text(
          l10n.profileEdit,
          style: TextStyle(color: FastTheme.accentGold, fontSize: 18),
        ),
        actions: [
          TextButton(
            onPressed: _busy ? null : _save,
            child: _busy
                ? SizedBox(
                    height: 18,
                    width: 18,
                    child: CircularProgressIndicator(
                      color: FastTheme.accentGold,
                      strokeWidth: 2,
                    ),
                  )
                : Text(
                    l10n.profileSave,
                    style: TextStyle(
                      color: FastTheme.accentGold,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
          ),
        ],
      ),
      body: _loading
          ? Center(
              child: CircularProgressIndicator(color: FastTheme.accentGold),
            )
          : ListView(
              padding: EdgeInsets.fromLTRB(
                20,
                20,
                20,
                40 + MediaQuery.of(context).viewPadding.bottom,
              ),
              children: [
                Center(
                  child: GestureDetector(
                    onTap: _pickAvatar,
                    child: Stack(
                      children: [
                        CircleAvatar(
                          radius: 44,
                          backgroundColor: FastTheme.accentGold.withValues(
                            alpha: 0.15,
                          ),
                          backgroundImage: _avatarBytes != null
                              ? MemoryImage(_avatarBytes!)
                              : (_avatarUrl != null && _avatarUrl!.isNotEmpty
                                    ? CachedNetworkImageProvider(_avatarUrl!)
                                          as ImageProvider
                                    : null),
                          child:
                              (_avatarBytes == null &&
                                  (_avatarUrl == null || _avatarUrl!.isEmpty))
                              ? Icon(
                                  Icons.person,
                                  size: 40,
                                  color: FastTheme.accentGold,
                                )
                              : null,
                        ),
                        Positioned(
                          right: 0,
                          bottom: 0,
                          child: Container(
                            padding: const EdgeInsets.all(6),
                            decoration: BoxDecoration(
                              color: FastTheme.accentGold,
                              shape: BoxShape.circle,
                            ),
                            child: Icon(
                              Icons.camera_alt,
                              size: 16,
                              color: FastTheme.bg,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                _label(l10n.handleDisplayName),
                TextField(
                  controller: _displayName,
                  style: TextStyle(color: FastTheme.text),
                  decoration: InputDecoration(
                    hintText: l10n.handleDisplayNameHint,
                  ),
                ),
                const SizedBox(height: 18),
                _label(l10n.handleBio),
                TextField(
                  controller: _bio,
                  style: TextStyle(color: FastTheme.text),
                  maxLines: 3,
                  maxLength: 200,
                  decoration: InputDecoration(hintText: l10n.handleBioHint),
                ),
                const SizedBox(height: 18),
                _label(l10n.kunyeRoleLabel),
                Wrap(
                  spacing: 8,
                  children: [
                    ChoiceChip(
                      label: Text(l10n.kunyeRoleAstrolog),
                      selected: _isAstrologer,
                      onSelected: (_) => setState(() => _isAstrologer = true),
                    ),
                    ChoiceChip(
                      label: Text(l10n.kunyeRoleLover),
                      selected: !_isAstrologer,
                      onSelected: (_) => setState(() {
                        _isAstrologer = false;
                        _astroField = null;
                      }),
                    ),
                  ],
                ),
                if (_isAstrologer) ...[
                  const SizedBox(height: 14),
                  _label(l10n.kunyeFieldLabel),
                  Wrap(
                    spacing: 8,
                    runSpacing: 4,
                    children: _fields
                        .map(
                          (f) => ChoiceChip(
                            label: Text(f),
                            selected: _astroField == f,
                            onSelected: (v) =>
                                setState(() => _astroField = v ? f : (_astroField == f ? null : _astroField)),
                          ),
                        )
                        .toList(),
                  ),
                ],
                const SizedBox(height: 18),
                _label(l10n.handleBirthDate),
                InkWell(
                  onTap: _pickDate,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 14,
                    ),
                    decoration: BoxDecoration(
                      color: FastTheme.bgSecondary,
                      border: Border.all(color: FastTheme.border),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.cake_outlined,
                          color: FastTheme.accentGold,
                          size: 20,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _birthDate == null
                                ? l10n.handleBirthDateHint
                                : '${_birthDate!.day}.${_birthDate!.month}.${_birthDate!.year}',
                            style: TextStyle(
                              color: _birthDate == null
                                  ? FastTheme.textDim
                                  : FastTheme.text,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  l10n.handleBirthPrivateNote,
                  style: TextStyle(
                    fontSize: 11,
                    color: FastTheme.textDim,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 18),
                _label(l10n.kunyeBirthTime),
                InkWell(
                  onTap: _pickTime,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 14,
                    ),
                    decoration: BoxDecoration(
                      color: FastTheme.bgSecondary,
                      border: Border.all(color: FastTheme.border),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.schedule_outlined,
                          color: FastTheme.accentGold,
                          size: 20,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _timeText.isEmpty
                                ? l10n.kunyeBirthTimeHint
                                : _timeText,
                            style: TextStyle(
                              color: _timeText.isEmpty
                                  ? FastTheme.textDim
                                  : FastTheme.text,
                            ),
                          ),
                        ),
                        if (_timeText.isNotEmpty)
                          GestureDetector(
                            onTap: () => setState(() => _birthTime = null),
                            child: Icon(
                              Icons.close,
                              color: FastTheme.textDim,
                              size: 18,
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  l10n.kunyeBirthTimeNote,
                  style: TextStyle(
                    fontSize: 11,
                    color: FastTheme.textDim,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 18),
                _label(l10n.kunyeBirthCity),
                TextField(
                  controller: _city,
                  style: TextStyle(color: FastTheme.text),
                  textCapitalization: TextCapitalization.words,
                  decoration: InputDecoration(
                    hintText: l10n.kunyeBirthCityHint,
                    prefixIcon: Icon(
                      Icons.location_on_outlined,
                      color: FastTheme.accentGold,
                      size: 20,
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _label(String t) => Padding(
    padding: const EdgeInsets.only(bottom: 6),
    child: Text(
      t,
      style: TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        color: FastTheme.accentGold,
      ),
    ),
  );
}
