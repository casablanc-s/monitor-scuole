import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def invia_mail(testo_mail):
    # Usiamo i nomi esatti dei tuoi Secrets
    mittente = os.getenv("EMAIL_MITTENTE")
    password = os.getenv("EMAIL_PASSWORD")
    destinatario = os.getenv("EMAIL_DESTINATARIO")

    if not mittente or not password:
        print("Errore: Credenziali non trovate!")
        return

    msg = MIMEMultipart()
    msg['From'] = mittente
    msg['To'] = destinatario
    msg['Subject'] = f"🔔 BANDO TEATRO TROVATO - {datetime.now().strftime('%d/%m')}"
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

def cerca_bandi():
    print(f"Avvio ricerca bandi... {datetime.now().strftime('%H:%M')}")
    # Cerca sui siti delle scuole di Torino bandi/avvisi per teatro del 2024/25/26
    query = 'site:.edu.it "torino" (bando OR avviso) (teatro OR teatrale)'
    query_enc = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={query_enc}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        risultati = soup.find_all('div', class_='result')
        
        trovati = []
        anni_validi = ["2024", "2025", "2026"]
        
        for res in risultati:
            link = res.find('a', class_='result__a')
            if link:
                titolo = link.get_text()
                url_bando = link['href']
                testo_completo = res.get_text().lower()
                
                # Filtriamo per anno per non avere roba vecchia
                if any(anno in titolo or anno in testo_completo for anno in anni_validi):
                    trovati.append(f"SCUOLA: {titolo}\nLINK: {url_bando}\n")

        if trovati:
            testo_finale = "Ciao! Ho trovato questi nuovi potenziali bandi di teatro:\n\n" + "\n".join(trovati)
            print(testo_finale)
            invia_mail(testo_finale)
        else:
            print("Nessun bando recente trovato oggi.")

    except Exception as e:
        print(f"Errore durante la ricerca: {e}")

if __name__ == "__main__":
    cerca_bandi()
