import 'dart:io';
import 'package:flutter/services.dart';
import 'package:open_file/open_file.dart';
import 'package:path_provider/path_provider.dart';

/// Sabit (kişiye özel olmayan) örnek/teaser PDF'ler.
/// Uygulamaya gömülü asset'ten açılır — fatura/üyelik gerektirmez.
class SamplePdfService {
  static const _books = {'rapor': 'iliski', 'potansiyel': 'potansiyel', 'ebeveyn': 'ebeveyn', 'natal': 'natal'};

  /// tip: rapor/potansiyel/ebeveyn/natal ; lang: tr/en/es
  static Future<bool> openSample(String tip, String lang) async {
    try {
      final book = _books[tip] ?? 'iliski';
      final lc = (lang == 'tr' || lang == 'es') ? lang : 'en';
      final asset = 'assets/samples/sample_${book}_$lc.pdf';
      final bytes = await rootBundle.load(asset);
      final dir = await getTemporaryDirectory();
      final dosya = File('${dir.path}/${asset.replaceAll('/', '_')}');
      await dosya.writeAsBytes(bytes.buffer.asUint8List(), flush: true);
      final sonuc = await OpenFile.open(dosya.path);
      return sonuc.type == ResultType.done;
    } catch (_) {
      return false;
    }
  }
}
