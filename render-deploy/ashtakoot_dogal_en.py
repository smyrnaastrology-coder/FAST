# -*- coding: utf-8 -*-
"""JARGON-FREE natural-language Ashtakoot explanations (EN).

Mirror of `ashtakoot_dogal_tr.py`: same 44 (koota, score) keys, same three
angles (0 promise / 1 narrative / 2 symbol), same >=3-line shape.

No Sanskrit/Jyotish term appears here; every text says what the score means
for the relationship in everyday life.
"""

import random
from typing import Dict, List, Optional

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
        "This area explains: whether your \"who is right\" arguments will come "
        "up in everyday life.",
        "This area symbolizes: whether the things you both call important "
        "actually line up.",
        "This area flags: how each of you reacts to what you gain and lose.",
    ],
    "vashya": [
        "This area shows what it promises: how strong your pull toward each "
        "other really is.",
        "This area explains: where the \"something in me stirred\" feeling "
        "comes from.",
        "This area symbolizes: that quiet first moment of attraction.",
        "This area flags: treating the pull as the only thing holding the relationship up.",
    ],
    "tara": [
        "This area shows what it promises: how often your daily rhythms "
        "overlap and when they split.",
        "This area explains: how one person going to bed late and the other "
        "waking early affects the relationship.",
        "This area symbolizes: a household where clocks run at different "
        "hours.",
        "This area flags: a running clock tally under one roof, kept without anyone meaning to.",
    ],
    "yoni": [
        "This area shows what it promises: how easily you will read each "
        "other's inner world.",
        "This area explains: how often \"what are they feeling right now?\" "
        "will come up.",
        "This area symbolizes: how far open the door to intimacy stands.",
        "This area flags: quiet mistakes you make while believing you understood everything.",
    ],
    "graha_maitri": [
        "This area shows what it promises: how well you can read each "
        "other's mind.",
        "This area explains: why you tell the same story differently.",
        "This area symbolizes: the ease of two people speaking the same "
        "language.",
        "This area flags: going quiet just because you already agree.",
    ],
    "gana": [
        "This area shows what it promises: how likely you are to live "
        "together without wearing each other out.",
        "This area explains: why your reactions sometimes collide at the "
        "same moment.",
        "This area symbolizes: two different rhythms settling into one home.",
        "This area flags: repeating \"that is not how I do it\" word for "
        "word.",
    ],
    "rasi": [
        "This area shows what it promises: whether you can walk toward one "
        "shared goal.",
        "This area explains: which areas of life you move through at the "
        "same speed.",
        "This area symbolizes: two people reading the same map.",
        "This area flags: walking toward one shared goal for entirely different reasons.",
    ],
    "nadi": [
        "This area shows what it promises: the chance that the same lack "
        "lives in both of you.",
        "This area explains: why you keep looking for the same thing in each "
        "other.",
        "This area symbolizes: two people standing at the same spot, either "
        "completing or colliding.",
        "This area flags: looking twice for the same missing thing and still leaving empty handed.",
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



#: Her (koota, puan) için ikinci gövde varyantı. `GOVDE` genel düzeyi
#: tanımlayıp sonucu söyler; buradaki metin somut günlük sahneyi kurar.
#: Çağıran taraf iki varyant arasından rastgele seçer.
GOVDE_ALT: Dict[str, Dict[int, str]] = {

    # ------------------------------------------------------- values / social view
    "varna": {
        0: ("You handle money in opposite ways.\n"
            "One keeps a running total, the other spends for the moment.\n"
            "Managing one budget, you two follow different rules."),
        1: ("The days you consider important are the same days.\n"
            "Both of you find a reason to mark an ordinary day together.\n"
            "Small matches like this hold a relationship up unnoticed."),
    },

    # ------------------------------------------------------------- mutual pull
    "vashya": {
        0: ("You show interest in different ways.\n"
            "One invites you over, the other calls for a long time.\n"
            "One says \"I want to see you\", the other \"I missed you\"; both "
            "come through the same door."),
        1: ("There is a balance between closeness and freedom.\n"
            "When one moves closer, the other gives a little space; that is "
            "breathing, not cooling off.\n"
            "The closer you get, the easier it becomes to find that distance "
            "again."),
        2: ("After time apart, one of you reaches out first.\n"
            "A short gap does not end the interest, it makes the reunion "
            "clearer.\n"
            "This is what keeps the relationship standing."),
    },

    # --------------------------------------------------------------- time / rhythm
    "tara": {
        0: ("Your weekends are built differently.\n"
            "One starts early, the other gets going in the evening.\n"
            "It takes about two weeks to work out what time you can actually "
            "meet."),
        1: ("Some of your days overlap too.\n"
            "Some weeks you wake at the same hour, some weeks you never meet.\n"
            "Picking the good days is worth more than worrying about the "
            "mismatched ones."),
        2: ("Your days start at similar hours.\n"
            "Leaving for work, sitting down to eat, going to sleep: all close "
            "together.\n"
            "Falling into the same rhythm makes shared tasks easy."),
        3: ("You get tired at the same hour.\n"
            "Your free hours happen to land at the same time.\n"
            "This is the easiest version of sharing a tired day."),
    },

    # ------------------------------------------------------------- inner world
    "yoni": {
        0: ("You both expect to be understood without talking.\n"
            "You read each other's state without asking.\n"
            "When the guess is wrong, the other goes quiet thinking \"you "
            "weren't listening\"."),
        1: ("A few subjects are still off limits.\n"
            "Halfway through a conversation, both of you pull back.\n"
            "Opening that subject without naming it wears less on you than "
            "keeping it shut."),
        2: ("You read the mood before it shows.\n"
            "A good day is audible, a hard one shows in posture.\n"
            "That reading turns into attention you never had to ask for."),
        3: ("You show you listened even when you did not agree.\n"
            "The other person gathers themselves once before speaking.\n"
            "Waiting is worth more here than asking."),
        4: ("There is very little left unshared.\n"
            "Knowing what the other thinks without asking is rare.\n"
            "That much openness makes joint decisions easier too."),
    },

    # ------------------------------------------------------- mind / communication
    "graha_maitri": {
        0: ("You name feelings in different words.\n"
            "One says \"I'm sad\" where the other says \"I'm tired\".\n"
            "Living the same moment under different names invites "
            "misunderstanding."),
        1: ("Most arguments start at the wrong hour.\n"
            "One is in a hurry, the other is ready to listen.\n"
            "The same thought, said at a better moment, lands differently."),
        2: ("You often finish each other's sentences.\n"
            "One of you struggles for a word and the other has it almost at "
            "once.\n"
            "That saves real time when a decision has to be made."),
        3: ("You reach the same conclusion by different routes.\n"
            "One decides first, the other a moment later.\n"
            "Different paths, same destination: the argument stays short."),
        4: ("You understand each other without talking.\n"
            "When one goes quiet, the other knows why.\n"
            "The only thing left unsaid may be the one thing that matters."),
        5: ("You decide at nearly the same moment.\n"
            "When one says \"this one\", the other is already there.\n"
            "Even hard decisions get made without a debate."),
    },

    # -------------------------------------------------------------- character
    "gana": {
        0: ("You decide in about two seconds.\n"
            "One answers before thinking, the other lists three options.\n"
            "Speed against caution shows up in every small choice."),
        1: ("Neither of you expects the other to be like you.\n"
            "You are not owed an explanation for being different.\n"
            "That expectation being absent keeps the difference harmless."),
        2: ("You laugh at almost the same things.\n"
            "The same funny moment lands on both of you at once.\n"
            "Small complaints close quickly through shared humour."),
        3: ("You keep up with daily life together.\n"
            "When one runs out of energy, the other takes half the load.\n"
            "That is support given without a word."),
        4: ("Your tastes and appetites line up.\n"
            "Same food, same programme, same evening.\n"
            "Everyday things you do together multiply."),
        5: ("One person's mood moves the other almost instantly.\n"
            "When you get angry, you get angry at the same time.\n"
            "For a relationship, getting angry together and calming down "
            "together is ideal."),
        6: ("You take turns without keeping score.\n"
            "One steps forward, the other steps back, then you swap.\n"
            "That kind of sharing keeps neither of you permanently second."),
    },

    # --------------------------------------------------------- shared direction
    "rasi": {
        0: ("You are not reading the same map.\n"
            "One points at the short term, the other at the long plan.\n"
            "When the direction changes, someone has to ask where the road "
            "leads again."),
        1: ("There is one direction you already agree on.\n"
            "In that area you reach the same decision without arguing.\n"
            "It is ground that never has to be reopened."),
        2: ("One of you slows down and the other waits.\n"
            "One hurries, the other slows to be sure.\n"
            "Sometimes the one waiting has to speed up too."),
        3: ("You call the same things important for the same reason.\n"
            "Both of you are fed by similar experience.\n"
            "That shared reason keeps a long plan on paper."),
        4: ("Your priorities back each other up.\n"
            "When one says \"this first\", the other says \"yes\".\n"
            "That agreement is what decides how fast you move."),
        5: ("You reach the same place by different routes.\n"
            "Same destination, different road.\n"
            "When one of you steps off the road, the other has to find a new "
            "one."),
        6: ("You understand the plan without explaining it.\n"
            "There is no need to discuss it, because tomorrow is already "
            "clear.\n"
            "A plan like that would hold with a third person too."),
        7: ("You decide together rather than separately.\n"
            "You set your own preference aside and ask for theirs first.\n"
            "That makes the hardest part of designing a shared life easier."),
    },

    # ----------------------------------------------------- inner drive / friction
    "nadi": {
        0: ("You close the same gap in two different ways.\n"
            "One forgets, the other works at it.\n"
            "Same emptiness, different method."),
        1: ("You want the same thing at the same time.\n"
            "When one starts craving it, so does the other.\n"
            "Either of you can explain why."),
        2: ("You are not looking at the same spot.\n"
            "Both of you fall into the same mistake without seeing it.\n"
            "One closes the blind spot the other has."),
        3: ("Its absence bothers you both at once.\n"
            "You stir when the other is doing well.\n"
            "That keeps either of you from being alone in it."),
        4: ("Same goal, different route.\n"
            "One hurries, the other waits their turn.\n"
            "Whoever waits ends up slowing the one who rushed."),
        5: ("Two opposite wants about the same thing.\n"
            "One wants more togetherness, the other wants more room.\n"
            "Talking about it tires you both quickly."),
        6: ("You arrive at the same place twice.\n"
            "One looks, the other cannot find it, then you swap.\n"
            "You notice the loop before you can break it."),
        7: ("One person's unease finds its exact match in the other.\n"
            "Neither settles until the other does.\n"
            "You cannot begin the conversation until you calm down together."),
        8: ("You take the same lesson twice.\n"
            "When one breaks, the other breaks too.\n"
            "The second round is shorter than the first."),
    },
}


#: Four angles: 0 promise, 1 explains, 2 symbolizes, 3 flags.
ACI_SAYISI = 4


def govde_varyantlari(kod: str, puan: int) -> List[str]:
    """All body variants available for `kod`/`puan`.

    `GOVDE` is always the first variant; `GOVDE_ALT` adds the second when
    present, so kootas with a single body keep working unchanged.
    """
    ilk = GOVDE.get(kod, {}).get(puan)
    if ilk is None:
        return []
    liste = [ilk]
    ikinci = GOVDE_ALT.get(kod, {}).get(puan)
    if ikinci is not None:
        liste.append(ikinci)
    return liste


def dogal_metin(kod: str, puan: int, aci: int,
                govde_index: Optional[int] = None) -> str:
    """Jargon-free text for `kod` at `puan` from angle `aci`.

    `aci`: 0 promise, 1 explains, 2 symbolizes, 3 flags.
    `govde_index`: body variant; `None` picks one at random. With four
    angles and two bodies, one score yields eight possible texts.
    """
    if GOVDE.get(kod, {}).get(puan) is None:
        return ""
    if govde_index is None:
        govde_index = random.randrange(len(govde_varyantlari(kod, puan)))
    return "%s\n%s" % (ACILAR.get(kod, [""] * ACI_SAYISI)[aci % ACI_SAYISI],
                       govde_varyantlari(kod, puan)[govde_index])


def mevcut(kod: str, puan: int) -> bool:
    return puan in GOVDE.get(kod, {})


#: Overall reading for the total score, in plain language.
#: The maximum is 36, but reachable totals only span 20-34, so the bands
#: follow the measured range: `cok_dusuk` = 20-23 (Weak relationship),
#: `dusuk` = 26-27 (Average), `orta` = 28-29 (Ideal),
#: `yuksek` = 33-34 (Strong).
TOPLAM: Dict[str, Dict[str, str]] = {
    "cok_dusuk": {
        "baslik": "Weak relationship",
        "aciklama": ("20-23 range. There is a lot to walk through and the habit "
                    "of being together is not settled yet.\n"
                    "That does not mean the door is closed; it only shows "
                    "today's fit is low.\n"
                    "What helps most is the effort to understand the other "
                    "person."),
        "ipucu": ("Small, steady steps carry a relationship further than "
                  "a dramatic beginning."),
    },
    "dusuk": {
        "baslik": "Average relationship",
        "aciklama": ("26-27 range. There are areas the relationship rests on "
                    "and does well, plus areas that still do not fit.\n"
                    "Your strong sides keep it standing; weak areas get "
                    "heavier if you never work on them together.\n"
                    "That is not bad, but it asks for deliberate work."),
        "ipucu": ("Start from the area where you are strongest; the rest "
                  "arrives over time."),
    },
    "orta": {
        "baslik": "Ideal relationship",
        "aciklama": ("28-29 range. Daily life does not wear you down, and most "
                    "of what you build together settles in.\n"
                    "Some situations are hard, but they do not stop you; on "
                    "top of that you both know where it strains.\n"
                    "The relationship stands on firm ground and stays open "
                    "to growth."),
        "ipucu": ("A solid base does not mean it lasts unchanged; notice "
                  "what you build on it."),
    },
    "yuksek": {
        "baslik": "Strong relationship",
        "aciklama": ("33-34 range. Your fit is close to complete.\n"
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
