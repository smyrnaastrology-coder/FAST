import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:uuid/uuid.dart';
import '../config/theme.dart';
import '../models/story_element.dart';
import '../widgets/story_drawing_canvas.dart';
import '../widgets/story_text_layer.dart';

class StoryEditorScreen extends StatefulWidget {
  final XFile imageFile;
  const StoryEditorScreen({super.key, required this.imageFile});

  @override
  State<StoryEditorScreen> createState() => _StoryEditorScreenState();
}

class _StoryEditorScreenState extends State<StoryEditorScreen> {
  final GlobalKey _repaintKey = GlobalKey();
  final List<DrawingStroke> _strokes = [];
  final List<TextElement> _textElements = [];
  String? _selectedTextId;
  bool _drawingMode = false;
  double _strokeWidth = 6.0;
  Color _currentColor = const Color(0xFF00E0FF);
  int _colorTab = 0; // 0 = neon, 1 = pastel
  bool _rendering = false;
  
  final List<Color> _neonColors = [
    const Color(0xFF00E0FF),
    const Color(0xFFFF3366),
    const Color(0xFF39FF14),
    const Color(0xFFFF00FF),
    const Color(0xFFFFAE00),
    const Color(0xFFFFFF00),
  ];
  
  final List<Color> _pastelColors = [
    const Color(0xFFF6A6C1),
    const Color(0xFFC9DEEE),
    const Color(0xFFB8E0D2),
    const Color(0xFFF7D6E0),
    const Color(0xFFFFD6A5),
    const Color(0xFFCAFFBF),
  ];

  List<Color> get _colors => _colorTab == 0 ? _neonColors : _pastelColors;

  void _addText() {
    final newText = TextElement(
      id: const Uuid().v4(),
      text: 'Metin',
      position: Offset(MediaQuery.of(context).size.width / 2 - 50, MediaQuery.of(context).size.height / 2 - 20),
    );
    setState(() {
      _textElements.add(newText);
      _selectedTextId = newText.id;
      _drawingMode = false;
    });
    _editText(newText);
  }

  void _editText(TextElement element) {
    final ctrl = TextEditingController(text: element.text);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: FastTheme.bg,
        title: Text('Metni Düzenle', style: TextStyle(color: FastTheme.accentGold)),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          style: TextStyle(color: FastTheme.text),
          decoration: InputDecoration(
            enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: FastTheme.border)),
            focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: FastTheme.accentGold)),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text('İptal', style: TextStyle(color: FastTheme.textMuted)),
          ),
          TextButton(
            onPressed: () {
              setState(() {
                element.text = ctrl.text.isEmpty ? 'Metin' : ctrl.text;
              });
              Navigator.pop(ctx);
            },
            child: Text('Tamam', style: TextStyle(color: FastTheme.accentGold)),
          ),
        ],
      ),
    );
  }

  void _deleteSelectedText() {
    if (_selectedTextId == null) return;
    setState(() {
      _textElements.removeWhere((e) => e.id == _selectedTextId);
      _selectedTextId = null;
    });
  }

  void _undo() {
    setState(() {
      if (_drawingMode && _strokes.isNotEmpty) {
        _strokes.removeLast();
      } else if (!_drawingMode && _textElements.isNotEmpty) {
        _textElements.removeLast();
        _selectedTextId = null;
      }
    });
  }

  Future<void> _finish() async {
    setState(() => _rendering = true);
    try {
      final boundary = _repaintKey.currentContext?.findRenderObject() as RenderRepaintBoundary?;
      if (boundary == null) throw Exception('Render error');
      final image = await boundary.toImage(pixelRatio: 2.0);
      final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
      if (byteData == null) throw Exception('ByteData error');
      final bytes = byteData.buffer.asUint8List();
      
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/story_${const Uuid().v4()}.png');
      await file.writeAsBytes(bytes);
      
      if (mounted) {
        Navigator.of(context).pop(file);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Hata: $e')));
      }
    } finally {
      if (mounted) setState(() => _rendering = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Canvas area
          RepaintBoundary(
            key: _repaintKey,
            child: Stack(
              children: [
                // Background image
                Positioned.fill(
                  child: Image.file(
                    File(widget.imageFile.path),
                    fit: BoxFit.cover,
                  ),
                ),
                // Drawing layer
                if (_drawingMode)
                  Positioned.fill(
                    child: StoryDrawingCanvas(
                      strokes: _strokes,
                      onStrokesChanged: (strokes) {
                        setState(() {
                          _strokes.clear();
                          _strokes.addAll(strokes);
                        });
                      },
                      currentColor: _currentColor,
                      strokeWidth: _strokeWidth,
                    ),
                  )
                else
                  Positioned.fill(
                    child: CustomPaint(
                      painter: StoryDrawingPainter(strokes: _strokes),
                    ),
                  ),
                // Text layers
                ..._textElements.map((element) => StoryTextLayerWidget(
                  element: element,
                  selected: _selectedTextId == element.id,
                  onTap: () {
                    setState(() {
                      _selectedTextId = element.id;
                      _drawingMode = false;
                    });
                  },
                  onChanged: (updated) {
                    setState(() {
                      final idx = _textElements.indexWhere((e) => e.id == updated.id);
                      if (idx >= 0) _textElements[idx] = updated;
                    });
                  },
                  onDelete: _deleteSelectedText,
                )),
              ],
            ),
          ),
          // Top bar
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close, color: Colors.white, size: 28),
                  ),
                  const Spacer(),
                  if (_selectedTextId != null && !_drawingMode)
                    IconButton(
                      onPressed: () {
                        final element = _textElements.firstWhere((e) => e.id == _selectedTextId);
                        _editText(element);
                      },
                      icon: const Icon(Icons.edit, color: Colors.white),
                    ),
                  if (_selectedTextId != null && !_drawingMode)
                    IconButton(
                      onPressed: _deleteSelectedText,
                      icon: const Icon(Icons.delete, color: Colors.white),
                    ),
                  IconButton(
                    onPressed: _undo,
                    icon: const Icon(Icons.undo, color: Colors.white),
                  ),
                  TextButton(
                    onPressed: _rendering ? null : _finish,
                    child: _rendering
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : Text('Paylaş', style: TextStyle(color: FastTheme.accentGold, fontWeight: FontWeight.bold, fontSize: 16)),
                  ),
                ],
              ),
            ),
          ),
          // Bottom toolbar
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: SafeArea(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Stroke width slider
                  if (_drawingMode)
                    Container(
                      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: Colors.black54,
                        borderRadius: BorderRadius.circular(30),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.brush, color: Colors.white, size: 18),
                          Expanded(
                            child: Slider(
                              value: _strokeWidth,
                              min: 2,
                              max: 14,
                              activeColor: _currentColor,
                              inactiveColor: Colors.white38,
                              onChanged: (v) => setState(() => _strokeWidth = v),
                            ),
                          ),
                          Text(_strokeWidth.toInt().toString(), style: const TextStyle(color: Colors.white)),
                        ],
                      ),
                    ),
                  // Color palette
                  if (_drawingMode)
                    Container(
                      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.black54,
                        borderRadius: BorderRadius.circular(30),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              _tabButton('Neon', 0),
                              const SizedBox(width: 12),
                              _tabButton('Pastel', 1),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: _colors.map((c) => _colorButton(c)).toList(),
                          ),
                        ],
                      ),
                    ),
                  // Main toolbar
                  Container(
                    margin: const EdgeInsets.all(16),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(40),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        _toolButton(Icons.text_fields, 'Metin', () => _addText()),
                        _toolButton(Icons.brush, 'Çizim', () {
                          setState(() {
                            _drawingMode = !_drawingMode;
                            _selectedTextId = null;
                          });
                        }, active: _drawingMode),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _tabButton(String label, int tab) {
    final active = _colorTab == tab;
    return GestureDetector(
      onTap: () => setState(() => _colorTab = tab),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        decoration: BoxDecoration(
          color: active ? FastTheme.accentGold : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(label, style: TextStyle(color: active ? Colors.black : Colors.white, fontWeight: FontWeight.w600)),
      ),
    );
  }

  Widget _colorButton(Color color) {
    final active = _currentColor == color;
    return GestureDetector(
      onTap: () => setState(() => _currentColor = color),
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
          border: Border.all(color: active ? Colors.white : Colors.white38, width: active ? 3 : 1),
          boxShadow: active ? [BoxShadow(color: color.withOpacity(0.6), blurRadius: 8)] : null,
        ),
      ),
    );
  }

  Widget _toolButton(IconData icon, String label, VoidCallback onTap, {bool active = false}) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: active ? FastTheme.accentGold : Colors.white, size: 28),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(color: active ? FastTheme.accentGold : Colors.white, fontSize: 11)),
        ],
      ),
    );
  }
}
