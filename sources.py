# =========================================================
# REJESTR ŹRÓDEŁ
#
# Jedyne miejsce, w którym dodaje się lub wyłącza źródło.
# Reszta pipeline'u czyta stąd i nie wie nic o konkretnych
# feedach - dzięki temu zmiana listy nie dotyka logiki.
#
# Każdy feed z tej listy został przed dodaniem sprawdzony pod
# kątem tego, czy faktycznie oddaje świeże wpisy z datami.
# Feedy, które tego nie robiły, są spisane niżej jako odrzucone -
# żeby nie testować ich drugi raz przy kolejnym przeglądzie.
# =========================================================

from dataclasses import dataclass, field
from typing import Tuple


# =========================================================
# RODZAJE ŹRÓDEŁ
#
# Rodzaj nie jest etykietą porządkową - jedzie razem z newsem
# aż do promptu, żeby model wiedział, że blog producenta to
# materiał prasowy firmy, a nie niezależne doniesienie.
# =========================================================

PRESS = "press"                # prasa branżowa, niezależna redakcja
VENDOR = "vendor"              # blog firmy - de facto komunikat prasowy
RESEARCH = "research"          # ośrodki badawcze
ANALYSIS = "analysis"          # praktycy i komentatorzy
COMMUNITY = "community"        # agregatory z filtrem społecznościowym

KIND_LABELS = {
    PRESS: "prasa branżowa",
    VENDOR: "blog firmowy (materiał własny firmy)",
    RESEARCH: "ośrodek badawczy",
    ANALYSIS: "analiza / komentarz praktyka",
    COMMUNITY: "agregator społecznościowy",
}


# =========================================================
# DEFINICJA ŹRÓDŁA
# =========================================================

@dataclass(frozen=True)
class Source:
    """
    Pojedynczy feed.

    cap      - ile newsów z tego źródła może maksymalnie wejść
               do puli. To jest główna dźwignia różnorodności:
               przy jednym wspólnym limicie źródła o dużym
               wolumenie zawsze wypychały te publikujące rzadziej.

    keywords - filtr dla feedów ogólnotechnicznych. Jeśli lista
               jest niepusta, tytuł musi zawierać któreś ze słów.
               Bez tego The Register wrzucałby do serwisu o AI
               newsy o spamie w skrzynkach pocztowych.

    org      - właściciel źródła, jeśli inny niż sama nazwa.
               Limit na źródło nie wystarcza, gdy jedna firma ma
               ich kilka: Google AI, DeepMind i Google Research to
               trzy feedy i jeden nadawca, więc bez tego wydanie
               potrafiło mieć dwie pozycje od tej samej firmy.

    enabled  - wyłącznik bez kasowania wpisu, żeby historia
               decyzji o źródle została w repo.
    """

    name: str
    url: str
    kind: str
    cap: int
    keywords: Tuple[str, ...] = field(default=())
    org: str = ""
    enabled: bool = True
    note: str = ""

    @property
    def owner(self):
        """Nadawca - własna organizacja albo samo źródło."""
        return self.org or self.name


# =========================================================
# SŁOWA KLUCZOWE DLA FEEDÓW OGÓLNYCH
# =========================================================

AI_KEYWORDS = (
    "ai", "artificial intelligence", "machine learning", "llm",
    "chatbot", "openai", "anthropic", "claude", "chatgpt", "gpt",
    "gemini", "deepmind", "copilot", "nvidia", "neural", "model",
    "agent", "algorithm", "automation", "datacenter", "data center",
    "deepfake", "robot",
)


# =========================================================
# LISTA ŹRÓDEŁ
#
# Kolejność ma znaczenie: przy dwóch doniesieniach o tym samym
# wydarzeniu zostaje to ze źródła wyżej na liście. Dlatego
# niezależna prasa idzie przed blogami firm.
# =========================================================

SOURCES = [

    # --- prasa branżowa -----------------------------------
    Source("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/",
           PRESS, cap=3),

    Source("The Verge", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
           PRESS, cap=3),

    Source("Ars Technica", "https://arstechnica.com/ai/feed/",
           PRESS, cap=3),

    Source("Wired", "https://www.wired.com/feed/tag/ai/latest/rss",
           PRESS, cap=2),

    Source("MIT Technology Review",
           "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
           PRESS, cap=2,
           note="Feed tematyczny, nie ogólny - ogólny mieszał AI z klimatem i biotechem."),

    Source("The Register", "https://www.theregister.com/headlines.atom",
           PRESS, cap=2, keywords=AI_KEYWORDS,
           note="Sceptyczna przeciwwaga dla hype'u. Feed sekcji ai_ml nie oddaje dat, "
                "więc bierzemy ogólny i filtrujemy po słowach kluczowych."),

    Source("Rest of World", "https://restofworld.org/feed/latest/",
           PRESS, cap=1, keywords=AI_KEYWORDS,
           note="Perspektywa spoza USA - reszta prasy na liście pisze z Doliny Krzemowej."),

    # --- blogi firm ---------------------------------------
    Source("OpenAI", "https://openai.com/news/rss.xml",
           VENDOR, cap=2, org="OpenAI"),

    Source("Google AI", "https://blog.google/technology/ai/rss/",
           VENDOR, cap=2, org="Google"),

    Source("Google DeepMind", "https://deepmind.google/blog/rss.xml",
           VENDOR, cap=2, org="Google"),

    Source("Hugging Face", "https://huggingface.co/blog/feed.xml",
           VENDOR, cap=2),

    Source("NVIDIA", "https://blogs.nvidia.com/feed/",
           VENDOR, cap=1, keywords=AI_KEYWORDS,
           note="Mocno marketingowy, stąd limit 1 i filtr."),

    # --- badania ------------------------------------------
    Source("MIT News", "https://news.mit.edu/rss/topic/artificial-intelligence2",
           RESEARCH, cap=2),

    Source("Google Research", "https://research.google/blog/rss/",
           RESEARCH, cap=1, org="Google",
           note="Formalnie badania, ale nadawca ten sam co Google AI i DeepMind - "
                "stąd wspólny limit na organizację."),

    # --- analiza ------------------------------------------
    Source("Simon Willison", "https://simonwillison.net/atom/everything/",
           ANALYSIS, cap=2,
           note="Praktyk - wyłapuje zmiany w narzędziach, zanim opisze je prasa."),

    Source("AI Snake Oil", "https://www.aisnakeoil.com/feed",
           ANALYSIS, cap=1,
           note="Narayanan i Kapoor - systematyczne studzenie przesadzonych doniesień."),

    # --- agregator ----------------------------------------
    Source("Hacker News",
           "https://hnrss.org/newest?q=AI+OR+LLM+OR+OpenAI+OR+Anthropic&points=100",
           COMMUNITY, cap=4,
           note="Próg 100 punktów robi selekcję za nas - stąd najwyższy limit na liście."),
]


# =========================================================
# ŹRÓDŁA ODRZUCONE PO TESTACH
#
# Zostawione świadomie: przy następnym przeglądzie listy widać,
# co już sprawdzono i dlaczego odpadło. Feed potrafi ożyć, więc
# warto je okresowo przetestować ponownie.
# =========================================================

REJECTED = {
    "VentureBeat AI": "feed zwraca zero wpisów",
    "Anthropic": "brak działającego RSS pod /rss.xml",
    "Meta AI": "feed zwraca zero wpisów",
    "Microsoft AI": "feed zwraca zero wpisów",
    "Mistral": "brak działającego RSS",
    "The Batch (deeplearning.ai)": "feed zwraca zero wpisów",
    "Euractiv": "feed zwraca zero wpisów",
    "Stanford HAI": "feed zwraca zero wpisów",
    "IEEE Spectrum AI": "feed zwraca zero wpisów",
    "Lawfare": "feed zwraca zero wpisów",
    "Tech Policy Press": "feed zwraca zero wpisów",
    "Brookings AI": "feed zwraca zero wpisów",
    "BAIR Berkeley": "feed zwraca zero wpisów",
    "Nature Machine Intelligence": "feed zwraca zero wpisów",
    "AWS Machine Learning": "działa, ale to poradniki produktowe, nie newsy",
    "arXiv cs.AI": "300 pozycji na dobę, same preprinty - zalałoby pulę",
}


def active_sources():
    """Źródła włączone do pobierania, w kolejności z rejestru."""
    return [source for source in SOURCES if source.enabled]


def owner_of(name):
    """Nadawca danego źródła - do limitu na organizację."""
    for source in SOURCES:
        if source.name == name:
            return source.owner
    return name


def shared_owners():
    """
    Nadawcy mający na liście więcej niż jedno źródło.

    Limit na organizację ma sens tylko dla nich. Nałożony na
    wszystkich nadpisywałby limity pojedynczych źródeł - przy
    limicie organizacji 3 Hacker News z własnym limitem 4
    dostawałby po cichu 3.
    """

    counts = {}

    for source in SOURCES:
        counts[source.owner] = counts.get(source.owner, 0) + 1

    return {owner for owner, count in counts.items() if count > 1}


def priority_of(name):
    """
    Pozycja źródła w rejestrze.

    Używane przy odsiewaniu duplikatów: niższa liczba wygrywa,
    więc doniesienie prasowe bije komunikat firmy o tym samym.
    """
    for index, source in enumerate(SOURCES):
        if source.name == name:
            return index
    return len(SOURCES)
