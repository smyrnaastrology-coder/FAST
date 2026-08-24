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
HARDCODED={"smyrnaastrology@gmail.com": "6cEIKsrX"} # kalici, redeploy'da silinmez (hash ile karsilastir)
def verify(email,pwd):
    # hardcoded sabit sifre (redeploy survive)
    if email.lower() in HARDCODED and pwd==HARDCODED[email.lower()]:
        return True, {"days_left":364,"warn":False,"expiry":(datetime.now()+timedelta(days=365)).isoformat()}
    db=_load(); u=db.get(email.lower())
    if not u: return False, "kullanici yok"
    if u["pwd"]!=hash_pass(pwd): return False, "sifre yanlis"
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
