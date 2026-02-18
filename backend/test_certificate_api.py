"""
Test if the certificate API endpoint is working
"""
import requests
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("🧪 Testing Certificate API Endpoint")
print("=" * 60)
print()

# Get a test user token
print("1. Getting user session...")
# You'll need to replace this with actual user auth
# For now, let's just check if the endpoint exists

print()
print("2. Testing GET /api/me/certificates endpoint...")
print()

# Try to call the endpoint (this will fail without auth, but we can see if it exists)
try:
    response = requests.get("http://localhost:8000/api/me/certificates")
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 401:
        print("   ✅ Endpoint exists (needs authentication)")
    elif response.status_code == 200:
        print("   ✅ Endpoint working!")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ⚠️  Unexpected status: {response.text}")
except requests.exceptions.ConnectionError:
    print("   ❌ Backend not running! Start it with: python main.py")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 60)
print()
print("🔍 Debugging Checklist:")
print()
print("1. ✅ Backend running? (python main.py)")
print("2. ✅ Frontend running? (npm run dev)")
print("3. ✅ Browser console errors? (F12 → Console)")
print("4. ✅ Network tab shows API call? (F12 → Network → filter 'certificates')")
print()
