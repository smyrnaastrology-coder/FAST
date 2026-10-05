# -*- coding: utf-8 -*-
"""Tier ortak yardimcilar: API cagrisi, bos/incomplete yonetimi, model cozumleme.

ONEMLI (2026 deneyimi):
- reasoning modelleri (gpt-5.6 serisi) chat.completions + temperature KABUL ETMEZ.
  Dogru yol Responses API: client.responses.create(model, input, max_output_tokens).
- max_output_tokens dusunce reasoning token'lari tbani yiyip metin BOS doner
  (status=incomplete). Bu yuzden pro/ust modellerde tavan yuksek tutulur.
- gpt-5.6+ 'minimal' effort'i desteklemez; 'low/medium/high' destekler.
"""
import os
from dataclasses import dataclass
from typing import Callable, Optional


def log(msg: str) -> None:
    print(f"[tier] {msg}", flush=True)


@dataclass
class Ctx:
    """Bir katmanin calisma baglami."""
    client: object = None            # OpenAI istemcisi (yerel katmanda None)
    prompt: str = ""                 # build_prompt() ciktisi
    engine_json: dict = None         # motor ciktisi (yerel katman bunu kullanir)
    lang: str = "tr"


@dataclass(frozen=True)
class Tier:
    """Tek bir yorumlama katmani."""
    id: str
    label: str
    run: Callable[[Ctx], str]        # ctx -> metin
    needs_key: bool = True           # False = yerel/deterministik
    best_for: str = ""


# ---------- API yardimcilari ----------

def chat_call(client, model: str, prompt: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
    """Chat Completions (gpt-4o / gpt-4o-mini)."""
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (r.choices[0].message.content or "").strip()


def responses_call(client, model: str, prompt: str, max_output_tokens: int = 4000,
                   effort: Optional[str] = None) -> str:
    """Responses API (reasoning modelleri: gpt-5.6 serisi). temperature YOK."""
    kw = {"model": model, "input": prompt, "max_output_tokens": max_output_tokens}
    if effort:
        kw["reasoning"] = {"effort": effort}
    r = client.responses.create(**kw)
    status = getattr(r, "status", "")
    txt = (getattr(r, "output_text", "") or "").strip()
    if not txt and status == "incomplete":
        log(f"{model} status=incomplete -> reasoning token'lari tbani yedi, metin yok")
    elif not txt:
        log(f"{model} bos metin dondu (status={status!r})")
    return txt


def resolve_model(tier_id: str, default: str, *aliases: str) -> str:
    """HORARY_TIER_<ID> env override; geriye donuk uyum icin alias'lar da desteklenir."""
    for key in [f"HORARY_TIER_{tier_id.upper()}"] + [f"HORARY_{a.upper()}_MODEL" for a in aliases]:
        v = os.getenv(key)
        if v:
            return v.strip()
    return default