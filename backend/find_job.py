import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment
env_path = r'd:\website@Antigravity\jops auto apply\backend\.env'
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

def find_easy_apply_job():
    print("\n--- Searching for Easy Apply Jobs ---")
    try:
        res = supabase.table('jobs').select('*').eq('is_easy_apply', True).limit(5).execute()
        if res.data:
            for job in res.data:
                print(f"ID: {job['id']} | Title: {job['title']} | Company: {job['company']}")
        else:
            print("No Easy Apply jobs found in database.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_easy_apply_job()
