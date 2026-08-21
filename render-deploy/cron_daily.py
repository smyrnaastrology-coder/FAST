"""Günlük bildirim cron — aktif aboneler için Minor Progress push.
Render Cron Job veya Uptime cron ile günlük 00:00 UTC çağrılır.
Gerçek FCM için FIREBASE_CREDENTIALS env gerekir; yoksa dry-run log.
"""
import os, json, sys
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.chdir(str(BASE))

try:
    from backend.billing import _load as _load_subs
    from backend.billing import SUBS_FILE
except Exception:
    SUBS_FILE = BASE / "data" / "subscriptions.json"
    def _load_subs(p): 
        import json
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def main(dry_run=True):
    subs = _load_subs(SUBS_FILE) if SUBS_FILE.exists() else {}
    active = [uid for uid, r in subs.items() if r.get("status")=="active"]
    print(f"[cron] {datetime.utcnow().isoformat()} active subs: {len(active)}")
    for uid in active:
        # TODO: motor rebuild + secondary_progression_analizi + FCM send
        # from core import FBST_Engine; generate daily minor progress snippet -> FCM
        print(f"  -> would push to {uid} {'(dry-run)' if dry_run else ''}")
    return len(active)

if __name__ == "__main__":
    dry = os.getenv("DRY_RUN","1") != "0"
    main(dry_run=dry)
