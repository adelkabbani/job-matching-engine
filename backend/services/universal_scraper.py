import os
import requests
from typing import Dict, Optional

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "").strip().replace('"', '').replace("'", "")

def scrape_job_form(url: str) -> Dict:
    """
    Use Firecrawl to extract form field information from a job application page.
    This bypasses the need for hardcoded CSS selectors.
    """
    if not FIRECRAWL_API_KEY:
        print("⚠️ FIRECRAWL_API_KEY not found in .env.")
        return {"status": "error", "message": "Firecrawl API key missing."}

    # Define the extraction schema as requested by the user
    extraction_schema = {
        "type": "object",
        "properties": {
            "full_name_field": {
                "type": "string",
                "description": "The CSS selector or ID for the Full Name or First Name input field."
            },
            "email_field": {
                "type": "string",
                "description": "The CSS selector or ID for the Email input field."
            },
            "resume_upload_selector": {
                "type": "string",
                "description": "The CSS selector for the file upload input for the Resume/CV."
            },
            "submit_button": {
                "type": "string",
                "description": "The CSS selector for the final 'Submit' or 'Apply' button."
            },
            "is_easy_apply_equivalent": {
                "type": "boolean",
                "description": "True if the form is short and can be automatically filled."
            },
            "additional_fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "description": "The human-readable label for the field."},
                        "selector": {"type": "string", "description": "The CSS selector for this field."},
                        "type": {"type": "string", "enum": ["text", "select", "radio", "checkbox"], "description": "Type of form field."}
                    }
                }
            }
        },
        "required": ["full_name_field", "email_field", "submit_button"]
    }

    payload = {
        "url": url,
        "formats": ["extract"],
        "extract": {
            "schema": extraction_schema,
            "systemPrompt": "Identify the primary job application form fields on this page. Focus on the main apply form. Return CSS selectors that are most likely to work with Playwright (IDs preferred)."
        }
    }

    try:
        print(f"🔥 [FIRECRAWL] Analyzing universal form at: {url}")
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data", {}).get("extract"):
                print(f"✅ [FIRECRAWL] Successfully extracted schema for {url}")
                return {
                    "status": "success",
                    "fields": data["data"]["extract"]
                }
            else:
                print(f"⚠️ [FIRECRAWL] Extraction returned no fields for {url}")
                return {"status": "error", "message": "Extraction failed or returned no fields."}
        else:
            print(f"❌ [FIRECRAWL] API returned status {response.status_code}: {response.text}")
            return {"status": "error", "message": f"Firecrawl API error: {response.status_code}"}
            
    except Exception as e:
        print(f"❌ [FIRECRAWL] Scrape process crashed: {e}")
        return {"status": "error", "message": str(e)}
