# -*- coding: utf-8 -*-
"""3 kademenin canli dogrulamasi + sure duzeltmesi (motorla tutarlilik)."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import engine.tiers as T
from engine.horary_engine import cast_horary_chart
from engine.interpreter import build_prompt, _correct_timing_hallucination

COEUR = (47.678, -116.781)
CHARTS = [
    ("s60_houston", (1980, 12, 5, 1 + 35 / 60.0, COEUR[0], COEUR[1], "sport_fan"),
     "Bu gece Houston Texans kazanacak mi?"),
    ("kayip_cocuk", (1984, 10, 14, 4.0, 47.6833, -116.7667, "missing_child"),
     "Kaybolan cocugum nerede?"),
    ("genel_is", (1985, 8, 15, 20.8333, 47.6833, -116.7667, "general"),
     "Bu ise girecek miyim?"),
    ("para", (1990, 1, 13, 2.45, 47.6833, -116.7667, "general"),
     "Bu parayi alacak miyim?"),
]
TIERS = [("basic", "gpt-4.1"), ("plus", "gpt-5.6-terra"), ("pro", "gpt-5.6-sol")]

print(f"{'harita':<13} {'kademe':<7} {'sure':>7} {'kar':>5} {'motor':<11} onizleme")
print("-" * 108)

for cname, args, q in CHARTS:
    chart = cast_horary_chart(*args)
    chart["question"] = q
    prompt = build_prompt(chart, "tr")
    motor_time = (chart.get("timing") or {}).get("text", "")
    print(f"\n{cname}  motor={chart.get('verdict')}  motor_suresi={motor_time!r}")
    for tier, model in TIERS:
        t0 = time.time()
        txt, used = T.run_ladder(tier, prompt, chart, "tr")
        dt = time.time() - t0
        fixed = _correct_timing_hallucination(txt, chart)
        assert fixed.strip(), f"{tier} bos metin"
        print(f"  {tier:<9} {dt:5.1f}s {len(txt):5d}  {motor_time:<11} "
              f"{txt[:44].replace(chr(10), ' ')}")

print("\n=== sure duzeltme birimi (motor 40 YIL, metin '6 gun' diyordu) ===")
fake = {"timing": {"text": "40 YIL"}}
for sample in [
    "Yaklasik 6 gun icinde bir haber gelebilir.",
    "Ilk haber 2 gun, genis donus 6-16 gun.",
    "Bu ay sonunda netlesir.",
    "Harita umut veriyor.",
]:
    print(f"  once : {sample}")
    print(f"  sonra: {_correct_timing_hallucination(sample, fake)}")
    print()