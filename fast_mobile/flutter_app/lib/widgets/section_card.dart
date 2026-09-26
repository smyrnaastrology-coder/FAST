import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';

class SectionCard extends StatefulWidget {
  final String title;
  final Widget child;
  final IconData? icon;

  const SectionCard({super.key, required this.title, required this.child, this.icon});

  @override
  State<SectionCard> createState() => _SectionCardState();
}

class _SectionCardState extends State<SectionCard> {
  bool _open = false;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () => setState(() => _open = !_open),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              child: Row(
                children: [
                  if (widget.icon != null) ...[
                    Icon(widget.icon, color: FastTheme.accent, size: 20),
                    const SizedBox(width: 10),
                  ],
                  Expanded(
                    child: Text(widget.title, style:  TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: FastTheme.text)),
                  ),
                  Icon(_open ? Icons.expand_less : Icons.expand_more, color: FastTheme.textLight),
                ],
              ),
            ),
          ),
          if (_open)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: widget.child,
            ),
        ],
      ),
    );
  }
}

class HtmlRender extends StatelessWidget {
  final String html;
  const HtmlRender(this.html, {super.key});

  @override
  Widget build(BuildContext context) {
    // HTML işleme: <br> -> yeni satır, <b>..</b> -> başlık (altın), diğer etiketler temizlenir.
    final text = html
        .replaceAll(RegExp(r'<br\s*/?>', caseSensitive: false), '\n')
        .replaceAll('&nbsp;', ' ')
        .replaceAll('&amp;', '&')
        .replaceAll('&lt;', '<')
        .replaceAll('&gt;', '>')
        .trim();
    if (text.isEmpty) return const SizedBox.shrink();

    final spans = <InlineSpan>[];
    final parcalar = text.split(RegExp(r'(<b>.*?</b>)', caseSensitive: false, dotAll: true));
    for (final parca in parcalar) {
      if (parca.isEmpty) continue;
      if (parca.startsWith('<b>') && parca.endsWith('</b>')) {
        final baslik = parca.substring(3, parca.length - 4).trim();
        if (baslik.isEmpty) continue;
        spans.add(TextSpan(
          text: '$baslik ',
          style: TextStyle(
            fontSize: 14,
            height: 1.5,
            fontWeight: FontWeight.w700,
            color: FastTheme.accentGold,
          ),
        ));
      } else {
        final temiz = parca.replaceAll(RegExp(r'<[^>]*>'), '');
        if (temiz.isEmpty) continue;
        spans.add(TextSpan(
          text: temiz,
          style: TextStyle(fontSize: 14, height: 1.5, color: FastTheme.text),
        ));
      }
    }
    return Text.rich(TextSpan(children: spans));
  }
}

class ScoreCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const ScoreCard({super.key, required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color)),
              const SizedBox(height: 4),
              Text(label, style:  TextStyle(fontSize: 11, color: FastTheme.textLight), textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}

class ChartImage extends StatelessWidget {
  final String url;
  final String label;
  const ChartImage({super.key, required this.url, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Image.network(url, fit: BoxFit.contain, loadingBuilder: (_, child, progress) {
            if (progress == null) return child;
            return const SizedBox(height: 200, child: Center(child: CircularProgressIndicator()));
          }, errorBuilder: (context, __, ___) => SizedBox(height: 200, child: Center(child: Text(AppLocalizations.of(context).imageLoadError)))),
        ),
      ],
    );
  }
}
