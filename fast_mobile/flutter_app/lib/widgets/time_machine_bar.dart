import 'dart:async';

import 'package:flutter/material.dart';

import '../config/theme.dart';

/// Zaman makinesi: hızlı adım butonları, oynat/durdur ve gün kaydırıcısı.
class TimeMachineBar extends StatefulWidget {
  final DateTime initial;
  final void Function(DateTime) onChanged;

  const TimeMachineBar({
    super.key,
    required this.initial,
    required this.onChanged,
  });

  @override
  State<TimeMachineBar> createState() => _TimeMachineBarState();
}

class _TimeMachineBarState extends State<TimeMachineBar> {
  late DateTime _dt;
  late final DateTime _anchor;
  int _stepDays = 1;
  bool _playing = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _dt = widget.initial;
    _anchor = widget.initial;
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String _fmt(DateTime d) {
    return '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')} '
        '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
  }

  void _emit(DateTime dt) {
    setState(() => _dt = dt);
    widget.onChanged(_dt);
  }

  void _shiftDays(int days) => _emit(_dt.add(Duration(days: days)));

  void _togglePlay() {
    if (_playing) {
      _timer?.cancel();
      setState(() => _playing = false);
      return;
    }
    setState(() => _playing = true);
    _timer = Timer.periodic(const Duration(milliseconds: 700), (_) {
      _emit(_dt.add(Duration(days: _stepDays)));
    });
  }

  Future<void> _pick() async {
    final d = await showDatePicker(
      context: context,
      initialDate: _dt,
      firstDate: DateTime(1900),
      lastDate: DateTime(2100),
    );
    if (d == null || !mounted) return;
    final t = await showTimePicker(
        context: context, initialTime: TimeOfDay(hour: _dt.hour, minute: _dt.minute));
    if (t == null || !mounted) return;
    _emit(DateTime(d.year, d.month, d.day, t.hour, t.minute));
  }

  @override
  Widget build(BuildContext context) {
    final offsetDays = _dt.difference(_anchor).inDays;
    final sliderVal = offsetDays.clamp(-730, 730).toDouble();

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12),
      padding: const EdgeInsets.fromLTRB(10, 8, 10, 4),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: FastTheme.border.withValues(alpha: 0.6)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(Icons.access_time, size: 16, color: FastTheme.accentGold),
              const SizedBox(width: 6),
              Expanded(
                child: GestureDetector(
                  onTap: _pick,
                  child: Text(
                    _fmt(_dt),
                    style: TextStyle(
                        color: FastTheme.text,
                        fontWeight: FontWeight.w700,
                        fontSize: 13),
                  ),
                ),
              ),
              TextButton(
                onPressed: () => _emit(DateTime.now()),
                style: TextButton.styleFrom(
                  minimumSize: const Size(0, 32),
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                ),
                child: Text('Şimdi',
                    style:
                        TextStyle(color: FastTheme.accentGold, fontSize: 12)),
              ),
            ],
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton(
                tooltip: 'Geri al',
                icon: Icon(Icons.keyboard_double_arrow_left,
                    color: FastTheme.textMuted),
                onPressed: () => _shiftDays(-_stepDays * 10),
              ),
              IconButton(
                tooltip: 'Geri',
                icon: Icon(Icons.chevron_left, color: FastTheme.text, size: 28),
                onPressed: () => _shiftDays(-_stepDays),
              ),
              Container(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(colors: [
                    FastTheme.accentGold,
                    FastTheme.accentGoldLight,
                  ]),
                ),
                child: IconButton(
                  tooltip: _playing ? 'Durdur' : 'Oynat',
                  icon: Icon(_playing ? Icons.pause : Icons.play_arrow,
                      color: FastTheme.bg),
                  onPressed: _togglePlay,
                ),
              ),
              IconButton(
                tooltip: 'İleri',
                icon: Icon(Icons.chevron_right, color: FastTheme.text, size: 28),
                onPressed: () => _shiftDays(_stepDays),
              ),
              IconButton(
                tooltip: 'İleri al',
                icon: Icon(Icons.keyboard_double_arrow_right,
                    color: FastTheme.textMuted),
                onPressed: () => _shiftDays(_stepDays * 10),
              ),
            ],
          ),
          Row(
            children: [
              _stepChip('1 Gün', 1),
              const SizedBox(width: 6),
              _stepChip('1 Ay', 30),
              const SizedBox(width: 6),
              _stepChip('1 Yıl', 365),
              const Spacer(),
              Text(
                offsetDays == 0
                    ? 'bugün'
                    : '${offsetDays > 0 ? '+' : ''}$offsetDays gün',
                style: TextStyle(color: FastTheme.textMuted, fontSize: 11),
              ),
            ],
          ),
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              trackHeight: 2,
              thumbShape:
                  const RoundSliderThumbShape(enabledThumbRadius: 7),
              overlayShape:
                  const RoundSliderOverlayShape(overlayRadius: 16),
            ),
            child: Slider(
              value: sliderVal,
              min: -730,
              max: 730,
              activeColor: FastTheme.accentGold,
              inactiveColor: FastTheme.border,
              onChanged: (v) {
                _timer?.cancel();
                setState(() => _playing = false);
                _emit(_anchor.add(Duration(days: v.round())));
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _stepChip(String label, int days) {
    final sel = _stepDays == days;
    return GestureDetector(
      onTap: () => setState(() => _stepDays = days),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: sel
              ? FastTheme.accentGold.withValues(alpha: 0.18)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: sel
                ? FastTheme.accentGold.withValues(alpha: 0.7)
                : FastTheme.border.withValues(alpha: 0.5),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: sel ? FastTheme.accentGold : FastTheme.textMuted,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}
