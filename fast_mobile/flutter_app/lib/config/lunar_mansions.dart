/// Ay'ın 28 menzili (menzil) ve her biri için kısa rehber.
/// Menzil indeksi ayın mutlak boylamından (0-360) hesaplanır: 360/28 ≈ 12.857°.
class LunarMansion {
  final int index; // 0-27
  final String name;
  final String meaning;
  final String doText;
  final String avoidText;

  const LunarMansion({
    required this.index,
    required this.name,
    required this.meaning,
    required this.doText,
    required this.avoidText,
  });
}

const List<LunarMansion> lunarMansions = [
  LunarMansion(index: 0, name: 'El-Buteyn', meaning: 'Küçük karın', doText: 'Kısa yolculuklar, haberleşme, yeni başlangıçlar', avoidText: 'Büyük yatırımlar, evlilik'),
  LunarMansion(index: 1, name: 'El-Süreyya', meaning: 'Ülker (Pleiades)', doText: 'Toplumsal işler, ticaret, sanat', avoidText: 'Yalnızlık gerektiren işler'),
  LunarMansion(index: 2, name: 'El-Deberan', meaning: 'Takip eden', doText: 'Araştırma, takip, gizli işler', avoidText: 'Açık anlaşmalar'),
  LunarMansion(index: 3, name: 'El-Hak\'a', meaning: 'Beyaz benek', doText: 'Temizlik, arınma, ibadet', avoidText: 'Kirli/karmaşık işler'),
  LunarMansion(index: 4, name: 'El-Han\'a', meaning: 'İşaret', doText: 'Seyahat, eğitim, öğrenme', avoidText: 'Durağan işler'),
  LunarMansion(index: 5, name: 'Ez-Zira', meaning: 'Tohum', doText: 'Ekim, başlangıç, planlama', avoidText: 'Hasat, bitirme'),
  LunarMansion(index: 6, name: 'En-Nesra', meaning: 'Kartal', doText: 'Yüksek hedefler, liderlik', avoidText: 'Alçakgönüllülük gerektiren işler'),
  LunarMansion(index: 7, name: 'Et-Tarf', meaning: 'Göz ucu', doText: 'Gözlem, analiz, strateji', avoidText: 'Hızlı kararlar'),
  LunarMansion(index: 8, name: 'El-Cebhe', meaning: 'Alın', doText: 'Onur, tanınma, resmi işler', avoidText: 'Gizlilik'),
  LunarMansion(index: 9, name: 'Ez-Zubra', meaning: 'Aslan yelesi', doText: 'Güç, cesaret, savunma', avoidText: 'Geri çekilme'),
  LunarMansion(index: 10, name: 'Es-Serfe', meaning: 'Dönüş', doText: 'Dönüşüm, yenilenme', avoidText: 'Sabit kalma'),
  LunarMansion(index: 11, name: 'El-Avva', meaning: 'Çağrıcı', doText: 'İletişim, davet, toplantı', avoidText: 'Yalnız çalışma'),
  LunarMansion(index: 12, name: 'Es-Simak', meaning: 'Yüksek', doText: 'Yükseliş, ilerleme', avoidText: 'Alçalma, geri çekilme'),
  LunarMansion(index: 13, name: 'El-Gafr', meaning: 'Örtü', doText: 'Koruma, saklama, güvenlik', avoidText: 'Açıklama, ifşa'),
  LunarMansion(index: 14, name: 'El-Zübânâ', meaning: 'Terazi kolları', doText: 'Denge, anlaşma, hukuk', avoidText: 'Tek taraflı kararlar'),
  LunarMansion(index: 15, name: 'El-İklil', meaning: 'Taç', doText: 'Taç giyme, onurlandırma', avoidText: 'Aşağılama'),
  LunarMansion(index: 16, name: 'El-Kalb', meaning: 'Kalp', doText: 'Sevgi, bağ, aile', avoidText: 'Soğukluk, kopuş'),
  LunarMansion(index: 17, name: 'Eş-Şevle', meaning: 'Kuyruk', doText: 'Bitirme, tamamlama', avoidText: 'Başlangıç'),
  LunarMansion(index: 18, name: 'En-Na\'aim', meaning: 'Deve kuşu', doText: 'Hız, hareket, seyahat', avoidText: 'Bekleme'),
  LunarMansion(index: 19, name: 'El-Belde', meaning: 'Şehir', doText: 'Yerleşim, inşaat, yuva', avoidText: 'Yıkım'),
  LunarMansion(index: 20, name: 'Se\'d ez-Zâbih', meaning: 'Kurban eden', doText: 'Fedakarlık, yardım, sadaka', avoidText: 'Bencilik'),
  LunarMansion(index: 21, name: 'Se\'d Bula', meaning: 'Yutan', doText: 'Temizlik, arınma', avoidText: 'Biriktirme'),
  LunarMansion(index: 22, name: 'Se\'d es-Su\'ud', meaning: 'Mutluluk', doText: 'Sevinç, kutlama, nikah', avoidText: 'Yas, üzüntü'),
  LunarMansion(index: 23, name: 'Se\'d el-Ahbüye', meaning: 'Çadırlar', doText: 'Topluluk, aile, misafirperverlik', avoidText: 'Yalnızlık'),
  LunarMansion(index: 24, name: 'El-Ferg', meaning: 'Boşluk', doText: 'Boşaltma, temizlik, arınma', avoidText: 'Doldurma, başlangıç'),
  LunarMansion(index: 25, name: 'El-Fergü\'s-Sâni', meaning: 'İkinci boşluk', doText: 'Bitirme, kapanış', avoidText: 'Açılış'),
  LunarMansion(index: 26, name: 'El-Batn el-Hût', meaning: 'Balık karnı', doText: 'Derinlik, içe dönüş, meditasyon', avoidText: 'Yüzeyel işler'),
  LunarMansion(index: 27, name: 'El-Rişâ', meaning: 'Halat', doText: 'Bağlama, birleştirme, sözleşme', avoidText: 'Koparma, ayrılma'),
];

LunarMansion mansionForLongitude(double lon) {
  final idx = ((lon % 360) / (360 / 28)).floor().clamp(0, 27);
  return lunarMansions[idx];
}