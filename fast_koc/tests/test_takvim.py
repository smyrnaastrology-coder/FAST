import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal, init_db
from backend.services.takvim_seed import takvim_seed_yukle


def test_takvim_gercek_veri():
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "backend", "data", "deneme_takvimi_2026_27.json"), encoding="utf-8") as f:
        veri = json.load(f)["denemeler"]
    assert len(veri) >= 40, len(veri)
    mebi_yks = [d for d in veri if d["id"].startswith("MEBI-YKS")]
    mebi_lgs = [d for d in veri if d["id"].startswith("MEBI-LGS")]
    assert len(mebi_yks) == 12
    assert len(mebi_lgs) == 10
    assert all(d["dogrulama_durumu"] == "dogrulandi-meb-resmi" for d in mebi_yks + mebi_lgs)
    assert all(d.get("bitis") for d in mebi_yks + mebi_lgs)
    maarif = [d for d in veri if d["id"] == "4K-MAARIF-TYT"]
    assert maarif and maarif[0]["segment"] == "YKS_MAARIF"


def test_takvim_seed_guncel_idempotent():
    init_db()
    db = SessionLocal()
    try:
        takvim_seed_yukle(db)
        ikinci = takvim_seed_yukle(db)
        assert ikinci == 0
        from backend.models import DenemeTakvim
        assert db.query(DenemeTakvim).count() >= 40
        assert db.query(DenemeTakvim).filter_by(kod="TG-01").first() is None  # eski seed temizlendi
        m1 = db.query(DenemeTakvim).filter_by(kod="MEBI-YKS-01").first()
        assert m1 is not None and m1.bitis is not None
    finally:
        db.close()
