# =========================================================
# ROZPOZNAWANIE POWTÓRZEŃ
#
# Trzy rodzaje powtórzeń, trzy różne mechanizmy:
#
# 1. Ten sam artykuł pod różnymi adresami (parametry UTM,
#    ukośnik na końcu) - canonical_url.
# 2. Ten sam artykuł co wczoraj - porównanie po canonical_url
#    z historią, w history.py.
# 3. To samo wydarzenie opisane przez różne redakcje -
#    same_story, po znaczących słowach z tytułu.
#
# Trzeci przypadek jest klasyczną wpadką takiego serwisu:
# pięć newsów, z czego trzy o tym samym.
# =========================================================

import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from config import SIMILARITY_MIN_TOKENS, SIMILARITY_THRESHOLD


# =========================================================
# ADRESY
# =========================================================

# Parametry śledzące - nie zmieniają treści, zmieniają adres
TRACKING_PREFIXES = ("utm_", "mc_", "pk_", "at_")

TRACKING_PARAMS = {
    "ref", "fbclid", "gclid", "igshid", "mkt_tok",
    "guccounter", "guce_referrer", "s", "cmpid",
}


def canonical_url(url):
    """
    Sprowadza adres do postaci porównywalnej.

    Bez tego ten sam artykuł z parametrem UTM i bez niego
    to dla historii dwa różne newsy - i wraca nazajutrz.
    """

    if not url:
        return ""

    url = url.strip()

    try:
        parts = urlsplit(url)
    except ValueError:
        return url.lower()

    # Fragment (#cos) nigdy nie wskazuje innego artykułu
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=False)
        if key.lower() not in TRACKING_PARAMS
        and not key.lower().startswith(TRACKING_PREFIXES)
    ]

    host = parts.netloc.lower()

    if host.startswith("www."):
        host = host[4:]

    path = parts.path.rstrip("/") or "/"

    return urlunsplit((
        parts.scheme.lower(),
        host,
        path,
        urlencode(sorted(query)),
        "",
    ))


# =========================================================
# TYTUŁY
# =========================================================

# Słowa, które w tytułach o AI nie niosą informacji.
# "ai" jest tu celowo: występuje w co drugim tytule,
# więc bez tego każde dwa newsy wyglądałyby na podobne.
STOPWORDS = {
    "the", "a", "an", "of", "for", "to", "in", "on", "with", "and",
    "or", "is", "are", "as", "at", "by", "from", "its", "it", "this",
    "that", "new", "ai", "how", "why", "what", "says", "say", "will",
    "can", "you", "your", "we", "our", "be", "has", "have", "was",
    "were", "not", "but", "more", "now", "into", "about", "after",
    "over", "up", "out", "than", "his", "her", "their", "they",
}


def normalize_title(title):
    """Upraszcza tytuł, żeby wyłapać dokładne duplikaty."""
    return re.sub(r"\W+", " ", title.lower(), flags=re.UNICODE).strip()


# Końcówki obcinane przy sprowadzaniu słowa do rdzenia,
# od najdłuższej do najkrótszej. Bez form z apostrofem -
# normalize_title zamienia apostrof na spację, więc "OpenAI's"
# rozpada się na "openai" i jednoliterowe "s" jeszcze wcześniej.
SUFFIXES = ("ing", "ed", "es", "s")

# Poniżej tylu znaków rdzeń przestaje cokolwiek znaczyć
# ("uses" -> "us"), więc wtedy zostawiamy słowo w całości.
MIN_STEM = 4


def stem(word):
    """
    Obcina najczęstsze końcówki fleksyjne.

    Bez tego "Nvidia unveils Rubin chip for datacenters" i
    "Rubin datacenter chip unveiled by Nvidia" to dla nas dwa
    różne newsy, a to jest dokładnie ten sam news z dwóch
    redakcji. Angielskie nagłówki różnią się głównie formą
    czasownika i liczbą rzeczownika.

    To celowo nie jest porządny stemmer: wystarczy, że obie
    strony porównania dostaną tę samą, spójną formę.
    """

    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= MIN_STEM:
            return word[: -len(suffix)]

    return word


def title_tokens(title):
    """
    Znaczące słowa z tytułu, sprowadzone do rdzenia.

    Krótkie słowa lecą razem ze stopwordami - w tytułach
    prasowych nie rozróżniają newsów.
    """

    words = normalize_title(title).split()

    return frozenset(
        stem(word)
        for word in words
        if len(word) > 2 and word not in STOPWORDS
    )


def same_story(tokens_a, tokens_b):
    """
    Czy dwa tytuły opisują to samo wydarzenie.

    Liczymy pokrycie względem krótszego tytułu, nie Jaccarda:
    "OpenAI kupuje Glass Imaging" i "OpenAI kupuje Glass Imaging
    za 300 mln dolarów po miesiącach rozmów" to ten sam news,
    a Jaccard ukarałby je za różnicę długości.
    """

    if not tokens_a or not tokens_b:
        return False

    common = tokens_a & tokens_b

    if len(common) < SIMILARITY_MIN_TOKENS:
        return False

    shorter = min(len(tokens_a), len(tokens_b))

    return len(common) / shorter >= SIMILARITY_THRESHOLD
