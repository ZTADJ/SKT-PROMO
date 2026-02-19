import requests
import re
import csv
from datetime import datetime
import time
import os

# Dein API-Key
API_KEY = '7820762d03de1f63a29f8b96423cb6a4'

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

def scrape_market(country, country_code, origin_city, url):
    # Wir nutzen render=true (für JS) und country_code=eu (damit AF uns nicht blockt)
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true&country_code=eu"
    
    try:
        print(f"Scanne {country} ({origin_city})...")
        # Längeres Timeout, da Rendering Zeit braucht
        response = requests.get(proxy_url, timeout=180)
        
        if response.status_code != 200:
            print(f"Fehler: Status {response.status_code}")
            return []

        html = response.text
        
        # Dieser Regex sucht nach Dallas/NYC etc., prüft isPromo und greift den Preis.
        # re.DOTALL ist wichtig, damit ".*?" auch über Zeilenumbrüche hinweg sucht.
        pattern = r'"label"\s*:\s*"([^"]+)"\s*.*?"isPromo"\s*:\s*true\s*.*?"price"\s*:\s*(\d+)'
        matches = re.findall(pattern, html, re.DOTALL)

        results = []
        for city, price in matches:
            # Wir nehmen nur "echte" Städtenamen (kurz genug)
            if len(city) < 40:
                results.append((city, price))
            
        unique_results = list(set(results))
        print(f"Erfolg: {len(unique_results)} Promos für {origin_city} gefunden.")
        return unique_results

    except Exception as e:
        print(f"Technischer Fehler bei {origin_city}: {e}")
        return []

if __name__ == "__main__":
    all_data = []
    
    # Märkte abarbeiten
    for country, code, origin, url in MARKETS:
        promos = scrape_market(country, code, origin, url)
        all_data.append((country, code, origin, promos))
        # Kurze Pause für die API-Stabilität
        time.sleep(2)

    # Datei schreiben
    filename = "promos.csv"
    now = datetime.now()
    year_val = now.strftime("%Y")
    q_val = f"Q{(now.month - 1) // 3 + 1} {year_val}"
    month_val = now.strftime("%B")
    date_val = now.strftime("%Y-%m-%d %H:%M")

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(["Year", "Quarter", "Month", "Date", "Country", "Code", "Origin City", "Destination City", "Price"])
        
        for country, code, origin, promos in all_data:
            if not promos:
                # Damit die Datei nicht "leer" aussieht für Git
                writer.writerow([year_val, q_val, month_val, date_val, country, code, origin, "No Promo Found", "0"])
            else:
                for dest, price in promos:
                    writer.writerow([year_val, q_val, month_val, date_val, country, code, origin, dest, price])

    print(f"Fertig! {filename} wurde erstellt.")
