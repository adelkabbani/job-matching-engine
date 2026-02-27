import asyncio
import os
import json
from supabase import create_client
from dotenv import load_dotenv
from services.linkedin_assistant import capture_current_search_results, launch_linkedin_browser

async def test_capture():
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    supabase = create_client(url, key)
    
    # Use the user_id found in previous debug
    user_id = "b47f778e-2ce7-4f95-aaa4-cc66582b5a3a"
    
    print("Testing capture_current_search_results...")
    result = await capture_current_search_results(user_id, supabase)
    
    print(f"Capture result status: {result.get('status')}")
    print(f"Jobs captured: {result.get('count')}")
    
    if result.get('count', 0) > 0:
        # Check if any have is_easy_apply: true
        easy_apply_count = sum(1 for j in result.get('jobs', []) if j.get('is_easy_apply'))
        print(f"Jobs with Easy Apply flag in memory: {easy_apply_count}")
        
        # Verify in DB for a few samples
        for job in result.get('jobs', [])[:3]:
            res = supabase.table("jobs").select("*").eq("job_url", job['url']).execute()
            if res.data:
                db_job = res.data[0]
                print(f"Job: {db_job['title']} | Easy Apply (DB): {db_job['is_easy_apply']}")
    else:
        print("No new jobs captured (might be duplicates).")

if __name__ == "__main__":
    asyncio.run(test_capture())
