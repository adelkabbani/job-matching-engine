"""
LinkedIn Assistant Service.
Uses Playwright to interact with an active LinkedIn session in the user's browser.
Ensures human-in-the-loop for safety and security.
"""
import asyncio
import os
import random
import time
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, BrowserContext, Page
from playwright_stealth import Stealth
from thefuzz import process
from utils.encryption import encrypt_value, decrypt_value
from services.job_matcher import get_user_skills, extract_skills_from_description, generate_match_report
from services.job_scraper import apply_filters

# Global variables for browser management
_browser_context: Optional[BrowserContext] = None
_playwright = None
_stop_requested = False

# Rate limiting state
_actions_this_minute = 0
_last_action_timestamp = 0
_applies_today = 0
_last_reset_date = ""

# Constants
USER_DATA_DIR = os.path.join(os.getcwd(), ".linkedin_session")
LINKEDIN_SEARCH_URL = "https://www.linkedin.com/jobs/search/"
LOGS_DIR = os.path.join(os.getcwd(), ".tmp", "logs", "applications")

# Sensitive fields that require human intervention
SENSITIVE_KEYWORDS = ["salary", "compensation", "visa", "work authorization", "relocation", "notice period", "citizenship"]

async def launch_linkedin_browser():
    """
    Launch a visible browser window with a persistent profile.
    This allows the user to log in once and stay logged in.
    """
    global _browser_context, _playwright
    
    if _browser_context:
        print("🔗 LinkedIn browser already running.")
        return True

    _playwright = await async_playwright().start()
    
    proxy_server = os.getenv("LINKEDIN_PROXY_SERVER")
    context_args = {
        "user_data_dir": USER_DATA_DIR,
        "headless": False,  # Must be visible for "Assisted" automation
        "args": ["--start-maximized", "--disable-blink-features=AutomationControlled"],
        "no_viewport": True
    }
    
    if proxy_server:
        context_args["proxy"] = {
            "server": proxy_server,
            "username": os.getenv("LINKEDIN_PROXY_USER", ""),
            "password": os.getenv("LINKEDIN_PROXY_PASS", "")
        }
        print("🛡️ Residential proxy configured.")

    # Using persistent context to save cookies/session
    _browser_context = await _playwright.chromium.launch_persistent_context(**context_args)
    
    # Open LinkedIn as initial page
    page = await _browser_context.new_page()
    await Stealth().apply_stealth_async(page)
    await page.goto("https://www.linkedin.com/login")
    
    print(f"🚀 LinkedIn Assistant launched. Profile saved in: {USER_DATA_DIR}")
    return True

async def stop_linkedin_browser():
    """Close the browser and cleanup."""
    global _browser_context, _playwright, _stop_requested
    _stop_requested = True
    if _browser_context:
        await _browser_context.close()
        _browser_context = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
    print("🛑 LinkedIn Assistant stopped.")

def request_stop():
    global _stop_requested
    _stop_requested = True
    print("⛔ Stop requested by user.")

async def _check_stop():
    global _stop_requested
    if _stop_requested:
        raise InterruptedError("Automation stopped by user.")

async def _rate_limit_check():
    global _actions_this_minute, _last_action_timestamp, _applies_today, _last_reset_date
    now = time.time()
    today = time.strftime("%Y-%m-%d")
    
    # 1. Daily Reset
    if today != _last_reset_date:
        _applies_today = 0
        _last_reset_date = today
        
    # 2. Max applies per day (Safety limit: 50)
    if _applies_today >= 50:
        raise Exception("Daily application limit reached (50). Please continue manually.")
        
    # 3. Minute limit (Throttle: 12 actions/min)
    if now - _last_action_timestamp < 60:
        if _actions_this_minute >= 12:
            wait_time = 60 - (now - _last_action_timestamp)
            print(f"⏳ Throttling: Waiting {wait_time:.2f}s...")
            await asyncio.sleep(wait_time)
            _actions_this_minute = 0
            _last_action_timestamp = time.time()
    else:
        _actions_this_minute = 0
        _last_action_timestamp = now
        
    _actions_this_minute += 1

async def capture_current_search_results(user_id: str, supabase) -> Dict:
    """
    Scrapes jobs from the current active LinkedIn Search tab.
    """
    global _browser_context
    
    debug_log_path = os.path.join(os.getcwd(), "linkedin_capture_debug.log")
    
    def log(msg):
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
        print(msg)

    log(f"\n--- Starting Capture for User {user_id} ---")
    
    if not _browser_context:
        log("❌ Error: Browser not launched. Call launch first.")
        return {"status": "error", "message": "Browser not launched. Call launch first."}

    # Find the tab that is on LinkedIn Search
    pages = _browser_context.pages
    log(f"📄 Number of open pages: {len(pages)}")
    target_page = None
    for p in pages:
        log(f"🔗 Checking page: {p.url}")
        if "linkedin.com/jobs/search" in p.url or "linkedin.com/jobs/collections" in p.url:
            target_page = p
            break
    
    if not target_page:
        log("❌ Error: No active LinkedIn search tab found.")
        return {"status": "error", "message": "No active LinkedIn search tab found. Please navigate to a job search first."}

    print(f"🕵️ Analyzing search results on: {target_page.url}")
    
    # 1. Capture basic job list items
    # Hyper-Robust Heuristic Engine
    jobs = await target_page.evaluate('''() => {
        // Multi-strategy card detection
        let jobCards = document.querySelectorAll('.job-card-container, .jobs-search-results-list__list-item, [role="button"][class*="_"], [data-job-id]');
        
        // Filter out non-job cards if we found too many generic button roles
        if (jobCards.length > 50) {
            jobCards = Array.from(jobCards).filter(c => c.innerText.includes('\\n') && (c.innerText.includes('Easy Apply') || c.querySelector('a')));
        }
        
        const results = [];
        
        jobCards.forEach(card => {
            let title = '', company = '', location = '', url = '', isEasyApply = false;

            // Strategy A: Standard Selectors
            const titleEl = card.querySelector('.job-card-list__title--link, .job-card-list__title, .artdeco-entity-lockup__title a, a[href*="/jobs/view/"] h2');
            const companyEl = card.querySelector('.job-card-container__primary-description, .job-card-container__company-name, .artdeco-entity-lockup__subtitle, .job-card-list__company-name');
            const locationEl = card.querySelector('.job-card-container__metadata-item, .artdeco-entity-lockup__caption, .job-card-container__metadata-wrapper li');
            const linkEl = card.querySelector('a[href*="/jobs/view/"]');
            
            // Link is critical for Job ID
            if (linkEl) {
                url = linkEl.href.split('?')[0];
            }

            // Field Parsing with Fallback to Heuristic
            if (titleEl) title = titleEl.innerText.trim();
            if (companyEl) company = companyEl.innerText.trim();
            if (locationEl) location = locationEl.innerText.trim();

            // Heuristic Fallback (Split Text)
            // LinkedIn cards often have: [Line 0: Title, Line 1: Company, Line 2: Location]
            if (!title || !company) {
                const lines = card.innerText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                if (lines.length >= 2) {
                    if (!title) title = lines[0];
                    if (!company) company = lines[1];
                    if (!location && lines[2]) location = lines[2];
                }
            }

            // Easy Apply Detection
            isEasyApply = card.innerText.includes('Easy Apply') || 
                          !!card.querySelector('.job-card-container__apply-method, .jobs-search-results-list__easy-apply-indicator, .job-card-list__footer-item--emphasis');

            if (title && url) {
                results.push({
                    title,
                    company: company || 'Unknown',
                    location: location || 'Remote',
                    url,
                    is_easy_apply: isEasyApply
                });
            }
        });
        return results;
    }''')

    if not jobs:
        log("⚠️ No jobs found by JS evaluation on this page.")
        # Diagnostic: check how many potential cards were seen at all
        card_count = await target_page.evaluate('() => document.querySelectorAll(".job-card-container, .jobs-search-results-list__list-item, [role=\\"button\\"][class*=\\"_\\"], [data-job-id]").length')
        log(f"🔍 Diagnostic: Selector count found {card_count} potential cards but failed to parse details.")
        # Log the first 500 chars of innerText of the first card if found
        first_card_text = await target_page.evaluate('() => { const c = document.querySelector(".job-card-container, .jobs-search-results-list__list-item, [role=\\"button\\"][class*=\\"_\\"], [data-job-id]"); return c ? c.innerText.substring(0, 300) : "NONE"; }')
        log(f"🔍 Sample Card Text: {first_card_text}")
        log(f"📄 Page Title: {await target_page.title()}")
        return {"status": "success", "count": 0, "message": "No jobs found on this page. Please ensure you are looking at the job list."}

    log(f"✅ Found {len(jobs)} jobs on page using heuristic engine. Processing...")
    # For MVP, we'll try to get descriptions if the user has clicked them or we can fetch them
    # For now, we'll just ingest them. In Track B, we can navigate to each URL if needed.
    
    user_skills = get_user_skills(supabase, user_id)
    filters_res = supabase.table("job_filters").select("*").eq("user_id", user_id).single().execute()
    user_filters = filters_res.data
    
    new_count = 0
    for job in jobs:
        # Check uniqueness - Correct column name is job_url
        log(f"🧐 Checking uniqueness for: {job['url']}")
        try:
            existing = supabase.table("jobs").select("id").eq("user_id", user_id).eq("job_url", job['url']).execute()
            if existing.data:
                log(f"⏭️ Skipping duplicate: {job['url']}")
                continue
        except Exception as e:
            log(f"❌ Error checking uniqueness: {e}")
            continue
            
        # For a full score, we ideally need the description. 
        # For capture MVP, we'll just save the basic info and the user can click "Score" later, 
        # OR we fetch it now. Let's try to fetch it now for the best UX.
        
        # Note: Fetching descriptions requires a bit of wait/clicking in the browser
        # For simplicity in Phase 1 of Phase 7, we'll just store and use a placeholder/partial if available.
        
        job_record = {
            'user_id': user_id,
            'title': job['title'],
            'company': job['company'],
            'description': "Full description pending... (Click View Job to see more)", 
            'job_url': job['url'],
            'source': 'linkedin_assistant',
            'location': job['location'],
            'is_easy_apply': job['is_easy_apply'],
            'match_score': 0, # Placeholder
            'filtered_out': False,
            'status': 'scraped'
        }
        
        try:
            log(f"📥 Inserting job: {job['title']} (Easy Apply: {job['is_easy_apply']})")
            insert_res = supabase.table("jobs").insert(job_record).execute()
            if insert_res.data:
                new_count += 1
                log(f"✅ Inserted: {job['title']}")
            else:
                log(f"⚠️ Insertion returned no data for: {job['title']}")
        except Exception as e:
            log(f"❌ Error inserting job: {e}")
            
    log(f"🏁 Finished capture. New jobs: {new_count}")

    return {"status": "success", "count": new_count, "jobs": jobs}

async def capture_job_details(job_id: str, user_id: str, supabase) -> Dict:
    """
    Navigates to the job URL, extracts full description, and detects Easy Apply.
    Updates the existing job record in the database.
    """
    global _browser_context
    if not _browser_context:
        return {"status": "error", "message": "Assistant browser not running."}

    # Fetch job URL from DB - Correct column is job_url
    res = supabase.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).single().execute()
    if not res.data:
        return {"status": "error", "message": "Job not found."}
    
    job_url = res.data.get('job_url') or res.data.get('raw_data', {}).get('url')
    if not job_url:
         return {"status": "error", "message": "Job URL not found."}
    
    # 1. Use an existing page or create new one
    page = _browser_context.pages[0] if _browser_context.pages else await _browser_context.new_page()
    
    try:
        print(f"📄 Capturing details for job: {job_url}")
        await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for description to load
        await page.wait_for_selector('.jobs-description', timeout=10000)
        
        # Extract data
        details = await page.evaluate('''() => {
            const descEl = document.querySelector('.jobs-description');
            const easyApplyBtn = document.querySelector('.jobs-apply-button--top-card button[aria-label*="Easy Apply"]');
            
            return {
                description: descEl ? descEl.innerText.trim() : '',
                is_easy_apply: !!easyApplyBtn
            };
        }''')
        
        if not details['description']:
            return {"status": "error", "message": "Could not extract job description."}

        # 2. Recalculate score with full description
        user_skills = get_user_skills(supabase, user_id)
        required_skills, optional_skills = extract_skills_from_description(details['description'])
        match_report = generate_match_report(user_skills, required_skills, optional_skills)
        
        # 3. Update DB
        update_data = {
            "description": details['description'],
            "is_easy_apply": details['is_easy_apply'],
            "match_score": match_report['match_score'],
            "matched_skills": match_report['matched_skills'],
            "missing_skills": match_report['missing_skills'],
            "strengths_summary": match_report['strengths_summary']
        }
        
        supabase.table("jobs").update(update_data).eq("id", job_id).execute()
        
        return {
            "status": "success", 
            "is_easy_apply": details['is_easy_apply'],
            "match_score": match_report['match_score']
        }
        
    except Exception as e:
        print(f"Error capturing job details: {e}")
        return {"status": "error", "message": str(e)}

async def autofill_easy_apply_modal(job_id: str, user_id: str, supabase, dry_run: bool = False) -> Dict:
    print(f"\n🚀 [ASSISTANT] autofill_easy_apply_modal triggered for job: {job_id}")
    """
    Orchestrates the autofill process for a LinkedIn Easy Apply modal.
    - Navigates to job
    - Clicks Easy Apply
    - Fills steps using profile + question bank
    - Stops before final submit
    """
    global _browser_context, _stop_requested, _applies_today
    if not _browser_context:
        print("❌ [ASSISTANT] Browser context is MISSING. Returning error.")
        return {"status": "error", "message": "Assistant browser not running."}

    _stop_requested = False # Reset for new attempt
    
    # 1. Fetch Job and Profile Data
    job_res = supabase.table("jobs").select("*").eq("id", job_id).eq("user_id", user_id).single().execute()
    profile_res = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    
    if not job_res.data or not profile_res.data:
        return {"status": "error", "message": "Job or Profile data missing."}
        
    job = job_res.data
    profile = profile_res.data
    
    page = _browser_context.pages[0] if _browser_context.pages else await _browser_context.new_page()
    
    # Setup log dir
    job_log_dir = os.path.join(LOGS_DIR, str(job_id))
    os.makedirs(job_log_dir, exist_ok=True)
    print(f"📁 [ASSISTANT] Log directory: {job_log_dir}")
    
    try:
        await _rate_limit_check()
        
        # 1.1 Extract basic job info for logic
        job_url = job.get('url') or job.get('raw_data', {}).get('url')
        company_name = job.get("company", "Unknown")
        
        if not job_url:
             print(f"❌ Job URL missing for {job_id}")
             return {"status": "error", "message": "Job URL not found."}

        # 1.2 LinkedIn Domain Check
        if "linkedin.com" not in job_url:
            print(f"❌ Aborting: This is NOT a LinkedIn job. URL: {job_url}")
            return {
                "status": "error", 
                "message": "Assistant currently only supports LinkedIn Easy Apply jobs. This job links to an external site."
            }

        # Apply stealth to the job page
        await Stealth().apply_stealth_async(page)
        
        # DEBUG: Initial Page Load
        await page.screenshot(path=os.path.join(job_log_dir, "0_page_load.png"))
        print(f"📸 Captured initial page load for job {job_id}")

        if page.url != job_url:
            try:
                print(f"🌐 Navigating to job URL: {job_url}")
                await page.goto(job_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)
                await page.screenshot(path=os.path.join(job_log_dir, "0.5_after_navigation.png"))
            except Exception as e:
                print(f"❌ Navigation failed: {e}")
                await page.screenshot(path=os.path.join(job_log_dir, "error_navigation_failed.png"))
                return {"status": "error", "message": f"Failed to navigate to job: {str(e)}"}
        
        await _check_stop()
        
        print(f"🔍 Searching for Easy Apply button...")
        await page.screenshot(path=os.path.join(job_log_dir, "0.6_before_button_check.png"))
        
        # Fallback selectors for Easy Apply button
        selectors = [
            'button[data-view-name="job-apply-button"]', # Highly reliable in recent logs
            '.jobs-apply-button--top-card button[aria-label*="Easy Apply"]',
            '.jobs-apply-button--top-card button:has-text("Easy Apply")',
            'button.jobs-apply-button[aria-label*="Easy Apply"]',
            'button.jobs-apply-button:has-text("Easy Apply")',
            '.jobs-s-apply button[aria-label*="Easy Apply"]',
            '.jobs-s-apply button:has-text("Easy Apply")',
            'button[aria-label*="Apply to"]', # Sometimes it says "Apply to [Company]"
            'button:has-text("Apply")' # Final desperate fallback for any "Apply" button
        ]
        
        easy_apply_btn = None
        for selector in selectors:
            try:
                easy_apply_btn = await page.query_selector(selector)
                if easy_apply_btn:
                    print(f"✅ Found button with selector: {selector}")
                    break
            except: continue

        if not easy_apply_btn:
            # DEBUG: Modal Not Found - Log Source
            print(f"⚠️ Easy Apply button NOT found. Saving page source for debug.")
            await page.screenshot(path=os.path.join(job_log_dir, "error_button_not_found.png"))
            source = await page.content()
            with open(os.path.join(job_log_dir, "page_source.html"), "w", encoding="utf-8") as f:
                f.write(source)

            # Check if modal already open
            modal = await page.query_selector('.jobs-easy-apply-modal')
            if not modal:
                print(f"❌ Easy Apply button or modal NOT found for {company_name}. See page_source.html")
                return {"status": "error", "message": "Easy Apply button not found on page."}
        else:
            print(f"🖱️ Clicking Easy Apply for {company_name}")
            await easy_apply_btn.click()
            await asyncio.sleep(2)
        
        # DEBUG: Check if modal opened
        await page.screenshot(path=os.path.join(job_log_dir, "1_modal_opened.png"))

        # 3. Form Filling Loop (Multi-step)
        max_steps = 10
        current_step = 0
        
        while current_step < max_steps:
            current_step += 1
            await _check_stop()
            await _rate_limit_check()
            
            # Screenshot for step
            await page.screenshot(path=os.path.join(job_log_dir, f"step_{current_step}.png"))
            
            # Detect modal state
            modal = await page.query_selector('.jobs-easy-apply-modal')
            if not modal:
                break # Modal closed or finished
                
            # Snapshot fields BEFORE filling to see what's blank
            blank_fields = await _extract_form_state(page)

            # Check for "Submit application" button (Final Step)
            submit_btn = await page.query_selector('button[aria-label="Submit application"]')
            if submit_btn:
                print("🛑 Final step reached. Clicking submit and verifying...")
                if dry_run:
                    return {"status": "success", "message": "Dry Run: Reached Submit button."}

                await submit_btn.click()
                _applies_today += 1 # Count it as an attempt
                
                try:
                    await page.wait_for_selector('h3:has-text("Application submitted"), .artdeco-modal__header:has-text("Application submitted"), [data-test-modal-id="postApplyModal"]', timeout=8000)
                    print("✅ Application successfully submitted! Logging to tracker.")
                    
                    # CAPTURE SUCCESS PROOF
                    success_path = os.path.join(job_log_dir, "success_proof.png")
                    await page.screenshot(path=success_path)
                    
                    supabase.table("applications").insert({
                        "user_id": user_id,
                        "job_id": job_id,
                        "company": job.get("company", "Unknown"),
                        "role_title": job.get("title", "Unknown"),
                        "status": "applied",
                        "match_score": job.get("match_score", 0),
                        "success_screenshot_path": success_path
                    }).execute()
                    
                    supabase.table("jobs").update({"status": "applied"}).eq("id", job_id).execute()
                    
                    close_btn = await page.query_selector('button[aria-label="Dismiss"]')
                    if close_btn: await close_btn.click()
                    
                    return {"status": "success", "message": "Application submitted automatically."}
                except Exception as e:
                    print(f"⚠️ Submission verification timed out: {e}")
                    # Still record as applied but with warning status
                    supabase.table("applications").insert({
                        "user_id": user_id,
                        "job_id": job_id,
                        "company": job.get("company", "Unknown"),
                        "role_title": job.get("title", "Unknown"),
                        "status": "applied",
                        "match_score": job.get("match_score", 0),
                        "success_screenshot_path": os.path.join(job_log_dir, f"step_{current_step}.png") # Use last known step
                    }).execute()
                    supabase.table("jobs").update({"status": "applied"}).eq("id", job_id).execute()
                    
                    return {"status": "warning", "message": "Clicked Submit, but verification timed out. Record saved anyway."}
            
            # Fill current step's fields
            current_state_before = await _extract_form_state(page)
            skipped_fields = await _fill_modal_fields(page, profile, supabase, user_id, job)
            
            if dry_run:
                return {"status": "success", "message": f"Dry Run: Fields filled. Skipped: {', '.join(skipped_fields) if skipped_fields else 'None'}"}

            # Click Next/Review
            next_btn = await page.query_selector('button[aria-label*="Next"], button[aria-label*="Review"]')
            if next_btn:
                # Add randomized delay for human-like behavior
                await asyncio.sleep(random.uniform(2.5, 4.0))
                await next_btn.click()
                await asyncio.sleep(2.0)
                
                # Check for Form Errors -> enter "Learning Mode"
                error_els = await page.query_selector_all('.artdeco-inline-feedback--error')
                if error_els:
                    print(f"⚠️ Form errors detected ({len(error_els)}). Waiting for human to fill fields and click Next...")
                    # Poll until user clicks Next or resolves it
                    waited = 0
                    while waited < 60:
                        temp_state = await _extract_form_state(page)
                        if temp_state:
                            current_state_after = temp_state
                            
                        modal_active = await page.query_selector('.artdeco-inline-feedback--error')
                        if not modal_active:
                            # User fixed the errors!
                            print("✅ Human intervention resolved error. Learning...")
                            await _learn_new_answers(current_state_before, current_state_after, supabase, user_id)
                            break
                        
                        await asyncio.sleep(2)
                        waited += 2
                        
                    if waited >= 60:
                        return {"status": "error", "message": "Timed out waiting for human intervention."}
                    
                    await asyncio.sleep(2.0)
            else:
                # Might be a custom question step or at the end
                break
                
        return {"status": "success", "message": "Assistant finished filling known fields. Please complete any remaining steps."}

    except InterruptedError:
        return {"status": "warning", "message": "Automation stopped by user."}
    except Exception as e:
        print(f"Error during autofill: {e}")
        return {"status": "error", "message": str(e)}

async def _extract_form_state(page: Page) -> Dict[str, str]:
    """Scrapes current visible fields and their values to track human changes."""
    state = {}
    
    # Inputs & Textareas
    inputs = await page.query_selector_all('input[type="text"], input:not([type]), textarea')
    for el in inputs:
        label = await _get_label_for_element(page, el)
        val = await el.input_value()
        if label: state[label] = val
        
    # Dropdowns (select)
    selects = await page.query_selector_all('select')
    for el in selects:
        label = await _get_label_for_element(page, el)
        val = await page.evaluate('(sel) => sel.options[sel.selectedIndex]?.text || ""', el)
        if label: state[label] = val
        
    # Radio buttons
    fieldsets = await page.query_selector_all('fieldset')
    for fs in fieldsets:
        legend = await fs.query_selector('legend')
        if not legend: continue
        label = await legend.inner_text()
        checked = await fs.query_selector('input[type="radio"]:checked')
        if checked:
            radio_id = await checked.get_attribute('id')
            radiolab = await page.query_selector(f'label[for="{radio_id}"]')
            state[label.strip()] = await radiolab.inner_text() if radiolab else "Yes"

    return state

async def _get_label_for_element(page: Page, el) -> str:
    label_id = await el.get_attribute('id')
    if label_id:
        label_el = await page.query_selector(f'label[for="{label_id}"]')
        if label_el: return await label_el.inner_text()
    return (await el.get_attribute('aria-label')) or ""

async def _learn_new_answers(before: Dict[str, str], after: Dict[str, str], supabase, user_id: str):
    """Detects what changed after human intervention and saves it to the Question Bank."""
    for label, new_val in after.items():
        old_val = before.get(label, "")
        if new_val and new_val != old_val:
            print(f"📖 Learning new answer: '{label}' -> '{new_val}'")
            
            # Determine category based on keywords
            cat = 'general'
            l = label.lower()
            if 'salary' in l or 'pay' in l or 'compensation' in l: cat = 'salary'
            elif 'visa' in l or 'sponsor' in l or 'citizen' in l: cat = 'visa'
            elif 'experience' in l or 'years' in l: cat = 'experience'
            
            # Encrypt if sensitive
            save_val = new_val
            if cat in ['salary', 'visa'] or any(kw in l for kw in SENSITIVE_KEYWORDS):
                try:
                    save_val = encrypt_value(save_val)
                    cat = 'sensitive'
                except Exception as e:
                    print(f"Failed to encrypt: {e}. Skipping sensitive data learning.")
                    return
                
            try:
                # Upsert query directly
                supabase.table("linkedin_question_bank").upsert({
                    "user_id": user_id,
                    "question_text": label.strip(),
                    "answer_text": save_val,
                    "category": cat
                }).execute()
            except Exception as e:
                print(f"Failed to save learned answer: {e}")

async def _fill_modal_fields(page: Page, profile: Dict, supabase, user_id: str, job: Dict = None) -> List[str]:
    """Detects and fills form fields in the current modal state."""
    skipped = []
    
    # 1. Fetch Question Bank once
    qb_res = supabase.table("linkedin_question_bank").select("*").eq("user_id", user_id).execute()
    qb_data = qb_res.data or []
    qb_questions = [row['question_text'] for row in qb_data]
    
    def _calc_exp() -> str:
        work_exp = profile.get('work_experience', [])
        years = 0
        if isinstance(work_exp, list) and work_exp:
            try:
                first_job = work_exp[-1]
                if 'start_date' in first_job:
                    start_yr = int(str(first_job['start_date'])[:4])
                    years = max(1, 2026 - start_yr)
            except: pass
        if years == 0:
            skills = profile.get('skills', [])
            years = max(1, len(skills) // 2) if isinstance(skills, list) else 3
        return str(years)

    # Helper to find answer
    def find_answer(label_text: str) -> Optional[str]:
        if not label_text: return None
        # Sensitive Protection
        if any(kw in label_text.lower() for kw in SENSITIVE_KEYWORDS):
            print(f"⚠️ Sensitive field detected: '{label_text}'. Skipping to force human review.")
            skipped.append(label_text)
            return None
            
        ans = _map_label_to_value(label_text, profile)
        
        # FUZZY MATCHING
        if not ans and qb_questions:
            best_match, score = process.extractOne(label_text, qb_questions)
            if score > 80:
                row = next((r for r in qb_data if r['question_text'] == best_match), None)
                if row:
                    print(f"🧠 Fuzzy match: '{label_text}' ~ '{best_match}' ({score}%)")
                    ans = row['answer_text']

        # EXP MATH
        if not ans and "years" in label_text.lower() and "experience" in label_text.lower():
            ans = _calc_exp()
            print(f"🧮 Auto-calculated experience: '{label_text}' -> {ans}")

        # GLOBAL DECRYPTION FIX
        if ans and isinstance(ans, str) and ans.startswith("gAAAAA"):
            try:
                decrypted = decrypt_value(ans)
                if decrypted: ans = decrypted
            except Exception as e:
                print(f"Failed to decrypt: {e}")

        return str(ans) if ans is not None else None

    # Handle Text Inputs & Textareas
    inputs = await page.query_selector_all('input[type="text"], input:not([type]), textarea')
    for el in inputs:
        label = await _get_label_for_element(page, el)
        ans = find_answer(label)
        if ans:
            await el.fill(str(ans))
            await asyncio.sleep(random.uniform(0.3, 0.8))

    # Handle Select Dropdowns
    selects = await page.query_selector_all('select')
    for el in selects:
        label = await _get_label_for_element(page, el)
        ans = find_answer(label)
        if ans:
            try:
                await el.select_option(label=ans)
                await asyncio.sleep(0.5)
            except:
                try: 
                    await el.select_option(value=ans)
                    await asyncio.sleep(0.5)
                except: pass

    # Handle Fieldsets (Radio/Checkboxes)
    fieldsets = await page.query_selector_all('fieldset')
    for fs in fieldsets:
        legend = await fs.query_selector('legend')
        if not legend: continue
        label = await legend.inner_text()
        ans = find_answer(label)
        if ans:
            radios = await fs.query_selector_all('input[type="radio"]')
            for r in radios:
                r_id = await r.get_attribute('id')
                if not r_id: continue
                rlab = await page.query_selector(f'label[for="{r_id}"]')
                if rlab:
                    rtext = await rlab.inner_text()
                    if ans.lower() in rtext.lower() or rtext.lower() in ans.lower():
                        await rlab.click()
                        await asyncio.sleep(0.5)
                        break

    # Handle lone checkboxes
    checkboxes = await page.query_selector_all('input[type="checkbox"]')
    for cb in checkboxes:
        cb_id = await cb.get_attribute('id')
        if cb_id:
            cblab = await page.query_selector(f'label[for="{cb_id}"]')
            if cblab:
                ltext = await cblab.inner_text()
                if "terms" in ltext.lower() or "agree" in ltext.lower() or "acknowledge" in ltext.lower():
                    await cblab.click()

    # SMART RESUME SELECTOR
    try:
        file_inputs = await page.query_selector_all('input[type="file"]')
        for el in file_inputs:
            label = await _get_label_for_element(page, el)
            is_resume = False
            if label and ("resume" in label.lower() or "cv" in label.lower()):
                is_resume = True
            
            # fallback based on accept attribute
            if not is_resume:
                accept = await el.get_attribute('accept')
                if accept and ('pdf' in accept.lower() or 'doc' in accept.lower()):
                    is_resume = True

            if is_resume:
                company_name = job.get("company", "Unknown") if job else "Unknown"
                safe_company = "".join([c for c in company_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                
                tailored_cv = os.path.join(os.getcwd(), ".tmp", "applications", safe_company, "tailored_cv.pdf")
                default_cv = os.path.join(os.getcwd(), ".tmp", "default_cv.pdf")
                
                if os.path.exists(tailored_cv):
                    print(f"📄 Found tailored CV for {company_name}")
                    await el.set_input_files(tailored_cv)
                    await asyncio.sleep(1)
                elif os.path.exists(default_cv):
                    print("📄 Using default CV")
                    await el.set_input_files(default_cv)
                    await asyncio.sleep(1)
                else:
                    print("⚠️ No CV found on disk!")
    except Exception as e:
        print(f"Failed to handle file uploads: {e}")

    return list(set(skipped))

def _map_label_to_value(label: str, profile: Dict) -> Optional[str]:
    """Basic mapping of LinkedIn labels to our profile data."""
    l = label.lower()
    if 'phone' in l or 'mobile' in l:
        return profile.get('phone_number')
    if 'email' in l:
        return profile.get('email')
    if 'first name' in l:
        return profile.get('full_name', '').split(' ')[0]
    if 'last name' in l:
        parts = profile.get('full_name', '').split(' ')
        return parts[-1] if len(parts) > 1 else ""
    return None
