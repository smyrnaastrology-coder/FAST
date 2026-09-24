# -*- coding: utf-8 -*-
"""Soru tipi -> ev eşlemesi + turned-house motoru (maytap: "arkadaşımın eşi").

QUESTION_HOUSES, mentörün tanımladığı soru-tipi kayıtıdır (ekol bazlı).
NOT: anne/baba haritası sisteme göre korunuyor (anne=4, baba=10, derin tablo ile
uyumlu). Mentör önerisi (anne=10, baba=4) kasıtlı değil çünkü mevcut
parse_derived / horary_rules ile çelişir; bu ayrım kullanıcıya bildirildi.
"""
import re

QUESTION_HOUSES = {
    "self": 1,
    "friend": 11,
    "friend_of_friend": 3,
    "partner": 7,
    "spouse": 7,
    "child": 5,
    "pregnancy": 5,   # hamilelik/gebelik -> çocuk evi 5
    "intimacy": 8,   # cinsel ilişki/birliktelik -> 8. ev (cinsellik)
    "mother": 4,
    "father": 10,
    "boss": 10,
    "employer": 10,
    "coworker": 6,
    "employee": 6,
    "sibling": 3,
    "uncle": 6,          # dayı/amca: annenin/babanın kardeşi -> 4/10'dan 3.ev = 6/12 (dayı 6)
    "court": 9,       # mahkeme/dava/hakim/yargıç
    "teacher": 9,
    "hoca": 9,
    "university": 9,
    "student": 3,
    "astrology_student": 9,  # astroloji öğrencisi -> 9. ev (Yay/Jüpiter: yüksek öğrenim, felsefe, bilgelik)
    "money": 2,
    "loan": 8,        # bankadan borç/kredi/ipotek (başkasının parası) -> 8. ev
    "lost_object": 2,
    "job": 10,
    "home": 4,
    "hidden_enemy": 12,  # şikayet eden / gizli düşman
    "sport_fav": 5,      # tuttuğun takım (oyun/spor) -> 5.ev; rakip onun 5.'si -> 11.ev (turned)
    "sport_rival": 11,
    "investment": 5,   # hisse senedi/borsa/yatırım (spekülasyon) -> 5.ev; kâr 2. evden görülür
}

LABEL_TR = {
    "self": "Soranın kendisi", "friend": "Arkadaş", "spouse": "Eş/Partner",
    "child": "Çocuk", "pregnancy": "Hamilelik (5. ev)", "intimacy": "Cinsel ilişki (8. ev)", "mother": "Anne", "father": "Baba", "boss": "Patron/Amir",
    "coworker": "İş arkadaşı", "employee": "Çalışan", "sibling": "Kardeş",
    "uncle": "Dayı/Amca",
    "teacher": "Hoca/Öğretmen", "university": "Üniversite", "student": "Öğrenci",
    "astrology_student": "Astroloji öğrencisi",
    "money": "Para/Değerli eşya", "loan": "Kredi/Borç/İpotek (8. ev)", "lost_object": "Kayıp eşya", "job": "İş",
    "home": "Ev/Ev dairesi", "hidden_enemy": "Gizli düşman / şikayet eden", "partner": "Eş/Partner",
    "sport_fav": "Tuttuğun takım (5.ev spor)", "sport_rival": "Rakip takım (11.ev)",
    "investment": "Hisse senedi/yatırım (5. ev spekülasyon)",
    "court": "Mahkeme/Dava (9. ev)",
}

# Nesne iyelikli ikinci kişi: "arkadaşımın EŞI" -> turned(base, nested)
NESTED_PERSON = {
    "eşi": 7, "eşinin": 7, "es i": 7, "esi": 7, "kocası": 7, "kocasi": 7, "karısı": 7, "karisi": 7,
    "sevgilisi": 5, "nişanlısı": 7, "nisanlisi": 7, "nişanlisi": 7,
    "babası": 10, "babasi": 10, "annesi": 4,
    "oğlu": 5, "oglu": 5, "kızı": 5, "kizi": 5, "çocuğu": 5, "cocugu": 5,
    "hocası": 9, "hocasi": 9, "öğrencisi": 3, "ogrencisi": 3, "öğretmeni": 9, "ogretmeni": 9,
    "patronu": 10, "müdürü": 10, "muduru": 10, "müdürü": 10,
    "arkadaşı": 11, "arkadasi": 11, "dostu": 11, "kardeşi": 3, "kardesi": 3,
    "abisi": 3, "ablası": 3, "ablasi": 3, "ağabeyi": 3, "agabeyi": 3,
    "komşusu": 3, "komsusu": 3, "müşterisi": 7, "musterisi": 7, "yeğeni": 3, "yegeni": 3,
}

# Soru tipi -> anahtar kelimeler (özgülden genele)
TYPE_KEYWORDS = [
    ("teacher", ("hoca", "öğretmen", "ogretmen", "profesör", "profesor", "öğretim", "ogretim", "akademisyen", "akademik", "üniversitede", "universitede")),
    ("court", ("mahkeme", "mahkemeye", "mahkemede", "mahkemenin", "hakim karar", "karar verecek", "karar verecek mi", "yargıç", "yargic", "dava açacak", "dava acacak", "dava açtım", "dava actim", "gözetim şartı", "gozetim sarti", "velayet")),
    ("astrology_student", ("astroloji öğrencim", "astroloji ogrencim", "astroloji öğrencisi", "astroloji ogrencisi", "astroloji öğrenen", "astroloji ogrenen", "astroloji dersi alan", "astroloji dersi alan")),
    ("student", ("öğrencim", "ogrencim", "öğrencimin", "ogrencimin", "öğrencimle", "ogrencimle", "kayıtlı öğrenci", "ogrenci")),
    ("coworker", ("iş arkadaşım", "is arkadasim", "iş arkadaşı", "is arkadasi", "mesai arkadaşım", "mesai arkadasim", "çalışma arkadaşım", "calisma arkadasim")),
    ("friend", ("arkadaşım", "arkadasim", "arkadaşının", "arkadasinin", "dostum")),
    ("sibling", ("kardeşim", "kardesim", "erkek kardeşim", "erkek kardesim", "ablam", "abim", "ağabeyim", "agabeyim", "bacım", "bacim", "kardeşimin", "kardesimin")),
    ("sport_fav", ("beşiktaş kazanacak", "besiktas kazanacak", "galatasaray kazanacak", "fenerbahçe kazanacak", "fenerbahce kazanacak", "trabzon kazanacak", "diyarbakırspor", "diyarbakirspor", "tuttuğum takım kazanacak", "tuttugum takim kazanacak", "takımım kazanacak", "takimim kazanacak", "maçı kazanacak", "maci kazanacak", "maçı kim kazanacak", "maci kim kazanacak", "kim kazanır", "kim kazanacak", "kazanacak mıyız", "kazanacak miyiz", "kazanır mıyız", "kazanir miyiz", "kazanacak mı", "kazanacak mi", "bizim takım", "bizim takim", "takımımız", "takimimiz")),
    ("investment", ("hisse senedi", "hisse senedi almalı", "hisse senedi almali", "hisse", "borsa", "borsaya", "borsadan", "yatırım yapmalı", "yatirim yapmali", "yatırım yapmalıyım", "yatirim yapmaliyim", "para yatırmalı", "para yatirmali", "sermaye koymalı", "sermaye koymali")),
    ("spouse", ("kocam", "karım", "karim", "eşim", "esim", "nişanlım", "nisanlim", "partnerim", "sevgilim", "eşimin", "esimin")),
    ("child", ("oğlum", "oglum", "oğullarım", "ogullarim", "kızım", "kizim", "kızlarım", "kizlarim", "çocuğum", "cocugum", "çocuklarım", "cocuklarim", "bebeğim", "bebegim")),
    ("pregnancy", ("hamile miyim", "hamile miyim", "hamile mi", "hamilemiyim", "gebe miyim", "gebe mi", "hamile olduğumu", "hamile oldugumu", "hamilelik", "hamile kalacak", "hamile kalacağım", "hamile kalacagim", "çocuğum mu olacak", "cocugum mu olacak", "bebeğim mi var", "bebegim mi var", "doğum yapacak", "dogum yapacak", "doğum yapacağım", "dogum yapacagim", "doğumu ne zaman", "dogumu ne zaman", "doğuracağım", "doguracagim")),
    ("intimacy", ("cinsel ilişki", "cinsel iliski", "cinsel beraberlik", "cinsel birliktelik", "seks yapmalı", "seks yapmali", "seks ilişkisi", "seks iliskisi", "yatakta beraber", "cinsel hayat")),
    ("boss", ("patronum", "müdürüm", "mudurum", "amirim", "şefim", "sefim", "yöneticim", "yoneticim")),
    ("employee", ("çalışanım", "calisanim", "elemanım", "elemanim", "personelim", "işçim", "iscim")),
    ("uncle", ("dayım", "dayimin", "dayımın", "dayi", "amcam", "amcamin", "amcamın")),
    ("mother", ("annem", "annemin", "anam", "anneciğim", "annecigim")),
    ("father", ("babam", "babamin", "babamın", "babacığım", "babacigim")),
    ("money", ("param", "maaşım", "maasim", "gelirim", "cüzdanım", "cuzdanim", "mücevherim", "mucevherim", "altınlarım", "altinlarim")),
    ("loan", ("kredi", "krediyi", "kredim", "bankadan borç", "bankadan borc", "ipotek", "mortgage", "borç para", "borc para", "borçlanmalı", "borclanmali", "borçlanarak", "borclanarak", "borçlanacağım", "borclanacagim", "borçlanıp", "borclanip", "borç çekecek", "borc cekecek", "borç alacağım", "borc alacagim", "faizle borç", "faizle borc")),
    ("lost_object", ("kalemim", "kalem", "bıçağım", "bicagim", "yüzüğüm", "yuzugum", "saatim", "kol saati", "evrakım", "evraklarım", "evraklarim", "gözlüğüm", "gozlugum", "anahtarım", "anahtarim", "çantam", "cantam", "telefonum", "bileziğim", "bilezigim")),
    ("job", ("işim", "isim", "mesleğim", "meslegim", "kariyerim")),
    ("home", ("evim", "evimin", "dairem", "apartmanım", "apartmanim", "sitem")),
    ("hidden_enemy", ("şikayet eden", "sikayet eden", "şikayetçi", "sikayetci", "ispiyonlayan", "gizli düşman", "gizli dusman")),
    ("university", ("üniversitem", "universitem", "okulum", "fakültem", "fakultem")),
    ("self", ("neredeyim", "nerdeyim", "ben nerede", "ben nerde")),
]

NESTED_WORDS = tuple(NESTED_PERSON.keys())


def turned_house(base_house, relative_house):
    """Bir kişinin kendi evinden itibaren başka bir kişi/konunun evi.
    Örn: arkadaş(11) -> eş(7): turned_house(11,7)=5
    """
    return ((base_house - 1) + (relative_house - 1)) % 12 + 1


def _tokens(q):
    return set(w for w in re.findall(r"[\w]+", q.lower()) if w)


def _strip_nested(q):
    """Nesne iyelikli ikinci-kişi kelimelerini metinden çıkar (ana ilişki ayrışsın).
    "arkadaşımın eşi nerede?" -> "arkadaşımın  nerede?" (eşi nested, arkadaş ana)
    """
    for tok in _tokens(q):
        if tok in NESTED_WORDS:
            q = q.replace(tok, " ")
    return q


def classify_question(question):
    """Soru tipini tahmin et. → {"type","house","label"} (eşleşme yoksa None).
    Nested (iyelikli ikinci kişi) kelimesi ana tipi kirletmeden tespit edilir.
    """
    q = _strip_nested(question.lower())
    for t, kws in TYPE_KEYWORDS:
        for kw in kws:
            if kw in q:
                house = QUESTION_HOUSES.get(t)
                if house is not None:
                    return {"type": t, "house": house, "label": LABEL_TR.get(t, t)}
    return None


_GEN_3RD = ("nın", "nin", "nun", "nün", "ının", "inin", "ınnın", "innin", "ın", "in", "un", "ün")


def _nested_tokens_ordered(q):
    """Metindeki nested (iyelikli ikinci-kişi) KELİMElerini konum sırasına göre (word, house).
    Tam-token eşleşmesi + üçüncü-kişi genitive eki sıyırma:
    'abisinin'->'abisi', 'kızının'->'kızı'; ama 'arkadaşımın'->'arkadaşım' (NESTED'de yok, 'arkadaşı' DEĞİL).
    """
    hits = []
    low = q.lower()
    seen = set()
    for m in re.finditer(r"[\w]+", low):
        tok = m.group(0)
        w = None; h = None
        if tok in NESTED_PERSON:
            w, h = tok, NESTED_PERSON[tok]
        else:
            for suf in _GEN_3RD:
                if tok.endswith(suf):
                    root = tok[: -len(suf)]
                    if root in NESTED_PERSON:
                        w, h = root, NESTED_PERSON[root]
                        break
        if w and (m.start(), w) not in seen:
            seen.add((m.start(), w))
            hits.append((m.start(), w, h))
    hits.sort(key=lambda x: x[0])
    return [(w, h) for _, w, h in hits]


def parse_nested(question):
    """"arkadaşımın eşi" → base(friend 11) içinden nested(eş 7) → turned=5.
    Zincirsel (çok katmanlı): "iş arkadaşımın abisinin kızı" → 6 →(abi 3)→ 8 →(kız 5)→ 12.
    İyelikli İKİNCİ KİŞİ kelimesi (eşi/babası/arkadaşı...) varsa döner, yoksa None.
    """
    q = question.lower()
    nested = _nested_tokens_ordered(q)
    if not nested:
        return None
    primary = classify_question(question)
    if not primary:
        return None
    base_h = primary["house"]
    derived = base_h
    steps = []
    for w, h in nested:
        nxt = turned_house(derived, h)
        steps.append((w, h, derived, nxt))
        derived = nxt
    # formül: ilk halkanın başlangıcı base_h; her adım "X. evden h. ev = nxt. ev"
    fparts = [f"{s[2]}. evden {s[1]}. ev = {s[3]}. ev" for s in steps]
    last_w = steps[-1][0]; last_h = steps[-1][1]
    return {
        "base_house": base_h, "base_word": primary["label"],
        "nested_word": last_w, "nested_house": last_h,
        "nested_chain": [(w, h) for w, h in nested],
        "derived": derived,
        "formula": "; ".join(fparts),
    }