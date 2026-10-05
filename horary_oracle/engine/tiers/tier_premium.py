# -*- coding: utf-8 -*-
"""TIER 3 - Premium: gpt-4o (dengeli kalite/hiz)."""
from .base import Tier, Ctx, chat_call, resolve_model


def run(ctx: Ctx) -> str:
    model = resolve_model("premium", "gpt-4o")
    return chat_call(ctx.client, model, ctx.prompt, max_tokens=800, temperature=0.3)


TIER = Tier(
    id="premium",
    label="Premium (gpt-4o)",
    run=run,
    best_for="8 kredi kademesi - yerlesik ve guvenilir",
)