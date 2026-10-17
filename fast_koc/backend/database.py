"""Fast Koc — veritabani katmani. SQLite (MVP) + Postgres (uretim) uyumlu."""
from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

def _url_temizle(ham: str) -> str:
    """Env'den gelen URL'yi temizle: kirp, tirnaklari at, postgres:// cevir."""
    url = (ham or "").strip().strip('"').strip("'").strip()
    if url.startswith("postgres://"):
        # Render/Heroku tarzi URL -> SQLAlchemy psycopg3 formatina cevir
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def _gecerli(url: str) -> bool:
    return bool(url) and "://" in url


_ham = os.environ.get("FASTKOC_DATABASE_URL") or ""
DATABASE_URL = _url_temizle(_ham)
if not _gecerli(DATABASE_URL):
    # Yanlis/eksik FASTKOC degeri -> Render'in otomatik DATABASE_URL'ine dus
    alternatif = _url_temizle(os.environ.get("DATABASE_URL") or "")
    if _gecerli(alternatif):
        DATABASE_URL = alternatif
    elif not _gecerli(DATABASE_URL):
        DATABASE_URL = "sqlite:///./fastkoc.db"
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
except Exception as e:
    # Secret sizdirmeden teshis: sadece sema + uzunluk goster
    sema = DATABASE_URL.split("://")[0] if "://" in DATABASE_URL else "(sema yok)"
    raise RuntimeError(
        f"FASTKOC_DATABASE_URL parse edilemedi (sema={sema!r}, uzunluk={len(DATABASE_URL)}). "
        f"Render panelinde degerin 'postgres://...' ile basladigini ve bosluk/newline icermedigini kontrol edin. "
        f"Orjinal hata: {e}"
    ) from e
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401  (tablolari kaydet)
    Base.metadata.create_all(bind=engine)
    _hafif_migrasyon()
    _indeks_migrasyon()


def _indeks_migrasyon() -> None:
    """Unique index'leri guvenli ekler; once olasi mukerrer satirlari temizler."""
    from sqlalchemy import text
    islemler = [
        ("DELETE FROM gunluk_log WHERE id NOT IN "
         "(SELECT MIN(id) FROM gunluk_log GROUP BY ogrenci_id, tarih)",
         "CREATE UNIQUE INDEX IF NOT EXISTS uq_gunluk_ogrenci_tarih ON gunluk_log (ogrenci_id, tarih)"),
        ("DELETE FROM baglantilar WHERE id NOT IN "
         "(SELECT MIN(id) FROM baglantilar GROUP BY ogrenci_id, sahip_id)",
         "CREATE UNIQUE INDEX IF NOT EXISTS uq_baglanti_ogrenci_sahip ON baglantilar (ogrenci_id, sahip_id)"),
    ]
    for temizle, indeks in islemler:
        try:
            with engine.begin() as conn:
                conn.execute(text(temizle))
                conn.execute(text(indeks))
        except Exception:
            pass


def _hafif_migrasyon() -> None:
    """Var olan SQLite/Postgres tablolarina yeni kolonlari ekler (create_all alter yapmaz)."""
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    try:
        kolonlar = {c["name"] for c in insp.get_columns("kitaplar")}
    except Exception:
        return
    with engine.begin() as conn:
        if "isbn_durum" not in kolonlar:
            conn.execute(text("ALTER TABLE kitaplar ADD COLUMN isbn_durum VARCHAR(48) DEFAULT 'yer-tutucu-dogrulanmadi'"))
        try:
            tkol = {c["name"] for c in insp.get_columns("deneme_takvim")}
        except Exception:
            tkol = set()
        if "dogrulama_durumu" not in tkol:
            conn.execute(text("ALTER TABLE deneme_takvim ADD COLUMN dogrulama_durumu VARCHAR(64) DEFAULT 'taslak-yayinci-teyidi-gerekir'"))
        if "kaynak_url" not in tkol:
            conn.execute(text("ALTER TABLE deneme_takvim ADD COLUMN kaynak_url VARCHAR(500) DEFAULT '-'"))
        if "bitis" not in tkol:
            conn.execute(text("ALTER TABLE deneme_takvim ADD COLUMN bitis DATE"))
        # Faz 3 kolonlari
        try:
            pkol = {c["name"] for c in insp.get_columns("profiles")}
        except Exception:
            pkol = set()
        if "rol" not in pkol:
            conn.execute(text("ALTER TABLE profiles ADD COLUMN rol VARCHAR(16) DEFAULT 'ogrenci'"))
        try:
            bkol = {c["name"] for c in insp.get_columns("bildirimler")}
        except Exception:
            bkol = set()
        if "kanal" not in bkol:
            conn.execute(text("ALTER TABLE bildirimler ADD COLUMN kanal VARCHAR(16) DEFAULT 'uygulama_ici'"))
        # Donem ayrimi: eski 'YKS' segmentli profilleri YKS_ESKI'ye tasi (2026-27: 12/mezun eski sistem)
        try:
            conn.execute(text("UPDATE profiles SET segment='YKS_ESKI' WHERE segment='YKS'"))
            conn.execute(text("UPDATE deneme_takvim SET segment='YKS' WHERE segment IS NULL"))
        except Exception:
            pass
