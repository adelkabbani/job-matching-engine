import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path="backend/.env")
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_KEY")

def run():
    print("🔧 Aggressive Login Fix for user_a@example.com...")
    if not URL or not KEY:
        print("❌ Error: Missing credentials.")
        return

    client = create_client(URL, KEY)
    email = "user_a@example.com"
    password = "StrongPass123!A"

    print(f"1. Searching for {email}...")
    try:
        users = client.auth.admin.list_users()
        target_user = None
        for u in users:
            if u.email == email:
                target_user = u
                break
        
        if target_user:
            print(f"   ⚠️ Found user {target_user.id}. DELETING to ensure clean state...")
            client.auth.admin.delete_user(target_user.id)
            print("   ✅ User deleted.")
        else:
            print("   ℹ️ User not found (clean state).")

        print("2. Creating new user...")
        res = client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": "User A (Fixed)"}
        })
        print(f"   ✅ User created: {res.user.id}")

        print("3. Verifying Login...")
        try:
            retry_client = create_client(URL, os.getenv("SUPABASE_ANON_KEY"))
            auth_res = retry_client.auth.sign_in_with_password({"email": email, "password": password})
            if auth_res.user:
                print("   ✅ LOGIN SUCCESSFUL! The password is definitely workin now.")
                print(f"   👉 Email: {email}")
                print(f"   👉 Password: {password}")
            else:
                print("   ❌ Login verification failed (No user returned).")
        except Exception as login_err:
             print(f"   ❌ Login verification failed: {login_err}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()
