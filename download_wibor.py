from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
import os

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
        
        # KROK 1: Strona główna
        print("KROK 1: Wchodzę na stronę główną Stooq...")
        page.goto("https://stooq.pl/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        
        # KROK 2: Strona PLOPLN1M
        print("KROK 2: Wchodzę na stronę PLOPLN1M...")
        page.goto("https://stooq.pl/q/?s=plopln1m", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        
        # KROK 3: Dane historyczne
        print("KROK 3: Klikam Dane historyczne...")
        page.click('a:has-text("Dane historyczne")')
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(download_dir, "01_dane_hist_gora.png"))
        
        # KROK 4: Przewiń stronę do linku "Pobierz dane"
        print("KROK 4: Szukam i przewijam do linku Pobierz dane...")
        
        download_link = page.locator('a:has-text("Pobierz dane")')
        if download_link.count() > 0:
            print(f"  Znaleziono {download_link.count()} linków 'Pobierz dane'")
            
            # Przewiń do elementu
            download_link.first.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
            
            page.screenshot(path=os.path.join(download_dir, "02_po_przewinieciu.png"))
            print("  Screenshot po przewinięciu: 02_po_przewinieciu.png")
            
            # Sprawdź czy element jest widoczny
            is_visible = download_link.first.is_visible()
            print(f"  Czy link jest widoczny: {is_visible}")
            
            # KROK 5: Pobierz plik
            print("KROK 5: Próbuję pobrać plik...")
            try:
                with page.expect_download(timeout=60000) as download_info:
                    download_link.first.click()
                
                download = download_info.value
                filepath = os.path.join(download_dir, "plopln1m.csv")
                download.save_as(filepath)
                print(f"  SUKCES! Zapisano: {filepath}")
                
                # Sprawdź zawartość
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:5]
                    print(f"  Pierwsze linie pliku:")
                    for line in lines:
                        print(f"    {line.strip()}")
                        
            except Exception as e:
                print(f"  Błąd pobierania: {e}")
                page.screenshot(path=os.path.join(download_dir, "03_blad.png"))
        else:
            print("  Nie znaleziono linku 'Pobierz dane'!")
            # Przewiń do końca strony i zrób screenshot
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(download_dir, "02_dol_strony.png"))
        
        browser.close()
    
    with open("last_update.txt", "w") as f:
        warsaw_time = datetime.now(ZoneInfo("Europe/Warsaw"))
        f.write(warsaw_time.strftime("%Y-%m-%d %H:%M:%S"))
    
    print("\nZakończono test.")

if __name__ == "__main__":
    main()
