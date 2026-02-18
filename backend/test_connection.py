
import os
from dotenv import load_dotenv
from supabase import create_client
import sys
import socket

# Load .env explicitly from the same directory
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"Loaded URL: {url}")
if not url:
    print("Error: SUPABASE_URL not found in environment!")
    sys.exit(1)

# Extract hostname
if "://" in url:
    hostname = url.split("://")[1].split("/")[0]
else:
    hostname = url.split("/")[0]

print(f"Resolving hostname: {hostname}")

try:
    ip = socket.gethostbyname(hostname)
    print(f"Resolved to IP: {ip}")
except Exception as e:
    print(f"DNS Resolution Failed: {e}")
    sys.exit(1)

try:
    print("Initializing Supabase client...")
    supabase = create_client(url, key)
    print("Client initialized.")
    
    print("Listing buckets...")
    buckets = supabase.storage.list_buckets()
    bucket_names = [b.name for b in buckets]
    print(f"Success! Found buckets: {bucket_names}")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Supabase Connection Failed: {e}")
