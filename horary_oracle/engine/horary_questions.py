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
    "mother": 4,
    "father": 10,
    "boss": 10,
    "employer": 10,
    "coworker": 6,
    "employee": 6,
    "sibling": 3,
    "uncle": 6,          # dayı/amca: annenin/babanın kardeşi -> 4/10'dan 3.ev = 6/12 (dayı 6)
    "teacher": 9,
    "hoca": 9,
    "university": 9,
    "student": 3,
    "astrology_student": 9,  # astroloji öğrencisi -> 9. ev (Yay/Jüpiter: yüksek öğrenim, felsefe, bilgelik)
    "money": 2,
    "lost_object": 2,
    "job": 10,
    "home": 4,
}

LABEL_TR = {
    "self": "Soranın kendisi", "friend": "Arkadaş", "spouse": "Eş/Partner",
    "child": "Çocuk", "mother": "Anne", "father": "Baba", "boss": "Patron/Amir",
    "coworker": "İş arkadaşı", "employee": "Çalışan", "sibling": "Kardeş",
    "uncle": "Dayı/Amca",
    "teacher": "Hoca/Öğretmen", "university": "Üniversite", "student": "Öğrenci",
    "astrology_student": "Astroloji öğrencisi",
    "money": "Para/Değerli eşya", "lost_object": "Kayıp eşya", "job": "İş",
    "home": "Ev/Ev dairesi", "partner": "Eş/Partner",
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
    "komşusu": 3, "komsusu": 3, "müşterisi": 7, "musterisi": 7, "yeğeni": 3, "yegeni": 3,
}

# Soru tipi -> anahtar kelimeler (özgülden genele)
TYPE_KEYWORDS = [
    ("teacher", ("hoca", "öğretmen", "ogretmen", "profesör", "profesor", "öğretim", "ogretim", "akademisyen", "akademik", "üniversitede", "universitede")),
    ("astrology_student", ("astroloji öğrencim", "astroloji ogrencim", "astroloji öğrencisi", "astroloji ogrencisi", "astroloji öğrenen", "astroloji ogrenen", "astroloji dersi alan", "astroloji dersi alan")),
    ("student", ("öğrencim", "ogrencim", "öğrencimin", "ogrencimin", "öğrencimle", "ogrencimle", "kayıtlı öğrenci", "ogrenci")),
    ("friend", ("arkadaşım", "arkadasim", "arkadaşının", "arkadasinin", "dostum")),
    ("spouse", ("kocam", "karım", "karim", "eşim", "esim", "nişanlım", "nisanlim", "partnerim", "sevgilim", "eşimin", "esimin")),
    ("child", ("oğlum", "oglum", "oğullarım", "ogullarim", "kızım", "kizim", "kızlarım", "kizlarim", "çocuğum", "cocugum", "çocuklarım", "cocuklarim", "bebeğim", "bebegim")),
    ("coworker", ("iş arkadaşım", "is arkadasim", "iş arkadaşı", "is arkadasi", "mesai arkadaşım", "mesai arkadasim", "çalışma arkadaşım", "calisma arkadasim")),
    ("boss", ("patronum", "müdürüm", "mudurum", "amirim", "şefim", "sefim", "yöneticim", "yoneticim")),
    ("employee", ("çalışanım", "calisanim", "elemanım", "elemanim", "personelim", "işçim", "iscim")),
    ("sibling", ("kardeşim", "kardesim", "ablam", "abim", "ağabeyim", "agabeyim", "bacım", "bacim", "kardeşimin", "kardesimin")),
    ("uncle", ("dayım", "dayimin", "dayımın", "dayi", "amcam", "amcamin", "amcamın")),
    ("mother", ("annem", "annemin", "anam", "anneciğim", "annecigim")),
    ("father", ("babam", "babamin", "babamın", "babacığım", "babacigim")),
    ("money", ("param", "maaşım", "maasim", "gelirim", "cüzdanım", "cuzdanim", "mücevherim", "mucevherim", "altınlarım", "altinlarim")),
    ("lost_object", ("bıçağım", "bicagim", "yüzüğüm", "yuzugum", "saatim", "kol saati", "evrakım", "evraklarım", "evraklarim", "gözlüğüm", "gozlugum", "anahtarım", "anahtarim", "çantam", "cantam", "telefonum", "bileziğim", "bilezigim")),
    ("job", ("işim", "isim", "mesleğim", "meslegim", "kariyerim")),
    ("home", ("evim", "evimin", "dairem", "apartmanım", "apartmanim", "sitem")),
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


def parse_nested(question):
    """"arkadaşımın eşi" → base(friend 11) içinden nested(eş 7) → turned=5.
    İyelikli İKİNCİ KİŞİ kelimesi (eşi/babası/arkadaşı...) varsa döner, yoksa None.
    """
    q = question.lower()
    nested_hit = None
    for w, h in sorted(NESTED_PERSON.items(), key=lambda x: len(x[0]), reverse=True):
        if w in _tokens(q):
            nested_hit = (w, h)
            break
    if not nested_hit:
        return None
    primary = classify_question(question)
    if not primary:
        return None
    base_h = primary["house"]
    derived = turned_house(base_h, nested_hit[1])
    return {
        "base_house": base_h, "base_word": primary["label"],
        "nested_word": nested_hit[0], "nested_house": nested_hit[1],
        "derived": derived,
        "formula": f"{base_h}. evden {nested_hit[1]}. ev = {derived}. ev",
    }