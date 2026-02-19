import requests
import re
import csv
from datetime import datetime
import time
import os
import io

# Dein persönlicher API-Key
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
    # render=true ist essenziell, um die Preise statt des "*" zu laden
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true"
    try:
        print(f"Scanne {country} ({origin})...")
        response = requests.get(proxy_url, timeout=120)
        if response.status_code == 200:
            html = response.text
            
            # Dieser Regex sucht die Stadt und schaut dann im Text weiter nach Währung und Betrag
            # Er deckt Formate wie "HUF 277,700" oder "277.700 HUF" ab.
            pattern = re.compile(
                r'bwdo-offer-card__city[^>]*>\s*([^<]+)\s*</span>'  # Gruppe 1: Stadt
                r'.*?bwdo-offer-card__price-currency[^>]*>\s*([^<]+)\s*</span>' # Gruppe 2: Währung (z.B. HUF)
                r'.*?bwdo-offer-card__price-amount[^>]*>\s*([^<]+)\s*</span>', # Gruppe 3: Betrag (z.B. 277,700)
                re.DOTALL
            )
            
            matches = pattern.findall(html)
            results = []
            for m in matches:
                city = m[0].strip()
                currency = m[1].strip()
                # Säubert den Preis von HTML-Resten und Leerzeichen
                price = m[2].strip().replace('&nbsp;', '').replace('\xa0', '')
                results.append((city, currency, price))
            
            unique_results = list(set(results))
            print(f"Erfolg: {len(unique_results)} Angebote für {origin} extrahiert.")
            return unique_results
        else:
            print(f"Fehler {response.status_code} bei {origin}")
            return []
    except Exception as e:
        print(f"Technischer Fehler bei {origin}: {e}")
        return []

def update_gist(csv_content):
    # Deine Gist ID hier einfügen
    gist_id = "DEINE_SECRET_GIST_ID_HIER_EINTRAGEN"
    token = os.getenv("GIST_TOKEN")
    if not token:
        print("Kein Token gefunden!")
        return

    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {token}"}
    payload = {"files": {"promos.csv": {"content": csv_content}}}
    
    r = requests.patch(url, headers=headers, json=payload)
    if r.status_code == 200:
        print("Gist mit Preisen und Währungen aktualisiert!")

if __name__ == "__main__":
    final_results = []
    for country, code, origin, url in MARKETS:
        data = scrape_market(country, code, origin, url)
        final_results.append((country, code, origin, data))
        time.sleep(1) # Kurze Pause zur Schonung der API
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Neue Header-Struktur
    writer.writerow(["Year", "Quarter", "Month", "Date", "Country", "Code", "Origin City", "Destination City", "Currency", "Price"])
    
    now = datetime.now()
    year_val = now.strftime("%Y")
    q_val = f"Q{(now.month - 1) // 3 + 1} {year_val}"
    month_val = now.strftime("%B")
    date_val = now.strftime("%Y-%m-%d %H:%M")

    for (country, code, origin, details) in final_results:
        if not details:
            writer.writerow([year_val, q_val, month_val, date_val, country, code, origin, "No promos", "-", "-"])
        else:
            for dest, curr, price in details:
                writer.writerow([year_val, q_val, month_val, date_val, country, code, origin, dest, curr, price])
    
    update_gist(output.getvalue())
