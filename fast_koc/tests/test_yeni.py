import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from backend.engine.optik import optik_karsilastir
from backend.services.sms_servisi import telefon_normalize, sms_gonder
from backend.services.koc_yorumu import koc_yorumu_uret
from backend.database import SessionLocal, init_db


def test_optik_temel():
    r = optik_karsilastir("ABCDE", "ABCXE")
    assert (r["dogru"], r["yanlis"], r["bos"]) == (4, 0, 1)
    r2 = optik_karsilastir("ABCDE", "ABCXD")
    assert (r2["dogru"], r2["yanlis"], r2["bos"]) == (3, 1, 1)


def test_optik_uzunluk_hatasi():
    with pytest.raises(ValueError):
        optik_karsilastir("ABCDE", "ABCD")


def test_optik_gecersiz_harf():
    with pytest.raises(ValueError):
        optik_karsilastir("ABCDE", "ABCDF")


def test_telefon_normalize():
    assert telefon_normalize("0532 123 45 67") == "05321234567"
    assert telefon_normalize("905321234567") == "05321234567"
    with pytest.raises(ValueError):
        telefon_normalize("123")


def test_sms_kuyruk_offline():
    init_db()
    db = SessionLocal()
    try:
        from backend.models import Profile
        pr = Profile(ad="SMS Test", segment="YKS_ESKI")
        db.add(pr); db.commit(); db.refresh(pr)
        r = sms_gonder(db, pr.id, "05321234567", "Test mesajı")
        assert r["bildirim_id"] > 0
        assert r["gonderildi"] is False  # anahtar yok
    finally:
        db.close()


def test_koc_yorumu_sablon(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    analiz = {"genel_basari": 45.0, "ozet_cumle": "test",
              "oncelikli": [{"kod": "X", "baslik": "Problemler"}]}
    r = koc_yorumu_uret(analiz, ad="Ali", segment="YKS_ESKI")
    assert r["kaynak"] == "sablon"  # OPENAI_API_KEY yok
    assert "Problemler" in r["yorum"]
