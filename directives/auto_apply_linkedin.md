# LinkedIn Auto-Apply Directive

## Objective
To automate job applications on LinkedIn safely and effectively, minimizing the risk of account bans.

## Safety Protocol (CRITICAL)

### 1. Authentication: Persistent Browser Profile
- **Strategy**: Do NOT automate the login process (username/password entry).
- **Explanation**: LinkedIn's anti-bot systems often flag automated logins.
- **Solution**: 
  - Launch Playwright with a persistent `userDataDir`.
  - First run: User logs in manually.
  - Future runs: Script reuses the cookies/session from that directory.

### 2. Application Scope: "Easy Apply" Only
- **Target**: Jobs with the "Easy Apply" badge.
- **Why**: Standard external applications require navigating varied third-party sites (Workday, Greenhouse, etc.), which is complex and error-prone. "Easy Apply" keeps the flow within LinkedIn's modal.

### 3. Human-Like Behavior
- **Delays**: Random waits (2-5 seconds) between clicks.
- **Typing**: Type into fields character-by-character, not instant paste.
- **Limits**: Max 10 applications per day initially.

## Implementation Details

### Workflow (`execution/apply_linkedin.py`)
1. **Launch Browser**: `playwright.chromium.launch_persistent_context(user_data_dir=...)`
2. **Check Login**: Navigate to `linkedin.com`. If redirected to login page, pause and ask user to login.
3. **Load Jobs**: Read `.tmp/jobs_filtered.json`.
4. **Iterate**:
   - Navigate to Job URL.
   - Click "Easy Apply".
   - **Form Filling**:
     - Phone: Read from profile.
     - CV: Upload `.tmp/applications/{company}/cv.docx`.
     - Questions: Use "Best Guess" or default to positive ("Yes", 5 years).
   - **Submit**: Click "Submit Application" (or "Review" -> "Submit").
5. **Log**: Update `.tmp/application_tracker.json`.

## Usage
```bash
# First time (login mode)
python execution/apply_linkedin.py --setup

# Automated mode (after login)
python execution/apply_linkedin.py
```
