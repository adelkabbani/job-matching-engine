"""
Check how many certificates are actually in the database for the current user
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

print("🔍 Checking Certificate Count in Database")
print("=" * 60)
print()

# Count all certificates
all_certs = supabase.table("documents")\
    .select("id, user_id, original_filename, created_at", count="exact")\
    .eq("doc_type", "certificate")\
    .execute()

total_count = all_certs.count if hasattr(all_certs, 'count') else len(all_certs.data)

print(f"📊 Total certificates in database: {total_count}")
print()

if all_certs.data and len(all_certs.data) > 0:
    print("📋 Sample certificates:")
    for cert in all_certs.data[:5]:  # Show first 5
        print(f"  - {cert['original_filename']} (User: {cert['user_id'][:8]}...)")
    print()
    
    # Group by user
    user_counts = {}
    for cert in all_certs.data:
        user_id = cert['user_id']
        user_counts[user_id] = user_counts.get(user_id, 0) + 1
    
    print(f"👥 Certificates by user:")
    for user_id, count in user_counts.items():
        print(f"  User {user_id[:8]}...: {count} certificates")
    print()

print("=" * 60)
print()
print("💡 If you want to delete ALL certificates, run:")
print("   python cleanup_certificates.py")
print()
