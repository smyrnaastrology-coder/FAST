import 'package:flutter/material.dart';

import '../config/theme.dart';

/// Ülke / şehir yazarken önerileri **alanın hemen altında** gösteren,
/// tek dokunuşla seçim yapan alan.
///
/// Flutter'ın `Autocomplete` kaplaması ilk dokunuşta odağı kaybettiği için
/// seçim ancak ikinci dokunuşta gerçekleşiyordu. Bu alan önerileri aynı
/// widget ağacında, satır içinde gösterdiği için tek dokunuş yeterlidir.
/// Sağdaki onay (✓) düğmesi yazılan metni "hazneye" yerleştirir.
class PlaceSuggestField extends StatefulWidget {
  const PlaceSuggestField({
    super.key,
    required this.label,
    required this.options,
    required this.displayOf,
    required this.onSelected,
    this.initialValue = '',
    this.hint,
    this.enabled = true,
    this.searchOf,
    this.onTextChanged,
  });

  final String label;
  final List<String> options;
  final String Function(String) displayOf;

  /// Kullanıcı bir öneriye dokunduğunda ya da ✓ ile onayladığında çağrılır.
  final ValueChanged<String> onSelected;

  /// Alan açılışında yazılı olacak metin.
  final String initialValue;
  final String? hint;
  final bool enabled;

  /// Arama için kullanılacak metin (varsayılan: [displayOf]).
  final String Function(String)? searchOf;

  /// Kullanıcı yazarken çağrılır (tam eşleşmeyi yakalamak için).
  final ValueChanged<String>? onTextChanged;

  @override
  State<PlaceSuggestField> createState() => _PlaceSuggestFieldState();
}

/// Türkçe karakterleri sadeleştirip büyük/küçük harf duyarsız arama yapar.
String _fold(String input) {
  const map = {
    'ç': 'c',
    'ğ': 'g',
    'ı': 'i',
    'İ': 'i',
    'ö': 'o',
    'ş': 's',
    'ü': 'u',
    'â': 'a',
    'î': 'i',
    'û': 'u',
  };
  final lower = input.toLowerCase();
  final b = StringBuffer();
  for (final ch in lower.split('')) {
    b.write(map[ch] ?? ch);
  }
  return b.toString();
}

class _PlaceSuggestFieldState extends State<PlaceSuggestField> {
  late final TextEditingController _ctrl;
  late final FocusNode _focus;
  bool _open = false;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.initialValue);
    _focus = FocusNode();
    _focus.addListener(_onFocusChanged);
  }

  @override
  void didUpdateWidget(covariant PlaceSuggestField old) {
    super.didUpdateWidget(old);
    // Dışarıdan gelen değer değiştiyse (ör. ülke değişince şehir sıfırlandı)
    // alanı güncelle; kullanıcı yazarken metne dokunma.
    if (widget.initialValue != old.initialValue && !_focus.hasFocus) {
      _ctrl.text = widget.initialValue;
    }
  }

  @override
  void dispose() {
    _focus.removeListener(_onFocusChanged);
    _focus.dispose();
    _ctrl.dispose();
    super.dispose();
  }

  void _onFocusChanged() {
    if (!_focus.hasFocus && _open) {
      setState(() => _open = false);
    }
  }

  String _search(String option) =>
      (widget.searchOf ?? widget.displayOf)(option);

  List<String> get _matches {
    final q = _fold(_ctrl.text.trim());
    final enabled = widget.enabled ? widget.options : const <String>[];
    if (q.isEmpty) return enabled.take(40).toList();
    final out = <String>[];
    for (final o in enabled) {
      final s = _fold(_search(o));
      final label = _fold(widget.displayOf(o));
      if (s.contains(q) || label.contains(q)) {
        out.add(o);
        if (out.length >= 60) break;
      }
    }
    return out;
  }

  void _select(String option, {bool unfocus = true}) {
    _ctrl.text = widget.displayOf(option);
    _ctrl.selection = TextSelection.collapsed(offset: _ctrl.text.length);
    setState(() => _open = false);
    if (unfocus) _focus.unfocus();
    widget.onSelected(option);
  }

  /// Yazılan metni (tam eşleşme yoksa ilk öneriyi) seçer.
  void _commitTyped() {
    final typed = _fold(_ctrl.text.trim());
    if (typed.isEmpty) return;
    final matches = _matches;
    if (matches.isEmpty) return;
    String? exact;
    for (final o in matches) {
      if (_fold(_search(o)) == typed || _fold(widget.displayOf(o)) == typed) {
        exact = o;
        break;
      }
    }
    _select(exact ?? matches.first);
  }

  @override
  Widget build(BuildContext context) {
    final matches = _open ? _matches : const <String>[];
    final current = _fold(_ctrl.text.trim());
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _ctrl,
          focusNode: _focus,
          enabled: widget.enabled,
          style: TextStyle(color: FastTheme.text),
          decoration: InputDecoration(
            labelText: widget.label,
            hintText: widget.hint,
            suffixIcon: _open && matches.isNotEmpty
                ? IconButton(
                    tooltip: 'Tamam',
                    icon: Icon(Icons.check, color: FastTheme.accentGold),
                    onPressed: _commitTyped,
                  )
                : null,
          ),
          onTap: () => setState(() => _open = true),
          onChanged: (v) {
            setState(() => _open = true);
            widget.onTextChanged?.call(v);
          },
          onSubmitted: (_) => _commitTyped(),
        ),
        if (matches.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(top: 4),
            constraints: const BoxConstraints(maxHeight: 200),
            decoration: BoxDecoration(
              color: FastTheme.cardBg,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: FastTheme.border.withValues(alpha: 0.7),
              ),
            ),
            child: Material(
              color: Colors.transparent,
              child: ListView.separated(
                shrinkWrap: true,
                padding: const EdgeInsets.symmetric(vertical: 2),
                itemCount: matches.length,
                separatorBuilder: (_, _) => Divider(
                  height: 1,
                  thickness: 0.5,
                  color: FastTheme.border.withValues(alpha: 0.4),
                ),
                itemBuilder: (_, i) {
                  final option = matches[i];
                  final label = widget.displayOf(option);
                  final active = _fold(label) == current;
                  return InkWell(
                    onTap: () => _select(option),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 11,
                      ),
                      child: Row(
                        children: [
                          Icon(
                            active
                                ? Icons.radio_button_checked
                                : Icons.radio_button_unchecked,
                            size: 16,
                            color: active
                                ? FastTheme.accentGold
                                : FastTheme.textMuted,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              label,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                color: active
                                    ? FastTheme.accentGold
                                    : FastTheme.text,
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
      ],
    );
  }
}
