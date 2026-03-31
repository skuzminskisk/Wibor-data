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
    url = f"https://stooq.pl/q/d/?s={ticker}"
    print(f"  URL: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    
    # Zamknij popup cookies jeśli istnieje
    try:
        page.click("button:has-text('Akceptuję')", timeout=3000)
        print("  Zaakceptowano cookies")
    except:
        pass
    
    try:
        page.click("button:has-text('Accept')", timeout=2000)
        print("  Accepted cookies")
    except:
        pass
    
    # Poczekaj na załadowanie strony
    page.wait_for_timeout(3000)
    
    # Zrób screenshot do debugowania
    screenshot_path = os.path.join(download_dir, f"{ticker}_screenshot.png")
    page.screenshot(path=screenshot_path)
    print(f"  Screenshot: {screenshot_path}")
    
    # Spróbuj różnych selektorów dla linku pobierania
    download_selectors = [
        'a[href*="/q/d/l/"]',
        'a:has-text("Pobierz dane")',
        'a:has-text("csv")',
        'a:has-text("CSV")',
        'a:has-text("Download")',
        '#d_data a[href*="l"]',
    ]
    
    download_link = None
    for selector in download_selectors:
        try:
            link = page.locator(selector).first
            if link.count() > 0:
                download_link = link
                print(f"  Znaleziono link: {selector}")
                break
        except:
            continue
    
    if download_link is None:
        # Wypisz wszystkie linki na stronie do debugowania
        all_links = page.locator("a").all()
        print(f"  Wszystkie linki na stronie ({len(all_links)}):")
        for i, link in enumerate(all_links[:20]):  # Pierwsze 20
            try:
                href = link.get_attribute("href") or ""
                text = link.inner_text()[:50] if link.inner_text() else ""
                print(f"    {i}: href='{href}' text='{text}'")
            except:
                pass
        raise Exception("Nie znaleziono linku do pobrania CSV")
    
    # Pobierz plik
    with page.expect_download(timeout=30000) as download_info:
        download_link.click()
    
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
            try:
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
                print(f"  {name}: dodano {sum(1 for r in all_rows if r['Ticker'] == name)} wierszy")
            except Exception as e:
                print(f"  Błąd czytania {filepath}: {e}")
    
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
        # Uruchom przeglądarkę z większym oknem
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="pl-PL"
        )
        page = context.new_page()
        
        # Najpierw wejdź na stronę główną (ustaw cookies)
        print("Wchodzę na stronę główną Stooq...")
        page.goto("https://stooq.pl/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        
        # Akceptuj cookies na stronie głównej
        try:
            page.click("button:has-text('Akceptuję')", timeout=3000)
            print("Zaakceptowano cookies na stronie głównej")
        except:
            pass
        
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
