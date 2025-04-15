import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://www.bcb.gob.bo/?q=resultado-subastas-bonos-tesoro"
PDF_BASE = "https://www.bcb.gob.bo"
PDF_FOLDER = "../data/pdfs/tgn_bonos"
os.makedirs(PDF_FOLDER, exist_ok=True)

MONTHS_ES = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

def parse_spanish_date(text):
    match = re.search(r"(\d{1,2})\s+([A-ZÁÉÍÓÚÑ]+),?\s+(\d{4})", text.upper())
    if match:
        day, month_str, year = match.groups()
        try:
            month = MONTHS_ES[month_str]
            return datetime(int(year), month, int(day))
        except KeyError:
            return None
    return None

# === Main scraper ===
def scrape_bonos_tgn_pdfs(start_date, end_date):
    print(f"🔍 Scraping BONOS TGN PDFs from {start_date.date()} to {end_date.date()}...")

    response = requests.get(BASE_URL)
    if response.status_code != 200:
        print(f"Failed to access the page: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("div", class_="views-row")

    found = 0
    downloaded = 0

    for row in rows:
        date_tag = row.find("span", class_="date-display-single")
        link_tag = row.find("a", href=True)

        if not date_tag or not link_tag:
            continue

        auction_date = parse_spanish_date(date_tag.text.strip())
        if not auction_date or not (start_date <= auction_date <= end_date):
            continue

        href = link_tag["href"]
        if "BT" not in href or not href.endswith(".pdf"):
            continue
        pdf_url = href if href.startswith("http") else PDF_BASE + href

        filename = f"BT_{auction_date.strftime('%Y_%m_%d')}.pdf"
        filepath = os.path.join(PDF_FOLDER, filename)

        if not os.path.exists(filepath):
            print(f"⬇️ Downloading {filename}")
            file_resp = requests.get(pdf_url)
            with open(filepath, "wb") as f:
                f.write(file_resp.content)
            downloaded += 1
        else:
            print(f"Already downloaded: {filename}")

        found += 1

    print(f"\n{downloaded} new PDFs downloaded ({found} matched date range)")

if __name__ == "__main__":
    scrape_bonos_tgn_pdfs(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2025, 4, 14)
    )

