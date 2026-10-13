"""Odeme/entitlement stub (Faz 3).

- Planlar: ucretsiz (MVP tam acik) | pro (koc paneli + sinirsiz karne + push onceligi).
- STRIPE_SECRET_KEY yoksa checkout sahte link uretir (test modu); varsa gercek API denenir.
- `plan_of`: ogrencinin guncel plani. `pro_gerekli`: dependency (MVP'de acik, uretimde 402).
"""
from __future__ import annotations
import os
import urllib.parse
import urllib.request
import json
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Abonelik

PLANLAR = {
    "ucretsiz": {"ucret": 0, "ozellik": ["analiz", "odev", "karne"]},
    "pro": {"ucret": 149, "para": "TRY/ay", "ozellik": ["analiz", "odev", "karne", "koc_paneli", "push_oncelik"]},
}


def plan_of(db: Session, ogrenci_id: int) -> str:
    ab = db.query(Abonelik).filter_by(ogrenci_id=ogrenci_id).order_by(Abonelik.id.desc()).first()
    if not ab:
        return "ucretsiz"
    if ab.bitis and ab.bitis < datetime.utcnow():
        return "ucretsiz"
    return ab.plan


def checkout_link(ogrenci_id: int, plan: str = "pro") -> dict:
    if plan not in PLANLAR:
        raise ValueError("bilinmeyen plan")
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        return {"mod": "stub", "url": f"https://odeme.fastkoc.local/checkout?ogrenci={ogrenci_id}&plan={plan}",
                "not": "STRIPE_SECRET_KEY yok; test linki. Gercek odeme icin anahtari tanimlayin."}
    try:
        veri = urllib.parse.urlencode({
            "mode": "subscription",
            "success_url": f"https://fastkoc.app/odeme/basarili?ogrenci={ogrenci_id}",
            "cancel_url": "https://fastkoc.app/odeme/iptal",
            "line_items[0][price_data][currency]": "try",
            "line_items[0][price_data][unit_amount]": str(PLANLAR[plan]["ucret"] * 100),
            "line_items[0][price_data][product_data][name]": f"Fast Koc {plan}",
            "line_items[0][quantity]": "1",
        }).encode()
        req = urllib.request.Request("https://api.stripe.com/v1/checkout/sessions", data=veri,
                                     headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=12) as r:
            js = json.loads(r.read().decode())
        return {"mod": "stripe", "url": js.get("url", ""), "session": js.get("id", "")}
    except Exception as e:
        return {"mod": "stripe-hata", "url": "", "not": str(e)[:200]}


def pro_aktif_et(db: Session, ogrenci_id: int, session_id: str = "") -> Abonelik:
    ab = Abonelik(ogrenci_id=ogrenci_id, plan="pro", stripe_session=session_id,
                  bitis=datetime.utcnow() + timedelta(days=30))
    db.add(ab); db.commit(); db.refresh(ab)
    return ab


def pro_gerekli(ogrenci_id: int, db: Session = Depends(get_db)):
    if plan_of(db, ogrenci_id) == "pro":
        return True
    if os.environ.get("ODEME_ZORUNLU", "false").lower() == "true":
        raise HTTPException(402, "pro gerekli")
    return True  # MVP'de acik
