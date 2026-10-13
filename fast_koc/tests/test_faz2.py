import io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date
from backend.services.isbn_dogrulama import isbn13_gecerli, katalog_dogrula
from backend.database import SessionLocal, init_db
from backend.models import Profile, SinavSonuc, GunlukLog
from backend.services.takvim_seed import takvim_seed_yukle, katalog_seed_yukle
from backend.services.karne_pdf import karne_pdf_uret


def test_isbn_checksum():
    assert isbn13_gecerli("9786051880006") is True
    assert isbn13_gecerli("9786051880001") is False
    assert isbn13_gecerli("123") is False
    assert isbn13_gecerli("") is False


def test_katalog_checksum_gecerli_yer_tutucu():
    rapor = katalog_dogrula(carli_kontrol=False)
    assert rapor["ozet"]["toplam"] == 16
    # tum ISBN'lar checksum-gecerli olmali ama canli dogrulama yok
    for s in rapor["kitaplar"]:
        assert s["checksum_gecerli"] is True, s
        assert s["durum"] == "dogrulanmadi-yer-tutucu"


def test_takvim_seed_idempotent_ve_dogrulama_alanli():
    init_db()
    db = SessionLocal()
    try:
        ilk = takvim_seed_yukle(db)
        ikinci = takvim_seed_yukle(db)
        assert ikinci == 0
        assert ilk >= 0
        from backend.models import DenemeTakvim
        bir = db.query(DenemeTakvim).first()
        assert bir is not None
        assert getattr(bir, "dogrulama_durumu", "") != ""
    finally:
        db.close()


def test_karne_pdf_uretiliyor():
    class P:
        ad = "Test Ogrenci"; segment = "YKS"; seviye = "orta"; hedef = "TYT 90+"
    sinavlar = []
    loglar = []
    odevler = []
    analiz = {"konular": [
        {"kod": "TYT-MAT-06", "baslik": "Problemler", "dogru": 3, "yanlis": 5, "bos": 2,
         "toplam": 10, "basari": 30.0, "durum": "kritik"}],
        "kritik_sayisi": 1, "ozet_cumle": "Test ozet."}
    pdf = karne_pdf_uret(P(), sinavlar, loglar, odevler, analiz, [], [])
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 5000
