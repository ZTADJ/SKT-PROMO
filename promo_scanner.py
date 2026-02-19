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

# Die erlaubten Länder-Codes (Nord-/Mittelamerika)
ALLOWED_COUNTRY_CODES = ["US", "CA", "MX", "CR"]

def scrape_market(country, country_code, origin_city, url):
    # country_code=eu hilft gegen Geo-Blocking, render=true laed JS
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true&country_code=eu"
    
    try:
        print(f"Scanne {country} ({origin_city})...")
        response = requests.get(proxy_url, timeout=180)
        
        if response.status_code != 200:
            print(f"Fehler: Status {response.status_code}")
            return []

        html = response.text
        
        # Regex fuer Label, CountryCode (US/CA/MX/CR), isPromo und Price
        pattern = r'"label"\s*:\s*"([^"]+)"\s*,\s*"countryCode"\s*:\s*"([^"]+)"\s*.*?"isPromo"\s*:\s*true\s*.*?"price"\s*:\s*(\d+)'
        
        matches = re.findall(pattern, html, re.DOTALL)

        results = []
        for city, dest_country_code, price in matches:
            if dest_country_code in ALLOWED_COUNTRY_CODES:
                results.append((city, dest_country_code, price))
            
        unique_results = list(set(results))
        print(f"Erfolg: {len(unique_results)} Promos fuer {origin_city} extrahiert.")
        return unique_results

    except Exception as e:
        print(f"Technischer Fehler bei {origin_city}: {e}")
        return []

if __name__ == "__main__":
    all_data = []
    
    for country, code, origin, url in MARKETS:
        promos = scrape_market(country, code, origin, url)
        all_data.append((country, code, origin, promos))
        time.sleep(2)

    filename = "promos.csv"
    now = datetime.now()
    
    # Formatierung: Year (2026), Month (FEB26), Date (2026-02-19)
    year_full = now.strftime("%Y")
    month_custom = now.strftime("%b").upper() + now.strftime("%y") # Erzeugt z.B. FEB26
    date_val = now.strftime("%Y-%m-%d %H:%M")
    q_val = f"Q{(now.month - 1) // 3 + 1} {year_full}"

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        
        # Neue Spaltennamen laut Wunsch
        writer.writerow(["Year", "Quarter", "Month", "Date", "O Ctry", "O Ctry Code", "O City", "D City", "D Ctry Code", "Fare"])
        
        for country, code, origin, promos in all_data:
            if not promos:
                writer.writerow([year_full, q_val, month_custom, date_val, country, code, origin, "No Promo Found", "-", "0"])
            else:
                for dest_city, dest_country_code, price in promos:
                    writer.writerow([year_full, q_val, month_custom, date_val, country, code, origin, dest_city, dest_country_code, price])

    print(f"Fertig! {filename} wurde mit neuen Headern erstellt.")
