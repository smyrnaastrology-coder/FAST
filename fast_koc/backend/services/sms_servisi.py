"""Veli SMS bilgilendirme stub (Netgsm/Twilio uyumlu iskelet).

- SMS_API_ANAHTARI yoksa gonderim denenmez, ileti `bildirimler` tablosuna kanal=sms ile yazilir (kuyruk).
- Anahtar varsa Netgsm GET API denenir (basit, username+password header varyanti da eklenebilir).
- Telefon formati: 05xx xxx xx xx (TR). Dogrulama hafif tutulur.
"""
from __future__ import annotations
import os
import urllib.parse
import urllib.request
from sqlalchemy.orm import Session
from ..models import Bildirim


def telefon_normalize(tel: str) -> str:
    s = "".join(c for c in (tel or "") if c.isdigit())
    if s.startswith("90") and len(s) == 12:
        s = "0" + s[2:]
    if len(s) == 11 and s.startswith("05"):
        return s
    raise ValueError("telefon 05xx formatinda olmali")


def sms_gonder(db: Session, ogrenci_id: int, telefon: str, metin: str) -> dict:
    tel = telefon_normalize(telefon)
    b = Bildirim(ogrenci_id=ogrenci_id, tip="veli_sms", kanal="sms",
                 metin=f"SMS->{tel}: {metin[:140]}")
    db.add(b); db.commit(); db.refresh(b)
    key = os.environ.get("SMS_API_ANAHTARI", "")
    if not key:
        return {"bildirim_id": b.id, "gonderildi": False,
                "not": "SMS_API_ANAHTARI yok; kuyruga yazildi."}
    try:
        url = ("https://api.netgsm.com.tr/sms/send/get/?usercode=&password=&gsmno="
               + tel + "&message=" + urllib.parse.quote(metin) + "&no=" + key)
        req = urllib.request.Request(url, headers={"User-Agent": "FastKoc/0.4"})
        with urllib.request.urlopen(req, timeout=10) as r:
            kod = r.read().decode().strip()
        ok = kod.startswith("00")
        return {"bildirim_id": b.id, "gonderildi": ok, "not": f"netgsm:{kod[:20]}"}
    except Exception as e:
        return {"bildirim_id": b.id, "gonderildi": False, "not": f"ag-hatasi: {e}"[:200]}
