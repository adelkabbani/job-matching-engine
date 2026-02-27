import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

supabase = create_client(url, key)

with open("recent_jobs_debug.txt", "w", encoding="utf-8") as f:
    try:
        # Get last 20 jobs captured by linkedin_assistant
        res = supabase.table("jobs").select("title, company, is_easy_apply, source, created_at").eq("source", "linkedin_assistant").order("created_at", desc=True).limit(20).execute()
        f.write(f"Last 20 LinkedIn Assistant jobs:\n")
        f.write(json.dumps(res.data, indent=2) + "\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
