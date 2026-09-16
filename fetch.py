# =========================================================
# POBIERANIE NEWSÓW
#
# Zadanie: z kilkunastu feedów zrobić pulę, z której model
# ma realnie co wybierać - czyli szeroką, ale nieprzechyloną
# w stronę źródeł, które publikują najwięcej.
#
# Kolejność operacji jest istotna:
#
#   pobranie -> okno czasowe -> filtr słów -> powtórki z historii
#   -> to samo wydarzenie u kilku redakcji -> limit źródła
#   -> limit rodzaju
#
# Limity idą na końcu celowo. Gdyby szły przed odsiewaniem,
# limit źródła zjadłaby powtórka, którą i tak zaraz kasujemy.
#
# Uruchomienie z --preview pokazuje pulę bez zapisu na dysk.
# =========================================================

import html
import json
import re
import socket
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

import feedparser

from config import (
    HOURS_BACK,
    MIN_POOL,
    DAILY_COUNT,
    FETCH_WORKERS,
    FETCH_TIMEOUT,
    FETCH_RETRIES,
    FETCH_RETRY_PAUSE,
    KIND_CAPS,
    MAX_ORG_IN_POOL,
    POOL_WARNING_THRESHOLD,
    SOURCE_SHARE_WARNING,
)
from sources import (
    active_sources,
    priority_of,
    owner_of,
    shared_owners,
    KIND_LABELS,
)
from dedup import canonical_url, normalize_title, title_tokens, same_story
from history import published_urls


PREVIEW = "--preview" in sys.argv

# Zawieszony feed nie może zablokować całego porannego wydania
socket.setdefaulttimeout(FETCH_TIMEOUT)

# Granica świeżości. Liczona raz, przed pobieraniem, żeby wszystkie
# wątki oceniały wpisy względem tego samego momentu.
cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)


# =========================================================
# POMOCNICZE
# =========================================================

def keyword_matcher(keywords):
    """
    Buduje wyrażenie dopasowujące całe słowa.

    Dopasowanie po fragmencie jest tu pułapką: "ai" wpadłoby
    w "said", "detail" i "air", więc feed ogólnotechniczny
    przepuściłby praktycznie wszystko.
    """

    if not keywords:
        return None

    pattern = "|".join(re.escape(word) for word in keywords)

    return re.compile(r"\b(?:%s)\b" % pattern, re.IGNORECASE)


def get_date(entry):
    """
    Pobiera datę niezależnie od tego, czy feed używa RSS czy Atom.
    """

    parsed = (
        entry.get("published_parsed")
        or entry.get("updated_parsed")
        or entry.get("created_parsed")
    )

    if not parsed:
        return None

    return datetime(*parsed[:6], tzinfo=timezone.utc)


# =========================================================
# POBIERANIE POJEDYNCZEGO FEEDU
#
# Funkcja nie rzuca wyjątkami: padnięcie jednego źródła
# nie może wywrócić wydania, więc błąd wraca jako dane.
# =========================================================

def fetch_source(source):

    result = {
        "source": source,
        "error": None,
        "total": 0,
        "fresh": 0,
        "filtered_out": 0,
        "retried": False,
        "items": [],
    }

    # Jedna ponowna próba. Cron leci raz na dobę, więc chwilowy
    # limit zapytań albo zerwane połączenie oznaczałyby źródło
    # wypadające z wydania na cały dzień. Przy siedemnastu feedach
    # uderzanych równolegle zdarza się to realnie.
    feed = None

    for attempt in range(FETCH_RETRIES + 1):

        if attempt:
            time.sleep(FETCH_RETRY_PAUSE)

        try:
            feed = feedparser.parse(source.url)
        except Exception as error:
            result["error"] = str(error)
            continue

        status = feed.get("status")

        if status and status >= 400:
            result["error"] = "HTTP %s" % status
            continue

        if not feed.entries:
            result["error"] = "feed nie zwrócił wpisów"
            continue

        result["error"] = None
        result["retried"] = bool(attempt)
        break

    if result["error"] or feed is None:
        return result

    result["total"] = len(feed.entries)

    matcher = keyword_matcher(source.keywords)

    for entry in feed.entries:

        # Część feedów (m.in. The Verge) oddaje tytuły z encjami
        # HTML. Bez odkodowania "Meta&#8217;s" jedzie tak do modelu,
        # a potem na stronę.
        title = html.unescape(entry.get("title", "")).strip()
        url = entry.get("link", "").strip()

        if not title or not url:
            continue

        published = get_date(entry)

        # Nie znamy daty - nie wiemy, czy news jest dzisiejszy
        if published is None:
            continue

        if published < cutoff:
            continue

        result["fresh"] += 1

        # Filtr tylko po tytule, nie po zajawce. Zajawka bywa
        # długa i trafia w słowo kluczowe przypadkiem.
        if matcher and not matcher.search(title):
            result["filtered_out"] += 1
            continue

        result["items"].append({
            "source": source.name,
            "kind": source.kind,
            "title": title,
            "url": url,
            "date": published.isoformat(),
        })

    return result


# =========================================================
# POBRANIE WSZYSTKIEGO RÓWNOLEGLE
# =========================================================

sources = active_sources()

print("Pobieram %d źródeł, okno %d godzin.\n" % (len(sources), HOURS_BACK))

with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
    results = list(pool.map(fetch_source, sources))


# =========================================================
# RAPORT ZE ŹRÓDEŁ
#
# Feed potrafi umrzeć po cichu i pula chudnie niezauważenie,
# więc martwe źródła mają być widoczne w logu od razu.
# =========================================================

print("ŹRÓDŁA")

dead = []

for result in results:

    source = result["source"]

    if result["error"]:
        dead.append(source.name)
        print("  %-24s BŁĄD: %s" % (source.name, result["error"]))
        continue

    line = "  %-24s %3d wpisów, świeżych: %3d" % (
        source.name, result["total"], result["fresh"]
    )

    if result["filtered_out"]:
        line += ", odsianych filtrem: %d" % result["filtered_out"]

    if result["retried"]:
        line += "   (druga próba)"

    print(line)

if dead:
    print("\n  UWAGA: nie odpowiedziało %d z %d źródeł (%s)."
          % (len(dead), len(sources), ", ".join(dead)))


# =========================================================
# ZŁOŻENIE PULI
# =========================================================

all_news = []
seen_titles = set()
seen_urls = set()

for result in results:
    for item in result["items"]:

        key = normalize_title(item["title"])
        url_key = canonical_url(item["url"])

        # Dokładny duplikat - ten sam tytuł lub ten sam adres
        if key in seen_titles or url_key in seen_urls:
            continue

        seen_titles.add(key)
        seen_urls.add(url_key)

        item["url_key"] = url_key
        item["org"] = owner_of(item["source"])
        item["tokens"] = title_tokens(item["title"])

        all_news.append(item)

all_news.sort(key=lambda x: x["date"], reverse=True)

pool_after_fetch = len(all_news)


# =========================================================
# ODSIEWANIE NEWSÓW JUŻ OPUBLIKOWANYCH
#
# Okno pobierania liczy dwie doby, więc bez tego ten sam
# artykuł potrafiłby trafić na stronę drugi dzień z rzędu.
# =========================================================

already_published = published_urls()

fresh_news = [
    item
    for item in all_news
    if item["url_key"] not in already_published
]

repeats = len(all_news) - len(fresh_news)

if len(fresh_news) >= MIN_POOL:
    all_news = fresh_news
else:
    # Pula zrobiła się za chuda - lepiej powtórzyć news
    # niż zostawić model bez materiału do wyboru.
    print("\nUwaga: po odsianiu powtórek zostałoby %d newsów "
          "(próg to %d). Dopuszczam powtórki." % (len(fresh_news), MIN_POOL))
    repeats = 0


# =========================================================
# TO SAMO WYDARZENIE U KILKU REDAKCJI
#
# Przechodzimy w kolejności z rejestru źródeł, nie po dacie:
# przy dwóch opisach tego samego zostaje ten ze źródła, któremu
# ufamy bardziej, a nie ten, który przypadkiem wyszedł minutę
# wcześniej.
# =========================================================

by_priority = sorted(
    all_news,
    key=lambda x: (priority_of(x["source"]), x["date"])
)

kept = []
duplicates = []

for item in by_priority:

    twin = next(
        (other for other in kept if same_story(item["tokens"], other["tokens"])),
        None
    )

    if twin:
        duplicates.append((item, twin))
        continue

    kept.append(item)

kept_ids = {id(item) for item in kept}

all_news = [item for item in all_news if id(item) in kept_ids]


# =========================================================
# LIMIT NA ŹRÓDŁO I NA RODZAJ ŹRÓDŁA
#
# Limit źródła pilnuje, żeby serwis nie był skrótem jednej
# redakcji. Limit rodzaju pilnuje, żeby nie był ścianą
# komunikatów prasowych - pięć blogów firmowych z limitem 2
# to wciąż dziesięć materiałów firmowych w puli.
# =========================================================

caps = {source.name: source.cap for source in sources}

# Limit organizacji dotyczy tylko firm z kilkoma feedami.
# Dla reszty nadawca równa się źródłu, więc limit źródła
# już wszystko załatwia.
capped_owners = shared_owners()

news = []
source_counts = defaultdict(int)
kind_counts = defaultdict(int)
org_counts = defaultdict(int)

over_source = 0
over_kind = 0
over_org = 0

for item in all_news:

    source_name = item["source"]
    kind = item["kind"]
    org = item["org"]

    if source_counts[source_name] >= caps.get(source_name, 3):
        over_source += 1
        continue

    if kind_counts[kind] >= KIND_CAPS.get(kind, 99):
        over_kind += 1
        continue

    # Jedna firma potrafi mieć kilka feedów - limit na źródło
    # przepuściłby trzy materiały Google z trzech różnych blogów.
    if org in capped_owners and org_counts[org] >= MAX_ORG_IN_POOL:
        over_org += 1
        continue

    news.append(item)
    source_counts[source_name] += 1
    kind_counts[kind] += 1
    org_counts[org] += 1


# =========================================================
# RAPORT Z ODSIEWANIA
# =========================================================

print("\nODSIEWANIE (z %d pobranych)" % pool_after_fetch)
print("  powtórki z poprzednich wydań:      %3d" % repeats)
print("  to samo wydarzenie, inna redakcja: %3d" % len(duplicates))
print("  ponad limit źródła:                %3d" % over_source)
print("  ponad limit rodzaju źródła:        %3d" % over_kind)
print("  ponad limit organizacji:           %3d" % over_org)

if duplicates:
    print("\n  Zduplikowane wydarzenia:")
    for item, twin in duplicates[:6]:
        print("    - %s: %s" % (item["source"], item["title"][:58]))
        print("      zostaje %s: %s" % (twin["source"], twin["title"][:58]))


# =========================================================
# SKŁAD PULI
# =========================================================

print("\nDO SELEKCJI TRAFIA %d NEWSÓW" % len(news))

print("\n  wg rodzaju źródła:")
for kind, count in sorted(kind_counts.items(), key=lambda x: -x[1]):
    print("    %-34s %2d" % (KIND_LABELS.get(kind, kind), count))

print("\n  wg źródła:")
for source_name, count in sorted(source_counts.items(), key=lambda x: -x[1]):
    share = count / len(news) if news else 0
    flag = "  <-- dominuje" if share > SOURCE_SHARE_WARNING else ""
    print("    %-24s %2d  (%2.0f%%)%s" % (source_name, count, share * 100, flag))


# =========================================================
# KONTROLA JAKOŚCI
# =========================================================

if len(news) < DAILY_COUNT:
    raise SystemExit(
        "\nBŁĄD: pula ma %d newsów, a wydanie potrzebuje %d. "
        "Przerywam - lepiej zostawić wczorajsze wydanie niż wydać byle co."
        % (len(news), DAILY_COUNT)
    )

if len(news) < POOL_WARNING_THRESHOLD:
    print("\n  UWAGA: pula poniżej %d newsów - selekcja robi się pozorna. "
          "Sprawdź listę źródeł w sources.py." % POOL_WARNING_THRESHOLD)


# =========================================================
# ZAPIS
#
# Pola pomocnicze (url_key, tokens) zostają tutaj - dalej
# w pipelinie nikt ich nie potrzebuje, a tokens to zbiór,
# którego JSON i tak by nie zapisał.
# =========================================================

if PREVIEW:
    print("\n[--preview] Nic nie zapisuję. Pula wyglądałaby tak:\n")
    for i, item in enumerate(news, start=1):
        print("  %2d. [%s] %s" % (i, item["source"], item["title"][:70]))
    raise SystemExit(0)

payload = [
    {
        "source": item["source"],
        "kind": item["kind"],
        "org": item["org"],
        "title": item["title"],
        "url": item["url"],
        "date": item["date"],
    }
    for item in news
]

with open("data/news.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
