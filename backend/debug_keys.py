import os
import json
import base64
from dotenv import load_dotenv
from supabase import create_client

# Explicitly load from backend/.env
load_dotenv(dotenv_path="backend/.env")

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_KEY")

print(f"--- DEBUG SUPABASE KEYS ---")
print(f"URL: {URL}")
if KEY:
    print(f"KEY (First 10): {KEY[:10]}...")
    print(f"KEY (Last 5): ...{KEY[-5:]}")
    
    # Decode JWT (Middle part)
    try:
        header, payload, sig = KEY.split('.')
        # Padding fix
        payload += '=' * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        print(f"JWT ROLE: {decoded.get('role')}")
        print(f"JWT EXP: {decoded.get('exp')}")
        print(f"JWT REF: {decoded.get('ref')}")
    except Exception as e:
        print(f"❌ Could not decode JWT: {e}")
else:
    print("❌ NO KEY FOUND")

if not KEY: exit()

print(f"\n--- TESTING CONNECTION ---")
client = create_client(URL, KEY)

# 1. Test Auth Admin (List Users)
print("1. Testing Admin List Users...")
try:
    users = client.auth.admin.list_users()
    print(f"✅ Success! Found {len(users)} users.")
except Exception as e:
    print(f"❌ FAILED: {e}")

# 2. Test RLS Bypass (Select All)
print("\n2. Testing RLS Bypass (Select All Docs)...")
try:
    res = client.table("documents").select("*", count="exact").execute()
    print(f"✅ Success! Found {len(res.data)} docs.")
except Exception as e:
    print(f"❌ FAILED: {e}")

# 3. Test Insert (RLS check)
print("\n3. Testing Insert (Ghost Doc)...")
import uuid
import time
try:
    # Use random user_id (Expect FK error if RLS passes, or Success if no FK)
    # If Error is 42501 (RLS), then Policy Failed.
    # If Error is 23503 (FK), then Policy PASSED.
    doc = {
        "user_id": str(uuid.uuid4()),
        "doc_type": "cv",
        "original_filename": "debug.txt",
        "storage_path": f"debug/{int(time.time())}.txt"
    }
    res = client.table("documents").insert(doc).execute()
    print(f"✅ Success! Inserted doc {res.data[0]['id']}")
except Exception as e:
    msg = str(e)
    if "42501" in msg or "row-level security" in msg:
        print(f"❌ FAILED: RLS Violation (Policy didn't match service_role)")
    elif "23503" in msg or "foreign key" in msg:
        print(f"✅ SUCCESS (Technically): RLS Passed! (Blocked by Foreign Key as expected)")
    else:
        print(f"❌ FAILED: {e}")
