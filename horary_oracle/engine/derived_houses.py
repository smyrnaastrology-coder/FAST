"""
Ev Türetme - 3.ev kardeş → kardeşin parası 4.ev
Formül: derived = (base + offset -1) %12 +1
"""
BASE_PERSON = {
    "kardeş":3, "kardes":3, "kardeşim":3, "kardeşimin":3,
    "anne":4, "annem":4, "annemin":4,
    "baba":10, "babam":10, "babamın":10, "babamin":10,
    "eş":7, "eşim":7, "esim":7, "eşimin":7, "kocam":7, "karım":7,
    "çocuk":5, "cocugum":5, "çocuğum":5, "oğlum":5, "kızım":5,
    "arkadaş":11, "arkadasim":11, "dost":11,
    "komşu":3, "komsu":3,
    "aşık":5, "asik":5, "sevgili":5, "sevgilim":5,
    "patron":10, "müdür":10,
    "öğrenci":5, "ogrenci":5, "öğrencim":5, "ogrencim":5, "ceren":5,
}

TOPIC_OFFSET = {
    "para":2, "parası":2, "parasi":2, "maaş":2, "maas":2,
    "ev":4, "evi":4, "araba":3, "iş":10, "is":10, "sağlık":6, "saglik":6,
    "ilişki":7, "iliskisi":7, "eş":7, "çocuk":5, "cocugu":5,
    "düşünce":3, "dusunce":3, "düşüncesi":3, "dusuncesi":3, "fikri":3, "aklı":3, "akli":3, "zihni":3, "iletişim":3, "iletisim":3,
}

def derived_house(base_house, offset):
    return (base_house + offset - 2) % 12 + 1

def parse_derived(question: str):
    q = question.lower()
    base = None; base_word=""
    for word, house in BASE_PERSON.items():
        if word in q:
            base = house; base_word = word; break
    if not base:
        return None
    offset = None; topic_word=""
    for word, off in TOPIC_OFFSET.items():
        if word in q and word != base_word:
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
    return {"chain":chain, "house":house}

# Test
if __name__=="__main__":
    print(parse_derived("kardeşimin parası"))
    print(parse_derived("annemin evi"))
    print(parse_derived("eşimin işi"))
    print(parse_multi("annemin kedisinin veterineri nerede"))
