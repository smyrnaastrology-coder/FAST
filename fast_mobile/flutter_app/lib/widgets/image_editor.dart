import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:image/image.dart' as img_lib;
import '../config/theme.dart';
import '../l10n/app_localizations.dart';

/// Seçilen görseli ekranda yakınlaştır/uzaştır (pinch), çevir, kaydır.
///
/// Hareketler (ham pointer ile işlenir — pinch/long-press çakışması yok):
///   1) İki parmakla sıkıştırma            -> büyüt / küçült
///   2) İki parmakla burulma (twist)       -> serbest döndür
///   3) Tek parmakla sürükleme            -> kaydır (pan)
///   4) "Döndür" düğmesi aktifken sürükle -> tek parmakla döndür
///   5) Basılı tutup sürükleme            -> tek parmakla döndür
///   6) Sağ alttaki düğmeler              -> 90° çevir, +/- zoom, sıfırla
///
/// Önizleme ile yüklenen çıktı BİREBİR aynı çizim fonksiyonunu
/// kullandığı için WYSIWYG'dir.
///
/// [aspect] çıktı en/boy oranı (post=1.0, hikâye=9/16).
/// Parent, kaydetmeden önce [ImageEditorState.render] çağırıp JPEG byte alır.
class ImageEditor extends StatefulWidget {
  final Uint8List bytes;
  final double aspect;
  final int outputWidth;
  final int quality;
  const ImageEditor({
    super.key,
    required this.bytes,
    this.aspect = 1.0,
    this.outputWidth = 1080,
    this.quality = 85,
  });

  @override
  ImageEditorState createState() => ImageEditorState();
}

class ImageEditorState extends State<ImageEditor> {
  ui.Image? _img;
  double _rot = 0.0; // radyan (serbest donus)
  double _scale = 1.0;
  Offset _offset = Offset.zero; // cerceve boyutuna oranli (pan)

  // ── Ham pointer durumu ──
  final Map<int, Offset> _ptrs = {};
  double _pinchDist = 0; // iki parmak baslangic mesafesi
  double _pinchAngle = 0; // iki parmak baslangic acisi
  Offset _pinchMid = Offset.zero; // iki parmak baslangic orta noktasi
  double _lastAngle = 0; // tek parmak icin son aci

  bool _rotateMode = false; // "Dondur" dugmesi
  bool _holdRotate = false; // basili tutma ile gecici dondurme
  Size _size = Size.zero;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant ImageEditor old) {
    super.didUpdateWidget(old);
    if (old.bytes != widget.bytes) {
      _rot = 0.0;
      _scale = 1.0;
      _offset = Offset.zero;
      _load();
    }
  }

  Future<void> _load() async {
    try {
      final c = await ui.instantiateImageCodec(widget.bytes);
      final f = await c.getNextFrame();
      if (mounted) setState(() => _img = f.image);
    } catch (_) {
      if (mounted) setState(() => _img = null);
    }
  }

  void rotate(int dir) => setState(() => _rot += dir * math.pi / 2);

  void zoom(double factor) => setState(() {
        _scale = (_scale * factor).clamp(0.5, 5.0);
      });

  void reset() => setState(() {
        _rot = 0.0;
        _scale = 1.0;
        _offset = Offset.zero;
        _rotateMode = false;
      });

  /// Mevcut transformu çıktı boyutunda JPEG olarak üretir.
  ///
  /// PNG yerine JPEG (q85) kullanılır: 1080px bir fotoğraf PNG'de ~2-4 MB,
  /// JPEG'de ~150-300 KB. Depolama limiti ve yükleme süresi bu sayede
  /// yaklaşık 10-20 kat iyileşir.
  Future<Uint8List> render() async {
    final img = _img;
    if (img == null) return widget.bytes;
    final outW = widget.outputWidth;
    final outH = math.max(1, (outW / widget.aspect).round());
    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder, Rect.fromLTWH(0, 0, outW.toDouble(), outH.toDouble()));
    draw(canvas, Size(outW.toDouble(), outH.toDouble()), img, _rot, _scale, _offset);
    final pic = recorder.endRecording();
    final out = await pic.toImage(outW, outH);
    try {
      final rgba = await out.toByteData(format: ui.ImageByteFormat.rawRgba);
      if (rgba == null) return widget.bytes;
      final pixels = rgba.buffer.asUint8List(rgba.offsetInBytes, rgba.lengthInBytes);
      final decoded = img_lib.Image.fromBytes(
        width: outW,
        height: outH,
        bytes: pixels.buffer,
        order: img_lib.ChannelOrder.rgba,
      );
      return img_lib.encodeJpg(decoded, quality: widget.quality);
    } finally {
      out.dispose();
    }
  }

  /// Onizleme ve cikti icin TEK cizim kaynagi.
  static void draw(Canvas c, Size size, ui.Image img, double rot, double scale, Offset off) {
    final rect = Offset.zero & size;
    c.save();
    c.clipRect(rect);
    c.drawRect(rect, Paint()..color = const Color(0xFF000000));
    final iw = img.width.toDouble();
    final ih = img.height.toDouble();
    // Donmus halin cerceve kutusunu kapsayacak sekilde olcekle (bosluk kalmasin).
    final cosA = math.cos(rot).abs();
    final sinA = math.sin(rot).abs();
    final bw = iw * cosA + ih * sinA;
    final bh = iw * sinA + ih * cosA;
    final base = math.max(size.width / bw, size.height / bh);
    // Pan ekran uzayinda (dondurmeden bagimsiz) uygulanir.
    c.translate(size.width / 2 + off.dx * size.width, size.height / 2 + off.dy * size.height);
    c.rotate(rot);
    final s = base * scale;
    c.drawImageRect(
      img,
      Rect.fromLTWH(0, 0, iw, ih),
      Rect.fromCenter(center: Offset.zero, width: iw * s, height: ih * s),
      Paint()..filterQuality = FilterQuality.high,
    );
    c.restore();
  }

  // ── Ham pointer islemleri ─────────────────────────────────────────
  double _angleAt(Offset local) {
    final center = Offset(_size.width / 2, _size.height / 2);
    return math.atan2(local.dy - center.dy, local.dx - center.dx);
  }

  void _onDown(PointerDownEvent e) {
    _ptrs[e.pointer] = e.localPosition;
    _lastAngle = _angleAt(e.localPosition);
    if (_ptrs.length == 2) {
      final p = _ptrs.values.take(2).toList();
      _pinchDist = (p[0] - p[1]).distance;
      _pinchAngle = math.atan2(p[1].dy - p[0].dy, p[1].dx - p[0].dx);
      _pinchMid = Offset((p[0].dx + p[1].dx) / 2, (p[0].dy + p[1].dy) / 2);
    }
  }

  void _onMove(PointerMoveEvent e) {
    if (!_ptrs.containsKey(e.pointer)) return;
    _ptrs[e.pointer] = e.localPosition;

    if (_ptrs.length >= 2) {
      // ── Iki parmak: pinch zoom + twist dondurme + orta nokta kaydirma ──
      final p = _ptrs.values.take(2).toList();
      final dist = (p[0] - p[1]).distance;
      final ang = math.atan2(p[1].dy - p[0].dy, p[1].dx - p[0].dx);
      final mid = Offset((p[0].dx + p[1].dx) / 2, (p[0].dy + p[1].dy) / 2);
      if (_pinchDist > 0 && dist > 0 && _size.width > 0 && _size.height > 0) {
        final factor = dist / _pinchDist;
        var dAng = ang - _pinchAngle;
        if (dAng > math.pi) {
          dAng -= 2 * math.pi;
        } else if (dAng < -math.pi) {
          dAng += 2 * math.pi;
        }
        final dMid = mid - _pinchMid;
        setState(() {
          _scale = (_scale * factor).clamp(0.5, 5.0);
          _rot += dAng;
          _offset = Offset(
            (_offset.dx + dMid.dx / _size.width).clamp(-1.0, 1.0),
            (_offset.dy + dMid.dy / _size.height).clamp(-1.0, 1.0),
          );
        });
      }
      _pinchDist = dist;
      _pinchAngle = ang;
      _pinchMid = mid;
      return;
    }

    // ── Tek parmak ──
    final angle = _angleAt(e.localPosition);
    if (_rotateMode || _holdRotate) {
      var d = angle - _lastAngle;
      if (d > math.pi) {
        d -= 2 * math.pi;
      } else if (d < -math.pi) {
        d += 2 * math.pi;
      }
      setState(() => _rot += d);
    } else if (_size.width > 0 && _size.height > 0) {
      setState(() {
        _offset = Offset(
          (_offset.dx + e.delta.dx / _size.width).clamp(-1.0, 1.0),
          (_offset.dy + e.delta.dy / _size.height).clamp(-1.0, 1.0),
        );
      });
    }
    _lastAngle = angle;
  }

  void _onUp(PointerEvent e) {
    _ptrs.remove(e.pointer);
    if (_ptrs.length < 2) _pinchDist = 0;
  }

  // ── Basili tutup cevirme ──
  void _onLongPressStart(LongPressStartDetails d) {
    setState(() => _holdRotate = true);
    _lastAngle = _angleAt(d.localPosition);
  }

  void _onLongPressEnd(LongPressEndDetails d) {
    if (_holdRotate) setState(() => _holdRotate = false);
  }

  @override
  Widget build(BuildContext context) {
    final img = _img;
    final l10n = AppLocalizations.of(context);
    return AspectRatio(
      aspectRatio: widget.aspect,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: Container(
          color: Colors.black,
          child: img == null
              ? Center(child: CircularProgressIndicator(color: FastTheme.accentGold))
              : LayoutBuilder(
                  builder: (ctx, constraints) {
                    final size = Size(constraints.maxWidth, constraints.maxHeight);
                    _size = size;
                    final rotating = _rotateMode || _holdRotate;
                    return GestureDetector(
                      onLongPressStart: _onLongPressStart,
                      onLongPressEnd: _onLongPressEnd,
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          Listener(
                            behavior: HitTestBehavior.opaque,
                            onPointerDown: _onDown,
                            onPointerMove: _onMove,
                            onPointerUp: _onUp,
                            onPointerCancel: _onUp,
                            child: CustomPaint(painter: _PreviewPainter(img, _rot, _scale, _offset)),
                          ),
                          // Ipucu / dondurme gostergesi
                          Positioned(
                            left: 8,
                            top: 8,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                              decoration: BoxDecoration(
                                color: Colors.black.withValues(alpha: 0.55),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: Colors.white24),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    rotating ? Icons.rotate_right : Icons.pinch_outlined,
                                    color: rotating ? FastTheme.accentGold : Colors.white70,
                                    size: 15,
                                  ),
                                  const SizedBox(width: 6),
                                  Text(
                                    rotating
                                        ? '${(_rot * 180 / math.pi).round() % 360}°'
                                        : l10n.editorPinchHint,
                                    style: TextStyle(
                                      color: rotating ? FastTheme.accentGold : Colors.white70,
                                      fontSize: 11.5,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          // Kontroller
                          Positioned(
                            right: 8,
                            bottom: 8,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Row(
                                  children: [
                                    _roundBtn(Icons.remove, () => zoom(1 / 1.3)),
                                    const SizedBox(width: 8),
                                    _roundBtn(Icons.add, () => zoom(1.3)),
                                    const SizedBox(width: 8),
                                    _roundBtn(
                                      Icons.rotate_right,
                                      () => setState(() => _rotateMode = !_rotateMode),
                                      active: _rotateMode,
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  children: [
                                    _roundBtn(Icons.rotate_left, () => rotate(-1)),
                                    const SizedBox(width: 8),
                                    _roundBtn(Icons.rotate_right, () => rotate(1)),
                                    const SizedBox(width: 8),
                                    _roundBtn(Icons.refresh, reset),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
      ),
    );
  }

  Widget _roundBtn(IconData icon, VoidCallback onTap, {bool active = false}) => GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(9),
          decoration: BoxDecoration(
            color: active ? FastTheme.accentGold : Colors.black.withValues(alpha: 0.55),
            shape: BoxShape.circle,
            border: Border.all(color: active ? FastTheme.accentGold : Colors.white24),
          ),
          child: Icon(icon, color: active ? FastTheme.bg : Colors.white, size: 22),
        ),
      );
}

class _PreviewPainter extends CustomPainter {
  final ui.Image img;
  final double rot;
  final double scale;
  final Offset off;
  _PreviewPainter(this.img, this.rot, this.scale, this.off);

  @override
  void paint(Canvas canvas, Size size) =>
      ImageEditorState.draw(canvas, size, img, rot, scale, off);

  @override
  bool shouldRepaint(covariant _PreviewPainter old) =>
      old.img != img || old.rot != rot || old.scale != scale || old.off != off;
}
