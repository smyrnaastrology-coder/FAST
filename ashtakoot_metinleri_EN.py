# -*- coding: utf-8 -*-
"""
Standart 36 puanlı Ashtakoot yorum metinleri — English.

Yapı `ashtakoot_metinleri.py` ile birebir aynıdır; yalnızca metinler İngilizcedir.
Birliktelik çerçevesi: eşleşme (es_sevgili) ve ebeveyn-çocuk (ebeveyn_cocuk).
"""

BANTLAR = ["mukemmel", "yuksek", "orta", "dusuk", "yok"]


def bant_bul(puan: int, azami: int) -> str:
    if azami <= 0 or puan <= 0:
        return "yok"
    oran = puan / azami
    if oran >= 1.0:
        return "mukemmel"
    if oran >= 0.70:
        return "yuksek"
    if oran >= 0.45:
        return "orta"
    return "dusuk"


KOOTA_METIN: dict = {

    "varna": {
        "ad": "Varna",
        "baslik": "Varna — Caste Compatibility",
        "soru": "Do your two value systems understand each other?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Identical varna",
                "aciklama": "Both Moons fall in the same varna (Brahmin, Kshatriya, Vaishya or "
                            "Shudra), which is the maximum score of 1/1.",
                "ipucu": "In classical Jyotish, varna is not lineage but a quality measured by "
                         "which pada the Moon occupied at birth. Do not read modern social "
                         "class into it.",
            },
            "yuksek": {
                "baslik": "Adjacent varnas",
                "aciklama": "Different but neighbouring categories; most of the time the "
                            "difference is not felt.",
                "ipucu": "Shared family history or similar priorities close this gap.",
            },
            "orta": {
                "baslik": "Distant but non-conflicting",
                "aciklama": "Different varnas, with neither friction nor strong attraction.",
                "ipucu": "Long-term harmony here is built through conscious communication.",
            },
            "dusuk": {
                "baslik": "The two extremes of the scale",
                "aciklama": "The opposite ends of the varna scale, indicating that your "
                            "cultural outlooks may differ.",
                "ipucu": "Varna carries only 1 of the 36 points and should never be read alone.",
            },
            "yok": {
                "baslik": "Varna mismatch",
                "aciklama": "The Moons fall in different varnas.",
                "ipucu": "Look at the heavier kootas: Nadi, Rasi and Gana.",
            },
        },
        "mod": {
            "es_sevgili": "Shared family roots and value world, held inside mutual respect.",
            "ebeveyn_cocuk": "The channel through which family values are transmitted; the gap "
                             "shows how values pass between generations.",
        },
    },

    "vashya": {
        "ad": "Vashya",
        "baslik": "Vashya — Predator / Prey Lifestyle",
        "soru": "Do your life rhythms and your hunter-prey dynamic align?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Same vashya group (2/2)",
                "aciklama": "Your Moon signs belong to the same lifestyle category: both "
                            "predators, both prey, or both creatures of the earth.",
                "ipucu": "Vashya comes from an ancient food-habit classification: Chatura "
                         "(bird), Chatushpada (quadruped), Manushya (human), Khala "
                         "(reptile/insect).",
            },
            "yuksek": {
                "baslik": "Mediated affinity (1/2)",
                "aciklama": "The categories differ, but one Moon sign falls under the sign lord "
                            "of the other. A partial kinship.",
                "ipucu": "This score comes through mediation rather than direct similarity.",
            },
            "orta": {
                "baslik": "Neighbouring categories",
                "aciklama": "No bridge between the groups; the match is neutral.",
                "ipucu": "Shared daily habits can easily close this distance.",
            },
            "dusuk": {
                "baslik": "Weak vashya link",
                "aciklama": "The vashya categories are far apart.",
                "ipucu": "A weak score describes the rhythm of the bond, not its quality.",
            },
            "yok": {
                "baslik": "Opposed categories",
                "aciklama": "Neither direct similarity nor overlap through the sign lord.",
                "ipucu": "This is one of the strongest indicators of differing life pace.",
            },
        },
        "mod": {
            "es_sevgili": "Daily rhythm and lifestyle compatibility.",
            "ebeveyn_cocuk": "How well the child's developmental needs fit the order the parent "
                             "provides.",
        },
    },

    "tara": {
        "ad": "Tara",
        "baslik": "Tara — Fortune and Timing",
        "soru": "Does your timing match each other?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Best tara (3/3)",
                "aciklama": "In the ninefold cycle of nakshatras, the first person's position "
                            "lands on the second person's most fortunate tara.",
                "ipucu": "Tara is a ninefold measure that repeats once across nine nakshatras. "
                         "Everyone has a tara; the question is whether your two overlap.",
            },
            "yuksek": {
                "baslik": "Middle tara (1/3)",
                "aciklama": "A middle position in the cycle. Timing works most of the time but "
                            "can tighten in hard periods.",
                "ipucu": "On its own, tara represents the written share of fortune.",
            },
            "orta": {
                "baslik": "Lower tara",
                "aciklama": "The lower part of the cycle; decisions taken together may run at "
                            "different speeds.",
                "ipucu": "Deliberately matching your decision pace is enough.",
            },
            "dusuk": {
                "baslik": "Weak tara",
                "aciklama": "You sit at opposite ends of the tara cycle.",
                "ipucu": "This area demands patience and should not be rushed.",
            },
            "yok": {
                "baslik": "Lowest tara (0/3)",
                "aciklama": "The first nakshatra falls at the lowest rank of the second's cycle.",
                "ipucu": "Tara is directional: A/B and B/A can give different results.",
            },
        },
        "mod": {
            "es_sevgili": "Fortune and timing, the temporal dimension of the bond.",
            "ebeveyn_cocuk": "How well the parent's timing suits the child's needs, and when "
                             "different phases can be answered.",
        },
    },

    "yoni": {
        "ad": "Yoni",
        "baslik": "Yoni — Physical Attraction",
        "soru": "How strong is the physical and emotional pull?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Same animal, same gender (4/4)",
                "aciklama": "Both nakshatras point to the same yoni animal. Yoni is the clearest "
                            "indicator of physical attraction at 4 of 36 points.",
                "ipucu": "Gender is read from the pada number: odd padas as masculine, even "
                         "padas as feminine.",
            },
            "yuksek": {
                "baslik": "Same animal, opposite gender (3/4)",
                "aciklama": "The animal matches but the pada gender differs. Classically this "
                            "is not equal, yet it is never rejected.",
                "ipucu": "Jaimini treats the opposite-gender match as unequal but forgiven.",
            },
            "orta": {
                "baslik": "Different animals",
                "aciklama": "The two nakshatras point to different yoni animals.",
                "ipucu": "Different yoni means a different language of attraction; Gana, Graha "
                         "Maitri and Rasi carry the total.",
            },
            "dusuk": {
                "baslik": "Related but unpaired animals",
                "aciklama": "The animals are of the same family but not the same.",
                "ipucu": "Yoni alone is never sufficient.",
            },
            "yok": {
                "baslik": "Yoni mismatch (0/4)",
                "aciklama": "No shared yoni at all. Some nakshatras (boat, drum, hand, void) have "
                            "no yoni counterpart and match only themselves.",
                "ipucu": "Yastrijiyotish builds yoni from just fifteen animal pairs, which is "
                         "why its coverage is deliberately narrow.",
            },
        },
        "mod": {
            "es_sevgili": "Physical attraction and romantic inclination.",
            "ebeveyn_cocuk": "The natural closeness and protective instinct between parent and "
                             "child, and which parent's side the child settles on more easily.",
        },
    },

    "graha_maitri": {
        "ad": "Graha Maitri",
        "baslik": "Graha Maitri — Planetary Friendship",
        "soru": "Is your reading of life close to theirs?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Same sign (5/5)",
                "aciklama": "Both Moons occupy the same zodiac sign, so the sign lord is the same "
                            "planet and the basic outlook overlaps.",
                "ipucu": "The same sign means the same planet. The element (fire/earth/air/water) "
                         "is not the deciding factor here.",
            },
            "yuksek": {
                "baslik": "Lords are friends (4/5)",
                "aciklama": "Different signs whose lords stand in natural friendship.",
                "ipucu": "This is Naisargika, natural friendship, not karmic bond from past lives.",
            },
            "orta": {
                "baslik": "Lords neutral (3/5)",
                "aciklama": "Neither natural affinity nor enmity between the sign lords.",
                "ipucu": "Neutral relations work without friction in most long partnerships.",
            },
            "dusuk": {
                "baslik": "Lords are enemies (1/5)",
                "aciklama": "The sign lords are in natural enmity, so basic outlooks may differ.",
                "ipucu": "The Sun (Leo) and Saturn (Aquarius/Capricorn) are a classic enemy pair.",
            },
            "yok": {
                "baslik": "Weak friendship",
                "aciklama": "The lowest score in the directional table.",
                "ipucu": "This is the only undecided koota; it equals Vashya's 2 points.",
            },
        },
        "mod": {
            "es_sevgili": "Overlap of values, goals and life priorities.",
            "ebeveyn_cocuk": "The parent's capacity to pass on a worldview to the child.",
        },
    },

    "gana": {
        "ad": "Gana",
        "baslik": "Gana — Basic Temperament",
        "soru": "Do your temperaments complete each other?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Same gana (6/6)",
                "aciklama": "Both Moons sit in the same temperament class: Deva, Manushya or "
                            "Rakshasa.",
                "ipucu": "Gana is Jaimini's threefold classification: Deva (mature), Manushya "
                         "(balanced), Rakshasa (impulsive).",
            },
            "yuksek": {
                "baslik": "Deva with Manushya (5/6)",
                "aciklama": "Maturity and balance support each other. Classically this is a "
                            "complimentary match of mutual respect.",
                "ipucu": "Jaimini counts this among the pairs where everything is in place.",
            },
            "orta": {
                "baslik": "Weak temperament match",
                "aciklama": "The asymmetric Manushya-Rakshasa pairing. A low score, but not a "
                            "rejected combination.",
                "ipucu": "The gana table is directional; A/B and B/A can differ.",
            },
            "dusuk": {
                "baslik": "Opposed temperaments",
                "aciklama": "Deva meets Rakshasa. Classical texts read this as the sign of old "
                            "enmity (shatru).",
                "ipucu": "Six of the 36 points sit on this single item, so it strongly moves the "
                         "total.",
            },
            "yok": {
                "baslik": "Gana mismatch (0/6)",
                "aciklama": "The directional table gives no points for this ordering.",
                "ipucu": "Rakshasa with Manushya is also zero in the classical table.",
            },
        },
        "mod": {
            "es_sevgili": "Temperament fit and the limits of each other's patience.",
            "ebeveyn_cocuk": "How much the child's nature matches the parent's, and where "
                             "upbringing clashes with natural temperament.",
        },
    },

    "rasi": {
        "ad": "Rasi",
        "baslik": "Rashi — Emotional and Mental Closeness",
        "soru": "How alike are your inner worlds?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Same sign (7/7)",
                "aciklama": "The full score on the heaviest koota. Your emotional languages "
                            "coincide exactly.",
                "ipucu": "Rasi carries 7 points and is the centre of gravity of Ashtakoot; "
                         "together with Nadi it makes 15 of the total.",
            },
            "yuksek": {
                "baslik": "2nd/4th friend or 3rd/12th (5/7)",
                "aciklama": "Signs two, three or four places apart. Many traditions also count "
                            "these as highly compatible.",
                "ipucu": "Neither element nor quality (cardinal/fixed/mutable) is used here; only "
                         "sign distance counts.",
            },
            "orta": {
                "baslik": "5th or 9th (3/7)",
                "aciklama": "A middling distance. The feelings are present, the expression is not.",
                "ipucu": "This distance does not make living together hard; it asks for translation.",
            },
            "dusuk": {
                "baslik": "6th or 8th (1/7)",
                "aciklama": "Close to the opposite-sign axis. Classically a field of friction "
                            "and of transformation.",
                "ipucu": "Meeting on an axis is more transformative than mere distance.",
            },
            "yok": {
                "baslik": "Exact opposition (0/7)",
                "aciklama": "The signs sit directly opposite (1-7, 2-8, 3-9, 4-10, 5-11, 6-12). "
                            "Strong emotional mirroring, but no points.",
                "ipucu": "Every karma scheme shows maximum tension on this axis.",
            },
        },
        "mod": {
            "es_sevgili": "Emotional closeness and the language of communication.",
            "ebeveyn_cocuk": "The emotional bond and mutual understanding between parent and child.",
        },
    },

    "nadi": {
        "ad": "Nadi",
        "baslik": "Nadi — Destined Conflict",
        "soru": "Do your paths collide?",
        "bantlar": {
            "mukemmel": {
                "baslik": "Different nadi (8/8)",
                "aciklama": "The nadi matches. This is 8 of 36 and the single largest item in "
                            "Ashtakoot.",
                "ipucu": "Nadi is threefold (nadi_1, nadi_2, nadi_3). Falling into the same nadi "
                         "is read as a collision of destiny.",
            },
            "yok": {
                "baslik": "Same nadi - no points (0/8)",
                "aciklama": "Both fall in the same nadi. This is Ashtakoot's only zero-scoring "
                            "and only eight-point item.",
                "ipucu": "Compared with itself, a person always scores 0 on Nadi for a total of "
                         "28/36. Since 36 is unreachable in practice, the real ceiling is 34 and "
                         "good long-term matches live around 30-34.",
            },
        },
        "mod": {
            "es_sevgili": "Where two life lines cross. Classically the same nadi is read as a "
                          "relationship taken from a previous life.",
            "ebeveyn_cocuk": "Continuity of destiny between generations; a shared nadi makes "
                             "transmission strong but constraining.",
        },
    },
}

TOPLAM_BANTLARI = {
    "cok_dusuk": {
        "baslik": "0-17 · Low",
        "aciklama": "Low internal compatibility. This does not mean the relationship or the "
                    "parent-child bond does not exist; it only means the Moon nakshatras do not "
                    "overlap on the eight criteria.",
        "ipucu": "Look at the other layers: Nadi, Rasi and Gana carry the weight.",
    },
    "dusuk": {
        "baslik": "18-24 · Below average",
        "aciklama": "Partial compatibility. Some kootas are strong, others are weak.",
        "ipucu": "The strong kootas are what the bond naturally rests on.",
    },
    "orta": {
        "baslik": "25-32 · Good",
        "aciklama": "Healthy compatibility, the classical texts' range for a good match.",
        "ipucu": "Most long-term partnerships fall in this band.",
    },
    "yuksek": {
        "baslik": "33-36 · Very high",
        "aciklama": "A rare strong match. Results above 33 are uncommon.",
        "ipucu": "36 is not attainable in practice; the same nadi caps the total at 34.",
    },
}

KENDISI_NOTU = {
    "baslik": "Self Comparison",
    "aciklama": "This table compares a person with their own Moon nakshatra. It is the "
                "internal consistency reference and always returns 28/36.",
    "ipucu": "Varna, Vashya, Tara, Yoni, Graha Maitri, Gana and Rasi score full while Nadi "
             "scores zero, which is why the result is 28 and not 36.",
}


def metin_getir(koota: str, puan: int, azami: int) -> dict:
    k = KOOTA_METIN.get(koota)
    if not k:
        return {"baslik": koota, "aciklama": "", "ipucu": ""}
    bant = bant_bul(puan, azami)
    m = k["bantlar"].get(bant)
    if m is None:
        sira = BANTLAR.index(bant)
        for adim in range(1, len(BANTLAR)):
            for hedef in (sira - adim, sira + adim):
                if 0 <= hedef < len(BANTLAR):
                    m = k["bantlar"].get(BANTLAR[hedef])
                    if m:
                        return dict(m, _bant=bant)
        return {"baslik": koota, "aciklama": "", "ipucu": ""}
    return dict(m, _bant=bant)


def mod_yorumu(koota: str, mod: str) -> str:
    k = KOOTA_METIN.get(koota)
    if not k:
        return ""
    return k.get("mod", {}).get(mod, "")


def toplam_metni(seviye: str) -> dict:
    return TOPLAM_BANTLARI.get(seviye, {"baslik": seviye, "aciklama": "", "ipucu": ""})


def tum_metinler(lang: str = "en") -> dict:
    return KOOTA_METIN
