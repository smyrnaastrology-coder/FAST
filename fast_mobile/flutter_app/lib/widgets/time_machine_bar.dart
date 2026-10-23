import 'package:flutter/material.dart';

import '../config/theme.dart';

class TimeMachineBar extends StatefulWidget {
  final DateTime initial;
  final void Function(DateTime) onChanged;

  const TimeMachineBar({super.key, required this.initial, required this.onChanged});

  @override
  State<TimeMachineBar> createState() => _TimeMachineBarState();
}

class _TimeMachineBarState extends State<TimeMachineBar> {
  late DateTime _dt;

  @override
  void initState() {
    super.initState();
    _dt = widget.initial;
  }

  String _fmt(DateTime d) {
    return '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')} ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
  }

  void _shift(Duration dur) {
    setState(() => _dt = _dt.add(dur));
    widget.onChanged(_dt);
  }

  Future<void> _pick() async {
    final d = await showDatePicker(
      context: context,
      initialDate: _dt,
      firstDate: DateTime(1900),
      lastDate: DateTime(2100),
    );
    if (d == null) return;
    if (!mounted) return;
    final t = await showTimePicker(context: context, initialTime: TimeOfDay(hour: _dt.hour, minute: _dt.minute));
    if (t == null) return;
    setState(() => _dt = DateTime(d.year, d.month, d.day, t.hour, t.minute));
    widget.onChanged(_dt);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: FastTheme.cardBg,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: FastTheme.border.withValues(alpha: 0.6)),
      ),
      child: Row(
        children: [
          IconButton(
            icon: Icon(Icons.fast_rewind, color: FastTheme.text),
            onPressed: () => _shift(const Duration(days: -1)),
          ),
          IconButton(
            icon: Icon(Icons.remove, color: FastTheme.text),
            onPressed: () => _shift(const Duration(hours: -1)),
          ),
          Expanded(
            child: GestureDetector(
              onTap: _pick,
              child: Text(
                _fmt(_dt),
                textAlign: TextAlign.center,
                style: TextStyle(color: FastTheme.text, fontWeight: FontWeight.w600),
              ),
            ),
          ),
          IconButton(
            icon: Icon(Icons.add, color: FastTheme.text),
            onPressed: () => _shift(const Duration(hours: 1)),
          ),
          IconButton(
            icon: Icon(Icons.fast_forward, color: FastTheme.text),
            onPressed: () => _shift(const Duration(days: 1)),
          ),
          IconButton(
            icon: Icon(Icons.refresh, color: FastTheme.accentGold),
            onPressed: () {
              setState(() => _dt = DateTime.now());
              widget.onChanged(_dt);
            },
          ),
        ],
      ),
    );
  }
}
