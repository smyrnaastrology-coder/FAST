"""Optik hizli giris: cevap anahtari + ogrenci cevaplari metni -> D/Y/B sayimi.

Format: harf dizisi, or. anahtar='ABCDEABCDE', cevap='ABCDEABXDE' (X/bos = bos).
Buyuk-kucuk duyarsiz; bosluklar yok sayilir; gecerli harfler A-E (+bos icin X, -, .).
Donus: {dogru, yanlis, bos} + soru bazinda detay.
"""
from __future__ import annotations
from typing import Dict, List

GECERLI = set("ABCDE")
BOS = set("X-.")


def optik_karsilastir(anahtar: str, cevap: str) -> Dict:
    a = [c for c in anahtar.upper() if c.strip()]
    c = [x for x in cevap.upper() if x.strip()]
    if len(a) == 0:
        raise ValueError("anahtar bos")
    if len(a) != len(c):
        raise ValueError(f"soru sayisi tutmuyor: anahtar {len(a)}, cevap {len(c)}")
    detay: List[Dict] = []
    d = y = b = 0
    for i, (ka, kc) in enumerate(zip(a, c), start=1):
        if ka not in GECERLI:
            raise ValueError(f"anahtar {i}. soru gecersiz harf: {ka}")
        if kc in BOS or kc == "":
            b += 1; sonuc = "bos"
        elif kc not in GECERLI:
            raise ValueError(f"cevap {i}. soru gecersiz harf: {kc}")
        elif kc == ka:
            d += 1; sonuc = "dogru"
        else:
            y += 1; sonuc = "yanlis"
        detay.append({"soru": i, "anahtar": ka, "cevap": kc, "sonuc": sonuc})
    return {"dogru": d, "yanlis": y, "bos": b, "toplam": len(a), "detay": detay}
