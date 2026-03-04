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
        
        # Check if all 5 required statuses are present or at least documented
        required = ['scraped', 'shortlisted', 'applying', 'applied', 'failed']
        print(f"🔥 LIVE DATABASE VALID STATUSES: {valid}")
        
        missing = [s for s in required if s not in valid]
        if missing:
            print(f"⚠️ Missing statuses in current records: {missing}")
            print("💡 This is normal if you haven't used them yet, but the SQL below forces them to be allowed.")
        else:
            print("✅ All required Auto-Pilot statuses are confirmed in recent records.")
            
    except Exception as e:
        print(f"❌ Query Error: {e}")

    print("\n[MASTER KEY] Run this SQL in your Supabase Editor to unlock the Universal Pivot:")
    print("-" * 50)
    print("""
-- UNLOCK ALL LABELS: scraped, shortlisted, applying, applied, failed, rejected
ALTER TABLE public.jobs DROP CONSTRAINT IF EXISTS jobs_status_check;
ALTER TABLE public.jobs ADD CONSTRAINT jobs_status_check 
CHECK (status IN ('scraped', 'shortlisted', 'applying', 'applied', 'failed', 'rejected'));

COMMENT ON TABLE public.jobs IS 'Universal Pivot: Pipeline unlocked for all application stages';
    """)
    print("-" * 50)

if __name__ == "__main__":
    migrate()
