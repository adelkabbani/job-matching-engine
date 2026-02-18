# Directive: Submit Applications

## Goal
Automate job application submissions while maintaining quality and ethical standards.

## ⚠️ Critical Safety Notice

**This directive involves REAL job applications that will be seen by REAL recruiters.**

Before proceeding:
1. Read `directives/application_safety.md` completely
2. Understand platform Terms of Service
3. Be prepared for interview requests
4. Start with dry-run mode

---

## Prerequisites

### 1. Review Generated Materials
```bash
# Check CVs
ls .tmp/applications/*/cv.docx

# Check cover letters
ls .tmp/applications/*/cover_letter.txt
```

Ensure all materials are:
- Accurate
- Professional
- Tailored to each role

### 2. Set Daily Limits
Recommended starting point: **3-5 applications/day**

Edit your workflow to include limits:
```bash
python execution/apply_to_jobs.py --limit 5
```

### 3. Install Browser Automation
```bash
pip install playwright
playwright install chromium
```

---

## Usage Modes

### Mode 1: Dry Run (RECOMMENDED FIRST)
Preview what would happen without actual submission:

```bash
python execution/apply_to_jobs.py --dry-run
```

**What it does:**
- Navigates to job pages
- Detects application type
- Takes screenshots
- Logs everything
- **Does NOT submit**

**Use this to:**
- Test the system
- See what platforms are used
- Verify no errors

### Mode 2: Single Company Test
Apply to one company to verify workflow:

```bash
python execution/apply_to_jobs.py --company "EnergyHub"
```

**What it does:**
- Prompts for confirmation
- Applies to specified company only
- Opens visible browser
- Takes screenshots
- Logs submission

### Mode 3: Limited Batch
Apply to first N jobs:

```bash
python execution/apply_to_jobs.py --limit 3
```

**What it does:**
- Prompts for confirmation
- Applies to first 3 jobs
- Human-like delays between (30-60s)
- Logs everything

### Mode 4: Full Auto (USE WITH EXTREME CAUTION)
```bash
python execution/apply_to_jobs.py --auto --limit 5
```

**What it does:**
- NO confirmation prompt
- Applies to jobs automatically
- Use only after thorough testing

---

## Application Workflow

### Step 1: Detect Platform
System automatically identifies:
- **LinkedIn Easy Apply**
- **Greenhouse** (boards.greenhouse.io)
- **Lever** (jobs.lever.co)
- **Workday** (myworkdayjobs.com)
- **Generic/Unknown**

### Step 2: Navigate & Fill
Depending on platform:
- Opens visible browser
- Navigates to job page
- Attempts to fill form
- Takes screenshot

### Step 3: Manual Intervention (Current)
Most applications will require manual completion:
- System opens the page
- You complete the form
- System logs the attempt

**Why manual?**
- Forms vary widely
- CAPTCHA is common
- Safety against errors

### Step 4: Logging
Every attempt is logged in:
- `.tmp/applications/{Company}/application_log.json` (per-company)
- `.tmp/application_tracker.json` (master log)

**Log includes:**
- Timestamp
- Company & job title
- Platform type
- Status (dry_run, manual_needed, error, submitted)
- Screenshot path

---

## Platform-Specific Notes

### LinkedIn Easy Apply
**Status**: Partial support

**How it works:**
1. Detects "Easy Apply" button
2. Clicks it
3. Opens application modal
4. **Requires manual completion** (forms vary)

**Limitations:**
- Must be logged into LinkedIn
- Forms change frequently
- Requires manual review

**Recommendation**: Use sparingly, high detection risk.

### Greenhouse
**Status**: Detection only

**How it works:**
1. Navigates to job page
2. Takes screenshot of form
3. Logs as "manual_needed"

**Why manual:**
- Every Greenhouse instance is customized
- Form fields vary by company
- No standard API

**Tip**: Greenhouse is usually straightforward to fill manually.

### Lever
**Status**: Detection only

Similar to Greenhouse. Manual completion recommended.

### Workday
**Status**: Not supported

**Recommendation**: Apply manually. Workday is notoriously complex.

### Unknown/Generic
**How it works:**
1. Navigates to provided link
2. Takes screenshot
3. Logs for manual review

---

## Safety Guardrails

### Built-in Limits
1. **30-60s delay** between applications
2. **Confirmation prompt** before submission (unless --auto)
3. **Visible browser** (not headless) to verify actions
4. **Screenshot capture** at each step
5. **Duplicate prevention** via tracker

### Manual Overrides
```bash
# Limit applications
--limit 5

# Specific company only
--company "Company Name"

# Dry run (no submission)
--dry-run
```

### Red Flags to Stop
If you see:
- ❌ Multiple CAPTCHA challenges
- ❌ "Account suspended" messages
- ❌ Forms filling incorrectly
- ❌ Applications to wrong jobs

**Stop immediately and review.**

---

## Monitoring & Tracking

### Check Application Tracker
```bash
# View all applications
cat .tmp/application_tracker.json | python -m json.tool

# Count by status
cat .tmp/application_tracker.json | grep '"status"' | sort | uniq -c
```

### Review Screenshots
```bash
# List all screenshots
ls .tmp/applications/*/screenshot_*.png

# View for specific company
open .tmp/applications/EnergyHub/screenshot_before_apply.png
```

### Follow Up on Responses
When you receive interview requests:
1. Update `.tmp/application_tracker.json` with status: "interview_requested"
2. Prepare using company research
3. Be honest about automated CV generation if asked

---

## Troubleshooting

### "Could not find Easy Apply button"
- **Cause**: Not an Easy Apply job
- **Solution**: Apply manually via job link

### "CAPTCHA detected"
- **Cause**: Platform anti-bot measures
- **Solution**: Complete CAPTCHA manually, then proceed

### "Form fields not filling"
- **Cause**: Unknown form structure
- **Solution**: System will flag as "manual_needed"

### "Browser crashes"
- **Cause**: System resources, complex JavaScript
- **Solution**: Reduce --limit, close other apps

### "Application already submitted"
- **Cause**: Duplicate in tracker
- **Solution**: Check `.tmp/application_tracker.json`, manual review

---

## Post-Submission

### Immediate (Same Day)
1. Review all screenshots
2. Verify application_tracker.json entries
3. Check for any error messages

### Next Day
1. Check email for auto-responses
2. Update tracker with any rejections
3. Prepare for potential phone screens

### Weekly
1. Analyze success rate
2. Refine filtering if needed
3. Adjust daily limits based on capacity

---

## Success Metrics

Track these in `.tmp/application_tracker.json`:

### Application Metrics
- Total submitted
- Platforms used
- Companies applied to

### Response Metrics (manual update)
- Auto-responses received
- Interview requests
- Rejections
- Offers

### Quality Metrics
- Applications requiring manual fixes
- Time saved vs manual
- Interview request rate (%}

**Industry Benchmark**: 2-5% interview rate is normal with quality applications.

---

## Integration with Full Workflow

Complete `/auto-apply` workflow:
1. Job discovery → jobs_found.json
2. Filtering → jobs_filtered.json
3. CV generation → applications/{Company}/cv.docx
4. Cover letter → applications/{Company}/cover_letter.txt
5. **Application submission** ← This step
6. Response tracking

---

## Future Enhancements

Planned improvements:
1. **Form field mapping** - Better auto-fill
2. **Platform-specific modules** - More ATS systems
3. **Interview scheduler** - Auto-book first available
4. **Response monitor** - Email integration
5. **Success rate optimizer** - Learn what works

For now, treat this as a **semi-automated tool** requiring human oversight.

---

## Quick Reference

```bash
# Test workflow (safe)
python execution/apply_to_jobs.py --dry-run

# Apply to 3 jobs (with confirmation)
python execution/apply_to_jobs.py --limit 3

# Apply to specific company
python execution/apply_to_jobs.py --company "EnergyHub"

# Full auto (experienced users only)
python execution/apply_to_jobs.py --auto --limit 5

# Check what was submitted
cat .tmp/application_tracker.json
```

---

**Remember**: Quality applications to genuine matches > volume. Use automation to save time, not to spam.
