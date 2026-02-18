
import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client

# Force stdout flush
sys.stdout.reconfigure(line_buffering=True)

OUTPUT_FILE = "backend/parsing_status.txt"

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear previous log
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("--- CHECKING DOCUMENT OWNERSHIP ---\n")

load_dotenv(dotenv_path="backend/.env")
URL = os.getenv("SUPABASE_URL")
# Use Service Key to bypass RLS
KEY = os.getenv("SUPABASE_SERVICE_KEY")

def run():
    if not URL or not KEY:
        log("❌ Credentials missing.")
        return

    try:
        client = create_client(URL, KEY)
    except Exception as e:
        log(f"❌ Connection Error: {e}")
        return
    
    # Get all CVs
    try:
        # Filter docs only where doc_type = 'cv'
        res = client.table("documents").select("id, original_filename, user_id, created_at").eq("doc_type", "cv").order("created_at", desc=True).limit(5).execute()
        
        if not res.data:
            log("❌ No CVs found.")
            return

        log("📊 Top 5 Latest CVs:")
        
        for doc in res.data:
            log(f"📄 {doc.get('original_filename')} | ID: {doc.get('id')}")
            log(f"   owner_user_id: {doc.get('user_id')}")
            log("---")
            
        current_user_id = "UNKNOWN (Frontend)" # We can't know frontend user ID here easily
        log(f"\n⚠️ NOTE: The Dashboard only shows CVs where user_id matches the logged-in user.")
        
    except Exception as e:
        log(f"❌ Query Error: {e}")

if __name__ == "__main__":
    run()
