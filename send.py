import html
import json
import os
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime


# =========================================================
# WYSYŁKA NEWSLETTERA PRZEZ BREVO
#
# Uruchamiane z run_daily.sh dopiero po udanej publikacji,
# więc mail zawsze odpowiada temu, co jest na stronie.
#
#   python3 send.py                 - kampania do całej listy
#   python3 send.py --test ADRES    - jeden mail testowy na ADRES
# =========================================================

API = "https://api.brevo.com/v3"

LIST_ID = 6

SENDER = {"name": "AI DAILY", "email": "newsletter@news.heuristica.pl"}
REPLY_TO = "staniszewski@heuristica.pl"

SITE_URL = "https://daily.heuristica.pl"

# Darmowy plan Brevo to 300 maili dziennie na całe konto,
# wspólne ze sklepem storytelling.com.pl. Newsletter nie może
# zjeść kredytów, na które czekają maile transakcyjne sklepu.
CREDITS_RESERVE = 50

# Plik z datą ostatniej wysyłki. Drugie uruchomienie tego samego
# dnia (np. ręczne po awarii) nie wyśle drugiego maila.
LAST_SENT_FILE = "newsletter_last_sent.txt"


# Brevo wpuszcza API tylko z autoryzowanych adresów IP, a na
# liście jest IPv6 tego VPS-a. IPv4 mikrusa jest współdzielone
# z innymi serwerami, więc go tam nie dodajemy - stąd wymuszenie
# IPv6 dla wszystkich połączeń z tego skryptu.
_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_ipv6(*args, **kwargs):
    results = _getaddrinfo(*args, **kwargs)
    ipv6 = [r for r in results if r[0] == socket.AF_INET6]
    return ipv6 or results


socket.getaddrinfo = _getaddrinfo_ipv6


def brevo(method, path, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None

    request = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "api-key": os.environ["BREVO_API_KEY"],
            "accept": "application/json",
            "content-type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Brevo {method} {path}: HTTP {e.code} {detail}")

    return json.loads(body) if body else {}


def esc(value):
    """Treść przychodzi z LLM-a, więc jej nie ufamy - jak w generate.py."""
    return html.escape(str(value), quote=True)


# =========================================================
# TREŚĆ MAILA
#
# Osobny szablon, nie kopia strony: programy pocztowe nie
# czytają <style> ani flexboksa, więc wszystko siedzi w tabelach
# i atrybutach style. Tło jasne, bo ciemne maile część skrzynek
# odwraca na własną rękę i wychodzi z tego nieczytelny tekst.
# =========================================================

GOLD = "#b8864f"
TEXT = "#1a1f2e"
MUTED = "#5f5a55"
BORDER = "#e4ddd3"


def build_html(news, today_display, archive_url, unsubscribe):
    cards = ""

    for i, item in enumerate(news, start=1):
        category = item.get("category", "").strip()

        badge = (
            f' &nbsp;·&nbsp; <span style="color:{MUTED};">{esc(category).upper()}</span>'
            if category
            else ""
        )

        cards += f"""
        <tr><td style="border-top:1px solid {BORDER}; padding:26px 0 28px 0;">
            <div style="font-size:12px; letter-spacing:1.5px; color:{GOLD}; font-weight:bold;">
                {i:02}{badge}
            </div>
            <h2 style="margin:8px 0 12px 0; font-size:20px; line-height:1.35; color:{TEXT};">
                {esc(item["title"])}
            </h2>
            <p style="margin:0 0 16px 0; font-size:15px; line-height:1.6; color:{MUTED};">
                {esc(item["summary"])}
            </p>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr><td style="border-left:3px solid {GOLD}; background:#f8f1e8; padding:12px 14px;">
                    <div style="font-size:12px; letter-spacing:0.5px; color:{GOLD}; font-weight:bold; margin-bottom:4px;">SO WHAT?</div>
                    <div style="font-size:15px; line-height:1.55; color:{TEXT};">{esc(item["so_what"])}</div>
                </td></tr>
            </table>
            <p style="margin:14px 0 0 0; font-size:14px;">
                <a href="{esc(item["url"])}" style="color:{GOLD}; text-decoration:none;">{esc(item["source"])} →</a>
            </p>
        </td></tr>
        """

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI DAILY 5 · {today_display}</title>
</head>
<body style="margin:0; padding:0; background:#f4f1ec;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f1ec;">
<tr><td align="center" style="padding:24px 12px;">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
    style="max-width:600px; background:#ffffff; border:1px solid {BORDER}; font-family:-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;">
<tr><td style="padding:32px 32px 8px 32px;">

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="padding-bottom:24px;">
        <div style="font-size:12px; letter-spacing:2px; color:{GOLD}; font-weight:bold;">HEURISTICA</div>
        <h1 style="margin:6px 0 4px 0; font-size:30px; color:{TEXT};">AI DAILY 5</h1>
        <div style="font-size:15px; color:{MUTED};">5 rzeczy, które warto dziś wiedzieć o AI · {today_display}</div>
        <div style="font-size:13px; margin-top:8px;">
            <a href="{archive_url}" style="color:{MUTED};">Czytaj w przeglądarce</a>
        </div>
    </td></tr>

    {cards}

    <tr><td style="border-top:1px solid {BORDER}; padding:22px 0 26px 0; font-size:12px; line-height:1.6; color:{MUTED};">
        Dostajesz ten mail, bo zapisałeś(-aś) się na AI DAILY 5 na
        <a href="{SITE_URL}" style="color:{MUTED};">daily.heuristica.pl</a>.
        Odpowiedz na tę wiadomość, jeśli chcesz coś napisać.<br>
        <a href="{unsubscribe}" style="color:{MUTED};">Wypisz się</a> ·
        <a href="{SITE_URL}/archive/index.html" style="color:{MUTED};">Archiwum</a><br>
        HEURISTICA - STANISZEWSKI MAREK, ul. Bukowińska 26C m. 11, 02-703 Warszawa
    </td></tr>
    </table>

</td></tr>
</table>

</td></tr>
</table>
</body>
</html>
"""


# =========================================================
# WYSYŁKA
# =========================================================

with open("data/daily.json", "r", encoding="utf-8") as f:
    news = json.load(f)

now = datetime.now()
today_display = now.strftime("%d.%m.%Y")
today_file = now.strftime("%Y-%m-%d")
archive_url = f"{SITE_URL}/archive/{today_file}.html"

subject = f"AI DAILY 5 · {now.strftime('%d.%m')}: {news[0]['title']}"
preview = " · ".join(item["title"] for item in news[1:3])

test_to = None
if len(sys.argv) == 3 and sys.argv[1] == "--test":
    test_to = sys.argv[2]
elif len(sys.argv) != 1:
    raise SystemExit("Użycie: python3 send.py [--test ADRES]")

if test_to:
    # Mail transakcyjny do jednej osoby - bez kampanii, bez listy.
    # Link wypisu działa tylko w kampanii, więc w teście jest atrapą.
    brevo("POST", "/smtp/email", {
        "sender": SENDER,
        "replyTo": {"email": REPLY_TO},
        "to": [{"email": test_to}],
        "subject": "[TEST] " + subject,
        "htmlContent": build_html(news, today_display, archive_url, "#"),
        "tags": ["ai-daily-test"],
    })
    print(f"Wysłano mail testowy na {test_to}.")
    sys.exit(0)

if os.path.exists(LAST_SENT_FILE):
    with open(LAST_SENT_FILE, "r", encoding="utf-8") as f:
        if f.read().strip() == today_file:
            print(f"Newsletter z {today_file} już wyszedł - pomijam.")
            sys.exit(0)

recipients = brevo("GET", f"/contacts/lists/{LIST_ID}").get("uniqueSubscribers", 0)

if recipients == 0:
    print("Lista subskrybentów jest pusta - nic nie wysyłam.")
    sys.exit(0)

account = brevo("GET", "/account")
credits = sum(
    plan.get("credits", 0)
    for plan in account.get("plan", [])
    if plan.get("creditsType") == "sendLimit"
)

if credits - recipients < CREDITS_RESERVE:
    raise SystemExit(
        f"Za mało kredytów Brevo: zostało {credits}, potrzeba {recipients} "
        f"+ {CREDITS_RESERVE} rezerwy dla sklepu. Newsletter NIE wyszedł."
    )

campaign = brevo("POST", "/emailCampaigns", {
    "name": f"AI DAILY 5 - {today_file}",
    "subject": subject,
    "previewText": preview,
    "sender": SENDER,
    "replyTo": REPLY_TO,
    "htmlContent": build_html(news, today_display, archive_url, "{{ unsubscribe }}"),
    "recipients": {"listIds": [LIST_ID]},
    "tag": "ai-daily",
})

brevo("POST", f"/emailCampaigns/{campaign['id']}/sendNow")

with open(LAST_SENT_FILE, "w", encoding="utf-8") as f:
    f.write(today_file)

print(f"Newsletter wysłany do {recipients} subskrybentów (kampania {campaign['id']}).")
