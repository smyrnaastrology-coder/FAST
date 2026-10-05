# -*- coding: utf-8 -*-
"""TIER 1.5 - Arali kademe: gpt-4.1 (hizli, ayrintili betimleme).
Olcum (Houston #60, 47k krkt prompt): ~3.0sn, 1024 krkt, yerlesik/derin anlatim.
Chat Completions (temperature destekler)."""
from .base import Tier, Ctx, chat_call, resolve_model


def run(ctx: Ctx) -> str:
    model = resolve_model("seer", "gpt-4.1")
    return chat_call(ctx.client, model, ctx.prompt, max_tokens=900, temperature=0.3)


TIER = Tier(
    id="seer",
    label="Seer (gpt-4.1)",
    run=run,
    best_for="oracle'den hizli ama gpt-4o'dan detayli uzun anlatim isteyen ara kademe",
)