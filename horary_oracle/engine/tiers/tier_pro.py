# -*- coding: utf-8 -*-
"""KALITE 3 (en iyi) - gpt-5.6-sol.
Olcum: 9.2s, 523 cikti tokeni, $0.0765/soru, EN YUKSEK konum dogrulugu (13/13).
Anlaticilik: "**Humkum: EVET...**" ile acir, yer tahmini verir, risk varsa
kendisi uyarir ("bu sureleri beklemeyin, hemen 112'ye basvurun").
temperature kabul etmez -> Responses API."""
from .base import Tier, Ctx, responses_call, resolve_model


def run(ctx: Ctx) -> str:
    model = resolve_model("pro", "gpt-5.6-sol")
    return responses_call(ctx.client, model, ctx.prompt, max_output_tokens=6000, effort="high")


TIER = Tier(
    id="pro",
    label="En iyi (gpt-5.6-sol)",
    run=run,
    best_for="en keskin hukum, en guvenilir konum okumasi, risk uyarilari",
)