"""
Ev Türetme - Derin Tablo
Formül: derived = (base + offset -1) %12 +1  (veya base+offset-2 mod 12 +1)
Kaynak: Lilly Christian Astrology, Goldstein-Jacobson, Frawley, Barclay
"""

# Kişi -> radikal evi (temel ev)
BASE_PERSON = {
    # 1. ev kendin
    "ben":1, "kendim":1, "kendimin":1,
    # 3. ev kardeş / komşu / akraba / öğrenci / kısa yol
    "kardeş":3, "kardes":3, "kardeşim":3, "kardesim":3, "kardeşimin":3, "abim":3, "ablam":3, "kardeşimle":3,
    "amca":3, "dayı":3, "dayi":3, "teyze":3, "hala":3,
    "komşu":3, "komsu":3, "komşum":3,
    "kuzen":3,
    "öğrenci":3, "ogrenci":3, "öğrencim":3, "ogrencim":3, "ogrencimin":3,
    # 4. ev anne / ev / aile / taşınmaz kökü (bazı ekollerde baba)
    "anne":4, "annem":4, "annemin":4, "anan":4, "anam":4,
    "aile":4, "ailem":4,
    # 5. ev çocuk / sevgili / flört / yaratıcılık / şans
    "çocuk":5, "cocuk":5, "çocuğum":5, "cocugum":5, "çocuğumuz":5, "oğlum":5, "oglum":5, "kızım":5, "kizim":5, "kizimin":5, "oglumun":5,
    "torun":9, # torun = çocuğun çocuğu (5'ten 5) -> 9, ama direkt 5'e de yakındır, 9'a mapliyoruz
    "sevgili":5, "sevgilim":5, "sevgilimin":5, "aşık":5, "asik":5, "aşk":5, "flört":5, "flort":5, "nişanlım":5, "nisanlim":5,
    "yaratıcılık":5,
    # 6. ev hastalık / hizmetli / çalışan / küçük hayvan
    "hasta":6, "hastam":6, "sağlık":6, "saglik":6,
    "çalışan":6, "calisan":6, "hizmetli":6, "işçi":6, "isci":6,
    "kedi":6, "kedim":6, "kedimin":6, "köpek":6, "kopek":6, "köpeğim":6, "evcil":6,
    # 7. ev eş / ortak / açık düşman / anlaşma
    "eş":7, "eşim":7, "esim":7, "eşimin":7, "kocam":7, "karım":7, "karim":7, "partnerim":7, "ortağım":7, "ortagim":7,
    "sevgili_eş":7, "nişanlı":7, "nisanli":7,
    "düşman":7, "rakip":7,
    # 8. ev ölüm / başkası parası / borç
    "ölüm":8, "olum":8, "miras":8,
    # 9. ev yüksek eğitim / guru / uzun yol / mahkeme / din
    "hoca":9, "öğretmen":9, "ogretmen":9, "profesör":9, "avukat":9, "hakim":9, "guru":9,
    "üniversite":9, "universite":9,
    # 10. ev baba / patron / kariyer / otorite
    "baba":10, "babam":10, "babamın":10, "babamin":10, "babamla":10,
    "patron":10, "müdür":10, "mudur":10, "amir":10, "şef":10, "sef":10,
    "kariyer":10, "iş":10, "is":10, "meslek":10,
    # 11. ev arkadaş / umut / büyük kardeş / topluluk
    "arkadaş":11, "arkadas":11, "arkadaşım":11, "arkadasim":11, "arkadaşımın":11, "dost":11, "dostum":11,
    "büyük kardeş":11, "abi":11,
    # 12. ev gizli düşman / hastane / hapishane / inziva
    "gizli":12, "düşman_gizli":12, "hapishane":12, "hastane":12,

    # özel: ceren gibi isimler genel 5 (öğrenci) sayılır zaten
    "ceren":5,
}

# Konu -> offset evi (base'in hangi evi)
TOPIC_OFFSET = {
    # 1 kendin
    "kendisi":1, "durumu":1, "hali":1,
    # 2 para / mal / değerli eşya
    "para":2, "parası":2, "parasi":2, "parasını":2, "maaş":2, "maas":2, "gelir":2, "kazanç":2, "mal":2, "mülk":2, "mulk":2,
    "cüzdan":2, "cuzdan":2, "altın":2, "altin":2, "takı":2, "taki":2, "değerli":2, "mücevher":2,
    "borç":2, "borcu":2,
    # 3 iletişim / kısa yol / araba / kardeş / komşu
    "araba":3, "arabası":3, "araç":3, "arac":3, "motor":3,
    "kardeş":3, "kardes":3, "komşu":3, "komsu":3,
    "iletişim":3, "iletisim":3, "haber":3, "mesaj":3, "telefon":3, "yol":3, "yolculuk_kısa":3,
    "düşünce":3, "dusunce":3, "fikri":3, "aklı":3, "akli":3, "zihni":3, "eğitim_kısa":3,
    # 4 ev / aile / arsa / temel
    "ev":4, "evi":4, "evi_nerede":4, "arsa":4, "tarla":4, "aile":4, "yuva":4, "temel":4,
    # 5 çocuk / aşk / hobi / yatırım
    "çocuk":5, "cocuk":5, "çocuğu":5, "cocugu":5, "hamile":5, "aşk":5, "ask":5, "sevgili":5, "hobi":5, "sahne":5,
    # 6 sağlık / hastalık / hizmet / evcil
    "sağlık":6, "saglik":6, "hastalık":6, "hastalik":6, "hasta":6, "kedi":6, "köpek":6, "hizmet":6,
    # 7 ilişki / evlilik / ortaklık / dava
    "ilişki":7, "iliskisi":7, "iliskim":7, "evlilik":7, "eş":7, "es":7, "ortak":7, "dava":7, "mahkeme_karşı":7,
    # 8 ölüm / miras / borç / cinsellik
    "ölüm":8, "olum":8, "miras":8, "borç_8":8, "kredi":8,
    # 9 yüksek eğitim / uzun yol / inanç / mahkeme
    "eğitim":9, "egitim":9, "üniversite":9, "yurtdışı":9, "yurtdisi":9, "uzak":9, "mahkeme":9, "inanç":9, "seyahat":9,
    # 10 kariyer / baba / otorite / statü
    "kariyer":10, "iş":10, "meslek":10, "patron":10, "baba":10, "statü":10, "ün":10,
    # 11 arkadaş / sosyal / umut
    "arkadaş":11, "arkadas":11, "sosyal":11, "umut":11, "topluluk":11,
    # 12 gizli / kayıp / hastane / hapishane
    "kayıp":12, "kayip":12, "gizli":12, "hastane":12, "hapishane":12, "inziva":12, "korku":12,

    # eşya gezegensel ipucu (horary'de 2. ev + gezegen)
    "gözlük":2, "gozluk":2, "saat":2, "telefon_eşya":2, "çanta":2, "kitap":3, "anahtar":3,
}

def derived_house(base_house, offset):
    return (base_house + offset - 2) % 12 + 1

# Yer-descriptor kelimeler (üniversite/hastane/hapishane) tek başına base olabilir ama
# yanında gerçek kişi ilişkisi varsa base YAPILMAZ - kişinin kendisini tarif ederler.
DESCRIPTOR_WORDS = ("üniversite", "universite", "hastane", "hapishane", "gizli")
# İlişki önceliği: hoca/öğretmen en özgül; arkadaş ikinci; diğer akrabalık son.
def _person_rank(word):
    if any(k in word for k in ("hoca", "öğretmen", "ogretmen", "profesör", "profesor", "hakim")):
        return 0
    if any(k in word for k in ("arkadaş", "arkadas", "dost")):
        return 1
    return 2

def parse_derived(question: str):
    q = question.lower()
    # 1) direkt kişi ilişkisi (üniversite/hastane vs. hariç)
    matched = [m for m in sorted(BASE_PERSON.items(), key=lambda x: len(x[0]), reverse=True) if m[0] in q and m[0] not in DESCRIPTOR_WORDS]
    # 2) yoksa descriptor kendisi base olur (örn. "üniversite nerede")
    if not matched:
        matched = [m for m in sorted(BASE_PERSON.items(), key=lambda x: len(x[0]), reverse=True) if m[0] in q]
    if not matched:
        return None
    base_word, base = min(matched, key=lambda m: (_person_rank(m[0]), -len(m[0])))
    # İyelik (genitive) yoksa "arkadaşım ... üniversitede hoca nerede" gibi durumlarda
    # başka ilişki kelimeleri offset/topic YAPILMAMALI (aynı kişiyi tarif ediyorlar).
    # Offset sadece "eşimin işi / arkadaşımın parası" gibi iyelikli konularda çalışır.
    _GEN_SUF = ("ınnın", "inin", "nın", "nin", "nün", "nun", "ın", "in", "un", "ün")
    possession = any(w + s in q for w in BASE_PERSON for s in _GEN_SUF)
    if not possession:
        return {"base_house": base, "base_word": base_word, "derived": base, "topic": "kişi kendisi"}
    offset = None; topic_word=""
    for word, off in sorted(TOPIC_OFFSET.items(), key=lambda x: len(x[0]), reverse=True):
        if word in q and word not in DESCRIPTOR_WORDS and word != base_word and word not in base_word and base_word not in word:
            # aynı kökse (baba/babam) atla
            offset = off; topic_word = word; break
    if not offset:
        return {"base_house":base, "base_word":base_word, "derived":base, "topic":"kişi kendisi"}
    derived = derived_house(base, offset)
    return {"base_house":base, "base_word":base_word, "offset":offset, "topic":topic_word, "derived":derived, "formula":f"{base}.evden {offset}.ev = {derived}.ev"}

def parse_multi(question: str):
    q = question.lower()
    persons = []
    for w,h in BASE_PERSON.items():
        if w in q:
            persons.append((q.index(w), w, h))
    persons = sorted(persons)
    if not persons:
        return None
    topics = []
    for w,off in TOPIC_OFFSET.items():
        if w in q:
            topics.append((q.index(w), w, off))
    topics = sorted(topics)
    base = persons[0][2]
    chain = [base]
    for _,_,off in topics:
        chain.append(off)
    house = chain[0]
    for off in chain[1:]:
        house = (house + off - 2) % 12 + 1
    return {"chain":chain, "house":house, "base_word":persons[0][1], "topics":[t[1] for t in topics]}

# Test
if __name__=="__main__":
    tests = [
        "kardeşimin parası",
        "annemin evi",
        "eşimin işi",
        "babam nerede",
        "annem nerede",
        "kızımın sevgilisi nerede",
        "oğlumun okulu",
        "arkadaşımın parası",
        "kaybolan gözlüğüm nerede",
        "eşim nerede",
        "ben neredeyim",
        "öğrencim nerede",
        "kedim nerede",
    ]
    for t in tests:
        print(t, "->", parse_derived(t), parse_multi(t))
