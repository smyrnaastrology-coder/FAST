#!/bin/bash
echo "=== FBST START SCRIPT ==="
echo "--- Konum ---"
pwd
echo "--- Repo icerigi ---"
ls -la
echo "--- Python ---"
python --version
echo "--- PORT env ---"
echo "PORT=$PORT"
echo "--- Import testi ---"
cd "$(dirname "$0")" || exit 1
python - <<'EOF'
import os, sys, traceback
print("CWD:", os.getcwd())
print("Root dosyalari:", sorted(os.listdir(".")))
if os.path.isdir("backend"):
    print("backend/:", sorted(os.listdir("backend")))
if os.path.isdir("core"):
    print("core/:", sorted(os.listdir("core")))
try:
    import backend.main
    print("IMPORT OK: backend.main")
except Exception:
    traceback.print_exc()
    sys.exit(1)
EOF
echo "--- Uvicorn baslatiliyor ---"
exec uvicorn backend.main:app_fast --host 0.0.0.0 --port "${PORT:-8000}"
