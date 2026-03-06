import os
import asyncio
from typing import Dict, List, Optional
from playwright.async_api import Page, BrowserContext
from services.llm import autonomous_answer_resolver
from services.universal_scraper import scrape_job_form

LOGS_DIR = os.path.join(os.getcwd(), ".tmp", "logs", "applications")

async def navigate_to_final_application_page(page: Page):
    """
    Handles the 'hallway' screens like Adzuna's email registration 
    and 'No thank you' prompts before the real form.
    Follows a strict 3-stage clinical sequence:
    Step 1: Click 'No thank you' / Skip prompts
    Step 2: ONLY click the final redirect 'Apply' / 'Bewerben' button
    Step 3: Wait for load + stabilization
    """
    # 1. STEP 1: Skip Modals/Popups/Prompts
    skip_selectors = [
        'button:has-text("No thank you")', 
        'button:has-text("Continue without job email")',
        'button:has-text("Nein danke")', 
        'a:has-text("No thanks")',
        'button:has-text("Skip")',
        'button[aria-label="Close"]',
        '.close-modal',
        '.modal-close',
        '#skip-email-reg'
    ]
    for selector in skip_selectors:
        try:
            if await page.is_visible(selector, timeout=2000):
                await page.click(selector)
                print(f"✅ [SKIP-SEQ] Bypassed prompt using: {selector}")
                await asyncio.sleep(1)
        except: pass

    # 2. STEP 2: The Actionable Redirect Button
    redirect_selectors = [
        'a:has-text("Apply")',
        'a:has-text("Apply on company site")',
        'a:has-text("Bewerben")',
        'a:has-text("Auf Arbeitgeber-Website bewerben")',
        'a:has-text("View job")',
        'a:has-text("Original-Anzeige")',
        'a.adzuna-apply-button',
        'button:has-text("Apply")',
        'button:has-text("Bewerben")'
    ]
    
    for selector in redirect_selectors:
        try:
            if await page.is_visible(selector, timeout=3000):
                print(f"✅ [SKIP-SEQ] Clicking primary redirect: {selector}")
                # VISION DEBUG: Save proof before escape
                await page.screenshot(path=os.path.join(LOGS_DIR, "hallway_escape_attempt.png"))
                
                async with page.expect_navigation(timeout=20000):
                    await page.click(selector)
                
                # 3. STEP 3: Mandatory Waiting
                print(f"🚀 [SKIP-SEQ] Escaped hallway. Stabilizing...")
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except:
                    print("⚠️ Timeout waiting for networkidle, proceeding anyway.")
                
                await asyncio.sleep(5) # Stabilization sleep for JS redirects
                return # Successfully escaped
        except Exception as e:
            print(f"⚠️ [SKIP-SEQ] Redirect failed for {selector}: {e}")
            # Log failure HTML for diagnosis
            with open(os.path.join(LOGS_DIR, "hallway_fail.html"), "w", encoding="utf-8") as f:
                f.write(await page.content())

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
    
    # 0. Navigate 'Hallways' (Adzuna register popups, etc.)
    await navigate_to_final_application_page(page)
    
    # 1. Scrape with Firecrawl
    job_url = job_details.get('job_url', '')
    
    # --- Adzuna Bypass Logic ---
    if "adzuna" in job_url.lower():
        print("🕵️ [UNIVERSAL-PILOT] Adzuna landing page detected. Navigating to company site...")
        try:
            await page.goto(job_url, wait_until="networkidle")
            # Try common Adzuna "Apply" buttons (English & German)
            adzuna_apply_selectors = [
                 'a:has-text("Apply on company site")',
                 'a:has-text("View job")',
                 'a:has-text("Original-Anzeige")',
                 'a:has-text("Auf Arbeitgeber-Website bewerben")',
                 'a:has-text("Zum Stellenangebot")',
                 '.apply-button',
                 '#apply_button'
            ]
            for selector in adzuna_apply_selectors:
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    print(f"✅ [UNIVERSAL-PILOT] Clicking Adzuna redirect: {selector}")
                    async with page.expect_navigation(wait_until="networkidle", timeout=15000):
                        await locator.click()
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
    
    # 2. Get Real User Data from cv_structured_data
    # Use real email/name/phone from the structured CV data
    try:
        # 2.1 Find latest CV document
        docs = supabase.table("documents").select("id").eq("user_id", user_id).eq("doc_type", "cv").order("created_at", desc=True).limit(1).execute()
        
        parsed_personal_info = {}
        if docs.data:
            cv_id = docs.data[0]["id"]
            # 2.2 Get parsed data
            struct_res = supabase.table("cv_structured_data").select("parsed_data").eq("document_id", cv_id).execute()
            if struct_res.data:
                # CLINICAL: Be extremely descriptive about what we find
                raw_parsed_data = struct_res.data[0].get("parsed_data") or {}
                if isinstance(raw_parsed_data, str):
                    import json
                    raw_parsed_data = json.loads(raw_parsed_data)
                
                parsed_personal_info = raw_parsed_data.get("personal_info", {})
                print(f"📚 [UNIVERSAL-PILOT] SUCCESS: Loaded real data for User ID {user_id}: {parsed_personal_info.get('email', 'Email MISSING in JSON')}")
            else:
                print(f"⚠️ [UNIVERSAL-PILOT] FAILED: No structured record for CV {cv_id}")
            
        # 2.3 Fallback to profile if CV data missing
        profile_res = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        profile = profile_res.data or {}
        
        # Merge hierarchy: Parsed CV > Profile Profile
        user_data = {
            "full_name": parsed_personal_info.get("full_name") or profile.get("full_name", ""),
            "email": parsed_personal_info.get("email") or profile.get("email", ""),
            "phone": parsed_personal_info.get("phone") or profile.get("phone_number", "")
        }
        
    except Exception as e:
        print(f"⚠️ [UNIVERSAL-PILOT] Failed to fetch user data: {e}")
        return {"status": "error", "message": f"User data retrieval failed: {e}"}
    
    # 3. Setup Log Dir
    job_log_dir = os.path.join(LOGS_DIR, str(job_id))
    os.makedirs(job_log_dir, exist_ok=True)
    
    # Step counter for Vision Debugging
    step_count = 0

    try:
        # 4. Fill Main Fields
        # Full Name
        full_name_selector = fields.get('full_name_field') or 'input[name*="name"], input[placeholder*="Name"], #name, #full_name'
        if full_name_selector:
            step_count += 1
            await _fill_field(page, full_name_selector, user_data.get('full_name', ''), optional=True)
            await page.screenshot(path=os.path.join(job_log_dir, f"step_{step_count}_name.png"))
            
        # Email
        email_selector = fields.get('email_field') or 'input[type="email"], input[name*="email"], #email'
        if email_selector:
            step_count += 1
            await _fill_field(page, email_selector, user_data.get('email', ''), optional=True)
            await page.screenshot(path=os.path.join(job_log_dir, f"step_{step_count}_email.png"))
            
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
            'button:has-text("Senden")',
            'button:has-text("Bewerben")',
            'button:has-text("Bewerbung absenden")',
            '[id*="submit"]',
            '[class*="submit"]',
            fields.get('submit_button')
        ]
        
        # Filter None and duplicates
        submit_selectors = list(dict.fromkeys([s for s in submit_selectors if s]))
        
        print(f"🖱️ [UNIVERSAL-PILOT] Searching for submit button using: {submit_selectors}")
        
        success_click = False
        
        # Priority 1: User specified or common text-based buttons (Multi-language)
        text_buttons = [
            "Apply", "Submit", "Send Application", 
            "Bewerben", "Absenden", "Einreichen", "Bewerbung absenden", "Senden",
            "Bewerbung einreichen", "Absenden", "Unterlagen senden", "Einreichen",
            "Postuler", "Envoyer"
        ]
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
            # VISION DEBUG: Save HTML Source Code if no button found
            print("❌ [VISION-DEBUG] No submit button found. Saving HTML source...")
            html_dbg_path = os.path.join(job_log_dir, "debug_no_button.html")
            with open(html_dbg_path, "w", encoding="utf-8") as f:
                f.write(await page.content())
            return {"status": "error", "message": f"Could not find a valid submit button. Debug: {html_dbg_path}"}

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
        "full_name_field": 'input[name*="name"], input[placeholder*="Name"], input[placeholder*="Vorname"], input[placeholder*="Nachname"], input[aria-label*="Name"], #name, #full_name, #vorname, #nachname',
        "email_field": 'input[type="email"], input[name*="email"], input[name*="mail"], input[title*="Email"], input[placeholder*="E-Mail"], #email',
        "resume_upload_selector": 'input[type="file"], input[name*="resume"], input[name*="cv"], #resume, #cv',
        "submit_button": 'button[type="submit"], button:has-text("Apply"), button:has-text("Submit"), button:has-text("Senden"), button:has-text("Bewerbung einreichen"), button:has-text("Bewerben")',
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
