# =========================================================
# SELEKCJA REDAKCYJNA
#
# Model dostaje ponumerowaną pulę i zwraca numery, nie adresy.
# To jest celowe: URL i nazwa źródła nigdy nie przechodzą przez
# model, tylko doklejamy je z naszych danych po numerze. Dzięki
# temu nie ma jak podać przekręconego albo zmyślonego linku,
# a to jedyna rzecz w tym serwisie, której czytelnik nie
# zweryfikuje samym spojrzeniem na stronę.
# =========================================================

import json
import os
from collections import Counter

from openai import OpenAI

from config import (
    HOURS_BACK,
    DAILY_COUNT,
    MAX_PER_SOURCE_IN_EDITION,
    MAX_VENDOR_IN_EDITION,
    MAX_ORG_IN_EDITION,
)
from sources import KIND_LABELS, VENDOR
from history import remember

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

with open("data/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

if len(news) < DAILY_COUNT:
    raise ValueError(
        f"Za mało newsów do selekcji: {len(news)}, "
        f"a potrzeba co najmniej {DAILY_COUNT}."
    )


# =========================================================
# PULA DLA MODELU
#
# Lista numerowana zamiast zrzutu JSON-a: czytelniejsza dla
# modelu i wyraźnie oddziela to, co ma ocenić (tytuł, źródło,
# rodzaj źródła), od tego, czego ma nie dotykać (adres).
# =========================================================

lines = []

for index, item in enumerate(news):

    opis = "%s | %s | %s" % (
        item["source"],
        KIND_LABELS.get(item.get("kind", ""), "nieznany rodzaj"),
        item["date"][:16].replace("T", " "),
    )

    # Nadawcę dopisujemy tylko wtedy, gdy różni się od nazwy
    # źródła - inaczej w każdej linii stałoby to samo dwa razy.
    org = item.get("org", "")

    if org and org != item["source"]:
        opis += " | nadawca: %s" % org

    lines.append("[%d] %s" % (index, opis))
    lines.append("    %s" % item["title"])

pool = "\n".join(lines)


prompt = f"""
Jesteś redaktorem serwisu:
"{DAILY_COUNT} rzeczy, które warto dziś wiedzieć o AI".

Masz ponumerowaną listę newsów z ostatnich {HOURS_BACK} godzin.

Wybierz dokładnie {DAILY_COUNT} najważniejszych.

Kryteria:
- znaczenie dla rozwoju AI
- wpływ biznesowy
- nowość
- wiarygodność
- różnorodność tematów
- różnorodność źródeł

Zasady:
- maksymalnie {MAX_PER_SOURCE_IN_EDITION} newsy z jednego źródła
- maksymalnie {MAX_VENDOR_IN_EDITION} newsy z blogów firmowych; blog firmowy
  to materiał własny firmy, a nie niezależne doniesienie, więc traktuj go
  z rezerwą i wybieraj tylko wtedy, gdy samo ogłoszenie jest ważne
- maksymalnie {MAX_ORG_IN_EDITION} newsy od jednego nadawcy; jeśli przy newsie
  podany jest nadawca, liczy się on, a nie nazwa źródła - kilka feedów może
  należeć do tej samej firmy
- unikaj kilku newsów dotyczących dokładnie tego samego wydarzenia
- preferuj różne obszary: modele, agenci, biznes, badania, regulacje,
  robotyka, narzędzia
- odrzuć clickbait, autopromocję i drobne aktualizacje produktowe
- nie wymyślaj informacji, których nie ma w tytule; jeśli tytuł jest
  zbyt ogólny, żeby napisać konkretne podsumowanie, wybierz inny news

Dla każdego wybranego newsa zwróć:

- id: numer z listy w nawiasie kwadratowym
- title: krótki tytuł po polsku
- summary: 2 krótkie zdania po polsku
- so_what: jedno konkretne zdanie odpowiadające na pytanie "co z tego wynika?"
- category: jedna kategoria, np. Models, Agents, Business, Research,
  Regulation, Robotics, Tools

Nie zwracaj adresu ani nazwy źródła - dokleimy je sami po numerze.

Zwróć WYŁĄCZNIE poprawny JSON.
Bez markdownu.
Bez komentarzy.
Bez ```json.

Format:

[
  {{
    "id": 0,
    "title": "...",
    "summary": "...",
    "so_what": "...",
    "category": "..."
  }}
]

NEWSY:

{pool}
"""

response = client.chat.completions.create(
    model="gpt-5.6",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

text = response.choices[0].message.content.strip()

# Awaryjne usunięcie bloków markdown, gdyby model mimo instrukcji ich użył
text = text.replace("```json", "").replace("```", "").strip()

try:
    chosen = json.loads(text)
except json.JSONDecodeError:
    print("Błąd: model nie zwrócił poprawnego JSON-a.")
    print("\nOdpowiedź modelu:\n")
    print(text)
    raise

if not isinstance(chosen, list):
    raise ValueError("Odpowiedź modelu nie jest listą.")

if len(chosen) != DAILY_COUNT:
    raise ValueError(
        f"Model zwrócił {len(chosen)} newsów zamiast dokładnie {DAILY_COUNT}."
    )


# =========================================================
# SKLEJENIE WYBORU Z NASZYMI DANYMI
#
# Twarde błędy, bo run_daily.sh przerywa wtedy całe wydanie
# i zostaje wczorajsze. Wolimy powtórzone wydanie niż wydanie
# z linkiem prowadzącym gdzie indziej, niż zapowiada tytuł.
# =========================================================

daily = []
used = []

for entry in chosen:

    if not isinstance(entry, dict) or "id" not in entry:
        raise ValueError(f"Wpis bez numeru newsa: {entry}")

    try:
        index = int(entry["id"])
    except (TypeError, ValueError):
        raise ValueError(f"Numer newsa nie jest liczbą: {entry.get('id')!r}")

    if not 0 <= index < len(news):
        raise ValueError(
            f"Model wskazał news numer {index}, a pula ma {len(news)} pozycji."
        )

    if index in used:
        raise ValueError(f"Model wybrał news numer {index} dwa razy.")

    used.append(index)

    original = news[index]

    daily.append({
        "title": entry.get("title", "").strip(),
        "summary": entry.get("summary", "").strip(),
        "so_what": entry.get("so_what", "").strip(),
        "category": entry.get("category", "").strip(),
        "source": original["source"],
        "url": original["url"],
    })

for item in daily:
    for field in ("title", "summary", "so_what"):
        if not item[field]:
            raise ValueError(f"Pusty {field} w newsie ze źródła {item['source']}.")


# =========================================================
# KONTROLA SKŁADU WYDANIA
#
# Tu tylko ostrzegamy. Naruszenie limitu to wpadka redakcyjna,
# a nie błąd techniczny - szkoda wywalać całe wydanie dlatego,
# że model wziął trzeci news z jednej redakcji.
# =========================================================

source_counts = Counter(item["source"] for item in daily)

org_counts = Counter(
    news[index].get("org") or news[index]["source"]
    for index in used
)

vendor_count = sum(
    1 for index in used if news[index].get("kind") == VENDOR
)

for source_name, count in source_counts.items():
    if count > MAX_PER_SOURCE_IN_EDITION:
        print(f"Uwaga: {count} newsy z jednego źródła ({source_name}), "
              f"limit to {MAX_PER_SOURCE_IN_EDITION}.")

for org_name, count in org_counts.items():
    if count > MAX_ORG_IN_EDITION:
        print(f"Uwaga: {count} newsy od jednego nadawcy ({org_name}), "
              f"limit to {MAX_ORG_IN_EDITION}.")

if vendor_count > MAX_VENDOR_IN_EDITION:
    print(f"Uwaga: {vendor_count} newsy z blogów firmowych, "
          f"limit to {MAX_VENDOR_IN_EDITION}.")


with open("data/daily.json", "w", encoding="utf-8") as f:
    json.dump(
        daily,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"Wybrano TOP {DAILY_COUNT} z puli {len(news)} newsów.")

for i, item in enumerate(daily, start=1):
    print(f'{i}. [{item["source"]}] {item["title"]}')


# =========================================================
# HISTORIA
#
# Zapisujemy dopiero tutaj, po udanej selekcji, żeby nieudany
# przebieg nie "spalił" newsów, które nigdy nie trafiły na stronę.
# =========================================================

added, total = remember(daily)

print(f"\nHistoria: dopisano {added}, łącznie {total} zapamiętanych newsów.")
