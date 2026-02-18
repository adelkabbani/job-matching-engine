# Directive: Find Job Listings

## Goal
Search for job listings on specific platforms (e.g., LinkedIn, Indeed) based on keywords and location.

## Inputs
- `keywords`: (e.g., "Software Engineer")
- `location`: (e.g., "Remote", "New York")
- `platforms`: List of platforms to search.

## Tools/Scripts
- `execution/search_jobs.py`: Scrapes or uses APIs to find jobs.

## Outputs
- `jobs_list.json` in `.tmp/`: A list of found jobs with details (title, company, link, etc.)

## Edge Cases
- No jobs found: Return an empty list and log the search parameters.
- Rate limiting: Implement retries or backoff in the execution script.
- Captchas: Alert orchestration layer if human intervention is needed.
