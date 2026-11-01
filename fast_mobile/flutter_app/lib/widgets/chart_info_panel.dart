import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../models/chart_data.dart';
import '../models/chart_labels.dart';
import 'chart_wheel_style.dart';

/// Haritanın sol üstünde gösterilen hesaplama bilgi paneli.
///
/// Tüm değerler [ChartData] içindeki gerçek hesaplama kaydından üretilir;
/// hiçbir bilgi sabit yazılmaz.
class ChartInfoPanel extends StatelessWidget {
  final ChartData data;
  final String title;
  final String subtitle;
  final ChartWheelStyle style;

  /// Taban yazı boyutu (harita boyutuyla ölçeklenir).
  final double fontSize;

  /// Sağ üstteki (dış harita) panel için sağa hizalama.
  final bool alignEnd;

  const ChartInfoPanel({
    super.key,
    required this.data,
    required this.style,
    this.title = '',
    this.subtitle = '',
    this.fontSize = 9,
    this.alignEnd = false,
  });

  String _coord(double value, String positive, String negative) {
    final dir = value >= 0 ? positive : negative;
    final abs = value.abs();
    final deg = abs.floor();
    final min = ((abs - deg) * 60).round();
    return '${deg.toString().padLeft(2, '0')}°$dir'
        '${min.toString().padLeft(2, '0')}′';
  }

  String _utc(double? tz) {
    if (tz == null) return '';
    final sign = tz >= 0 ? '+' : '-';
    final abs = tz.abs();
    final hours = abs.floor();
    final minutes = ((abs - hours) * 60).round();
    final mm = minutes == 0 ? '' : ':${minutes.toString().padLeft(2, '0')}';
    return 'UTC $sign$hours$mm';
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final material = MaterialLocalizations.of(context);
    final meta = data.meta;

    final parsed = DateTime.tryParse('${meta.date} ${meta.time}');
    final dateText = parsed != null
        ? material.formatFullDate(parsed)
        : meta.date;

    final timeParts = <String>[
      if (meta.time.isNotEmpty) meta.time,
      if (_utc(meta.tz).isNotEmpty) _utc(meta.tz),
    ];

    final lines = <_InfoLine>[
      if (title.isNotEmpty) _InfoLine(title, bold: true, scale: 1.30),
      if (subtitle.isNotEmpty) _InfoLine(subtitle, scale: 1.05),
      _InfoLine(dateText),
      if (timeParts.isNotEmpty) _InfoLine(timeParts.join('  ')),
      if (meta.place.isNotEmpty) _InfoLine(meta.place),
      _InfoLine(
        '${_coord(meta.lat, 'N', 'S')}  ${_coord(meta.lng, 'E', 'W')}',
      ),
      _InfoLine(l10n.chartInfoGeocentric),
      _InfoLine(l10n.chartInfoTropical),
      _InfoLine(chartHouseSystemLabel(l10n, data.houseSystem)),
      _InfoLine(l10n.chartInfoMeanNode),
    ];

    return DecoratedBox(
      decoration: BoxDecoration(
        color: style.background,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 1),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: alignEnd
              ? CrossAxisAlignment.end
              : CrossAxisAlignment.start,
          children: [
            for (final line in lines)
              Text(
                line.text,
                textAlign: alignEnd ? TextAlign.right : TextAlign.left,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: line.bold ? style.text : style.muted,
                  fontSize: fontSize * line.scale,
                  fontWeight: line.bold ? FontWeight.w700 : FontWeight.w400,
                  height: 1.25,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _InfoLine {
  final String text;
  final bool bold;
  final double scale;
  const _InfoLine(this.text, {this.bold = false, this.scale = 1.0});
}
