import requests
import re
import csv
from datetime import datetime
import time

# Dein persönlicher API-Key
API_KEY = '7820762d03de1f63a29f8b96423cb6a4'

# Liste der Märkte und URLs
MARKETS = {
    "Polen": "https://wwws.airfrance.pl/deals?zoneCode=NAME&zoneType=AREA",
    "Ungarn": "https://wwws.airfrance.hu/deals?zoneCode=NAME&zoneType=AREA",
    "Tschechien": "https://wwws.airfrance.cz/deals?zoneCode=NAME&zoneType=AREA",
    "Rumanien": "https://wwws.airfrance.ro/deals?zoneCode=NAME&zoneType=AREA",
    "Kroatien": "https://wwws.airfrance.hr/deals?zoneCode=NAME&zoneType=AREA",
    "Bulgarien": "https://wwws.airfrance.bg/deals?zoneCode=NAME&zoneType=AREA",
    "Turkei": "https://wwws.airfrance.com.tr/deals?zoneCode=NAME&zoneType=AREA",
    "Israel": "https://wwws.airfrance.co.il/deals?zoneCode=NAME&zoneType=AREA"
}

def scrape_market(market_name, url):
    # Der Tunnel-Link mit render=true
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true"
    
    try:
        print(f"Scanne Markt: {market_name}...")
        response = requests.get(proxy_url, timeout=120)
        
        if response.status_code == 200:
            html = response.text
            # Suche nach Städten mit Promo fare
            pattern = re.compile(r'Promo fare.*?bwdo-offer-card__city[^>]*>\s*([^<]+)\s*</span>', re.DOTALL)
            found_cities = list(set(pattern.findall(html)))
            clean_cities = [c.strip() for c in found_cities]
            
            print(f"Erfolg für {market_name}: {len(clean_cities)} Promos gefunden.")
            return clean_cities
        else:
            print(f"Fehler bei {market_name}: Status {response.status_code}")
            return []
    except Exception as e:
        print(f"Technischer Fehler bei {market_name}: {e}")
        return []

def save_to_csv(data):
    # data ist eine Liste von [Zeitpunkt, Markt, Stadt]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open('promos.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for market, cities in data.items():
            if not cities:
                # Optional: Auch vermerken, wenn ein Markt keine Promos hat
                writer.writerow([now, market, "KEINE PROMOS"])
            for city in cities:
                writer.writerow([now, market, city])

if __name__ == "__main__":
    all_results = {}
    
    for market, url in MARKETS.items():
        cities = scrape_market(market, url)
        all_results[market] = cities
        # Kleine Pause, um den API-Dienst nicht zu überlasten
        time.sleep(2)
    
    save_to_csv(all_results)
    print("Alle Märkte verarbeitet und gespeichert.")
