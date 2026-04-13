"""
Monitor Albi Online Scuole - Torino e Provincia
Cerca bandi per laboratori teatrali negli albi online delle scuole.
"""

import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import json
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── CONFIGURAZIONE ──────────────────────────────────────────────────────────
EMAIL_MITTENTE  = os.environ.get("EMAIL_MITTENTE", "")   # es. tuoemail@gmail.com
EMAIL_PASSWORD  = os.environ.get("EMAIL_PASSWORD", "")   # App Password Gmail
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO", "")  # dove ricevi le notifiche

PAROLE_CHIAVE = [
    "teatro", "teatrale", "laboratorio", "esperto", "esperto esterno",
    "animazione teatrale", "drammatizzazione", "recitazione"
]

# File locale per ricordare i bandi già notificati
STORICO_FILE = "bandi_notificati.json"
# ────────────────────────────────────────────────────────────────────────────


def carica_storico():
    if os.path.exists(STORICO_FILE):
        with open(STORICO_FILE, "r") as f:
            return set(json.load(f))
    return set()


def salva_storico(storico):
    with open(STORICO_FILE, "w") as f:
        json.dump(list(storico), f)


def scarica_scuole_torino():
    """
    Scarica l'elenco delle scuole di Torino e provincia
    dalla banca dati aperta del MIUR.
    Restituisce lista di dict con 'nome' e 'sito'.
    """
    url = (
        "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/"
        "SCUANAGRAFESTAT20242025.json"
    )
    print("Scarico elenco scuole MIUR...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Errore scaricamento MIUR: {e}")
        return []

    scuole = []
    for item in data:
        prov = item.get("PROVINCIA", "").upper()
        sito = item.get("SITOWEBSCUOLA", "").strip()
        nome = item.get("DENOMINAZIONESCUOLA", "").strip()
        # Filtra Torino (codice TO) e solo chi ha un sito
        if prov == "TO" and sito and sito.startswith("http"):
            scuole.append({"nome": nome, "sito": sito.rstrip("/")})

    print(f"  → {len(scuole)} scuole trovate con sito web")
    return scuole


def costruisci_url_feed(sito):
    """
    Prova i path RSS più comuni degli albi scolastici italiani (Argo, Axios, ecc.)
    """
    candidati = [
        "/feed/",
        "/feed",
        "/?feed=rss2",
        "/albo-online/feed/",
        "/albo-pretorio/feed/",
        "/category/albo-online/feed/",
        "/wp-json/wp/v2/posts?per_page=20&_fields=title,link,date",
    ]
    return [sito + path for path in candidati]


def contiene_parola_chiave(testo):
    testo_lower = testo.lower()
    return any(kw in testo_lower for kw in PAROLE_CHIAVE)


def analizza_feed(url_feed):
    """Scarica e analizza un feed RSS. Restituisce lista di (titolo, link, data)."""
    risultati = []
    try:
        req = urllib.request.Request(url_feed, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            contenuto = resp.read()
        root = ET.fromstring(contenuto)
        # RSS 2.0
        for item in root.findall(".//item"):
            titolo = item.findtext("title", "").strip()
            link   = item.findtext("link", "").strip()
            data   = item.findtext("pubDate", "").strip()
            if titolo and link:
                risultati.append((titolo, link, data))
    except Exception:
        pass
    return risultati


def invia_email(bandi_trovati):
    if not EMAIL_MITTENTE or not EMAIL_PASSWORD or not EMAIL_DESTINATARIO:
        print("⚠️  Credenziali email non configurate — stampo i risultati:")
        for scuola, titolo, link, data in bandi_trovati:
            print(f"  [{scuola}] {titolo}\n  {link}\n  {data}\n")
        return

    corpo_html = "<h2>🎭 Nuovi bandi laboratori teatrali - Scuole Torino</h2>\n<ul>"
    for scuola, titolo, link, data in bandi_trovati:
        corpo_html += (
            f"<li><b>{scuola}</b><br>"
            f"<a href='{link}'>{titolo}</a><br>"
            f"<small>{data}</small></li>\n"
        )
    corpo_html += "</ul>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎭 {len(bandi_trovati)} nuovi bandi teatrali scuole TO - {datetime.today().strftime('%d/%m/%Y')}"
    msg["From"]    = EMAIL_MITTENTE
    msg["To"]      = EMAIL_DESTINATARIO
    msg.attach(MIMEText(corpo_html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_MITTENTE, EMAIL_PASSWORD)
        server.sendmail(EMAIL_MITTENTE, EMAIL_DESTINATARIO, msg.as_string())
    print(f"✅ Email inviata con {len(bandi_trovati)} bandi")


def main():
    print(f"\n{'='*50}")
    print(f"Avvio monitoraggio - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*50}\n")

    storico = carica_storico()
    scuole  = scarica_scuole_torino()

    if not scuole:
        print("Nessuna scuola trovata. Uscita.")
        return

    bandi_nuovi = []

    for i, scuola in enumerate(scuole, 1):
        nome = scuola["nome"]
        sito = scuola["sito"]
        if i % 50 == 0:
            print(f"  Controllo scuola {i}/{len(scuole)}...")

        for url_feed in costruisci_url_feed(sito):
            articoli = analizza_feed(url_feed)
            if articoli:
                for titolo, link, data in articoli:
                    if contiene_parola_chiave(titolo) and link not in storico:
                        bandi_nuovi.append((nome, titolo, link, data))
                        storico.add(link)
                break  # feed trovato, non provare altri path

    salva_storico(storico)

    print(f"\nRisultato: {len(bandi_nuovi)} nuovi bandi trovati")

    if bandi_nuovi:
        invia_email(bandi_nuovi)
    else:
        print("Nessun nuovo bando da segnalare oggi.")


if __name__ == "__main__":
    main()
