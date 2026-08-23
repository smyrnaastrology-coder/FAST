"""Soru logu + outcome - JSONL"""
import json, os, datetime

LOG = os.path.join(os.path.dirname(__file__), "..", "data", "questions.jsonl")

def log_question(q, engine_json, outcome=None):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    rec={"ts":datetime.datetime.utcnow().isoformat(),"question":q,"engine":engine_json,"outcome":outcome}
    with open(LOG,"a",encoding="utf-8") as f:
        f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    return rec

def set_outcome(idx, outcome):
    # outcome: YES/NO/UNCERTAIN realized
    pass
