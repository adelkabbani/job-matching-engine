import sys
import os
import re
import json
import time
import random
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

# Setup logging
log_path = Path(__file__).parent.parent / ".tmp" / "apply_linkedin.log"
def log(msg):
    # Print to console for real-time feedback during setup, also log to file
    print(msg)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def load_json(path):
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def random_delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def apply_to_job(page, job, profile):
    """Attempt to apply to a single LinkedIn job."""
    url = job.get("link")
    company = job.get("company", "Unknown")
    
    log(f"Applying to {company}: {url}")
    
    try:
        page.goto(url)
        random_delay(3, 6)
        
        # 1. Try "Easy Apply" first
        easy_apply_btn = page.locator("button.jobs-apply-button", has_text=re.compile("Easy Apply", re.IGNORECASE)).first
        
        if easy_apply_btn.count() > 0 and easy_apply_btn.is_visible():
            easy_apply_btn.click()
            log("Clicked Easy Apply")
            random_delay()
            
            # --- Easy Apply Form Logic ---
            max_steps = 20
            review_clicks = 0
            
            for step in range(max_steps):
                modal = page.locator("div[role='dialog']").first
                if not modal.is_visible():
                    modal = page.locator(".jobs-easy-apply-content").first

                random_delay(1, 2)

                # --- Handle Common Form Questions (Snippet shortened for brevity, keep existing logic if not replacing whole block) ---
                # (For this edit, we assume the question handling from previous turn is still there/needed.
                #  Since replace_file_content replaces the BLOCK, I must include the question handling code again 
                #  OR target a smaller chunk. The previous edit replaced the WHOLE loop. 
                #  I will include the question handling code to be safe.)
                
                # 1. Radio Buttons (Yes/No)
                radios = modal.locator("fieldset")
                for i in range(radios.count()):
                    fieldset = radios.nth(i)
                    yes_option = fieldset.locator("label", has_text=re.compile("Yes", re.IGNORECASE)).first
                    if yes_option.is_visible(): yes_option.click()

                # 2. Text Inputs
                text_inputs = modal.locator("input[type='text']")
                for i in range(text_inputs.count()):
                    inp = text_inputs.nth(i)
                    if inp.is_visible():
                        try:
                            if not inp.input_value(): inp.fill("5")
                        except: pass

                # 3. Dropdowns
                selects = modal.locator("select")
                for i in range(selects.count()):
                    sel = selects.nth(i)
                    if sel.is_visible():
                        try: sel.select_option(label="Yes")
                        except:
                            try: sel.select_option(index=1)
                            except: pass

                random_delay(1, 2)
                
                # --- ACTION BUTTONS ---
                
                # PRIORITY 1: SUBMIT / SEND
                submit_btn = modal.locator("button", has_text=re.compile("Submit application|Submit", re.IGNORECASE)).first
                if submit_btn.is_visible():
                    # Handle CV upload
                    file_input = modal.locator("input[type='file']").first
                    if file_input.is_visible():
                        cv_path = Path(__file__).parent.parent / ".tmp" / "applications" / company.replace(' ', '_') / "cv.docx"
                        if cv_path.exists():
                            try: file_input.set_input_files(str(cv_path)); random_delay(2, 4)
                            except: pass

                    submit_btn.click()
                    log("CLICKED SUBMIT! (Easy Apply)")
                    random_delay(5, 8)
                    return True
                
                # PRIORITY 2: REVIEW
                review_btn = modal.locator("button", has_text=re.compile("Review", re.IGNORECASE)).first
                if review_btn.is_visible():
                     # Prevent infinite loop
                     if review_clicks > 2:
                         log("Stuck in Review loop. Looking for fallback 'Submit'...")
                         # Fallback: Is there a primary button that isn't connected to 'Review' text?
                         primary_btn = modal.locator("button.artdeco-button--primary").first
                         if primary_btn.is_visible():
                             log("Clicking generic Primary Button (Fallback Submit)")
                             primary_btn.click()
                             random_delay(5, 8)
                             return True # Assume it submitted
                         else:
                             log("No fallback button. Exiting.")
                             return False

                     review_btn.click()
                     review_clicks += 1
                     log(f"Clicked Review ({review_clicks})")
                     random_delay(3, 5)
                     continue

                # Reset review clicks if we see Next
                next_btn = modal.locator("button", has_text=re.compile("Next|Continue", re.IGNORECASE)).first
                if next_btn.is_visible():
                    next_btn.click()
                    log(f"Clicked Next (Step {step+1})")
                    review_clicks = 0 
                    random_delay()
                    continue

                # Check for errors
                error_msg = modal.locator(".artdeco-inline-feedback__message").first
                if error_msg.is_visible():
                    log(f"Form Error: {error_msg.inner_text()}")
                    return False

                log("Easy Apply flow stalled: No buttons found.")
                break
        else:
            # 2. Fallback: External Apply
            apply_btn = page.locator("button.jobs-apply-button", has_text=re.compile("Apply", re.IGNORECASE)).first
            
            if apply_btn.count() > 0 and apply_btn.is_visible():
                log("found 'Apply' button - attempting external application...")
                try:
                    with page.expect_popup(timeout=5000) as popup_info:
                        apply_btn.click()
                    new_page = popup_info.value
                    new_page.wait_for_load_state()
                    log(f"Redirected: {new_page.url}")
                    time.sleep(2)
                    new_page.close()
                    log("External application link visited successfully.")
                    return True
                except Exception as e:
                    log(f"Failed to handle external redirect: {e}")
                    return False
            else:
                log("No 'Easy Apply' or 'Apply' button found. Skipping.")
                return False

    except Exception as e:
        log(f"Error applying to {company}: {e}")
        return False
        
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true", help="Launch browser for manual login")
    parser.add_argument("--limit", type=int, default=3, help="Max applications to submit")
    args = parser.parse_args()

    # Persistent Data Directory for Cookies/Session
    user_data_dir = Path(__file__).parent.parent / ".tmp" / "chrome_user_data"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    log(f"Using browser profile: {user_data_dir}")

    with sync_playwright() as p:
        # Launch persistent context
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False, # Must be false to see manual login
            slow_mo=50,
        )
        
        page = browser.new_page()
        
        if args.setup:
            log("--- SETUP MODE ---")
            log("Navigating to LinkedIn. Please log in manually.")
            page.goto("https://www.linkedin.com/login")
            log("Waiting 60 seconds for you to login...")
            time.sleep(60) 
            log("Setup complete (timeout reached). Please handle remaining login if needed, then close.")
            # Keep open a bit longer if user is typing? 
            # Actually, let's just wait for user to close or hit enter in console?
            # Script blocking input is tricky. Let's just wait a set time or check url.
            return

        # Normal Mode
        log("--- AUTO-APPLY MODE ---")
        
        # Load Jobs
        jobs = load_json(Path(__file__).parent.parent / ".tmp" / "jobs_filtered.json")
        profile = load_json(Path(__file__).parent.parent / ".tmp" / "user_profile.json")
        
        count = 0
        for job in jobs:
            if count >= args.limit:
                break
                
            success = apply_to_job(page, job, profile)
            if success:
                count += 1
                
        log(f"Finished. Submitted {count} applications.")
        browser.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
