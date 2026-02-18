import sys
import os
import traceback

try:
    # Clean previous run
    if os.path.exists("success.txt"): os.remove("success.txt")
    if os.path.exists("failure.txt"): os.remove("failure.txt")

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(r"d:\website@Antigravity\jops auto apply\.env")
    from supabase import create_client
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    supabase = create_client(url, key)

    from services.job_discovery import discover_and_score_jobs
    
    user_id = "b47f778e-2ce7-4f95-aaa4-cc66582b5a3a"
    result = discover_and_score_jobs(user_id, supabase)
    
    with open("success.txt", "w", encoding="utf-8") as f:
        f.write(str(result))

except Exception:
    with open("failure.txt", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
