import json, os, hashlib, secrets, string, threading, shutil
from datetime import datetime, timedelta

# DB yolu: hem root'tan (uvicorn api:app) hem horary_oracle içinden çalıştırılsa doğru
_BASE = os.path.dirname(os.path.abspath(__file__))
# RUNTIME DB: git'te OLMAYAN dosya.
#
# DIKKAT (2026-10): Render free plan'da kalici disk YOKTUR ve bu dosya deploy
# dizininde (gecici dosya sistemi) duruyor. Her redeploy / dyno yeniden
# baslatmada / uyku-uyanma dongusunda SILINIR. Silinen dosya bir sonraki
# istekte bos veri olarak okunur ve kullanici kaydi 100 krediyle YENIDEN
# OLUSTURULUR -> kullanici "99 kredim geri 100 oldu" diyordu.
# Kalici depolama USERS_DB ile baglanmalidir (bkz. render.yaml).
DB = os.getenv("USERS_DB") or os.path.join(_BASE, "users_runtime.json")
LEGACY = os.path.join(_BASE, "users.json")
AUDIT = os.getenv("HORARY_AUDIT_DB") or os.path.join(_BASE, "horary_credit_audit.jsonl")

# Tum yazma islemleri tek kilitte. Once kilit yoktu: iki es zamanli istekten
# biri okudugu bayagi digerinin uzerine yaziyordu (kredi kaybi).
_LOCK = threading.RLock()

# kredi varsayilanlari (env ile degistirilebilir)
def _envint(name, default):
    try: return int(os.getenv(name, default))
    except: return default
DEFAULT_CREDITS = _envint("DEFAULT_CREDITS", 100)   # yeni hesap acilisinda
TRIAL_CREDITS = _envint("TRIAL_CREDITS", 10)       # 2 gun deneme kayitlari


class StorageError(RuntimeError):
    """DB okunamadi/yazilamadi. ESKIDEN bu sessizce yutulup {} donuyordu;
    sonuc: butun krediler bir anda sifirliyor ve kullanici 'kayit yok'
    gorunuyordu. Simdi hata yukselir ve dosya yedeklenir."""


def _audit(event, **kw):
    """Kredi hareketleri ve veri kaybi olaylari. Sifirdan bakilabilsin ki
    'kredim neden geri geldi?' sorusu cevaplanabilsin."""
    try:
        rec = {"ts": datetime.now().isoformat(), "event": event}
        rec.update(kw)
        with open(AUDIT, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _log(msg):
    try:
        import sys
        print(f"[auth] {msg}", file=sys.stderr, flush=True)
    except Exception:
        pass


def _quarantine(reason):
    """Bozuk dosyayi zaman damgasiyla yedekle ki veri incelenebilsin."""
    try:
        if os.path.exists(DB):
            shutil.copy2(DB, f"{DB}.corrupt-{datetime.now():%Y%m%d-%H%M%S}")
    except Exception:
        pass
    _log(f"CRITICAL DB bozuk ({reason}); yedeklendi. SILINDI: {DB}")
    _audit("storage_corrupt", reason=reason)


def migrate_legacy_once():
    """Eski (git'teki) users.json'dan TEK SEFERLIK kredi tasima - SADECE
    elle cagrilir (admin/terminal). Uygulama acilista ASLA cagrilmaz.

    NEDEN KALDIRILDI: bu mantik her DB yoklugunda devreye giriyordu. Render
    free plan'da kalici disk olmadigi icin DB her redeploy'da siliniyor ve
    eski 100 kredili yedek geri geliyordu - kullanicinin "99 kredim geri
    100 oldu" dedigi durumun ikinci sebebi buydu. Artik hicbir sey kendiliginden
    geri gelmez.

    Kalicilik dogrusu USERS_DB + kalici disk; bu sadece gecis araci."""
    if not os.path.exists(LEGACY):
        return False, "legacy dosya yok"
    try:
        with open(LEGACY, encoding="utf-8") as f:
            old = json.load(f)
        if not isinstance(old, dict) or not old:
            return False, "legacy dosya bos/gecersiz"
        if os.path.exists(DB):
            return False, f"{DB} zaten var - mevcut kredilerin uzerine yazilmayacak"
        old["__migrated_from_legacy"] = time_now()
        _atomic_write(old)
        n = len([k for k in old if not k.startswith("__")])
        _audit("migrated_legacy", n=n)
        _log(f"eski users.json migrate edildi ({n} kayit)")
        return True, f"{n} kayit aktarildi"
    except Exception as e:
        return False, str(e)


def time_now():
    import time
    return time.time()


def _load():
    """DB'yi okur. Dosya yoksa {} (ilk kullanim). Bozuk/yarim dosyada SILENTCE
    bos donme YOK - veri kaybi gizlenmesin diye hata yukselir.

    Burada HICBIR sey kendiliginden geri yuklenmez. Gecmise donus yolu
    (legacy migrate) bilerek cikarildi: Render'in gecici diski DB'yi her
    deploy'da siliyor ve her yeniden yuklemede krediler 100'e donuyordu."""
    if not os.path.exists(DB):
        return {}
    try:
        with open(DB, "r", encoding="utf-8") as f:
            txt = f.read()
    except Exception as e:
        _audit("storage_unreadable", error=str(e)[:200])
        raise StorageError(f"kullanici DB'si okunamadi: {e}")
    if not txt.strip():
        return {}
    try:
        d = json.loads(txt)
    except Exception as e:
        _quarantine(f"json bozuk: {str(e)[:120]}")
        raise StorageError("kullanici DB'si bozuk - geri yuklenmeli")
    if not isinstance(d, dict):
        _quarantine("kok dizi degil")
        raise StorageError("kullanici DB'si beklenmeyen bicimde")
    return d


def _atomic_write(d):
    """Once gecici dosyaya yaz, sonra yerine koy. Yarida kesilen yazim
    dosyayi bozmasin (bozuk dosya = tum krediler sifirlanirdi)."""
    tmp = f"{DB}.tmp{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, DB)


def _save(d):
    with _LOCK:
        _atomic_write(d)


def update(mutator):
    """Kilidi tutar: oku -> mutator(db) -> yaz.

    Bunun yerine ayri ayri _load()/_save() kullanmak yarista kayip yazmaya
    yol acar: A 100 okur, B 1 harcar ve yazar, A 100'u geri yazar -> kredi
    HESAPTA KALIR. Tek kilit bunu imkansiz kilar.
    """
    with _LOCK:
        db = _load()
        out = mutator(db)
        _atomic_write(db)
        return out


def _resolve_credits(u, email=""):
    """credits anahtari olmayan kayitlar icin guvenli kural.

    ONCEDEN: burada DEFAULT_CREDITS (100) yaziliyordu. Bozulan/eksik bir
    kayit aninda 100 bedava soruya donuyordu - '99 kredi geri 100 oldu'
    belirtisinin bir parcasi buydu. Artik deneme kredisi verilir, kalici
    yazilir ve denetime yazilir.
    """
    if u.get("credits") is None:
        u["credits"] = TRIAL_CREDITS
        _audit("credits_missing_resolved", email=email, assigned=TRIAL_CREDITS)
        _log(f"KRITIK: {email} kaydinda 'credits' anahtari yok -> {TRIAL_CREDITS} atandi")
    return u


def get_user(email):
    """Kayitli kullaniciyi dondurur, yoksa None."""
    u = _load().get((email or "").strip().lower())
    if not u: return None
    return _resolve_credits(u, email)


def spend_credit(email, amount=1):
    """Kredi dusur + yeni bakiyeyi dondur. Ayni hesabin tum kayitlari (email +
    kullaniciadi alias'i) birlikte duser; aksi halde alias ile girip tekrar
    kredi kazanilirdi. None = kullanici yok.

    Tum oku-degistir-yaz tek kilit icinde olur; yarista kayip yazma olmaz."""
    e = (email or "").strip().lower()
    before = after = None

    def _mut(db):
        nonlocal before, after
        u = db.get(e)
        if u is None:
            return None
        _resolve_credits(u, e)
        # ayni hesabin butun anahtarlari: e, alias_of zinciri, e'nin kullaniciadi
        keys = {e}
        if u.get("alias_of"): keys.add(str(u["alias_of"]).lower())
        if "@" in e: keys.add(e.split("@")[0])
        seen = set()
        while True:
            new = set(keys) - seen
            if not new: break
            seen |= new
            for k in new:
                rec = db.get(k)
                if rec is None: continue
                if rec.get("alias_of"): keys.add(str(rec["alias_of"]).lower())
                _resolve_credits(rec, k)
                before = rec.get("credits")
                rec["credits"] = max(0, before - amount)
        after = u["credits"]
        return u["credits"]

    left = update(_mut)
    if left is None:
        return None
    _audit("spend", email=e, amount=amount, before=before, after=after)
    return left


def hash_pass(p): return hashlib.sha256(p.encode()).hexdigest()
def gen_pass(n=8): return ''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(n))
def create_user(email, days=365, credits=None):
    """Yeni kayit: 2 gun deneme (trial). 1 yil lisans icin extend() cagrilir.
    credits=None -> TRIAL_CREDITS (eskiden anahtar hic yazilmazdi => 'sinirsiz')."""
    db=_load(); pwd=gen_pass()
    if credits is None: credits = TRIAL_CREDITS
    e=(email or "").strip().lower()
    db[e]={"pwd":hash_pass(pwd),"expiry":(datetime.now()+timedelta(days=days)).isoformat(),"created":datetime.now().isoformat(),"credits":credits}
    _save(db); _audit("create_user", email=e, credits=credits, days=days)
    return pwd

HARDCODED={"smyrnaastrology@gmail.com": "Tuana21.", "gokturk_yildiz@hotmail.com": "Es1hMLCK"} # kalici, redeploy'da silinmez - deneme kullanicilari runtime DB'de 2 gun
DEFAULT_PLAN={"smyrnaastrology@gmail.com":"elite", "gokturk_yildiz@hotmail.com":""}
# Ilk hardcoded giris yapan hesap bu olur; testlerde kullanilir.
HARDCODED_KEY = sorted(HARDCODED)[0]

def _plan_of(u, email):
    p = u.get("plan") if u and u.get("plan") is not None else DEFAULT_PLAN.get(email, "")
    return p


def verify(email,pwd, device_id=None):
    # 2 cihaz izni (1 Android + 1 Apple/iOS aynı e-mail ile girsin)
    def _check_devices(u, did):
        ids = u.get("device_ids") or ([u["device_id"]] if u.get("device_id") else [])
        if did in ids: return True, ""
        if len(ids) >= 2:
            return False, "bu hesap 2 cihazda aktif - 3. cihaza izin yok (admin sıfırlar)"
        ids.append(did); u["device_ids"]=ids; u["device_id"]=did
        return True, ""

    e = (email or "").strip().lower()
    if e in HARDCODED and pwd == HARDCODED[e]:
        db = _load()
        u = db.get(e)
        if device_id and not u:
            # Kayit YOK. Normalde bu bir hata durumudur; Render'in gecici dosya
            # sistemi DB'yi her deploy'da sildigi icin burasiASIL kayit
            # kaybolmasidir. Sessizce 100 kredi vermek yerine olayı DENETLENEBILIR
            # sekilde kaydediyoruz.
            u = {"pwd": hash_pass(pwd), "expiry": (datetime.now()+timedelta(days=365)).isoformat(),
                 "created": datetime.now().isoformat(), "device_ids": [device_id],
                 "device_id": device_id, "credits": DEFAULT_CREDITS,
                 "plan": DEFAULT_PLAN.get(e, "")}
            db[e] = u; _save(db)
            _audit("HARDCODED_RECREATED", email=e, credits=DEFAULT_CREDITS,
                   cause="kayit bulunamadi - DB dosyasi silinmis olabilir (gecici disk)")
            _log(f"KRITIK: {e} kaydi yoktu, {DEFAULT_CREDITS} krediyle yeniden olusturuldu. "
                 f"DB kalici diskte DEGILSE bu her deploy'da tekrarlanir.")
        else:
            def _mut(db):
                uu = db.get(e)
                if uu is None: return
                if device_id:
                    _check_devices(uu, device_id)
            if device_id:
                update(_mut)
        _u = _load().get(e)
        _plan = _plan_of(_u, e)
        _cr = _resolve_credits(dict(_u), e)["credits"] if _u else DEFAULT_CREDITS
        if _u and _u.get("expiry"):
            try:
                _exp = datetime.fromisoformat(_u["expiry"])
                _dl = max(0, (_exp - datetime.now()).days)
                return True, {"days_left": _dl, "warn": _dl <= 30, "expiry": _u["expiry"], "plan": _plan, "credits": _cr}
            except Exception: pass
        return True, {"days_left":364,"warn":False,"expiry":(datetime.now()+timedelta(days=365)).isoformat(),"plan":_plan,"credits":_cr}

    db=_load(); u=db.get(e)
    if not u: return False, "kullanici yok"
    if u["pwd"]!=hash_pass(pwd): return False, "sifre yanlis"
    if device_id:
        # DIKKAT: burada KESINLIKLE _save(db) kullanma. verify() cihaz listesini
        # gunceller ama kredilere dokunmaz; ayri bir _save(db) bayagi yazip
        # es zamanli harcamayi SILER. Bu, canli yasan "99 kredi geri 100 oldu"
        # hatasinin birinci sebebiydi: uygulama acilirken arka planda verify()
        # calisir ve ayni anda sorulan sorunun harcanan kredisini geri getirir.
        err = [None]

        def _dev(db2):
            uu = db2.get(e)
            if uu is None:
                return
            ok2, msg2 = _check_devices(uu, device_id)
            if not ok2:
                err[0] = msg2
        update(_dev)
        if err[0]:
            return False, err[0]
        u = _load().get(e) or u
    exp=datetime.fromisoformat(u["expiry"])
    if exp < datetime.now(): return False, "suresi doldu"
    days_left=(exp-datetime.now()).days
    warn = days_left<=30
    _cr = u.get("credits")
    if _cr is None: _cr = TRIAL_CREDITS   # eski kayitlarda credits yoktu -> kaza ile sinirsiz olmasin
    return True, {"days_left":days_left,"warn":warn,"expiry":u["expiry"],"plan":u.get("plan",""),"credits":_cr}

def extend(email,days=365):
    def _mut(db):
        u = db.get((email or "").strip().lower())
        if not u: return False
        exp=datetime.fromisoformat(u["expiry"])
        base=exp if exp>datetime.now() else datetime.now()
        u["expiry"]=(base+timedelta(days=days)).isoformat()
        return True
    return update(_mut)