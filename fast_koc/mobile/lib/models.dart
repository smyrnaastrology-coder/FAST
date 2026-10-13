// Fast Koç — mobil modeller (API sozlesmesi, Faz 3).
// Segment: LGS | ARA_9_10_11 | YKS_ESKI (12/mezun, eski sistem) | YKS_MAARIF.
// GET /api/segmentler donem bayragini ve secilebilir listeyi verir.
class Ogrenci {
  final int id; final String ad, rol, segment, seviye; final String sistem;
  Ogrenci({required this.id, required this.ad, required this.rol,
    required this.segment, required this.seviye, this.sistem = ''});
  factory Ogrenci.fromJson(Map<String, dynamic> j) => Ogrenci(
    id: j['id'] as int, ad: j['ad'] ?? '', rol: j['rol'] ?? 'ogrenci',
    segment: j['segment'] ?? 'YKS_ESKI', seviye: j['seviye'] ?? 'orta',
    sistem: j['sistem'] ?? '');
}

class OdevGun {
  final String gun, ders, konu; final int adet;
  OdevGun({required this.gun, required this.ders, required this.konu, required this.adet});
  factory OdevGun.fromJson(Map<String, dynamic> j) => OdevGun(
    gun: j['gun'] ?? '', ders: j['ders'] ?? '',
    konu: j['konu_baslik'] ?? '', adet: (j['adet'] ?? 0) as int);
}

class BildirimSatir {
  final int id; final String tip, kanal, metin;
  BildirimSatir({required this.id, required this.tip, required this.kanal, required this.metin});
  factory BildirimSatir.fromJson(Map<String, dynamic> j) => BildirimSatir(
    id: j['id'] as int, tip: j['tip'] ?? '', kanal: j['kanal'] ?? 'uygulama_ici',
    metin: j['metin'] ?? '');
}
