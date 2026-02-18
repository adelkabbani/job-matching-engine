
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Force stdout flush
sys.stdout.reconfigure(line_buffering=True)

load_dotenv(dotenv_path="backend/.env")
URL = os.getenv("SUPABASE_URL")
# Use Service Key to bypass RLS
KEY = os.getenv("SUPABASE_SERVICE_KEY")

def run():
    print("--- CLAIM LEGACY CVs ---")
    if not URL or not KEY:
        print("❌ Credentials missing.")
        return

    try:
        client = create_client(URL, KEY)
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return
    
    # Get all CVs
    try:
        # Filter docs only where doc_type = 'cv'
        res = client.table("documents").select("id, original_filename, user_id, created_at").eq("doc_type", "cv").order("created_at", desc=True).limit(5).execute()
        
        if not res.data:
            print("❌ No CVs found.")
            return

        print("\n📊 Top 5 Latest CVs:")
        
        for i, doc in enumerate(res.data):
            print(f"[{i+1}] {doc.get('original_filename')} | ID: {doc.get('id')}")
            print(f"    Owner: {doc.get('user_id')}")
            
        print("\nTo claim these CVs for your current user:")
        print("1. Find your User ID (e.g., from browser console or profile check)")
        target_user_id = input("👉 Enter YOUR User ID (or press Enter to skip): ").strip()
        
        if not target_user_id:
            print("Skipped.")
            return
            
        # Update logic
        print(f"\nUpdating top 5 CVs to owner: {target_user_id}...")
        for doc in res.data:
            update_res = client.table("documents").update({"user_id": target_user_id}).eq("id", doc.get("id")).execute()
            print(f"✅ Updated {doc.get('original_filename')}")
            
        print("\n🎉 Done! Refresh the Dashboard.")
        
    except Exception as e:
        print(f"❌ Query Error: {e}")

if __name__ == "__main__":
    run()
