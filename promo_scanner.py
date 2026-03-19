import requests
import re
import csv
from datetime import datetime
import time

API_KEY = '7820762d03de1f63a29f8b96423cb6a4'

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

ALLOWED_COUNTRIES = ["US", "CA", "MX", "CR"]

def scrape_market(country_name, country_code, o_city, o_code, url):
    # Wir nutzen wieder render=true, um sicherzugehen, dass das JS-Objekt vollstaendig ist
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true&country_code=eu"
    
    try:
        print(f"Scanne {country_name} ({o_code})...")
        response = requests.get(proxy_url, timeout=180)
        if response.status_code != 200:
            return []

        html = response.text
        
        # Diese Logik sucht gezielt nach den Bloecken, die mit DealsOffer beginnen.
        # Wir splitten das HTML bei jedem DealsOffer-Beginn auf.
        chunks = html.split('{"__typename":"DealsOffer"')
        
        market_results = []
        
        for chunk in chunks[1:]: # Index 0 ist der Text davor
            # Wir begrenzen den Chunk auf den Bereich bis zum Ende des Angebots.
            # Da ein Angebot ca. 500-800 Zeichen hat, nehmen wir 1200 zur Sicherheit.
            segment = chunk[:1200]
            
            # 1. PRUEFUNG: Ist es eine Promo? (Muss exakt "isPromo":true enthalten)
            if '"isPromo":true' in segment:
                try:
                    # 2. DATEN EXTRAHIEREN
                    # Wir suchen den Code (z.B. RDU)
                    d_city_code = re.search(r'"code"\s*:\s*"([^"]+)"', segment).group(1)
                    # Wir suchen das Label (z.B. Raleigh Durham)
                    d_city_name = re.search(r'"label"\s*:\s*"([^"]+)"', segment).group(1)
                    # Wir suchen das Land (z.B. US)
                    d_ctry_code = re.search(r'"countryCode"\s*:\s*"([^"]+)"', segment).group(1)
                    # Wir suchen den Preis (kann Zahl oder Dezimal sein)
                    fare = re.search(r'"price"\s*:\s*([\d\.]+)', segment).group(1)

                    # 3. FILTER: Nur US, CA, MX, CR
                    if d_ctry_code in ALLOWED_COUNTRIES:
                        market_results.append([d_city_name, d_city_code, d_ctry_code, fare])
                except Exception:
                    continue # Falls ein Feld fehlt, naechstes Segment

        # Duplikate entfernen (gleiches Ziel, gleiche Fare)
        unique_results = []
        seen = set()
        for res in market_results:
            identifier = (res[1], res[3]) # Code + Fare
            if identifier not in seen:
                unique_results.append(res)
                seen.add(identifier)
        
        print(f"-> {len(unique_results)} saubere Promos gefunden.")
        return unique_results

    except Exception as e:
        print(f"Fehler bei {o_code}: {e}")
        return []

if __name__ == "__main__":
    now = datetime.now()
    year_val = now.strftime("%Y")
    month_val = now.strftime("%b").upper() + now.strftime("%y") # FEB26
    date_val = now.strftime("%Y-%m-%d %H:%M")
    q_val = f"Q{(now.month - 1) // 3 + 1} {year_val}"

    all_rows = []

    for c_name, c_code, o_city, o_code, url in MARKETS:
        promos = scrape_market(c_name, c_code, o_city, o_code, url)
        
        if not promos:
            all_rows.append([year_val, q_val, month_val, date_val, c_code, o_city, o_code, "No Promo Found", "-", "-", "0"])
        else:
            for p in promos:
                # Spalten: Year, Quarter, Month, Date, O Ctry Code, O City, O City Code, D City, D City Code, D Ctry Code, Fare
                all_rows.append([year_val, q_val, month_val, date_val, c_code, o_city, o_code, p[0], p[1], p[2], p[3]])
        
        time.sleep(2)

    with open("promos.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Year", "Quarter", "Month", "Date", "O Ctry Code", "O City", "O City Code", "D City", "D City Code", "D Ctry Code", "Fare"])
        writer.writerows(all_rows)

    print("CSV erfolgreich erstellt!")
