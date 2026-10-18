import html
import json
import os
from datetime import datetime


def esc(value):
    """
    Escapuje tekst pochodzacy od modelu.

    Tytul z & albo < rozjechalby strone, a tresc nie jest
    pisana recznie - przychodzi z LLM-a, wiec nie ufamy jej.
    """
    return html.escape(str(value), quote=True)


# =========================================================
# FORMULARZ ZAPISU NA NEWSLETTER
#
# Formularz Brevo, ale bez ich arkusza stylów: ich jasny,
# niebieski wygląd gryzł się z serwisem. Zostają identyfikatory
# i klasy, po których main.js Brevo wysyła zapis w tle
# i pokazuje komunikat sukcesu albo błędu.
#
# Zgoda, double opt-in i wypisywanie się są po stronie Brevo
# (lista "AI DAILY - subskrybenci", ID 6).
# =========================================================

NEWSLETTER_FORM = """
<section class="newsletter sib-form">
<div id="sib-form-container" class="sib-form-container">

    <div class="nl-label">NEWSLETTER</div>
    <h2>Dostawaj AI DAILY 5 mailem</h2>
    <p>Pięć najważniejszych informacji o AI, codziennie rano w Twojej skrzynce.</p>

    <div id="error-message" class="sib-form-message-panel nl-message nl-error">
        <span class="sib-form-message-panel__inner-text">
            Nie udało się zapisać. Spróbuj ponownie za chwilę.
        </span>
    </div>

    <div id="success-message" class="sib-form-message-panel nl-message nl-success">
        <span class="sib-form-message-panel__inner-text">
            Prawie gotowe! Sprawdź skrzynkę i kliknij link potwierdzający,
            żeby zacząć otrzymywać AI DAILY 5. Jeśli maila nie ma, zajrzyj do spamu.
        </span>
    </div>

    <div id="sib-container">
    <form id="sib-form" method="POST" action="https://c3f47f46.sibforms.com/serve/MUIFAP0qRWgzhw01YnMUz4NqppLUAwey6vUceILLloxAR_DyLLzvVLmHX4XKvSR906ulJuwFHr100SREECszCZybEgvFoGN0tcZi6cutWB2dxHDSQbUKgSpFn210OtuQgbnMKGNKx79Uhmy5epsJLOEzX1Ht3KeHIpDYKOJvNPt4UQ7aOgDHWbjwi4mxXaylku799J8Yldx-TsS9eg==" data-type="subscription">

        <div class="sib-input sib-form-block">
            <div class="form__entry entry_block">
                <div class="nl-row">
                    <input class="input" type="email" id="EMAIL" name="EMAIL"
                        autocomplete="email" value="" placeholder="Twój adres e-mail"
                        aria-label="Twój adres e-mail" data-required="true" required>

                    <button class="sib-form-block__button sib-form-block__button-with-loader"
                        form="sib-form" type="submit">
                        <svg class="icon clickable__icon progress-indicator__icon sib-hide-loader-icon" viewBox="0 0 512 512">
                            <path d="M460.116 373.846l-20.823-12.022c-5.541-3.199-7.54-10.159-4.663-15.874 30.137-59.886 28.343-131.652-5.386-189.946-33.641-58.394-94.896-95.833-161.827-99.676C261.028 55.961 256 50.751 256 44.352V20.309c0-6.904 5.808-12.337 12.703-11.982 83.556 4.306 160.163 50.864 202.11 123.677 42.063 72.696 44.079 162.316 6.031 236.832-3.14 6.148-10.75 8.461-16.728 5.01z"/>
                        </svg>
                        Zapisz się
                    </button>
                </div>
                <label class="entry__error entry__error--primary"></label>
            </div>
        </div>

        <div class="sib-optin sib-form-block" data-required="true">
            <div class="form__entry entry_mcq">
                <label class="nl-consent">
                    <input type="checkbox" value="1" id="OPT_IN" name="OPT_IN" required>
                    <span>Zgadzam się na otrzymywanie newslettera AI DAILY 5 na podany adres e-mail.
                    Wypiszesz się w każdej chwili linkiem w stopce maila.</span>
                </label>
                <label class="entry__error entry__error--primary"></label>
            </div>
        </div>

        <p class="nl-rodo">
            Administratorem danych jest HEURISTICA - STANISZEWSKI MAREK, ul. Bukowińska 26C m. 11,
            02-703 Warszawa. Adres e-mail przetwarzam wyłącznie w celu wysyłki newslettera, na podstawie
            Twojej zgody (art. 6 ust. 1 lit. a RODO), do czasu jej wycofania. Wysyłkę obsługuje
            Sendinblue SAS (Brevo), Francja, która może też wykorzystywać część danych do ochrony
            platformy przed nadużyciami
            (<a href="https://www.brevo.com/en/legal/privacypolicy/" target="_blank" rel="nofollow noopener">polityka prywatności Brevo</a>).
            Przysługuje Ci prawo dostępu do danych, ich sprostowania i usunięcia oraz skargi
            do Prezesa UODO. Kontakt: staniszewski@heuristica.pl
        </p>

        <input type="text" name="email_address_check" value="" class="input--hidden" tabindex="-1" autocomplete="off">
        <input type="hidden" name="locale" value="en">
    </form>
    </div>

</div>
</section>

<script>
  window.REQUIRED_CODE_ERROR_MESSAGE = 'Please choose a country code';
  window.LOCALE = 'en';
  window.EMAIL_INVALID_MESSAGE = window.SMS_INVALID_MESSAGE = "Nieprawidłowe dane. Sprawdź adres e-mail i spróbuj ponownie.";
  window.REQUIRED_ERROR_MESSAGE = "To pole jest wymagane.";
  window.GENERIC_INVALID_MESSAGE = "Nieprawidłowe dane. Sprawdź adres e-mail i spróbuj ponownie.";
  window.INVALID_NUMBER = "Nieprawidłowe dane. Sprawdź adres e-mail i spróbuj ponownie.";
  window.INVALID_DATE = "Please enter a valid date";
  window.REQUIRED_MULTISELECT_MESSAGE = 'Please select at least 1 option';
  window.translation = {
    common: {
      selectedList: '{quantity} list selected',
      selectedLists: '{quantity} lists selected',
      selectedOption: '{quantity} selected',
      selectedOptions: '{quantity} selected',
    }
  };
  var AUTOHIDE = Boolean(1);
</script>
<script defer src="https://sibforms.com/forms/end-form/build/main.js"></script>
"""


with open("data/daily.json", "r", encoding="utf-8") as f:
    news = json.load(f)

today_display = datetime.now().strftime("%d.%m.%Y")
today_file = datetime.now().strftime("%Y-%m-%d")

cards = ""

for i, item in enumerate(news, start=1):

    # Kategoria bywa pusta, bo select.py czysci nazwy spoza
    # slownika. Wtedy karta po prostu nie ma etykiety - lepiej
    # bez niej niz z nazwa, ktorej nikt wiecej nie uzyje.
    category = item.get("category", "").strip()

    badge = (
        f'<span class="category">{esc(category)}</span>'
        if category
        else ""
    )

    cards += f"""
    <article>
        <div class="meta">
            <span class="number">{i:02}</span>
            {badge}
        </div>

        <h2>{esc(item["title"])}</h2>

        <p>{esc(item["summary"])}</p>

        <div class="so-what">
            <strong>SO WHAT?</strong>
            <div>{esc(item["so_what"])}</div>
        </div>

        <a class="source" href="{esc(item["url"])}" target="_blank">
            {esc(item["source"])} →
        </a>
    </article>
    """

html = f"""
<!DOCTYPE html>
<html lang="pl">

<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QDHLBXLXT4"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-QDHLBXLXT4');
</script>
<title>AI DAILY 5 · Heuristica</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap" rel="stylesheet">

<style>

:root {{
    --bg-primary: #0f1419;
    --bg-secondary: #1a1f2e;
    --text-primary: #e8e6e1;
    --text-muted: #a09a94;
    --border-color: #2d3d4a;
    --accent-gold: #d4a574;
    --accent-green: #2d5a4e;
}}

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
    line-height: 1.65;
}}

.container {{
    max-width: 900px;
    margin: 36px auto;
    padding: 48px 52px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
}}

.brand {{
    font-family: 'Poppins', sans-serif;
    font-size: 14px;
    letter-spacing: 2px;
    color: var(--accent-gold);
    margin-bottom: 8px;
}}

h1 {{
    font-family: 'Poppins', sans-serif;
    font-size: 2.4em;
    margin: 0 0 8px 0;
    letter-spacing: -0.3px;
}}

.subtitle {{
    font-size: 1.08em;
    color: var(--text-muted);
    margin: 0 0 8px 0;
}}

.date {{
    color: var(--text-muted);
    font-size: 0.92em;
    margin-bottom: 44px;
}}

article {{
    border-top: 1px solid var(--border-color);
    padding: 34px 0 38px 0;
}}

.meta {{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}}

.number {{
    font-family: 'Poppins', sans-serif;
    color: var(--accent-gold);
    font-size: 0.82em;
    letter-spacing: 1.5px;
}}

.category {{
    font-family: 'Poppins', sans-serif;
    font-size: 0.68em;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--text-muted);
    border: 1px solid var(--border-color);
    border-radius: 999px;
    padding: 3px 10px;
}}

h2 {{
    font-family: 'Poppins', sans-serif;
    font-size: 1.42em;
    line-height: 1.35;
    margin: 10px 0 14px 0;
}}

article p {{
    color: var(--text-muted);
    margin: 0 0 18px 0;
}}

.so-what {{
    margin: 20px 0;
    padding: 16px 18px;
    border-left: 3px solid var(--accent-gold);
    background: rgba(212, 165, 116, 0.08);
}}

.so-what strong {{
    display: block;
    color: var(--accent-gold);
    margin-bottom: 6px;
    font-size: 0.85em;
    letter-spacing: 0.5px;
}}

.source {{
    color: var(--accent-gold);
    text-decoration: none;
    font-size: 0.92em;
}}

.source:hover {{
    text-decoration: underline;
}}

.newsletter {{
    border-top: 1px solid var(--border-color);
    padding: 34px 0 38px 0;
}}

.nl-label {{
    font-family: 'Poppins', sans-serif;
    color: var(--accent-gold);
    font-size: 0.82em;
    letter-spacing: 1.5px;
}}

.newsletter > div > p {{
    color: var(--text-muted);
    margin: 0 0 20px 0;
}}

.nl-row {{
    display: flex;
    gap: 10px;
}}

.nl-row input {{
    flex: 1;
    min-width: 0;
    padding: 12px 14px;
    font-size: 1em;
    color: var(--text-primary);
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 3px;
}}

.nl-row input:focus {{
    outline: none;
    border-color: var(--accent-gold);
}}

.nl-row button {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 12px 22px;
    font-family: 'Poppins', sans-serif;
    font-size: 0.95em;
    color: var(--bg-primary);
    background: var(--accent-gold);
    border: none;
    border-radius: 3px;
    cursor: pointer;
}}

.nl-row button:hover {{
    filter: brightness(1.08);
}}

.progress-indicator__icon {{
    width: 16px;
    height: 16px;
    fill: currentColor;
    animation: nl-spin 1s linear infinite;
}}

.sib-hide-loader-icon {{
    display: none;
}}

@keyframes nl-spin {{
    to {{ transform: rotate(360deg); }}
}}

.nl-consent {{
    display: flex;
    gap: 10px;
    align-items: flex-start;
    margin-top: 16px;
    font-size: 0.9em;
    color: var(--text-muted);
    cursor: pointer;
}}

.nl-consent input {{
    margin-top: 4px;
    accent-color: var(--accent-gold);
}}

.entry__error {{
    display: block;
    color: #e8a0a0;
    font-size: 0.85em;
}}

.entry__error:empty {{
    display: none;
}}

.entry__error:not(:empty) {{
    margin-top: 6px;
}}

.nl-rodo {{
    margin: 16px 0 0 0;
    font-size: 0.75em;
    line-height: 1.55;
    color: var(--text-muted);
    opacity: 0.8;
}}

.nl-rodo a {{
    color: var(--text-muted);
}}

.input--hidden {{
    display: none;
}}

.nl-message {{
    display: none;
    margin-bottom: 16px;
    padding: 14px 16px;
    border-radius: 3px;
    font-size: 0.95em;
}}

/* Tę klasę dokleja main.js Brevo po wysłaniu formularza. */
.sib-form-message-panel--active {{
    display: block;
}}

.nl-success {{
    color: #bfe6d3;
    background: var(--accent-green);
}}

.nl-error {{
    color: #f2c9c9;
    background: #5a2d2d;
}}

footer {{
    border-top: 1px solid var(--border-color);
    margin-top: 10px;
    padding-top: 28px;
    color: var(--text-muted);
    font-size: 0.85em;
}}

@media (max-width: 750px) {{

    .container {{
        margin: 0;
        padding: 32px 22px;
        border-left: none;
        border-right: none;
    }}

    h1 {{
        font-size: 2em;
    }}

    h2 {{
        font-size: 1.25em;
    }}

    .nl-row {{
        flex-direction: column;
    }}

    .nl-row button {{
        justify-content: center;
    }}
}}

</style>
</head>

<body>

<div class="container">

<header>
    <div class="brand">HEURISTICA</div>
    <h1>AI DAILY 5</h1>
    <p class="subtitle">5 rzeczy, które warto dziś wiedzieć o AI.</p>
    <div class="date">{today_display}</div>
</header>

{cards}

{NEWSLETTER_FORM}

<footer>
    AI DAILY 5 · Heuristica ·
    <a href="/archive/index.html">Archiwum</a>
</footer>

</div>

</body>
</html>
"""

with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html)

os.makedirs("docs/archive", exist_ok=True)

archive_path = f"docs/archive/{today_file}.html"

with open(archive_path, "w", encoding="utf-8") as f:
    f.write(html)

print("Wygenerowano:")
print("- docs/index.html")
print(f"- {archive_path}")

# =========================================================
# INDEKS ARCHIWUM
# =========================================================

archive_dir = "docs/archive"

archive_files = sorted(
    [
        filename
        for filename in os.listdir(archive_dir)
        if filename.endswith(".html") and filename != "index.html"
    ],
    reverse=True
)

archive_links = ""

for filename in archive_files:
    date_label = filename.replace(".html", "")

    archive_links += f"""
    <li>
        <a href="{filename}">{date_label}</a>
    </li>
    """

archive_html = f"""
<!DOCTYPE html>
<html lang="pl">

<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QDHLBXLXT4"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-QDHLBXLXT4');
</script>
<title>Archiwum · AI DAILY 5</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap" rel="stylesheet">

<style>

:root {{
    --bg-primary: #0f1419;
    --bg-secondary: #1a1f2e;
    --text-primary: #e8e6e1;
    --text-muted: #a09a94;
    --border-color: #2d3d4a;
    --accent-gold: #d4a574;
}}

body {{
    margin: 0;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}

.container {{
    max-width: 900px;
    margin: 36px auto;
    padding: 48px 52px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
}}

.brand {{
    font-family: 'Poppins', sans-serif;
    font-size: 14px;
    letter-spacing: 2px;
    color: var(--accent-gold);
}}

h1 {{
    font-family: 'Poppins', sans-serif;
}}

ul {{
    list-style: none;
    padding: 0;
}}

li {{
    border-top: 1px solid var(--border-color);
    padding: 18px 0;
}}

a {{
    color: var(--accent-gold);
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

.back {{
    margin-top: 40px;
}}

</style>
</head>

<body>

<div class="container">

<div class="brand">HEURISTICA</div>

<h1>Archiwum AI DAILY 5</h1>

<ul>
{archive_links}
</ul>

<div class="back">
    <a href="../index.html">← Najnowsze wydanie</a>
</div>

</div>

</body>
</html>
"""

with open("docs/archive/index.html", "w", encoding="utf-8") as f:
    f.write(archive_html)

print("- docs/archive/index.html")
