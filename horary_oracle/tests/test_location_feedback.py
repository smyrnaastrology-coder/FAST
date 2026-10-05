# -*- coding: utf-8 -*-
"""Geri bildirim -> motor besleme testleri.

Kritik kurallar:
  1. Jeton imzali: kimse rastgele veri enjekte edemez
  2. Jeton suresi dolunca gecersiz
  3. Geri bildirim yaniti/KALIBRASYONU degistirmez
  4. 'Bulamadim' da veridir (yon tutmadi)
  5. Gercek basari orani olculebilir
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from engine import location_feedback as FB

# Modulun GERCEK varsayilan deposu (testler gecici depoya yaziyor, ama
# varsayilanin dogru dosya olup olmadigini da denetlememiz lazim).
_DEFAULT_STORE = FB.STORE

# testler gecici depoya yazsin, gercek veriye dokunmadan
_tmp = os.path.join(tempfile.gettempdir(), "fb_test_store.json")
FB.STORE = _tmp
if os.path.exists(_tmp):
    os.remove(_tmp)


def test_token_roundtrip():
    t = FB.make_token("a@b.com", "Kalemim nerde?", "lost_object", 38.42, 27.14, "Kuzeydoğu")
    d = FB.read_token(t)
    assert d is not None, "jeton okunamadi"
    assert d["e"] == "a@b.com"
    assert d["t"] == "lost_object"
    assert d["dir"] == "Kuzeydoğu", d
    print("OK 1) jeton gidis-donus calisiyor")


def test_token_tampered():
    t = FB.make_token("a@b.com", "q", "lost_object", 1, 2)
    bad = t[:-4] + "0000"
    assert FB.read_token(bad) is None, "kurcalanmis jeton kabul edildi!"
    assert FB.read_token(t[:-1] + ("0" if t[-1] != "0" else "1")) is None
    print("OK 2) kurcalanmis jeton reddediliyor (imza)")


def test_token_no_signature():
    assert FB.read_token("abc") is None
    assert FB.read_token("") is None
    assert FB.read_token("a.b") is None
    print("OK 3) imzasiz/bozuk jeton reddediliyor")


def test_token_expiry():
    import time as _t
    old = int(_t.time()) - 10 * 3600          # 10 saat once (TTL 6 saat)
    body = FB._b64e({"e": "x@y.com", "q": "q", "t": "lost_object",
                     "lat": 1, "lon": 2, "dir": "", "ts": old})
    import hmac as _h, hashlib as _hsh
    sig = _h.new(FB._secret().encode(), body.encode(), _hsh.sha256).hexdigest()[:32]
    assert FB.read_token(f"{body}.{sig}") is None, "sure dolmus jeton kabul edildi!"
    print("OK 4) 6 saatten eski jeton reddediliyor")


def test_record_found_and_miss():
    FB.record("a@b.com", "Kalemim nerde?", "lost_object", "found",
              found_where="salon, koltuk altı", predicted_dir="Kuzeydoğu")
    FB.record("a@b.com", "Anahtarım nerde?", "lost_object", "not_found",
              predicted_dir="Batı", recast="Mutfak, giyinme odası")
    st = FB.stats("lost_object")
    assert st["n"] == 2, st
    assert st["found"] == 1 and st["not_found"] == 1, st
    assert st["hit_rate"] == 0.5, st
    print("OK 5) 'buldum' ve 'bulamadim' ikisi de kayit, hit_rate=0.5")


def test_miss_is_also_data():
    """'Bulamadim' cevabi yon tutmadi demek - bu da olcum."""
    FB.record("b@b.com", "Cüzdanım nerde?", "lost_object", "not_found",
              predicted_dir="Güney")
    s = FB.stats("lost_object")
    assert s["n"] == 3 and s["found"] == 1
    assert s["not_found"] == 2
    print("OK 6) 'bulamadim' de veri olarak birikiyor (n=3, found=1)")


def test_by_type_breakdown():
    FB.record("c@b.com", "İşe girecek miyim?", "job", "found")
    bt = FB.stats()["by_type"]
    assert "lost_object" in bt and "job" in bt, bt
    assert bt["job"]["found"] == 1
    print("OK 7) soru tipine gore kırılım:", {k: v["n"] for k, v in bt.items()})


def test_hit_rate_none_when_empty():
    FB.STORE = os.path.join(tempfile.gettempdir(), "fb_empty_store.json")
    if os.path.exists(FB.STORE):
        os.remove(FB.STORE)
    st = FB.stats("hic_boyle_bir_tip")
    assert st["n"] == 0 and st["hit_rate"] is None
    print("OK 8) veri yokken hit_rate None (yanlis '0%' gostermez)")


def test_no_calibration_mutation():
    """Geri bildirim kalibrasyon dosyasina DOKUNMAMALI."""
    FB.STORE = _tmp
    cal_before = None
    import hashlib as _hs
    cal_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "horary_calibration.json")
    if os.path.exists(cal_path):
        with open(cal_path, "rb") as f:
            cal_before = _hs.sha256(f.read()).hexdigest()
    FB.record("d@b.com", "Kalem nerde?", "lost_object", "found", found_where="mutfak")
    FB.record("d@b.com", "Kalem nerde?", "lost_object", "not_found")
    if cal_before:
        with open(cal_path, "rb") as f:
            after = _hs.sha256(f.read()).hexdigest()
        assert cal_before == after, "geri bildirim kalibrasyonu degistirdi!"
    print("OK 9) geri bildirim kalibrasyon dosyasini degistirmiyor")


def test_store_json_valid():
    with open(_tmp, "r", encoding="utf-8") as f:
        db = json.load(f)
    assert "entries" in db and isinstance(db["entries"], list)
    assert db["entries"], "kayitlar yazilmadi"
    e = db["entries"][0]
    for k in ("ts", "question", "outcome"):
        assert k in e, k
    print(f"OK 10) depo gecerli JSON, {len(db['entries'])} kayit")


def test_store_not_shared_with_legacy_list():
    """Konum geri bildirimi ESKI is-sonucu geri bildirim dosyasiyla ayni
    dosyaya yazmamali. O dosya JSON LISTESidir ve farkli sema kullanir; ayni
    dosyaya yazmak ya veriyi bozar ya da yazmayi AttributeError ile engeller."""
    import engine.location_feedback as M
    real = _DEFAULT_STORE
    assert os.path.basename(real) == "horary_location_feedback.json", real
    assert real != os.path.join(os.path.dirname(real), "horary_feedback.json")
    print("OK 11) konum geri bildirimi ayri depoda:", os.path.basename(real))


def test_legacy_list_file_does_not_crash():
    """Depo yanlislikla JSON listesi olsa bile cokmemeli, sessizce bos baslamali."""
    import importlib
    import engine.location_feedback as M
    legacy = os.path.join(tempfile.gettempdir(), "fb_legacy_list.json")
    with open(legacy, "w", encoding="utf-8") as f:
        json.dump([{"question": "eski kayit", "predicted": {}}], f)
    old = M.STORE
    try:
        M.STORE = legacy
        db = M._load()
        assert isinstance(db, dict), type(db)
        assert db["entries"] == []
        n = M.record("e@x.com", "q", "lost_object", "found")
        assert n == 1, n
    finally:
        M.STORE = old
        if os.path.exists(legacy):
            os.remove(legacy)
    print("OK 12) eski liste bicimi cokmeden bos basliyor")


def test_token_is_single_use():
    """Kritik: ayni jeton iki kez gonderilemez. Aksi halde tek bir cevap
    binlerce sahte kayit uretir ve motoru bozabilir."""
    import engine.location_feedback as M
    old = M.STORE
    single = os.path.join(tempfile.gettempdir(), "fb_single_use.json")
    try:
        M.STORE = single
        if os.path.exists(single):
            os.remove(single)
        t = M.make_token("a@b.com", "Kalemim nerde?", "lost_object", 38.4, 27.1, "Kuzey")
        ok1, info1 = M.submit(t, found=True, found_where="salon")
        assert ok1, info1
        assert info1["saved"] == 1, info1
        ok2, info2 = M.submit(t, found=True, found_where="salon")
        assert not ok2, "AYNI JETON IKINCE KABUL EDILDI!"
        assert "kullanildi" in info2["error"], info2
        assert M.stats()["n"] == 1, "replay kaydi eklenmis"
        print("OK 13) jeton tek kullanimlik (replay reddedildi)")
    finally:
        M.STORE = old
        if os.path.exists(single):
            os.remove(single)


def test_submit_rejects_bad_token_without_writing():
    """Bozuk jeton HICBIR sey yazmamali."""
    import engine.location_feedback as M
    old = M.STORE
    single = os.path.join(tempfile.gettempdir(), "fb_reject.json")
    try:
        M.STORE = single
        ok, info = M.submit("sahte.jeton", found=True)
        assert not ok and info.get("error"), info
        assert not os.path.exists(single), "gecersiz jetonla dosya olustu!"
        assert M.stats()["n"] == 0
        print("OK 14) gecersiz jeton kayit yazmiyor")
    finally:
        M.STORE = old
        if os.path.exists(single):
            os.remove(single)


def test_submit_records_real_question_type():
    """Streamlit eskiden her seyi 'lost_object' yaziyordu; tip basina basari
    orani bu yuzden bozuluyordu. submit jetondan gelen gercek tipi yazmali."""
    import engine.location_feedback as M
    old = M.STORE
    single = os.path.join(tempfile.gettempdir(), "fb_qtype.json")
    try:
        M.STORE = single
        for qt in ("child", "job", "lost_object"):
            t = M.make_token("a@b.com", "soru", qt, 38.4, 27.1, "K")
            assert M.submit(t, found=True)[0]
        bt = M.stats()["by_type"]
        assert set(bt) == {"child", "job", "lost_object"}, bt
        assert bt["child"]["n"] == 1 and bt["job"]["n"] == 1, bt
        print("OK 15) gercek soru tipi kaydediliyor:", sorted(bt))
    finally:
        M.STORE = old
        if os.path.exists(single):
            os.remove(single)


def test_concurrent_submit_no_lost_writes():
    """Iki istek ayni anda gelirse biri digerinin kaydini EZMEMELI.
    (Kilidi olmayan eski surumde 'son yazan kazanir' -> veri kaybi.)"""
    import threading
    import engine.location_feedback as M
    old = M.STORE
    conc = os.path.join(tempfile.gettempdir(), "fb_concurrent.json")
    try:
        M.STORE = conc
        if os.path.exists(conc):
            os.remove(conc)
        tokens = [M.make_token(f"u{i}@b.com", "q", "lost_object", 38.4, 27.1, "K")
                  for i in range(20)]
        results = []
        lock = threading.Lock()

        def work(tk):
            r = M.submit(tk, found=True, found_where="x")
            with lock:
                results.append(r[0])

        ths = [threading.Thread(target=work, args=(t,)) for t in tokens]
        for t in ths:
            t.start()
        for t in ths:
            t.join()
        assert all(results), f"{results.count(False)} basarisiz"
        assert M.stats()["n"] == 20, M.stats()["n"]
        print("OK 16) es zamanli 20 gonderim, 20 kayit (kayip yok)")
    finally:
        M.STORE = old
        if os.path.exists(conc):
            os.remove(conc)


if __name__ == "__main__":
    test_token_roundtrip()
    test_token_tampered()
    test_token_no_signature()
    test_token_expiry()
    test_record_found_and_miss()
    test_miss_is_also_data()
    test_by_type_breakdown()
    test_hit_rate_none_when_empty()
    test_no_calibration_mutation()
    test_store_json_valid()
    test_store_not_shared_with_legacy_list()
    test_legacy_list_file_does_not_crash()
    test_token_is_single_use()
    test_submit_rejects_bad_token_without_writing()
    test_submit_records_real_question_type()
    test_concurrent_submit_no_lost_writes()
    os.remove(_tmp)
    print("\ntest_location_feedback: 16/16 OK")
    print("SONUC: geri bildirim guvenli (imzali + TEK KULLANIMLI jeton), eski veri")
    print("        dosyasiyla paylasmaz, kalibrasyonu degistirmez, es zamanli")
    print("        yazmalarda kayit kaybolmaz, gercek soru tipiyle olculur.")