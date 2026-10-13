"""ISBN dogrulama: checksum (ISBN-13) + Google Books canli kontrol + rapor uretici.

Kullanim (fast_koc klasorunden):
    python -m backend.services.isbn_dogrulama
Rapor: backend/data/isbn_dogrulama_raporu.json
Not: seed katalogdaki 97860518800xx ISBN'lar YER TUTUCUdur (checksum gecse bile
Google Books'ta bulunmaz). Bu script bunu acikca raporlar; yayin oncesi editor
gercek ISBN'leri Admin sayfasindan girmelidir.
"""
from __future__ import annotations
import json
import os
import sys

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
KATALOG = os.path.join(DATA, "kitap_katalog.json")
RAPOR = os.path.join(DATA, "isbn_dogrulama_raporu.json")


def isbn13_gecerli(isbn: str) -> bool:
    s = "".join(c for c in (isbn or "") if c.isdigit())
    if len(s) != 13:
        return False
    toplam = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(s[:12]))
    kontrol = (10 - toplam % 10) % 10
    return kontrol == int(s[12])


def katalog_dogrula(carli_kontrol: bool = False) -> dict:
    from .kitap_servisi import google_books_isbn
    with open(KATALOG, encoding="utf-8") as f:
        katalog = json.load(f)
    satirlar = []
    for k in katalog["kitaplar"]:
        isbn = k.get("isbn", "")
        checksum = isbn13_gecerli(isbn)
        api = google_books_isbn(isbn) if (carli_kontrol and checksum) else None
        durum = "dogrulandi" if api else ("checksum-hatali" if not checksum else "dogrulanmadi-yer-tutucu")
        satirlar.append({
            "id": k["id"], "baslik": k["baslik"], "isbn": isbn,
            "checksum_gecerli": checksum,
            "google_books_bulundu": bool(api),
            "google_books_baslik": (api or {}).get("baslik_api"),
            "durum": durum,
        })
    ozet = {"toplam": len(satirlar),
            "dogrulandi": sum(1 for s in satirlar if s["durum"] == "dogrulandi"),
            "sorunlu": sum(1 for s in satirlar if s["durum"] != "dogrulandi")}
    return {"ozet": ozet, "kitaplar": satirlar}


def main():
    carli = "--canli" in sys.argv
    rapor = katalog_dogrula(carli_kontrol=carli)
    with open(RAPOR, "w", encoding="utf-8") as f:
        json.dump(rapor, f, ensure_ascii=False, indent=1)
    print(f"Toplam {rapor['ozet']['toplam']}, dogrulandi {rapor['ozet']['dogrulandi']}, "
          f"sorunlu {rapor['ozet']['sorunlu']} (canli={carli})")
    for s in rapor["kitaplar"]:
        if s["durum"] != "dogrulandi":
            print(f"  ! {s['id']} {s['baslik'][:40]} isbn={s['isbn']} -> {s['durum']}")
    if rapor["ozet"]["sorunlu"] and not carli:
        print("Ipucu: python -m backend.services.isbn_dogrulama --canli  (internet gerekir)")


if __name__ == "__main__":
    main()
