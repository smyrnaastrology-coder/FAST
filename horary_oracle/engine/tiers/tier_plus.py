# -*- coding: utf-8 -*-
"""KALITE 2 (gelismis) - gpt-5.6-terra.
Olcum: 8.0s, 439 cikti tokeni, $0.0383/soru, 0 yanlis konum.
Ozelligi: her yanitta tek cumlede karar veriyor ("**Evet... ama kil payi**"),
sonra gerekce. Kayip cocuk haritasinda "hemen 112 arayin" gibi guvenlik
uyarisini KENDISI ekledi - hicbir kademe bunu istemedi.
gpt-5.6 'temperature' KABUL ETMEZ -> Responses API. 'minimal' effort 400 ile
reddedilir; low/medium/high calisir."""
from .base import Tier, Ctx, responses_call, resolve_model


def run(ctx: Ctx) -> str:
    model = resolve_model("plus", "gpt-5.6-terra")
    return responses_call(ctx.client, model, ctx.prompt, max_output_tokens=6000, effort="high")


TIER = Tier(
    id="plus",
    label="Gelismis (gpt-5.6-terra)",
    run=run,
    best_for="net hukum + derin gerekce, temel kadar ucuz",
)