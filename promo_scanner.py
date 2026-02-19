import requests
import re
import csv
from datetime import datetime
import time
import os
import io

# Dein persönlicher API-Key
API_KEY = '7820762d03de1f63a29f8b96423cb6a4'

# Liste der Märkte, Codes, Städte und URLs
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

def update_gist(csv_content):
    # HIER DEINE LANGE GIST-ID EINTRAGEN (aus der Browser-URL des Gists)
    gist_id = "DEINE_SECRET_GIST_ID_HIER_EINTRAGEN"
    token = os.getenv("GIST_TOKEN")
    
    if not token:
        print("Fehler: Kein GIST_TOKEN in den Repository Secrets gefunden!")
        return

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {token}"}
    payload = {"files": {"promos.csv": {"content": csv_content}}}
    
    try:
        r = requests.patch(url, headers=headers, json=payload)
        if r.status_code == 200:
            print("Secret Gist erfolgreich aktualisiert!")
        else:
            print(f"Gist-Fehler: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Fehler beim Gist-Update: {e}")

if __name__ == "__main__":
    final_results = []
    for country, code, origin, url in MARKETS:
        cities = scrape_market(country, code, origin, url)
        final_results.append((country, code, origin, cities))
        time.sleep(2)
    
    # CSV-Struktur im Speicher aufbauen
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header Zeile
    writer.writerow(["Year", "Quarter", "Month", "Date", "Country", "Code", "Origin City", "Destination City"])
    
    now = datetime.now()
    year_val = now.strftime("%Y")
    # Format: Q1 2026
    q_val = f"Q{(now.month - 1) // 3 + 1} {year_val}"
    month_val = now.strftime("%B")
    date_val = now.strftime("%Y-%m-%d %H:%M")

    for (country, code, origin, cities) in final_results:
        if not cities:
            # Jetzt "No promos" statt "KEINE PROMOS"
            writer.writerow([year_val, q_val, month_val, date_val, country, code, origin, "No promos"])
        else:
            for dest in cities:
                writer.writerow([year_val, q_val, month_val, date_val, country, code, origin, dest])
    
    # Den gesamten Inhalt an den Secret Gist senden
    update_gist(output.getvalue())
    print("Vorgang abgeschlossen.")
