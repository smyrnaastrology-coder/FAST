import os, sys, traceback

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.chdir(BASE)

print("CWD:", os.getcwd())
print("Root icerigi:", sorted(os.listdir(".")))

try:
    from backend.main import app_fast
    print("IMPORT OK: backend.main")
except Exception:
    traceback.print_exc()
    print("--- main.py nerede araniyor ---")
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", "node_modules")]
        if "main.py" in files:
            print("main.py bulundu:", root)
    sys.exit(1)

import uvicorn
port = int(os.environ.get("PORT", "8000"))
print(f"Uvicorn {port} portunda basliyor...")
uvicorn.run(app_fast, host="0.0.0.0", port=port)
