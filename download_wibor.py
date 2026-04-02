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
        
        # KROK 1: Strona główna Stooq
        print("KROK 1: Wchodzę na stronę główną Stooq...")
        page.goto("https://stooq.pl/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(download_dir, "01_strona_glowna.png"))
        print("  Screenshot: 01_strona_glowna.png")
        
        # KROK 2: Kliknij na link do WIBOR/WIBID/POLSTR/WIRON
        print("KROK 2: Szukam linku do WIBOR WIBID POLSTR WIRON...")
        
        # Szukaj linku - może być w różnych miejscach
        wibor_link_selectors = [
            'a:has-text("WIBOR")',
            'a:has-text("WIBID")',
            'a[href*="t=2"]',  # kategoria stóp procentowych
            'a[href*="wibor"]',
        ]
        
        clicked = False
        for selector in wibor_link_selectors:
            try:
                links = page.locator(selector).all()
                print(f"  Selektor '{selector}': {len(links)} elementów")
                for link in links:
                    text = link.inner_text()
                    href = link.get_attribute("href") or ""
                    print(f"    - text='{text[:50]}' href='{href}'")
                    if "WIBOR" in text or "WIBID" in text:
                        link.click()
                        clicked = True
                        break
                if clicked:
                    break
            except Exception as e:
                print(f"  Błąd przy selektorze {selector}: {e}")
                continue
        
        if not clicked:
            # Alternatywnie - szukaj w menu/kategoriach
            print("  Szukam w menu kategorii...")
            page.screenshot(path=os.path.join(download_dir, "02_przed_kliknieciem.png"))
            
            # Spróbuj bezpośrednio wejść na stronę kategorii stóp procentowych
            print("  Wchodzę bezpośrednio na stronę stóp procentowych...")
            page.goto("https://stooq.pl/t/?i=513", wait_until="domcontentloaded", timeout=60000)
        
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(download_dir, "02_strona_wibor.png"))
        print("  Screenshot: 02_strona_wibor.png")
        
        # KROK 3: Kliknij na PLOPLN1M
        print("KROK 3: Szukam linku do PLOPLN1M...")
        
        plopln1m_selectors = [
            'a:has-text("PLOPLN1M")',
            'a:has-text("WIBOR PLN 1M")',
            'a[href*="plopln1m"]',
        ]
        
        clicked = False
        for selector in plopln1m_selectors:
            try:
                link = page.locator(selector).first
                if link.count() > 0:
                    text = link.inner_text()
                    href = link.get_attribute("href") or ""
                    print(f"  Znaleziono: text='{text}' href='{href}'")
                    link.click()
                    clicked = True
                    break
            except Exception as e:
                print(f"  Błąd przy selektorze {selector}: {e}")
                continue
        
        if not clicked:
            print("  Nie znaleziono linku PLOPLN1M, wchodzę bezpośrednio...")
            page.goto("https://stooq.pl/q/?s=plopln1m", wait_until="domcontentloaded", timeout=60000)
        
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(download_dir, "03_strona_plopln1m.png"))
        print("  Screenshot: 03_strona_plopln1m.png")
        
        # KROK 4: Kliknij na "Dane historyczne"
        print("KROK 4: Szukam linku do Danych historycznych...")
        
        hist_selectors = [
            'a:has-text("Dane historyczne")',
            'a:has-text("historyczne")',
            'a[href*="/q/d/"]',
        ]
        
        clicked = False
        for selector in hist_selectors:
            try:
                link = page.locator(selector).first
                if link.count() > 0:
                    text = link.inner_text()
                    href = link.get_attribute("href") or ""
                    print(f"  Znaleziono: text='{text}' href='{href}'")
                    link.click()
                    clicked = True
                    break
            except Exception as e:
                print(f"  Błąd przy selektorze {selector}: {e}")
                continue
        
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(download_dir, "04_dane_historyczne.png"))
        print("  Screenshot: 04_dane_historyczne.png")
        
        # KROK 5: Szukaj przycisku "Pobierz dane"
        print("KROK 5: Szukam przycisku Pobierz dane...")
        
        download_selectors = [
            'a:has-text("Pobierz dane")',
            'a[href*="q/d/l/"]',
        ]
        
        for selector in download_selectors:
            try:
                link = page.locator(selector).first
                if link.count() > 0:
                    href = link.get_attribute("href") or ""
                    text = link.inner_text()
                    print(f"  Znaleziono link: text='{text}' href='{href}'")
            except:
                pass
        
        # Spróbuj pobrać
        print("KROK 6: Próbuję pobrać plik...")
        try:
            with page.expect_download(timeout=60000) as download_info:
                page.click('a:has-text("Pobierz dane")')
            
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
            page.screenshot(path=os.path.join(download_dir, "05_blad.png"))
        
        browser.close()
    
    # Zapisz timestamp
    with open("last_update.txt", "w") as f:
        warsaw_time = datetime.now(ZoneInfo("Europe/Warsaw"))
        f.write(warsaw_time.strftime("%Y-%m-%d %H:%M:%S"))
    
    print("\nZakończono test.")

if __name__ == "__main__":
    main()
