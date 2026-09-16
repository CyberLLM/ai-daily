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
