# Directive: Build User Profile

## Goal
Create a comprehensive professional profile by ingesting user's CV, certificates, and other credentials.

## Inputs
- User-uploaded documents:
  - CV/Resume (PDF, DOCX, TXT)
  - Certificates (PDF, image files)
  - LinkedIn export (if available)
  - Portfolio links

## Tools/Scripts
- `execution/ingest_profile.py`: Main ingestion script
- `schemas/profile_schema.json`: Validation schema

## Process

### Step 1: Document Upload
User provides their professional documents. Store in `.tmp/uploads/`.

### Step 2: Text Extraction
Run `python execution/ingest_profile.py path/to/cv.pdf`

This will:
1. Extract text from the document
2. Parse basic information (name, email, phone, skills)
3. Validate against schema
4.Save to `.tmp/user_profile.json`

### Step 3: Manual Enhancement
The basic parser captures ~40-60% of information. User should:
1. Open `.tmp/user_profile.json`
2. Fill in missing sections:
   - Work experience (companies, roles, achievements)
   - Education details
   - Project descriptions
   - Certifications
   - Job preferences (desired roles, locations, salary)

### Step 4: AI Enhancement (Future)
Once we integrate AI:
- Will automatically extract work experience with achievements
- Identify transferable skills
- Suggest professional headline
- Generate skill proficiency levels based on context

## Outputs
- `.tmp/user_profile.json`: Complete professional profile
- Confidence score indicating data quality

## Validation Rules
- Email must be valid format
- At least one work experience OR education entry
- At least 3 technical skills
- Preferences section should have desired_roles

## Edge Cases
- **Scanned PDF**: OCR will be needed (future enhancement)
- **Multiple CVs**: Merge information, taking most recent
- **Non-English**: May require translation layer
- **Missing data**: Flag for manual input

## Privacy
- All data stays local in `.tmp/` directory
- No data sent to external services (except AI API for parsing, which is opt-in)
- User can delete profile anytime
