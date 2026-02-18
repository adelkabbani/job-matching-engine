---
description: Fully automated job search and application preparation
---
// turbo-all
1. **Scrape Job Listings**
   - Execute the scraper for the specified keyword and location.
   - Command: `python execution/scrape_techforgood.py "Software Engineer" "remote"`

2. **Filter by Preferences**
   - Apply location, language, and keyword filters.
   - Command: `python execution/filter_jobs.py`

3. **Generate ATS-Optimized CVs**
   - Create tailored resumes for each job.
   - Command: `python execution/generate_cv.py`

4. **Generate Cover Letters**
   - Create personalized cover letters.
   - Command: `python execution/generate_cover_letter.py`

5. **Review Applications**
   - All materials saved in `.tmp/applications/{Company}/`
   - Review and customize for dream jobs before submission.
