#!/bin/bash
set -euo pipefail

cd /root/ai-daily

# =========================================================
# OBSŁUGA BŁĘDÓW
#
# Bez tego awaria select.py (padnięte API, zły JSON, zła liczba
# newsów) przepuszczała skrypt dalej, a generate.py publikował
# wczorajszą treść pod dzisiejszą datą.
# =========================================================

fail() {
    local code=$?
    echo "=========================================================="
    echo "BŁĄD: pipeline przerwany $(date '+%Y-%m-%d %H:%M:%S'), kod wyjścia $code"
    echo "Strona NIE została zaktualizowana - zostaje poprzednie wydanie."
    echo "=========================================================="
    exit $code
}

trap fail ERR

echo "=========================================================="
echo "START $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================================="

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

echo "KONIEC $(date '+%Y-%m-%d %H:%M:%S')"
