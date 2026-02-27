import asyncio
import os
import json
from supabase import create_client
from dotenv import load_dotenv
from services.linkedin_assistant import capture_current_search_results, launch_linkedin_browser, _browser_context

async def test_capture_full():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    supabase = create_client(url, key)
    
    user_id = "b47f778e-2ce7-4f95-aaa4-cc66582b5a3a"
    
    with open("capture_test_log.txt", "w", encoding="utf-8") as log:
        log.write("🚀 Starting full capture test...\n")
        
        try:
            # 1. Launch browser
            log.write("🌐 Launching LinkedIn browser...\n")
            await launch_linkedin_browser()
            
            # 2. Get the target page
            from services.linkedin_assistant import _browser_context
            page = _browser_context.pages[0]
            
            # 3. Navigate to a search (if not already there)
            search_url = "https://www.linkedin.com/jobs/search/?keywords=frontend%20engineer%20easy%20apply&location=Berlin&f_AL=true"
            log.write(f"🧭 Navigating to: {search_url}\n")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for results
            await asyncio.sleep(5)
            
            # 4. Trigger capture
            log.write("🕵️ Triggering capture...\n")
            # We need to capture the stdout of the capture function.
            # Since we are in the same process, we can just call it and it will print to the system stdout.
            # To capture it here, we'll just rely on the test_capture_full script's own logs.
            
            result = await capture_current_search_results(user_id, supabase)
            
            log.write(f"📊 Result Status: {result.get('status')}\n")
            log.write(f"📊 Jobs Captured: {result.get('count')}\n")
            log.write(f"📊 Jobs Found: {len(result.get('jobs', []))}\n")
            
            log.write("🏁 Test finished.\n")
            
        except Exception as e:
            import traceback
            log.write(f"❌ Test failed: {e}\n")
            log.write(traceback.format_exc() + "\n")

if __name__ == "__main__":
    asyncio.run(test_capture_full())
