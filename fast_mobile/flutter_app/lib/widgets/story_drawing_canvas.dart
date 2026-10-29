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
        ..style = PaintingStyle.stroke
        ..isAntiAlias = true;

      if (stroke.points.length == 1) {
        canvas.drawCircle(stroke.points.first, stroke.strokeWidth / 2, paint..style = PaintingStyle.fill);
        continue;
      }

      // Yumuşatılmış çizgi: noktalar arasında quadratic bezier.
      final path = Path();
      path.moveTo(stroke.points.first.dx, stroke.points.first.dy);
      for (int i = 1; i < stroke.points.length - 1; i++) {
        final p = stroke.points[i];
        final next = stroke.points[i + 1];
        final mid = Offset((p.dx + next.dx) / 2, (p.dy + next.dy) / 2);
        path.quadraticBezierTo(p.dx, p.dy, mid.dx, mid.dy);
      }
      final last = stroke.points.last;
      path.lineTo(last.dx, last.dy);
      canvas.drawPath(path, paint);
    }
  }

  @override
  bool shouldRepaint(covariant StoryDrawingPainter oldDelegate) {
    return oldDelegate.strokes != strokes;
  }
}

/// Fotoğrafın üzerine parmakla serbest çizim.
///
/// [Listener] kullanılır (GestureDetector değil) böylece üstteki/yan taraftaki
/// jest tanıyıcılar (pinch/zoom, scroll) ile rekabete girmez ve her parmak
/// hareketi çizgiye dönüşür. İki parmak birden dokunursa çizim iptal edilir.
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
  int _pointers = 0;

  void _start(Offset p) {
    setState(() {
      _currentStroke = DrawingStroke(
        points: [p],
        color: widget.currentColor,
        strokeWidth: widget.strokeWidth,
      );
    });
  }

  void _extend(Offset p) {
    final s = _currentStroke;
    if (s == null) return;
    // Çok küçük hareketleri atlayarak çizgiyi hafiflet.
    final last = s.points.last;
    if ((p - last).distanceSquared < 1.2) return;
    setState(() {
      _currentStroke = s.copyWith(points: [...s.points, p]);
    });
  }

  void _finish() {
    final s = _currentStroke;
    if (s == null) return;
    final updated = [...widget.strokes, s];
    widget.onStrokesChanged(updated);
    setState(() => _currentStroke = null);
  }

  @override
  Widget build(BuildContext context) {
    final drawn = _currentStroke == null
        ? widget.strokes
        : [...widget.strokes, _currentStroke!];
    return Listener(
      behavior: HitTestBehavior.opaque,
      onPointerDown: (e) {
        _pointers++;
        if (_pointers == 1) {
          _start(e.localPosition);
        } else {
          // İki parmak: çizimi iptal et, pinch/zoom'a izin ver.
          setState(() => _currentStroke = null);
        }
      },
      onPointerMove: (e) {
        if (_pointers == 1) _extend(e.localPosition);
      },
      onPointerUp: (_) {
        _pointers = (_pointers - 1).clamp(0, 10);
        if (_pointers == 0) _finish();
      },
      onPointerCancel: (_) {
        _pointers = (_pointers - 1).clamp(0, 10);
        if (_pointers == 0) _finish();
      },
      child: ClipRect(
        child: CustomPaint(
          painter: StoryDrawingPainter(strokes: drawn),
          size: Size.infinite,
        ),
      ),
    );
  }
}
