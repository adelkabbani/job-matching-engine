import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path("backend/.env"))
db_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")

if not db_url:
    print("Database URL not found.")
    exit(1)

try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()

    sql = """
    CREATE TABLE IF NOT EXISTS public.cv_versions (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        user_id UUID NOT NULL,
        job_id UUID NOT NULL,
        tailored_content JSONB NOT NULL,
        keywords_found JSONB DEFAULT '[]'::jsonb,
        keywords_missing JSONB DEFAULT '[]'::jsonb,
        ats_score INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
    );
    """
    
    cursor.execute(sql)
    print("✅ Created cv_versions table successfully!")
    
except Exception as e:
    print(f"❌ Failed to create table: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
