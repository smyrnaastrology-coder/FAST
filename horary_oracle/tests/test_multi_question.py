# -*- coding: utf-8 -*-
"""Bilesik/Coklu soru modulu birim testleri (test_multi_question.py)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.multi_question import split_questions, classify_slot, sub_answers, multi_instruction_text  # noqa: E402


def test_split_questions_multi():
    subs = split_questions("Leon borcunu gonderecek mi? Beni gormeye gelecek mi? Iletisime gececek mi?")
    assert len(subs) == 3, subs


def test_split_questions_single():
    assert len(split_questions("Bu ise girecek miyim?")) == 1


def test_classify_slots():
    assert classify_slot("Nerede simdi")["slot"] == "where"
    assert classify_slot("Ne zaman doner")["slot"] == "when"
    assert classify_slot("Neden yazmadi")["slot"] == "why"
    assert classify_slot("Kim aldi")["slot"] == "who"
    assert classify_slot("Nasil bulunur")["slot"] == "how"
    assert classify_slot("Borcunu gonderecek mi")["slot"] == "yesno"
    assert classify_slot("Bu ise girecek miyim?")["slot"] == "yesno"


def test_sub_answers_on_real_chart():
    from engine.horary_engine import cast_horary_chart
    r = cast_horary_chart(1984, 10, 14, 4.0, 47.6833, -116.7667, "missing_child")
    ej = {
        "verdict": r["verdict"], "score": r["score"], "perfection": r["perfection"],
        "strictures": r["strictures"], "querent": r["querent"]["planet"],
        "quesited": r["quesited"]["planet"],
        "querent_sign": r["querent"]["sign"], "quesited_sign": r["quesited"]["sign"],
        "houses": {"asc": r["houses"]["asc"], "asc_sign": r["houses"]["asc_sign"],
                   "mc": r["houses"]["mc"]},
        "planets": {k: {"sign": v["sign"], "deg": round(v["deg"], 2), "house": v["house"],
                        "retro": v.get("retro", False), "lon": v["lon"]}
                    for k, v in r["planets"].items()},
        "timing": r.get("timing"),
        "location": {"direction": "KUZEY", "house": 4, "height": "", "ev_ici": "oda"},
        "question": "Ginny ne zaman geri donecek? Nerede simdi? Evine nasil doner?",
    }
    rows = sub_answers(ej, split_questions(ej["question"]))
    assert len(rows) == 3, rows
    labels = [x["label"] for x in rows]
    assert "NE ZAMAN" in labels and "NEREDE" in labels and "NASIL" in labels
    assert any("6-16" in x["facts"] for x in rows)
    txt = multi_instruction_text(ej, rows)
    assert "MULTI" and "NE ZAMAN" and "NEREDE" in txt.upper()


def test_sub_verdict_56_pam_california():
    from engine.horary_engine import cast_horary_chart
    from engine.multi_question import sub_qtype, sub_verdict
    r = cast_horary_chart(1990, 1, 13, 2.45, 47.6833, -116.7667, "general")
    s1 = "Pam ve ben is ortagi olmali miyiz"
    s2 = "Esim ve ben Kaliforniya'ya tasinmali miyiz"
    s3 = "Bu finansal olarak mumkun mu"
    assert sub_qtype(s1) == "business"
    assert sub_qtype(s2) == "relocation"
    assert sub_qtype(s3) == "finance"
    v1 = sub_verdict(r, s1)
    v2 = sub_verdict(r, s2)
    v3 = sub_verdict(r, s3)
    assert v1["qtype"] == "business" and v1["verdict"] == "NO", v1
    assert v2["qtype"] == "relocation" and v2["verdict"] == "NO", v2
    assert v3["qtype"] == "finance" and v3["verdict"] == "BAĞIMLI", v3
    assert "Uranus" in v1["facts"] and "Venus" in v1["facts"] and "Sun" in v1["facts"]
    assert "Mars" in v2["facts"] and "Pluto" in v2["facts"]


def test_sub_answers_56_full_multi():
    from engine.horary_engine import cast_horary_chart
    r = cast_horary_chart(1990, 1, 13, 2.45, 47.6833, -116.7667, "general")
    q = "Pam ve ben is ortagi olmali miyiz? Esim ve ben Kaliforniya'ya tasinmali miyiz? Bu finansal olarak mumkun mu?"
    ej = {
        "verdict": r["verdict"], "score": r["score"], "perfection": r["perfection"],
        "strictures": r["strictures"], "querent": r["querent"]["planet"],
        "quesited": r["quesited"]["planet"],
        "querent_sign": r["querent"]["sign"], "quesited_sign": r["quesited"]["sign"],
        "houses": {"asc": r["houses"]["asc"], "asc_sign": r["houses"]["asc_sign"],
                   "mc": r["houses"]["mc"]},
        "planets": {k: {"sign": v["sign"], "deg": round(v["deg"], 2), "house": v["house"],
                        "retro": v.get("retro", False), "lon": v["lon"]}
                    for k, v in r["planets"].items()},
        "timing": r.get("timing"),
        "location": {"direction": "KUZEY", "house": 4, "height": "", "ev_ici": "oda"},
        "question": q,
    }
    rows = sub_answers(ej, split_questions(q), res=r)
    assert len(rows) == 3, rows
    assert [x["sub_verdict"] for x in rows] == ["NO", "NO", "BAĞIMLI"], rows
    assert rows[0]["qtype_label"] == "İŞ ORTAKLIĞI"
    assert rows[1]["qtype_label"] == "TAŞINMA"
    assert rows[2]["qtype_label"] == "FİNANS"
    txt = multi_instruction_text(ej, rows)
    assert "İŞ ORTAKLIĞI" in txt and "TAŞINMA" in txt and "FİNANS" in txt and "(NO)" in txt and "(BAĞIMLI)" in txt


def test_sub_verdict_57_ben_nikki_boise():
    from engine.horary_engine import cast_horary_chart
    from engine.multi_question import sub_qtype, sub_verdict
    r = cast_horary_chart(1985, 8, 15, 20.8333, 47.6833, -116.7667, "general")
    s1 = "Ben orduya gitmeli mi"
    s2 = "Nikki'yi (ati) satin almis olmali miyiz"
    s3 = "Boise'ye tasinmali miyiz"
    assert sub_qtype(s1) == "army"
    assert sub_qtype(s2) == "animal"
    assert sub_qtype(s3) == "relocation"
    v1 = sub_verdict(r, s1)
    v2 = sub_verdict(r, s2)
    v3 = sub_verdict(r, s3)
    assert v1["qtype"] == "army" and v1["verdict"] == "NO", v1
    assert v2["qtype"] == "animal" and v2["verdict"] == "NO", v2
    assert v3["qtype"] == "relocation" and v3["verdict"] == "NO", v3
    assert "Neptune" in v1["facts"], v1   # onun 10. evi (harita 4) BalIk -> Neptune modern
    assert "Satürn" in v2["facts"] or "Saturn" in v2["facts"], v2
    assert "Moon" in v3["facts"] and "Neptune" in v3["facts"], v3


def test_sub_answers_57_domicile_pisces_neptune():
    from engine.horary_engine import cast_horary_chart
    from engine.multi_question import _ruler
    from core.ephemeris import DOMICILE
    assert DOMICILE["Balık"] == "Neptune"
    s, rul = _ruler(338.29)   # BalIk 8.29
    assert s == "Balık" and rul == "Neptune", (s, rul)


if __name__ == "__main__":
    test_split_questions_multi()
    test_split_questions_single()
    test_classify_slots()
    test_sub_answers_on_real_chart()
    test_sub_verdict_56_pam_california()
    test_sub_answers_56_full_multi()
    test_sub_verdict_57_ben_nikki_boise()
    test_sub_answers_57_domicile_pisces_neptune()
    print("test_multi_question: 8/8 OK")