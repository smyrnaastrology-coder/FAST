"""Takvim + katalog seed yukleyici (JSON -> DB). Idempotent: kod varsa atlar."""
from __future__ import annotations
import json
import os
from datetime import date
from sqlalchemy.orm import Session
from ..models import DenemeTakvim, Kitap

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _tarih(s: str | None) -> date | None:
    if not s:
        return None
    return date.fromisoformat(s)


def takvim_seed_yukle(db: Session) -> int:
    with open(os.path.join(DATA, "deneme_takvimi_2026_27.json"), encoding="utf-8") as f:
        denemeler = json.load(f)["denemeler"]
    eklenen = 0
    gecerli_kodlar = set()
    for d in denemeler:
        gecerli_kodlar.add(d["id"])
        var = db.query(DenemeTakvim).filter_by(kod=d["id"]).first()
        if var:
            # JSON'daki bilgileri mevcut satira isle (guncelleme)
            var.ad = d["ad"]; var.segment = d["segment"]; var.yayin = d.get("yayin", "")
            var.tarih = _tarih(d["tarih"]); var.bitis = _tarih(d.get("bitis"))
            var.basvuru_son = _tarih(d.get("basvuru_son"))
            var.erken_uyari_gun = d.get("erken_uyari_gun", 7)
            var.dogrulama_durumu = d.get("dogrulama_durumu", var.dogrulama_durumu)
            var.kaynak_url = d.get("kaynak_url", var.kaynak_url or "-")
            continue
        db.add(DenemeTakvim(kod=d["id"], ad=d["ad"], segment=d["segment"], yayin=d.get("yayin", ""),
                             tarih=_tarih(d["tarih"]), bitis=_tarih(d.get("bitis")),
                             basvuru_son=_tarih(d.get("basvuru_son")),
                             erken_uyari_gun=d.get("erken_uyari_gun", 7),
                             dogrulama_durumu=d.get("dogrulama_durumu", "taslak-yayinci-teyidi-gerekir"),
                             kaynak_url=d.get("kaynak_url", "-")))
        eklenen += 1
    # kaldirilan eski seed satirlarini temizle (or. TG-01..TG-12)
    db.query(DenemeTakvim).filter(DenemeTakvim.kod.notin_(gecerli_kodlar)).delete(synchronize_session=False)
    db.commit()
    return eklenen


def katalog_seed_yukle(db: Session) -> int:
    with open(os.path.join(DATA, "kitap_katalog.json"), encoding="utf-8") as f:
        kitaplar = json.load(f)["kitaplar"]
    eklenen = 0
    for k in kitaplar:
        var = db.query(Kitap).filter_by(katalog_id=k["id"]).first()
        if var:
            var.isbn = k.get("isbn", var.isbn)
            var.isbn_durum = k.get("isbn_durum", var.isbn_durum or "yer-tutucu-dogrulanmadi")
            continue
        db.add(Kitap(katalog_id=k["id"], isbn=k.get("isbn", ""),
                     isbn_durum=k.get("isbn_durum", "yer-tutucu-dogrulanmadi"),
                     baslik=k["baslik"],
                     yazar=k.get("yazar", ""), yayin=k.get("yayin", ""), tur=k.get("tur", ""),
                     seviye=k.get("seviye", "orta"), dersler=k.get("dersler", []),
                     aciklama=k.get("aciklama", ""), maarif=k.get("maarif", [])))
        eklenen += 1
    db.commit()
    return eklenen
