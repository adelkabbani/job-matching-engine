import sys
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load env vars
load_dotenv()

# Setup logging
log_path = Path(__file__).parent.parent / ".tmp" / "scrape_linkedin.log"
def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

log("Starting scrape_linkedin.py...")

def load_profile():
    path = Path(__file__).parent.parent / ".tmp" / "user_profile.json"
    if not path.exists():
        log("Profile not found. Please run ingest_cv.py first.")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_search_queries(profile):
    """Get AI generated queries or fallback to manual build."""
    prefs = profile.get("preferences", {})
    queries = prefs.get("search_queries", [])
    
    if queries:
        return queries
        
    # Fallback to simple builder if no AI keywords found
    log("⚠️ No AI keywords found. Using fallback builder.")
    skills = profile.get("skills", [])
    top_skills = skills[:3] if skills else ["Software Engineer"]
    skills_query = " OR ".join([f'"{s}"' for s in top_skills])
    location = "Berlin" 
    exp_level = profile.get("experience_level", "Entry Level")
    level_kw = '("Intern" OR "Junior" OR "Trainee" OR "Entry Level")' if "Experienced" not in exp_level else ""
    
    return [f'site:linkedin.com/jobs ({skills_query}) "{location}" {level_kw}']

def scrape_linkedin_jobs(queries):
    """Use Firecrawl Search to find LinkedIn jobs for multiple queries."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        log("Error: FIRECRAWL_API_KEY not set.")
        return []
        
    url = "https://api.firecrawl.dev/v1/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    all_results = []
    
    for query in queries:
        # Enforce Berlin if missing (Safety check)
        if "berlin" not in query.lower():
            query += " Berlin"
            
        log(f"🔍 Searching: {query}")
        
        payload = {
            "query": query,
            "limit": 5, 
            "scrapeOptions": {
                "formats": ["markdown"]
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 429:
                log("Rate limited. Waiting 10s...")
                time.sleep(10)
                response = requests.post(url, json=payload, headers=headers)
                
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                for item in data.get("data", []):
                    title_company = item.get("title", "").split(" | ")[0]
                    parts = title_company.split(" - ")
                    
                    title = parts[0] if parts else "Unknown Role"
                    company = parts[1] if len(parts) > 1 else "Unknown Company"
                    
                    job = {
                        "title": title,
                        "company": company,
                        "link": item.get("url"),
                        "description": item.get("description", "")[:500] + "...", # Capture more for filtering
                        "source": "LinkedIn",
                        "date_posted": "Recent",
                        "location": "Berlin", # We enforced this in query
                        "query_used": query
                    }
                    
                    if "/jobs/view/" in job["link"] or "/jobs/" in job["link"]:
                         all_results.append(job)
                         
            time.sleep(2) # Be polite
            
        except Exception as e:
            log(f"Firecrawl Search Failed for '{query}': {e}")
            
    return all_results

if __name__ == "__main__":
    profile = load_profile()
    queries = get_search_queries(profile)
    
    # Cap queries to avoid burning credits
    if len(queries) > 5:
        queries = queries[:5]
        
    jobs = scrape_linkedin_jobs(queries)
    
    log(f"Found {len(jobs)} total jobs.")
    
    output_path = Path(__file__).parent.parent / ".tmp" / "jobs_found.json"
    
    existing_jobs = []
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            try:
                existing_jobs = json.load(f)
            except: pass
            
    existing_links = {j.get("link") for j in existing_jobs}
    
    new_count = 0
    for job in jobs:
        if job["link"] not in existing_links:
            existing_jobs.append(job)
            new_count += 1
            
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_jobs, f, indent=2, ensure_ascii=False)
        
    log(f"Added {new_count} new jobs to {output_path}")


# Setup logging
log_path = Path(__file__).parent.parent / ".tmp" / "scrape_linkedin.log"
def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

log("Starting scrape_linkedin.py...")

def load_profile():
    path = Path(__file__).parent.parent / ".tmp" / "user_profile.json"
    if not path.exists():
        log("Profile not found. Please run ingest_cv.py first.")
        sys.exit(1)
    with open(path, 'r') as f:
        return json.load(f)

def build_search_query(profile):
    """Build a targeted search query based on profile data."""
    skills = profile.get("skills", [])
    exp_level = profile.get("experience_level", "Experienced")
    
    # Get top 3 skills to avoid query getting too long
    top_skills = skills[:3] if skills else ["Software Engineer"]
    skills_query = " OR ".join([f'"{s}"' for s in top_skills])
    
    # Location (Default to Berlin/Germany as per user request, or from config if available)
    # The user mentioned "Germany berlin" in the prompt.
    location = "Berlin" 
    
    # Experience Level Keywords
    level_kw = ""
    if exp_level == "Fresher":
        level_kw = '("Intern" OR "Junior" OR "Trainee" OR "Entry Level")'
    else:
        # For experienced, maybe exclude intern
        level_kw = '-Intern -Student'
        
    query = f'site:linkedin.com/jobs ({skills_query}) "{location}" {level_kw}'
    return query

def scrape_linkedin_jobs(query):
    """Use Firecrawl Search to find LinkedIn jobs."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        log("Error: FIRECRAWL_API_KEY not set.")
        return []
        
    url = "https://api.firecrawl.dev/v1/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    payload = {
        "query": query,
        "limit": 5, # Start small
        "scrapeOptions": {
            "formats": ["markdown"]
        }
    }
    
    log(f"Searching: {query}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if data.get("success"):
            for item in data.get("data", []):
                # Basic parsing of search result
                # LinkedIn titles often look like "Role - Company | LinkedIn"
                title_company = item.get("title", "").split(" | ")[0]
                parts = title_company.split(" - ")
                
                title = parts[0] if parts else "Unknown Role"
                # Sometimes company is in description or second part of title
                company = parts[1] if len(parts) > 1 else "Unknown Company"
                
                job = {
                    "title": title,
                    "company": company,
                    "link": item.get("url"),
                    "description": item.get("description", "")[:200] + "...",
                    "source": "LinkedIn",
                    "date_posted": "Recent", # Search results might not have precise date
                    "location": "Berlin" # Assumed from query
                }
                
                # Filter out non-job pages (e.g. profiles)
                if "/jobs/view/" in job["link"] or "/jobs/" in job["link"]:
                     results.append(job)
        
        return results
        
    except Exception as e:
        log(f"Firecrawl Search Failed: {e}")
        return []

if __name__ == "__main__":
    profile = load_profile()
    query = build_search_query(profile)
    
    jobs = scrape_linkedin_jobs(query)
    
    log(f"Found {len(jobs)} jobs.")
    
    # Append to jobs_found.json
    output_path = Path(__file__).parent.parent / ".tmp" / "jobs_found.json"
    
    existing_jobs = []
    if output_path.exists():
        with open(output_path, 'r') as f:
            try:
                existing_jobs = json.load(f)
            except: pass
            
    # Simple dedup based on link
    existing_links = {j.get("link") for j in existing_jobs}
    
    new_count = 0
    for job in jobs:
        if job["link"] not in existing_links:
            existing_jobs.append(job)
            new_count += 1
            
    with open(output_path, 'w') as f:
        json.dump(existing_jobs, f, indent=2)
        
    log(f"Added {new_count} new jobs to {output_path}")
