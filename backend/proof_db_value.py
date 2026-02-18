
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv(dotenv_path="backend/.env")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_KEY")

def run():
    print("\n🔐 DB Proof: Fetching Raw Content from `profiles` table...")
    
    if not URL or not KEY:
        print("❌ Credentials missing.")
        return

    client = create_client(URL, KEY)
    email = "user_a@example.com"
    
    # Get User ID
    users = client.auth.admin.list_users()
    target_user = None
    for u in users:
        if u.email == email:
            target_user = u
            break
            
    if not target_user:
        print(f"❌ User {email} not found.")
        return

    # Fetch raw value
    res = client.table("profiles").select("openrouter_key").eq("id", target_user.id).single().execute()
    data = res.data
    
    raw_value = data.get("openrouter_key", "")
    
    print("-" * 50)
    print(f"User: {email}")
    print(f"Column: profiles.openrouter_key")
    print("-" * 50)
    
    if not raw_value:
        print("❌ Value is EMPTY/NULL")
    elif raw_value.startswith("sk-or-"):
        print(f"❌ PLAIN TEXT DETECTED: {raw_value[:15]}...")
        print("   (This is NOT encrypted!)")
    else:
        print(f"✅ ENCRYPTED CIPHERTEXT: {raw_value[:50]}...")
        print("   (Does not start with 'sk-or-'. Safe!)")
    print("-" * 50)

if __name__ == "__main__":
    run()
