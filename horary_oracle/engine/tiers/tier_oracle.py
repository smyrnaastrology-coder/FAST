# -*- coding: utf-8 -*-
"""TIER 2 - Oracle / ucuz: gpt-4o-mini (en hizli, en ucuz, yeterli kalite)."""
from .base import Tier, Ctx, chat_call, resolve_model


def run(ctx: Ctx) -> str:
    model = resolve_model("oracle", "gpt-4o-mini")
    return chat_call(ctx.client, model, ctx.prompt, max_tokens=800, temperature=0.3)


TIER = Tier(
    id="oracle",
    label="Oracle (gpt-4o-mini)",
    run=run,
    best_for="ucretsiz/5 kredi kademesi - hizli ve yeterli",
)