import json, os, hashlib, secrets, string
from datetime import datetime, timedelta
# DB yolu: hem root'tan (uvicorn api:app) hem horary_oracle içinden çalıştırılsa doğru
_BASE = os.path.dirname(__file__)
# RUNTIME DB: git'te OLMAYAN dosya. Git'e commit'li users.json her Render deploy'unda
# 100 krediye geri donuyordu (98 -> 100 sifirlamasi). Artik ayri, untracked dosya.
DB = os.getenv("USERS_DB") or os.path.join(_BASE, "users_runtime.json")
LEGACY = os.path.join(_BASE, "users.json")
# kredi varsayilanlari (env ile degistirilebilir)
def _envint(name, default):
    try: return int(os.getenv(name, default))
    except: return default
DEFAULT_CREDITS = _envint("DEFAULT_CREDITS", 100)   # kalici/deneme hesaplari
TRIAL_CREDITS = _envint("TRIAL_CREDITS", 10)       # 2 gun deneme kayitlari
def _migrate_legacy():
    """Ilk calistirmada eski (git'teki) users.json'dan kredileri runtime DB'ye tasi.
    Git'e commit'li oldugu icin eski dosya 100 kredide donuyor - sadece ilk migrate icin."""
    if os.path.exists(DB) or not os.path.exists(LEGACY): return
    try:
        old = json.load(open(LEGACY, encoding='utf-8'))
        if old: _save(old)
    except: pass
def _load():
    _migrate_legacy()
    if not os.path.exists(DB): return {}
    try: return json.load(open(DB,encoding='utf-8'))
    except: return {}
def _save(d): json.dump(d, open(DB,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
def get_user(email):
    """Kayitli kullaniciyi dondurur, yoksa None. credits anahtari yoksa varsayilana ceker."""
    u = _load().get((email or "").strip().lower())
    if not u: return None
    if u.get("credits") is None: u["credits"] = DEFAULT_CREDITS
    return u
def spend_credit(email, amount=1):
    """Kredi dusur + yeni bakiyeyi dondur. Ayni hesabin tum kayitlari (email + kullaniciadi
    alias'i) birlikte duser; aksi halde alias ile girip tekrar kredi kazanilirdi.
    None = kullanici yok."""
    e = (email or "").strip().lower()
    db = _load()
    u = db.get(e)
    if u is None: return None
    if u.get("credits") is None: u["credits"] = DEFAULT_CREDITS
    # ayni hesabin butun anahtarlari: e, alias_of zinciri, e'nin kullaniciadi
    keys = {e}
    if u.get("alias_of"): keys.add(u["alias_of"].lower())
    if "@" in e: keys.add(e.split("@")[0])
    for k in list(keys):
        rec = db.get(k)
        if rec is None: continue
        if rec.get("alias_of"): keys.add(str(rec["alias_of"]).lower())
        if rec.get("credits") is None: rec["credits"] = DEFAULT_CREDITS
        rec["credits"] = rec["credits"] - amount
    _save(db)
    return u["credits"]
def hash_pass(p): return hashlib.sha256(p.encode()).hexdigest()
def gen_pass(n=8): return ''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(n))
def create_user(email, days=365, credits=None):
    """Yeni kayit: 2 gun deneme (trial). Suresiz degil, dolunca satın alma gerekir. 1 yil lisans icin extend() cagrilir.
    credits=None -> TRIAL_CREDITS (eskiden anahtar hic yazilmazdi => 'sinirsiz' sayiliyordu)."""
    db=_load(); pwd=gen_pass()
    if credits is None: credits = TRIAL_CREDITS
    db[email.lower()]={"pwd":hash_pass(pwd),"expiry":(datetime.now()+timedelta(days=days)).isoformat(),"created":datetime.now().isoformat(),"credits":credits}
    _save(db); return pwd
HARDCODED={"smyrnaastrology@gmail.com": "Tuana21.", "gokturk_yildiz@hotmail.com": "Es1hMLCK"} # kalici, redeploy'da silinmez - deneme kullanicilari runtime DB'de 2 gun
DEFAULT_PLAN={"smyrnaastrology@gmail.com":"elite", "gokturk_yildiz@hotmail.com":""}
def verify(email,pwd, device_id=None):
    # 2 cihaz izni (1 Android + 1 Apple/iOS aynı e-mail ile girsin)
    def _check_devices(u, did):
        if not did: return True, ""
        ids = u.get("device_ids") or ([u["device_id"]] if u.get("device_id") else [])
        if did in ids: return True, ""
        if len(ids) >= 2:
            return False, "bu hesap 2 cihazda aktif - 3. cihaza izin yok (admin sıfırlar)"
        ids.append(did); u["device_ids"]=ids; u["device_id"]=did
        return True, ""
    if email.lower() in HARDCODED and pwd==HARDCODED[email.lower()]:
        db=_load(); u=db.get(email.lower())
        if device_id and u:
            ok,msg=_check_devices(u, device_id)
            if not ok: return False, msg
            _save(db)
        if device_id and not u:
            # credits/plan YAZILIR: once anahtar hic yazilmiyordu => 'sinirsiz' sayiliyordu
            u={"pwd":hash_pass(pwd),"expiry":(datetime.now()+timedelta(days=365)).isoformat(),"device_ids":[device_id],"device_id":device_id,"credits":DEFAULT_CREDITS,"plan":DEFAULT_PLAN.get(email.lower(),"")}
            db[email.lower()]=u; _save(db)
        elif u and device_id and not u.get("device_ids") and not u.get("device_id"):
            u["device_ids"]=[device_id]; u["device_id"]=device_id; _save(db)
        # elite icin plan bilgisi de dondur
        _u = db.get(email.lower())
        _plan = _u.get("plan") if _u and _u.get("plan") is not None else DEFAULT_PLAN.get(email.lower(),"")
        # credits anahtari yoksa sinirsiz sayilmasin -> varsayilan
        _cr = _u.get("credits") if _u else None
        if _cr is None: _cr = DEFAULT_CREDITS
        # gerçek runtime DB expiry'sini yansıt (hardcoded 364 sabit değil)
        if _u and _u.get("expiry"):
            try:
                _exp = datetime.fromisoformat(_u["expiry"])
                _dl = max(0, (_exp - datetime.now()).days)
                return True, {"days_left": _dl, "warn": _dl <= 30, "expiry": _u["expiry"], "plan": _plan, "credits": _cr}
            except: pass
        return True, {"days_left":364,"warn":False,"expiry":(datetime.now()+timedelta(days=365)).isoformat(),"plan":_plan,"credits":_cr}
    db=_load(); u=db.get(email.lower())
    if not u: return False, "kullanici yok"
    if u["pwd"]!=hash_pass(pwd): return False, "sifre yanlis"
    if device_id:
        ok,msg=_check_devices(u, device_id)
        if not ok: return False, msg
        _save(db)
    exp=datetime.fromisoformat(u["expiry"])
    if exp < datetime.now(): return False, "suresi doldu"
    days_left=(exp-datetime.now()).days
    warn = days_left<=30
    _cr = u.get("credits")
    if _cr is None: _cr = TRIAL_CREDITS   # eski kayitlarda credits yoktu -> kaza ile sinirsiz olmasin
    return True, {"days_left":days_left,"warn":warn,"expiry":u["expiry"],"plan":u.get("plan",""),"credits":_cr}
def extend(email,days=365):
    db=_load(); u=db.get(email.lower())
    if not u: return False
    exp=datetime.fromisoformat(u["expiry"])
    base=exp if exp>datetime.now() else datetime.now()
    u["expiry"]=(base+timedelta(days=days)).isoformat()
    _save(db); return True
