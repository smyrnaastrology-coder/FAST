import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';

/// Güneş burcu hesaplama ve sunucu-erişilebilir yardımcılar.
///
/// Burç yalnızca profil kartında gösterilir. Doğum tarihinin kendisi
/// `user_birthdates` tablosunda tutulur ve RLS ile yalnızca sahibine açıktır.
class AstroSigns {
  /// Burç adları (görünen). Ana dil TR; EN/ES çevirileri l10n ile eklenebilir.
  static const List<String> names = [
    'Oğlak', 'Kova', 'Balık', 'Koç', 'Boğa', 'İkizler',
    'Yengeç', 'Aslan', 'Başak', 'Terazi', 'Akrep', 'Yay',
  ];

  static const List<String> symbols = [
    '♑', '♒', '♓', '♈', '♉', '♊',
    '♋', '♌', '♍', '♎', '♏', '♐',
  ];

  /// Her ayın burç geçiş günü (o gün yeni burç başlar).
  /// Oca=20(Aqu), Şub=19(Pis), Mar=21(Ari), Nis=20(Tau), May=21(Gem),
  /// Haz=21(Can), Tem=23(Leo), Ağu=23(Vir), Eyl=23(Lib), Eki=23(Sco),
  /// Kas=22(Sag), Ara=22(Cap).
  static const List<int> _cutoff = [20, 19, 21, 20, 21, 21, 23, 23, 23, 23, 22, 22];

  /// Verilen gün için burç indeksini döndürür.
  /// `names`/`symbols` sırası: Oğlak, Kova, Balık, Koç, Boğa, İkizler,
  /// Yengeç, Aslan, Başak, Terazi, Akrep, Yay.
  static int _signIndex(int month, int day) {
    // Geçiş gününden önceki günler => o ayın *önceki* burcu (month-1 indeksi).
    // Geçiş günü ve sonrası => sonraki burcu (month % 12 indeksi).
    return day < _cutoff[month - 1] ? (month - 1) : (month % 12);
  }

  /// [month] 1–12, [day] 1–31 → burç adı.
  static String signName(int month, int day) => names[_signIndex(month, day)];

  /// Burç sembolü (Emoji).
  static String signSymbol(int month, int day) => symbols[_signIndex(month, day)];

  /// Mutlak ekliptik boylam (0–360) → burç indeksi (names/symbols sırası).
  /// 0° = Koç başlangıcı. names sırası Oğlak'la başladığı için +3 kaydırma.
  static int indexFromLongitude(double deg) {
    final d = deg % 360;
    final ecliptic = (d ~/ 30) % 12; // 0=Koç ... 11=Balık
    return (ecliptic + 3) % 12; // names indeksine çevir (Oğlak=0)
  }

  /// Mutlak boylam → burç adı.
  static String signNameFromLongitude(double deg) => names[indexFromLongitude(deg)];

  /// Mutlak boylam → burç sembolü.
  static String signSymbolFromLongitude(double deg) => symbols[indexFromLongitude(deg)];

  /// AstroSigns indeksini (0=Oğlak..11=Yay) aktif dile çevirir.
  static String localizedName(int index, AppLocalizations l10n) {
    final ecliptic = (index - 3 + 12) % 12;
    switch (ecliptic) {
      case 0: return l10n.chartSignAries;
      case 1: return l10n.chartSignTaurus;
      case 2: return l10n.chartSignGemini;
      case 3: return l10n.chartSignCancer;
      case 4: return l10n.chartSignLeo;
      case 5: return l10n.chartSignVirgo;
      case 6: return l10n.chartSignLibra;
      case 7: return l10n.chartSignScorpio;
      case 8: return l10n.chartSignSagittarius;
      case 9: return l10n.chartSignCapricorn;
      case 10: return l10n.chartSignAquarius;
      default: return l10n.chartSignPisces;
    }
  }

  /// Türkçeye kaydedilmiş burç adını aktif dile çevirir (bilinmiyorsa aynen).
  static String localizedNameOf(String? sign, AppLocalizations l10n) {
    if (sign == null || sign.isEmpty) return sign ?? '';
    final i = names.indexOf(sign);
    if (i < 0) return sign;
    return localizedName(i, l10n);
  }

  /// Aktif dile göre burç listesi (AstroSigns.names sırasıyla).
  static List<String> localizedNames(AppLocalizations l10n) =>
      List.generate(12, (i) => localizedName(i, l10n));

  /// 'YYYY-MM-DD' → burç adı. Geçersizse null.
  static String? fromIsoDate(String? iso) {
    if (iso == null || iso.isEmpty) return null;
    final p = iso.split('-');
    if (p.length < 3) return null;
    final m = int.tryParse(p[1]);
    final d = int.tryParse(p[2]);
    if (m == null || d == null || m < 1 || m > 12 || d < 1 || d > 31) return null;
    return signName(m, d);
  }

  /// 'YYYY-MM-DD' → burç sembolü. Geçersizse null.
  static String? symbolFromIsoDate(String? iso) {
    if (iso == null || iso.isEmpty) return null;
    final p = iso.split('-');
    if (p.length < 3) return null;
    final m = int.tryParse(p[1]);
    final d = int.tryParse(p[2]);
    if (m == null || d == null || m < 1 || m > 12 || d < 1 || d > 31) return null;
    return signSymbol(m, d);
  }

  /// '♌ Aslan' gibi rozet metni. Burç yoksa boş string.
  static String badge(String? sign) {
    if (sign == null || sign.isEmpty) return '';
    final i = names.indexOf(sign);
    return i >= 0 ? '${symbols[i]} $sign' : sign;
  }

  /// Bir kullanıcının burcunu profil kartı için hazır rozet olarak üretir.
  ///
  /// [degree] verilirse (doğum saati biliniyorsa) burç derecesi eklenir:
  /// `☉ ♎ Terazi 0.0°`. [planetSymbol] Güneş (☉) veya Ay (☽) için kullanılır.
  static Widget chip(
    String? sign, {
    Color? color,
    double? degree,
    bool degreeKnown = false,
    String planetSymbol = '☉',
    AppLocalizations? l10n,
  }) {
    if (sign == null || sign.isEmpty) return const SizedBox.shrink();
    final i = names.indexOf(sign);
    final displayName = (l10n != null && i >= 0) ? localizedName(i, l10n) : sign;
    final symbol = i >= 0 ? symbols[i] : '';
    final b = symbol.isEmpty ? displayName : '$symbol $displayName';
    final d = degreeKnown && degree != null ? ' ${degree.toStringAsFixed(1)}°' : '';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: (color ?? const Color(0xFFC9A96E)).withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text('$planetSymbol $b$d',
          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color ?? const Color(0xFFC9A96E))),
    );
  }
}
