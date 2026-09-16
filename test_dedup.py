# =========================================================
# TESTY ODSIEWANIA POWTÓRZEŃ
#
# Uruchomienie: python3 test_dedup.py
#
# Dedup jest jedynym miejscem w pipelinie, które podejmuje
# nieoczywistą decyzję bez udziału modelu - i jedynym, które
# potrafi po cichu skasować dobry news. Progi z config.py
# mają tu swoje przypadki brzegowe, żeby zmiana wartości
# od razu pokazała, co przestaje działać.
# =========================================================

import sys

from dedup import canonical_url, title_tokens, same_story


passed = 0
failed = []


def check(name, condition):
    global passed
    if condition:
        passed += 1
    else:
        failed.append(name)


def stories_match(title_a, title_b):
    return same_story(title_tokens(title_a), title_tokens(title_b))


# =========================================================
# ADRESY
# =========================================================

check(
    "parametry UTM nie tworzą nowego adresu",
    canonical_url("https://example.com/news?utm_source=rss&utm_medium=feed")
    == canonical_url("https://example.com/news"),
)

check(
    "ukośnik na końcu nie tworzy nowego adresu",
    canonical_url("https://example.com/news/")
    == canonical_url("https://example.com/news"),
)

check(
    "www nie tworzy nowego adresu",
    canonical_url("https://www.example.com/news")
    == canonical_url("https://example.com/news"),
)

check(
    "kotwica nie tworzy nowego adresu",
    canonical_url("https://example.com/news#section-2")
    == canonical_url("https://example.com/news"),
)

check(
    "znaczący parametr zostaje",
    canonical_url("https://example.com/article?id=42")
    != canonical_url("https://example.com/article"),
)

check(
    "różne artykuły zostają różne",
    canonical_url("https://example.com/a") != canonical_url("https://example.com/b"),
)

check(
    "pusty adres nie wywraca funkcji",
    canonical_url("") == "",
)


# =========================================================
# TO SAMO WYDARZENIE
# =========================================================

check(
    "ten sam news, tytuł dłuższy o szczegóły",
    stories_match(
        "OpenAI acquires Glass Imaging",
        "OpenAI acquires Glass Imaging for $300 million after months of talks",
    ),
)

check(
    "ten sam news, inna kolejność słów",
    stories_match(
        "Nvidia unveils Rubin chip for datacenters",
        "Rubin datacenter chip unveiled by Nvidia",
    ),
)

check(
    "dwa różne newsy o tej samej firmie nie są duplikatem",
    not stories_match(
        "OpenAI acquires Glass Imaging",
        "OpenAI launches new pricing for enterprise customers",
    ),
)

check(
    "samo słowo AI nie robi z newsów duplikatów",
    not stories_match(
        "AI is changing how we work",
        "AI is changing how we travel",
    ),
)

check(
    "krótkie tytuły nie sklejają się przypadkiem",
    not stories_match("Gemini Live audio", "Gemini pricing update"),
)

check(
    "pusty tytuł nie jest niczyim duplikatem",
    not stories_match("", "OpenAI acquires Glass Imaging"),
)


# =========================================================
# WYNIK
# =========================================================

print("Testy dedup: %d zdanych, %d niezdanych." % (passed, len(failed)))

for name in failed:
    print("  NIEZDANY: %s" % name)

sys.exit(1 if failed else 0)
