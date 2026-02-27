"""
Job discovery service.
Interfaces with public job APIs (Adzuna) to find jobs based on user profile.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Absolute path loading
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True) # Override=True is critical!

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "").strip().replace('"', '').replace("'", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip().replace('"', '').replace("'", "")

if not ADZUNA_APP_ID:
    print(f"DEBUG: Attempted to load from: {env_path.absolute()}")
    print("CRITICAL: ADZUNA_APP_ID is still empty after stripping!")

import requests
from typing import List, Dict, Tuple
from services.job_scraper import apply_filters
from services.job_matcher import get_user_skills, extract_skills_from_description, generate_match_report

# Constants
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/de/search"  # Focus on Germany


def search_jobs(query: str, location: str = "Berlin") -> List[Dict]:
    """
    Search jobs using Adzuna API across multiple pages.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("⚠️ ADZUNA_APP_ID or ADZUNA_APP_KEY not found. Using MOCK data.")
        return get_mock_jobs(location)
        
    jobs = []
    
    # Loop to fetch Pages 1, 2, and 3 instead of just 1
    for page in range(1, 4):
        params = {
            'app_id': ADZUNA_APP_ID,
            'app_key': ADZUNA_APP_KEY,
            'results_per_page': 20, # 60 jobs total
            'what': query,
            'where': location,
            'content-type': 'application/json'
        }
        
        try:
            print(f"DEBUG: Fetching Adzuna Page {page} for query '{query}' in '{location}'...")
            response = requests.get(f"{ADZUNA_BASE_URL}/{page}", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            page_results = data.get('results', [])
            if not page_results:
                break # No more results from Adzuna
                
            for result in page_results:
                job = {
                    'title': result.get('title'),
                    'company': result.get('company', {}).get('display_name'),
                    'description': result.get('description'),
                    'url': result.get('redirect_url'),
                    'location': result.get('location', {}).get('display_name'),
                    'remote_ok': 'remote' in (result.get('description') or '').lower() or 'remote' in (result.get('title') or '').lower(),
                    'language': 'english', 
                    'experience_level': 'mid', 
                    'source': 'adzuna'
                }
                jobs.append(job)
                
        except Exception as e:
            print(f"Error during Adzuna search on page {page}: {e}")
            if not jobs:
                return get_mock_jobs(location)
            break
            
    return jobs

def get_mock_jobs(location: str):
    """Return realistic mock engineering jobs matching the user profile."""
    return [
        {
            'title': 'Telecommunications Data Engineer',
            'company': 'Deutsche Telekom',
            'description': 'We are looking for a Telecommunications Data Engineer to join our Network Analytics team in Berlin. You will work with LTE, 5G, and VoIP network data, building ETL pipelines in Python and SQL. Experience with network performance monitoring and data warehousing (Snowflake, dbt) is critical. English is required.',
            'url': 'https://example.com/job-telecom1',
            'location': location,
            'remote_ok': False,
            'language': 'english',
            'experience_level': 'mid',
            'source': 'mock'
        },
        {
            'title': 'Network Data Analyst',
            'company': 'Vodafone Germany GmbH',
            'description': 'Vodafone is hiring a Network Data Analyst with expertise in network monitoring, KPI dashboarding, and Tableau. Must have Python and SQL skills. Experience with Cisco routers and MPLS networks is a strong plus. English language required.',
            'url': 'https://example.com/job-network1',
            'location': location,
            'remote_ok': True,
            'language': 'english',
            'experience_level': 'mid',
            'source': 'mock'
        },
        {
            'title': 'Data Engineer (Network Intelligence)',
            'company': 'Ericsson',
            'description': 'Ericsson seeks a Data Engineer to build advanced analytics pipelines for our 5G rollout. You will use Spark, Airflow, and Databricks. Strong SQL and Python skills are essential. Knowledge of telecom signaling (SS7, Diameter) is beneficial. English required.',
            'url': 'https://example.com/job-data-eng1',
            'location': location,
            'remote_ok': True,
            'language': 'english',
            'experience_level': 'mid',
            'source': 'mock'
        }
    ]

def discover_and_score_jobs(user_id: str, supabase) -> Dict:
    """
    Primary discovery function for a user.
    Uses user settings to search, filter, and score jobs.
    """
    try:
        # 1. Fetch user filter settings
        try:
            filters_res = supabase.table("job_filters")\
                .select("*")\
                .eq("user_id", user_id)\
                .limit(1)\
                .execute()
                
            user_filters = filters_res.data[0] if filters_res.data else {}
        except Exception as e:
            print(f"Error fetching filters: {e}")
            user_filters = {}

        # 1.5. Merge LLM keywords from user_profile.json if available
        try:
            from pathlib import Path
            import json
            profile_path = Path(__file__).parent.parent.parent / ".tmp" / "user_profile.json"
            if profile_path.exists():
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                    # Support both list formats and string formats
                    queries = profile_data.get("preferences", {}).get("search_queries", [])
                    if queries:
                        if isinstance(queries, str):
                            user_filters["role_keywords"] = [queries]
                        else:
                            user_filters["role_keywords"] = queries
                        print(f"DEBUG: Loaded LLM keywords from profile: {queries}")
        except Exception as json_e:
            print(f"Error reading user_profile.json: {json_e}")

        # Default filters if missing — PHASE 3: Broadened for Telecommunications & Data Engineering
        if not user_filters:
            user_filters = {
                'role_keywords': [
                    'Telecommunications Engineer',
                    'Network Data Analyst',
                    'Telecommunications Data Engineer',
                    'Network Analyst',
                    'Data Engineer',
                    'Data Analyst'
                ],
                'locations': ['Berlin'],
                'languages': ['english'],
                'experience_levels': ['mid', 'junior', 'senior']  # Allow junior engineering roles
            }
            
        # 2. Search for jobs (one search per keyword per location for now)
        all_found_jobs = []
        
        # Determine keywords to search
        keyword_list = user_filters.get('role_keywords', [
            'Telecommunications Engineer',
            'Network Analyst',
            'Data Engineer',
            'Data Analyst'
        ])
        
        locations = user_filters.get('locations', ['Berlin'])
        
        for loc in locations:
            for kw in keyword_list[:5]:  # Allow up to 5 keywords for better coverage
                # Strip out hallucinated locations from the LLM keyword so Adzuna actually finds jobs
                import re
                clean_kw = re.sub(r'(?i)\b(remote|san francisco|new york city|new york|berlin|london)\b', '', kw).strip()
                # Further compress multiple spaces
                clean_kw = re.sub(r'\s+', ' ', clean_kw)
                     
                print(f"DEBUG: Searching API natively for keyword: '{clean_kw}' in {loc} (Original LLM Keyword: '{kw}')")
                found = search_jobs(clean_kw, loc)
                all_found_jobs.extend(found)
            
        if not all_found_jobs:
            return {"status": "success", "count": 0, "message": "No jobs found or missing API keys"}
            
        # 2.5 Filter duplicates (Python side because 'url' column is missing)
        existing_jobs = supabase.table("jobs").select("raw_data").eq("user_id", user_id).execute()
        existing_urls = set()
        if existing_jobs.data:
            for row in existing_jobs.data:
                if row.get('raw_data') and row['raw_data'].get('url'):
                    existing_urls.add(row['raw_data']['url'])
        
        unique_jobs = []
        for job in all_found_jobs:
            if job['url'] not in existing_urls:
                unique_jobs.append(job)
                existing_urls.add(job['url']) # Prevent duplicates within the batch
        
        all_found_jobs = unique_jobs
        
        # 3. Process and Score each job
        user_skills = get_user_skills(supabase, user_id)
        new_jobs_count = 0
        
        for job_data in all_found_jobs:
            try:
                # PHASE 3: German Language Detection
                # Skip jobs where the description is primarily in German 
                # (unless English is explicitly required as well)
                description = job_data.get('description', '') or ''
                desc_lower = description.lower()
                
                german_markers = [
                    'wir suchen', 'aufgaben:', 'anforderungen:', 'dein profil',
                    'deine aufgaben', 'was wir bieten', 'stellenbeschreibung',
                    'bewerbung', 'kenntnisse', 'erfahrung', 'berufserfahrung',
                    'deutschkenntnisse', 'arbeitsort', 'vollzeit', 'teilzeit'
                ]
                english_required_markers = ['english required', 'english is required', 'english mandatory',
                                            'business english', 'proficient in english']
                
                is_primarily_german = sum(1 for m in german_markers if m in desc_lower) >= 3
                english_also_required = any(m in desc_lower for m in english_required_markers)
                
                if is_primarily_german and not english_also_required:
                    print(f"⏭️ SKIP (German-only job detected): {job_data.get('title')} @ {job_data.get('company')}")
                    continue
                    
                # PHASE 3: Mark job level correctly — don't penalize engineer roles labeled 'junior'
                # If the title contains an engineering specialty, it's a valid mid-level role 
                engineering_titles = ['engineer', 'analyst', 'developer', 'architect', 'data', 'network', 'telecom']
                if job_data.get('experience_level') == 'junior':
                    title_lower = (job_data.get('title') or '').lower()
                    if any(t in title_lower for t in engineering_titles):
                        job_data['experience_level'] = 'mid'  # Promote to mid for engineering roles
                
                # Apply filters
                passes, reason = apply_filters(job_data, user_filters)
                
                # Scoring logic
                required_skills, optional_skills = extract_skills_from_description(job_data['description'])
                match_report = generate_match_report(user_skills, required_skills, optional_skills)
                
                # Prepare DB record
                job_record = {
                    'user_id': user_id,
                    'title': job_data['title'],
                    'company': job_data['company'],
                    'description': job_data['description'],
                    'job_url': job_data.get('url'),
                    'source': 'adzuna',
                    'location': job_data['location'],
                    'remote_ok': job_data['remote_ok'],
                    'language': job_data['language'],
                    'experience_level': job_data['experience_level'],
                    'match_score': match_report['match_score'],
                    'matched_skills': match_report['matched_skills'],
                    'missing_skills': match_report['missing_skills'],
                    'strengths_summary': match_report['strengths_summary'],
                    'filtered_out': not passes,
                    'filter_reason': None if passes else reason,
                    'raw_data': job_data,
                    'status': 'scraped'
                }
                
                supabase.table("jobs").insert(job_record).execute()
                new_jobs_count += 1
            except Exception as inner_e:
                import traceback
                print(f"==================================================")
                print(f"CRITICAL ERROR SAVING JOB TO SUPABASE:")
                print(f"Title: {job_data.get('title')}")
                print(f"Company: {job_data.get('company')}")
                print(f"Exception: {inner_e}")
                traceback.print_exc()
                print(f"==================================================")
                continue
            
        return {
            "status": "success",
            "count": new_jobs_count,
            "message": f"Discovered {new_jobs_count} new jobs"
        }

    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Discovery failed: {str(e)}",
            "trace": traceback.format_exc()
        }
