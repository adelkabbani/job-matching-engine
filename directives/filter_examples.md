# Job Filtering Feature - Example Usage

## Scenario 1: Remote-Only English Jobs

**Your Profile Settings:**
```json
{
  "preferences": {
    "desired_locations": ["Remote"],
    "remote_preference": "remote-only",
    "required_languages": ["English"]
  }
}
```

**What Gets Filtered:**
- ✅ "Remote (US)" → INCLUDED
- ✅ "Remote, USA" → INCLUDED
- ✅ "Remote Worldwide" → INCLUDED
- ❌ "San Francisco, CA" → EXCLUDED (not remote)
- ❌ "Hybrid - New York" → EXCLUDED (not fully remote)
- ❌ "Buenos Aires, Argentina (Spanish required)" → EXCLUDED (requires Spanish)

---

## Scenario 2: Flexible Location, Multiple Languages

**Your Profile Settings:**
```json
{
  "preferences": {
    "desired_locations": ["Remote", "London", "Berlin", "Paris"],
    "remote_preference": "flexible",
    "required_languages": ["English", "French"]
  }
}
```

**What Gets Filtered:**
- ✅ "Remote (Global)" → INCLUDED
- ✅ "London, UK" → INCLUDED
- ✅ "Paris, France" → INCLUDED
- ✅ "Berlin, Germany" → INCLUDED
- ✅ "Amsterdam, Netherlands" → INCLUDED (flexible location)
- ❌ "Tokyo, Japan (Japanese required)" → EXCLUDED (no Japanese in requirements)

---

## Scenario 3: Must-Have Keywords + Deal-Breakers

**Your Profile Settings:**
```json
{
  "preferences": {
    "desired_locations": ["Remote"],
    "remote_preference": "remote-only",
    "required_languages": ["English"],
    "must_have_keywords": ["Python", "AI"],
    "deal_breakers": ["crypto", "blockchain", "gambling"]
  }
}
```

**What Gets Filtered:**
- ✅ "Senior Python Engineer - AI/ML Focus" → INCLUDED (has both Python + AI)
- ✅ "AI Engineer (Python, TensorFlow)" → INCLUDED
- ❌ "Python Developer" → EXCLUDED (missing "AI")
- ❌ "AI Engineer (Java)" → EXCLUDED (missing "Python")
- ❌ "Python AI Engineer at Crypto Startup" → EXCLUDED (has "crypto")
- ❌ "Python Developer - Online Gambling Platform" → EXCLUDED (has "gambling")

---

## Scenario 4: On-Site Only, Specific City

**Your Profile Settings:**
```json
{
  "preferences": {
    "desired_locations": ["San Francisco, CA"],
    "remote_preference": "on-site",
    "required_languages": ["English"]
  }
}
```

**What Gets Filtered:**
- ✅ "San Francisco, CA" → INCLUDED
- ❌ "Remote (US)" → EXCLUDED (remote_preference is on-site)
- ❌ "New York, NY" → EXCLUDED (wrong city)
- ❌ "San Francisco, CA (Remote option)" → EXCLUDED if strict on-site

> **Note**: Currently, `remote_preference: "on-site"` doesn't strictly enforce on-site. 
> It's more permissive. For strict on-site filtering, you'd need to exclude "Remote" 
> from desired_locations or add it to deal_breakers.

---

## Tips for Best Results

### 1. Start Broad, Then Narrow
First run without filters to see what's available:
```json
{
  "preferences": {
    "remote_preference": "flexible"
  }
}
```

Then add filters based on what you see.

### 2. Use Must-Have Wisely
Don't require too many keywords:
- ✅ Good: `["Python", "Backend"]`
- ❌ Too strict: `["Python", "Django", "PostgreSQL", "AWS", "Kubernetes", "Redis"]`

### 3. Language Defaults to English
If a job doesn't mention language requirements, we assume English.
This means:
- If you set `"required_languages": ["English"]`, most jobs will pass
- Only jobs explicitly requir ing OTHER languages will be filtered out

### 4. Location Matching is Fuzzy
We do substring matching:
- Your preference: `"San Francisco"`
- Matches: "San Francisco, CA", "San Francisco Bay Area", "SF, California"

### 5. Deal-Breakers Are Powerful
One deal-breaker word = instant rejection:
- `"deal_breakers": ["crypto"]`
- Will exclude: "Crypto Exchange", "Blockchain & Crypto", "Bitcoin Startup"

---

## Testing Your Filters

1. Create test profile with your filters
2. Run: `python execution/filter_jobs.py`
3. Check output:
   - "Filtered to X matching jobs" should be reasonable (not 0, not all)
   - Review top 5 matches
   - Adjust filters if needed

4. Iterate until you get 5-20 matches per search

---

## Common Filter Combinations

**Climate Tech Jobs Only:**
```json
{
  "industry_preference": ["climate", "clean energy"],
  "required_languages": ["English"],
  "remote_preference": "flexible"
}
```

**Senior Remote Python Roles:**
```json
{
  "desired_roles": ["Senior Software Engineer", "Staff Engineer", "Principal Engineer"],
  "must_have_keywords": ["Python", "Senior"],
  "remote_preference": "remote-only",
  "salary_expectations": {
    "minimum": 150000
  }
}
```

**Startup Jobs in SF/NYC:**
```json
{
  "desired_locations": ["San Francisco", "New York"],
  "company_size_preference": ["startup", "small"],
  "remote_preference": "flexible"
}
```
