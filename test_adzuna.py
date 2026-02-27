import os
import requests
from dotenv import load_dotenv

# 1. Force the .env override to read exactly what the backend sees
load_dotenv('backend/.env', override=True)

app_id = os.getenv("ADZUNA_APP_ID", "").strip().replace('"', '').replace("'", "")
app_key = os.getenv("ADZUNA_APP_KEY", "").strip().replace('"', '').replace("'", "")

print("-" * 40)
print(f"Loaded ID:  '{app_id[:4]}...' (Total Length: {len(app_id)})")
print(f"Loaded Key: '{app_key[:4]}...' (Total Length: {len(app_key)})")
print("-" * 40)

if not app_id or not app_key:
    print("❌ ERROR: The keys are physically missing or failing to load from backend/.env!")
    exit(1)

# 2. Replicate the precise Adzuna API call from job_discovery.py
url = "https://api.adzuna.com/v1/api/jobs/de/search/1"
params = {
    'app_id': app_id,
    'app_key': app_key,
    'results_per_page': 5,
    'what': 'python',
    'where': 'Berlin',
    'content-type': 'application/json'
}

print("Sending test request to Adzuna API...")
try:
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        jobs = data.get('results', [])
        print(f"\n✅ API SUCCESS: Adzuna returned {len(jobs)} brand new jobs!")
        for j in jobs[:3]:
            print(f"  - {j.get('title')}")
    else:
        print(f"\n❌ API BOUNCED (Status {response.status_code})")
        print(f"ADZUNA SAID: {response.text}")
        print("This is exactly why you aren't seeing new links. Adzuna is rejecting your keys/IP.")
except Exception as e:
    print(f"\n❌ NETWORK ERROR: {e}")
