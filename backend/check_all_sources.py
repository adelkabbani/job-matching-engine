import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

supabase = create_client(url, key)

with open("all_linkedin_jobs_debug.txt", "w", encoding="utf-8") as f:
    try:
        # Check all unique sources
        res_sources = supabase.table("jobs").select("source").execute()
        sources = list(set([r['source'] for r in res_sources.data]))
        f.write(f"Available sources: {sources}\n")
        
        # Get count per source
        for s in sources:
            count_res = supabase.table("jobs").select("id", count="exact").eq("source", s).execute()
            f.write(f"Source '{s}': {count_res.count} jobs\n")

        # Get jobs where is_easy_apply is true
        easy_res = supabase.table("jobs").select("title, company, source").eq("is_easy_apply", True).execute()
        f.write(f"Jobs with is_easy_apply=True: {len(easy_res.data)}\n")
        f.write(json.dumps(easy_res.data, indent=2) + "\n")
        
    except Exception as e:
        f.write(f"Error: {e}\n")
