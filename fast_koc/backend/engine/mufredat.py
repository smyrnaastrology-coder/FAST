"""Mufredat segment cozucu (donem ayrimi).

2026-27 donemi: 9-10-11 Maarif Modeli, 12 + mezun eski sistem.
2027-28 ve sonrasi: tumu Maarif (TUMU_MAARIF_DONEMI bayragi).

Segmentler: LGS | ARA_9_10_11 | YKS_ESKI | YKS_MAARIF
Eski 'YKS' degeri geriye uyumluluk icin YKS_ESKI olarak okunur.
"""
from __future__ import annotations
import json
import os
from functools import lru_cache
from typing import Dict, List

MUFREDAT_YOLU = os.path.join(os.path.dirname(__file__), "..", "data", "maarif_mufredat.json")

SEGMENT_META = {
    "LGS": {"etiket": "LGS (8. sınıf)", "sistem": "maarif"},
    "ARA_9_10_11": {"etiket": "9-10-11. sınıflar", "sistem": "maarif"},
    "YKS_ESKI": {"etiket": "YKS — 12/Mezun (Eski Sistem)", "sistem": "eski"},
    "YKS_MAARIF": {"etiket": "YKS — Maarif (11. sınıf erken hazırlık)", "sistem": "maarif"},
}

GECERLI_SEGMENTLER = list(SEGMENT_META.keys())


def tumu_maarif_donemi() -> bool:
    """2027-28 ve sonrasi True olmali (env ile acilir)."""
    return os.environ.get("FASTKOC_TUMU_MAARIF", "false").lower() == "true"


def coz(segment: str | None) -> str:
    """Ham segment degerini gecerli segmente cozumler. Bilinmeyen -> YKS_ESKI (guvenli)."""
    s = (segment or "").strip()
    if s == "YKS":
        return "YKS_ESKI"  # geriye uyumluluk: mevcut YKS'liler eski sistem 12/mezun
    if s in SEGMENT_META:
        return s
    return "YKS_ESKI"


def sistem_of(segment: str) -> str:
    return SEGMENT_META[coz(segment)]["sistem"]


def etiket_of(segment: str) -> str:
    return SEGMENT_META[coz(segment)]["etiket"]


def secilebilir_segmentler() -> List[str]:
    """Profil formunda gosterilecek segmentler (doneme gore)."""
    if tumu_maarif_donemi():
        return ["LGS", "ARA_9_10_11", "YKS_MAARIF"]
    return GECERLI_SEGMENTLER


def siniftan_oner(sinif: str) -> str:
    """Sinif metnine gore segment onerisi: 8->LGS, 9/10/11->ARA, 12/mezun->YKS_ESKI."""
    s = (sinif or "").lower()
    if "8" in s:
        return "LGS"
    if any(x in s for x in ("9", "10", "11")):
        return "ARA_9_10_11"
    return "YKS_ESKI"


@lru_cache(maxsize=1)
def _ham_yukle() -> Dict:
    with open(MUFREDAT_YOLU, encoding="utf-8") as f:
        return json.load(f)


def dersler(segment: str) -> Dict[str, List[Dict]]:
    """Segmentin ders->konu agaci. Alias cozumlu."""
    return _ham_yukle()["segmentler"][coz(segment)]["dersler"]


def takvim_eslesme(segment: str) -> List[str]:
    """Deneme takvimi filtre degerleri. Iki YKS varyanti ayni TG'lere girer."""
    c = coz(segment)
    if c in ("YKS_ESKI", "YKS_MAARIF"):
        return ["YKS", "YKS_ESKI", "YKS_MAARIF"]
    return [c]


def analiz_segmenti(segment: str) -> str:
    """Net hesabi icin: LGS ham, digerleri YKS formulu."""
    return "LGS" if coz(segment) == "LGS" else "YKS"
