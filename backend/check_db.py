
import os
from dotenv import load_dotenv
from supabase import create_client
import json
import sys

# Load .env
load_dotenv()

def log(msg):
    with open("backend/db_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear previous log
with open("backend/db_log.txt", "w", encoding="utf-8") as f:
    f.write("Starting DB Check...\n")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    log("Error: Credentials missing in .env")
    exit(1)

try:
    supabase = create_client(url, key)
    
    # Fetch all documents
    response = supabase.table("documents").select("*").execute()
    documents = response.data
    
    log(f"\n--- 📂 Found {len(documents)} Document(s) in DB ---")
    
    for doc in documents:
        log(f"\n📄 ID: {doc['id']}")
        log(f"   Name: {doc['original_filename']}")
        log(f"   Type: {doc['doc_type']}")
        log(f"   Path: {doc['storage_path']}")
        log(f"   Created: {doc['created_at']}")
        log("-" * 40)
        
except Exception as e:
    log(f"Error fetching data: {e}")
