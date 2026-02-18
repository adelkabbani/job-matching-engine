# Directive: Filter Jobs by Preferences

## Goal
Filter discovered jobs based on user's location, language, and keyword preferences.

## Inputs
- `.tmp/user_profile.json`: User's preferences
- `.tmp/jobs_found.json`: All discovered jobs

## Tools/Scripts
- `execution/filter_jobs.py`: Filtering engine

## Process

### Step 1: Set Your Preferences
Edit `.tmp/user_profile.json` under the `preferences` section:

```json
"preferences": {
  "desired_locations": ["Remote", "San Francisco", "New York"],
  "remote_preference": "remote-only",
  "required_languages": ["English"],
  "must_have_keywords": ["Python", "React"],
  "deal_breakers": ["crypto", "gambling"]
}
```

**Location Options:**
- `desired_locations`: Array of cities/countries or "Remote"
- `remote_preference`: "remote-only", "hybrid", "on-site", or "flexible"

**Language Filtering:**
- `required_languages`: Array of languages (e.g., ["English"], ["English", "Spanish"])
- If empty, no language filtering applied
- Matches are smart: looks for language keywords in job description

**Keyword Filtering:**
- `must_have_keywords`: ALL must appear in job (AND logic)
- `deal_breakers`: ANY disqualifies the job (OR logic)

### Step 2: Run Filtering
```bash
python execution/filter_jobs.py
```

This will:
1. Load your profile and preferences
2. Load all discovered jobs
3. Apply location filter
4. Apply language filter
5. Apply keyword filters
6. Save matches to `.tmp/jobs_filtered.json`

### Step 3: Review Results
The script outputs:
- How many jobs matched
- Top 5 matches with reasons
- Suggestions if no matches found

## Outputs
- `.tmp/jobs_filtered.json`: Jobs matching all filters
- Each job includes `match_reasons` array explaining why it matched

## Filter Logic

### Location Matching
- **remote-only**: Only jobs with "Remote" in location
- **flexible**: Accepts all locations
- **specific cities**: Matches if job location contains your city
- **Example**: 
  - Your preference: ["Remote", "New York"]
  - Matches: "Remote (US)", "New York, NY", "New York, NY/Remote"
  - Doesn't match: "San Francisco, CA"

### Language Matching
Currently supports: English, Spanish, French, German, Mandarin, Japanese, Korean

**Logic:**
- If `required_languages` is empty → accept all jobs
- If language explicitly mentioned in job → check if it matches
- If no language mentioned → assume English by default
- **Example**:
  - Your preference: ["English"]
  - Job says "Spanish required" → filtered OUT
  - Job says nothing about language → INCLUDED (assumes English)

### Keyword Matching
- **must_have**: ALL keywords must appear (case-insensitive)
- **deal_breakers**: If ANY appear, job is excluded
- **Example**:
  - must_have: ["Python", "AI"]
  - Job title: "Python Engineer with AI focus" → ✅ MATCH
  - Job title: "Python Developer" → ❌ NO MATCH (missing "AI")

## Edge Cases
- **No matches**: Script suggests broadening filters
- **All jobs match**: Consider adding must_have keywords
- **Location unclear**: Jobs with unknown location pass filter

## Integration with Workflow

This filter runs BEFORE matching/application generation:
1. Job Discovery → finds 100+ jobs
2. **Filtering** → narrows to 10-20 relevant jobs
3. Matching → scores the 10-20 by fit
4. Application → generates materials for top 5

## Future Enhancements
- Salary range filtering
- Company size filtering
- Industry filtering
- Seniority level matching
