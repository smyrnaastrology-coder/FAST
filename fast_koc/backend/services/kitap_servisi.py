"""Kitap servisi: seed katalog + Google Books / Open Library zenginlestirme + cache.

Kullanim:
    from backend.services.kitap_servisi import kitap_oner, kapak_url_al
Telif notu: yalnizca kapak URL + kisa tanitim + satin alma baglantisi gosterilir.
"""
from __future__ import annotations
import json
import os
import time
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Any, Dict, List, Optional

KATALOG_YOLU = os.path.join(os.path.dirname(__file__), "..", "data", "kitap_katalog.json")
CACHE_DOSYA = os.path.join(os.path.dirname(__file__), "..", "data", "kitap_cache.json")
CACHE_SURE_SN = 30 * 24 * 3600  # 30 gun

SEVIYE_SIRASI = {"temel": 0, "orta": 1, "ileri": 2}


def katalog_yukle() -> List[Dict[str, Any]]:
    with open(KATALOG_YOLU, encoding="utf-8") as f:
        return json.load(f)["kitaplar"]


def _cache_oku() -> Dict[str, Any]:
    try:
        with open(CACHE_DOSYA, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _cache_yaz(cache: Dict[str, Any]) -> None:
    try:
        with open(CACHE_DOSYA, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def google_books_isbn(isbn: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
    """Google Books API'den ISBN ile kuenye ceker. Ag yoksa None doner."""
    isbn = (isbn or "").strip()
    if not isbn:
        return None
    url = "https://www.googleapis.com/books/v1/volumes?q=" + urllib.parse.quote("isbn:" + isbn)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FastKoc/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            veri = json.loads(r.read().decode("utf-8", "ignore"))
        items = veri.get("items") or []
        if not items:
            return None
        info = items[0].get("volumeInfo", {})
        img = (info.get("imageLinks") or {})
        return {
            "baslik_api": info.get("title"),
            "yazar_api": info.get("authors"),
            "aciklama_api": (info.get("description") or "")[:600],
            "sayfa_api": info.get("pageCount"),
            "kapak_api": img.get("thumbnail") or img.get("smallThumbnail"),
            "yayin_api": info.get("publisher"),
        }
    except Exception:
        return None


def kapak_url_al(isbn: str, baslik: str = "") -> str:
    """Once cache/API, olmazsa Open Library, o da olmazsa placeholder dondurur."""
    isbn = (isbn or "").strip()
    cache = _cache_oku()
    simdi = time.time()
    if isbn and isbn in cache and simdi - cache[isbn].get("_ts", 0) < CACHE_SURE_SN:
        k = cache[isbn]
        if k.get("kapak"):
            return k["kapak"]
    api = google_books_isbn(isbn) if isbn else None
    if api and api.get("kapak_api"):
        kapak = api["kapak_api"].replace("http://", "https://")
        cache[isbn] = {"kapak": kapak, "_ts": simdi, **api}
        _cache_yaz(cache)
        return kapak
    if isbn:
        # Open Library her zaman denenebilir (ucretsiz, anahtarsiz)
        return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
    return "assets/kitap_placeholder.png"


def kitap_oner(segment: str, ders: Optional[str] = None, konu_kodlari: Optional[List[str]] = None,
               ogrenci_seviye: str = "orta", tur: Optional[str] = None,
               limit: int = 6) -> List[Dict[str, Any]]:
    """Seviyeye + derse + eksik konulara gore sirali kitap onerisi.

    Siralama: konu eslesme sayisi (agirlikli) + seviye yakinligi.
    """
    katalog = katalog_yukle()
    konu_kodlari = set(konu_kodlari or [])
    sonuc = []
    for k in katalog:
        puan = 0
        if ders and ders in k.get("dersler", []):
            puan += 3
        elif ders is None:
            puan += 1
        eslesme = len(konu_kodlari & set(k.get("maarif", [])))
        puan += eslesme * 4
        # seviye yakinligi: ayni seviye +2, bir kademe fark +1
        try:
            fark = abs(SEVIYE_SIRASI.get(k["seviye"], 1) - SEVIYE_SIRASI.get(ogrenci_seviye, 1))
            puan += {0: 2, 1: 1}.get(fark, 0)
        except KeyError:
            pass
        if tur and k.get("tur") != tur:
            puan -= 2
        # segment uyumu: LGS kitaplari ders adinda LGS gecer
        sonuc.append((puan, k))
    sonuc.sort(key=lambda x: x[0], reverse=True)
    oneriler = []
    for puan, k in sonuc[:limit]:
        k2 = dict(k)
        k2["onerilme_puani"] = puan
        k2["kapak_url"] = kapak_url_al(k.get("isbn", ""), k.get("baslik", ""))
        oneriler.append(k2)
    return oneriler
