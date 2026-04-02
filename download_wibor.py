from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
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
    
    url = f"https://stooq.pl/q/d/?s={ticker}"
    print(f"  URL: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    
    # Screenshot do debugowania
    screenshot_path = os.path.join(download_dir, f"{ticker}_screenshot.png")
    page.screenshot(path=screenshot_path)
    print(f"  Screenshot: {screenshot_path}")
    
    # Sprawdź czy strona się załadowała
    page_content = page.content()
    if "Pobierz dane" in page_content:
        print("  Znaleziono 'Pobierz dane' w HTML")
    else:
        print("  NIE znaleziono 'Pobierz dane' w HTML")
        print(f"  Długość HTML: {len(page_content)} znaków")
    
    # Spróbuj różnych selektorów
    selectors = [
        'a:has-text("Pobierz dane")',
        'a[href*="/q/d/l/"]',
        'text=Pobierz dane w pliku csv',
        'a:has-text("csv")',
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector)
            count = element.count()
            print(f"  Selektor '{selector}': {count} elementów")
            if count > 0:
                with page.expect_download(timeout=30000) as download_info:
                    element.first.click()
                download = download_info.value
                filepath = os.path.join(download_dir, f"{ticker}.csv")
                download.save_as(filepath)
                print(f"  Zapisano: {filepath}")
                return filepath
        except Exception as e:
            print(f"  Selektor '{selector}' nie zadziałał: {e}")
            continue
    
    raise Exception("Żaden selektor nie zadziałał")

def merge_csv_files(download_dir, output_file):
    """Łączy wszystkie CSV w jeden plik z kolumną Ticker"""
    all_rows = []
    
    for ticker, name in TICKERS.items():
        filepath = os.path.join(download_dir, f"{ticker}.csv")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 5:
                        all_rows.append({
                            'Data': row[0],
                            'Otwarcie': row[1],
                            'Najwyższy': row[2],
                            'Najniższy': row[3],
                            'Zamknięcie': row[4],
                            'Ticker': name
                        })
            print(f"  {name}: {sum(1 for r in all_rows if r['Ticker'] == name)} wierszy")
    
    all_rows.sort(key=lambda x: (x['Data'], x['Ticker']), reverse=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Otwarcie', 'Najwyższy', 'Najniższy', 'Zamknięcie', 'Ticker'])
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\nŁącznie wierszy: {len(all_rows)}")

def main():
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL"
        )
        page = context.new_page()
        
        # Wejdź na stronę główną
        print("Wchodzę na stronę główną Stooq...")
        page.goto("https://stooq.pl/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        
        # Screenshot strony głównej
        page.screenshot(path=os.path.join(download_dir, "main_page.png"))
        print("Screenshot strony głównej zapisany")
        
        for ticker, name in TICKERS.items():
            try:
                download_single_ticker(page, ticker, name, download_dir)
            except Exception as e:
                print(f"  Błąd przy {ticker}: {e}")
        
        browser.close()
    
    merge_csv_files(download_dir, "wibor_all.csv")
    
    with open("last_update.txt", "w") as f:
        warsaw_time = datetime.now(ZoneInfo("Europe/Warsaw"))
        f.write(warsaw_time.strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()
