import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.engine import mufredat as muf


def test_alias_yks_eski():
    assert muf.coz("YKS") == "YKS_ESKI"
    assert muf.coz("YKS_ESKI") == "YKS_ESKI"
    assert muf.coz("YKS_MAARIF") == "YKS_MAARIF"
    assert muf.coz("BOZUK") == "YKS_ESKI"
    assert muf.coz(None) == "YKS_ESKI"


def test_sistem_ayrimi():
    assert muf.sistem_of("YKS_ESKI") == "eski"
    assert muf.sistem_of("YKS_MAARIF") == "maarif"
    assert muf.sistem_of("LGS") == "maarif"
    assert muf.sistem_of("ARA_9_10_11") == "maarif"


def test_sinif_onerisi():
    assert muf.siniftan_oner("12") == "YKS_ESKI"
    assert muf.siniftan_oner("mezun") == "YKS_ESKI"
    assert muf.siniftan_oner("11") == "ARA_9_10_11"
    assert muf.siniftan_oner("8") == "LGS"


def test_takvim_paylasimi():
    # iki YKS varyanti ayni TG havuzunu gorur
    assert set(muf.takvim_eslesme("YKS_ESKI")) == set(muf.takvim_eslesme("YKS_MAARIF"))
    assert "YKS" in muf.takvim_eslesme("YKS_ESKI")
    assert muf.takvim_eslesme("LGS") == ["LGS"]


def test_ders_agaci_var():
    assert "TYT-Matematik" in muf.dersler("YKS_ESKI")
    assert "TYT-Matematik" in muf.dersler("YKS_MAARIF")
    assert "Matematik" in muf.dersler("LGS")


def test_donem_bayragi(monkeypatch):
    monkeypatch.setenv("FASTKOC_TUMU_MAARIF", "true")
    assert muf.tumu_maarif_donemi() is True
    assert "YKS_ESKI" not in muf.secilebilir_segmentler()
    assert "YKS_MAARIF" in muf.secilebilir_segmentler()
    monkeypatch.setenv("FASTKOC_TUMU_MAARIF", "false")
    assert "YKS_ESKI" in muf.secilebilir_segmentler()
