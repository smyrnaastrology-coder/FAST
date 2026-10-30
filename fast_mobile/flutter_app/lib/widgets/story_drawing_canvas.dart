import 'dart:math' as math;

import 'package:flutter/material.dart';
import '../models/story_element.dart';

/// Çizim aracı çeşitleri.
enum PenTool { pen, neon, highlight, eraser }

Path _pathOf(List<Offset> points) {
  // Yumuşatılmış çizgi: noktalar arasında quadratic bezier.
  final path = Path();
  path.moveTo(points.first.dx, points.first.dy);
  for (int i = 1; i < points.length - 1; i++) {
    final p = points[i];
    final next = points[i + 1];
    final mid = Offset((p.dx + next.dx) / 2, (p.dy + next.dy) / 2);
    path.quadraticBezierTo(p.dx, p.dy, mid.dx, mid.dy);
  }
  final last = points.last;
  path.lineTo(last.dx, last.dy);
  return path;
}

class StoryDrawingPainter extends CustomPainter {
  final List<DrawingStroke> strokes;

  StoryDrawingPainter({required this.strokes});

  @override
  void paint(Canvas canvas, Size size) {
    for (final stroke in strokes) {
      if (stroke.points.isEmpty) continue;

      final base = Paint()
        ..color = stroke.highlight
            ? stroke.color.withValues(alpha: 0.38)
            : stroke.color
        ..strokeWidth =
            stroke.highlight ? stroke.strokeWidth * 2.4 : stroke.strokeWidth
        ..strokeCap = stroke.highlight ? StrokeCap.square : StrokeCap.round
        ..strokeJoin = StrokeJoin.round
        ..style = PaintingStyle.stroke
        ..isAntiAlias = true;

      if (stroke.points.length == 1) {
        final dotPaint = Paint()
          ..color = base.color
          ..style = PaintingStyle.fill
          ..isAntiAlias = true;
        canvas.drawCircle(
            stroke.points.first, base.strokeWidth / 2, dotPaint);
        continue;
      }

      final path = _pathOf(stroke.points);

      if (stroke.neon) {
        final glow = Paint()
          ..color = stroke.color.withValues(alpha: 0.55)
          ..strokeWidth = stroke.strokeWidth * 2.4
          ..strokeCap = StrokeCap.round
          ..strokeJoin = StrokeJoin.round
          ..style = PaintingStyle.stroke
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 7)
          ..isAntiAlias = true;
        canvas.drawPath(path, glow);
      }

      canvas.drawPath(path, base);
    }
  }

  // Çizim katmanı her değişimde yeniden çizilir. (Liste yerinde güncellendiği
  // için referans karşılaştırması geri almayı ekrana yansıtmıyordu.)
  @override
  bool shouldRepaint(covariant StoryDrawingPainter oldDelegate) => true;
}

/// Fotoğrafın üzerine parmakla serbest çizim.
///
/// [Listener] kullanılır (GestureDetector değil) böylece üstteki/yan taraftaki
/// jest tanıyıcılar (pinch/zoom, scroll) ile rekabete girmez ve her parmak
/// hareketi çizgiye dönüşür. İki parmak birden dokunursa çizim iptal edilir.
class StoryDrawingCanvas extends StatefulWidget {
  final List<DrawingStroke> strokes;
  final ValueChanged<List<DrawingStroke>> onStrokesChanged;

  /// Bir çizim/silme hareketi başlarken çağrılır (geri alma geçmişi için).
  final VoidCallback? onGestureStart;

  final Color currentColor;
  final double strokeWidth;
  final PenTool tool;

  const StoryDrawingCanvas({
    super.key,
    required this.strokes,
    required this.onStrokesChanged,
    required this.currentColor,
    required this.strokeWidth,
    this.tool = PenTool.pen,
    this.onGestureStart,
  });

  @override
  State<StoryDrawingCanvas> createState() => _StoryDrawingCanvasState();
}

class _StoryDrawingCanvasState extends State<StoryDrawingCanvas> {
  DrawingStroke? _currentStroke;
  int _pointers = 0;

  bool get _isEraser => widget.tool == PenTool.eraser;

  void _start(Offset p) {
    if (_isEraser) {
      setState(() => _currentStroke = null);
      _erase(p);
      return;
    }
    setState(() {
      _currentStroke = DrawingStroke(
        points: [p],
        color: widget.currentColor,
        strokeWidth: widget.strokeWidth,
        neon: widget.tool == PenTool.neon,
        highlight: widget.tool == PenTool.highlight,
      );
    });
  }

  void _extend(Offset p) {
    if (_isEraser) {
      _erase(p);
      return;
    }
    final s = _currentStroke;
    if (s == null) return;
    // Çok küçük hareketleri atlayarak çizgiyi hafiflet.
    final last = s.points.last;
    if ((p - last).distanceSquared < 1.2) return;
    setState(() {
      _currentStroke = s.copyWith(points: [...s.points, p]);
    });
  }

  /// Silgi: parmağın değdiği noktaları çizgilerden çıkarır, kalan parçaları
  /// ayrı çizgiler olarak korur.
  void _erase(Offset p) {
    final radius = math.max(widget.strokeWidth * 1.8, 16.0);
    final remaining = <DrawingStroke>[];
    var changed = false;
    for (final stroke in widget.strokes) {
      var hit = false;
      final runs = <List<Offset>>[];
      var run = <Offset>[];
      for (final pt in stroke.points) {
        final near = (pt - p).distance <= radius + stroke.strokeWidth / 2;
        if (near) {
          hit = true;
          if (run.length > 1) runs.add(run);
          run = <Offset>[];
        } else {
          run.add(pt);
        }
      }
      if (!hit) {
        remaining.add(stroke);
        continue;
      }
      changed = true;
      if (run.length > 1) runs.add(run);
      for (final r in runs) {
        remaining.add(stroke.copyWith(points: r));
      }
    }
    if (changed) widget.onStrokesChanged(remaining);
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
          widget.onGestureStart?.call();
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
