# -*- coding: utf-8 -*-
"""JARGON-FREE natural-language Ashtakoot explanations (EN).

Mirror of `ashtakoot_dogal_tr.py`: same 44 (koota, score) keys, same three
angles (0 promise / 1 narrative / 2 symbol), same >=3-line shape.

No Sanskrit/Jyotish term appears here; every text says what the score means
for the relationship in everyday life.
"""

from typing import Dict, List

KOOTA_BASLIK: Dict[str, str] = {
    "varna": "Values and social outlook",
    "vashya": "Mutual attraction",
    "tara": "Timing and rhythm",
    "yoni": "Inner world and intimacy",
    "graha_maitri": "Thinking and communication",
    "gana": "Character and daily life",
    "rasi": "Shared direction",
    "nadi": "Inner drive and friction",
}

ACILAR: Dict[str, List[str]] = {
    "varna": [
        "This area shows what it promises: whether you will clash over values "
        "while building a life together.",
        "This area explains: where your \"who is right\" arguments will come "
        "from in everyday life.",
        "This area symbolizes: who at the table will still feel at home.",
    ],
    "vashya": [
        "This area shows what it promises: how strong your pull toward each "
        "other really is.",
        "This area explains: where the \"something in me stirred\" feeling "
        "comes from.",
        "This area symbolizes: that quiet first moment of attraction.",
    ],
    "tara": [
        "This area shows what it promises: how often your daily rhythms "
        "overlap and when they split.",
        "This area explains: how one person going to bed late and the other "
        "waking early affects the relationship.",
        "This area symbolizes: a household where clocks run at different "
        "hours.",
    ],
    "yoni": [
        "This area shows what it promises: how easily you will read each "
        "other's inner world.",
        "This area explains: how often \"what are they feeling right now?\" "
        "will come up.",
        "This area symbolizes: how far open the door to intimacy stands.",
    ],
    "graha_maitri": [
        "This area shows what it promises: how well you can read each "
        "other's mind.",
        "This area explains: why you tell the same story differently.",
        "This area symbolizes: the ease of two people speaking the same "
        "language.",
    ],
    "gana": [
        "This area shows what it promises: how likely you are to live "
        "together without wearing each other out.",
        "This area explains: why your reactions sometimes collide at the "
        "same moment.",
        "This area symbolizes: two different rhythms settling into one home.",
    ],
    "rasi": [
        "This area shows what it promises: whether you can walk toward one "
        "shared goal.",
        "This area explains: which areas of life you move through at the "
        "same speed.",
        "This area symbolizes: two people reading the same map.",
    ],
    "nadi": [
        "This area shows what it promises: the chance that the same lack "
        "lives in both of you.",
        "This area explains: why you keep looking for the same thing in each "
        "other.",
        "This area symbolizes: two people standing at the same spot, either "
        "completing or colliding.",
    ],
}

GOVDE: Dict[str, Dict[int, str]] = {

    # ------------------------------------------------ values / social view
    "varna": {
        0: ("Your value worlds differ noticeably.\n"
            "Family, money and authority may bring different expectations.\n"
            "This need not create conflict, but it can replay the same "
            "argument over small things."),
        1: ("Your value worlds are very close.\n"
            "On family, money and responsibility you easily land in the same "
            "place.\n"
            "That agreement is the quiet, comfortable ground your daily life "
            "stands on."),
    },

    # ---------------------------------------------------------- mutual pull
    "vashya": {
        0: ("What you share is more habit than attraction.\n"
            "You know each other, but the \"something stirred when I saw "
            "them\" feeling is weak.\n"
            "This is not a defect; trust built by living together can still "
            "grow into spark."),
        1: ("The pull between you is balanced.\n"
            "Interest comes with a matching return; neither too much nor too "
            "little.\n"
            "That balance is what makes a relationship sustainable."),
        2: ("The pull is strong and mutual.\n"
            "In the moment you notice each other, both of you say yes.\n"
            "It feeds the relationship directly; even when things get hard, "
            "you gravitate back easily."),
    },

    # --------------------------------------------------------- timing / rhythm
    "tara": {
        0: ("Your daily rhythms run in opposite directions.\n"
            "One is a morning and scheduled person, the other lives closer "
            "to night and surprise.\n"
            "Different hours under one roof can matter more than cultural "
            "differences do."),
        1: ("Your daily rhythms partly overlap.\n"
            "Some stretches run exactly alike, others pull completely apart.\n"
            "That does not weaken the relationship; it only creates seasonal "
            "misfit."),
        2: ("Your daily rhythms largely overlap.\n"
            "The hours you are together look similar.\n"
            "That gives shared tasks and shared free time solid ground."),
        3: ("Your daily rhythms are nearly identical.\n"
            "If one sleeps late the other does too; if one is busy so is the "
            "other.\n"
            "This is one of the hardest fields to break and also the one that "
            "saves the most time."),
    },

    # ------------------------------------------------------------ inner world
    "yoni": {
        0: ("Your inner worlds are closed to each other.\n"
            "You struggle to guess what the other feels, and they struggle "
            "the same way about you.\n"
            "Naming feelings instead of guessing them is what shortens this "
            "distance."),
        1: ("Your inner worlds are partly open.\n"
            "You read a lot of each other, but some feelings stay hidden.\n"
            "This means the deeper layers have not opened yet, not that "
            "intimacy is zero."),
        2: ("Your inner worlds are moderately open.\n"
            "Most of the time you can read joy and sorrow in each other.\n"
            "What stays dark usually comes from unspoken past rather than "
            "from the present."),
        3: ("You read each other's inner world easily.\n"
            "Much goes understood without words; sadness often shows on the "
            "first glance.\n"
            "The flip side is expectation: if you can read them that well, "
            "you owe the same openness back."),
        4: ("Your inner worlds are nearly transparent.\n"
            "Almost everything is understood unspoken, and one person's need "
            "finds its answer on the other side.\n"
            "This level of intimacy is rare and is the strongest source of "
            "trust in the relationship."),
    },

    # --------------------------------------------------- thinking / dialogue
    "graha_maitri": {
        0: ("Your ways of thinking are nearly opposite.\n"
            "You are cooler and analytical while the other is more emotional "
            "and intuitive.\n"
            "It looks like conflict at first, but you are simply speaking "
            "different languages."),
        1: ("Your thinking mostly agrees but parts company on a few basic "
            "points.\n"
            "Daily conversation flows; deeper talks draw clear lines.\n"
            "Reading the difference as complementary rather than as an "
            "obstacle strengthens this area."),
        2: ("Your basic way of thinking matches.\n"
            "In most arguments you reach the same conclusion.\n"
            "Fine differences remain, but they are the kind you can talk "
            "through."),
        3: ("Your thinking is close and complementary.\n"
            "One misses the detail the other catches, which pays off in "
            "shared decisions.\n"
            "Understanding each other too well can also delay the honest "
            "conversation."),
        4: ("Your thinking is almost intertwined.\n"
            "You reach the same conclusion and complete each other's "
            "thoughts.\n"
            "One caution: agreeing must not become a place to hide "
            "disagreement."),
        5: ("Your thinking is at its peak.\n"
            "You understand each other before speaking; you nearly hear "
            "what the other means.\n"
            "Shared decisions and shared direction grow out of this fit."),
    },

    # ------------------------------------------------------------- character
    "gana": {
        0: ("Your characters are very different.\n"
            "One is careful and slow, the other bold and fast.\n"
            "It shows up as \"hurry up\" and \"wait a moment\" repeating "
            "over and over."),
        1: ("You differ in character but inside mutual respect.\n"
            "One may be more outward, the other more inward.\n"
            "That difference enriches daily life; trouble starts only when "
            "\"you don't do it my way\" appears."),
        2: ("Your character fit is moderate.\n"
            "You laugh at the same things but react in different ways.\n"
            "Small complaints usually resolve before they grow."),
        3: ("Your characters are close without being identical.\n"
            "You laugh at the same funny moment, though one moves faster.\n"
            "That is an easy, relaxed kind of fit."),
        4: ("Your characters agree well.\n"
            "Reactions, energy and expectations line up.\n"
            "You are efficient together, and daily pace does not wear "
            "either of you down."),
        5: ("Your characters strongly overlap.\n"
            "Reactions and expectations are near-identical.\n"
            "The flip side is that when one changes, the other is expected "
            "to change too."),
        6: ("Your characters complete each other.\n"
            "One person's energy is balanced by the other's steadiness.\n"
            "That is the strongest daily fit and it also gives you the power "
            "to do more together."),
    },

    # --------------------------------------------------------- shared direction
    "rasi": {
        0: ("You do not naturally work in the same area.\n"
            "One defines the relationship emotionally, the other through "
            "action.\n"
            "Reading different maps blurs the direction when you move "
            "forward together."),
        1: ("You move together on some ground and not on others.\n"
            "Topics with a shared goal work; scattered topics slow down.\n"
            "Choosing which one to solve first gives the relationship a "
            "clear direction."),
        2: ("Your direction partly overlaps.\n"
            "You catch the same pace on some subjects while one of you moves "
            "ahead on others.\n"
            "Small regular adjustments keep it balanced when you work "
            "together."),
        3: ("Your direction largely matches.\n"
            "You see the same reasons for something to matter.\n"
            "That is solid ground for shared decisions and long-term plans."),
        4: ("Your direction aligns.\n"
            "Priorities run through your mind in the same order.\n"
            "You end up on the same side of life's big decisions."),
        5: ("Your direction fits strongly.\n"
            "You value the same things in the same way.\n"
            "Moving together costs no effort; it actually adds energy."),
        6: ("Your direction is nearly identical.\n"
            "You understand what each other wants without being told.\n"
            "Walking toward a goal together feels effortless, as if leaning "
            "on each other."),
        7: ("Your direction matches completely.\n"
            "What one person prioritises, the other does too.\n"
            "That is rare unity in designing a shared life; you always walk "
            "the same road toward the goal."),
    },

    # ----------------------------------------------------- inner drive / friction
    "nadi": {
        0: ("Your natural inner drives complete each other.\n"
            "One fills a gap while the other fills it from a different "
            "angle.\n"
            "The relationship draws its strength from exactly that "
            "completeness."),
        1: ("Your inner drives largely overlap.\n"
            "You want the same things at different times but with the same "
            "instinct.\n"
            "That creates strong unity around shared goals."),
        2: ("Your inner drives point the same way.\n"
            "Both of you sense the same lack.\n"
            "That is a match with a high chance of completing each other."),
        3: ("Your inner drives are close.\n"
            "Similar needs produce similar reactions in you both.\n"
            "It is a fit that makes sharing easy."),
        4: ("Your inner drives mostly overlap, but the shades differ.\n"
            "You aim at the same thing in different ways.\n"
            "Moving together can produce small snags."),
        5: ("Your inner drives clash in places.\n"
            "You may want different things from the same situation.\n"
            "This is the area most worth talking about; saying it out loud, "
            "rather than hiding it, keeps it manageable."),
        6: ("Your inner drives clearly conflict.\n"
            "You feed on similar needs but pull toward different places.\n"
            "That can drain the relationship, though awareness makes it "
            "steerable."),
        7: ("Your inner drives nearly collide.\n"
            "You look for the same lack in each other and both head for the "
            "same spot.\n"
            "This is the hardest area, but it is not a clash: it is two "
            "people wanting the same thing."),
        8: ("Your inner drives are identical.\n"
            "You react to the same lack in the same way and want the same "
            "thing.\n"
            "That creates inner friction, but it does not mean the end: if "
            "you want the same thing twice, looking for it together works."),
    },
}


def dogal_metin(kod: str, puan: int, aci: int) -> str:
    """Return the jargon-free text for `kod` at `puan` from angle `aci`."""
    govde = GOVDE.get(kod, {}).get(puan)
    if govde is None:
        return ""
    return "%s\n%s" % (ACILAR.get(kod, [""] * 3)[aci % 3], govde)


def mevcut(kod: str, puan: int) -> bool:
    return puan in GOVDE.get(kod, {})


#: Total (0-36) in plain language. `cok_dusuk` = 0-17, `dusuk` = 18-24,
#: `orta` = 25-32, `yuksek` = 33-36.
TOPLAM: Dict[str, Dict[str, str]] = {
    "cok_dusuk": {
        "baslik": "A weak start",
        "aciklama": ("There is a lot to walk through and the habit of being "
                    "together is not settled yet.\n"
                    "That does not mean the door is closed; it only shows "
                    "today's fit is low.\n"
                    "What helps most is the effort to understand the other "
                    "person."),
        "ipucu": ("Small, steady steps carry a relationship further than "
                  "a dramatic beginning."),
    },
    "dusuk": {
        "baslik": "Some areas fit well",
        "aciklama": ("There are areas the relationship rests on and does "
                    "well, plus areas that still do not fit.\n"
                    "Your strong sides keep it standing; weak areas get "
                    "heavier if you never work on them together.\n"
                    "That is not bad, but it asks for deliberate work."),
        "ipucu": ("Start from the area where you are strongest; the rest "
                  "arrives over time."),
    },
    "orta": {
        "baslik": "A solid fit",
        "aciklama": ("Most long-term relationships fall in this range.\n"
                    "Daily life does not wear you down; some situations are "
                    "hard, but they do not stop you.\n"
                    "The relationship stands on firm ground and stays open "
                    "to growth."),
        "ipucu": ("A solid base does not mean it lasts unchanged; notice "
                  "what you build on it."),
    },
    "yuksek": {
        "baslik": "A strong fit",
        "aciklama": ("Your fit is close to complete.\n"
                    "You speak the same language day to day, you understand "
                    "each other and you care about the same things.\n"
                    "Such matches are rare, but a high score does not mean "
                    "the relationship lasts forever."),
        "ipucu": ("A strong fit keeps communication easy; it still does not "
                  "replace honest, deep conversation."),
    },
}


def toplam_metin(seviye: str) -> Dict[str, str]:
    return dict(TOPLAM.get(seviye, {}))
