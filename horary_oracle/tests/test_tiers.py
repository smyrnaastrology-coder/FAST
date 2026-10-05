# -*- coding: utf-8 -*-
"""Yorum katmanlari (engine.tiers) testleri - AG OLMAYAN sahte OpenAI istemcisi ile.

Kontrol edilenler:
1. Merdiven sirasi: local < oracle < premium < elite < master (en kotuden en iyiye)
2. plan -> katman eslemesi
3. Hata/bos metin durumunda BIR ALT katmana dusulmesi
4. Tum katmanlar basarisiz -> yerel deterministik metin (hicbir zaman bos cevap yok)
5. reasoning modellerine 'temperature' gonderilmiyor (Responses API)
6. anahtar yoksa hicbir LLM cagrisi yapilmadan yerel metne dusulmesi
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import engine.tiers as T
from engine.tiers import base


class _Err:
    def __init__(self, n):
        self.n = n


class FakeClient:
    """chat.completions + responses.take; hangi katmanin ne dondugunu izler."""
    def __init__(self, behavior):
        self.behavior = behavior      # {tier_id: "ok" | "" | "raise"}
        self.calls = []               # ("chat"|"responses", model, kwargs)
        self.chat = _Chat(self)
        self.responses = _Responses(self)

    def _act(self, kind, model, kwargs):
        tier = T.tier_index  # sadece import
        self.calls.append((kind, model, kwargs))
        b = self.behavior
        # model -> tier eslemesi (sadece test icin)
        tid = {v: k for k, v in {"oracle": "gpt-4o-mini", "premium": "gpt-4o",
                                  "elite": "o1", "master": "gpt-5.6-sol"}.items()}.get(model, "local")
        mode = b.get(tid, "ok")
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
        r = type("R", (), {"status": "completed", "output_text": txt})()
        return r


def _patch_client(monkey_behavior, key="sk-test"):
    """run_ladder'in OpenAI istemcisi yerine sahte istemci koyar."""
    fake = FakeClient(monkey_behavior)

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
    for m in [k for k in sys.modules if k == "openai"]:
        del sys.modules[m]


def test_ladder_order():
    ids = [t.id for t in T.TIERS]
    assert ids == ["local", "oracle", "premium", "elite", "master"], ids
    print("OK 1) merdiven sirasi:", " < ".join(ids))


def test_plan_mapping():
    assert T.plan_to_tier("elite") == "elite"
    assert T.plan_to_tier("premium") == "premium"
    assert T.plan_to_tier("") == "oracle"
    assert T.plan_to_tier("xyz") == "oracle"
    print("OK 2) plan -> katman eslemesi")


def test_fallback_one_step():
    fake = _patch_client({"elite": "raise"})         # elite patlar -> premium'a dusmeli
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("elite", "P", {}, "tr")
    finally:
        _restore_openai()
    assert used == "premium", used
    assert txt == "premium metni"
    assert fake.calls[0][0] == "responses", fake.calls   # o1 Responses API
    assert fake.calls[1][0] == "chat", fake.calls         # gpt-4o chat API
    print("OK 3a) elite hata -> premium'a dusuldu:", used)


def test_fallback_empty_text():
    _patch_client({"elite": ""})                      # elite bos metin -> premium
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("elite", "P", {}, "tr")
    finally:
        _restore_openai()
    assert used == "premium", used
    print("OK 3b) elite bos metin -> premium'a dusuldu:", used)


def test_fallback_all_the_way_to_local():
    _patch_client({"oracle": "raise", "premium": "", "elite": "raise", "master": "raise"})
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("elite", "P", {"verdict": "YES", "strictures": []}, "tr")
    finally:
        _restore_openai()
    # master en ust oldugu icin zincir master->elite->premium->oracle->local
    assert used == "local", used
    assert txt and txt.strip(), "yerel katman bos metin verdi!"
    print("OK 4) tum katmanlar basarisiz -> yerel:", used, f"({len(txt)} krkt)")


def test_no_temperature_on_reasoning_models():
    fake = _patch_client({})                          # hepsi ok
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        for tier, want_kind in (("elite", "responses"), ("master", "responses"),
                                ("premium", "chat"), ("oracle", "chat")):
            fake.calls.clear()
            T.run_ladder(tier, "P", {}, "tr")
            kind, model, kw = fake.calls[0]
            assert kind == want_kind, (tier, kind)
            if kind == "responses":
                assert "temperature" not in kw, f"{tier} reasoning modeline temperature gonderildi!"
                assert "messages" not in kw, f"{tier} Responses API soylem formatinda olmali"
                assert kw["max_output_tokens"] >= 4000, f"{tier} token tavani cok dusuk -> bos doner!"
                # o1 'effort' parametresini kabul etmiyor; sadece gpt-5.6 serisi alir
                if tier == "master":
                    assert kw.get("reasoning", {}).get("effort") == "high"
                else:
                    assert "reasoning" not in kw, f"{tier} icin effort gonderilmemeli"
            else:
                assert "temperature" in kw, f"{tier} chat modelinde temperature yok"
    finally:
        _restore_openai()
    print("OK 5) reasoning modellerinde temperature yok, token tavani yuksek")


def test_no_key_goes_local():
    os.environ.pop("OPENAI_API_KEY", None)
    txt, used = T.run_ladder("elite", "P", {"verdict": "YES", "strictures": []}, "tr")
    assert used == "local", used
    assert txt.strip()
    print("OK 6) anahtar yok -> yerel katman:", used)


if __name__ == "__main__":
    test_ladder_order()
    test_plan_mapping()
    test_fallback_one_step()
    test_fallback_empty_text()
    test_fallback_all_the_way_to_local()
    test_no_temperature_on_reasoning_models()
    test_no_key_goes_local()
    print("test_tiers: 8/8 OK")