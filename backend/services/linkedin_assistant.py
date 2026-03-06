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
from services.llm import autonomous_answer_resolver
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
AI_DECISIONS_LOG = os.path.join(os.getcwd(), "backend", "logs", "ai_decisions.log")

def _log_ai_decision(question: str, answer: str):
    """Log AI decisions for transparency and debugging."""
    os.makedirs(os.path.dirname(AI_DECISIONS_LOG), exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(AI_DECISIONS_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [Q] {question}\n")
        f.write(f"[{timestamp}] [A] {answer}\n")
        f.write("-" * 40 + "\n")

# Sensitive fields that require human intervention
SENSITIVE_KEYWORDS = ["salary", "compensation", "visa", "work authorization", "relocation", "notice period", "citizenship"]

async def dismiss_cookie_banners(page: Page):
    """Proactively dismiss common cookie banners."""
    selectors = [
        'button:has-text("Accept")', 
        'button:has-text("Alle akzeptieren")', 
        'button:has-text("Zustimmen")',
        'button:has-text("Allow all")'
    ]
    for selector in selectors:
        try:
            if await page.is_visible(selector, timeout=2000):
                print(f"🍪 [COOKIE-BUSTER] Dismissing banner: {selector}")
                await page.click(selector)
        except: pass

async def launch_linkedin_browser():
    """
    Launch a visible browser window with a persistent profile.
    This allows the user to log in once and stay logged in.
    """
    print("💓 [HEARTBEAT] launch_linkedin_browser called.")
    global _browser_context, _playwright
    
    if _browser_context:
        print("🔗 LinkedIn browser already running.")
        return True

    _playwright = await async_playwright().start()
    
    # Headless Mode support for "Auto-Pilot"
    headless = os.getenv("HEADLESS_MODE", "FALSE").upper() == "TRUE"
    
    proxy_server = os.getenv("LINKEDIN_PROXY_SERVER")
    context_args = {
        "user_data_dir": USER_DATA_DIR,
        "headless": headless,
        "args": ["--start-maximized", "--disable-blink-features=AutomationControlled"],
        "no_viewport": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
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
    
    # [NEW] Apply stealth to all future pages/tabs automatically
    async def apply_stealth_to_page(p):
        try:
            # Apply standard stealth
            await Stealth().apply_stealth_async(p)
            
            # Additional JS-level stealth overrides
            await p.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            print(f"🛡️ [HEARTBEAT] Hardened Stealth applied to ({p.url[:30]}...)")
        except: pass
    
    _browser_context.on("page", lambda p: asyncio.create_task(apply_stealth_to_page(p)))
    
    # Open LinkedIn as initial page
    page = await _browser_context.new_page()
    await Stealth().apply_stealth_async(page)
    await page.goto("https://www.linkedin.com/login")
    
    print(f"🚀 LinkedIn Assistant launched. Profile saved in: {USER_DATA_DIR}")
    return True

async def navigate_linkedin_to(url: str):
    """
    Directs the active LinkedIn Assistant browser to a specific URL.
    """
    global _browser_context
    if not _browser_context:
        print("❌ Navigate failed: Browser not launched.")
        return False
    
    pages = _browser_context.pages
    if pages:
        page = pages[0]
        print(f"🌐 Navigating backend browser to: {url}")
        await page.goto(url, wait_until="networkidle")
        return True
    return False

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
    global _browser_context
    if not _browser_context:
        return {"status": "error", "message": "Browser not launched."}

    pages = _browser_context.pages
    target_page = next((p for p in pages if "linkedin.com/jobs/search" in p.url), None)
    
    if not target_page:
        return {"status": "error", "message": "No active LinkedIn search tab found. Please stay on the Job Search page."}

    print(f"🕵️ Hybrid Hyper-Resilient Scan starting on: {target_page.url}")

    # Re-enable console mirroring
    target_page.on("console", lambda msg: print(f"  [BROWSER] {msg.text}"))

    # 1. FORCE LOADING (Lazy Load Killer)
    # Strategy: Side-panel scroll + user's Human-Mimic mouse wheel
    await target_page.evaluate('''async () => {
        const listSelectors = ['.jobs-search-results-list', 'div[class*="jobs-search-results-list"]', 'section[aria-label="results"]'];
        let container = listSelectors.map(s => document.querySelector(s)).find(el => !!el);
        if (container) {
            console.log("🖱️ Side-panel container found, scrolling...");
            for (let i = 0; i < 5; i++) {
                container.scrollTop += 1200;
                await new Promise(r => setTimeout(r, 400));
            }
            container.scrollTop = 0;
        }
    }''')
    
    # User's requested Human-Mimic Scrolling
    await target_page.mouse.wheel(0, 4000) # Quick scroll to bottom
    await asyncio.sleep(1)
    await target_page.mouse.wheel(0, -4000) # Scroll back up
    await asyncio.sleep(1)

    # 2. HYBRID EXTRACTION
    jobs = await target_page.evaluate('''() => {
        const results = [];
        const seenUrls = new Set();
        
        // --- Strategy A: Tracking Engine (Stable Components) ---
        const cards = Array.from(document.querySelectorAll('[data-view-name="job-search-job-card"], .job-card-container'));
        cards.forEach(card => {
            try {
                const trackingStr = card.getAttribute('data-view-tracking-scope') || "";
                const idMatch = trackingStr.match(/normalized_jobPosting:(\\d+)/) || 
                               trackingStr.match(/jobPosting:(\\d+)/);
                
                if (idMatch) {
                    const jobId = idMatch[1];
                    const url = `https://www.linkedin.com/jobs/view/${jobId}/`;
                    if (seenUrls.has(url)) return;

                    const titleEl = card.querySelector('p[class*="title"], .job-card-list__title, .artdeco-entity-lockup__title');
                    const companyEl = card.querySelector('p[class*="company"], [class*="company-name"], .artdeco-entity-lockup__subtitle');
                    
                    const title = titleEl ? titleEl.innerText.trim() : card.innerText.split('\\n')[0];
                    const company = companyEl ? companyEl.innerText.trim() : "Unknown";
                    const isEasyApply = card.innerText.includes('Easy Apply');

                    seenUrls.add(url);
                    results.push({ title, company, url, is_easy_apply: isEasyApply, method: "TrackingEngine" });
                }
            } catch (e) {}
        });

        // --- Strategy B: Selector Fallback (User's Link-first logic) ---
        const allLinks = Array.from(document.querySelectorAll('a[href*="/jobs/view/"]'));
        allLinks.forEach(link => {
            const url = link.href.split('?')[0];
            if (seenUrls.has(url)) return;
            
            const card = link.closest('.job-card-container, .jobs-search-results-list__list-item, li');
            if (!card) return;

            const title = link.innerText.trim().split('\\n')[0];
            if (title.length < 5) return; 

            const companySelectors = ['.job-card-container__company-name', '.artdeco-entity-lockup__subtitle', '.job-card-container__primary-description'];
            let company = "Unknown Company";
            for (const s of companySelectors) {
                const el = card.querySelector(s);
                if (el) { company = el.innerText.trim(); break; }
            }

            const isEasyApply = card.innerText.includes('Easy Apply');

            seenUrls.add(url);
            results.push({ title, company, url, is_easy_apply: isEasyApply, method: "LinkFallback" });
        });

        return results;
    }''')

    if not jobs:
        content = await target_page.content()
        with open("debug_capture.html", "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "error", "message": "Still 0 jobs found. See debug_capture.html"}

    # 3. DB INGESTION
    count = 0
    for j in jobs:
        try:
            data = {
                "user_id": user_id,
                "title": j['title'],
                "company": j['company'],
                "job_url": j['url'],
                "status": "scraped",
                "is_easy_apply": j['is_easy_apply'],
                "match_score": 100 
            }
            supabase.table("jobs").upsert(data, on_conflict="job_url").execute()
            count += 1
            print(f"  [DB] Ingested via {j['method']}: {j['title']}")
        except Exception as e:
            print(f"Error saving job: {e}")

    return {"status": "success", "count": count, "message": f"Success! Captured {count} jobs via Hybrid Engine."}

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
    
    # HARDENED: Prevent NoneType crash if raw_data is missing/null
    job_data_obj = res.data or {}
    job_url = job_data_obj.get('job_url') or (job_data_obj.get('raw_data') or {}).get('url')
    
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
    print(f"💓 [HEARTBEAT] Starting auto-apply for job {job_id}")
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
        print(f"❌ [ASSISTANT] Job {job_id} or Profile {user_id} NOT found in DB. Aborting.")
        return {"status": "error", "message": "Job or Profile data missing."}
        
    job = job_res.data
    profile = profile_res.data

    # STRICT GUARD for job record validtiy
    if not job or not job.get('id') and not job.get('job_id'):
        print("⚠️ [ASSISTANT] Aborting: Job record is None or missing ID")
        return {"status": "error", "message": "Job record invalid."}
    
    page = _browser_context.pages[0] if _browser_context.pages else await _browser_context.new_page()
    
    # Setup log dir
    job_log_dir = os.path.join(LOGS_DIR, str(job_id))
    os.makedirs(job_log_dir, exist_ok=True)
    print(f"📁 [ASSISTANT] Log directory: {job_log_dir}")
    
    try:
        await _rate_limit_check()
        
        # 1.1 Extract basic job info for logic
        # HARDENED: Prevent NoneType crash if raw_data is missing/null
        job_url = job.get('job_url') or job.get('url') or (job.get('raw_data') or {}).get('url')
        company_name = job.get("company", "Unknown")
        
        if not job_url:
             print(f"❌ [HEARTBEAT] Job URL missing for {job_id}")
             # Log failure report
             with open(os.path.join(job_log_dir, "failure_report.json"), "w") as f:
                 import json
                 json.dump({"job_id": job_id, "error": "URL missing", "url": None}, f)
             return {"status": "error", "message": "Job URL not found."}
        
        print(f"🌐 [HEARTBEAT] Target URL: {job_url}")

        # 1.2 LinkedIn Domain Check
        if "linkedin.com" not in job_url:
            print(f"❌ Aborting: This is NOT a LinkedIn job. URL: {job_url}")
            return {
                "status": "error", 
                "message": "Assistant currently only supports LinkedIn Easy Apply jobs. This job links to an external site."
            }

        # Apply stealth to the job page
        await Stealth().apply_stealth_async(page)
        await dismiss_cookie_banners(page)
        
        # DEBUG: Initial Page Load
        await page.screenshot(path=os.path.join(job_log_dir, "0_page_load.png"), timeout=60000)
        print(f"📸 Captured initial page load for job {job_id}")

        if page.url != job_url:
            try:
                print(f"🌐 Navigating to job URL: {job_url}")
                await page.goto(job_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)
                await page.screenshot(path=os.path.join(job_log_dir, "0.5_after_navigation.png"), timeout=60000)
            except Exception as e:
                print(f"❌ Navigation failed: {e}")
                await page.screenshot(path=os.path.join(job_log_dir, "error_navigation_failed.png"), timeout=60000)
                return {"status": "error", "message": f"Failed to navigate to job: {str(e)}"}
        
        await _check_stop()
        
        # 2. Check if job is expired/closed before clicking
        closed_selectors = [
            '.jobs-details-top-card__apply-error',
            '.artdeco-inline-feedback--error:has-text("No longer accepting applications")',
            '.jobs-apply-button--top-card:has-text("No longer accepting applications")',
            'div:has-text("No longer accepting applications")'
        ]
        for sel in closed_selectors:
            if await page.query_selector(sel):
                print(f"🛑 [HEARTBEAT] Job is closed for {company_name}. Skipping.")
                return {"status": "error", "message": "Job is no longer accepting applications."}

        print(f"🔍 Searching for Easy Apply button...")
        await page.screenshot(path=os.path.join(job_log_dir, "0.6_before_button_check.png"), timeout=60000)
        
        # Enable Tracing (GUARDED)
        try:
            await _browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)
        except Exception as e:
            print(f"⚠️ [ASSISTANT] Tracing start ignored: {e}")
        
        # Fallback selectors for Easy Apply button
        selectors = [
            'button[data-view-name="job-apply-button"]', 
            '.jobs-apply-button--top-card button[aria-label*="Easy Apply"]',
            '.jobs-apply-button--top-card button:has-text("Easy Apply")',
            'button.jobs-apply-button[aria-label*="Easy Apply"]',
            'button.jobs-apply-button:has-text("Easy Apply")',
            '.jobs-s-apply button[aria-label*="Easy Apply"]',
            '.jobs-s-apply button:has-text("Easy Apply")',
            'button[aria-label*="Apply to"]' # Sometimes it says "Apply to [Company]"
        ]
        
        easy_apply_btn = None
        for selector in selectors:
            try:
                btn = await page.query_selector(selector)
                if btn:
                    # Double check it's not an external button (external buttons usually have an SVG with an arrow)
                    is_external = await page.evaluate('(el) => !!el.querySelector("svg[data-test-icon=\"external-link-small\"]")', btn)
                    if not is_external:
                        easy_apply_btn = btn
                        print(f"✅ Found button with selector: {selector}")
                        break
                    else:
                        print(f"⏭️ Skipping external button: {selector}")
            except: continue

        if not easy_apply_btn:
            # Check if modal already open
            modal = await page.query_selector('.jobs-easy-apply-modal')
            if not modal:
                print(f"❌ [HEARTBEAT] Easy Apply button or modal NOT found for {company_name}")
                # Log failure report
                with open(os.path.join(job_log_dir, "failure_report.json"), "w") as f:
                    import json
                    json.dump({"job_id": job_id, "error": "Button/Modal not found", "url": job_url}, f)
                return {"status": "error", "message": "Easy Apply button not found on page."}
        else:
            print(f"💓 [HEARTBEAT] Found Easy Apply button. Clicking now...")
            print(f"🖱️ Clicking Easy Apply for {company_name}")
            await easy_apply_btn.click()
            await asyncio.sleep(2)
        
        # DEBUG: Check if modal opened
        await page.screenshot(path=os.path.join(job_log_dir, "1_modal_opened.png"), timeout=60000)

        # 3. Form Filling Loop (Multi-step)
        max_steps = 10
        current_step = 0
        
        while current_step < max_steps:
            current_step += 1
            await _check_stop()
            await _rate_limit_check()
            
            # Screenshot for step
            await page.screenshot(path=os.path.join(job_log_dir, f"step_{current_step}.png"), timeout=60000)
            
            # Detect modal state
            modal = await page.query_selector('.jobs-easy-apply-modal')
            if not modal:
                break # Modal closed or finished
                
            # Snapshot fields BEFORE filling to see what's blank
            blank_fields = await _extract_form_state(page)

            # Check for "Submit application" button (Final Step)
            submit_btn = await page.query_selector('button[aria-label="Submit application"]')
            if submit_btn:
                print("💓 [HEARTBEAT] Final step reached. Submit button visible.")
                print("🛑 Final step reached. Clicking submit and verifying...")
                if dry_run:
                    return {"status": "success", "message": "Dry Run: Reached Submit button."}

                await submit_btn.click()
                _applies_today += 1 # Count it as an attempt
                
                try:
                    await page.wait_for_selector('h3:has-text("Application submitted"), .artdeco-modal__header:has-text("Application submitted"), [data-test-modal-id="postApplyModal"]', timeout=8000)
                    print("💓 [HEARTBEAT] Application submitted successfully!")
                    print("✅ Application successfully submitted! Logging to tracker.")
                    
                    # CAPTURE SUCCESS PROOF
                    success_path = os.path.join(job_log_dir, "success_proof.png")
                    await page.screenshot(path=success_path, timeout=60000)
                    
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
                        "success_screenshot_path": os.path.join(job_log_dir, f"step_{current_step}.png"), # Use last known step
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
                
                # Handle form errors automatically — no human polling
                # UNASSISTED MODE: Auto-resolve form errors using LLM
                error_els = await page.query_selector_all('.artdeco-inline-feedback--error')
                if error_els:
                    print(f"⚠️ Form errors detected ({len(error_els)}). Resolving autonomously...")
                    
                    current_form_state = await _extract_form_state(page)
                    for label, val in current_form_state.items():
                        # If a field is empty or has an error (which we check by proximity in a real browser, 
                        # but here we'll just re-fill all visible fields to be safe)
                        ans = autonomous_answer_resolver(label, profile, job)
                        if ans:
                            print(f"🤖 Resolved '{label}' -> {ans}")
                            # Find the specific element
                            input_el = await page.query_selector(f'label:has-text("{label}") + input, input[aria-label*="{label}"]')
                            if input_el:
                                await input_el.fill(ans)
                                await asyncio.sleep(0.5)
                    
                    # Try clicking Next again
                    await next_btn.click()
                    await asyncio.sleep(2.0)
                    
                    # If still errors, we skip this job to avoid infinite loops
                    final_errors = await page.query_selector_all('.artdeco-inline-feedback--error')
                    if final_errors:
                        print("❌ Autonomous resolution failed. Skipping job.")
                        return {"status": "error", "message": "Could not resolve form questions automatically."}
            else:
                # Might be a custom question step or at the end
                break
                
        return {"status": "success", "message": "Assistant completed application automatically."}

    except InterruptedError:
        return {"status": "warning", "message": "Automation stopped by user."}
    except Exception as e:
        print(f"❌ Error during autofill: {e}")
        # Enable tracing for failures
        if _browser_context:
            trace_path = os.path.join(job_log_dir, "trace.zip")
            try:
                await _browser_context.tracing.stop(path=trace_path)
                print(f"🛡️ Trace saved to: {trace_path}")
            except: pass
        return {"status": "error", "message": str(e)}

async def _llm_generate_answer(question: str, profile: Dict, job: Dict = None) -> Optional[str]:
    """
    Use the LLM (OpenRouter) to automatically answer an unknown form question
    based on the user profile and job context. This replaces human polling.
    """
    import requests, os
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip().replace('"', '').replace("'", "")
    if not api_key:
        print("⚠️ No OPENROUTER_API_KEY — cannot auto-generate answer.")
        return None
    
    name = profile.get('full_name', 'the applicant')
    skills = ', '.join(profile.get('skills', [])[:10]) if isinstance(profile.get('skills'), list) else ''
    exp = profile.get('work_experience', [])
    job_title = job.get('title', 'the role') if job else 'the role'
    company = job.get('company', 'the company') if job else 'the company'
    
    prompt = f"""You are filling out a job application form on behalf of {name}.

Applicant profile:
- Skills: {skills}
- Applying for: {job_title} at {company}
- Experience entries: {len(exp) if isinstance(exp, list) else 'unknown'}

Generate a SHORT, professional, and factual answer to this form question:
\"{question}\"

Rules:
- Answer in 1-3 words or a single sentence max.
- For yes/no questions, answer Yes or No.
- For experience years, calculate from profile.
- For visa/work authorization, assume: 'Yes' (legally authorized).
- Do NOT include any explanation, just the answer text."""

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "google/gemini-flash-1.5", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1},
            timeout=15
        )
        if resp.ok:
            return resp.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"LLM answer generation failed: {e}")
    return None

async def _save_to_question_bank(question: str, answer: str, supabase, user_id: str):
    """Persist a new LLM-generated answer to the Question Bank for future use."""
    try:
        supabase.table("linkedin_question_bank").upsert({
            "user_id": user_id,
            "question_text": question.strip(),
            "answer_text": answer.strip(),
            "category": "auto_generated"
        }, on_conflict="user_id,question_text").execute()
    except Exception as e:
        print(f"Failed to save LLM answer to question bank: {e}")

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
    qb_questions = [row.get('question_text') for row in qb_data if row.get('question_text')]
    
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

        # EXPERT RESOLVER (Replacing old LLM fallback)
        if not ans and label_text:
            ans = autonomous_answer_resolver(label_text, profile, job)
            if ans:
                 print(f"🤖 Autonomous Resolver suggested: '{label_text}' -> {ans}")
                 _log_ai_decision(label_text, ans)

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
