import requests
import re
import csv
from datetime import datetime
import time
import os

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
    # Wir nutzen render=true, um sicherzustellen, dass die JSON-Daten im HTML landen
    proxy_url = f"http://api.scraperapi.com?api_key={API_KEY}&url={url}&render=true&country_code=eu"
    
    try:
        print(f"Scanne {country_name} ({o_code})...")
        response = requests.get(proxy_url, timeout=180)
        if response.status_code != 200:
            return []

        html = response.text
        
        # 1. Wir zerlegen das HTML in einzelne Brocken, jeder beginnt mit einem DealsOffer
        raw_offers = html.split('{"__typename":"DealsOffer"')
        
        market_results = []
        
        # Der erste Split ist Müll (Text vor dem ersten Deal), also überspringen wir index 0
        for chunk in raw_offers[1:]:
            # Wir nehmen nur den Teil bis zum Ende des Objekts, um nicht in den nächsten Deal zu rutschen
            chunk = chunk[:1000] 
            
            # WICHTIGSTER CHECK: Ist es eine Promo?
            if '"isPromo":true' in chunk:
                try:
                    # Wir ziehen die Daten mit ganz einfachen Suchen raus
                    d_city_name = re.search(r'"label":"([^"]+)"', chunk).group(1)
                    d_city_code = re.search(r'"code":"([^"]+)"', chunk).group(1)
                    d_ctry_code = re.search(r'"countryCode":"([^"]+)"', chunk).group(1)
                    fare = re.search(r'"price":(\d+)', chunk).group(1)

                    # Filter auf deine Länder
                    if d_ctry_code in ALLOWED_COUNTRIES:
                        market_results.append([d_city_name, d_city_code, d_ctry_code, fare])
                except:
                    continue

        # Duplikate filtern
        unique_results = []
        for res in market_results:
            if res not in unique_results:
                unique_results.append(res)
        
        print(f"-> {len(unique_results)} Promos gefunden.")
        return unique_results

    except Exception as e:
        print(f"Fehler: {e}")
        return []

if __name__ == "__main__":
    now = datetime.now()
    year_val = now.strftime("%Y")
    # FEB26 Format
    month_val = now.strftime("%b").upper() + now.strftime("%y")
    date_val = now.strftime("%Y-%m-%d %H:%M")
    q_val = f"Q{(now.month - 1) // 3 + 1} {year_val}"

    all_data = []

    for c_name, c_code, o_city, o_code, url in MARKETS:
        promos = scrape_market(c_name, c_code, o_city, o_code, url)
        
        if not promos:
            all_data.append([year_val, q_val, month_val, date_val, c_code, o_city, o_code, "No Promo Found", "-", "-", "0"])
        else:
            for p in promos:
                # Spalten: Year, Quarter, Month, Date, O Ctry Code, O City, O City Code, D City, D City Code, D Ctry Code, Fare
                all_data.append([year_val, q_val, month_val, date_val, c_code, o_city, o_code, p[0], p[1], p[2], p[3]])
        
        time.sleep(2)

    with open("promos.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Year", "Quarter", "Month", "Date", "O Ctry Code", "O City", "O City Code", "D City", "D City Code", "D Ctry Code", "Fare"])
        writer.writerows(all_data)

    print("Fertig! Check jetzt die promos.csv.")
