"""Fast Koc — Pydantic semalar."""
from __future__ import annotations
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class ProfilIn(BaseModel):
    ad: str = "Ogrenci"
    rol: str = Field("ogrenci", pattern="^(ogrenci|veli|koc|admin)$")
    segment: str = Field("YKS_ESKI", pattern="^(LGS|ARA_9_10_11|YKS|YKS_ESKI|YKS_MAARIF)$")
    sinif: str = ""
    alan: str = ""
    seviye: str = Field("orta", pattern="^(temel|orta|ileri)$")
    hedef: str = ""
    gunluk_hedef_soru: int = 80


class KonuKirim(BaseModel):
    kod: str
    baslik: str = ""
    dogru: int = 0
    yanlis: int = 0
    bos: int = 0


class SinavIn(BaseModel):
    ogrenci_id: int
    tur: str = "deneme"
    ad: str = ""
    tarih: date
    ders: str
    konular: List[KonuKirim]


class GunlukLogIn(BaseModel):
    ogrenci_id: int
    tarih: date
    cozulen_soru: int = 0
    calisilan_dk: int = 0
    notlar: str = ""


class OdevOnayIn(BaseModel):
    odev_id: int
    yapilan: int


class BaglantiIn(BaseModel):
    ogrenci_id: int
    sahip_id: int
    rol: str = Field("veli", pattern="^(veli|koc)$")


class CihazIn(BaseModel):
    ogrenci_id: int
    fcm_token: str
    platform: str = "android"
