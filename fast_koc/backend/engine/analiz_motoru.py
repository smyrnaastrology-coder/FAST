"""Konu bazli sinav analiz motoru.

Girdi: sinav konu kirimlari [{kod, baslik, dogru, yanlis, bos}]
Cikti: ders ozeti + konu duzeyinde basari% + durum (kritik/gelismeli/guclu) + oncelikli 3 konu.
Net hesabi: YKS icin D - Y/4 (guncel OSYM), LGS ham puan icin D (yanlis goturmez).
"""
from __future__ import annotations
from typing import Dict, List
from . import mufredat as _muf

KRITIK_ESIK = 40.0
GUCLU_ESIK = 70.0


def konu_analiz(konular: List[Dict], segment: str = "YKS") -> Dict:
    satirlar = []
    td = ty = tb = 0
    for k in konular:
        d = int(k.get("dogru", 0)); y = int(k.get("yanlis", 0)); b = int(k.get("bos", 0))
        top = d + y + b
        oran = (d / top * 100.0) if top else 0.0
        durum = "guclu" if oran >= GUCLU_ESIK else ("gelismeli" if oran >= KRITIK_ESIK else "kritik")
        satirlar.append({
            "kod": k.get("kod", ""), "baslik": k.get("baslik", ""),
            "dogru": d, "yanlis": y, "bos": b, "toplam": top,
            "basari": round(oran, 1), "durum": durum,
        })
        td += d; ty += y; tb += b
    if _muf.analiz_segmenti(segment) == "LGS":
        net = float(td)
    else:
        net = round(td - ty / 4.0, 2)
    genel = round(td / (td + ty + tb) * 100.0, 1) if (td + ty + tb) else 0.0
    # oncelik: once kritik (basari dusuk), sonra agirlik varsayimiyla cok sorulu konular
    oncelikli = sorted(satirlar, key=lambda s: (s["basari"], -s["toplam"]))[:3]
    zayif = [s for s in satirlar if s["durum"] == "kritik"]
    return {
        "toplam_dogru": td, "toplam_yanlis": ty, "toplam_bos": tb,
        "net": net, "genel_basari": genel,
        "konular": sorted(satirlar, key=lambda s: s["basari"]),
        "kritik_sayisi": len(zayif),
        "oncelikli": [{"kod": s["kod"], "baslik": s["baslik"], "basari": s["basari"]} for s in oncelikli],
        "ozet_cumle": _ozet_cumle(genel, net, zayif, oncelikli),
    }


def _ozet_cumle(genel: float, net: float, zayif: List[Dict], oncelikli: List[Dict]) -> str:
    if genel >= GUCLU_ESIK:
        taban = f"Genel basarin %{genel} ile guclu (net {net}). "
    elif genel >= KRITIK_ESIK:
        taban = f"Genel basarin %{genel} ile gelisiyor (net {net}). "
    else:
        taban = f"Genel basarin %{genel} ile kritik bolgede (net {net}). "
    if oncelikli:
        isimler = ", ".join(s["baslik"] or s["kod"] for s in oncelikli)
        taban += f"Once su 3 konuya odaklan: {isimler}. "
    if zayif:
        taban += f"{len(zayif)} konuda oncul eksik olabilir; konu anlatimiyla basla, sonra soru bankasina gec."
    else:
        taban += "Kritik eksik yok; hizi ve deneme provasi one al."
    return taban


def cok_sinav_birlestir(sinavlar: List[Dict]) -> Dict:
    """Birden fazla sinavin konu kirimlarini toplayip kumulatif analiz dondurur."""
    birlesik: Dict[str, Dict] = {}
    for s in sinavlar:
        for k in s.get("konular", []):
            kod = k.get("kod", "?")
            b = birlesik.setdefault(kod, {"kod": kod, "baslik": k.get("baslik", ""), "dogru": 0, "yanlis": 0, "bos": 0})
            b["dogru"] += int(k.get("dogru", 0)); b["yanlis"] += int(k.get("yanlis", 0)); b["bos"] += int(k.get("bos", 0))
    return konu_analiz(list(birlesik.values()))
