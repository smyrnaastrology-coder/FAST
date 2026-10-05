# -*- coding: utf-8 -*-
"""KALITE 1 (temel) - gpt-4.1.
Olcum (5 horary haritasi, 47k krkt prompt):
  gpt-4.1  3.4s  325 cikti tokeni  $0.0356/soru  0 yanlis konum
  gpt-4o   3.7s  186 cikti tokeni  $0.0432/soru  0 yanlis konum
Yani 4.1 1.75x daha uzun aciklama yaziyor VE daha ucuz (girdi $2/M, cikti $8/M
gpt-4o'nun $2.50/$10'undan dusuk). Bu yuzden temel kademe 4o degil 4.1."""
from .base import Tier, Ctx, chat_call, resolve_model


def run(ctx: Ctx) -> str:
    model = resolve_model("basic", "gpt-4.1")
    return chat_call(ctx.client, model, ctx.prompt, max_tokens=1100, temperature=0.3)


TIER = Tier(
    id="basic",
    label="Temel (gpt-4.1)",
    run=run,
    best_for="gunluk kullanim - uzun aciklamali, ucuz, kanitli",
)