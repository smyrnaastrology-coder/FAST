# -*- coding: utf-8 -*-
"""TIER 3.5 - Ust kademe: gpt-5.6-terra (reasoning, hizli).
Olcum (Houston #60): ~6.2sn, 663 krkt, net "Evet... ama kil payi" huku mu.
gpt-5.6 'temperature' KABUL ETMEZ -> Responses API; 'minimal' effort reddedilir
(400), low/medium/high calisir. max_output_tokens yuksek tutulur (bos done onlemi)."""
from .base import Tier, Ctx, responses_call, resolve_model


def run(ctx: Ctx) -> str:
    model = resolve_model("sage", "gpt-5.6-terra")
    return responses_call(ctx.client, model, ctx.prompt, max_output_tokens=6000, effort="high")


TIER = Tier(
    id="sage",
    label="Sage (gpt-5.6-terra reasoning)",
    run=run,
    best_for="premium ile master arasinda: hizli reasoning + net hukum",
)