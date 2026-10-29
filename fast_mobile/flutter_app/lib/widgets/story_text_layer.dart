import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/story_element.dart';

/// Hikâye metin katmanları. Google Fonts ile gerçek font çeşitleri sunar.
const List<MapEntry<String, String>> kStoryFonts = [
  MapEntry('Poppins', 'Poppins'),
  MapEntry('Playfair Display', 'Playfair'),
  MapEntry('Caveat', 'El yazısı'),
  MapEntry('Bebas Neue', 'Bebas'),
  MapEntry('Montserrat', 'Montserrat'),
];

TextStyle storyFontStyle(
  String family, {
  required Color color,
  required double fontSize,
  FontWeight weight = FontWeight.w700,
}) {
  TextStyle base;
  switch (family) {
    case 'Playfair Display':
      base = GoogleFonts.playfairDisplay();
      break;
    case 'Caveat':
      base = GoogleFonts.caveat();
      break;
    case 'Bebas Neue':
      base = GoogleFonts.bebasNeue();
      break;
    case 'Montserrat':
      base = GoogleFonts.montserrat();
      break;
    default:
      base = GoogleFonts.poppins();
  }
  return base.copyWith(
    color: color,
    fontSize: fontSize,
    fontWeight: weight,
    height: 1.2,
    shadows: const [
      Shadow(blurRadius: 6, color: Colors.black54, offset: Offset(1, 2)),
    ],
  );
}

class StoryTextLayerWidget extends StatefulWidget {
  final TextElement element;
  final bool selected;
  final VoidCallback onTap;
  final ValueChanged<TextElement> onChanged;
  final VoidCallback onDelete;

  const StoryTextLayerWidget({
    super.key,
    required this.element,
    required this.selected,
    required this.onTap,
    required this.onChanged,
    required this.onDelete,
  });

  @override
  State<StoryTextLayerWidget> createState() => _StoryTextLayerWidgetState();
}

class _StoryTextLayerWidgetState extends State<StoryTextLayerWidget> {
  Offset _startPos = Offset.zero;
  Offset _startFocal = Offset.zero;
  double _startScale = 1;
  double _startRotation = 0;

  @override
  Widget build(BuildContext context) {
    final e = widget.element;
    return Positioned(
      left: e.position.dx,
      top: e.position.dy,
      child: GestureDetector(
        behavior: HitTestBehavior.translucent,
        onTap: widget.onTap,
        onScaleStart: (d) {
          widget.onTap();
          _startPos = e.position;
          _startFocal = d.focalPoint;
          _startScale = e.scale;
          _startRotation = e.rotation;
        },
        onScaleUpdate: (d) {
          final nextScale = (_startScale * d.scale).clamp(0.3, 6.0);
          final nextRotation = _startRotation + d.rotation;
          final nextPos = _startPos + (d.focalPoint - _startFocal);
          widget.onChanged(
            e.copyWith(
              position: nextPos,
              scale: nextScale,
              rotation: nextRotation,
            ),
          );
        },
        child: Transform.rotate(
          angle: e.rotation,
          child: Transform.scale(
            scale: e.scale,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: widget.selected
                  ? BoxDecoration(
                      border: Border.all(color: Colors.white70, width: 1),
                      borderRadius: BorderRadius.circular(6),
                    )
                  : null,
              child: Text(
                e.text,
                textAlign: TextAlign.center,
                style: storyFontStyle(
                  e.fontFamily,
                  color: e.color,
                  fontSize: e.fontSize,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
