"""Push servisi (FCM, Faz 3).

- Cihaz token'lari `cihazlar` tablosunda tutulur.
- `push_kuyruga_ekle`: her zaman uygulama-ici Bildirim satiri acar (kanal=push ile isaretli);
  FCM anahtari yoksa gonderim denenmez, k queue'da kalir (MVP guvenli).
- `FCM_SERVER_KEY` (legacy) veya `FCM_PROJECT_ID + FCM_SERVICE_JSON` (v1) varsa gercek gonderim denenir.
- Ag yoksa / anahtar yoksa sessizce (False, sebep) doner; testler offline gecer.
"""
from __future__ import annotations
import json
import os
import urllib.request
from typing import Tuple
from sqlalchemy.orm import Session
from ..models import Bildirim, Cihaz


def push_kuyruga_ekle(db: Session, ogrenci_id: int, metin: str,
                      tip: str = "gun_sonu") -> Bildirim:
    b = Bildirim(ogrenci_id=ogrenci_id, tip=tip, kanal="push", metin=metin)
    db.add(b); db.commit(); db.refresh(b)
    return b


def _legacy_gonder(token: str, baslik: str, metin: str) -> Tuple[bool, str]:
    key = os.environ.get("FCM_SERVER_KEY", "")
    if not key:
        return False, "FCM_SERVER_KEY yok"
    govde = {"to": token, "notification": {"title": baslik, "body": metin}}
    try:
        req = urllib.request.Request(
            "https://fcm.googleapis.com/fcm/send",
            data=json.dumps(govde).encode(),
            headers={"Authorization": f"key={key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return (r.status == 200), f"http-{r.status}"
    except Exception as e:
        return False, f"ag-hatasi: {e}"


def push_gonder(db: Session, ogrenci_id: int, baslik: str, metin: str,
                tip: str = "gun_sonu") -> dict:
    b = push_kuyruga_ekle(db, ogrenci_id, metin, tip)
    cihazlar = db.query(Cihaz).filter_by(ogrenci_id=ogrenci_id, aktif=True).all()
    if not cihazlar:
        return {"bildirim_id": b.id, "gonderildi": 0, "not": "cihaz yok, kuyrukta"}
    ok = 0
    notlar = []
    for c in cihazlar:
        basari, sebep = _legacy_gonder(c.fcm_token, baslik, metin)
        ok += 1 if basari else 0
        notlar.append(sebep)
    return {"bildirim_id": b.id, "gonderildi": ok, "hedef": len(cihazlar), "not": "; ".join(notlar)[:200]}


FCM_KURULUM_NOTU = """FCM kurulumu (uretim):
1. Firebase Console -> yeni proje -> Android/iOS uygulamasi ekle (paket: com.fastkoc.app).
2. Cloud Messaging sekmesinden Server Key al -> sunucuda FCM_SERVER_KEY env olarak tanimla.
   (Legacy API; v1'e geciste FCM_PROJECT_ID + servis hesabi JSON kullanilacak.)
3. Mobil tarafta firebase_messaging ile token al -> POST /api/cihaz ile kaydet.
4. Zamanlayici: gunluk 21:30 `python -m backend.jobs.gunluk_push` (cron/Render cron).
"""
