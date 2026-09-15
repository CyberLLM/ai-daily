# =========================================================
# KONFIGURACJA WSPÓLNA DLA CAŁEGO PIPELINE'U
#
# Jedno miejsce, żeby fetch.py i select.py nie rozjeżdżały
# się w tym, jak stare newsy jeszcze uznajemy za świeże.
# =========================================================

# Ile godzin wstecz sięgamy po newsy
HOURS_BACK = 72

# Maksymalna liczba newsów z jednego źródła trafiająca do selekcji
MAX_PER_SOURCE = 5

# Ile newsów ma wybrać model
DAILY_COUNT = 5

# Przez ile dni pamiętamy opublikowane newsy, żeby ich nie powtarzać
HISTORY_DAYS = 7

# Jeśli po odsianiu powtórek w puli zostanie mniej newsów niż tyle,
# rezygnujemy z odsiewania. Lepiej powtórzyć news niż nie wydać niczego.
MIN_POOL = 8

# Plik z historią opublikowanych newsów
HISTORY_FILE = "data/published.json"
