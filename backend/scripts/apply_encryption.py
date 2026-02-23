"""
Apply Encryption
Sweeps the database for unencrypted sensitive values and encrypts them at rest.
Run this script once after generating a new ENCRYPTION_KEY in your .env
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add backend to path so we can import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.encryption import encrypt_value

load_dotenv()

def sweep_and_encrypt():
    url: str = os.getenv("SUPABASE_URL")
    key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Supabase credentials not found in .env")
        sys.exit(1)
        
    if not os.getenv("ENCRYPTION_KEY"):
        print("❌ ENCRYPTION_KEY not found in .env. Please generate one first.")
        from utils.encryption import generate_key
        print(f"Example key: {generate_key()}")
        sys.exit(1)

    supabase: Client = create_client(url, key)
    
    print("🔍 Sweeping `linkedin_question_bank` for unencrypted sensitive data...")
    
    # Target categories that contain sensitive data
    sensitive_cats = ['salary', 'visa', 'sensitive']
    
    try:
        res = supabase.table("linkedin_question_bank").select("id, answer_text, category").in_("category", sensitive_cats).execute()
        rows = res.data
        
        if not rows:
            print("No sensitive records found.")
            return

        encrypted_count = 0
        for row in rows:
            ans = row.get("answer_text")
            # Basic check: Fernet tokens usually start with gAAAAA
            if ans and not ans.startswith("gAAAAA"):
                print(f"🔒 Encrypting record ID: {row['id']}")
                safe_val = encrypt_value(ans)
                supabase.table("linkedin_question_bank").update({
                    "answer_text": safe_val
                }).eq("id", row['id']).execute()
                encrypted_count += 1
                
        print(f"✅ Successfully encrypted {encrypted_count} records.")

    except Exception as e:
        print(f"❌ Error during sweep: {e}")

if __name__ == "__main__":
    sweep_and_encrypt()
