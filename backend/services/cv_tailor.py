"""
CV Tailoring Service.
Logic to reorder and reshape CV bullet points based on Job Description keywords.
"""
from typing import Dict, List, Set, Tuple
import re

def tailor_cv(job_description: str, cv_data: Dict, cert_skills: List[str]) -> Dict:
    """
    Tailors a CV by reordering experience and highlighting relevant skills.
    Only uses existing data from the user profile and certificates.
    """
    jd_keywords = _extract_keywords(job_description)
    
    # 1. Tailor Work Experience
    tailored_experience = []
    for exp in cv_data.get('work_experience', []):
        tailored_exp = exp.copy()
        bullets = exp.get('description', [])
        if isinstance(bullets, str):
            bullets = [b.strip() for b in bullets.split('\n') if b.strip()]
        
        # Score each bullet based on JD keywords
        scored_bullets = []
        for bullet in bullets:
            score = sum(1 for kw in jd_keywords if kw.lower() in bullet.lower())
            scored_bullets.append((bullet, score))
        
        # Sort bullets by score (descending)
        scored_bullets.sort(key=lambda x: x[1], reverse=True)
        tailored_exp['description'] = [b[0] for b in scored_bullets]
        tailored_experience.append(tailored_exp)

    # 2. Tailor Skills Section
    # Combine CV skills and certificate skills
    all_user_skills = set(cv_data.get('skills', [])) | set(cert_skills)
    
    # Identify skills that match JD keywords
    matched_skills = [s for s in all_user_skills if s.lower() in [k.lower() for k in jd_keywords]]
    other_skills = [s for s in all_user_skills if s not in matched_skills]
    
    # Prioritize matched skills
    tailored_skills = matched_skills + other_skills

    return {
        **cv_data,
        'work_experience': tailored_experience,
        'skills': tailored_skills,
        'ats_metadata': {
            'keywords_found': matched_skills,
            'keywords_missing': [k for k in jd_keywords if k.lower() not in [s.lower() for s in all_user_skills]]
        }
    }

def _extract_keywords(text: str) -> List[str]:
    """Simple keyword extraction from JD."""
    # This could be improved with NLP or LLM in the next step
    # For now, using a set of common tech keywords + common nouns
    common_words = set(['and', 'the', 'for', 'with', 'experience', 'skills', 'knowledge', 'ability', 'required', 'preferred'])
    words = re.findall(r'\b\w+\b', text.lower())
    return sorted(list(set([w for w in words if len(w) > 2 and w not in common_words])), key=len, reverse=True)[:30]
