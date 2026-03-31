from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
import os

TICKERS = {
    'plopln1m': 'WIBOR_1M',
    'plopln3m': 'WIBOR_3M',
    'plopln6m': 'WIBOR_6M',
    'ploplnon': 'WIBOR_ON',
    'plbplnon': 'WIBID_ON'
}

def download_single_ticker(page, ticker, name, download_dir):
    """Pobiera CSV dla jednego tickera"""
    print(f"Pobieram {name} ({ticker})...")
    
    # Wejdź na stronę danych historycznych
    page.goto(f"https://stooq.pl/q/d/?s={ticker}", wait_until="networkidle")
    
    # Poczekaj na załadowanie
    page.wait_for_timeout(2000)
    
    # Znajdź i kliknij link do pobrania CSV
    with page.expect_download() as download_info:
        # Kliknij link "Pobierz dane w pliku csv"
        page.click('a[href*="/q/d/l/"]')
    
    download = download_info.value
    filepath = os.path.join(download_dir, f"{ticker}.csv")
    download.save_as(filepath)
    print(f"  Zapisano: {filepath}")
    return filepath

def merge_csv_files(download_dir, output_file):
    """Łączy wszystkie CSV w jeden plik z kolumną Ticker"""
    all_rows = []
    
    for ticker, name in TICKERS.items():
        filepath = os.path.join(download_dir, f"{ticker}.csv")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Pomiń nagłówek
                for row in reader:
                    if len(row) >= 5:
                        all_rows.append({
                            'Date': row[0],
                            'Open': row[1],
                            'High': row[2],
                            'Low': row[3],
                            'Close': row[4],
                            'Ticker': name
                        })
    
    # Sortuj po dacie i tickerze
    all_rows.sort(key=lambda x: (x['Date'], x['Ticker']), reverse=True)
    
    # Zapisz połączony plik
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Open', 'High', 'Low', 'Close', 'Ticker'])
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\nPołączono dane do: {output_file}")
    print(f"Łącznie wierszy: {len(all_rows)}")

def main():
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        # Uruchom przeglądarkę
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        # Pobierz dane dla każdego tickera
        for ticker, name in TICKERS.items():
            try:
                download_single_ticker(page, ticker, name, download_dir)
            except Exception as e:
                print(f"  Błąd przy {ticker}: {e}")
        
        browser.close()
    
    # Połącz wszystkie pliki
    merge_csv_files(download_dir, "wibor_all.csv")
    
    # Dodaj timestamp
    with open("last_update.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))

if __name__ == "__main__":
    main()
