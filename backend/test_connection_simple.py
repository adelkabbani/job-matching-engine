import sys
import socket
print("Starting test...", file=sys.stderr)

url = "https://kstqpyyvziyetokvwggf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzdHFweXl2eml5ZXRva3d2Z2dmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDc0MTI4MywiZXhwIjoyMDg2MzE3MjgzfQ.iCdQwmcs2y0HdqnDQYLx_HklO0JR8BCz-tiSrBouTgM"

try:
    print(f"Testing URL: {url}", file=sys.stderr)
    hostname = "kstqpyyvziyetokvwggf.supabase.co"
    print(f"Resolving {hostname}...", file=sys.stderr)
    ip = socket.gethostbyname(hostname)
    print(f"Resolved to {ip}", file=sys.stderr)
except Exception as e:
    print(f"DNS FAIL: {e}", file=sys.stderr)

try:
    from supabase import create_client
    print("Supabase import ok", file=sys.stderr)
    client = create_client(url, key)
    print("Client created", file=sys.stderr)
    print("Listing buckets...", file=sys.stderr)
    buckets = client.storage.list_buckets()
    print(f"Buckets: {[b.name for b in buckets]}", file=sys.stderr)
except Exception as e:
    print(f"Supabase FAIL: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
