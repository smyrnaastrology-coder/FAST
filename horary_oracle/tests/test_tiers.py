# -*- coding: utf-8 -*-
"""Yorum kaliteleri (engine.tiers) testleri - AG OLMAYAN sahte OpenAI istemcisi ile.

Kontrol edilenler:
1. Merdiven sirasi: local < basic < plus < pro (3 satilabilir kademe)
2. plan -> kademe eslemesi (eski plan adlari geriye donuk calisir)
3. Hata/bos metin durumunda BIR ALT kademeye dusulmesi
4. Tum kademeler basarisiz -> yerel deterministik metin
5. reasoning modellerine 'temperature' gonderilmiyor (Responses API)
6. anahtar yoksa yerel metne dusulmesi
7. Baslatilan kademeden ASLA ust kademeye atlanmamasi
8. O1 kaldirildi: hicbir kademede model adi icermiyor
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import engine.tiers as T

MODEL_TIER = {"gpt-4.1": "basic", "gpt-5.6-terra": "plus", "gpt-5.6-sol": "pro"}


class FakeClient:
    """chat.completions + responses.take; hangi kademenin ne dondugunu izler."""
    def __init__(self, behavior):
        self.behavior = behavior      # {tier_id: "ok" | "" | "raise"}
        self.calls = []               # ("chat"|"responses", model, kwargs)
        self.chat = _Chat(self)
        self.responses = _Responses(self)

    def _act(self, kind, model, kwargs):
        self.calls.append((kind, model, kwargs))
        tid = MODEL_TIER.get(model, "local")
        mode = self.behavior.get(tid, "ok")
        if mode == "raise":
            raise RuntimeError(f"{tid} simulasyon hatasi")
        if mode == "":
            return ""
        return f"{tid} metni"


class _Chat:
    def __init__(self, c):
        self.c = c
        self.completions = self

    def create(self, **kw):
        txt = self.c._act("chat", kw["model"], kw)
        msg = type("M", (), {"content": txt})()
        return type("R", (), {"choices": [type("C", (), {"message": msg})()]})()


class _Responses:
    def __init__(self, c):
        self.c = c

    def create(self, **kw):
        txt = self.c._act("responses", kw["model"], kw)
        return type("R", (), {"status": "completed", "output_text": txt})()


def _patch_client(behavior):
    fake = FakeClient(behavior)

    class _FakeOpenAI:
        def __init__(self, api_key=None):
            self.chat = fake.chat
            self.responses = fake.responses

    import types
    mod = types.ModuleType("openai")
    mod.OpenAI = _FakeOpenAI
    sys.modules["openai"] = mod
    return fake


def _restore_openai():
    sys.modules.pop("openai", None)


def test_ladder_order():
    ids = [t.id for t in T.TIERS]
    assert ids == ["local", "basic", "plus", "pro"], ids
    print("OK 1) 3 kademe + yerel:", " < ".join(ids))


def test_plan_mapping():
    assert T.plan_to_tier("") == "basic", "bos plan Temel olmali"
    assert T.plan_to_tier("elite") == "pro", "eski elite en iyiye baglanmali"
    assert T.plan_to_tier("premium") == "basic", "eski premium Temel'e baglanmali"
    assert T.plan_to_tier("plus") == "plus"
    assert T.plan_to_tier("pro") == "pro"
    assert T.plan_to_tier("xyz") == "basic"
    print("OK 2) plan -> kademe eslemesi (geriye donuk uyumlu)")


def test_no_o1_anywhere():
    """o1 satistan kaldirildi: hicbir kademede model adi/etiketi olmamali."""
    for t in T.TIERS:
        blob = (t.id + t.label + t.best_for).lower()
        assert "o1" not in blob, f"{t.id} icinde o1 referansi var"
    models = []
    _patch_client({})
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        for tier in ["basic", "plus", "pro"]:
            T.run_ladder(tier, "P", {}, "tr")
    finally:
        _restore_openai()
    print("OK 3) o1 merdivende yok")


def test_fallback_one_step():
    fake = _patch_client({"pro": "raise"})           # pro patirsa plus'a dusmeli
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("pro", "P", {}, "tr")
    finally:
        _restore_openai()
    assert used == "plus", used
    assert txt == "plus metni"
    assert len(fake.calls) == 2, fake.calls
    assert fake.calls[0][0] == "responses", fake.calls
    assert fake.calls[1][0] == "responses", fake.calls
    print("OK 4a) pro hata -> plus'a dusuldu:",
          " -> ".join(m for _, m, _ in fake.calls))


def test_fallback_empty_text():
    _patch_client({"pro": "", "plus": ""})           # bos metin -> basic
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("pro", "P", {}, "tr")
    finally:
        _restore_openai()
    assert used == "basic", used
    print("OK 4b) pro bos metin -> basic'e dusuldu:", used)


def test_fallback_all_the_way_to_local():
    _patch_client({"basic": "raise", "plus": "", "pro": "raise"})
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("pro", "P", {"verdict": "YES", "strictures": []}, "tr")
    finally:
        _restore_openai()
    assert used == "local", used
    assert txt and txt.strip(), "yerel kademe bos metin verdi!"
    print("OK 5) tum kademeler basarisiz -> yerel:", used, f"({len(txt)} krkt)")


def test_no_temperature_on_reasoning_models():
    fake = _patch_client({})
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        for tier, want_kind in (("pro", "responses"), ("plus", "responses"),
                                ("basic", "chat")):
            fake.calls.clear()
            T.run_ladder(tier, "P", {}, "tr")
            kind, model, kw = fake.calls[0]
            assert kind == want_kind, (tier, kind, model)
            if kind == "responses":
                assert "temperature" not in kw, f"{tier} reasoning modeline temperature gonderildi!"
                assert "messages" not in kw, f"{tier} Responses API soylem formatinda olmali"
                assert kw["max_output_tokens"] >= 4000, f"{tier} token tavani cok dusuk -> bos doner!"
                assert kw.get("reasoning", {}).get("effort") == "high"
            else:
                assert "temperature" in kw, f"{tier} chat modelinde temperature yok"
                assert kw["max_tokens"] >= 1000, f"{tier} max_tokens dusuk, uzun aciklama kesilir"
    finally:
        _restore_openai()
    print("OK 6) reasoning'de temperature yok, temel yeterli token tavani")


def test_no_key_goes_local():
    os.environ.pop("OPENAI_API_KEY", None)
    txt, used = T.run_ladder("pro", "P", {"verdict": "YES", "strictures": []}, "tr")
    assert used == "local", used
    assert txt.strip()
    print("OK 7) anahtar yok -> yerel:", used)


def test_fallback_stays_below_start():
    fake = _patch_client({"basic": "raise"})        # basic sadece local'a dusebilir
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("basic", "P", {"verdict": "YES", "strictures": []}, "tr")
    finally:
        _restore_openai()
    assert used == "local", used
    models = [m for _, m, _ in fake.calls]
    assert models == ["gpt-4.1"], f"basic'ten ust kademeye atlandi: {models}"
    print("OK 8) basic baslatildi -> ust kademeye atlanmadi:", models)


if __name__ == "__main__":
    test_ladder_order()
    test_plan_mapping()
    test_no_o1_anywhere()
    test_fallback_one_step()
    test_fallback_empty_text()
    test_fallback_all_the_way_to_local()
    test_no_temperature_on_reasoning_models()
    test_no_key_goes_local()
    test_fallback_stays_below_start()
    print("test_tiers: 10/10 OK")