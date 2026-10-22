import 'package:flutter/material.dart';

import '../config/theme.dart';

/// Holavon amblemi — yeni marka: mavi içli, altın kaplamalı "h".
///
/// [HolavonLogo] resmi marka görselini (`assets/holavon_logo.png`) gösterir.
/// Görsel şeffaftır; koyu ve açık zeminlerde doğrudan kullanılabilir.
/// [onLight] beyaz zemin üstünde hazırlanmış varyantı (`holavon_logo_light.png`)
/// seçer ve yuvarlatılmış köşe maskesi uygular.
class HolavonLogo extends StatelessWidget {
  final double size;
  final double radius;
  final double? glow;
  final Color? glowColor;
  final bool onLight;

  const HolavonLogo({
    super.key,
    this.size = 40,
    this.radius = 12,
    this.glow,
    this.glowColor,
    this.onLight = false,
  });

  @override
  Widget build(BuildContext context) {
    final asset = onLight ? 'assets/holavon_logo_light.png' : 'assets/holavon_logo.png';
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(onLight ? radius : 0),
        boxShadow: glow == null
            ? null
            : [
                BoxShadow(
                  color: (glowColor ?? FastTheme.logoBlue).withValues(alpha: glow!),
                  blurRadius: size * 0.45,
                  spreadRadius: size * 0.06,
                ),
              ],
      ),
      clipBehavior: onLight ? Clip.antiAlias : Clip.none,
      child: Image.asset(
        asset,
        width: size,
        height: size,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => const SizedBox.shrink(),
      ),
    );
  }
}
