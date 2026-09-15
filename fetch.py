import json
import re
import socket
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import feedparser

from config import HOURS_BACK, MAX_PER_SOURCE, MIN_POOL
from history import published_urls


# =========================================================
# KONFIGURACJA
# =========================================================

# Zawieszony feed nie może zablokować całego porannego wydania
socket.setdefaulttimeout(20)

feeds = {
    "TechCrunch": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "OpenAI": "https://openai.com/news/rss.xml",
}


# =========================================================
# FUNKCJE
# =========================================================

def normalize_title(title):
    """Upraszcza tytuł, żeby łatwiej wykrywać duplikaty."""
    return re.sub(r"\W+", " ", title.lower()).strip()


def get_date(entry):
    """
    Próbuje pobrać datę niezależnie od tego,
    czy feed używa RSS czy Atom.
    """

    parsed = (
        entry.get("published_parsed")
        or entry.get("updated_parsed")
        or entry.get("created_parsed")
    )

    if not parsed:
        return None

    return datetime(
        parsed.tm_year,
        parsed.tm_mon,
        parsed.tm_mday,
        parsed.tm_hour,
        parsed.tm_min,
        parsed.tm_sec,
        tzinfo=timezone.utc,
    )


# =========================================================
# POBIERANIE
# =========================================================

cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)

all_news = []
seen = set()

for source, feed_url in feeds.items():

    try:
        feed = feedparser.parse(feed_url)
    except Exception as error:
        # Padnięcie jednego źródła nie może wywrócić wydania
        print(f"{source}: BŁĄD pobierania ({error})")
        continue

    total = len(feed.entries)
    fresh = 0

    for entry in feed.entries:

        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()

        if not title or not url:
            continue

        published = get_date(entry)

        # Nie znamy daty → pomijamy
        if published is None:
            continue

        # Za stary news
        if published < cutoff:
            continue

        key = normalize_title(title)

        # Dokładny duplikat
        if key in seen:
            continue

        seen.add(key)
        fresh += 1

        all_news.append({
            "source": source,
            "title": title,
            "url": url,
            "date": published.isoformat(),
        })

    print(f"{source}: {total} wpisów, świeżych: {fresh}")


# =========================================================
# SORTOWANIE
# =========================================================

all_news.sort(
    key=lambda x: x["date"],
    reverse=True
)


# =========================================================
# ODSIEWANIE NEWSÓW JUŻ OPUBLIKOWANYCH
#
# Okno pobierania liczy kilka dni, więc bez tego ten sam
# artykuł potrafiłby trafić na stronę drugi dzień z rzędu.
# =========================================================

already_published = published_urls()

fresh_news = [
    item
    for item in all_news
    if item["url"] not in already_published
]

repeats = len(all_news) - len(fresh_news)

if len(fresh_news) >= MIN_POOL:
    all_news = fresh_news
    print(f"\nOdsiano {repeats} newsów opublikowanych wcześniej.")
else:
    # Pula zrobiła się za chuda — lepiej powtórzyć news
    # niż zostawić model bez materiału do wyboru.
    print(
        f"\nUwaga: po odsianiu powtórek zostałoby {len(fresh_news)} newsów "
        f"(próg to {MIN_POOL}). Dopuszczam powtórki."
    )


# =========================================================
# LIMIT NA JEDNO ŹRÓDŁO
# =========================================================

news = []
source_counts = defaultdict(int)

for item in all_news:

    source = item["source"]

    if source_counts[source] >= MAX_PER_SOURCE:
        continue

    news.append(item)
    source_counts[source] += 1


# =========================================================
# ZAPIS
# =========================================================

with open("data/news.json", "w", encoding="utf-8") as f:
    json.dump(
        news,
        f,
        ensure_ascii=False,
        indent=2
    )


# =========================================================
# PODSUMOWANIE
# =========================================================

print("\nDo selekcji LLM trafia:")

for source, count in source_counts.items():
    print(f"- {source}: {count}")

print(f"\nŁącznie: {len(news)} newsów z ostatnich {HOURS_BACK} godzin.")
