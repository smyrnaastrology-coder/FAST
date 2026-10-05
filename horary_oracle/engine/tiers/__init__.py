# -*- coding: utf-8 -*-
"""YORUMLAMA KATMANLARI (en kotuden en iyiye) + plan -> katman eslemesi.

    local  (deterministik, ucretsiz)      <- anahtar yoksa da son care
    oracle (gpt-4o-mini)                  <- en ucuz hizli kademe
    seer   (gpt-4.1)                      <- ara kademe: hizli + detayli anlatim
    premium(gpt-4o)                       <- dengeli kademe
    sage   (gpt-5.6-terra reasoning)      <- hizli reasoning, net hukum
    elite  (o1 reasoning)                 <- en derin gerekce zinciri
    master (gpt-5.6-sol)                  <- en kapsamli ust kademe

Bir katman bos metin donerse veya hata verirse OTOMATIK olarak bir altindaki
katmana dusulur; en altinda yerel deterministik yorum vardir, yani hicbir
sartta bos cevap donmez.

Model degistirmek icin env: HORARY_TIER_ORACLE / _PREMIUM / _ELITE / _MASTER
(ayrica geriye donuk uyum: HORARY_ELITE_MODEL).
"""
import os

from .base import Ctx, Tier, log
from .tier_local import TIER as T_LOCAL
from .tier_oracle import TIER as T_ORACLE
from .tier_seer import TIER as T_SEER
from .tier_premium import TIER as T_PREMIUM
from .tier_sage import TIER as T_SAGE
from .tier_elite import TIER as T_ELITE
from .tier_master import TIER as T_MASTER

# en kotuden en iyiye (aralik kademeler olcum sonucu eklendi)
TIERS = [T_LOCAL, T_ORACLE, T_SEER, T_PREMIUM, T_SAGE, T_ELITE, T_MASTER]

PLAN_TIER = {
    "": "oracle",
    "free": "oracle",
    "oracle": "oracle",
    "seer": "seer",
    "premium": "premium",
    "sage": "sage",
    "elite": "elite",
    "pro": "elite",
    "master": "master",
    "max": "master",
}


def plan_to_tier(plan: str) -> str:
    return PLAN_TIER.get((plan or "").strip().lower(), "oracle")


def tier_index(tier_id: str) -> int:
    for i, t in enumerate(TIERS):
        if t.id == tier_id:
            return i
    return 0


def tier_labels() -> str:
    return " < ".join(f"{t.id}({t.label.split('(')[-1].rstrip(')')})" for t in TIERS)


def run_ladder(tier_id: str, prompt: str, engine_json: dict, lang: str = "tr"):
    """Verilen katmandan baslar; hata/bos metin olursa KOTUYE DOGRU iner
    (elite -> premium -> oracle -> local). Asla daha iyi katmana atlamaz.
    Donus: (metin, kullanilan_tier_id).

    NOT: run_ladder secilen katmandan BASLAR ve asagi iner. Yani seer baslatirsak
    gpt-4.1'den gpt-4o'ya ve gpt-5.6-terra'ya ASLA cikmaz - onlar ust kademedir."""
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