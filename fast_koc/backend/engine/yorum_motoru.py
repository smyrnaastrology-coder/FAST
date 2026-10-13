"""Grafik yorumu + gunluk kiyas cumbeleri uretici."""
from __future__ import annotations
from typing import Dict, List


def gunluk_kiyas(hedef_soru: int, yapilan_soru: int, odev_adetleri: List[int] | None = None) -> str:
    odev_adetleri = odev_adetleri or []
    odev_toplam = sum(odev_adetleri)
    baz = odev_toplam if odev_toplam else hedef_soru
    oran = (yapilan_soru / baz * 100.0) if baz else 0.0
    if oran >= 100:
        return (f"Harikasin! Hedef {baz} soruydu, {yapilan_soru} cozdun (%{oran:.0f}). "
                "Bu tempoyu koru; yarin bir ust seviyeden 10 soru ekleyelim mi?")
    if oran >= 70:
        return (f"Iyi gidiyorsun: {yapilan_soru}/{baz} soru (%{oran:.0f}). "
                f"Eksik {baz - yapilan_soru} soru yarinki plana eklendi. Hangi konuda takildin, not birak.")
    if oran > 0:
        return (f"Bugun {yapilan_soru}/{baz} soruda kaldin (%{oran:.0f}). "
                "Sorun sure mi, zorluk mu? Yarin kritik konudan kisa tekrar + az soruyla basla, sonra hizi artir.")
    return ("Bugun soru girisi yok. Kucuk basla: 20 dakikalik tek test coz ve gir. "
            "Sifir gunleri zinciri kirar; yarin telafi plani hazirlayacagim.")


def donem_yorumu(haftalik_sorular: List[int], haftalik_netler: List[float],
                 zayif_konular: List[str]) -> str:
    if not haftalik_sorular:
        return "Henuz yeterli veri yok. 7 gun duzenli giris yapinca trend yorumu acilacak."
    ort = sum(haftalik_sorular) / len(haftalik_sorular)
    trend = ""
    if len(haftalik_sorular) >= 2:
        fark = haftalik_sorular[-1] - haftalik_sorular[-2]
        trend = f"Gecen haftaya gore {fark:+d} soru. " + ("Yukselis suruyor." if fark > 0 else "Dusus var; hedefi kucultup duzeni koru." if fark < 0 else "Stabil.")
    net_cumle = ""
    if haftalik_netler and len(haftalik_netler) >= 2:
        dn = haftalik_netler[-1] - haftalik_netler[0]
        net_cumle = f" Net degisimi {dn:+.1f}."
    zayif = f" Odak: {', '.join(zayif_konular[:3])}." if zayif_konular else ""
    return f"Haftalik ortalama {ort:.0f} soru. {trend}{net_cumle}{zayif}"
