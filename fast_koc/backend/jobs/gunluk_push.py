"""Zamanlanmis gunluk push isi (Faz 3). Cron ornegi: 30 21 * * * cd /app/fast_koc && python -m backend.jobs.gunluk_push"""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from datetime import date
from backend.database import SessionLocal, init_db
from backend.models import Profile, GunlukLog
from backend.services import bildirim_servisi
from backend.services.push_servisi import push_gonder


def main() -> dict:
    init_db()
    db = SessionLocal()
    try:
        erken = bildirim_servisi.erken_uyari_tara(db)
        gun_sonu = 0
        pushlar = 0
        for pr in db.query(Profile).filter_by(rol="ogrenci").all():
            var = db.query(GunlukLog).filter_by(ogrenci_id=pr.id, tarih=date.today()).first()
            if not var:
                bildirim_servisi.gun_sonu_hatirlatma_uret(db, pr.id)
                gun_sonu += 1
                r = push_gonder(db, pr.id, "Fast Koç", "Bugünkü soru sayını girmeyi unutma! 1 dakikada bitiyor.")
                pushlar += r.get("gonderildi", 0)
        print(f"erken_uyari={erken} gun_sonu={gun_sonu} push_gonderildi={pushlar}")
        return {"erken_uyari": erken, "gun_sonu": gun_sonu, "push_gonderildi": pushlar}
    finally:
        db.close()


if __name__ == "__main__":
    main()
