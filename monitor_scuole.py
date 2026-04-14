import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def invia_mail(testo_mail):
    mittente = os.getenv("EMAIL_MITTENTE")
    password = os.getenv("EMAIL_PASSWORD")
    destinatario = os.getenv("EMAIL_DESTINATARIO")
    if not mittente or not password:
        print("Errore: Secrets non configurati correttamente.")
        return

    msg = MIMEMultipart()
    msg['From'] = mittente
    msg['To'] = destinatario
    msg['Subject'] = f"🎭 BANDI ESTATE/PNRR TORINO: Aggiornamento {datetime.now().strftime('%d/%m')}"
    msg.attach(MIMEText(testo_mail, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(mittente, password)
        server.send_message(msg)
        server.quit()
        print("📧 Mail inviata con successo!")
    except Exception as e:
        print(f"❌ Errore invio mail: {e}")

def monitora_ust_torino():
    """Controlla direttamente il sito del Provveditorato di Torino"""
    print("Inizio scansione UST Torino...")
    url = "http://www.istruzionepiemonte.it/torino/avvisi/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    trovati = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        for link in soup.find_all('a'):
            testo = link.get_text().lower()
            # Cerca parole chiave nei titoli degli avvisi dell'UST
            if any(k in testo for k in ["teatro", "teatrale", "piano estate", "agenda nord", "esperto"]):
                trovati.append(f"🔴 SITO UST TORINO: {link.get_text().strip()}\nLINK: {link['href']}\n")
    except Exception as e:
        print(f"Errore UST Torino: {e}")
    return trovati

def cerca_web_massivo():
    """Ricerca PNRR, Agenda Nord e Piano Estate su tutti i siti .edu.it di Torino"""
    print("Inizio ricerca massiva su siti scolastici (PNRR/Agenda Nord/Estate)...")
    # Query potente che incrocia i grandi progetti con il teatro a Torino
    query = 'site:.edu.it "torino" ("piano estate" OR "agenda nord" OR PNRR OR bando OR avviso) (teatro OR teatrale OR recitazione)'
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    trovati = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        for result in soup.find_all('div', class_='result'):
            t = result.get_text().lower()
            # Filtro per anni recenti per evitare vecchi bandi
            if any(anno in t for anno in ["2024", "2025", "2026"]):
                link = result.find('a', class_='result__a')
                if link:
                    trovati.append(f"🟡 DAL WEB (Scuola/PNRR): {link.get_text()}\nLINK: {link['href']}\n")
    except Exception as e:
        print(f"Errore ricerca web: {e}")
    return trovati

if __name__ == "__main__":
    # Uniamo i risultati di entrambe le ricerche
    risultati_totali = monitora_ust_torino() + cerca_web_massivo()
    
    if risultati_totali:
        # Elimina eventuali duplicati
        risultati_unici = list(set(risultati_totali))
        report = f"REPORT BANDI TEATRO TORINO - {datetime.now().strftime('%d/%m/%Y')}\n"
        report += "Ho trovato i seguenti avvisi che potrebbero contenere laboratori di teatro:\n\n"
        report += "\n".join(risultati_unici)
        report += "\n\nNota: Controlla sempre i moduli interni se il bando è generico (PNRR/Estate)."
        
        print(report)
        invia_mail(report)
    else:
        print("Nessun nuovo bando o progetto trovato oggi.")
