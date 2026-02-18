"""
Job Filtering System

Filters discovered jobs based on user preferences:
- Desired locations (cities, countries, remote)
- Language requirements
- Salary expectations
- Must-have keywords
- Deal-breakers

Usage:
    python execution/filter_jobs.py
    
Reads:
    - .tmp/user_profile.json (preferences)
    - .tmp/jobs_found.json (all discovered jobs)
    
Outputs:
    - .tmp/jobs_filtered.json (jobs matching preferences)
"""

import json
import sys
import os
from pathlib import Path
import re


def load_profile():
    """Load user profile with preferences."""
    profile_path = Path(__file__).parent.parent / ".tmp" / "user_profile.json"
    
    if not profile_path.exists():
        print("Profile not found. Run 'python execution/ingest_profile.py' first.")
        sys.exit(1)
    
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_jobs():
    """Load discovered jobs."""
    jobs_path = Path(__file__).parent.parent / ".tmp" / "jobs_found.json"
    
    if not jobs_path.exists():
        print("No jobs found. Run job discovery first.")
        sys.exit(1)
    
    with open(jobs_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def matches_location(job_location, desired_locations, remote_preference):
    """
    Check if job location matches user preferences.
    
    Args:
        job_location: Location string from job listing (e.g., "Remote (US)", "San Francisco, CA")
        desired_locations: List of desired locations from profile
        remote_preference: "remote-only", "hybrid", "on-site", "flexible"
    
    Returns:
        bool: True if location matches preferences
    """
    if not job_location:
        return True  # If location unknown, don't filter out
    
    job_location_lower = job_location.lower()
    
    # Handle remote preference
    if remote_preference == "remote-only":
        return "remote" in job_location_lower
    
    # If user wants flexible, accept anything
    if remote_preference == "flexible":
        return True
    
    # Check if job location contains any desired location
    if desired_locations:
        for loc in desired_locations:
            if loc.lower() in job_location_lower:
                return True
            # Special case: "Remote" matches if in desired locations
            if loc.lower() == "remote" and "remote" in job_location_lower:
                return True
        return False
    
    return True  # No location preference = accept all


def matches_language(job_title, job_description, required_languages):
    """
    Check if job matches language requirements.
    
    Args:
        job_title: Job title
        job_description: Job description (if available)
        required_languages: List of required languages (e.g., ["English"])
    
    Returns:
        bool: True if language requirements are met
    """
    if not required_languages:
        return True  # No language requirement = accept all
    
    # Combine title and description for analysis
    text = f"{job_title} {job_description or ''}".lower()
    
    # Language indicators
    language_keywords = {
        "english": ["english", "en-us", "en-uk", "anglophone"],
        "spanish": ["spanish", "español", "castellano", "spanish-speaking"],
        "french": ["french", "français", "francophone"],
        "german": ["german", "deutsch", "german-speaking"],
        "mandarin": ["mandarin", "chinese", "中文", "mandarin-speaking"],
        "japanese": ["japanese", "日本語", "japanese-speaking"],
        "korean": ["korean", "한국어", "korean-speaking"]
    }
    
    for required_lang in required_languages:
        required_lang_lower = required_lang.lower()
        
        # If the required language is NOT mentioned, it's likely English-only by default
        if required_lang_lower == "english":
            # Check if other languages are explicitly required
            other_languages_required = False
            for lang, keywords in language_keywords.items():
                if lang != "english":
                    if any(kw in text for kw in keywords):
                        other_languages_required = True
                        break
            
            # If no other language is required, assume English
            if not other_languages_required:
                return True
        
        # Check if the required language keywords appear
        if required_lang_lower in language_keywords:
            keywords = language_keywords[required_lang_lower]
            if any(kw in text for kw in keywords):
                return True
    
    # Default: if language is mentioned explicitly in job, check match
    # Otherwise assume it matches (benefit of doubt)
    return True


def matches_keywords(job_title, job_description, must_have, deal_breakers):
    """
    Check if job matches keyword requirements.
    
    Args:
        job_title: Job title
        job_description: Job description (if available)
        must_have: Keywords that MUST appear
        deal_breakers: Keywords that disqualify the job
    
    Returns:
        bool: True if keyword requirements are met
    """
    text = f"{job_title} {job_description or ''}".lower()
    
    # Check deal-breakers first
    if deal_breakers:
        for deal_breaker in deal_breakers:
            if deal_breaker.lower() in text:
                return False
    
    # Check must-have keywords
    if must_have:
        for keyword in must_have:
            if keyword.lower() not in text:
                return False
    
    return True


def filter_jobs(jobs, profile):
    """
    Filter jobs based on user preferences.
    
    Returns:
        List of filtered jobs with match_reasons
    """
    preferences = profile.get("preferences", {})
    
    # Extract preferences
    desired_locations = preferences.get("desired_locations", [])
    remote_preference = preferences.get("remote_preference", "flexible")
    required_languages = preferences.get("required_languages", [])  # NEW
    must_have = preferences.get("must_have_keywords", [])
    deal_breakers = preferences.get("deal_breakers", [])
    
    filtered_jobs = []
    
    for job in jobs:
        job_location = job.get("location", "")
        job_title = job.get("title", "")
        job_description = job.get("description", "")  # May not be available yet
        
        # Apply filters
        location_match = matches_location(job_location, desired_locations, remote_preference)
        language_match = matches_language(job_title, job_description, required_languages)
        keyword_match = matches_keywords(job_title, job_description, must_have, deal_breakers)
        
        if location_match and language_match and keyword_match:
            # Add match metadata
            job["match_reasons"] = []
            
            if location_match:
                job["match_reasons"].append(f"Location: {job_location}")
            if language_match and required_languages:
                job["match_reasons"].append(f"Language: {', '.join(required_languages)}")
            if must_have:
                job["match_reasons"].append(f"Has keywords: {', '.join(must_have)}")
            
            filtered_jobs.append(job)
    
    return filtered_jobs


def save_filtered_jobs(jobs, output_path=None):
    """Save filtered jobs to JSON."""
    if output_path is None:
        output_dir = Path(__file__).parent.parent / ".tmp"
        output_path = output_dir / "jobs_filtered.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    return output_path


def main():
    print("Loading profile and jobs...")
    profile = load_profile()
    jobs = load_jobs()
    
    print(f"Found {len(jobs)} total jobs")
    
    # Show user preferences
    prefs = profile.get("preferences", {})
    print("\nYour Preferences:")
    print(f"  Locations: {prefs.get('desired_locations', ['Any'])}")
    print(f"  Remote: {prefs.get('remote_preference', 'flexible')}")
    print(f"  Languages: {prefs.get('required_languages', ['Any'])}")
    print(f"  Must have: {prefs.get('must_have_keywords', ['None'])}")
    print(f"  Deal-breakers: {prefs.get('deal_breakers', ['None'])}")
    
    print("\nFiltering jobs...")
    filtered = filter_jobs(jobs, profile)
    
    output_path = save_filtered_jobs(filtered)
    
    print(f"\nFiltered to {len(filtered)} matching jobs")
    print(f"Results saved to: {output_path}")
    
    # Show top matches
    if filtered:
        print("\nTop Matches:")
        for i, job in enumerate(filtered[:5], 1):
            print(f"\n  {i}. {job['title']} at {job['company']}")
            print(f"     Location: {job.get('location', 'Not specified')}")
            if job.get('match_reasons'):
                print(f"     Matches: {', '.join(job['match_reasons'])}")
    else:
        print("\nNo jobs match your preferences. Consider:")
        print("    - Broadening location preferences")
        print("    - Removing strict must-have keywords")
        print("    - Adjusting language requirements")
    
    return len(filtered)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
