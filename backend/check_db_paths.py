from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

def check_screenshot_paths():
    res = supabase.table("applications").select("id, job_id, success_screenshot_path, status").not_.is_("success_screenshot_path", "null").execute()
    if res.data:
        print(f"✅ Found {len(res.data)} applications with success_screenshot_path:")
        for app in res.data:
            print(f"ID: {app['id']} | Job ID: {app['job_id']} | Status: {app['status']} | Path: {app['success_screenshot_path']}")
    else:
        print("❌ No applications found with success_screenshot_path.")

    # Also check most recent applications
    print("\nRecent applications (last 5):")
    res_recent = supabase.table("applications").select("id, job_id, success_screenshot_path, status, created_at").order("created_at", desc=True).limit(5).execute()
    for app in res_recent.data:
        print(f"ID: {app['id']} | Status: {app['status']} | Path: {app['success_screenshot_path']} | Date: {app['created_at']}")

if __name__ == "__main__":
    check_screenshot_paths()
