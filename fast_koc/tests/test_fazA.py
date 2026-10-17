import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["AUTH_ZORUNLU"] = "false"
os.environ["ODEME_ZORUNLU"] = "false"
from datetime import date, datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, init_db
from backend import models
from backend.services import bildirim_servisi

init_db()
client = TestClient(app)


def _profil(ad="FazA Ogr"):
    r = client.post("/api/profil", json={"ad": ad, "rol": "ogrenci", "segment": "YKS", "seviye": "orta"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_health_db_ping():
    r = client.get("/api/health")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True and j["db"] is True


def test_cors_header():
    r = client.get("/api/health", headers={"Origin": "https://example.com"})
    # varsayilan "*" -> Access-Control-Allow-Origin "*"
    assert r.headers.get("access-control-allow-origin") in ("*", "https://example.com")


def test_bildirim_get_salt_okunur():
    oid = _profil("FazA Bildirim")
    r1 = client.get(f"/api/bildirim/{oid}")
    assert r1.status_code == 200
    j1 = r1.json()
    assert "bildirimler" in j1 and "okunmamis" in j1
    # ikinci cagri yeni bildirim URETMEMELI (salt okunur)
    r2 = client.get(f"/api/bildirim/{oid}")
    assert len(r2.json()["bildirimler"]) == len(j1["bildirimler"])


def test_gun_sonu_dedup():
    db = SessionLocal()
    try:
        pr = models.Profile(ad="FazA Dedup", segment="YKS_ESKI")
        db.add(pr); db.commit(); db.refresh(pr)
        a = bildirim_servisi.gun_sonu_hatirlatma_uret(db, pr.id)
        b = bildirim_servisi.gun_sonu_hatirlatma_uret(db, pr.id)
        assert a.id == b.id  # ayni gun tekrar uretilmez
        sayi = db.query(models.Bildirim).filter_by(ogrenci_id=pr.id, tip="gun_sonu").count()
        assert sayi == 1
    finally:
        db.close()


def test_bildirim_oku_endpoint():
    db = SessionLocal()
    try:
        pr = models.Profile(ad="FazA Oku", segment="YKS_ESKI")
        db.add(pr); db.commit(); db.refresh(pr)
        b = bildirim_servisi.gun_sonu_hatirlatma_uret(db, pr.id)
        bid = b.id
    finally:
        db.close()
    r = client.post(f"/api/bildirim/{bid}/oku")
    assert r.status_code == 200 and r.json()["okundu"] is True
    r404 = client.post("/api/bildirim/99999999/oku")
    assert r404.status_code == 404


def test_gunluk_unique_constraint():
    db = SessionLocal()
    try:
        pr = models.Profile(ad="FazA Gunluk", segment="YKS_ESKI")
        db.add(pr); db.commit(); db.refresh(pr)
        # API upsert: ayni tarih icin tek kayit
        for soru in (10, 25):
            r = client.post("/api/gunluk", json={"ogrenci_id": pr.id, "tarih": date.today().isoformat(),
                                                 "cozulen_soru": soru, "calisilan_dk": 60, "notlar": ""})
            assert r.status_code == 200
        n = db.query(models.GunlukLog).filter_by(ogrenci_id=pr.id, tarih=date.today()).count()
        assert n == 1
    finally:
        db.close()


def test_baglanti_dedup():
    db = SessionLocal()
    try:
        o = models.Profile(ad="FazA O", segment="YKS_ESKI"); db.add(o)
        k = models.Profile(ad="FazA K", rol="koc", segment="YKS_ESKI"); db.add(k)
        db.commit(); db.refresh(o); db.refresh(k)
        for _ in range(2):
            r = client.post("/api/baglanti", json={"ogrenci_id": o.id, "sahip_id": k.id, "rol": "koc"})
            assert r.status_code == 200
        n = db.query(models.Baglanti).filter_by(ogrenci_id=o.id, sahip_id=k.id).count()
        assert n == 1
    finally:
        db.close()
