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
    job_url = job_details.get('job_url')
    scrape_res = scrape_job_form(job_url)
    if scrape_res["status"] == "error":
        return scrape_res
        
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
        if fields.get('full_name_field'):
            await _fill_field(page, fields['full_name_field'], profile.get('full_name', ''))
            
        # Email
        if fields.get('email_field'):
            await _fill_field(page, fields['email_field'], profile.get('email', ''))
            
        # Resume Upload
        if fields.get('resume_upload_selector'):
            # Fetch the tailored CV path
            cv_res = supabase.table("cv_versions").select("id").eq("job_id", job_id).execute()
            # For now, we assume a resume is ready or use the base one
            # Logic to find the actual file path would go here
            print(f"📤 [UNIVERSAL-PILOT] Resume upload requested at: {fields['resume_upload_selector']}")
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

async def _fill_field(page: Page, selector: str, value: str):
    try:
        await page.wait_for_selector(selector, timeout=5000)
        # Check if it's a select or input
        tag_name = await page.evaluate(f'(s) => document.querySelector(s)?.tagName', selector)
        if tag_name == 'SELECT':
            await page.select_option(selector, label=value)
        else:
            await page.fill(selector, value)
        print(f"  [FILL] {selector} -> {value}")
    except Exception:
        print(f"  [WARN] Could not fill field: {selector}")
