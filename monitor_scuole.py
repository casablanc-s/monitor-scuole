import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def invia_mail(testo_mail):
    mittente = os.getenv("EMAIL_MITTENTE")
    password = os.getenv("EMAIL_PASSWORD")
    destinatario = os.getenv("EMAIL_DESTINATARIO")

    if not mittente or not password:
        print("Errore: Credenziali non trovate!")
        return

    msg = MIMEMultipart()
    msg['From'] = mittente
    msg['To'] = destinatario
    msg['Subject'] = f"🎭 MONITORAGGIO BANDI: Novità Torino - {datetime.now().strftime('%d/%m')}"
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
    print(f"=== AVVIO RICERCA POTENZIATA (PNRR, AGENDA NORD, PIANO ESTATE) ===")
    
    # Query avanzata che include i grandi progetti "ombrello"
    termini_progetto = '(PNRR OR "Agenda Nord" OR "Piano Estate" OR "FSE" OR "PON" OR "esperto esterno")'
    termini_teatro = '(teatro OR teatrale OR recitazione OR drammatizzazione OR "espressione corporea")'
    query = f'site:.edu.it "torino" {termini_progetto} {termini_teatro}'
    
    query_enc = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={query_enc}"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        risultati = soup.find_all('div', class_='result')
        
        trovati_diretti = []
        trovati_potenziali = []
        anni_validi = ["2024", "2025", "2026"]
        
        for res in risultati:
            link = res.find('a', class_='result__a')
            if not link: continue
            
            titolo = link.get_text()
            url_bando = link['href']
            testo_anteprima = res.get_text().lower()
            
            # Verifichiamo se è roba recente
            if any(anno in titolo or anno in testo_anteprima for anno in anni_validi):
                # Se leggiamo esplicitamente "teatro" è un colpo sicuro
                if any(t in testo_anteprima for t in ["teatro", "teatrale", "recitazione"]):
                    trovati_diretti.append(f"🔴 BANDO TEATRO ESPLICITO: {titolo}\nLINK: {url_bando}\n")
                else:
                    # Se è un grande bando ma la parola teatro non si legge nell'anteprima
                    trovati_potenziali.append(f"🟡 PROGETTO QUADRO (Controllare moduli interni): {titolo}\nLINK: {url_bando}\n")

        if trovati_diretti or trovati_potenziali:
            report = "Ciao! Ecco i risultati della scansione odierna su Torino e provincia:\n\n"
            
            if trovati_diretti:
                report += "--- BANDI CON RIFERIMENTO DIRETTO ---\n" + "\n".join(trovati_diretti) + "\n"
            
            if trovati_potenziali:
                report += "--- PROGETTI AMPI (PNRR/AGENDA NORD) DA VERIFICARE ---\n"
                report += "Nota: questi bandi potrebbero contenere moduli di teatro all'interno.\n\n"
                report += "\n".join(trovati_potenziali)
            
            print(report)
            invia_mail(report)
        else:
            print("Nessun bando o progetto quadro trovato oggi.")

    except Exception as e:
        print(f"Errore durante la ricerca: {e}")

if __name__ == "__main__":
    cerca_bandi()
