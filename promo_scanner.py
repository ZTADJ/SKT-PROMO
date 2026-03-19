import requests
import re
import csv
from datetime import datetime
import time
import os

# Dein API-Key
API_KEY = '7820762d03de1f63a29f8b96423cb6a4'

# Die Liste der Maerkte mit den festen O City Codes
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

# Filter fuer Nord- und Mittelamerika
ALLOWED_COUNTRIES = ["US", "CA", "MX", "CR"]

def scrape_market(country_name, country_code, o_city, o_code, url):
    # render=true ist wichtig, um das JSON-Objekt im HTML zu finden
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true&country_code=eu"
    
    try:
        print(f"Scanne {country_name} ({o_code})...")
        response = requests.get(proxy_url, timeout=180)
        if response.status_code != 200:
            print(f"Fehler: Status {response.status_code}")
            return []

        html = response.text
        
        # Wir splitten das HTML bei jedem neuen DealsOffer-Objekt
        chunks = html.split('{"__typename":"DealsOffer"')
        
        market_results = []
        
        for chunk in chunks[1:]: # Index 0 ist der Header/Text vor dem ersten Deal
            # Wir nehmen nur ein sicheres Segment (ca. 1200 Zeichen), um nicht in den naechsten Deal zu rutschen
            segment = chunk[:1200]
            
            # WICHTIG: Nur wenn isPromo:true direkt in diesem Block steht
            if '"isPromo":true' in segment:
                try:
                    # Suche nach Code, Label, Country und Price innerhalb des Segments
                    d_city_code = re.search(r'"code"\s*:\s*"([^"]+)"', segment).group(1)
                    d_city_name = re.search(r'"label"\s*:\s*"([^"]+)"', segment).group(1)
                    d_ctry_code = re.search(r'"countryCode"\s*:\s*"([^"]+)"', segment).group(1)
                    fare = re.search(r'"price"\s*:\s*([\d\.]+)', segment).group(1)

                    # Nur erlaubte Laender hinzufuegen
                    if d_ctry_code in ALLOWED_COUNTRIES:
                        market_results.append([d_city_name, d_city_code, d_ctry_code, fare])
                except Exception:
                    continue

        # Duplikate innerhalb eines Marktes entfernen
        unique_results = []
        seen = set()
        for res in market_results:
            identifier = (res[1], res[3]) # Kombi aus Stadt-Code und Preis
            if identifier not in seen:
                unique_results.append(res)
                seen.add(identifier)
        
        print(f"-> {len(unique_results)} saubere Promos gefunden.")
        return unique_results

    except Exception as e:
        print(f"Fehler bei {o_code}: {e}")
        return []

if __name__ == "__main__":
    # Zeitstempel generieren
    now = datetime.now()
    year_val = now.strftime("%Y")
    month_val = now.strftime("%b").upper() + now.strftime("%y") # Erzeugt z.B. MAR26
    date_val = now.strftime("%Y-%m-%d %H:%M")
    q_val = f"Q{(now.month - 1) // 3 + 1} {year_val}"

    all_rows = []

    # Alle Maerkte nacheinander abarbeiten
    for c_name, c_code, o_city, o_code, url in MARKETS:
        promos = scrape_market(c_name, c_code, o_city, o_code, url)
        
        if not promos:
            # Falls nichts gefunden wurde, schreiben wir eine "No Promo" Zeile
            all_rows.append([year_val, q_val, month_val, date_val, c_code, o_city, o_code, "No Promo Found", "-", "-", "0"])
        else:
            for p in promos:
                # Spalten: Year, Quarter, Month, Date, O Ctry Code, O City, O City Code, D City, D City Code, D Ctry Code, Fare
                all_rows.append([year_val, q_val, month_val, date_val, c_code, o_city, o_code, p[0], p[1], p[2], p[3]])
        
        time.sleep(2) # Kurze Pause fuer die API

    # SPEICHER-LOGIK: Anfuegen (Append) statt Ueberschreiben
    filename = "promos.csv"
    
    # Pruefen, ob die Datei existiert und Inhalt hat
    file_exists = os.path.isfile(filename)
    is_empty = os.path.getsize(filename) == 0 if file_exists else True

    with open(filename, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        
        # Nur Header schreiben, wenn die Datei neu oder leer ist
        if is_empty:
            writer.writerow(["Year", "Quarter", "Month", "Date", "O Ctry Code", "O City", "O City Code", "D City", "D City Code", "D Ctry Code", "Fare"])
        
        # Neue Zeilen unten dranhaengen
        writer.writerows(all_rows)

    print(f"Fertig! Die neuen Daten wurden erfolgreich an {filename} angehaengt.")
