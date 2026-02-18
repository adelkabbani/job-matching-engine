"""
Migration Helper: Apply 010_certificate_structured_data.sql

This script guides you through applying the certificate_structured_data table migration.
Since Supabase-py doesn't support DDL execution, you must run the SQL manually.
"""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SUPABASE_URL:
    print("❌ Error: SUPABASE_URL not found in .env")
    exit(1)

# Extract project ID from URL
project_id = SUPABASE_URL.split("//")[1].split(".")[0]

print("=" * 60)
print("📋 Migration 010: Certificate Structured Data Table")
print("=" * 60)
print()
print("⚠️  This migration creates the 'certificate_structured_data' table")
print("    to store AI-extracted certificate information.")
print()
print("🔗 Steps to Apply:")
print()
print(f"1. Open Supabase SQL Editor:")
print(f"   https://supabase.com/dashboard/project/{project_id}/sql/new")
print()
print("2. Copy the contents of:")
print("   backend/migrations/010_certificate_structured_data.sql")
print()
print("3. Paste into the SQL Editor and click 'Run'")
print()
print("4. Verify the table was created:")
print("   - Check Table Editor for 'certificate_structured_data'")
print("   - Confirm RLS policies are enabled")
print()
print("=" * 60)
print()

# Read and display the migration file
migration_path = os.path.join(os.path.dirname(__file__), "migrations", "010_certificate_structured_data.sql")

if os.path.exists(migration_path):
    print("📄 Migration SQL Preview:")
    print("-" * 60)
    with open(migration_path, 'r') as f:
        print(f.read())
    print("-" * 60)
else:
    print("⚠️  Migration file not found at:", migration_path)

print()
print("✅ After running the migration, you can:")
print("   - Upload certificates via the dashboard")
print("   - Click 'Analyze Certificate' to extract structured data")
print("   - View certificate details (title, issuer, date, skills)")
print()
