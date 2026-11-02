import 'package:flutter/material.dart';

import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/moon_mansion_content.dart';
import '../models/sky_moon_guide.dart';

String _phaseTitle(AppLocalizations l, String phase) => switch (phase) {
  'waxing_crescent' => l.skyMoonPhaseCrescentTitle,
  'first_quarter' => l.skyMoonPhaseFirstQuarterTitle,
  'waxing_gibbous' => l.skyMoonPhaseGibbousTitle,
  'full' => l.skyMoonPhaseFullTitle,
  'waning_gibbous' => l.skyMoonPhaseWaningGibbousTitle,
  'last_quarter' => l.skyMoonPhaseLastQuarterTitle,
  'waning_crescent' => l.skyMoonPhaseWaningCrescentTitle,
  _ => l.skyMoonPhaseNewTitle,
};

String _phasePrompt(AppLocalizations l, String phase) => switch (phase) {
  'waxing_crescent' => l.skyMoonPhaseCrescentPrompt,
  'first_quarter' => l.skyMoonPhaseFirstQuarterPrompt,
  'waxing_gibbous' => l.skyMoonPhaseGibbousPrompt,
  'full' => l.skyMoonPhaseFullPrompt,
  'waning_gibbous' => l.skyMoonPhaseWaningGibbousPrompt,
  'last_quarter' => l.skyMoonPhaseLastQuarterPrompt,
  'waning_crescent' => l.skyMoonPhaseWaningCrescentPrompt,
  _ => l.skyMoonPhaseNewPrompt,
};

String _mansionDate(BuildContext context, DateTime time) {
  final local = time.toLocal();
  final date = MaterialLocalizations.of(context).formatMediumDate(local);
  final clock = MaterialLocalizations.of(
    context,
  ).formatTimeOfDay(TimeOfDay.fromDateTime(local), alwaysUse24HourFormat: true);
  return '$date · $clock';
}

class MoonGuideCard extends StatelessWidget {
  final SkyMoonGuide guide;

  const MoonGuideCard({super.key, required this.guide});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final locale = Localizations.localeOf(context).languageCode;
    final mansionNumber = guide.mansion.number.clamp(1, 28);
    final mansionName = MoonMansionContent.names[mansionNumber - 1];
    final percent = guide.mansion.progress.clamp(0, 100);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            FastTheme.accentGold.withValues(alpha: 0.12),
            FastTheme.cardBg,
          ],
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _heading(l.skyMoonPhaseLabel, Icons.brightness_6_outlined),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: Text(
                  _phaseTitle(l, guide.phase.phase),
                  style: TextStyle(
                    color: FastTheme.text,
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Text(
                '${guide.phase.illumination.toStringAsFixed(0)}%',
                style: TextStyle(
                  color: FastTheme.accentGoldLight,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 5),
          Text(
            _phasePrompt(l, guide.phase.phase),
            style: TextStyle(
              color: FastTheme.textMuted,
              fontSize: 12,
              height: 1.4,
            ),
          ),
          if (guide.phase.endsAt != null) ...[
            const SizedBox(height: 5),
            Text(
              '${l.skyMoonPhaseEndsAt}: ${_mansionDate(context, guide.phase.endsAt!)}',
              style: TextStyle(
                color: FastTheme.textMuted.withValues(alpha: 0.8),
                fontSize: 11,
              ),
            ),
          ],
          const SizedBox(height: 18),
          _heading(l.skyMoonMansionLabel, Icons.auto_awesome_outlined),
          const SizedBox(height: 8),
          Text(
            '${l.skyMoonMansionNumber(mansionNumber.toString())} · $mansionName',
            style: TextStyle(
              color: FastTheme.text,
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 5),
          ClipRRect(
            borderRadius: BorderRadius.circular(5),
            child: LinearProgressIndicator(
              value: percent / 100,
              minHeight: 6,
              backgroundColor: FastTheme.border,
              valueColor: AlwaysStoppedAnimation(FastTheme.accentGold),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            l.skyMoonMansionProgress(percent.toStringAsFixed(0)),
            style: TextStyle(
              color: FastTheme.textMuted.withValues(alpha: 0.8),
              fontSize: 10.5,
            ),
          ),
          if (guide.mansion.leavesAt != null) ...[
            const SizedBox(height: 5),
            Text(
              '${l.skyMoonMansionLeavesAt}: ${_mansionDate(context, guide.mansion.leavesAt!)}',
              style: TextStyle(
                color: FastTheme.textMuted.withValues(alpha: 0.8),
                fontSize: 11,
              ),
            ),
          ],
          const SizedBox(height: 8),
          Text(
            MoonMansionContent.prompt(mansionNumber, locale),
            style: TextStyle(
              color: FastTheme.textMuted,
              fontSize: 12,
              height: 1.4,
            ),
          ),
          if (guide.transitions.isNotEmpty) ...[
            const SizedBox(height: 14),
            Text(
              l.skyMoonMansionNext,
              style: TextStyle(
                color: FastTheme.accentGoldLight,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 5),
            for (final transition in guide.transitions.take(5))
              Padding(
                padding: const EdgeInsets.only(top: 3),
                child: Text(
                  '${_mansionDate(context, transition.time)} · '
                  '${MoonMansionContent.names[transition.number.clamp(1, 28) - 1]}',
                  style: TextStyle(
                    color: FastTheme.textMuted.withValues(alpha: 0.85),
                    fontSize: 11,
                  ),
                ),
              ),
          ],
          const SizedBox(height: 12),
          Text(
            l.skyMoonMansionMethodNote,
            style: TextStyle(
              color: FastTheme.textMuted.withValues(alpha: 0.7),
              fontSize: 10.5,
              height: 1.35,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            l.skyMoonGuideNote,
            style: TextStyle(
              color: FastTheme.textMuted.withValues(alpha: 0.7),
              fontSize: 10.5,
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }

  Widget _heading(String title, IconData icon) => Row(
    children: [
      Icon(icon, size: 17, color: FastTheme.accentGoldLight),
      const SizedBox(width: 7),
      Text(
        title,
        style: TextStyle(
          color: FastTheme.accentGoldLight,
          fontSize: 12,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.3,
        ),
      ),
    ],
  );
}
