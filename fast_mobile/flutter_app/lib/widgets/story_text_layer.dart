import 'package:flutter/material.dart';
import '../models/story_element.dart';

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
  Offset _startOffset = Offset.zero;
  Offset _startPos = Offset.zero;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: widget.element.position.dx,
      top: widget.element.position.dy,
      child: GestureDetector(
        onTap: widget.onTap,
        onPanStart: (d) {
          _startOffset = d.globalPosition;
          _startPos = widget.element.position;
        },
        onPanUpdate: (d) {
          final delta = d.globalPosition - _startOffset;
          widget.onChanged(widget.element.copyWith(position: _startPos + delta));
        },
        child: Transform.rotate(
          angle: widget.element.rotation,
          child: Transform.scale(
            scale: widget.element.scale,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: widget.selected
                  ? BoxDecoration(
                      border: Border.all(color: Colors.white, width: 1),
                      borderRadius: BorderRadius.circular(4),
                    )
                  : null,
              child: Text(
                widget.element.text,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: widget.element.color,
                  fontSize: widget.element.fontSize,
                  fontFamily: widget.element.fontFamily,
                  fontWeight: FontWeight.bold,
                  shadows: const [
                    Shadow(blurRadius: 4, color: Colors.black54, offset: Offset(1, 1)),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
