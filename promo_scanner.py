import requests
import re
import csv
from datetime import datetime
import time
import os

API_KEY = '7820762d03de1f63a29f8b96423cb6a4'

# Liste der Märkte mit dem jeweiligen O City Code
MARKETS = [
    ("Poland", "PL", "Warsaw", "WAW", "https://wwws.airfrance.pl/deals?zoneCode=NAME&zoneType=AREA"),
    ("Poland", "PL", "Krakow", "KRK", "https://wwws.airfrance.pl/deals?zoneCode=NAME&zoneType=AREA&originCode=KRK&originType=CITY"),
    ("Hungary", "HU", "Budapest", "BUD", "https://wwws.airfrance.hu/deals?zoneCode=NAME&zoneType=AREA"),
    ("Czech Republic", "CZ", "Prague", "PRG", "https://wwws.airfrance.cz/deals?zoneCode=NAME&zoneType=AREA"),
    ("Romania", "RO", "Bucharest", "BUH", "https://wwws.airfrance.ro/deals?zoneCode=NAME&zoneType=AREA"),
    ("Croatia", "HR", "Zagreb", "ZAG", "https://wwws.airfrance.hr/deals?zoneCode=NAME&zoneType=AREA"),
    ("Croatia", "HR", "Split", "SPU", "https://wwws.airfrance.hr/deals?zoneCode=NAME&zoneType=AREA&originCode=SPU&originType=CITY"),
    ("Bulgaria", "BG", "Sofia", "SOF", "https://wwws.airfrance.bg/deals?zoneCode=NAME&zoneType=AREA"),
    ("Turkey", "TR", "Istanbul", "IST", "https://wwws.airfrance.com.tr/deals?zoneCode=NAME&zoneType=AREA"),
    ("Israel", "IL", "Tel Aviv", "TLV", "https://wwws.airfrance.co.il/deals?zoneCode=NAME&zoneType=AREA"),
    ("Serbia", "RS", "Belgrade", "BEG", "https://wwws.airfrance.rs/deals?zoneCode=NAME&zoneType=AREA")
]

ALLOWED_COUNTRY_CODES = ["US", "CA", "MX", "CR"]

def scrape_market(country, country_code, origin_city, origin_code, url):
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true&country_code=eu"
    
    try:
        print(f"Scanne {country} ({origin_city})...")
        response = requests.get(proxy_url, timeout=180)
        if response.status_code != 200:
            return []

        html = response.text
        
        # SCHRITT 1: Wir finden jeden einzelnen DealsOffer-Block separat.
        # So verhindern wir, dass Daten zwischen verschiedenen Städten vermischt werden.
        offer_blocks = re.findall(r'\{"__typename":"DealsOffer".*?\}\}', html)

        results = []
        for block in offer_blocks:
            # SCHRITT 2: Nur wenn "isPromo":true im Block steht, extrahieren wir den Rest
            if '"isPromo":true' in block:
                try:
                    # Extrahiere Details nur aus diesem EINEN Block
                    d_city_code = re.search(r'"code":"([^"]+)"', block).group(1)
                    d_city_name = re.search(r'"label":"([^"]+)"', block).group(1)
                    d_country_code = re.search(r'"countryCode":"([^"]+)"', block).group(1)
                    fare = re.search(r'"price":(\d+)', block).group(1)

                    # SCHRITT 3: Filter auf Zielgebiete
                    if d_country_code in ALLOWED_COUNTRY_CODES:
                        results.append({
                            'd_city': d_city_name,
                            'd_city_code': d_city_code,
                            'd_ctry_code': d_country_code,
                            'fare': fare
                        })
                except AttributeError:
                    # Falls ein Block unvollständig ist, überspringen
                    continue
            
        unique_results = { (f['d_city'], f['d_city_code']): f for f in results }.values()
        print(f"Erfolg: {len(unique_results)} saubere Promos gefunden.")
        return list(unique_results)

    except Exception as e:
        print(f"Fehler: {e}")
        return []

if __name__ == "__main__":
    all_rows = []
    now = datetime.now()
    year_full = now.strftime("%Y")
    month_custom = now.strftime("%b").upper() + now.strftime("%y")
    date_val = now.strftime("%Y-%m-%d %H:%M")
    q_val = f"Q{(now.month - 1) // 3 + 1} {year_full}"

    for country, country_code, origin_city, origin_code, url in MARKETS:
        promos = scrape_market(country, country_code, origin_city, origin_code, url)
        
        if not promos:
            all_rows.append([year_full, q_val, month_custom, date_val, country_code, origin_city, origin_code, "No Promo Found", "-", "-", "0"])
        else:
            for p in promos:
                all_rows.append([
                    year_full, q_val, month_custom, date_val, 
                    country_code, origin_city, origin_code, 
                    p['d_city'], p['d_city_code'], p['d_ctry_code'], p['fare']
                ])
        time.sleep(2)

    with open("promos.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Exakte Spaltenköpfe laut Vorgabe
        writer.writerow(["Year", "Quarter", "Month", "Date", "O Ctry Code", "O City", "O City Code", "D City", "D City Code", "D Ctry Code", "Fare"])
        writer.writerows(all_rows)

    print("Fertig! Die Daten wurden strikt getrennt extrahiert.")
