import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/chart_labels.dart';
import '../providers/chart_provider.dart';
import 'chart_create_screen.dart';
import 'chart_detail_screen.dart';
import '../widgets/chart_mark.dart';

class ChartListScreen extends StatefulWidget {
  const ChartListScreen({super.key});

  @override
  State<ChartListScreen> createState() => _ChartListScreenState();
}

class _ChartListScreenState extends State<ChartListScreen> {
  bool _autoOpened = false;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final cp = context.read<ChartProvider>();
      await cp.loadSaved();
      if (!mounted) return;
      // Kayıtlı harita varsa listeyi atlayıp doğrudan ilk haritayı aç.
      if (!_autoOpened && cp.saved.isNotEmpty) {
        _autoOpened = true;
        cp.open(cp.saved.first);
        if (mounted) {
          Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const ChartDetailScreen()),
          );
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final cp = context.watch<ChartProvider>();
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      backgroundColor: FastTheme.bg,
      appBar: AppBar(
        backgroundColor: FastTheme.bg,
        title: Text(
          l10n.chartListTitle,
          style: TextStyle(
            color: FastTheme.accentGold,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.add, color: FastTheme.accentGold),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ChartCreateScreen()),
            ),
          ),
        ],
      ),
      body: cp.saved.isEmpty
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.auto_graph,
                      color: FastTheme.accentGold.withValues(alpha: 0.6),
                      size: 42),
                  const SizedBox(height: 10),
                  Text(
                    l10n.chartListEmpty,
                    style: TextStyle(
                        color: FastTheme.textMuted.withValues(alpha: 0.7)),
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(
                          builder: (_) => const ChartCreateScreen()),
                    ),
                    style: FilledButton.styleFrom(
                        backgroundColor: FastTheme.accentGold),
                    child: Text(l10n.chartListCreateFirst),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 24),
              itemCount: cp.saved.length,
              itemBuilder: (context, i) {
                final c = cp.saved[i];
                final name = c.meta.name?.isNotEmpty == true
                    ? c.meta.name!
                    : l10n.chartDefaultName;
                return Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  decoration: BoxDecoration(
                    color: FastTheme.cardBg,
                    borderRadius: BorderRadius.circular(12),
                    border:
                        Border.all(color: FastTheme.border.withValues(alpha: 0.5)),
                  ),
                  child: ListTile(
                    trailing: IconButton(tooltip: l10n.chartDelete, icon: const Icon(Icons.delete_outline),
                      onPressed: () => cp.delete(c)),
                    leading: const ChartMark(size: 40),
                    title: Text(name,
                        style: TextStyle(
                            color: FastTheme.text, fontWeight: FontWeight.w600)),
                    subtitle: Text(
                        '${c.meta.date} ${c.meta.time} • '
                        '${chartHouseSystemLabel(l10n, c.houseSystem)}'
                        '${c.meta.place.isNotEmpty ? ' • ${c.meta.place}' : ''}',
                        style: TextStyle(
                            color: FastTheme.textMuted.withValues(alpha: 0.7))),
                    onTap: () {
                      cp.open(c);
                      Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const ChartDetailScreen()),
                      );
                    },
                  ),
                );
              },
            ),
    );
  }
}
