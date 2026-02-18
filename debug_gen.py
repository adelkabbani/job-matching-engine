import json
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse

print("Imports worked")

try:
    with open(".tmp/jobs_filtered.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} jobs")
except Exception as e:
    print(f"Error loading jobs: {e}")

try:
    with open(".tmp/user_profile.json", "r", encoding="utf-8") as f:
        profile = json.load(f)
    print("Loaded profile")
except Exception as e:
    print(f"Error loading profile: {e}")
