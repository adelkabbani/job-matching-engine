# Directive: Generate Cover Letters

## Goal
Create personalized, compelling cover letters for each job application that tell your story and explain why you're the right fit.

## Inputs
- `.tmp/user_profile.json`: Your experience and achievements
- `.tmp/jobs_filtered.json`: Jobs you're applying to

## Tools/Scripts
- `execution/generate_cover_letter.py`: Cover letter generator

## Process

### Step 1: Run Generator
```bash
# Generate for all filtered jobs
python execution/generate_cover_letter.py

# Generate for specific company
python execution/generate_cover_letter.py --company "EnergyHub"
```

### Step 2: Review & Customize
Generated letters are saved to `.tmp/applications/{Company}/cover_letter.txt`

**What to check:**
1. **Personal details**: Name, email, phone are correct
2. **Company-specific details**: Does the "why this company" paragraph make sense?
3. **Achievements**: Are they relevant to this role?
4. **Tone**: Professional yet genuine?

**When to customize:**
- **Dream jobs**: Add specific company research
- **Referrals**: Mention who referred you
- **Career transitions**: Explain the pivot
- **Unique circumstances**: Remote relocation, visa sponsorship, etc.

### Step 3: (Optional) AI Enhancement
For important applications, you can use AI to enhance the letter:

**With ChatGPT/Claude:**
1. Copy the generated template
2. Prompt: "Enhance this cover letter with specific details about [Company]. Research their recent projects and mission."
3. Review and incorporate improvements

---

## Cover Letter Structure

Our generated letters follow this proven structure:

### 1. **Header** (Auto-generated)
- Your name
- Contact information
- Date
- Company name
- Hiring manager

### 2. **Opening Paragraph** (Personalized)
- Position you're applying for
- Where you found it
- Brief summary of your background
- Hook: Why you're excited about THIS role

**Example:**
> "I am excited to apply for the Software Engineer position at EnergyHub, as advertised on Tech Jobs for Good. As a Software Engineer with 5+ years of experience building scalable applications, I am drawn to EnergyHub's mission to drive meaningful impact through clean energy technology."

### 3. **Experience Paragraph** (Tailored)
- Highlight most relevant experience
- Specific achievements with metrics
- Technologies you've used
- Connect to job requirements

**Example:**
> "In my current role as Senior Engineer at TechCorp, I led the development of microservices serving 10M+ users. This experience has honed my ability to work with Python, AWS, and Docker while maintaining strong focus on code quality and team collaboration."

### 4. **Why This Company** (Company-specific)
- What excites you about their mission
- How your values align
- Specific projects or initiatives you admire

**Example:**
> "I am particularly drawn to EnergyHub because of its commitment to addressing climate change through innovative technology. The opportunity to contribute to clean energy solutions aligns perfectly with my personal values and professional goals."

### 5. **Closing Paragraph** (Confident)
- Reiterate fit
- Express enthusiasm
- Call to action

**Example:**
> "I am confident that my technical expertise, combined with my passion for building impactful solutions, makes me a strong fit for this role. I look forward to discussing how I can contribute to EnergyHub's continued success."

### 6. **Signature**
- "Sincerely," or "Best regards,"
- Your name

---

## Smart Personalization

Our system automatically personalizes based on:

### Industry/Mission Detection
- **Climate/Energy**: Emphasizes sustainability values
- **Healthcare**: Focuses on improving lives
- **Education**: Highlights democratizing knowledge
- **Open Source/Research**: Values transparency
- **Public Service**: Civic engagement focus

### Keywords from Job
- Extracts important skills from job description
- Emphasizes matching experience
- Uses same terminology as job posting

### Your Profile
- Pulls recent achievements
- Highlights relevant technologies
- Connects experience to role requirements

---

## Best Practices

### ✅ Do:
- **Be specific**: Name the company and role
- **Show research**: Reference their mission/projects
- **Quantify achievements**: "increased by 40%", "served 10M users"
- **Be genuine**: Authentic enthusiasm > flattery
- **Keep it concise**: 3-4 paragraphs max, ~300 words
- **Proofread**: Zero typos

### ❌ Don't:
- **Generic letters**: "To whom it may concern" or "I am writing to apply..."
- **Repeat your resume**: Cover letter tells the story behind the facts
- **Negative language**: Focus on what you bring, not what you lack
- **Desperation**: "I really need this job"
- **Lies or exaggeration**: Only claim skills you have
- **Wall of text**: Use short paragraphs with white space

---

## When to Skip Cover Letters

Some applications don't need cover letters:
- **"Easy Apply" on LinkedIn**: Often skipped
- **Bulk applications**: Save effort for promising matches
- **Recruiter outreach**: Resume is enough initially

Our system generates them for all jobs so you have them ready, but you decide which to submit.

---

## Future AI Enhancements

Coming soon:
1. **Company research**: Auto-fetch recent news, projects, blog posts
2. **Achievement mining**: Extract metrics from your descriptions
3. **Tone matching**: Adapt formality to company culture
4. **Follow-up generation**: Thank you notes, check-in emails
5. **A/B testing**: Track which letter styles get responses

For now, we provide high-quality templates that you can enhance manually for top-priority applications.

---

## Integration with Workflow

Cover letters are generated after CVs:
1. Profile ingestion
2. Job discovery & filtering
3. CV generation (ATS-optimized)
4. **Cover letter generation** ← You are here
5. Application submission

All materials saved in `.tmp/applications/{Company}/`:
- `cv.docx`
- `cover_letter.txt`
- (Future) `application_tracking.json`
