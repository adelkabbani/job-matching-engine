import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

print(f"URL: {url}")
print(f"Key beginning: {key[:10] if key else 'None'}...")

if not url or not key:
    print("Missing credentials")
    exit(1)

supabase = create_client(url, key)

try:
    print("Querying jobs table...")
    res = supabase.table("jobs").select("*").limit(5).execute()
    print(f"Data returned: {len(res.data) if res.data else 0} rows")
    if res.data:
        print("Columns found in first row:")
        print(json.dumps(list(res.data[0].keys()), indent=2))
        print("Example row:")
        print(json.dumps(res.data[0], indent=2, default=str))
    else:
        print("No jobs found in DB.")
except Exception as e:
    print(f"Error: {e}")
