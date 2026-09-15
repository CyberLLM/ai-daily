import json
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

with open("data/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

prompt = f"""
Jesteś redaktorem serwisu:
"5 rzeczy, które warto dziś wiedzieć o AI".

Masz listę newsów z ostatnich 48 godzin.

Wybierz dokładnie 5 najważniejszych newsów.

Kryteria:
- znaczenie dla rozwoju AI
- wpływ biznesowy
- nowość
- wiarygodność
- różnorodność tematów
- różnorodność źródeł

Zasady:
- maksymalnie 2 newsy z jednego źródła
- unikaj kilku newsów dotyczących dokładnie tego samego wydarzenia
- preferuj różne obszary: modele, agenci, biznes, badania, regulacje, robotyka, narzędzia
- odrzuć clickbait, autopromocję i drobne aktualizacje
- nie wymyślaj informacji, których nie ma w danych wejściowych
- zachowaj oryginalny URL i nazwę źródła

Dla każdego wybranego newsa zwróć:

- title: krótki tytuł po polsku
- summary: 2 krótkie zdania po polsku
- so_what: jedno konkretne zdanie odpowiadające na pytanie "co z tego wynika?"
- category: jedna kategoria, np. Models, Agents, Business, Research, Regulation, Robotics, Tools
- source
- url

Zwróć WYŁĄCZNIE poprawny JSON.
Bez markdownu.
Bez komentarzy.
Bez ```json.

Format:

[
  {{
    "title": "...",
    "summary": "...",
    "so_what": "...",
    "category": "...",
    "source": "...",
    "url": "..."
  }}
]

NEWSY:

{json.dumps(news, ensure_ascii=False, indent=2)}
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
    daily = json.loads(text)
except json.JSONDecodeError:
    print("Błąd: model nie zwrócił poprawnego JSON-a.")
    print("\nOdpowiedź modelu:\n")
    print(text)
    raise

if not isinstance(daily, list):
    raise ValueError("Odpowiedź modelu nie jest listą.")

if len(daily) != 5:
    raise ValueError(
        f"Model zwrócił {len(daily)} newsów zamiast dokładnie 5."
    )

with open("data/daily.json", "w", encoding="utf-8") as f:
    json.dump(
        daily,
        f,
        ensure_ascii=False,
        indent=2
    )

print("Wybrano TOP 5.")

for i, item in enumerate(daily, start=1):
    print(
        f'{i}. [{item.get("source", "?")}] '
        f'{item.get("title", "")}'
    )
