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
        tid = {v: k for k, v in {"oracle": "gpt-4o-mini", "seer": "gpt-4.1",
                                  "premium": "gpt-4o", "sage": "gpt-5.6-terra",
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
    assert ids == ["local", "oracle", "seer", "premium", "sage", "elite", "master"], ids
    print("OK 1) merdiven sirasi:", " < ".join(ids))


def test_plan_mapping():
    assert T.plan_to_tier("elite") == "elite"
    assert T.plan_to_tier("premium") == "premium"
    assert T.plan_to_tier("seer") == "seer"
    assert T.plan_to_tier("sage") == "sage"
    assert T.plan_to_tier("") == "oracle"
    assert T.plan_to_tier("xyz") == "oracle"
    print("OK 2) plan -> katman eslemesi")


def test_fallback_one_step():
    fake = _patch_client({"elite": "raise"})         # elite patlar -> sage'e dusmeli
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("elite", "P", {}, "tr")
    finally:
        _restore_openai()
    assert used == "sage", used
    assert txt == "sage metni"
    assert fake.calls[0][0] == "responses", fake.calls   # o1 Responses API
    assert fake.calls[1][0] == "responses", fake.calls   # gpt-5.6-terra da Responses API
    assert len(fake.calls) == 2, fake.calls              # sage basardi, daha dusulmedi
    print("OK 3a) elite hata -> tek dusus:", " -> ".join(m for _, m, _ in fake.calls))


def test_fallback_empty_text():
    _patch_client({"elite": "", "sage": ""})          # elite bos -> premium'a dusmeli
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("elite", "P", {}, "tr")
    finally:
        _restore_openai()
    assert used == "premium", used
    print("OK 3b) elite bos metin -> premium'a dusuldu:", used)


def test_fallback_all_the_way_to_local():
    _patch_client({"oracle": "raise", "seer": "raise", "premium": "", "sage": "",
                   "elite": "raise"})
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("elite", "P", {"verdict": "YES", "strictures": []}, "tr")
    finally:
        _restore_openai()
    # elite -> sage -> premium -> seer -> oracle -> local
    assert used == "local", used
    assert txt and txt.strip(), "yerel katman bos metin verdi!"
    print("OK 4) tum katmanlar basarisiz -> yerel:", used, f"({len(txt)} krkt)")


def test_no_temperature_on_reasoning_models():
    fake = _patch_client({})                          # hepsi ok
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        for tier, want_kind in (("elite", "responses"), ("master", "responses"),
                                ("sage", "responses"),
                                ("premium", "chat"), ("seer", "chat"), ("oracle", "chat")):
            fake.calls.clear()
            T.run_ladder(tier, "P", {}, "tr")
            kind, model, kw = fake.calls[0]
            assert kind == want_kind, (tier, kind, model)
            if kind == "responses":
                assert "temperature" not in kw, f"{tier} reasoning modeline temperature gonderildi!"
                assert "messages" not in kw, f"{tier} Responses API soylem formatinda olmali"
                assert kw["max_output_tokens"] >= 4000, f"{tier} token tavani cok dusuk -> bos doner!"
                # o1 'effort' parametresini kabul etmiyor; gpt-5.6 serisi alir (minimal de reddedilir)
                if tier in ("sage", "master"):
                    assert kw.get("reasoning", {}).get("effort") == "high"
                else:
                    assert "reasoning" not in kw, f"{tier} icin effort gonderilmemeli"
            else:
                assert "temperature" in kw, f"{tier} chat modelinde temperature yok"
    finally:
        _restore_openai()
    print("OK 5) reasoning modellerinde temperature yok, token tavani yuksek")


def test_fallback_stays_below_start():
    """Baslatilan katmandan ASLA ust kademeye atlanmamali (seer -> sage olmamali)."""
    fake = _patch_client({"seer": "raise"})   # seer asagi dusmeli
    os.environ["OPENAI_API_KEY"] = "sk-test"
    try:
        txt, used = T.run_ladder("seer", "P", {"verdict": "YES", "strictures": []}, "tr")
    finally:
        _restore_openai()
    # seer'in ALTINDA sadece oracle ve local var -> premium/sage ASLA denenmemeli
    assert used == "oracle", used
    models = [m for _, m, _ in fake.calls]
    assert models == ["gpt-4.1", "gpt-4o-mini"], models
    print("OK 7) seer -> sadece asagi dustu (premium/sage denenmedi):", models)


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
    test_fallback_stays_below_start()
    print("test_tiers: 9/9 OK")