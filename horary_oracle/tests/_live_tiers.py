# -*- coding: utf-8 -*-
"""Yeni aralik kademelerin canli dogrulamasi: seer (gpt-4.1) ve sage (gpt-5.6-terra).
Gercek Houston #60 haritasi + build_prompt uzerinden tam merdiven."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import engine.tiers as T
from engine.horary_engine import cast_horary_chart
from engine.interpreter import build_prompt

chart = cast_horary_chart(1980, 12, 5, 1 + 35 / 60.0, 47.678, -116.781, "sport_fan")
chart["question"] = "Bu gece Houston Texans kazanacak mi?"
prompt = build_prompt(chart, "tr")
print(f"MOTOR: verdict={chart.get('verdict')} timing={chart.get('timing', {}).get('text', '')}")
print(f"prompt: {len(prompt)} krkt\n")
print(f"{'kademe':<8} {'model':<16} {'sure':>7}  {'krkt':>5}  onizleme")
print("-" * 110)

for tier in ["local", "oracle", "seer", "premium", "sage", "elite", "master"]:
    t0 = time.time()
    txt, used = T.run_ladder(tier, prompt, chart, "tr")
    dt = time.time() - t0
    model = {"local": "-", "oracle": "gpt-4o-mini", "seer": "gpt-4.1",
             "premium": "gpt-4o", "sage": "gpt-5.6-terra",
             "elite": "o1", "master": "gpt-5.6-sol"}[tier]
    ok = "OK " if used == tier else "-> "
    print(f"{ok}{tier:<7} {model:<16} {dt:6.1f}s  {len(txt):5d}  {txt[:52].replace(chr(10), ' ')}")
    assert txt.strip(), f"{tier} bos metin dondu!"

print("\nhepsi metin verdi, hicbir katman bos kalmadi")