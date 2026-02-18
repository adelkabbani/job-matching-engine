import requests
from bs4 import BeautifulSoup
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def scrape_jobs(keyword, location="remote"):
    """
    Scrape jobs using Firecrawl API for reliability.
    Falls back to basic requests if Firecrawl is not available.
    """
    base_url = "https://techjobsforgood.com/jobs/"
    params = {
        "q": keyword,
        "locations": location
    }
    
    # Build the full search URL
    search_url = f"{base_url}?q={keyword.replace(' ', '+')}&locations={location.replace(' ', '+')}"
    
    print(f"Searching for '{keyword}' in '{location}'...")
    print(f"URL: {search_url}")
    
    # Try Firecrawl first (if environment variable is set)
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    
    if firecrawl_api_key:
        try:
            print(f"Using Firecrawl API for extraction (Key length: {len(firecrawl_api_key)})...")
            return scrape_with_firecrawl(search_url, keyword)
        except Exception as e:
            print(f"Firecrawl failed: {e}, falling back to basic scraping...")
            import traceback
            traceback.print_exc()
    
    # Fallback to basic requests
    return scrape_with_requests(search_url)


def scrape_with_firecrawl(url, keyword):
    """Use Firecrawl API to extract job listings."""
    import requests as req
    
    api_key = os.getenv("FIRECRAWL_API_KEY")
    api_url = "https://api.firecrawl.dev/v1/extract"
    
    print(f"Calling Firecrawl API: {api_url}")
    print(f"Target URL: {url}")
    
    payload = {
        "urls": [url],
        "prompt": f"Extract all {keyword} job listings. For each job, get the title, company, location, and the full link to the job post. Return a list of jobs.",
        "schema": {
            "type": "object",
            "properties": {
                "jobs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "company": {"type": "string"},
                            "location": {"type": "string"},
                            "link": {"type": "string"}
                        },
                        "required": ["title", "company", "link"]
                    }
                }
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = req.post(api_url, json=payload, headers=headers)
        print(f"Firecrawl Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Firecrawl Error Response: {response.text}")
            response.raise_for_status()
        
        data = response.json()
        print(f"Firecrawl Response Data Keys: {data.keys()}")
        
        if not data.get("success"):
             print(f"Firecrawl reported failure: {data}")
        
        jobs = data.get("data", {}).get("jobs", [])
        print(f"Extracted {len(jobs)} jobs from Firecrawl")
        
        # Add source field
        for job in jobs:
            job["source"] = "Tech Jobs for Good"
        
        return jobs
        
    except Exception as e:
        print(f"Error during Firecrawl request: {e}")
        raise e


def scrape_with_requests(url):
    """Basic fallback scraping using requests + BeautifulSoup."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    
    # Based on investigation, job cards use structure:
    # a.content contains the link and wraps company/location
    for a in soup.select('a.content'):
        href = a.get('href', '')
        if not href:
            continue
            
        full_link = "https://techjobsforgood.com" + href if href.startswith("/") else href
        
        # The title isn't directly in the card according to agent, 
        # but let's see if we can find it in the content text
        content_text = a.get_text(separator="|").strip()
        lines = [l.strip() for l in content_text.split("|") if l.strip()]
        
        # Heuristic: First line might be company if title is missing
        company_tag = a.select_one('span.company_name')
        location_tag = a.select_one('span.location')
        
        company = company_tag.text.strip() if company_tag else (lines[0] if lines else "Unknown")
        loc = location_tag.text.strip() if location_tag else "Remote"
        
        # If the agent said title is missing from card, let's use a placeholder or follow the link
        # For now, let's assume the first non-company/non-location string is descriptive
        title = "Software Role" # Default
        for line in lines:
            if line != company and line != loc:
                title = line
                break

        job = {
            "title": title,
            "company": company,
            "location": loc,
            "link": full_link,
            "source": "Tech Jobs for Good"
        }
        
        if not any(j['link'] == job['link'] for j in jobs):
            jobs.append(job)
    
    return jobs

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scrape_techforgood.py <keyword> [location]")
        sys.exit(1)
        
    keyword = sys.argv[1]
    location = sys.argv[2] if len(sys.argv) > 2 else "remote"
    
    output_dir = os.path.join(os.path.dirname(__file__), "..", ".tmp")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "jobs_found.json")
    
    try:
        results = scrape_jobs(keyword, location)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Found {len(results)} jobs. Results saved to {output_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
