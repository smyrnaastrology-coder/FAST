# -*- coding: utf-8 -*-
"""Kredi/hesap guvenligi testleri (test_credits.py).

Kapatilan acıklar:
1. cast'e email gondermeden (anonim) istek -> 401 + kredi harcanmaz
2. kayitli olmayan email ile istek -> 401
3. kredili kullanicida her soru 1 kredi dusurur, credits_left doner
4. kredisi biten kullanici -> 200 + verdict NO_CREDITS
5. credits anahtari olmayan eski kayit -> sınırsız sayılmaz (varsayilana düşer)
6. kredi DB'si git'e commit'li degil (deploy kredileri sıfırlamaz)
"""
import os
import sys
import json
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import auth  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
import api as api_mod  # noqa: E402

TEST_EMAIL = "test-kredi@asartepe.local"


def _reset_db(credits=5):
    db = auth._load()
    for k in list(db.keys()):
        if k == TEST_EMAIL:
            del db[k]
    db[TEST_EMAIL] = {
        "pwd": auth.hash_pass("pw"),
        "expiry": "2099-01-01T00:00:00",
        "created": "2026-01-01T00:00:00",
        "credits": credits,
    }
    auth._save(db)


def _cast(client, **over):
    payload = {"question": "Bu ise girecek miyim?", "lat": 41.0, "lon": 29.0, "lang": "tr"}
    payload.update(over)
    return client.post("/api/horary/cast", json=payload)


def test_cast_requires_login():
    _reset_db(5)
    c = TestClient(api_mod.app)
    r = _cast(c)  # email yok
    assert r.status_code == 401, r.text
    assert auth.get_user(TEST_EMAIL)["credits"] == 5, "401 kredi harcamamali"


def test_cast_rejects_unregistered_email():
    _reset_db(5)
    c = TestClient(api_mod.app)
    r = _cast(c, email="yok@olmayan.local")
    assert r.status_code == 401, r.text


def test_known_email_decrements_credit():
    _reset_db(5)
    c = TestClient(api_mod.app)
    r = _cast(c, email=TEST_EMAIL)
    assert r.status_code == 200, r.text
    assert r.json()["credits_left"] == 4, r.json().get("credits_left")
    assert auth.get_user(TEST_EMAIL)["credits"] == 4
    r2 = _cast(c, email=TEST_EMAIL)
    assert r2.json()["credits_left"] == 3
    assert auth.get_user(TEST_EMAIL)["credits"] == 3


def test_zero_credit_returns_no_credits_verdict():
    _reset_db(0)
    c = TestClient(api_mod.app)
    r = _cast(c, email=TEST_EMAIL)
    assert r.status_code == 200, r.text
    assert r.json()["verdict"] == "NO_CREDITS"
    assert r.json()["credits_left"] == 0


def test_missing_credit_key_is_not_unlimited():
    _reset_db(5)
    db = auth._load()
    db[TEST_EMAIL].pop("credits", None)
    auth._save(db)
    u = auth.get_user(TEST_EMAIL)
    assert u["credits"] == auth.DEFAULT_CREDITS, u
    assert u["credits"] < 10**9, "credits anahtari yoksa sınırsız sayılmamalı"


def test_trial_users_get_credit_balance():
    _reset_db(5)
    db = auth._load()
    del db[TEST_EMAIL]
    auth._save(db)
    auth.create_user(TEST_EMAIL, days=2)
    assert auth.get_user(TEST_EMAIL)["credits"] == auth.TRIAL_CREDITS


def test_alias_shares_balance():
    # kullaniciadi (alias) kaydi ayni bakiyeyi paylasmali
    alias = TEST_EMAIL.split("@")[0]
    _reset_db(5)
    db = auth._load()
    db[alias] = dict(db[TEST_EMAIL])
    db[alias]["alias_of"] = TEST_EMAIL
    auth._save(db)
    left = auth.spend_credit(TEST_EMAIL)
    assert left == 4, left
    assert auth._load()[alias]["credits"] == 4, "alias kendi kredisini koruyor -> sınırsız kazanç"
    left2 = auth.spend_credit(alias)
    assert left2 == 3, left2
    assert auth._load()[TEST_EMAIL]["credits"] == 3
    db = auth._load(); db.pop(alias, None); auth._save(db)


def test_greeting_does_not_consume_credit():
    # "merhaba" gibi selamlasma motor acmaz -> kredi harcanmamali
    _reset_db(5)
    c = TestClient(api_mod.app)
    r = c.post("/api/horary/cast", json={"question": "merhaba", "lat": 41.0, "lon": 29.0, "lang": "tr", "email": TEST_EMAIL})
    assert r.status_code == 200, r.text
    assert r.json()["verdict"] == "CHAT", r.json().get("verdict")
    assert auth.get_user(TEST_EMAIL)["credits"] == 5


def test_credit_db_not_tracked_by_git():
    # deploy'da kredilerin 100'e donmemesi icin DB git'te olmamali
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    try:
        out = subprocess.run(
            ["git", "-C", root, "ls-files", "horary_oracle/users.json", "horary_oracle/users_runtime.json"],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
    except Exception:
        return  # git yoksa sessiz gec
    assert out == "", "kredi DB'si git'e commit'li: %s" % out


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for fn in fns:
        try:
            fn()
            print("OK   %s" % fn.__name__)
            ok += 1
        except Exception as e:
            print("FAIL %s -> %s" % (fn.__name__, e))
    print("%d/%d gecti" % (ok, len(fns)))
    sys.exit(0 if ok == len(fns) else 1)
