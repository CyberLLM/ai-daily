import json
import os
from datetime import datetime, timezone, timedelta

from config import HISTORY_DAYS, HISTORY_FILE
from dedup import canonical_url


# =========================================================
# HISTORIA OPUBLIKOWANYCH NEWSÓW
#
# Okno pobierania to dwie doby, więc ten sam artykuł potrafi
# wrócić nazajutrz. Trzymamy więc listę URL-i, które już
# poszły na stronę, i odsiewamy je przy kolejnym wydaniu.
#
# Kluczem jest URL, nie tytuł: model tłumaczy tytuły na polski,
# więc porównywanie ich między dniami i tak by nic nie dało.
#
# Porównujemy adres sprowadzony do postaci kanonicznej. Ten sam
# artykuł potrafi przyjść raz z parametrem UTM, raz bez - i bez
# tego wracał na stronę drugi dzień z rzędu mimo historii.
# Kanonizacja przy odczycie oznacza, że stare wpisy zapisane
# w surowej postaci też się dopasują.
# =========================================================


def load_history():
    """Wczytuje historię, pomijając wpisy starsze niż HISTORY_DAYS."""

    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Uszkodzona historia nie może wywrócić całego wydania
        print("Uwaga: nie udało się wczytać historii, zaczynam od pustej.")
        return []

    if not isinstance(entries, list):
        return []

    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)
    ).date().isoformat()

    return [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("published_on", "") >= cutoff
    ]


def published_urls():
    """Zbiór kanonicznych URL-i opublikowanych w ostatnich HISTORY_DAYS dniach."""

    return {
        canonical_url(entry["url"])
        for entry in load_history()
        if entry.get("url")
    }


def remember(items):
    """Dopisuje właśnie opublikowane newsy i przycina stare wpisy."""

    entries = load_history()
    known = {canonical_url(entry.get("url", "")) for entry in entries}

    today = datetime.now(timezone.utc).date().isoformat()

    added = 0

    for item in items:

        url = item.get("url", "").strip()
        key = canonical_url(url)

        if not url or key in known:
            continue

        # Zapisujemy adres w oryginalnej postaci - jest też
        # materiałem do wglądu, nie tylko kluczem porównania.
        entries.append({
            "url": url,
            "title": item.get("title", ""),
            "published_on": today,
        })

        known.add(key)
        added += 1

    directory = os.path.dirname(HISTORY_FILE)

    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    return added, len(entries)
