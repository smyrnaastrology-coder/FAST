import json, os, hashlib, secrets, string
from datetime import datetime, timedelta
DB="horary_oracle/users.json"
def _load():
    if not os.path.exists(DB): return {}
    try: return json.load(open(DB,encoding='utf-8'))
    except: return {}
def _save(d): json.dump(d, open(DB,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
def hash_pass(p): return hashlib.sha256(p.encode()).hexdigest()
def gen_pass(n=8): return ''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(n))
def create_user(email, days=365):
    db=_load(); pwd=gen_pass()
    db[email.lower()]={"pwd":hash_pass(pwd),"expiry":(datetime.now()+timedelta(days=days)).isoformat(),"created":datetime.now().isoformat()}
    _save(db); return pwd
HARDCODED={"smyrnaastrology@gmail.com": "6cEIKsrX", "gokturk_yildiz@hotmail.com": "Es1hMLCK"} # kalici, redeploy'da silinmez
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
            u={"pwd":hash_pass(pwd),"expiry":(datetime.now()+timedelta(days=365)).isoformat(),"device_ids":[device_id],"device_id":device_id}
            db[email.lower()]=u; _save(db)
        elif u and device_id and not u.get("device_ids") and not u.get("device_id"):
            u["device_ids"]=[device_id]; u["device_id"]=device_id; _save(db)
        return True, {"days_left":364,"warn":False,"expiry":(datetime.now()+timedelta(days=365)).isoformat()}
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
    return True, {"days_left":days_left,"warn":warn,"expiry":u["expiry"]}
def extend(email,days=365):
    db=_load(); u=db.get(email.lower())
    if not u: return False
    exp=datetime.fromisoformat(u["expiry"])
    base=exp if exp>datetime.now() else datetime.now()
    u["expiry"]=(base+timedelta(days=days)).isoformat()
    _save(db); return True
