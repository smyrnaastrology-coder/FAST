"""Fast Koc — SQLAlchemy modelleri (9 tablo)."""
from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Boolean, JSON
from .database import Base


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True)
    auth_user_id = Column(String(128), unique=True, nullable=True)
    rol = Column(String(16), default="ogrenci")  # ogrenci | veli | koc | admin (Faz 3)
    ad = Column(String(120), nullable=False, default="Ogrenci")
    segment = Column(String(32), nullable=False, default="YKS_ESKI")  # LGS | ARA_9_10_11 | YKS_ESKI | YKS_MAARIF (eski 'YKS' = YKS_ESKI)
    sinif = Column(String(16), default="")
    alan = Column(String(16), default="")  # SAY | EA | SOZ | DIL (YKS)
    seviye = Column(String(16), default="orta")  # temel | orta | ileri
    hedef = Column(String(256), default="")
    gunluk_hedef_soru = Column(Integer, default=80)
    olusturma = Column(DateTime, default=datetime.utcnow)


class SinavSonuc(Base):
    __tablename__ = "sinav_sonuclar"
    id = Column(Integer, primary_key=True)
    ogrenci_id = Column(Integer, ForeignKey("profiles.id"), index=True, nullable=False)
    tur = Column(String(32), default="deneme")  # deneme | okul | TG
    ad = Column(String(160), default="")
    tarih = Column(Date, default=date.today)
    ders = Column(String(80), nullable=False)
    # konu kirimlari: [{kod, baslik, dogru, yanlis, bos}]
    konular = Column(JSON, default=list)
    toplam_dogru = Column(Integer, default=0)
    toplam_yanlis = Column(Integer, default=0)
    toplam_bos = Column(Integer, default=0)
    net = Column(Float, default=0.0)


class GunlukLog(Base):
    __tablename__ = "gunluk_log"
    id = Column(Integer, primary_key=True)
    ogrenci_id = Column(Integer, ForeignKey("profiles.id"), index=True, nullable=False)
    tarih = Column(Date, index=True, nullable=False)
    cozulen_soru = Column(Integer, default=0)
    calisilan_dk = Column(Integer, default=0)
    notlar = Column(Text, default="")


class Odev(Base):
    __tablename__ = "odevler"
    id = Column(Integer, primary_key=True)
    ogrenci_id = Column(Integer, ForeignKey("profiles.id"), index=True, nullable=False)
    hafta = Column(String(16), default="")  # 2026-W42
    gun = Column(String(16), default="Pazartesi")
    tarih = Column(Date, nullable=True)
    ders = Column(String(80), default="")
    konu_kod = Column(String(32), default="")
    konu_baslik = Column(String(160), default="")
    kaynak_kitap_id = Column(String(32), default="")
    adet = Column(Integer, default=30)
    hedef_dk = Column(Integer, default=45)
    durum = Column(String(16), default="verildi")  # verildi | yapildi | eksik
    yapilan = Column(Integer, default=0)


class Kitap(Base):
    __tablename__ = "kitaplar"
    id = Column(Integer, primary_key=True)
    katalog_id = Column(String(32), unique=True, nullable=False)
    isbn = Column(String(32), default="")
    isbn_durum = Column(String(48), default="yer-tutucu-dogrulanmadi")  # dogrulandi | yer-tutucu-dogrulanmadi
    baslik = Column(String(200), nullable=False)
    yazar = Column(String(120), default="")
    yayin = Column(String(120), default="")
    tur = Column(String(32), default="soru_bankasi")
    seviye = Column(String(16), default="orta")
    dersler = Column(JSON, default=list)
    kapak_url = Column(String(500), default="")
    aciklama = Column(Text, default="")
    maarif = Column(JSON, default=list)


class DenemeTakvim(Base):
    __tablename__ = "deneme_takvim"
    id = Column(Integer, primary_key=True)
    kod = Column(String(32), unique=True, nullable=False)
    ad = Column(String(200), nullable=False)
    segment = Column(String(32), index=True, default="YKS")
    yayin = Column(String(120), default="")
    tarih = Column(Date, index=True, nullable=False)
    bitis = Column(Date, nullable=True)  # uygulama araligi bitisi
    basvuru_son = Column(Date, nullable=True)
    erken_uyari_gun = Column(Integer, default=7)
    dogrulama_durumu = Column(String(64), default="taslak-yayinci-teyidi-gerekir")
    kaynak_url = Column(String(500), default="-")


class Bildirim(Base):
    __tablename__ = "bildirimler"
    id = Column(Integer, primary_key=True)
    ogrenci_id = Column(Integer, ForeignKey("profiles.id"), index=True, nullable=False)
    tip = Column(String(32), default="gun_sonu")  # gun_sonu | erken_uyari | odev | sistem
    kanal = Column(String(16), default="uygulama_ici")  # uygulama_ici | push (Faz 3)
    metin = Column(Text, nullable=False)
    okundu = Column(Boolean, default=False)
    tarih = Column(DateTime, default=datetime.utcnow)


class Baglanti(Base):
    """Veli/koç <-> öğrenci bağlantısı (Faz 3). durum: beklemede | aktif | reddedildi."""
    __tablename__ = "baglantilar"
    id = Column(Integer, primary_key=True)
    ogrenci_id = Column(Integer, ForeignKey("profiles.id"), index=True, nullable=False)
    sahip_id = Column(Integer, ForeignKey("profiles.id"), index=True, nullable=False)  # veli/koc profili
    rol = Column(String(16), default="veli")  # veli | koc
    durum = Column(String(16), default="aktif")
    olusturma = Column(DateTime, default=datetime.utcnow)


class Cihaz(Base):
    """Push bildirim hedefi (FCM token, Faz 3)."""
    __tablename__ = "cihazlar"
    id = Column(Integer, primary_key=True)
    ogrenci_id = Column(Integer, ForeignKey("profiles.id"), index=True, nullable=False)
    fcm_token = Column(String(512), unique=True, nullable=False)
    platform = Column(String(16), default="android")  # android | ios | web
    aktif = Column(Boolean, default=True)
    olusturma = Column(DateTime, default=datetime.utcnow)


class Abonelik(Base):
    """Ödeme/entitlement (Faz 3). plan: ucretsiz | pro. Stripe stub ile beslenir."""
    __tablename__ = "abonelikler"
    id = Column(Integer, primary_key=True)
    ogrenci_id = Column(Integer, ForeignKey("profiles.id"), index=True, nullable=False)
    plan = Column(String(16), default="ucretsiz")
    stripe_session = Column(String(128), default="")
    baslangic = Column(DateTime, default=datetime.utcnow)
    bitis = Column(DateTime, nullable=True)
