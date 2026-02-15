import requests
import re
import csv
from datetime import datetime
import time
import os

# Dein persönlicher API-Key
API_KEY = '7820762d03de1f63a29f8b96423cb6a4'

# Liste der Märkte, Codes, Städte und URLs
# Format: (Country, CountryCode, OriginCity, URL)
MARKETS = [
    ("Poland", "PL", "Warsaw", "https://wwws.airfrance.pl/deals?zoneCode=NAME&zoneType=AREA"),
    ("Poland", "PL", "Krakow", "https://wwws.airfrance.pl/deals?zoneCode=NAME&zoneType=AREA&originCode=KRK&originType=CITY"),
    ("Hungary", "HU", "Budapest", "https://wwws.airfrance.hu/deals?zoneCode=NAME&zoneType=AREA"),
    ("Czech Republic", "CZ", "Prague", "https://wwws.airfrance.cz/deals?zoneCode=NAME&zoneType=AREA"),
    ("Romania", "RO", "Bucharest", "https://wwws.airfrance.ro/deals?zoneCode=NAME&zoneType=AREA"),
    ("Croatia", "HR", "Zagreb", "https://wwws.airfrance.hr/deals?zoneCode=NAME&zoneType=AREA"),
    ("Croatia", "HR", "Split", "https://wwws.airfrance.hr/deals?zoneCode=NAME&zoneType=AREA&originCode=SPU&originType=CITY"),
    ("Bulgaria", "BG", "Sofia", "https://wwws.airfrance.bg/deals?zoneCode=NAME&zoneType=AREA"),
    ("Turkey", "TR", "Istanbul", "https://wwws.airfrance.com.tr/deals?zoneCode=NAME&zoneType=AREA"),
    ("Israel", "IL", "Tel Aviv", "https://wwws.airfrance.co.il/deals?zoneCode=NAME&zoneType=AREA"),
    ("Serbia", "RS", "Belgrade", "https://wwws.airfrance.rs/deals?zoneCode=NAME&zoneType=AREA")
]

def scrape_market(country, code, origin, url):
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true"
    try:
        print(f"Scanne {country} ({origin})...")
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            html = response.text
            pattern = re.compile(r'Promo fare.*?bwdo-offer-card__city[^>]*>\s*([^<]+)\s*</span>', re.DOTALL)
            found_cities = list(set(pattern.findall(html)))
            clean_cities = [c.strip() for c in found_cities]
            print(f"Erfolg: {len(clean_cities)} Promos für {origin} gefunden.")
            return clean_cities
        else:
            print(f"Fehler {response.status_code} bei {origin}")
            return []
    except Exception as e:
        print(f"Technischer Fehler bei {origin}: {e}")
        return []

def save_to_csv(results):
    file_exists = os.path.isfile('promos.csv')
    now = datetime.now()
    
    # Zeit-Komponenten vorbereiten
    year = now.strftime("%Y")
    quarter = (now.month - 1) // 3 + 1
    month = now.strftime("%B")
    full_date = now.strftime("%Y-%m-%d %H:%M")

    with open('promos.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Kopfzeile nur schreiben, wenn die Datei neu erstellt wird
        if not file_exists or os.stat('promos.csv').st_size == 0:
            writer.writerow(["Year", "Quarter", "Month", "Date", "Country", "Code", "Origin City", "Destination City"])
        
        for (country, code, origin, cities) in results:
            if not cities:
                writer.writerow([year, quarter, month, full_date, country, code, origin, "KEINE PROMOS"])
            else:
                for dest in cities:
                    writer.writerow([year, quarter, month, full_date, country, code, origin, dest])

if __name__ == "__main__":
    final_data = []
    for country, code, origin, url in MARKETS:
        cities = scrape_market(country, code, origin, url)
        final_data.append((country, code, origin, cities))
        time.sleep(2)
    
    save_to_csv(final_data)
    print("Fertig!")
