import requests
import re
import csv
from datetime import datetime

# Die URL von Air France Polen
URL = "https://wwws.airfrance.pl/deals?zoneCode=NAME&zoneType=AREA"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def scrape_air_france():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=30)
        html = response.text
        
        # Wir suchen nach dem Muster: Promo fare + etwas Text + Stadtname
        # Wir nutzen RegEx (reguläre Ausdrücke), um den Text zwischen den Tags zu finden
        pattern = re.compile(r'Promo fare.*?bwdo-offer-card__city[^>]*>\s*([^<]+)\s*</span>', re.DOTALL)
        found_cities = pattern.findall(html)
        
        # Ergebnisse säubern (Leerzeichen entfernen)
        found_cities = [city.strip() for city in found_cities]
        
        print(f"Gefundene Städte mit Promos: {found_cities}")
        return found_cities
    except Exception as e:
        print(f"Fehler beim Scannen: {e}")
        return []

def save_to_csv(cities):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Datei öffnen und neue Zeilen hinzufügen
    with open('promos.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not cities:
            writer.writerow([now, "Keine Promos gefunden"])
        for city in cities:
            writer.writerow([now, city])

if __name__ == "__main__":
    promo_cities = scrape_air_france()
    save_to_csv(promo_cities)
