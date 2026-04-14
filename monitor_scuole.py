import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse
import time

def cerca_bandi_smart():
    print(f"=== RICERCA AUTOMATICA BANDI TORINO - {datetime.now().strftime('%d/%m/%Y')} ===")
    
    # Query: cerca sui siti .edu.it documenti con Torino, bando/avviso e teatro
    query = 'site:.edu.it "torino" (bando OR avviso) (teatro OR teatrale OR "laboratorio teatrale")'
    query_enc = urllib.parse.quote(query)
    
    # Usiamo DuckDuckGo versione HTML (più semplice da leggere per uno script)
    url = f"https://html.duckduckgo.com/html/?q={query_enc}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Errore di connessione: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        # Troviamo tutti i blocchi dei risultati
        risultati = soup.find_all('div', class_='result')

        print(f"Analizzando i risultati trovati...\n")
        
        trovati = []
        for res in risultati:
            link_tag = res.find('a', class_='result__a')
            snippet_tag = res.find('a', class_='result__snippet')
            
            if link_tag:
                titolo = link_tag.get_text()
                url_bando = link_tag['href']
                # Verifichiamo se nell'anteprima si parla di anni recenti (2024, 2025, 2026)
                testo_anteprima = snippet_tag.get_text().lower() if snippet_tag else ""
                
                # Filtro semplice per escludere bandi molto vecchi
                anni_recenti = ["2024", "2025", "2026"]
                if any(anno in testo_anteprima or anno in titolo for anno in anni_recenti):
                    print(f"TROVATO: {titolo}")
                    print(f"LINK: {url_bando}\n")
                    trovati.append(f"{titolo} - {url_bando}")

        if not trovati:
            print("Nessun bando recente trovato oggi.")
    except Exception as e:
        print(f"Errore durante la ricerca: {e}")

if __name__ == "__main__":
    cerca_bandi_smart()
