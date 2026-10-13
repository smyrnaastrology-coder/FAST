"""Yapay zeka koc yorumu: OPENAI_API_KEY varsa LLM, yoksa sablon (offline guvenli).

`koc_yorumu_uret(analiz, profil_ozet)`: kisa, motive edici, somut 3 adimli paragraf dondurur.
"""
from __future__ import annotations
import json
import os
import urllib.request
from typing import Dict


def _sablon(analiz: Dict, ad: str = "") -> str:
    oncelikli = analiz.get("oncelikli", [])
    isimler = ", ".join(o.get("baslik") or o.get("kod", "") for o in oncelikli[:3])
    hitap = f"{ad}, " if ad else ""
    return (f"{hitap}verilerin hazir. Genel basarin %{analiz.get('genel_basari', 0)}. "
            f"Once su 3 konuya odaklan: {isimler or 'zayif konular'}. "
            f"1) Her birine 25 dk konu tekrari yap. "
            f"2) Her konudan 30 soru coz, yanlislari deftere isle. "
            f"3) Hafta sonu sureli denemeyle olc. Kritik konu kalmayana kadar yeni konu acma.")


def koc_yorumu_uret(analiz: Dict, ad: str = "", segment: str = "") -> Dict:
    key = os.environ.get("OPENAI_API_KEY", "")
    sablon = _sablon(analiz, ad)
    if not key:
        return {"kaynak": "sablon", "yorum": sablon}
    try:
        govde = {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": (
                    "Sen Fast Koc adinda Turkce konusan bir sinav kocusun. "
                    "Kisa (max 120 kelime), somut ve motive edici yaz. 3 adim ver.")},
                {"role": "user", "content": (
                    f"Ogrenci: {ad or '-'} ({segment}). Analiz ozeti: {analiz.get('ozet_cumle', '')} "
                    f"Oncelikli: {analiz.get('oncelikli', [])}")},
            ],
            "max_tokens": 300,
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(govde).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=25) as r:
            js = json.loads(r.read().decode())
        metin = js["choices"][0]["message"]["content"].strip()
        return {"kaynak": "yapay-zeka", "yorum": metin}
    except Exception as e:
        return {"kaynak": "sablon-yedek", "yorum": sablon, "not": str(e)[:200]}
