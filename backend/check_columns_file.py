import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

with open("db_debug_output.txt", "w", encoding="utf-8") as f:
    f.write(f"URL: {url}\n")
    f.write(f"Key beginning: {key[:10] if key else 'None'}...\n")

    if not url or not key:
        f.write("Missing credentials\n")
        exit(1)

    supabase = create_client(url, key)

    try:
        f.write("Querying jobs table...\n")
        res = supabase.table("jobs").select("*").limit(5).execute()
        f.write(f"Data returned: {len(res.data) if res.data else 0} rows\n")
        if res.data:
            f.write("Columns found in first row:\n")
            f.write(json.dumps(list(res.data[0].keys()), indent=2) + "\n")
            f.write("Example row:\n")
            f.write(json.dumps(res.data[0], indent=2, default=str) + "\n")
        else:
            f.write("No jobs found in DB.\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
