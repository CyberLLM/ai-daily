#!/bin/bash
set -euo pipefail

cd /root/ai-daily

source /root/.config/ai-daily.env

python3 fetch.py
python3 select.py
python3 generate.py

# =========================================================
# PUBLIKACJA NA GITHUB PAGES
# =========================================================

if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -q -m "AI DAILY 5 - wydanie $(date +%F)"
    git push -q origin main
    echo "Opublikowano na GitHub Pages."
else
    echo "Brak zmian - nic nie publikuje."
fi
