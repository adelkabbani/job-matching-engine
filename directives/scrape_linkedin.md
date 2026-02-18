# LinkedIn Job Scraping Directive

## Objective
To discover relevant job opportunities on LinkedIn that match the user's profile skills and location.

## Strategy

### 1. Search Method: Public Search via Firecrawl
**Why**: Avoids the complexity and risk of automating a logged-in LinkedIn account (bans, captchas).
**How**: Use Firecrawl's search capability with advanced operators.
**Query Pattern**: `site:linkedin.com/jobs "Software Engineer" "Remote" "Easy Apply" -intitle:profiles`

### 2. Extraction Logic
- **Tools**: `firecrawl_scrape` (or `firecrawl_extract` if structured data needed).
- **Target Data**:
  - Title
  - Company
  - Location
  - Date Posted
  - **Apply Link** (Critical for next step)
  - "Easy Apply" indicator (if visible in snippets)

### 3. Filtering (Pre-emptive)
- Apply negative keywords in search query to remove noise (e.g., `-senior` if Fresher).
- Use `after:24h` or similar if search engine supports it (Google does, Firecrawl might depend on backend).

### 4. Output Schema
Append to `.tmp/jobs_found.json`:
```json
{
  "source": "LinkedIn",
  "title": "...",
  "company": "...",
  "link": "https://www.linkedin.com/jobs/view/...",
  "description": "...", 
  "easy_apply": true/false
}
```

## Risks & Mitigations
- **Rate Limits**: Firecrawl handles this, but we should limit to ~10-20 results per run initially.
- **Stale Jobs**: LinkedIn public pages often show closed jobs. We must verify "Active" status if possible during extraction.

## Usage
```bash
python execution/scrape_linkedin.py
```
