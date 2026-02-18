"""
Job scraper service.
Handles job ingestion from URLs and applies user filters.
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Tuple, Optional
import re


def fetch_job_from_url(url: str) -> Optional[Dict]:
    """
    Fetch job details from URL.
    Simple HTML parsing for MVP.
    
    Args:
        url: Job posting URL
    
    Returns:
        Dict with job details or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract job details (generic approach)
        # This is a simple heuristic - can be improved per-site
        job_data = {
            'url': url,
            'title': extract_title(soup),
            'company': extract_company(soup),
            'description': extract_description(soup),
            'location': extract_location(soup),
            'remote_ok': detect_remote(soup),
            'language': detect_language(soup),
            'experience_level': detect_experience_level(soup),
            'raw_html': str(soup)[:5000]  # Store snippet for debugging
        }
        
        return job_data
        
    except Exception as e:
        print(f"Error fetching job from URL: {e}")
        return None


def extract_title(soup: BeautifulSoup) -> str:
    """Extract job title from HTML."""
    # Try common patterns
    title_selectors = [
        'h1',
        '[class*="job-title"]',
        '[class*="jobTitle"]',
        '[data-testid*="title"]',
        'title'
    ]
    
    for selector in title_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            return element.get_text(strip=True)
    
    return "Unknown Title"


def extract_company(soup: BeautifulSoup) -> str:
    """Extract company name from HTML."""
    company_selectors = [
        '[class*="company"]',
        '[class*="employer"]',
        '[data-testid*="company"]'
    ]
    
    for selector in company_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            return element.get_text(strip=True)
    
    return "Unknown Company"


def extract_description(soup: BeautifulSoup) -> str:
    """Extract job description from HTML."""
    desc_selectors = [
        '[class*="description"]',
        '[class*="job-description"]',
        '[id*="description"]',
        'article',
        'main'
    ]
    
    for selector in desc_selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 100:  # Ensure it's substantial
                return text
    
    # Fallback: get all text
    return soup.get_text(separator=' ', strip=True)[:5000]


def extract_location(soup: BeautifulSoup) -> str:
    """Extract location from HTML."""
    location_selectors = [
        '[class*="location"]',
        '[class*="job-location"]',
        '[data-testid*="location"]'
    ]
    
    for selector in location_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            return element.get_text(strip=True)
    
    # Try to find location in text
    text = soup.get_text()
    location_patterns = [
        r'(?:Location|Based in|Office in):\s*([A-Za-z\s,]+)',
        r'(Berlin|Munich|Hamburg|Remote)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "Unknown"


def detect_remote(soup: BeautifulSoup) -> bool:
    """Detect if job is remote."""
    text = soup.get_text().lower()
    remote_keywords = ['remote', 'work from home', 'wfh', 'distributed', 'anywhere']
    return any(keyword in text for keyword in remote_keywords)


def detect_language(soup: BeautifulSoup) -> str:
    """Detect job language (simple heuristic)."""
    text = soup.get_text().lower()
    
    # Check for German keywords
    german_keywords = ['deutsch', 'deutschkenntnisse', 'muttersprache']
    if any(keyword in text for keyword in german_keywords):
        return 'german'
    
    # Default to English
    return 'english'


def detect_experience_level(soup: BeautifulSoup) -> str:
    """Detect experience level from job description."""
    text = soup.get_text().lower()
    
    if any(word in text for word in ['senior', '5+ years', '7+ years', 'lead', 'principal']):
        return 'senior'
    elif any(word in text for word in ['junior', 'entry level', 'graduate', '0-2 years']):
        return 'junior'
    else:
        return 'mid'


def apply_filters(job_data: Dict, user_filters: Dict) -> Tuple[bool, str]:
    """
    Check if job passes user filters.
    
    Args:
        job_data: Job details
        user_filters: User filter preferences
    
    Returns:
        Tuple of (passes, reason)
    """
    # Language filter
    if job_data['language'] not in user_filters.get('languages', ['english']):
        return False, f"Language mismatch: {job_data['language']}"
    
    # Location filter
    location_lower = job_data['location'].lower()
    user_locations = [loc.lower() for loc in user_filters.get('locations', ['berlin', 'remote'])]
    
    location_match = (
        any(loc in location_lower for loc in user_locations) or
        job_data['remote_ok']
    )
    
    if not location_match:
        return False, f"Location mismatch: {job_data['location']}"
    
    # Role relevance (keyword match in description)
    description_lower = job_data['description'].lower()
    role_keywords = user_filters.get('role_keywords', ['data', 'ai', 'analytics', 'it'])
    
    if not any(keyword in description_lower for keyword in role_keywords):
        return False, "Role not relevant (no matching keywords)"
    
    # Experience level filter
    user_levels = user_filters.get('experience_levels', ['junior', 'mid'])
    if job_data['experience_level'] not in user_levels:
        return False, f"Experience level mismatch: {job_data['experience_level']}"
    
    return True, "Passed all filters"


def ingest_job(url: str, user_id: str, supabase) -> Dict:
    """
    Main ingestion function.
    Fetches job, applies filters, calculates match score.
    
    Args:
        url: Job URL
        user_id: User ID
        supabase: Supabase client
    
    Returns:
        Dict with status and job data
    """
    # Fetch job details
    job_data = fetch_job_from_url(url)
    if not job_data:
        return {'status': 'error', 'message': 'Failed to fetch job from URL'}
    
    # Get user filters
    filters_res = supabase.table("job_filters")\
        .select("*")\
        .eq("user_id", user_id)\
        .single()\
        .execute()
    
    user_filters = filters_res.data if filters_res.data else {
        'languages': ['english'],
        'locations': ['berlin', 'remote'],
        'role_keywords': ['data', 'ai', 'analytics', 'it'],
        'experience_levels': ['junior', 'mid']
    }
    
    # Apply filters
    passes, reason = apply_filters(job_data, user_filters)
    
    # Calculate match score (even if filtered, for transparency)
    from services.job_matcher import get_user_skills, extract_skills_from_description, generate_match_report
    
    user_skills = get_user_skills(supabase, user_id)
    required_skills, optional_skills = extract_skills_from_description(job_data['description'])
    match_report = generate_match_report(user_skills, required_skills, optional_skills)
    
    # Save to database
    job_record = {
        'user_id': user_id,
        'title': job_data['title'],
        'company': job_data['company'],
        'description': job_data['description'],
        # 'url': url, # REMOVED: Column missing in DB
        'source': 'manual',
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
    
    result = supabase.table("jobs").insert(job_record).execute()
    
    return {
        'status': 'success',
        'job_id': result.data[0]['id'] if result.data else None,
        'filtered_out': not passes,
        'filter_reason': reason if not passes else None,
        'match_score': match_report['match_score'],
        'message': 'Job ingested successfully'
    }
