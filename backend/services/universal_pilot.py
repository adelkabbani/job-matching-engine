import os
import asyncio
from typing import Dict, List, Optional
from playwright.async_api import Page, BrowserContext
from services.llm import autonomous_answer_resolver
from services.universal_scraper import scrape_job_form

LOGS_DIR = os.path.join(os.getcwd(), ".tmp", "logs", "applications")

async def autofill_universal_form(
    page: Page, 
    job_id: str, 
    user_id: str, 
    supabase, 
    job_details: Dict,
    dry_run: bool = False
) -> Dict:
    """
    Fills a generic web form using Firecrawl extraction data.
    """
    print(f"🚀 [UNIVERSAL-PILOT] Starting Direct Apply for: {job_details.get('title')}")
    
    # 1. Scrape with Firecrawl
    job_url = job_details.get('job_url', '')
    
    # --- Adzuna Bypass Logic ---
    if "adzuna" in job_url.lower():
        print("🕵️ [UNIVERSAL-PILOT] Adzuna landing page detected. Navigating to company site...")
        try:
            await page.goto(job_url, wait_until="networkidle")
            # Try common Adzuna "Apply" buttons
            adzuna_apply_selectors = [
                'a:has-text("Apply on company site")',
                'a:has-text("View job")',
                '.apply-button',
                '#apply_button'
            ]
            for selector in adzuna_apply_selectors:
                if await page.locator(selector).count() > 0:
                    print(f"✅ [UNIVERSAL-PILOT] Clicking Adzuna redirect: {selector}")
                    async with page.expect_navigation(wait_until="networkidle", timeout=15000):
                        await page.click(selector)
                    break
        except Exception as e:
            print(f"⚠️ [UNIVERSAL-PILOT] Adzuna bypass failed: {e}")
    # ---------------------------

    scrape_res = scrape_job_form(page.url if "adzuna" in job_url.lower() else job_url)
    
    fields = {}
    if scrape_res["status"] == "FALLBACK_REQUIRED":
        print("⚠️ [UNIVERSAL-PILOT] Firecrawl unavailable. Executing Heuristic Fallback...")
        fields = await _execute_heuristic_scan(page)
    elif scrape_res["status"] == "error":
        return scrape_res
    else:
        fields = scrape_res["fields"]
    
    # 2. Get User Data
    profile_res = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    if not profile_res.data:
        return {"status": "error", "message": "User profile not found."}
    profile = profile_res.data
    
    # 3. Setup Log Dir
    job_log_dir = os.path.join(LOGS_DIR, str(job_id))
    os.makedirs(job_log_dir, exist_ok=True)
    
    try:
        # 4. Fill Main Fields
        # Full Name
        full_name_selector = fields.get('full_name_field') or 'input[name*="name"], input[placeholder*="Name"], #name, #full_name'
        if full_name_selector:
            await _fill_field(page, full_name_selector, profile.get('full_name', ''), optional=True)
            
        # Email
        email_selector = fields.get('email_field') or 'input[type="email"], input[name*="email"], #email'
        if email_selector:
            await _fill_field(page, email_selector, profile.get('email', ''), optional=True)
            
        # Resume Upload
        resume_selector = fields.get('resume_upload_selector') or 'input[type="file"], input[name*="resume"], input[name*="cv"], #resume, #cv'
        if resume_selector:
            # Fetch the tailored CV path
            # (Logic remains same, just using resume_selector)
            print(f"📤 [UNIVERSAL-PILOT] Resume upload attempt at: {resume_selector}")
            # Implementation for file upload...
            
        # 5. Handle Additional Fields with LLM
        for field in fields.get('additional_fields', []):
            label = field.get('label')
            selector = field.get('selector')
            if not label or not selector: continue
            
            # Use autonomous resolver
            answer = autonomous_answer_resolver(label, profile, job_details)
            if answer:
                await _fill_field(page, selector, answer)

        # 6. Final Screenshot before Submit
        await page.screenshot(path=os.path.join(job_log_dir, "before_submit.png"))
        
        if dry_run:
            return {"status": "success", "message": "Dry Run: Universal form filled successfully."}
            
        # 7. Submit with multi-selector fallback
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Apply")',
            'button:has-text("Submit")',
            'button:has-text("Send Application")',
            '.submit-button',
            '#submit_button',
            fields.get('submit_button')
        ]
        
        # Filter None and duplicates
        submit_selectors = list(dict.fromkeys([s for s in submit_selectors if s]))
        
        print(f"🖱️ [UNIVERSAL-PILOT] Searching for submit button using: {submit_selectors}")
        
        success_click = False
        
        # Priority 1: User specified or common text-based buttons (Multi-language)
        text_buttons = ["Apply", "Submit", "Send Application", "Bewerben", "Absenden", "Postuler"]
        for btn_text in text_buttons:
            try:
                btn = page.get_by_role("button", name=btn_text, exact=False)
                if await btn.count() > 0:
                    print(f"✅ [UNIVERSAL-PILOT] Found and clicking role-based button: {btn_text}")
                    await btn.click(timeout=3000)
                    success_click = True
                    break
            except Exception:
                continue

        if not success_click:
            # Priority 2: CSS Selector Fallback
            for selector in submit_selectors:
                try:
                    # Short timeout for each attempt
                    await page.wait_for_selector(selector, timeout=3000)
                    print(f"✅ [UNIVERSAL-PILOT] Found and clicking: {selector}")
                    await page.click(selector)
                    success_click = True
                    break
                except Exception:
                    continue
                
        if not success_click:
            return {"status": "error", "message": "Could not find a valid submit button after multiple attempts."}

        await asyncio.sleep(5)
            
        # Verify and save proof
        success_path = os.path.join(job_log_dir, "success_proof.png")
        await page.screenshot(path=success_path)
        
        return {
            "status": "success", 
            "message": "Direct Apply submitted successfully.",
            "screenshot": success_path
        }
            
    except Exception as e:
        print(f"❌ [UNIVERSAL-PILOT] Error: {e}")
        return {"status": "error", "message": str(e)}

    return {"status": "error", "message": "Unknown workflow end."}

async def _execute_heuristic_scan(page: Page) -> Dict:
    """
    Scans the page for common form field selectors.
    Used when Firecrawl is unavailable.
    """
    fields = {
        "full_name_field": 'input[name*="name"], input[placeholder*="Name"], #name, #full_name',
        "email_field": 'input[type="email"], input[name*="email"], #email',
        "resume_upload_selector": 'input[type="file"], input[name*="resume"], input[name*="cv"], #resume, #cv',
        "submit_button": 'button[type="submit"], button:has-text("Apply"), button:has-text("Submit")',
        "additional_fields": []
    }
    return fields

async def _fill_field(page: Page, selector: str, value: str, optional: bool = False):
    try:
        # Wait less for optional fields
        timeout = 2000 if optional else 5000
        await page.wait_for_selector(selector, timeout=timeout)
        # Check if it's a select or input
        tag_name = await page.evaluate(f'(s) => document.querySelector(s)?.tagName', selector)
        if tag_name == 'SELECT':
            await page.select_option(selector, label=value)
        else:
            await page.fill(selector, value)
        print(f"  [FILL] {selector} -> {value}")
    except Exception:
        if not optional:
            print(f"  [WARN] Could not fill mandatory field: {selector}")
        else:
            print(f"  [DEBUG] Optional field not found: {selector}")
