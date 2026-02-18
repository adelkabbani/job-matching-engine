from playwright.sync_api import sync_playwright
from pathlib import Path
import time

# Config
BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".tmp" / "chrome_user_data_german"

def verify_session():
    """
    Verifies if the saved browser session is still logged in.
    """
    print("🕵️ Checking if we are logged in...")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=True, # Headless for verification
            )
            
            page = browser.new_page()
            
            # Navigate to a page that requires login
            # "Meine Vormerkungen" (Saved Jobs) usually requires auth
            target_url = "https://www.arbeitsagentur.de/eservices-esuche/j/index.jsf"
            page.goto(target_url)
            page.wait_for_load_state("networkidle")
            
            # Check for "Abmelden" (Logout) or "Profil" text
            # This confirms we are inside
            content = page.content()
            
            if "Abmelden" in content or "Profil" in content or "Meine Vormerkungen" in content:
                print("✅ SUCCESS: You are logged in!")
                print("   The bot can now scrape your private job recommendations.")
            else:
                print("❌ FAILURE: You are NOT logged in.")
                print("   The session cookie might have expired or wasn't saved.")
                print("   Please run 'python execution/login_arbeitsagentur.py' again.")
                
            browser.close()
            
        except Exception as e:
            print(f"❌ Error checking session: {e}")
            print("make sure you closed the previous Chrome window completely!")

if __name__ == "__main__":
    verify_session()
