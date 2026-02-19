import requests
import re
import csv
from datetime import datetime
import time
import os

# Dein API-Key bleibt gleich
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

def scrape_market(country, code, origin, url):
    # WICHTIG: Wir sagen ScraperAPI, dass es warten soll, bis die Preise (.bwdo-offer-card__price-amount) da sind
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true&wait_for_selector=.bwdo-offer-card__price-amount"
    
    try:
        print(f"Scanne {country} ({origin})...")
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            html = response.text
            
            # Diese Suche zieht alle Staedte, Waehrungen und Betraege einzeln raus
            cities = re.findall(r'bwdo-offer-card__city[^>]*>\s*(.*?)\s*</span>', html)
            currencies = re.findall(r'bwdo-offer-card__price-currency[^>]*>\s*(.*?)\s*</span>', html)
            amounts = re.findall(r'bwdo-offer-card__price-amount[^>]*>\s*(.*?)\s*</span>', html)

            results = []
            for city, curr, price in zip(cities, currencies, amounts):
                clean_city = city.strip()
                clean_curr = curr.strip()
                clean_price = price.strip().replace('&nbsp;', '').replace('\xa0', '').replace('*', '')
                
                # Nur speichern, wenn wir wirklich einen Preis haben
                if clean_price:
                    results.append((clean_city, clean_curr, clean_price))
            
            print(f"Erfolg: {len(results)} Angebote fuer {origin} gefunden.")
            return results
        else:
            print(f"Fehler {response.status_code} bei {origin}")
            return []
    except Exception as e:
        print(f"Technischer Fehler bei {origin}: {e}")
        return []

if __name__ == "__main__":
    final_results = []
    for country, code, origin, url in MARKETS:
        data = scrape_market(country, code, origin, url)
        final_results.append((country, code, origin, data))
        time.sleep(2) # Kurz warten
    
    # Datei lokal schreiben (Das braucht GitHub Actions zum Committen)
    file_exists = os.path.isfile("promos.csv")
    
    with open("promos.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Year", "Quarter", "Month", "Date", "Country", "Code", "Origin City", "Destination City", "Currency", "Price"])
        
        now = datetime.now()
        year_val = now.strftime("%Y")
        q_val = f"Q{(now.month - 1) // 3 + 1} {year_val}"
        month_val = now.strftime("%B")
        date_val = now.strftime("%Y-%m-%d %H:%M")

        for (country, code, origin, details) in final_results:
            if not details:
                # Falls nichts gefunden wurde, schreiben wir einen Platzhalter, damit die Datei nicht leer bleibt
                writer.writerow([year_val, q_val, month_val, date_val, country, code, origin, "Keine Angebote gefunden", "-", "-"])
            else:
                for dest, curr, price in details:
                    writer.writerow([year_val, q_val, month_val, date_val, country, code, origin, dest, curr, price])
    
    print("Fertig! promos.csv wurde lokal aktualisiert.")
