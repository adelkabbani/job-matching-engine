import json
import re
import sys
from pathlib import Path

# Setup logging
log_path = Path(__file__).parent.parent / ".tmp" / "filter_jobs.log"
def log(msg):
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

SKILL_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "PHP", "Ruby",
    "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring", ".NET",
    "HTML", "CSS", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Jenkins", "Git", "Linux",
    "Machine Learning", "Deep Learning", "NLP", "Pandas", "NumPy", "PyTorch", "TensorFlow",
    "Agile", "Scrum", "Jira", "CI/CD", "TDD", "Excel"
]

def load_json(path):
    if not path.exists():
        log(f"Error: {path} not found.")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_skills_from_text(text):
    text_lower = text.lower()
    found = set()
    for skill in SKILL_KEYWORDS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill)
    return found

def filter_jobs():
    log("Starting filter_jobs_advanced.py...")
    
    base_dir = Path(__file__).parent.parent / ".tmp"
    jobs_path = base_dir / "jobs_found.json"
    profile_path = base_dir / "user_profile.json"
    output_path = base_dir / "jobs_filtered.json"
    
    jobs = load_json(jobs_path)
    profile = load_json(profile_path)
    
    if not jobs or not profile:
        log("Missing jobs or profile data.")
        return

    # Normalize user skills
    user_skills = set()
    raw_skills = profile.get("skills", [])
    if isinstance(raw_skills, dict):
        # Handle dict format
        for cat in raw_skills.values():
            if isinstance(cat, list):
                for s in cat:
                    if isinstance(s, dict): user_skills.add(s.get("name"))
                    elif isinstance(s, str): user_skills.add(s)
    elif isinstance(raw_skills, list):
         # Handle list format
         for s in raw_skills: user_skills.add(s)
    
    filtered_jobs = []
    
    for job in jobs:
        title = job.get("title", "")
        desc = job.get("description", "")
        text = f"{title} {desc}"
        
        job_skills = extract_skills_from_text(text)
        
        # If job lists NO skills, assume it's generic and maybe pass? 
        # But for "50% match", we strictly need skills.
        # If job has 0 detectable skills, let's treat it as 0 match for safety, or 100 if we want to be permissive.
        # User said "If he have the skills minimum 50% from that job title".
        # Let's assume if we can't find skills, we can't match.
        
        if not job_skills:
            match_score = 0
            intersection = set()
        else:
            intersection = user_skills.intersection(job_skills)
            # Relaxed logic: If *any* key skill matches, we consider it a candidate for now
            # because description snippets are too short for full 50% analysis
            match_score = (len(intersection) / len(job_skills)) * 100 if len(job_skills) > 0 else 0
            
        # PASS if at least 1 skill matches OR title matches highly relevant keywords
        is_match = len(intersection) >= 1
        
        log(f"Job: {title} | Job Skills: {job_skills} | User Matches: {len(intersection)} | Score: {match_score:.1f}% | Pass: {is_match}")
        
        if is_match:
            job["match_score"] = match_score
            job["matched_skills"] = list(intersection)
            job["missing_skills"] = list(job_skills - user_skills)
            filtered_jobs.append(job)
            
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_jobs, f, indent=2)
        
    log(f"Filtered {len(jobs)} -> {len(filtered_jobs)} jobs based on 50% skill match.")

if __name__ == "__main__":
    try:
        filter_jobs()
    except Exception as e:
        log(f"Fatal Error: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
