import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/social_provider.dart';
import '../services/social_service.dart';

/// Topluluğa ilk girişte @kullanıcı adı alma ekranı (onboarding).
class HandleClaimScreen extends StatefulWidget {
  final VoidCallback? onClaimed;
  const HandleClaimScreen({super.key, this.onClaimed});

  @override
  State<HandleClaimScreen> createState() => _HandleClaimScreenState();
}

class _HandleClaimScreenState extends State<HandleClaimScreen> {
  final _username = TextEditingController();
  final _displayName = TextEditingController();
  final _bio = TextEditingController();
  final _city = TextEditingController();
  DateTime? _birthDate;
  TimeOfDay? _birthTime;
  bool _isAstrologer = false;
  String? _astroField;
  bool _busy = false;
  String? _error;

  static const _fields = ['Karma', 'Vedik', 'Uranyen', 'Klasik', 'Modern / Batı', 'Horary'];

  @override
  void dispose() {
    _username.dispose();
    _displayName.dispose();
    _bio.dispose();
    _city.dispose();
    super.dispose();
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

  Future<void> _claim() async {
    final l10n = AppLocalizations.of(context);
    final uname = _username.text.trim().toLowerCase();
    if (uname.length < 3) {
      setState(() => _error = l10n.handleTooShort);
      return;
    }
    if (!RegExp(r'^[a-z0-9_.]+$').hasMatch(uname)) {
      setState(() => _error = l10n.handleInvalid);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      double? lat;
      double? lon;
      String? city;
      String? country;
      final cityText = _city.text.trim();
      if (cityText.isNotEmpty) {
        final geo = await SocialService.geocodeCity(cityText);
        if (geo == null) {
          if (mounted) setState(() => _error = l10n.kunyeCityNotFound);
          return;
        }
        lat = (geo['lat'] as num?)?.toDouble();
        lon = (geo['lon'] as num?)?.toDouble();
        city = geo['city']?.toString() ?? cityText;
        country = geo['country']?.toString();
      }
      if (!mounted) return;
      await SocialService.claimHandle(
        username: uname,
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
      );
      if (!mounted) return;
      await context.read<SocialProvider>().refreshProfile();
      if (!mounted) return;
      widget.onClaimed?.call();
    } catch (e) {
      if (!mounted) return;
      final msg = e.toString();
      setState(() {
        if (msg.contains('username_taken')) {
          _error = l10n.handleTaken;
        } else if (msg.contains('username_invalid')) {
          _error = l10n.handleInvalid;
        } else if (msg.contains('username_too_short')) {
          _error = l10n.handleTooShort;
        } else {
          _error = l10n.loginErrorGeneric;
        }
      });
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
        title: Text(l10n.handleTitle, style: TextStyle(color: FastTheme.accentGold, fontSize: 18)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Text(l10n.handleSubtitle,
              style: TextStyle(fontSize: 14, color: FastTheme.textMuted, height: 1.5)),
          const SizedBox(height: 24),
          _label(l10n.handleLabel),
          TextField(
            controller: _username,
            style: TextStyle(color: FastTheme.text),
            inputFormatters: [
              FilteringTextInputFormatter.allow(RegExp(r'[a-z0-9_.]')),
              LowercaseFormatter(),
            ],
            decoration: InputDecoration(
              hintText: 'cosmicsoul',
              prefixText: '@',
              prefixStyle: TextStyle(color: FastTheme.accentGold),
            ),
          ),
          const SizedBox(height: 18),
          _label(l10n.handleDisplayName),
          TextField(
            controller: _displayName,
            style: TextStyle(color: FastTheme.text),
            decoration: InputDecoration(hintText: l10n.handleDisplayNameHint),
          ),
          const SizedBox(height: 18),
          _label(l10n.handleBio),
          TextField(
            controller: _bio,
            style: TextStyle(color: FastTheme.text),
            maxLines: 3,
            decoration: InputDecoration(hintText: l10n.handleBioHint),
          ),
          const SizedBox(height: 18),
          _label(l10n.handleBirthDate),
          InkWell(
            onTap: _pickDate,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
              decoration: BoxDecoration(
                color: FastTheme.bgSecondary,
                border: Border.all(color: FastTheme.border),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.cake_outlined, color: FastTheme.accentGold, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _birthDate == null
                          ? l10n.handleBirthDateHint
                          : '${_birthDate!.day}.${_birthDate!.month}.${_birthDate!.year}',
                      style: TextStyle(color: _birthDate == null ? FastTheme.textDim : FastTheme.text),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_birthDate != null) ...[
            const SizedBox(height: 8),
            Text(l10n.kunyeCalcNote,
                style: TextStyle(fontSize: 11, color: FastTheme.textDim, height: 1.4)),
            Text(l10n.handleBirthPrivateNote,
                style: TextStyle(fontSize: 11, color: FastTheme.textDim, height: 1.4)),
          ],
          const SizedBox(height: 18),
          _label(l10n.kunyeBirthTime),
          InkWell(
            onTap: _pickTime,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
              decoration: BoxDecoration(
                color: FastTheme.bgSecondary,
                border: Border.all(color: FastTheme.border),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.schedule_outlined, color: FastTheme.accentGold, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _timeText.isEmpty ? l10n.kunyeBirthTimeHint : _timeText,
                      style: TextStyle(color: _timeText.isEmpty ? FastTheme.textDim : FastTheme.text),
                    ),
                  ),
                  if (_timeText.isNotEmpty)
                    GestureDetector(
                      onTap: () => setState(() => _birthTime = null),
                      child: Icon(Icons.close, color: FastTheme.textDim, size: 18),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 6),
          Text(l10n.kunyeBirthTimeNote,
              style: TextStyle(fontSize: 11, color: FastTheme.textDim, height: 1.4)),
          const SizedBox(height: 18),
          _label(l10n.kunyeBirthCity),
          TextField(
            controller: _city,
            style: TextStyle(color: FastTheme.text),
            textCapitalization: TextCapitalization.words,
            decoration: InputDecoration(
              hintText: l10n.kunyeBirthCityHint,
              prefixIcon: Icon(Icons.location_on_outlined, color: FastTheme.accentGold, size: 20),
            ),
          ),
          const SizedBox(height: 20),
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
                  .map((f) => ChoiceChip(
                        label: Text(f),
                        selected: _astroField == f,
                        onSelected: (v) => setState(() => _astroField = v ? f : null),
                      ))
                  .toList(),
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: TextStyle(color: FastTheme.error, fontSize: 13)),
          ],
          const SizedBox(height: 28),
          GestureDetector(
            onTap: _busy ? null : _claim,
            child: Container(
              height: 50,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: [FastTheme.accentGold, FastTheme.accentGoldLight]),
                borderRadius: BorderRadius.circular(12),
              ),
              child: _busy
                  ? SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: FastTheme.bg, strokeWidth: 2))
                  : Text(l10n.handleContinue,
                      style: TextStyle(color: FastTheme.bg, fontWeight: FontWeight.w700, fontSize: 15)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _label(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(t, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: FastTheme.accentGold)),
      );
}

/// Anında küçük harfe çeviren input formatter.
class LowercaseFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(TextEditingValue oldValue, TextEditingValue newValue) =>
      newValue.copyWith(text: newValue.text.toLowerCase());
}
