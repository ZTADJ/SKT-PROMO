import requests
import re
import csv
from datetime import datetime
import time
import os
import json

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
    # Wir nutzen ScraperAPI, um das gerenderte HTML zu bekommen
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true"
    
    try:
        print(f"Scanne {country} ({origin_city})...")
        response = requests.get(proxy_url, timeout=120)
        if response.status_code != 200:
            return []

        html = response.text
        results = []

        # Wir suchen alle "DealsOffer" Blöcke im Quellcode
        # Dieser Regex findet alles zwischen {"__typename":"DealsOffer" ... und dem Ende des Objekts }
        offers = re.findall(r'\{"__typename":"DealsOffer".*?\}', html)

        for offer_str in offers:
            try:
                # Wir reparieren den String minimal, falls nötig, und laden ihn als JSON
                offer_data = json.loads(offer_str)
                
                # Check 1: Ist es eine Promo?
                if offer_data.get("isPromo") is True:
                    city_label = offer_data.get("location", {}).get("label")
                    price = offer_data.get("price")
                    
                    if city_label and price:
                        results.append((city_label, price))
            except:
                continue # Falls ein Block mal kein gültiges JSON ist, ignorieren

        # Duplikate entfernen
        unique_results = list(set(results))
        print(f"Erfolg: {len(unique_results)} Promos gefunden.")
        return unique_results

    except Exception as e:
        print(f"Fehler: {e}")
        return []

if __name__ == "__main__":
    all_data = []
    for country, code, origin, url in MARKETS:
        promos = scrape_market(country, code, origin, url)
        all_data.append((country, code, origin, promos))
        time.sleep(1)

    # Datei lokal speichern
    with open("promos.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Year", "Quarter", "Month", "Date", "Country", "Code", "Origin City", "Destination City", "Price"])
        
        now = datetime.now()
        y, m, d = now.year, now.strftime("%B"), now.strftime("%Y-%m-%d %H:%M")
        q = f"Q{(now.month - 1) // 3 + 1} {y}"

        for country, code, origin, promos in all_data:
            if not promos:
                writer.writerow([y, q, m, d, country, code, origin, "No Promo Found", "0"])
            else:
                for dest, price in promos:
                    writer.writerow([y, q, m, d, country, code, origin, dest, price])

    print("CSV erfolgreich erstellt!")
