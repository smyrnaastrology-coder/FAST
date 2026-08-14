#!/bin/bash
echo "=== FBST START SCRIPT v3 ==="
cd "$(dirname "$0")"
echo "--- CWD ---"
pwd
echo "--- Python ---"
python --version
echo "--- PORT env ---"
echo "PORT=$PORT"
echo "--- run.py baslatiliyor ---"
exec python run.py
