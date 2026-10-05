# -*- coding: utf-8 -*-
"""billing.py regresyon testi — sizinti kapandi mi?

Kapsam:
  1) Dosya modunda hak tuketimi kalici
  2) PG cok surekli basarisiz olsa bile mark_free_used bir depoya yazar
     (ONCEKI SURUMDE BURASI SESSIZCE GECIYORDU -> sinirsiz ucretsiz PDF)
  3) PG okunamaz ve hicbir kayit yoksa has_free_used fail-closed -> True
     (ONCEKI SURUMDE False DONUYORDU -> fail-open, herkese ucretsiz PDF)
  4) can_download_pdf bu durumda reddediyor
"""
import importlib
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath("backend"))

GEÇICI = tempfile.mkdtemp(prefix="billing_test_")
os.environ["DATABASE_URL"] = "postgresql://u:p@127.0.0.1:1/yok"  # kasıtlı erişilemez

ok = True


def kontrol(kosul, ad, ek=""):
    global ok
    if kosul:
        print("  GECTI:", ad)
    else:
        print("  KALDI:", ad, ek)
        ok = False


import backend.billing as b  # noqa: E402

# Veri dosyalarini gecici klasore yonlendir
b.DATA_DIR = Path(GEÇICI)
b.SUBS_FILE = b.DATA_DIR / "subscriptions.json"
b.FREE_FILE = b.DATA_DIR / "free_pdf_used.json"
b.PURCHASES_FILE = b.DATA_DIR / "pdf_purchases.json"

print("=== 1) PG erisilemez durumunda tuketim ===")
b._SCHEMA_READY = False
b.mark_free_used("uid_test_a")
kontrol(b.has_free_used("uid_test_a") is True,
        "mark_free_used sonrasi has_free_used True",
        f"beklenen True, gelen {b.has_free_used('uid_test_a')}")

print()
print("=== 2) Tuketim kalici mi (modul yeniden yuklenince)? ===")
del sys.modules["backend.billing"]
import backend.billing as b2  # noqa: E402
b2.DATA_DIR = Path(GEÇICI)
b2.SUBS_FILE = b2.DATA_DIR / "subscriptions.json"
b2.FREE_FILE = b2.DATA_DIR / "free_pdf_used.json"
b2.PURCHASES_FILE = b2.DATA_DIR / "pdf_purchases.json"
kontrol(b2.has_free_used("uid_test_a") is True,
        "yeniden yuklemede sonra da True",
        f"gelen {b2.has_free_used('uid_test_a')}")

print()
print("=== 3) YENI kullanici: PG okunamaz VE hicbir depo yok -> fail-closed ===")
# Fail-closed yalnizca "hicbir yerde kayit yok" iken devreye girer.
# Dosya deposu calisiyorsa sistem dogru bir cevap verebilir ve izin vermesi
# dogrudur (Render'da disk gecici oldugu icin kalici cozum PostgreSQL'dir).
b2.FREE_FILE = Path(GEÇICI) / "hic_boyle_dosya.json"
kontrol(not b2.FREE_FILE.exists(), "test oncesi dosya gercekten yok")
kontrol(b2.has_free_used("uid_test_yeni") is True,
        "bilinmeyen durumda True (fail-closed)",
        f"beklenen True, gelen {b2.has_free_used('uid_test_yeni')}")

print()
print("=== 4) Indirme karari ===")
karar = b2.can_download_pdf("uid_test_yeni", "", "natal")
kontrol(karar["allowed"] is False and karar["reason"] == "no_right",
        "can_download_pdf reddediyor", f"gelen {karar}")

print()
print("=== 5) Abone her zaman serbest ===")
b2.upsert_subscription("uid_test_abone", "sub_daily", 0, "active")
karar = b2.can_download_pdf("uid_test_abone", "", "natal")
kontrol(karar["allowed"] is True and karar["reason"] in ("subscribed", "pdf_single"),
        "abone PDF alabiliyor", f"gelen {karar}")

print()
print("=== 6) pdf_single kalici hak ===")
b2.grant_pdf_single("uid_test_tek", 0)
kontrol(b2.can_download_pdf("uid_test_tek", "", "natal")["allowed"] is True,
        "pdf_single sahibi PDF alabiliyor")

print()
print("SONUC:", "GECTI" if ok else "KALDI")
sys.exit(0 if ok else 1)