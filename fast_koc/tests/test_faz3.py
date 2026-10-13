import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["AUTH_ZORUNLU"] = "false"
os.environ["ODEME_ZORUNLU"] = "false"
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, init_db
from backend import models

init_db()
client = TestClient(app)


def _profil(ad="Faz3 Ogr", rol="ogrenci"):
    r = client.post("/api/profil", json={"ad": ad, "rol": rol, "segment": "YKS", "seviye": "orta"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_auth_me_anonim():
    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["sub"] == "anonim"


def test_baglanti_ve_koc_paneli():
    oid = _profil("Faz3 Ogrenci")
    kid = _profil("Faz3 Koc", "koc")
    r = client.post("/api/baglanti", json={"ogrenci_id": oid, "sahip_id": kid, "rol": "koc"})
    assert r.status_code == 200
    r = client.get(f"/api/koc/{kid}/ogrenciler")
    assert r.status_code == 200
    assert any(o["id"] == oid for o in r.json()["ogrenciler"])


def test_cihaz_ve_push_kuyrugu_offline():
    oid = _profil("Faz3 Push")
    r = client.post("/api/cihaz", json={"ogrenci_id": oid, "fcm_token": "test-token-faz3", "platform": "android"})
    assert r.status_code == 200
    r = client.post(f"/api/push/{oid}", params={"metin": "test push"})
    assert r.status_code == 200
    assert r.json()["bildirim_id"] > 0
    # FCM anahtari yok -> gonderildi 0, ama kuyruk acildi
    assert r.json()["gonderildi"] == 0


def test_odeme_stub_akisi():
    oid = _profil("Faz3 Pro")
    r = client.get(f"/api/plan/{oid}")
    assert r.json()["plan"] == "ucretsiz"
    r = client.post(f"/api/odeme/checkout/{oid}")
    assert r.status_code == 200
    assert r.json()["mod"] == "stub"  # STRIPE_SECRET_KEY yok
    r = client.post(f"/api/odeme/aktif/{oid}", params={"session_id": "test"})
    assert r.status_code == 200
    r = client.get(f"/api/plan/{oid}")
    assert r.json()["plan"] == "pro"
