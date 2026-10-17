"""Gun-sonu + erken-uyari uygulama-ici bildirim servisi (push yok, MVP)."""
from __future__ import annotations
from datetime import date, datetime
from sqlalchemy.orm import Session
from ..models import Bildirim, DenemeTakvim, GunlukLog, Odev


def gun_sonu_hatirlatma_uret(db: Session, ogrenci_id: int, tarih: date | None = None) -> Bildirim:
    tarih = tarih or date.today()
    # Ayni gun icin tekrar uretme (dedup): cron tekrar calissa da spam olmaz.
    bas = datetime.combine(tarih, datetime.min.time())
    son = datetime.combine(tarih, datetime.max.time())
    mevcut = db.query(Bildirim).filter(
        Bildirim.ogrenci_id == ogrenci_id,
        Bildirim.tip == "gun_sonu",
        Bildirim.tarih >= bas,
        Bildirim.tarih <= son,
    ).first()
    if mevcut:
        return mevcut
    var = db.query(GunlukLog).filter_by(ogrenci_id=ogrenci_id, tarih=tarih).first()
    if var:
        metin = "Bugunku kaydini guncelleyebilirsin. Cozdukce grafiklerin canlanacak."
    else:
        metin = "Gun sonu: bugun cozdugun soru sayisini ve calisma sureni gir. 1 dakikada bitiyor!"
    b = Bildirim(ogrenci_id=ogrenci_id, tip="gun_sonu", metin=metin)
    db.add(b); db.commit(); db.refresh(b)
    return b


def erken_uyari_tara(db: Session, bugun: date | None = None) -> int:
    """Yaklasan TG denemeler icin okunmamis uyari yoksa bildirim uretir. Donus: uretilen sayi."""
    from datetime import timedelta
    from ..engine import mufredat as muf
    bugun = bugun or date.today()
    uretilen = 0
    for d in db.query(DenemeTakvim).all():
        kalan = (d.tarih - bugun).days
        if 0 <= kalan <= (d.erken_uyari_gun or 7):
            # YKS varyantlari (ESKI/MAARIF) ayni TG'lere girer
            from ..models import Profile
            ogrenciler = db.query(Profile).all()
            hedefler = [o for o in ogrenciler if d.segment in muf.takvim_eslesme(o.segment or "")]
            for o in hedefler:
                var = db.query(Bildirim).filter(
                    Bildirim.ogrenci_id == o.id,
                    Bildirim.tip == "erken_uyari",
                    Bildirim.metin.like(f"%{d.kod}%"),
                    Bildirim.okundu == False,  # noqa: E712
                ).first()
                if var:
                    continue
                db.add(Bildirim(ogrenci_id=o.id, tip="erken_uyari",
                                metin=f"[{d.kod}] {d.ad} {d.tarih} tarihinde! {kalan} gun kaldi. Basvuru son: {d.basvuru_son or '-'}"))
                uretilen += 1
    db.commit()
    return uretilen
