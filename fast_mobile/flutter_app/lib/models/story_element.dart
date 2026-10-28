import 'dart:ui';

class DrawingStroke {
  final List<Offset> points;
  final Color color;
  final double strokeWidth;

  DrawingStroke({
    required this.points,
    required this.color,
    required this.strokeWidth,
  });

  DrawingStroke copyWith({
    List<Offset>? points,
    Color? color,
    double? strokeWidth,
  }) {
    return DrawingStroke(
      points: points ?? this.points,
      color: color ?? this.color,
      strokeWidth: strokeWidth ?? this.strokeWidth,
    );
  }
}

class TextElement {
  final String id;
  String text;
  Offset position;
  double scale;
  double rotation;
  Color color;
  double fontSize;
  String fontFamily;

  TextElement({
    required this.id,
    required this.text,
    required this.position,
    this.scale = 1.0,
    this.rotation = 0.0,
    this.color = const Color(0xFFFFFFFF),
    this.fontSize = 28,
    this.fontFamily = 'Roboto',
  });

  TextElement copyWith({
    String? text,
    Offset? position,
    double? scale,
    double? rotation,
    Color? color,
    double? fontSize,
    String? fontFamily,
  }) {
    return TextElement(
      id: id,
      text: text ?? this.text,
      position: position ?? this.position,
      scale: scale ?? this.scale,
      rotation: rotation ?? this.rotation,
      color: color ?? this.color,
      fontSize: fontSize ?? this.fontSize,
      fontFamily: fontFamily ?? this.fontFamily,
    );
  }
}
