import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def migrate():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Supabase credentials missing (Checked SUPABASE_SERVICE_KEY).")
        return

    supabase: Client = create_client(url, key)
    
    print("\n--- 🔍 Current Database Statuses ---")
    try:
        res = supabase.table("jobs").select("status").limit(100).execute()
        valid = list(set([x.get("status") for x in res.data if x.get("status")]))
        print(f"LIVE DATABASE VALID STATUSES: {valid}")
        
        if 'applied' in valid:
            print("✅ 'applied' status ALREADY EXISTS.")
        else:
            print("⚠️ 'applied' status MISSING.")
    except Exception as e:
        print(f"❌ Query Error: {e}")

    print("\n[INSTRUCTION] Please run this SQL in Supabase UI to UNLOCK all labels:")
    print("-" * 30)
    print("""
ALTER TABLE public.jobs DROP CONSTRAINT IF EXISTS jobs_status_check;
ALTER TABLE public.jobs ADD CONSTRAINT jobs_status_check CHECK (status IN ('scraped', 'shortlisted', 'applying', 'applied', 'failed'));
    """)
    print("-" * 30)

if __name__ == "__main__":
    migrate()
