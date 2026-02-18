"""
Script to clean up duplicate certificate uploads
This will help you start fresh with a clean database
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

print("🗑️  Certificate Cleanup Script")
print("=" * 60)
print()

# Count certificates
docs = supabase.table("documents")\
    .select("id", count="exact")\
    .eq("doc_type", "certificate")\
    .execute()

total = docs.count if hasattr(docs, 'count') else len(docs.data)

print(f"Found {total} certificates in database")
print()
print("⚠️  WARNING: This will DELETE ALL certificates!")
print()

confirm = input("Type 'DELETE ALL' to confirm: ")

if confirm == "DELETE ALL":
    print()
    print("🗑️  Deleting all certificates...")
    
    # Delete all certificate documents
    result = supabase.table("documents")\
        .delete()\
        .eq("doc_type", "certificate")\
        .execute()
    
    print(f"✅ Deleted {len(result.data) if result.data else 'all'} certificates")
    print()
    print("✨ Database is now clean. You can upload fresh certificates.")
else:
    print()
    print("❌ Cancelled. No certificates were deleted.")
