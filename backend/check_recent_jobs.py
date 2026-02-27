import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

supabase = create_client(url, key)

try:
    # Get last 10 jobs captured by linkedin_assistant
    res = supabase.table("jobs").select("title, company, is_easy_apply, source, created_at").eq("source", "linkedin_assistant").order("created_at", desc=True).limit(10).execute()
    print(f"Last 10 LinkedIn Assistant jobs:")
    print(json.dumps(res.data, indent=2))
except Exception as e:
    print(f"Error: {e}")
