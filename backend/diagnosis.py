
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent dir to path to import local modules if needed
sys.path.append(os.path.dirname(os.getcwd()))

load_dotenv()

def diagnose():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Supabase credentials missing in .env")
        return

    supabase: Client = create_client(url, key)
    
    print("--- 📊 DATABASE DIAGNOSIS ---")
    
    # Check total jobs
    jobs = supabase.table("jobs").select("id", count="exact").execute()
    print(f"Total jobs: {jobs.count}")
    
    # Check applied jobs
    applied = supabase.table("applications").select("*").execute()
    print(f"Total 'applications' records: {len(applied.data)}")
    for app in applied.data:
        print(f"  - Job: {app.get('role_title')} @ {app.get('company')} | Status: {app.get('status')}")

    # Check high match jobs that are NOT yet applied
    high_match = supabase.table("jobs").select("id", "title", "company", "match_score", "status").gte("match_score", 90).eq("status", "scraped").execute()
    print(f"Jobs ready for Auto-Pilot (Score >= 90, status='scraped'): {len(high_match.data)}")
    for j in high_match.data:
        print(f"  - Ready: {j['title']} @ {j['company']} (Score: {j['match_score']})")

    print("\n--- 📁 LOGS DIAGNOSIS ---")
    logs_dir = Path(".tmp/logs/applications")
    if not logs_dir.exists():
        print("❌ Logs directory not found.")
    else:
        dirs = [d for d in logs_dir.iterdir() if d.is_dir()]
        print(f"Found {len(dirs)} job log directories.")
        
        # Check for any success proofs
        successes = list(logs_dir.glob("**/success_proof.png"))
        print(f"Found {len(successes)} 'success_proof.png' files.")
        for s in successes:
            print(f"  - Success Proof: {s} (Size: {s.stat().st_size} bytes)")

if __name__ == "__main__":
    diagnose()
