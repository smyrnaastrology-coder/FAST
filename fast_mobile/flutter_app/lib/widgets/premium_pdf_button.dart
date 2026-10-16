import 'package:flutter/material.dart';
import '../config/theme.dart';

/// Premium PDF indirme butonu: altın degrade + ışıma + kitap ikonu.
/// İki ekranda da (sonuç + analiz) aynı görünüm için ortak widget.
class PremiumPdfButton extends StatelessWidget {
  final VoidCallback? onPressed;
  final bool loading;
  final String label;

  const PremiumPdfButton({
    super.key,
    required this.onPressed,
    required this.label,
    this.loading = false,
  });

  @override
  Widget build(BuildContext context) {
    final inactive = onPressed == null && !loading;
    return Opacity(
      opacity: inactive ? 0.55 : 1.0,
      child: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [FastTheme.accentGoldLight, FastTheme.accentGold],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: FastTheme.accentGoldGlow,
              blurRadius: 18,
              offset: const Offset(0, 6),
            ),
          ],
          border: Border.all(color: Colors.white.withValues(alpha: 0.25)),
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: loading ? null : onPressed,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (loading)
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: FastTheme.bg,
                      ),
                    )
                  else
                    Icon(Icons.menu_book, size: 22, color: FastTheme.bg),
                  const SizedBox(width: 10),
                  Flexible(
                    child: Text(
                      label,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.3,
                        color: FastTheme.bg,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
