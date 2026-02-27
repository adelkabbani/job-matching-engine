import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment
env_path = r'd:\website@Antigravity\jops auto apply\backend\.env'
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

def check_schema():
    print("\n--- 1. Checking 'jobs' Table Columns ---")
    try:
        # Get one row to see all columns
        res = supabase.table('jobs').select('*').limit(1).execute()
        if res.data:
            columns = list(res.data[0].keys())
            print(f"Current columns: {columns}")
            for col in ['is_easy_apply', 'status']:
                if col in columns:
                    print(f"  ✅ '{col}' EXISTS")
                else:
                    print(f"  ❌ '{col}' MISSING")
        else:
            print("No data in 'jobs' table to check columns via select *.")
            # Fallback: try to select specific columns
            for col in ['is_easy_apply', 'status']:
                try:
                    supabase.table('jobs').select(col).limit(1).execute()
                    print(f"  ✅ '{col}' EXISTS")
                except Exception:
                    print(f"  ❌ '{col}' MISSING")
    except Exception as e:
        print(f"Error checking jobs table: {e}")

    print("\n--- 2. Checking Other Tables ---")
    for table in ['applications', 'linkedin_question_bank']:
        try:
            supabase.table(table).select('count', count='exact').limit(1).execute()
            print(f"  ✅ Table '{table}' EXISTS")
        except Exception as e:
            if 'does not exist' in str(e).lower() or 'PGRST204' in str(e):
                print(f"  ❌ Table '{table}' MISSING")
            else:
                print(f"  ❓ Table '{table}' check failed: {str(e)[:100]}")

if __name__ == "__main__":
    check_schema()
