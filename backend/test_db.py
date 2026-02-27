import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment
env_path = r'd:\website@Antigravity\jops auto apply\backend\.env'
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    exit(1)

supabase: Client = create_client(url, key)

def get_schema_info():
    print("\n--- 1. Testing Column Existence ---")
    test_columns = ['url', 'job_url', 'source', 'status', 'matched_skills']
    
    # We can try to select one row and see which columns come back
    try:
        res = supabase.table('jobs').select('*').limit(1).execute()
        if res.data:
            print(f"Columns found in first row: {list(res.data[0].keys())}")
        else:
            print("No data in jobs table yet.")
            # Try to force an error by selecting non-existent columns
            for col in test_columns:
                try:
                    supabase.table('jobs').select(col).limit(1).execute()
                    print(f"  ✅ Column '{col}' EXISTS")
                except Exception as e:
                    if 'column not found' in str(e).lower() or 'does not exist' in str(e).lower() or 'PGRST204' in str(e):
                        print(f"  ❌ Column '{col}' DOES NOT EXIST")
                    else:
                        print(f"  ❓ Column '{col}' check failed: {str(e)[:100]}")
    except Exception as e:
        print(f"Error fetching schema info: {e}")

if __name__ == "__main__":
    get_schema_info()
