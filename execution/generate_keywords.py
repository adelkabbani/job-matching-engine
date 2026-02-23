import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
log_path = Path(__file__).parent.parent / ".tmp" / "generate_keywords.log"
def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

log("Starting generate_keywords.py...")

try:
    # Import LLM service
    sys.path.append(str(Path(__file__).parent.parent))
    from backend.services.llm import generate_search_keywords
    log("Imports successful.")
except Exception as e:
    log(f"Import Error: {e}")
    sys.exit(1)

def generate(profile_path):
    path = Path(profile_path)
    if not path.exists():
        log(f"Error: Profile not found: {profile_path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        profile = json.load(f)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        log("Error: OPENROUTER_API_KEY not found in .env")
        return

    log("Generating smart search keywords...")
    try:
        keywords = generate_search_keywords(profile, api_key)
        log(f"✅ Generated {len(keywords)} keywords: {keywords}")
        
        # Save back to profile
        if "preferences" not in profile: profile["preferences"] = {}
        profile["preferences"]["search_queries"] = keywords
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
            
        log(f"Updated profile at {path}")
        
    except Exception as e:
        log(f"❌ Keyword Generation Failed: {e}")

if __name__ == "__main__":
    profile_path = Path(__file__).parent.parent / ".tmp" / "user_profile.json"
    generate(profile_path)
