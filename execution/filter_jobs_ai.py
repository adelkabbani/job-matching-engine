"""
AI-Powered Job Filtering
Uses Google Gemini to score jobs based on semantic match with user profile.

Usage:
    python execution/filter_jobs_ai.py [min_score]

Requires:
    GEMINI_API_KEY in .env
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import typing_extensions as typing

# Load environment variables
load_dotenv()

# Logging
log_path = Path(__file__).parent.parent / ".tmp" / "ai_scoring.log"
def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def setup_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env variable.")
        print("Please fetch a key from https://aistudio.google.com/app/apikey")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-flash-latest')

def load_json(path):
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def summarize_profile(profile):
    """Convert complex profile JSON into a concise text summary for the AI."""
    personal = profile.get("personal_info", {})
    exp = profile.get("work_experience", [])
    skills = profile.get("skills", {})
    
    summary = f"""
    Candidate: {personal.get('full_name', 'Candidate')}
    Role: {personal.get('linkedin_profile', 'Software Engineer')}
    
    Skills: {json.dumps(skills)}
    
    Experience:
    """
    for role in exp[:3]: # Top 3 roles
        summary += f"- {role.get('job_title', '')} at {role.get('company', '')}: {role.get('description', '')[:200]}...\n"
        
    return summary

def score_job(model, job, profile_summary):
    """Ask Gemini to score the job match."""
    
    prompt = f"""
    Act as a Technical Recruiter. Evaluate this job match.
    
    CANDIDATE PROFILE:
    {profile_summary}
    
    JOB LISTING:
    Title: {job.get('title')}
    Company: {job.get('company')}
    Description: {job.get('description')[:1000]}...
    
    TASK:
    1. Analyze if the candidate's skills and experience match the job requirements.
    2. Provide a match score from 0 to 100.
    3. Briefly explain the reasoning (pros/cons).
    
    OUTPUT FORMAT (JSON):
    {{
        "score": <0-100>,
        "reason": "<short explanation>",
        "missing_skills": ["<skill1>", "<skill2>"],
        "matched_skills": ["<skill1>", "<skill2>"]
    }}
    """
    
    retries = 3
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Quota exceeded" in error_str:
                wait_time = 20 * (attempt + 1)
                print(f"   ⏳ Rate limit hit. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            print(f"   ⚠️ AI Error: {e}")
            log(f"   ⚠️ AI Error: {e}")
            return {"score": 0, "reason": f"AI Error: {e}", "missing_skills": [], "matched_skills": []}
    
    return {"score": 0, "reason": "Rate limit exceeded after retries", "missing_skills": [], "matched_skills": []}

def main():
    print("🧠 AI Job Scorer (Powered by Gemini)")
    
    # Setup
    model = setup_gemini()
    tmp_dir = Path(__file__).parent.parent / ".tmp"
    
    # Load Data
    print("   Loading data...")
    profile = load_json(tmp_dir / "user_profile.json")
    jobs = load_json(tmp_dir / "jobs_found.json")
    
    profile_summary = summarize_profile(profile)
    
    filtered_jobs = []
    min_score = int(sys.argv[1]) if len(sys.argv) > 1 else 70
    
    print(f"   Scoring {len(jobs)} jobs (Threshold: {min_score}/100)...")
    print("-" * 50)
    
    for i, job in enumerate(jobs, 1):
        log(f"   Processing {i}/{len(jobs)}: {job.get('title')[:40]}...")
        print(f"   Processing {i}/{len(jobs)}: {job.get('title')[:40]}...", end="", flush=True)
        
        analysis = score_job(model, job, profile_summary)
        score = analysis.get("score", 0)
        
        log(f" -> Score: {score}. Reason: {analysis.get('reason', 'None')}")
        print(f" -> Score: {score}")
        
        # Add AI analysis to job object
        job["match_score"] = score
        job["ai_analysis"] = analysis
        
        if score >= min_score:
            filtered_jobs.append(job)
            
        # Avoid rate limits (Conservative 5s delay)
        time.sleep(5)
        
    # Save Results
    output_path = tmp_dir / "jobs_filtered.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filtered_jobs, f, indent=2, ensure_ascii=False)
        
    print("-" * 50)
    print(f"✅ AI Filtering Complete.")
    print(f"   Matched: {len(filtered_jobs)} / {len(jobs)} jobs")
    print(f"   Saved to: {output_path}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
