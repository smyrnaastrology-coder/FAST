// Depolama optimizasyonu doğrulaması: 1080px PNG -> JPEG (q85) boyut farkı.
import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/painting.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img_lib;

Future<Uint8List> toJpg(ui.Image img, int quality) async {
  final w = img.width, h = img.height;
  final rgba = await img.toByteData(format: ui.ImageByteFormat.rawRgba);
  final pixels = rgba!.buffer.asUint8List(rgba.offsetInBytes, rgba.lengthInBytes);
  final decoded = img_lib.Image.fromBytes(
    width: w,
    height: h,
    bytes: pixels.buffer,
    order: img_lib.ChannelOrder.rgba,
  );
  return img_lib.encodeJpg(decoded, quality: quality);
}

void main() {
  for (final path in ['assets/holavon_logo.png', '../../kapak.png']) {
    test('PNG -> JPEG boyut kazanci: $path', () async {
      final file = File(path);
      if (!file.existsSync()) return;
      final bytes = file.readAsBytesSync();
      final codec = await ui.instantiateImageCodec(bytes);
      final frame = await codec.getNextFrame();
      final src = frame.image;

    // 1080px'e küçült (post çıktısı).
    const outW = 1080;
    final outH = 1080;
    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder, Rect.fromLTWH(0, 0, outW.toDouble(), outH.toDouble()));
    canvas.drawImageRect(
      src,
      Rect.fromLTWH(0, 0, src.width.toDouble(), src.height.toDouble()),
      Rect.fromLTWH(0, 0, outW.toDouble(), outH.toDouble()),
      Paint(),
    );
    final pic = recorder.endRecording();
    final rendered = await pic.toImage(outW, outH);

    final png = await rendered.toByteData(format: ui.ImageByteFormat.png);
    final jpg = await toJpg(rendered, 85);

    final pngKb = png!.lengthInBytes / 1024;
    final jpgKb = jpg.lengthInBytes / 1024;
    // ignore: avoid_print
    print('kaynak : ${(bytes.length / 1024).toStringAsFixed(0)} KB '
        '(${src.width}x${src.height})');
    // ignore: avoid_print
    print('1080 PNG: ${pngKb.toStringAsFixed(0)} KB');
    // ignore: avoid_print
    print('1080 JPG: ${jpgKb.toStringAsFixed(0)} KB (q85)');
    // ignore: avoid_print
    print('kazanc  : ${(pngKb / jpgKb).toStringAsFixed(1)}x kuculdu');

      expect(jpg.lengthInBytes, lessThan(png.lengthInBytes));
      expect(jpgKb, lessThan(400));
    });
  }
}
