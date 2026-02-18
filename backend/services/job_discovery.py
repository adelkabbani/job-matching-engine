"""
Job discovery service.
Interfaces with public job APIs (Adzuna) to find jobs based on user profile.
"""
import os
import requests
from typing import List, Dict, Tuple
from services.job_scraper import apply_filters
from services.job_matcher import get_user_skills, extract_skills_from_description, generate_match_report

# Constants
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/de/search"  # Focus on Germany

def search_jobs(query: str, location: str = "Berlin") -> List[Dict]:
    """
    Search jobs using Adzuna API.
    
    Args:
        query: Search keywords
        location: Target location
        
    Returns:
        List of job data or empty list if failed/no keys
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("⚠️ ADZUNA_APP_ID or ADZUNA_APP_KEY not found. Using MOCK data.")
        return get_mock_jobs(location)
        
    params = {
        'app_id': ADZUNA_APP_ID,
        'app_key': ADZUNA_APP_KEY,
        'results_per_page': 20,
        'what': query,
        'where': location,
        'content-type': 'application/json'
    }
    
    try:
        response = requests.get(f"{ADZUNA_BASE_URL}/1", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for result in data.get('results', []):
            job = {
                'title': result.get('title'),
                'company': result.get('company', {}).get('display_name'),
                'description': result.get('description'),
                'url': result.get('redirect_url'),
                'location': result.get('location', {}).get('display_name'),
                'remote_ok': 'remote' in (result.get('description') or '').lower() or 'remote' in (result.get('title') or '').lower(),
                'language': 'english', # Heuristic: most data roles are English. Can improve with langdetect
                'experience_level': 'mid', # Default
                'source': 'adzuna'
            }
            jobs.append(job)
            
        return jobs
        
    except Exception as e:
        print(f"Error during Adzuna search: {e}")
        return get_mock_jobs(location)

def get_mock_jobs(location: str):
    """Return realistic mock jobs for testing/demo."""
    return [
        {
            'title': 'Senior Python Developer',
            'company': 'TechGenius GmbH',
            'description': 'We are looking for a Senior Python Developer with experience in FastAPI, Docker, and React. Must have strong SQL skills and experience with cloud platforms like AWS. Bonus points for Machine Learning knowledge.',
            'url': 'https://example.com/job1',
            'location': location,
            'remote_ok': True,
            'language': 'english',
            'experience_level': 'senior',
            'source': 'mock'
        },
        {
            'title': 'Data Scientist',
            'company': 'DataCorp Berlin',
            'description': 'Join our analytics team. You should know Python, Pandas, Scikit-Learn, and SQL. Experience with Tableau is a plus. We work in an Agile environment.',
            'url': 'https://example.com/job2',
            'location': location,
            'remote_ok': False,
            'language': 'english',
            'experience_level': 'mid',
            'source': 'mock'
        },
        {
            'title': 'Frontend Engineer (React)',
            'company': 'StartupXYZ',
            'description': 'Looking for a frontend wizard with React, TypeScript, and TailwindCSS experience. You will build user-facing dashboards. Node.js backend knowledge is helpful.',
            'url': 'https://example.com/job3',
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

        # Default filters if missing
        if not user_filters:
            user_filters = {
                'role_keywords': ['data', 'ai', 'analytics', 'it'],
                'locations': ['Berlin'],
                'languages': ['english'],
                'experience_levels': ['mid']
            }
            
        keywords = " ".join(user_filters.get('role_keywords', ['data', 'ai']))
        locations = user_filters.get('locations', ['Berlin'])
        
        # 2. Search for jobs (one search per location for now)
        all_found_jobs = []
        for loc in locations:
            found = search_jobs(keywords, loc)
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
            # Apply filters
                
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
                # 'url': job_data['url'], # REMOVED: Column missing in DB
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
                'raw_data': job_data
            }
            
            supabase.table("jobs").insert(job_record).execute()
            new_jobs_count += 1
            
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
