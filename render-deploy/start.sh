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
# -u: stdout'u tamponlamasın. Render'da PYTHONUNBUFFERED tanimli degilse
# python ciktisi blok tamponlanip hic gorunmuyor; bu yuzden hata mesajlari
# (orn. psycopg2 baglanti hatasi) loga hic dusmuyordu.
exec python -u run.py
