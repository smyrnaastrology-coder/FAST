# -*- coding: utf-8 -*-
"""YORUMLAMA KALITELERI - 3 SATILABILIR KADEME + 1 YEREL SON CARE.

    local  deterministik        anahtar yoksa / LLM calismazsa (satilabilir degil)
    basic  gpt-4.1              KALITE 1 - Temel      $0.036/soru
    plus   gpt-5.6-terra        KALITE 2 - Gelismis   $0.038/soru
    pro    gpt-5.6-sol          KALITE 3 - En iyi     $0.077/soru

Olcum tabani: 5 horary haritasi (spor x2, kayip cocuk, is, para), 47k krkt prompt.

NEDEN o1 YOK: o1 de 0 hata verdi ama $0.356/soru (pro'nun 4.6 kati) ve 17.6s.
Ayni isi gpt-5.6-sol 5 kat hizli ve daha yuksek konum dogruluguyla yapiyor
(13/13 vs 5/5). Satisa koyulmadi.

NEDEN gpt-4o-mini YOK: tek yanlis burc okumasini o yapti (Ay 7° -> "120°").

Bir katman bos metin donerse veya hata verirse OTOMATIK olarak bir ALTINDAKI
katmana dusulur; en altta yerel deterministik yorum vardir - hicbir sartta
bos cevap donmez. YukarI kademeye ASLA atlanmaz.

Model degistirmek icin env: HORARY_TIER_BASIC / _PLUS / _PRO
(ayrica geriye donuk uyum: HORARY_ELITE_MODEL vb.)
"""
import os

from .base import Ctx, Tier, log
from .tier_local import TIER as T_LOCAL
from .tier_basic import TIER as T_BASIC
from .tier_plus import TIER as T_PLUS
from .tier_pro import TIER as T_PRO

# kotu -> iyi
TIERS = [T_LOCAL, T_BASIC, T_PLUS, T_PRO]

PLAN_TIER = {
    "": "basic",            # bos plan / deneme -> Temel
    "free": "basic",
    "trial": "basic",
    "basic": "basic",
    "oracle": "basic",
    "seer": "basic",
    "premium": "basic",
    "plus": "plus",
    "sage": "plus",
    "pro": "pro",
    "elite": "pro",         # eski elite -> en iyi kademe (o1 kaldirildi)
    "master": "pro",
    "max": "pro",
}


def plan_to_tier(plan: str) -> str:
    return PLAN_TIER.get((plan or "").strip().lower(), "basic")


def tier_index(tier_id: str) -> int:
    for i, t in enumerate(TIERS):
        if t.id == tier_id:
            return i
    return 1  # bilinmeyen -> basic (local yanlislik olurdu)


def tier_labels() -> str:
    return " < ".join(t.id for t in TIERS)


def run_ladder(tier_id: str, prompt: str, engine_json: dict, lang: str = "tr"):
    """Verilen katmandan baslar; hata/bos metin olursa KOTUYE DOGRU iner
    (pro -> plus -> basic -> local). Asla daha iyi katmana atlamaz.
    Donus: (metin, kullanilan_tier_id)."""
    start = tier_index(tier_id)
    client = None
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        except Exception as e:
            log(f"OpenAI istemcisi kurulamadi: {e}")

    # en kotu: istenen katman, sonra altindakiler (local her zaman son care)
    for t in reversed(TIERS[:start + 1]):
        if t.needs_key and client is None:
            log(f"{t.id} atlandi (OPENAI_API_KEY yok)")
            continue
        try:
            txt = (t.run(Ctx(client=client, prompt=prompt, engine_json=engine_json, lang=lang)) or "").strip()
        except Exception as e:
            log(f"{t.id} hata: {type(e).__name__}: {str(e)[:160]}")
            continue
        if txt:
            if t.id != tier_id:
                log(f"{tier_id} -> {t.id} dusuldu")
            return txt, t.id
        log(f"{t.id} bos metin, bir alt katmana geciliyor")
    return "", ""