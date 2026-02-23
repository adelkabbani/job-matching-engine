# Directive: Personalized LinkedIn Search Strategy

## Objective
Automate the discovery of high-relevance job opportunities on LinkedIn for **Adel Kabbani** by leveraging deep profile understanding and AI-generated search queries.

## Core Constraints
1.  **Location**: **Berlin** (Strict).
2.  **Language**: **English Only**. Reject jobs requiring German fluency.
3.  **Experience Level**: **Entry-level / Junior**. Avoid "Senior", "Lead", "Manager" roles unless explicitly "Junior Manager" or similar entry-points.

## Workflow

### 1. Data Ingestion (Deep Understanding)
- **Input**: `Adel Kabbani CV.pdf` + Certificates.
- **Process**: Use LLM (Gemini/OpenRouter) to extract not just keywords, but *competencies* and *projects*.
- **Output**: Structured `user_profile.json` with a rich "skills.context" section.

### 2. Smart Keyword Generation
- **Input**: `user_profile.json`.
- **Logic**: derived from profile + market trends.
    - *Example*: If profile has "React" + "Python", generate:
        - "Junior Full Stack Developer Berlin"
        - "Entry Level Python Engineer Berlin"
        - "React Developer English Speaking Berlin"
- **Output**: Update `user_profile.json` with `preferences.search_queries` (List of strings).

### 3. Targeted Scraping
- **Tool**: `execution/scrape_linkedin.py` (using Firecrawl or similar).
- **Input**: Iterate through `preferences.search_queries`.
- **Constraint**: Ensure `location=Berlin` is part of the query payload or URL.

### 4. Strict Filtering
- **Tool**: `execution/filter_jobs.py`.
- **Logic**:
    - **Language Check**: Scan Title + Description.
        - *Reject*: "Fließend Deutsch", "German language required", "C1 German".
        - *Accept*: "English speaking", "International team", "No German required".
    - **Experience Check**:
        - *Reject*: "5+ years", "Senior", "Principal", "Architect", "Lead".
        - *Accept*: "0-2 years", "Junior", "Graduate", "Entry Level".

## Success Metrics
- **High Precision**: >80% of scraped jobs should be immediately relevant (Berlin + English).
- **Automation**: The pipeline runs end-to-end with a single command.
