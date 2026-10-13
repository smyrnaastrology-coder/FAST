"""Haftalik/gunluk odev uretici. Maarif oncul zincirini dikkate alir.

Mantik:
- kritik konular -> konu_anlatim turunde kitap + gunluk 20-30 soru
- gelismeli -> soru_bankasi + 30-50 soru
- guclu -> test/deneme + zamanli prova
- oncul eksik varsa once oncul konu odevlendirilir.
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, List
from . import mufredat as _muf

GUNLER = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]

SEVIYE_SORU = {"temel": (20, 30), "orta": (30, 50), "ileri": (40, 60)}


def konu_bilgisi(segment: str, kod: str) -> Dict:
    veri = _muf.dersler(segment)
    for ders, konular in veri.items():
        for k in konular:
            if k["kod"] == kod:
                return {"ders": ders, **k}
    return {"ders": "", "kod": kod, "baslik": kod, "oncul": [], "zorluk": 3}


def haftalik_plan(ogrenci_seviye: str, segment: str, analiz: Dict,
                  kitap_esleme: Dict[str, str] | None = None,
                  hafta_baslangic: date | None = None) -> List[Dict]:
    """analiz: analiz_motoru.konu_analiz ciktisi. Donus: 7 gunluk odev listesi."""
    kitap_esleme = kitap_esleme or {}
    hafta_baslangic = hafta_baslangic or date.today()
    durum_map = {k["kod"]: k for k in analiz.get("konular", [])}
    # oncelik sirasi: kritik -> gelismeli -> guclu (pekiştirme icin 1 gun)
    sirali = sorted(analiz.get("konular", []), key=lambda s: ({"kritik": 0, "gelismeli": 1, "guclu": 2}[s["durum"]], s["basari"]))
    if not sirali:
        return []
    odevler: List[Dict] = []
    alt, ust = SEVIYE_SORU.get(ogrenci_seviye, (30, 50))
    for i, gun in enumerate(GUNLER):
        # Pazar: haftalik deneme/prova gunu
        if gun == "Pazar":
            odevler.append({
                "gun": gun, "tarih": (hafta_baslangic + timedelta(days=i)).isoformat(),
                "ders": "Deneme", "konu_kod": "DENEME", "konu_baslik": "Haftalik sureli deneme + yanlis defteri",
                "kaynak": "", "adet": ust, "hedef_dk": 90, "neden": "Haftanin kazanimi olculur.",
            })
            continue
        s = sirali[i % len(sirali)]
        bilgi = konu_bilgisi(segment, s["kod"])
        # oncul eksikse once onu ver
        oncul = (bilgi.get("oncul") or [])
        secilen_kod = oncul[0] if (s["durum"] == "kritik" and oncul and oncul[0] not in durum_map) else s["kod"]
        if secilen_kod != s["kod"]:
            bilgi = konu_bilgisi(segment, secilen_kod)
            baslik = bilgi.get("baslik", secilen_kod) + " (oncul tekrar)"
        else:
            baslik = s["baslik"]
        if s["durum"] == "kritik":
            adet, tur_notu = alt, "Konu anlatimi + kolay test"
        elif s["durum"] == "gelismeli":
            adet, tur_notu = (alt + ust) // 2, "Soru bankasi orta testler"
        else:
            adet, tur_notu = ust, "Zor test + sureli cozum"
        odevler.append({
            "gun": gun, "tarih": (hafta_baslangic + timedelta(days=i)).isoformat(),
            "ders": bilgi.get("ders", ""), "konu_kod": secilen_kod, "konu_baslik": baslik,
            "kaynak": kitap_esleme.get(secilen_kod, ""),
            "adet": adet, "hedef_dk": 45 if s["durum"] != "kritik" else 60,
            "neden": f"%{s['basari']} basari ({s['durum']}). {tur_notu}.",
        })
    return odevler
