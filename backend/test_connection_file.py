
import sys
import socket

def log(msg):
    with open("backend/connection_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

log("Starting test...")

url = "https://kstqpyyvziyetokwvggf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzdHFweXl2eml5ZXRva3d2Z2dmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDc0MTI4MywiZXhwIjoyMDg2MzE3MjgzfQ.iCdQwmcs2y0HdqnDQYLx_HklO0JR8BCz-tiSrBouTgM"

try:
    log(f"Testing URL: {url}")
    hostname = "kstqpyyvziyetokvwggf.supabase.co"
    log(f"Resolving {hostname}...")
    ip = socket.gethostbyname(hostname)
    log(f"Resolved to {ip}")
except Exception as e:
    log(f"DNS FAIL: {e}")

try:
    from supabase import create_client
    log("Supabase import ok")
    client = create_client(url, key)
    log("Client created")
    log("Listing buckets...")
    buckets = client.storage.list_buckets()
    log(f"Buckets: {[b.name for b in buckets]}")
except Exception as e:
    log(f"Supabase FAIL: {e}")
    import traceback
    traceback.print_exc() # Try distinct
