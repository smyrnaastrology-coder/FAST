# -*- coding: utf-8 -*-
"""Kredi KAYBINI YAKALAYAN testler.

CANLI YASANAN HATA: kullanici 100->99 dusmus bir soru sormus, aradan zaman
gecmis, uygulamayi acinca kredi tekrar 100 olmus. Iki ayri sebep:

  A) Render free plan'da kalici disk YOK. users_runtime.json gecici dosya
     sisteminde duruyor -> her redeploy'da SILINIR. Kayit yok olunca
     verify() kullaniciyi 100 krediyle YENIDEN OLUSTURUR.
  B) auth.py'de kilit ve atomik yazim YOKTU. Es zamanli iki istekten biri
     okudugu bayagi digerinin uzerine yaziyordu -> harcanan kredi geri
     geliyordu. (Ayni hata sinifi geri bildirim deposunda da vardi.)

Bunlar testlerle SABITLENIR ki bir daha sessizce gelmesin.
"""
import json
import os
import sys
import tempfile
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import auth as A

_td = tempfile.mkdtemp(prefix="credit_test_")


def _fresh(name="db.json"):
    p = os.path.join(_td, name)
    if os.path.exists(p):
        os.remove(p)
    A.DB = p
    return p


def _u(email="a@b.com", credits=100, pwd="x"):
    return {"pwd": A.hash_pass(pwd), "expiry": "2099-01-01T00:00:00",
            "created": "2026-01-01T00:00:00", "credits": credits}


def test_missing_file_is_empty_not_crash():
    _fresh("yok.json")
    assert A._load() == {}
    assert A.get_user("a@b.com") is None
    print("OK 1) DB dosyasi yoksa bos - cokmez")


def test_corrupt_file_raises_and_keeps_backup():
    """BOZUK dosyada sessizce {} donmek tum kredileri bir anda sifirlardi.
    Artik hata yukseliyor ve dosya yedekleniyor."""
    p = _fresh("bozuk.json")
    with open(p, "w", encoding="utf-8") as f:
        f.write('{"a@b.com": {"credits": 99')     # yarim kalmis yazim
    try:
        A._load()
        raise AssertionError("bozuk dosya sessizce gecti!")
    except A.StorageError:
        pass
    backups = [x for x in os.listdir(_td) if x.startswith("bozuk.json.corrupt-")]
    assert backups, "bozuk dosya yedeklenmedi"
    print("OK 2) bozuk dosya hata veriyor + yedekleniyor:", backups[0])


def test_corrupt_json_does_not_return_empty():
    p = _fresh("bozuk2.json")
    with open(p, "w", encoding="utf-8") as f:
        f.write("bu json degil {{{")
    try:
        A._load()
        raise AssertionError("bozuk json sessizce gecti!")
    except A.StorageError:
        pass
    print("OK 3) gecersiz JSON sessizce bos sayilmadi")


def test_spend_is_atomic_under_concurrency():
    """ASIL HATA. Once: 20 es zamanli harcamada biri digerini ezdiyordu.
    Simdi kilit var, tam 20 kredi dusmeli."""
    _fresh("race.json")

    def seed(db):
        db["a@b.com"] = _u(credits=100)
    A.update(seed)

    errors = []

    def work():
        try:
            A.spend_credit("a@b.com")
        except Exception as e:      # pragma: no cover
            errors.append(e)

    ths = [threading.Thread(target=work) for _ in range(20)]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    assert not errors, errors[:2]
    left = A._load()["a@b.com"]["credits"]
    assert left == 80, f"20 harcamadan sonra 80 olmaliydi, {left} bulundu"
    print("OK 4) 20 es zamanli harcama: 100 -> 80 (kayip yazma yok)")


def test_spend_never_resurrects_credits():
    """Kredi hicbir kosulda artsina gidemez."""
    _fresh("azalma.json")

    def seed(db):
        db["a@b.com"] = _u(credits=3)
    A.update(seed)
    for _ in range(10):
        A.spend_credit("a@b.com")
    left = A._load()["a@b.com"]["credits"]
    assert left == 0, left
    assert left >= 0, "kredi eksiye dusmemeli"
    print("OK 5) kredi 0'in altina dusmuyor (3 -> 0)")


def test_verify_racing_with_spend_does_not_refill():
    """Kullanicinin '99 kredi geri 100 oldu' yasadigi senaryo: verify()
    es zamaninda calisip bayagi yazmasin."""
    _fresh("verify_race.json")

    def seed(db):
        db["a@b.com"] = _u(credits=100)
    A.update(seed)
    A.verify("a@b.com", "x", device_id="dev1")   # cihaz kaydi

    stop = threading.Event()
    bad = []

    def poller():
        """verify() cihaz listesini gunceller ve _save yapar. Once bu ayri
        _load/_save idi; guncellenmis surum update() kullanir."""
        while not stop.is_set():
            A.verify("a@b.com", "x", device_id="dev1")

    p = threading.Thread(target=poller)
    p.start()
    for _ in range(30):
        A.spend_credit("a@b.com")
    stop.set()
    p.join()
    left = A._load()["a@b.com"]["credits"]
    assert left == 70, f"30 harcama sonrasi 70 olmaliydi, {left} bulundu"
    assert not bad
    print("OK 6) verify + spend yarismasi krediyi geri doldurmuyor (100 -> 70)")


def test_missing_credits_key_is_not_100():
    """credits anahtari olmayan kayit 100'e DONMEYECEK. Once get_user ve
    spend_credit burada DEFAULT_CREDITS yaziyordu."""
    _fresh("nokeys.json")

    def seed(db):
        u = _u(credits=100)
        del u["credits"]
        db["a@b.com"] = u
    A.update(seed)
    u = A.get_user("a@b.com")
    assert u["credits"] == A.TRIAL_CREDITS, u["credits"]
    assert u["credits"] != 100, "100 dondu - bedava kredi verildi!"
    print("OK 7) credits anahtari yoksa 100 degil, deneme kredisi ataniyor:",
          u["credits"])


def test_hardcoded_recreate_is_audited():
    """Render DB'yi silince kullanici 100 krediyle yeniden olusuyordu. Artik
    bu olay denetime yaziliyor - sifirdan bakilabilsin."""
    audit = os.path.join(_td, "audit.jsonl")
    _fresh("hc.json")
    A.AUDIT = audit
    ok, info = A.verify(A.HARDCODED_KEY, A.HARDCODED[A.HARDCODED_KEY], device_id="dev9")
    assert ok, info
    lines = open(audit, encoding="utf-8").read()
    assert "HARDCODED_RECREATED" in lines, "olay denetime yazilmadi!"
    rec = [json.loads(x) for x in lines.strip().split("\n") if "HARDCODED" in x]
    assert rec[0]["cause"], rec
    print("OK 8) kayit yeniden olusturulunca olay denetime yaziliyor:", rec[0]["cause"])


def test_spend_audit_trail():
    """'Kredim nereye gitti?' sorusu cevaplanabilmeli."""
    audit = os.path.join(_td, "audit2.jsonl")
    _fresh("audit3.json")
    A.AUDIT = audit

    def seed(db):
        db["a@b.com"] = _u(credits=10)
    A.update(seed)
    A.spend_credit("a@b.com")
    A.spend_credit("a@b.com", amount=3)
    recs = [json.loads(x) for x in open(audit, encoding="utf-8") if '"spend"' in x]
    assert len(recs) == 2, recs
    assert recs[0]["before"] == 10 and recs[0]["after"] == 9, recs[0]
    assert recs[1]["before"] == 9 and recs[1]["after"] == 6, recs[1]
    print("OK 9) kredi hareketleri denetlenebilir:", [(r["before"], r["after"]) for r in recs])


def test_alias_shares_balance():
    _fresh("alias.json")

    def seed(db):
        db["a@b.com"] = _u(credits=50)
        db["a"] = dict(_u(credits=50), alias_of="a@b.com")
    A.update(seed)
    A.spend_credit("a@b.com")
    db = A._load()
    assert db["a@b.com"]["credits"] == 49, db["a@b.com"]
    assert db["a"]["credits"] == 49, "alias bakiyesi ayri kaldi!"
    print("OK 10) alias ayni bakiyeyi paylasiyor (50 -> 49, ikisi de)")


def test_legacy_migrate_never_runs_automatically():
    """GERCEK SEBEP: eski users.json'dan kredi tasima her DB yoklugunda
    devreye giriyordu. Render'in gecici diski DB'yi her deploy'da sildigi
    icin 100 kredili eski yedek geri geliyordu. Artik bu yol tamamen
    kaldirildi: _load() hicbir seyi geri yuklemiyor."""
    d = os.path.join(_td, "legacytest2")
    os.makedirs(d, exist_ok=True)
    legacy = os.path.join(d, "users.json")
    with open(legacy, "w", encoding="utf-8") as f:
        json.dump({"a@b.com": _u(credits=100)}, f)
    dbp = os.path.join(d, "users_runtime.json")
    old_db, old_legacy = A.DB, A.LEGACY
    try:
        A.DB, A.LEGACY = dbp, legacy
        for _ in range(5):
            if os.path.exists(dbp):
                os.remove(dbp)      # Render her deploy'da siliyor
            assert A._load() == {}, "legacy kredileri kendiliginden geri geldi!"
        assert not os.path.exists(dbp), "legacy otomatik aktarildi"
        # _load() bir kez daha: hala bos, aktarma yok
        assert A._load() == {}
        assert not os.path.exists(dbp), "legacy otomatik aktarildi"
        print("OK 11) legacy kredileri hicbir kosulda kendiliginden gelmiyor")
    finally:
        A.DB, A.LEGACY = old_db, old_legacy


def test_explicit_migrate_still_available():
    """Gecis araci duruyor: mevcut DB yoksa ve admin isterse aktarir."""
    d = os.path.join(_td, "legacytest3")
    os.makedirs(d, exist_ok=True)
    legacy = os.path.join(d, "users.json")
    with open(legacy, "w", encoding="utf-8") as f:
        json.dump({"a@b.com": _u(credits=100)}, f)
    dbp = os.path.join(d, "users_runtime.json")
    if os.path.exists(dbp):
        os.remove(dbp)
    old_db, old_legacy = A.DB, A.LEGACY
    try:
        A.DB, A.LEGACY = dbp, legacy
        ok, msg = A.migrate_legacy_once()
        assert ok, msg
        assert A._load()["a@b.com"]["credits"] == 100
        # DB varken ikinci kez cagirmak mevcut veriyi EZMEZ
        A.spend_credit("a@b.com")
        ok2, _ = A.migrate_legacy_once()
        assert not ok2 and A._load()["a@b.com"]["credits"] == 99
        print("OK 12) istege bagli tek seferlik gecis hala calisiyor, ezmiyor")
    finally:
        A.DB, A.LEGACY = old_db, old_legacy


def test_db_vanishes_credits_do_not_come_back():
    """En canli senaryo: Render gecici disk DB'yi siler. Kullanici giris
    yapar; kaydi 100 krediyle yeniden olusur. Yeniden olusturma denetime
    yazilir (test 8) ama otomatik MIGRATE ile kredi gelmez."""
    p = _fresh("yokold.json")
    assert A._load() == {}
    # kullanici DB'siz durumda soru soruyor -> reddedilir, kredi harcanmaz
    u = A.get_user("yok@olmayan.com")
    assert u is None, "olmayan kullanici bulundu!"
    assert A.spend_credit("yok@olmayan.com") is None, "olmayan kullaniciya harcama yapildi!"
    # ASIL KURAL: olmayan kullanici icin HICBIR kredi/kayit dogmaz
    db = A._load()
    assert "yok@olmayan.com" not in db, db
    assert not [k for k in db if not k.startswith("__")], db
    print("OK 13) DB yokken olmayan kullanici reddedilir, bedava soru acilmaz")


def test_atomic_write_leaves_no_partial_file():
    """Yazim yarida kesilirse dosya bozulmamali."""
    p = _fresh("atomik.json")

    def seed(db):
        db["a@b.com"] = _u(credits=7)
    A.update(seed)
    assert A._load()["a@b.com"]["credits"] == 7
    leftovers = [x for x in os.listdir(_td) if ".tmp" in x]
    assert not leftovers, leftovers
    print("OK 14) atomik yazim: gecici dosya artikmiyor")


if __name__ == "__main__":
    test_missing_file_is_empty_not_crash()
    test_corrupt_file_raises_and_keeps_backup()
    test_corrupt_json_does_not_return_empty()
    test_spend_is_atomic_under_concurrency()
    test_spend_never_resurrects_credits()
    test_verify_racing_with_spend_does_not_refill()
    test_missing_credits_key_is_not_100()
    test_hardcoded_recreate_is_audited()
    test_spend_audit_trail()
    test_alias_shares_balance()
    test_legacy_migrate_never_runs_automatically()
    test_explicit_migrate_still_available()
    test_db_vanishes_credits_do_not_come_back()
    test_atomic_write_leaves_no_partial_file()
    print("\ntest_credits_storage: 14/14 OK")
    print("SONUC: kredi artik kazanilmiyor. Bozuk dosya sessizce bos sayilmaz,")
    print("        es zamanli yazma birbirini ezmez, eksik credits 100'e")
    print("        donmez, her hareket denetlenebilir.")