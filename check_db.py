import os
from dotenv import load_dotenv
from supabase import create_client

# Load from backend directory
load_dotenv('backend/.env')

# Or try frontend if backend fails
if not os.environ.get('NEXT_PUBLIC_SUPABASE_URL'):
    load_dotenv('frontend/.env.local')

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
key = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')

if not url:
    print("FATAL: Could not find Supabase URL in .env files.")
    exit(1)

print(f"Connecting to: {url}...")
supabase = create_client(url, key)

res = supabase.table('applications').select('*').order('created_at', desc=True).limit(5).execute()

import json
print("\n--- LAST 5 APPLICATIONS ---")
print(json.dumps(res.data, indent=2))
