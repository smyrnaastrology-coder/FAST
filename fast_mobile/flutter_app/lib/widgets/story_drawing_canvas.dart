import 'package:flutter/material.dart';
import '../models/story_element.dart';

class StoryDrawingPainter extends CustomPainter {
  final List<DrawingStroke> strokes;

  StoryDrawingPainter({required this.strokes});

  @override
  void paint(Canvas canvas, Size size) {
    for (final stroke in strokes) {
      if (stroke.points.isEmpty) continue;
      final paint = Paint()
        ..color = stroke.color
        ..strokeWidth = stroke.strokeWidth
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round
        ..style = PaintingStyle.stroke;
      final path = Path();
      path.moveTo(stroke.points.first.dx, stroke.points.first.dy);
      for (int i = 1; i < stroke.points.length; i++) {
        path.lineTo(stroke.points[i].dx, stroke.points[i].dy);
      }
      canvas.drawPath(path, paint);
    }
  }

  @override
  bool shouldRepaint(covariant StoryDrawingPainter oldDelegate) {
    return oldDelegate.strokes != strokes;
  }
}

class StoryDrawingCanvas extends StatefulWidget {
  final List<DrawingStroke> strokes;
  final ValueChanged<List<DrawingStroke>> onStrokesChanged;
  final Color currentColor;
  final double strokeWidth;

  const StoryDrawingCanvas({
    super.key,
    required this.strokes,
    required this.onStrokesChanged,
    required this.currentColor,
    required this.strokeWidth,
  });

  @override
  State<StoryDrawingCanvas> createState() => _StoryDrawingCanvasState();
}

class _StoryDrawingCanvasState extends State<StoryDrawingCanvas> {
  DrawingStroke? _currentStroke;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onPanStart: (details) {
        setState(() {
          _currentStroke = DrawingStroke(
            points: [details.localPosition],
            color: widget.currentColor,
            strokeWidth: widget.strokeWidth,
          );
        });
      },
      onPanUpdate: (details) {
        if (_currentStroke == null) return;
        setState(() {
          _currentStroke = _currentStroke!.copyWith(
            points: List<Offset>.from(_currentStroke!.points)..add(details.localPosition),
          );
        });
      },
      onPanEnd: (_) {
        if (_currentStroke == null) return;
        final updated = List<DrawingStroke>.from(widget.strokes)..add(_currentStroke!);
        widget.onStrokesChanged(updated);
        setState(() => _currentStroke = null);
      },
      child: CustomPaint(
        painter: StoryDrawingPainter(
          strokes: _currentStroke == null
              ? widget.strokes
              : List<DrawingStroke>.from(widget.strokes)..add(_currentStroke!),
        ),
        size: Size.infinite,
      ),
    );
  }
}
