import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    print("Missing credentials")
    exit(1)

supabase = create_client(url, key)

try:
    res = supabase.table("jobs").select("*").limit(1).execute()
    if res.data:
        print("Columns found in 'jobs' table:")
        print(list(res.data[0].keys()))
    else:
        print("No jobs found in DB.")
except Exception as e:
    print(f"Error: {e}")
