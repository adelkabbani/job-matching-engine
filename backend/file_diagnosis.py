
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def diagnose():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    
    with open("diag_output.txt", "w", encoding="utf-8") as f:
        if not url or not key:
            f.write("❌ Supabase credentials missing in .env\n")
            return

        try:
            supabase: Client = create_client(url, key)
            f.write("--- 📊 DATABASE DIAGNOSIS ---\n")
            
            # Check total jobs
            res_total = supabase.table("jobs").select("id", count="exact").execute()
            f.write(f"Total jobs: {getattr(res_total, 'count', 'N/A')}\n")
            
            # Check high match jobs
            # We want to see WHY they aren't being applied.
            # Filtering criteria in main.py:
            # .gte("match_score", 90).eq("status", "scraped").like("job_url", "%linkedin.com/jobs/view/%")
            
            f.write("\nChecking Eligibility for Auto-Pilot:\n")
            
            # 1. Total Scraped + High Match
            res_high = supabase.table("jobs").select("id", "title", "company", "match_score", "status", "job_url").gte("match_score", 90).eq("status", "scraped").execute()
            high_data = getattr(res_high, 'data', []) or []
            f.write(f"1. Matches >= 90 (Status='scraped'): {len(high_data)}\n")
            
            linkedin_count = 0
            for j in high_data:
                j_url = j.get("job_url") or ""
                if "linkedin.com/jobs/view/" in j_url:
                    linkedin_count += 1
                    f.write(f"   ✅ [LINKEDIN] {j.get('title')} @ {j.get('company')} | URL: {j_url}\n")
                else:
                    f.write(f"   ❌ [NON-LK] {j.get('title')} @ {j.get('company')} | URL: {j_url[:50]}...\n")
            
            f.write(f"\nSummary: Found {linkedin_count} valid LinkedIn jobs ready for Auto-Pilot.\n")

            # Check existing applications
            res_apps = supabase.table("applications").select("*").execute()
            apps_data = getattr(res_apps, 'data', []) or []
            f.write(f"\nExisting Applications: {len(apps_data)}\n")
            for app in apps_data:
                f.write(f"  - {app.get('role_title')} @ {app.get('company')} | Status: {app.get('status')}\n")

        except Exception as e:
            import traceback
            f.write(f"❌ ERROR: {str(e)}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    diagnose()
