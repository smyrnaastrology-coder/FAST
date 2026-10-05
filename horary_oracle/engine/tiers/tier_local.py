# -*- coding: utf-8 -*-
"""TIER 1 (en kotu) - Yerel deterministik yorumlayici. API anahtari gerektirmez."""
from .base import Tier, Ctx


def run(ctx: Ctx) -> str:
    # Gecikmeli import: engine.interpreter bu paketi import eder -> dongusel import olmamali
    from engine.interpreter import mock_interpret
    return mock_interpret(ctx.engine_json or {}, ctx.lang or "tr")


TIER = Tier(
    id="local",
    label="Yerel (deterministik, ucretsiz)",
    run=run,
    needs_key=False,
    best_for="LLM yokken/anahtar hatasinda asla bos cevap vermemek",
)