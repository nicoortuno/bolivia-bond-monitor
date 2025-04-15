import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime

PDF_FOLDER = "../data/pdfs/tgn_bonos"
OUTPUT_CSV = "../data/bonos_tgn_auctions.csv"

def extract_date_from_filename(filename):
    match = re.search(r"BT_(\d{4})_(\d{2})_(\d{2})\.pdf", filename)
    if match:
        year, month, day = map(int, match.groups())
        return datetime(year, month, day)
    return None

def extract_data_from_text(text, filename, date):
    results = []

    try:
        clean = lambda s: float(s.replace(".", "").replace(",", "."))

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        motivo = None
        if "DPM" in text:
            motivo = "DPM"
        elif "DPF" in text:
            motivo = "DPF"

        for i, line in enumerate(lines):
            if "Plazo" in line and "días" in line:
                plazo_match = re.search(r"Plazo:\s*(\d+)", line)
                plazo = int(plazo_match.group(1)) if plazo_match else None

                for j in range(i + 1, min(i + 10, len(lines))):
                    if re.match(r"^\s*\d+\)", lines[j]):
                        cleaned_line = re.sub(r"^\s*\d+\)\s*", "", lines[j])
                        numbers = re.findall(r"[\d\.,]+", cleaned_line)

                        if len(numbers) >= 3:
                            row = {
                            "filename": filename,
                            "date": date,
                            "plazo_dias": plazo,
                            "cantidad_demandada": clean(numbers[0]),
                            "cantidad_adjudicada": clean(numbers[2]),
                            "tre": clean(numbers[1]),
                            "motivo_rechazo": motivo
                        }
                            results.append(row)
                        break  

    except Exception as e:
        print(f"❌ Error parsing: {filename} — {e}")

    return results

def extract_data_from_pdf(pdf_path):
    filename = os.path.basename(pdf_path)
    auction_date = extract_date_from_filename(filename)
    data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""

            data = extract_data_from_text(full_text, filename, auction_date)

    except Exception as e:
        print(f"❌ Failed to process {filename}: {e}")

    return data

def run_extraction():
    print("🔍 Extracting BONOS TGN auction data...")
    all_rows = []

    for file in os.listdir(PDF_FOLDER):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(PDF_FOLDER, file)
            rows = extract_data_from_pdf(pdf_path)
            all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    df.sort_values(["date", "plazo_dias"], inplace=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Extraction complete! Data saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    run_extraction()
