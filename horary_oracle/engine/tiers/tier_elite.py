# -*- coding: utf-8 -*-
"""TIER 4 - Elite: o1 (reasoning). Responses API, temperature YOK, yuksek token tavani.

Onceki "o1 bos dondu" sebebi: chat.completions + temperature/max_tokens ile cagrildi.
o1 bunlari kabul etmez; reasoning token'lari tbani yediginde metin BOS gelir
(status=incomplete) - o yuzden max_output_tokens yuksek tutulur.
"""
from .base import Tier, Ctx, responses_call, resolve_model


def run(ctx: Ctx) -> str:
    # HORARY_ELITE_MODEL geriye donuk uyum icin alias olarak desteklenir
    model = resolve_model("elite", "o1", "elite")
    # reasoning modelleri soylem API'si ister; o1'den baska o-serisi de Responses API ile calisir
    return responses_call(ctx.client, model, ctx.prompt, max_output_tokens=4000)


TIER = Tier(
    id="elite",
    label="Elite (o1 reasoning)",
    run=run,
    best_for="15 kredi kademesi - gerekce zinciri en derin",
)