import 'dart:io';
import 'dart:math' as math;
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

/// Hikâye editörü.
///
/// Tasarım:
///  - Tuval her zaman 9:16 (hikâye oranı) ve tam ekranı kaplar; görsel
///    `BoxFit.cover` ile tuvali doldurur, altta siyah boşluk kalmaz.
///  - "Taşı" modunda iki parmakla büyüt/küçült/döndür, tek parmakla kaydır.
///  - "Çizim" modunda tek parmak fotoğrafın üzerine çizer (neon/pastel).
///  - Metinler parmakla taşınır, iki parmakla büyütülür/döndürülür; font,
///    renk ve boyut alt panelden seçilir.
///  - Tüm katmanlar tek bir RepaintBoundary içinde olduğu için paylaşılan
///    görsel ekranda görünenin birebir aynısıdır (WYSIWYG).
class StoryEditorScreen extends StatefulWidget {
  final XFile imageFile;
  const StoryEditorScreen({super.key, required this.imageFile});

  @override
  State<StoryEditorScreen> createState() => _StoryEditorScreenState();
}

enum _EditorMode { move, draw }

class _StoryEditorScreenState extends State<StoryEditorScreen> {
  final GlobalKey _repaintKey = GlobalKey();
  final List<DrawingStroke> _strokes = [];
  final List<TextElement> _textElements = [];
  String? _selectedTextId;
  String? _editingTextId;
  TextEditingController? _textCtrl;
  FocusNode? _textFocus;
  _EditorMode _mode = _EditorMode.move;
  PenTool _tool = PenTool.pen;
  double _strokeWidth = 6.0;
  Color _currentColor = const Color(0xFF00E0FF);
  int _colorTab = 0; // 0 = canlı, 1 = pastel
  bool _rendering = false;

  /// Geri alma geçmişi (çizimler + metinler).
  final List<_UndoSnapshot> _history = [];
  static const int _historyLimit = 60;

  // Görsel dönüşümü
  Offset _offset = Offset.zero;
  double _scale = 1.0;
  double _rotation = 0.0;
  late Offset _startFocal;
  late double _startScale;
  late double _startRotation;
  Size _canvasSize = Size.zero;

  final List<Color> _neonColors = [
    const Color(0xFF00E0FF), const Color(0xFFFF3366), const Color(0xFF39FF14),
    const Color(0xFFFF00FF), const Color(0xFFFFAE00), const Color(0xFFFFFF00),
    const Color(0xFF00FF88), const Color(0xFFFF4D4D), const Color(0xFF4D79FF),
    const Color(0xFFFF66CC), const Color(0xFF00FFFF), const Color(0xFFFFD700),
  ];

  final List<Color> _pastelColors = [
    const Color(0xFFF6A6C1), const Color(0xFFC9DEEE), const Color(0xFFB8E0D2),
    const Color(0xFFF7D6E0), const Color(0xFFFFD6A5), const Color(0xFFCAFFBF),
    const Color(0xFFD4C5F9), const Color(0xFFFFE0E0), const Color(0xFFE0F7FA),
    const Color(0xFFFFF3C4), const Color(0xFFE8D5C4), const Color(0xFFCCE5FF),
  ];

  final List<Color> _textColors = [
    Colors.white, Colors.black, const Color(0xFFFF3366), const Color(0xFF00E0FF),
    const Color(0xFF39FF14), const Color(0xFFFFAE00), const Color(0xFFFF00FF),
    const Color(0xFFFFFF00), const Color(0xFF4D79FF),
  ];

  List<Color> get _colors => _colorTab == 0 ? _neonColors : _pastelColors;

  TextElement? get _selectedText {
    if (_selectedTextId == null) return null;
    for (final e in _textElements) {
      if (e.id == _selectedTextId) return e;
    }
    return null;
  }

  void _addText() {
    _pushHistory();
    final newText = TextElement(
      id: const Uuid().v4(),
      text: 'Metin',
      position: const Offset(60, 120),
      color: Colors.white,
    );
    setState(() {
      _textElements.add(newText);
      _selectedTextId = newText.id;
      _mode = _EditorMode.move;
    });
    _editText(newText);
  }

  /// Metni fotoğrafın üstünü kapatmayan, alt paneldeki satır içi alanda
  /// düzenler. (Eski tam ekran diyalog beyaz perde gibi görünüyordu.)
  void _editText(TextElement element) {
    final old = _textCtrl;
    if (old != null) {
      old.removeListener(_onInlineTextChanged);
      WidgetsBinding.instance.addPostFrameCallback((_) => old.dispose());
    }
    final ctrl = TextEditingController(text: element.text);
    _textCtrl = ctrl;
    _textFocus?.dispose();
    _textFocus = FocusNode();
    ctrl.addListener(_onInlineTextChanged);
    ctrl.selection = TextSelection(
      baseOffset: 0,
      extentOffset: ctrl.text.length,
    );
    setState(() {
      _selectedTextId = element.id;
      _editingTextId = element.id;
      _mode = _EditorMode.move;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _textFocus?.requestFocus();
    });
  }

  void _onInlineTextChanged() {
    final id = _editingTextId;
    final ctrl = _textCtrl;
    if (id == null || ctrl == null) return;
    final idx = _textElements.indexWhere((e) => e.id == id);
    if (idx < 0) return;
    setState(() {
      _textElements[idx] = _textElements[idx].copyWith(text: ctrl.text);
    });
  }

  void _finishInlineEdit() {
    final id = _editingTextId;
    if (id != null) {
      final idx = _textElements.indexWhere((e) => e.id == id);
      if (idx >= 0 && _textElements[idx].text.trim().isEmpty) {
        setState(() {
          _textElements[idx] = _textElements[idx].copyWith(text: 'Metin');
        });
      }
    }
    _textFocus?.unfocus();
    setState(() => _editingTextId = null);
  }

  void _updateSelectedText(TextElement Function(TextElement) fn) {
    final e = _selectedText;
    if (e == null) return;
    setState(() {
      final idx = _textElements.indexWhere((x) => x.id == e.id);
      if (idx >= 0) _textElements[idx] = fn(_textElements[idx]);
    });
  }

  void _deleteSelectedText() {
    if (_selectedTextId == null) return;
    _pushHistory();
    if (_editingTextId == _selectedTextId) {
      _textFocus?.unfocus();
      _editingTextId = null;
    }
    setState(() {
      _textElements.removeWhere((e) => e.id == _selectedTextId);
      _selectedTextId = null;
    });
  }

  /// Bir sonraki adımdan önce mevcut durumu yığına alır.
  void _pushHistory() {
    if (_history.length >= _historyLimit) _history.removeAt(0);
    _history.add(
      _UndoSnapshot(
        strokes: List<DrawingStroke>.of(_strokes),
        texts: List<TextElement>.of(_textElements),
      ),
    );
  }

  void _undo() {
    if (_history.isEmpty) return;
    final snap = _history.removeLast();
    _textFocus?.unfocus();
    setState(() {
      _strokes
        ..clear()
        ..addAll(snap.strokes);
      _textElements
        ..clear()
        ..addAll(snap.texts);
      _selectedTextId = null;
      _editingTextId = null;
    });
  }

  void _clearAll() {
    if (_strokes.isEmpty && _textElements.isEmpty) return;
    _pushHistory();
    _textFocus?.unfocus();
    setState(() {
      _strokes.clear();
      _textElements.clear();
      _selectedTextId = null;
      _editingTextId = null;
    });
  }

  void _resetImageTransform() {
    setState(() {
      _offset = Offset.zero;
      _scale = 1.0;
      _rotation = 0.0;
    });
  }

  Matrix4 _imageMatrix() {
    final c = Offset(_canvasSize.width / 2, _canvasSize.height / 2);
    return Matrix4.identity()
      ..translate(_offset.dx, _offset.dy)
      ..translate(c.dx, c.dy)
      ..rotateZ(_rotation)
      ..scale(_scale)
      ..translate(-c.dx, -c.dy);
  }

  void _onScaleStart(ScaleStartDetails d) {
    _startFocal = d.localFocalPoint;
    _startScale = _scale;
    _startRotation = _rotation;
  }

  void _onScaleUpdate(ScaleUpdateDetails d) {
    final newScale = (_startScale * d.scale).clamp(0.7, 5.0);
    final newRotation = _startRotation + d.rotation;
    final c = Offset(_canvasSize.width / 2, _canvasSize.height / 2);
    final p = _startFocal - c;
    final cosR = math.cos(newRotation);
    final sinR = math.sin(newRotation);
    final rotated = Offset(
      newScale * (p.dx * cosR - p.dy * sinR),
      newScale * (p.dx * sinR + p.dy * cosR),
    );
    setState(() {
      _scale = newScale;
      _rotation = newRotation;
      _offset = (d.localFocalPoint - c) - rotated;
    });
  }

  Future<void> _finish() async {
    FocusScope.of(context).unfocus();
    setState(() {
      _rendering = true;
      _selectedTextId = null;
      _editingTextId = null;
    });
    // Seçim çerçevesinin çizilmemesi için bir kare bekle.
    await Future<void>.delayed(const Duration(milliseconds: 40));
    try {
      final boundary =
          _repaintKey.currentContext?.findRenderObject() as RenderRepaintBoundary?;
      if (boundary == null) throw Exception('Render error');
      final image = await boundary.toImage(pixelRatio: 2.5);
      final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
      if (byteData == null) throw Exception('ByteData error');
      final bytes = byteData.buffer.asUint8List();

      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/story_${const Uuid().v4()}.png');
      await file.writeAsBytes(bytes);

      if (mounted) Navigator.of(context).pop(file);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hata: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _rendering = false);
    }
  }

  @override
  void dispose() {
    _textCtrl?.removeListener(_onInlineTextChanged);
    _textCtrl?.dispose();
    _textFocus?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Klavye açılınca tuvalin küçülmesini engelle: klavye panelin üstüne biner,
    // metin alanı ise klavyenin hemen üstünde yüzer. Böylece fotoğraf hiçbir
    // zaman beyaz bir katmanla / kırpılmış bir alanla kapanmaz.
    final keyboard = MediaQuery.of(context).viewInsets.bottom;
    return Scaffold(
      backgroundColor: Colors.black,
      resizeToAvoidBottomInset: false,
      body: SafeArea(
        child: Stack(
          children: [
            Column(
              children: [
                _topBar(),
                Expanded(child: _canvasArea()),
                _bottomPanel(),
              ],
            ),
            if (_editingTextId != null)
              Positioned(
                left: 10,
                right: 10,
                bottom: keyboard + 10,
                child: _inlineTextEditor(),
              ),
          ],
        ),
      ),
    );
  }

  Widget _inlineTextEditor() {
    return Container(
      padding: const EdgeInsets.fromLTRB(8, 6, 4, 6),
      decoration: BoxDecoration(
        color: const Color(0xFF11151C).withValues(alpha: 0.97),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: FastTheme.accentGold.withValues(alpha: 0.55)),
        boxShadow: const [
          BoxShadow(color: Colors.black54, blurRadius: 12, offset: Offset(0, 4)),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: TextField(
              controller: _textCtrl,
              focusNode: _textFocus,
              autofocus: true,
              maxLines: 3,
              minLines: 1,
              cursorColor: FastTheme.accentGold,
              style: const TextStyle(color: Colors.white, fontSize: 16),
              onSubmitted: (_) => _finishInlineEdit(),
              decoration: InputDecoration(
                isDense: true,
                hintText: 'Yazı yaz… fotoğrafın üstünde canlı görünür',
                hintStyle: const TextStyle(color: Colors.white38, fontSize: 13),
                filled: true,
                fillColor: const Color(0xFF1B1F2A),
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          IconButton(
            tooltip: 'Tamam',
            onPressed: _finishInlineEdit,
            icon: Icon(Icons.check_circle, color: FastTheme.accentGold),
          ),
        ],
      ),
    );
  }

  Widget _topBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 4, 8, 0),
      child: Row(
        children: [
          IconButton(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.close, color: Colors.white, size: 26),
          ),
          const Spacer(),
          IconButton(
            tooltip: 'Geri al',
            onPressed: _history.isEmpty ? null : _undo,
            icon: Icon(
              Icons.undo,
              color: _history.isEmpty ? Colors.white24 : Colors.white,
            ),
          ),
          IconButton(
            tooltip: 'Tüm çizimleri/yazıları sil',
            onPressed:
                (_strokes.isEmpty && _textElements.isEmpty) ? null : _clearAll,
            icon: Icon(
              Icons.delete_sweep_outlined,
              color: (_strokes.isEmpty && _textElements.isEmpty)
                  ? Colors.white24
                  : Colors.white,
            ),
          ),
          IconButton(
            tooltip: 'Görseli sıfırla',
            onPressed: _resetImageTransform,
            icon: const Icon(Icons.restart_alt, color: Colors.white),
          ),
          const SizedBox(width: 4),
          TextButton(
            onPressed: _rendering ? null : _finish,
            child: _rendering
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      color: Colors.white,
                      strokeWidth: 2,
                    ),
                  )
                : Text(
                    'Paylaş',
                    style: TextStyle(
                      color: FastTheme.accentGold,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _canvasArea() {
    return Center(
      child: LayoutBuilder(
        builder: (context, cons) {
          const aspect = 9 / 16;
          var w = cons.maxWidth;
          var h = w / aspect;
          if (h > cons.maxHeight) {
            h = cons.maxHeight;
            w = h * aspect;
          }
          _canvasSize = Size(w, h);
          return SizedBox(
            width: w,
            height: h,
            child: RepaintBoundary(
              key: _repaintKey,
              child: Stack(
                clipBehavior: Clip.hardEdge,
                fit: StackFit.expand,
                children: [
                  // 1) Fotoğraf (cover — tuvali tamamen doldurur)
                  Transform(
                    transform: _imageMatrix(),
                    child: Image.file(
                      File(widget.imageFile.path),
                      fit: BoxFit.cover,
                      width: w,
                      height: h,
                      gaplessPlayback: true,
                    ),
                  ),
                  // 2) Çizim katmanı
                  Positioned.fill(
                    child: _mode == _EditorMode.draw
                        ? StoryDrawingCanvas(
                            strokes: _strokes,
                            onGestureStart: _pushHistory,
                            onStrokesChanged: (strokes) {
                              setState(() {
                                _strokes
                                  ..clear()
                                  ..addAll(strokes);
                              });
                            },
                            currentColor: _currentColor,
                            strokeWidth: _strokeWidth,
                            tool: _tool,
                          )
                        : CustomPaint(
                            painter: StoryDrawingPainter(strokes: _strokes),
                          ),
                  ),
                  // 3) Taşı modunda jest katmanı (fotoğrafı döndür/büyüt)
                  if (_mode == _EditorMode.move)
                    Positioned.fill(
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onScaleStart: _onScaleStart,
                        onScaleUpdate: _onScaleUpdate,
                        onTap: () => setState(() => _selectedTextId = null),
                      ),
                    ),
                  // 4) Metin katmanları
                  ..._textElements.map(
                    (element) => IgnorePointer(
                      ignoring: _mode == _EditorMode.draw,
                      child: StoryTextLayerWidget(
                        element: element,
                        selected: _selectedTextId == element.id,
                        onTap: () {
                          if (_editingTextId != null &&
                              _editingTextId != element.id) {
                            _finishInlineEdit();
                          }
                          setState(() {
                            _selectedTextId = element.id;
                          });
                        },
                        onChanged: (updated) {
                          setState(() {
                            final idx = _textElements.indexWhere(
                              (e) => e.id == updated.id,
                            );
                            if (idx >= 0) _textElements[idx] = updated;
                          });
                        },
                        onDelete: _deleteSelectedText,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _bottomPanel() {
    final sel = _selectedText;
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF11151C),
        border: Border(
          top: BorderSide(color: FastTheme.border.withValues(alpha: 0.4)),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_mode == _EditorMode.draw) _drawControls(),
          if (sel != null) _textControls(sel),
          _mainTools(),
        ],
      ),
    );
  }

  Widget _drawControls() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            height: 34,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                _penChip('Kalem', PenTool.pen, Icons.edit),
                _penChip('Neon', PenTool.neon, Icons.auto_awesome),
                _penChip('Fosforlu', PenTool.highlight, Icons.brush),
                _penChip('Silgi', PenTool.eraser, Icons.cleaning_services),
              ],
            ),
          ),
          Row(
            children: [
              Icon(
                _tool == PenTool.eraser ? Icons.cleaning_services : Icons.brush,
                color: Colors.white70,
                size: 16,
              ),
              Expanded(
                child: SliderTheme(
                  data: SliderTheme.of(context).copyWith(
                    trackHeight: 2,
                    thumbShape:
                        const RoundSliderThumbShape(enabledThumbRadius: 8),
                  ),
                  child: Slider(
                    value: _strokeWidth,
                    min: 2,
                    max: 20,
                    activeColor: _currentColor,
                    inactiveColor: Colors.white24,
                    onChanged: (v) => setState(() => _strokeWidth = v),
                  ),
                ),
              ),
              SizedBox(
                width: 26,
                child: Text(
                  _strokeWidth.toInt().toString(),
                  textAlign: TextAlign.end,
                  style: const TextStyle(color: Colors.white70, fontSize: 12),
                ),
              ),
              const SizedBox(width: 10),
              _tabButton('Canlı', 0),
              const SizedBox(width: 6),
              _tabButton('Pastel', 1),
            ],
          ),
          const SizedBox(height: 6),
          SizedBox(
            height: 40,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _colors.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (_, i) => _colorButton(_colors[i]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _penChip(String label, PenTool tool, IconData icon) {
    final active = _tool == tool;
    return GestureDetector(
      onTap: () => setState(() => _tool = tool),
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: active ? FastTheme.accentGold : Colors.white.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: active ? Colors.black : Colors.white),
            const SizedBox(width: 5),
            Text(
              label,
              style: TextStyle(
                color: active ? Colors.black : Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _textControls(TextElement sel) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_editingTextId == sel.id)
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Yazıyı klavyeden yaz — fotoğrafın üstünde canlı görünür',
                style: TextStyle(color: FastTheme.accentGold, fontSize: 12),
              ),
            )
          else
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                onPressed: () => _editText(sel),
                icon: const Icon(Icons.edit, color: Colors.white70, size: 18),
                label: const Text(
                  'Yazıyı düzenle',
                  style: TextStyle(color: Colors.white70, fontSize: 13),
                ),
              ),
            ),
          const SizedBox(height: 6),
          SizedBox(
            height: 32,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: kStoryFonts.length,
              separatorBuilder: (_, __) => const SizedBox(width: 6),
              itemBuilder: (_, i) {
                final f = kStoryFonts[i];
                final active = sel.fontFamily == f.key;
                return GestureDetector(
                  onTap: () => _updateSelectedText(
                    (e) => e.copyWith(fontFamily: f.key),
                  ),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: active
                          ? FastTheme.accentGold
                          : Colors.white.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      f.value,
                      style: storyFontStyle(
                        f.key,
                        color: active ? Colors.black : Colors.white,
                        fontSize: 13,
                        weight: FontWeight.w600,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 36,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: _textColors.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 8),
                    itemBuilder: (_, i) {
                      final c = _textColors[i];
                      final active = sel.color == c;
                      return GestureDetector(
                        onTap: () =>
                            _updateSelectedText((e) => e.copyWith(color: c)),
                        child: Container(
                          width: 30,
                          height: 30,
                          decoration: BoxDecoration(
                            color: c,
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: active ? FastTheme.accentGold : Colors.white38,
                              width: active ? 3 : 1,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
              IconButton(
                tooltip: 'Sil',
                onPressed: _deleteSelectedText,
                icon: const Icon(Icons.delete_outline,
                    color: Colors.white, size: 20),
              ),
            ],
          ),
          Row(
            children: [
              const Icon(Icons.format_size, color: Colors.white54, size: 16),
              Expanded(
                child: SliderTheme(
                  data: SliderTheme.of(context).copyWith(
                    trackHeight: 2,
                    thumbShape:
                        const RoundSliderThumbShape(enabledThumbRadius: 8),
                  ),
                  child: Slider(
                    value: sel.fontSize.clamp(12, 72),
                    min: 12,
                    max: 72,
                    activeColor: FastTheme.accentGold,
                    inactiveColor: Colors.white24,
                    onChanged: (v) =>
                        _updateSelectedText((e) => e.copyWith(fontSize: v)),
                  ),
                ),
              ),
              Text(
                sel.fontSize.toInt().toString(),
                style: const TextStyle(color: Colors.white70, fontSize: 12),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _mainTools() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _toolButton(Icons.text_fields, 'Metin', _addText),
          _toolButton(
            Icons.open_with,
            'Taşı',
            () => setState(() {
              _mode = _EditorMode.move;
              _selectedTextId = null;
            }),
            active: _mode == _EditorMode.move && _selectedTextId == null,
          ),
          _toolButton(
            Icons.draw,
            'Çizim',
            () => setState(() {
              _mode = _EditorMode.draw;
              _selectedTextId = null;
            }),
            active: _mode == _EditorMode.draw,
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
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: active ? FastTheme.accentGold : Colors.white.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: active ? Colors.black : Colors.white,
            fontWeight: FontWeight.w600,
            fontSize: 11,
          ),
        ),
      ),
    );
  }

  Widget _colorButton(Color color) {
    final active = _currentColor == color;
    return GestureDetector(
      onTap: () => setState(() => _currentColor = color),
      child: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
          border: Border.all(
            color: active ? Colors.white : Colors.white24,
            width: active ? 3 : 1,
          ),
          boxShadow: active
              ? [BoxShadow(color: color.withValues(alpha: 0.7), blurRadius: 10)]
              : null,
        ),
      ),
    );
  }

  Widget _toolButton(
    IconData icon,
    String label,
    VoidCallback onTap, {
    bool active = false,
  }) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: active ? FastTheme.accentGold : Colors.white,
              size: 24,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                color: active ? FastTheme.accentGold : Colors.white,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Geri alma için saklanan anlık görüntü.
class _UndoSnapshot {
  final List<DrawingStroke> strokes;
  final List<TextElement> texts;

  _UndoSnapshot({required this.strokes, required this.texts});
}
