# =========================================================
# KONFIGURACJA WSPÓLNA DLA CAŁEGO PIPELINE'U
#
# Jedno miejsce, żeby fetch.py i select.py nie rozjeżdżały
# się w tym, jak stare newsy jeszcze uznajemy za świeże.
#
# Sama lista źródeł mieszka w sources.py.
# =========================================================

# Ile godzin wstecz sięgamy po newsy.
#
# Było 72, ale to była proteza na zbyt chudą pulę: przy sześciu
# źródłach krótsze okno nie zbierało materiału na wydanie.
# Przy obecnym rejestrze 48 godzin w zupełności wystarcza,
# a serwis przestaje podawać trzydniowe newsy jako "dziś".
HOURS_BACK = 48

# Ile newsów ma wybrać model
DAILY_COUNT = 5

# Ile newsów z jednego źródła może wejść do finałowej piątki.
# Limit na pulę jest osobny i siedzi przy każdym źródle
# w sources.py - ten dotyczy już tego, co widzi czytelnik.
MAX_PER_SOURCE_IN_EDITION = 2

# Ile newsów z blogów firmowych może wejść do finałowej piątki.
# Bez tego wydanie potrafiło zjechać w stronę komunikatów
# prasowych dwóch największych firm.
MAX_VENDOR_IN_EDITION = 2

# Ile newsów od jednej organizacji może wejść do finałowej piątki.
# Limit na źródło tego nie łapie: Google ma trzy osobne feedy
# (Google AI, DeepMind, Google Research), więc mieścił się w limicie
# per źródło, a i tak brał dwie z pięciu pozycji wydania.
MAX_ORG_IN_EDITION = 2

# To samo na poziomie puli - żeby model w ogóle nie dostał
# dziesięciu materiałów od jednego nadawcy do wyboru.
MAX_ORG_IN_POOL = 3


# =========================================================
# LIMITY NA RODZAJ ŹRÓDŁA
#
# Limit per źródło nie wystarcza: pięć blogów firmowych z
# limitem 2 to wciąż dziesięć komunikatów prasowych w puli.
# Ten limit trzyma proporcje całych kategorii.
# =========================================================

KIND_CAPS = {
    "vendor": 6,
    "community": 4,
    "research": 3,
    "analysis": 3,
    # prasa bez limitu - to ma być trzon serwisu
}


# =========================================================
# POBIERANIE
# =========================================================

# Ile feedów pobieramy równolegle. Przy siedemnastu źródłach
# pobieranie po kolei potrafiłoby trwać minuty, gdyby kilka
# serwerów odpowiadało wolno.
FETCH_WORKERS = 8

# Twardy limit na pojedynczy feed. Zawieszony serwer nie może
# zablokować całego porannego wydania.
FETCH_TIMEOUT = 20

# Ile razy ponawiamy nieudane pobranie. Cron leci raz na dobę,
# więc chwilowy limit zapytań wyrzuciłby źródło z wydania na cały
# dzień - a przy siedemnastu feedach naraz zdarza się to realnie.
FETCH_RETRIES = 1

# Pauza przed ponowną próbą, w sekundach.
FETCH_RETRY_PAUSE = 3


# =========================================================
# ODSIEWANIE DUPLIKATÓW
#
# Ten sam news opisują tego samego dnia trzy redakcje.
# Porównujemy znaczące słowa z tytułów: jeśli pokrywają się
# na tyle mocno, zostaje wersja ze źródła wyżej w rejestrze.
# =========================================================

# Ile wspólnych słów musi wystąpić, żeby w ogóle rozważać duplikat.
SIMILARITY_MIN_TOKENS = 3

# Jaka część krótszego tytułu musi się pokrywać (0-1).
# Świadomie ostrożnie: lepiej przepuścić duplikat, który
# model i tak odrzuci, niż skasować osobny news.
SIMILARITY_THRESHOLD = 0.65


# =========================================================
# HISTORIA
# =========================================================

# Przez ile dni pamiętamy opublikowane newsy, żeby ich nie powtarzać
HISTORY_DAYS = 7

# Plik z historią opublikowanych newsów
HISTORY_FILE = "data/published.json"

# Jeśli po odsianiu powtórek w puli zostanie mniej newsów niż tyle,
# rezygnujemy z odsiewania. Lepiej powtórzyć news niż nie wydać niczego.
MIN_POOL = 8


# =========================================================
# KONTROLA JAKOŚCI PULI
#
# Progi ostrzegawcze. Nie przerywają wydania, ale zostawiają
# w logu wyraźny ślad, że lista źródeł wymaga przeglądu -
# feed potrafi umrzeć po cichu i pula chudnie niezauważenie.
# =========================================================

# Poniżej tylu newsów w puli selekcja robi się pozorna.
POOL_WARNING_THRESHOLD = 15

# Powyżej takiego udziału jednego źródła w puli (0-1) serwis
# zaczyna być skrótem tego jednego źródła.
SOURCE_SHARE_WARNING = 0.30
