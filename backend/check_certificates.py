"""
Quick test to verify certificate API endpoints are working
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing env vars")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("🔍 Checking for uploaded certificates...")
print()

# Check documents table
docs = supabase.table("documents")\
    .select("id, original_filename, doc_type, content_text")\
    .eq("doc_type", "certificate")\
    .execute()

if docs.data:
    print(f"✅ Found {len(docs.data)} certificate(s) in database:")
    print()
    for doc in docs.data:
        print(f"  📄 {doc['original_filename']}")
        print(f"     ID: {doc['id']}")
        print(f"     Has OCR text: {'Yes' if doc.get('content_text') else 'No'}")
        print()
else:
    print("⚠️  No certificates found in database")
    print()

print("=" * 60)
print()
print("🔧 Next Steps:")
print()
print("1. **Restart Frontend** (if not already running):")
print("   cd frontend")
print("   npm run dev")
print()
print("2. **Check browser console** for any errors")
print()
print("3. **Refresh the dashboard page**")
print()
print("The Certificate Analysis section should appear below Resume Preview")
print("if you have certificates uploaded.")
print()
