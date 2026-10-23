import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/chart_provider.dart';
import 'chart_detail_screen.dart';

class ChartCreateScreen extends StatefulWidget {
  const ChartCreateScreen({super.key});

  @override
  State<ChartCreateScreen> createState() => _ChartCreateScreenState();
}

class _ChartCreateScreenState extends State<ChartCreateScreen> {
  final _name = TextEditingController();
  final _date = TextEditingController();
  final _time = TextEditingController(text: '12:00');
  final _lat = TextEditingController(text: '41.0082');
  final _lon = TextEditingController(text: '28.9784');

  String _hs = 'P';

  Future<void> _pickDate() async {
    final d = await showDatePicker(
      context: context,
      initialDate: DateTime(1990, 1, 1),
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
    );
    if (d != null) {
      _date.text = '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    }
  }

  Future<void> _pickTime() async {
    final t = await showTimePicker(context: context, initialTime: const TimeOfDay(hour: 12, minute: 0));
    if (t != null) {
      _time.text = '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
    }
  }

  @override
  Widget build(BuildContext context) {
    final cp = context.watch<ChartProvider>();
    cp.setHouseSystem(_hs);

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text('Yeni Harita',
            style: TextStyle(
                color: FastTheme.accentGold,
                fontSize: 18,
                fontWeight: FontWeight.w700)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _name,
            style: TextStyle(color: FastTheme.text),
            decoration: InputDecoration(
              labelText: 'İsim (opsiyonel)',
              labelStyle: TextStyle(color: FastTheme.textMuted),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _date,
            readOnly: true,
            onTap: _pickDate,
            style: TextStyle(color: FastTheme.text),
            decoration: InputDecoration(
              labelText: 'Doğum Tarihi (YYYY-MM-DD)',
              labelStyle: TextStyle(color: FastTheme.textMuted),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _time,
            readOnly: true,
            onTap: _pickTime,
            style: TextStyle(color: FastTheme.text),
            decoration: InputDecoration(
              labelText: 'Doğum Saati (HH:MM)',
              labelStyle: TextStyle(color: FastTheme.textMuted),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _lat,
                  style: TextStyle(color: FastTheme.text),
                  decoration: InputDecoration(
                    labelText: 'Enlem',
                    labelStyle: TextStyle(color: FastTheme.textMuted),
                  ),
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _lon,
                  style: TextStyle(color: FastTheme.text),
                  decoration: InputDecoration(
                    labelText: 'Boylam',
                    labelStyle: TextStyle(color: FastTheme.textMuted),
                  ),
                  keyboardType: TextInputType.number,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text('Ev Sistemi', style: TextStyle(color: FastTheme.textMuted)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: ['P', 'W', 'R', 'K', 'E'].map((hs) {
              final sel = _hs == hs;
              return ChoiceChip(
                label: Text(hs),
                selected: sel,
                onSelected: (_) {
                  setState(() => _hs = hs);
                  cp.setHouseSystem(hs);
                },
                selectedColor: FastTheme.accentGold,
              );
            }).toList(),
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: cp.loading
                ? null
                : () async {
                    await cp.create(
                      name: _name.text.trim(),
                      date: _date.text.trim(),
                      time: _time.text.trim(),
                      lat: double.tryParse(_lat.text) ?? 41.0082,
                      lng: double.tryParse(_lon.text) ?? 28.9784,
                    );
                    if (context.mounted && cp.current != null) {
                      Navigator.of(context).pushReplacement(
                        MaterialPageRoute(builder: (_) => const ChartDetailScreen()),
                      );
                    }
                  },
            style: FilledButton.styleFrom(backgroundColor: FastTheme.accentGold),
            child: Text(cp.loading ? 'Hesaplanıyor...' : 'Haritayı Oluştur'),
          ),
          if (cp.error != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Text(cp.error!,
                  style: const TextStyle(color: Colors.redAccent)),
            ),
        ],
      ),
    );
  }
}
