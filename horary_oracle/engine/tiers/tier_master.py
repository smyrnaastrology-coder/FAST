# -*- coding: utf-8 -*-
"""TIER 5 (en iyi, opsiyonel) - Master: gpt-5.6 serisi.

2026-10 olcum (anahtar erisimi dogrulandi, #60 Houston canli cagri):
  gpt-5.6-sol   7.2 sn  dogru ("EVET... kili payi, uzatma olabilir")
  gpt-5.6-terra 5.5 sn  dogru ("kili payi, gerilimli")   en oz
  gpt-5.6-luna 6.5 sn  dogru
  gpt-5.5-pro 101.9 sn  dogru ama interaktif icin cok yavas
Not: gpt-5.6 'temperature' KABUL ETMEZ (400) - sadece Responses API.
     'minimal' effort desteklenmez; low/medium/high desteklenir.
"""
from .base import Tier, Ctx, responses_call, resolve_model


def run(ctx: Ctx) -> str:
    model = resolve_model("master", "gpt-5.6-sol")
    return responses_call(ctx.client, model, ctx.prompt, max_output_tokens=6000, effort="high")


TIER = Tier(
    id="master",
    label="Master (gpt-5.6-sol)",
    run=run,
    best_for="en derin yorum; su an bir plana bagli degil (HORARY_TIER_MASTER ile secilir)",
)