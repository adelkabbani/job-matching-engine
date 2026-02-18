from playwright.sync_api import sync_playwright
import time
import os
from pathlib import Path

# Config
BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".tmp" / "chrome_user_data_german"

def login_arbeitsagentur():
    """
    Launches a browser for the user to login to Arbeitsagentur.de.
    Saves the session state (cookies/storage) for future headless runs.
    """
    print("🚀 Launching Browser for Arbeitsagentur Login...")
    print("👉 Please log in manually. The script will wait.")
    
    with sync_playwright() as p:
        # Use persistent context to save login state
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False, # Must be visible for manual login
            args=["--start-maximized"],
            viewport=None
        )
        
        page = browser.new_page()
        
        # Go to login page
        page.goto("https://www.arbeitsagentur.de/eservices-esuche/j/index.jsf")
        
        print("\n⏳ Waiting for you to log in...")
        print("Please navigate to 'Jobbörse' -> 'Meine Vormerkungen' after login.")
        print("Press CTRL+C in the terminal when you are done and want to close.")
        
        try:
            # Keep browser open until user is done
            # In a real app we might check for a specific selector like "Logout"
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n✅ Session captured! Closing browser.")
            browser.close()

if __name__ == "__main__":
    login_arbeitsagentur()
