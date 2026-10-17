"""Fast Koc — FastAPI backend (MVP). Calistirma: uvicorn backend.main:app --reload --port 8090 (fast_koc klasorunden)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import date
from typing import List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import get_db, init_db
from backend import models, schemas
from backend.auth import mevcut_kullanici
from backend.engine import analiz_motoru, odev_motoru, yorum_motoru
from backend.engine import mufredat as muf
from backend.services import takvim_seed
from backend.services.kitap_servisi import kitap_oner

from contextlib import asynccontextmanager


@asynccontextmanager
async def _yasam(app: FastAPI):
    init_db()
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        takvim_seed.takvim_seed_yukle(db)
        takvim_seed.katalog_seed_yukle(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Fast Koc API", version="0.3.0", lifespan=_yasam)

# CORS: FASTKOC_CORS_ORIGINS virgulle ayrilmis liste (varsayilan "*").
_cors = os.environ.get("FASTKOC_CORS_ORIGINS", "*").strip()
_origins = ["*"] if _cors == "*" else [o.strip() for o in _cors.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/auth/me")
def auth_me(kullanici: dict = Depends(mevcut_kullanici)):
    return kullanici


@app.post("/api/baglanti")
def baglanti_olustur(b: schemas.BaglantiIn, db: Session = Depends(get_db)):
    for pid in (b.ogrenci_id, b.sahip_id):
        if not db.get(models.Profile, pid):
            raise HTTPException(404, f"profil yok: {pid}")
    var = db.query(models.Baglanti).filter_by(ogrenci_id=b.ogrenci_id, sahip_id=b.sahip_id).first()
    if var:
        var.rol = b.rol; var.durum = "aktif"; db.commit()
        return {"id": var.id, "durum": var.durum}
    k = models.Baglanti(ogrenci_id=b.ogrenci_id, sahip_id=b.sahip_id, rol=b.rol)
    db.add(k); db.commit(); db.refresh(k)
    return {"id": k.id, "durum": k.durum}


@app.get("/api/koc/{sahip_id}/ogrenciler")
def koc_ogrenciler(sahip_id: int, db: Session = Depends(get_db)):
    sahip = db.get(models.Profile, sahip_id)
    if not sahip:
        raise HTTPException(404, "profil yok")
    baglar = db.query(models.Baglanti).filter_by(sahip_id=sahip_id, durum="aktif").all()
    out = []
    for b in baglar:
        o = db.get(models.Profile, b.ogrenci_id)
        if not o:
            continue
        sinav_say = db.query(models.SinavSonuc).filter_by(ogrenci_id=o.id).count()
        gun_say = db.query(models.GunlukLog).filter_by(ogrenci_id=o.id).count()
        out.append({"id": o.id, "ad": o.ad, "segment": o.segment, "seviye": o.seviye,
                    "sinav_sayisi": sinav_say, "gunluk_kayit": gun_say, "baglanti_rol": b.rol})
    return {"sahip": sahip.ad, "ogrenciler": out}


@app.post("/api/cihaz")
def cihaz_kaydet(c: schemas.CihazIn, db: Session = Depends(get_db)):
    if not db.get(models.Profile, c.ogrenci_id):
        raise HTTPException(404, "profil yok")
    var = db.query(models.Cihaz).filter_by(fcm_token=c.fcm_token).first()
    if var:
        var.ogrenci_id = c.ogrenci_id; var.aktif = True; db.commit()
        return {"id": var.id}
    d = models.Cihaz(ogrenci_id=c.ogrenci_id, fcm_token=c.fcm_token, platform=c.platform)
    db.add(d); db.commit(); db.refresh(d)
    return {"id": d.id}


@app.post("/api/push/{ogrenci_id}")
def push_gonder_api(ogrenci_id: int, metin: str = "Bugünkü soru sayını gir!", db: Session = Depends(get_db)):
    from backend.services.push_servisi import push_gonder
    if not db.get(models.Profile, ogrenci_id):
        raise HTTPException(404, "profil yok")
    return push_gonder(db, ogrenci_id, "Fast Koç", metin)


@app.get("/api/plan/{ogrenci_id}")
def plan_getir(ogrenci_id: int, db: Session = Depends(get_db)):
    from backend.services.odeme_servisi import plan_of, PLANLAR
    if not db.get(models.Profile, ogrenci_id):
        raise HTTPException(404, "profil yok")
    plan = plan_of(db, ogrenci_id)
    return {"plan": plan, "ozellikler": PLANLAR[plan]["ozellik"]}


@app.post("/api/odeme/checkout/{ogrenci_id}")
def odeme_checkout(ogrenci_id: int, plan: str = "pro", db: Session = Depends(get_db)):
    from backend.services.odeme_servisi import checkout_link
    if not db.get(models.Profile, ogrenci_id):
        raise HTTPException(404, "profil yok")
    return checkout_link(ogrenci_id, plan)


@app.post("/api/odeme/aktif/{ogrenci_id}")
def odeme_aktif(ogrenci_id: int, session_id: str = "", db: Session = Depends(get_db)):
    from backend.services.odeme_servisi import pro_aktif_et
    if not db.get(models.Profile, ogrenci_id):
        raise HTTPException(404, "profil yok")
    ab = pro_aktif_et(db, ogrenci_id, session_id)
    return {"plan": ab.plan, "bitis": ab.bitis.isoformat() if ab.bitis else None}


@app.get("/api/karne/{ogrenci_id}")
def karne_pdf(ogrenci_id: int, db: Session = Depends(get_db)):
    from backend.services.karne_pdf import karne_pdf_uret
    pr = db.get(models.Profile, ogrenci_id)
    if not pr:
        raise HTTPException(404, "profil yok")
    sinavlar = db.query(models.SinavSonuc).filter_by(ogrenci_id=ogrenci_id).order_by(models.SinavSonuc.tarih).all()
    loglar = db.query(models.GunlukLog).filter_by(ogrenci_id=ogrenci_id).order_by(models.GunlukLog.tarih).all()
    odevler = db.query(models.Odev).filter_by(ogrenci_id=ogrenci_id).order_by(models.Odev.tarih).all()
    if sinavlar:
        analiz = analiz_motoru.cok_sinav_birlestir([{"konular": s.konular} for s in sinavlar])
        kodlar = [k.get("kod", "") for s in sinavlar for k in (s.konular or [])]
    else:
        analiz = {"konular": [], "kritik_sayisi": 0, "ozet_cumle": "Henuz sinav sonucu yok."}
        kodlar = []
    oneriler = kitap_oner(muf.coz(pr.segment), konu_kodlari=kodlar, ogrenci_seviye=pr.seviye, limit=6)
    yaklasan = db.query(models.DenemeTakvim).filter(
        models.DenemeTakvim.segment.in_(muf.takvim_eslesme(pr.segment))).order_by(models.DenemeTakvim.tarih).all()
    pdf = karne_pdf_uret(pr, sinavlar, loglar, odevler, analiz, oneriler, yaklasan)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=fastkoc_karne_{ogrenci_id}.pdf"})


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"ok": db_ok, "app": "fast-koc", "version": "0.3.0", "db": db_ok}


@app.post("/api/profil")
def profil_olustur(p: schemas.ProfilIn, db: Session = Depends(get_db)):
    seg = muf.coz(p.segment)
    pr = models.Profile(ad=p.ad, rol=p.rol, segment=seg, sinif=p.sinif, alan=p.alan,
                        seviye=p.seviye, hedef=p.hedef, gunluk_hedef_soru=p.gunluk_hedef_soru)
    db.add(pr); db.commit(); db.refresh(pr)
    return {"id": pr.id, "ad": pr.ad, "rol": pr.rol, "segment": pr.segment,
            "sistem": muf.sistem_of(pr.segment), "seviye": pr.seviye}


@app.get("/api/profil/{ogrenci_id}")
def profil_getir(ogrenci_id: int, db: Session = Depends(get_db)):
    pr = db.get(models.Profile, ogrenci_id)
    if not pr:
        raise HTTPException(404, "profil yok")
    return {"id": pr.id, "ad": pr.ad, "rol": getattr(pr, "rol", "ogrenci"),
            "segment": muf.coz(pr.segment), "sistem": muf.sistem_of(pr.segment), "sinif": pr.sinif,
            "alan": pr.alan, "seviye": pr.seviye, "hedef": pr.hedef,
            "gunluk_hedef_soru": pr.gunluk_hedef_soru}


@app.post("/api/sinav")
def sinav_kaydet(s: schemas.SinavIn, db: Session = Depends(get_db)):
    pr = db.get(models.Profile, s.ogrenci_id)
    if not pr:
        raise HTTPException(404, "profil yok")
    konular = [k.model_dump() for k in s.konular]
    analiz = analiz_motoru.konu_analiz(konular, segment=pr.segment)
    kayit = models.SinavSonuc(ogrenci_id=s.ogrenci_id, tur=s.tur, ad=s.ad, tarih=s.tarih,
                              ders=s.ders, konular=konular,
                              toplam_dogru=analiz["toplam_dogru"], toplam_yanlis=analiz["toplam_yanlis"],
                              toplam_bos=analiz["toplam_bos"], net=analiz["net"])
    db.add(kayit); db.commit()
    return {"sinav_id": kayit.id, "analiz": analiz}


@app.get("/api/analiz/{ogrenci_id}")
def analiz_getir(ogrenci_id: int, ders: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.SinavSonuc).filter_by(ogrenci_id=ogrenci_id)
    if ders:
        q = q.filter_by(ders=ders)
    sinavlar = q.all()
    if not sinavlar:
        raise HTTPException(404, "sinav sonucu yok")
    birlesik = [{"konular": s.konular} for s in sinavlar]
    pr = db.get(models.Profile, ogrenci_id)
    return analiz_motoru.cok_sinav_birlestir(birlesik) | {"sinav_sayisi": len(sinavlar),
                                                          "segment": muf.coz(pr.segment) if pr else "YKS_ESKI"}


@app.post("/api/gunluk")
def gunluk_kaydet(g: schemas.GunlukLogIn, db: Session = Depends(get_db)):
    var = db.query(models.GunlukLog).filter_by(ogrenci_id=g.ogrenci_id, tarih=g.tarih).first()
    if var:
        var.cozulen_soru = g.cozulen_soru; var.calisilan_dk = g.calisilan_dk; var.notlar = g.notlar
    else:
        db.add(models.GunlukLog(ogrenci_id=g.ogrenci_id, tarih=g.tarih,
                                cozulen_soru=g.cozulen_soru, calisilan_dk=g.calisilan_dk, notlar=g.notlar))
    db.commit()
    # o gunku odevlerle kiyas
    pr = db.get(models.Profile, g.ogrenci_id)
    odevler = db.query(models.Odev).filter_by(ogrenci_id=g.ogrenci_id, tarih=g.tarih).all()
    yorum = yorum_motoru.gunluk_kiyas(pr.gunluk_hedef_soru if pr else 80, g.cozulen_soru,
                                      [o.adet for o in odevler])
    return {"yorum": yorum, "odev_sayisi": len(odevler)}


@app.get("/api/odev/haftalik/{ogrenci_id}")
def haftalik_odev(ogrenci_id: int, db: Session = Depends(get_db)):
    from datetime import timedelta
    pr = db.get(models.Profile, ogrenci_id)
    if not pr:
        raise HTTPException(404, "profil yok")
    sinavlar = db.query(models.SinavSonuc).filter_by(ogrenci_id=ogrenci_id).all()
    if not sinavlar:
        raise HTTPException(404, "once sinav sonucu girin")
    analiz = analiz_motoru.cok_sinav_birlestir([{"konular": s.konular} for s in sinavlar])
    # kitap esleme: her oncelikli konuya 1 kitap
    esleme = {}
    for o in analiz.get("oncelikli", []):
        oner = kitap_oner(pr.segment, ders=None, konu_kodlari=[o["kod"]],
                          ogrenci_seviye=pr.seviye, limit=1)
        if oner:
            esleme[o["kod"]] = f"{oner[0]['baslik']} ({oner[0]['yayin']})"
    plan = odev_motoru.haftalik_plan(pr.seviye, pr.segment, analiz, kitap_esleme=esleme)
    # DB'ye yaz (bu haftayi temizleyip yeniden)
    bugun = date.today()
    hafta = f"{bugun.isocalendar().year}-W{bugun.isocalendar().week:02d}"
    db.query(models.Odev).filter_by(ogrenci_id=ogrenci_id, hafta=hafta).delete()
    for o in plan:
        from datetime import date as _d
        db.add(models.Odev(ogrenci_id=ogrenci_id, hafta=hafta, gun=o["gun"],
                           tarih=_d.fromisoformat(o["tarih"]), ders=o["ders"],
                           konu_kod=o["konu_kod"], konu_baslik=o["konu_baslik"],
                           kaynak_kitap_id=o.get("kaynak", ""), adet=o["adet"],
                           hedef_dk=o.get("hedef_dk", 45)))
    db.commit()
    return {"hafta": hafta, "plan": plan, "analiz_ozet": analiz["ozet_cumle"]}


@app.post("/api/odev/onay")
def odev_onay(o: schemas.OdevOnayIn, db: Session = Depends(get_db)):
    od = db.get(models.Odev, o.odev_id)
    if not od:
        raise HTTPException(404, "odev yok")
    od.yapilan = o.yapilan
    od.durum = "yapildi" if o.yapilan >= od.adet else "eksik"
    db.commit()
    return {"durum": od.durum}


@app.get("/api/kitap/oner/{ogrenci_id}")
def kitap_oner_api(ogrenci_id: int, ders: str | None = None, db: Session = Depends(get_db)):
    pr = db.get(models.Profile, ogrenci_id)
    if not pr:
        raise HTTPException(404, "profil yok")
    sinavlar = db.query(models.SinavSonuc).filter_by(ogrenci_id=ogrenci_id).all()
    kodlar = []
    for s in sinavlar:
        for k in (s.konular or []):
            kodlar.append(k.get("kod", ""))
    return {"oneriler": kitap_oner(muf.coz(pr.segment), ders=ders, konu_kodlari=kodlar,
                                   ogrenci_seviye=pr.seviye, limit=6)}


@app.get("/api/takvim")
def takvim(segment: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.DenemeTakvim).order_by(models.DenemeTakvim.tarih)
    if segment:
        q = q.filter(models.DenemeTakvim.segment.in_(muf.takvim_eslesme(segment)))
    return [{"kod": d.kod, "ad": d.ad, "yayin": d.yayin, "tarih": d.tarih.isoformat(),
             "bitis": d.bitis.isoformat() if getattr(d, "bitis", None) else None,
             "basvuru_son": d.basvuru_son.isoformat() if d.basvuru_son else None,
             "kalan_gun": (d.tarih - date.today()).days,
             "dogrulama_durumu": getattr(d, "dogrulama_durumu", ""),
             "kaynak_url": getattr(d, "kaynak_url", "-")} for d in q.all()]


@app.get("/api/segmentler")
def segmentler():
    return {"donem": "2026-27", "tumu_maarif": muf.tumu_maarif_donemi(),
            "segmentler": [{"kod": k, **v} for k, v in muf.SEGMENT_META.items()],
            "secilebilir": muf.secilebilir_segmentler()}


@app.post("/api/optik")
def optik_hesapla(anahtar: str, cevap: str):
    from backend.engine.optik import optik_karsilastir
    try:
        return optik_karsilastir(anahtar, cevap)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/sms/{ogrenci_id}")
def sms_gonder_api(ogrenci_id: int, telefon: str, metin: str = "Fast Koc: bugunku odev kontrolu yapildi.",
                   db: Session = Depends(get_db)):
    from backend.services.sms_servisi import sms_gonder
    if not db.get(models.Profile, ogrenci_id):
        raise HTTPException(404, "profil yok")
    try:
        return sms_gonder(db, ogrenci_id, telefon, metin)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/koc-yorum/{ogrenci_id}")
def koc_yorum_api(ogrenci_id: int, db: Session = Depends(get_db)):
    from backend.services.koc_yorumu import koc_yorumu_uret
    pr = db.get(models.Profile, ogrenci_id)
    if not pr:
        raise HTTPException(404, "profil yok")
    sinavlar = db.query(models.SinavSonuc).filter_by(ogrenci_id=ogrenci_id).all()
    if not sinavlar:
        raise HTTPException(404, "once sinav sonucu girin")
    analiz = analiz_motoru.cok_sinav_birlestir([{"konular": s.konular} for s in sinavlar])
    return koc_yorumu_uret(analiz, ad=pr.ad, segment=muf.coz(pr.segment))


@app.get("/api/bildirim/{ogrenci_id}")
def bildirimler(ogrenci_id: int, db: Session = Depends(get_db)):
    # Salt okunur: uretim yan etkisi yok. Uretim cron (jobs/gunluk_push) ile yapilir.
    bils = db.query(models.Bildirim).filter_by(ogrenci_id=ogrenci_id).order_by(models.Bildirim.id.desc()).limit(20).all()
    return {"okunmamis": sum(1 for b in bils if not b.okundu),
            "bildirimler": [{"id": b.id, "tip": b.tip, "kanal": getattr(b, "kanal", "uygulama_ici"),
                             "metin": b.metin, "okundu": b.okundu,
                             "tarih": b.tarih.isoformat()} for b in bils]}


@app.post("/api/bildirim/{bildirim_id}/oku")
def bildirim_oku(bildirim_id: int, db: Session = Depends(get_db)):
    b = db.get(models.Bildirim, bildirim_id)
    if not b:
        raise HTTPException(404, "bildirim yok")
    b.okundu = True
    db.commit()
    return {"id": b.id, "okundu": True}
