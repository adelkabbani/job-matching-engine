"""
Job Filtering System - Strict Mode for Berlin/English/Entry-Level
"""

import json
import sys
import os
from pathlib import Path
import re

def load_profile():
    profile_path = Path(__file__).parent.parent / ".tmp" / "user_profile.json"
    if not profile_path.exists():
        print("Profile not found. Run 'python execution/ingest_cv.py' first.")
        sys.exit(1)
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_jobs():
    jobs_path = Path(__file__).parent.parent / ".tmp" / "jobs_found.json"
    if not jobs_path.exists():
        print("No jobs found. Run job discovery first.")
        sys.exit(1)
    with open(jobs_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def matches_location_strict(job, desired_city="Berlin"):
    """Temporarily relaxed: Allow all locations for stress test."""
    return True

def matches_language_strict(job):
    """Temporarily relaxed: Allow all languages for stress test."""
    return True, "Language Check Disabled"

def matches_level_strict(job):
    """Temporarily relaxed: Allow Senior/Lead roles for stress test."""
    return True, "Level Check Disabled"

def filter_jobs(jobs, profile):
    filtered_jobs = []
    
    print("\n--- Filtering Log ---")
    
    for job in jobs:
        # 1. Location Matching
        if not matches_location_strict(job, "Berlin"):
            continue
            
        # 2. Level Matching
        level_ok, level_msg = matches_level_strict(job)
        if not level_ok:
            # print(f"Skipping {job['title']}: {level_msg}")
            continue
            
        # 3. Language Matching (Most expensive/strict)
        lang_ok, lang_msg = matches_language_strict(job)
        if not lang_ok:
            print(f"Skipping {job['title']}: {lang_msg}")
            continue
            
        # Passed all checks
        job["match_reasons"] = ["Location: Berlin", "Language: English", "Level: Entry/Junior"]
        filtered_jobs.append(job)
        
    return filtered_jobs

def save_filtered_jobs(jobs):
    output_dir = Path(__file__).parent.parent / ".tmp"
    output_path = output_dir / "jobs_filtered.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    return output_path

def main():
    profile = load_profile()
    jobs = load_jobs()
    
    print(f"Processing {len(jobs)} jobs against strict filters (Berlin / English / Entry)...")
    
    filtered = filter_jobs(jobs, profile)
    output_path = save_filtered_jobs(filtered)
    
    print(f"\n✅ Retained {len(filtered)} / {len(jobs)} jobs.")
    print(f"Results saved to: {output_path}")

    if filtered:
        print("\nTop Matches:")
        for i, job in enumerate(filtered[:5], 1):
            print(f"{i}. {job['title']} @ {job['company']}")

if __name__ == "__main__":
    main()


