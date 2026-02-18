
import os
from dotenv import load_dotenv
from supabase import create_client

def run_migration():
    print("🚀 Applying Migration 009: Add AI Versioning...")
    
    # Load env
    load_dotenv(dotenv_path="backend/.env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("❌ Error: Missing Supabase credentials.")
        return

    try:
        supabase = create_client(url, key)
        
        # Read SQL file
        with open("backend/migrations/009_add_ai_versioning.sql", "r") as f:
            sql = f.read()
            
        # Execute (rpc if available, but for now we just try direct execution via a pg helper or just assume user runs it? 
        # Wait, Supabase-py doesn't execute raw SQL directly unless we have a stored procedure or use dashboard.
        # Actually, for this environment, I usually just ask user to run SQL.
        # BUT, I can try to use the `rpc` method if I had a `exec_sql` function.
        # Since I don't, I'll just print the instructions or try to use a standardized way if available.
        
        # Let's just create a dummy "success" message for now as I can't run DDL via REST API easily without a helper.
        # WAIT! I can use the trick: Create a function via dashboard? No.
        
        print(f"⚠️  NOTE: Supabase-py client cannot execute raw DDL (CREATE TABLE/ALTER TABLE) directly.")
        print("    Please run the contents of 'backend/migrations/009_add_ai_versioning.sql' in your Supabase SQL Editor.")
        print("    (Or if you have a local Postgres connection, use that).")
        
        # However, for the sake of this agent environment, I often just assume it's done or use a workaround.
        # Let's try to simulate it or leave it to the user.
        # Actually, I'll just mark it as "Manual Action Required" in the output.
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_migration()
