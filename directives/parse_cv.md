# CV Parsing & Profile Ingestion Directive

## Objective
To transform a raw CV file (PDF or DOCX) into a structured JSON profile that powers the HyperApply system.

## Parsing Logic

### 1. Text Extraction
- **PDF**: Use `pdfplumber` for high-fidelity text extraction. Key benefit: preserves layout better than `pypdf`.
- **DOCX**: Use `python-docx` to read paragraphs.

### 2. Information Extraction Rules

#### A. Contact Information
- **Email**: Regex match for standard email patterns.
- **Phone**: Regex match for common international formats (e.g., `+49...`, `(555)...`).

#### B. Education (Degree & University)
- **Keywords**: "Bachelor", "Master", "B.Sc", "M.Sc", "PhD", "Associate".
- **Logic**: 
  - Locate lines containing these keywords.
  - The "University" is often in the same line or the immediate preceding/succeeding line.
  - *Heuristic*: Look for "University", "College", "Institute", "School" near the degree major.

#### C. Skills
- **Method**: Keyword matching against a comprehensive taxonomy.
- **Taxonomy**:
  - **Languages**: Python, JavaScript, Java, C++, Go, Rust, etc.
  - **Frameworks**: React, Node.js, Django, FastAPI, Spring, etc.
  - **Tools**: Docker, Kubernetes, AWS, Azure, Git, Jenkins.
  - **Databases**: PostgreSQL, MongoDB, Redis, SQL.

#### D. Experience Level ("Fresher" Detection)
- **Signal 1**: Presence of "Work Experience" or "Professional Experience" headers.
- **Signal 2**: Duration calculations (if possible).
- **Signal 3**: Keyword "Intern" vs "Engineer"/"Developer".
- **Logic**: 
  - If "Work Experience" section is missing OR only contains "Intern"/"Student" roles -> **Fresher**.
  - Else -> **Experienced**.

### 3. Output Schema
Update `.tmp/user_profile.json` with:
```json
{
  "personal_info": {
    "name": "...",
    "email": "...",
    "phone": "..."
  },
  "education": [
    {
      "degree": "...",
      "university": "..."
    }
  ],
  "skills": ["Python", "React", ...],
  "experience_level": "Fresher" | "Experienced"
}
```

## Usage
```bash
python execution/ingest_cv.py "path/to/cv.pdf"
```
