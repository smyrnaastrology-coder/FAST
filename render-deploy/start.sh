#!/bin/bash
echo "=== FBST START SCRIPT v2 ==="
echo "--- Python ---"
python --version
echo "--- PORT env ---"
echo "PORT=$PORT"
echo "--- run.py baslatiliyor ---"
exec python run.py
