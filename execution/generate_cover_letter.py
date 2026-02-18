"""
AI-Powered Cover Letter Generator

Generates personalized, compelling cover letters for each job application.

Features:
- Tells a story connecting your experience to the role
- References specific company achievements/mission
- Explains "why this job" and "why this company"
- Professional yet genuine tone
- Customized for each position

Usage:
    python execution/generate_cover_letter.py
    python execution/generate_cover_letter.py --company "EnergyHub"
    
Reads:
    - .tmp/user_profile.json
    - .tmp/jobs_filtered.json
    
Outputs:
    - .tmp/applications/{company_name}/cover_letter.txt
    - .tmp/applications/{company_name}/cover_letter.pdf (optional)
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse


def load_profile():
    """Load user profile."""
    profile_path = Path(__file__).parent.parent / ".tmp" / "user_profile.json"
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_jobs():
    """Load filtered jobs."""
    jobs_path = Path(__file__).parent.parent / ".tmp" / "jobs_filtered.json"
    with open(jobs_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_cover_letter(profile, job):
    """
    Generate a personalized cover letter.
    
    In production, this would use AI (GPT-4, Claude) for compelling narratives.
    For now, uses intelligent templates with personalization.
    """
    personal_info = profile.get('personal_info', {})
    work_exp = profile.get('work_experience', [])
    
    # Extract job details
    company = job.get('company', 'your company')
    title = job.get('title', 'this position')
    location = job.get('location', '')
    source = job.get('source', 'Tech Jobs for Good')
    
    # Get relevant experience
    most_recent_role = work_exp[0] if work_exp else {}
    current_title = most_recent_role.get('title', 'Software Engineer')
    current_company = most_recent_role.get('company', 'my current company')
    
    # Get matching skills (from match_reasons if available)
    match_reasons = job.get('match_reasons', [])
    
    # Build the cover letter
    today = datetime.now().strftime("%B %d, %Y")
    
    letter = f"""{personal_info.get('full_name', 'Your Name')}
{personal_info.get('email', 'your.email@example.com')}
{personal_info.get('phone', '+1-555-0123')}
{location if location else ''}

{today}

Hiring Manager
{company}

Dear Hiring Manager,

{generate_opening_paragraph(profile, job)}

{generate_experience_paragraph(profile, job)}

{generate_why_company_paragraph(profile, job)}

{generate_closing_paragraph(profile, job)}

I look forward to the opportunity to discuss how I can contribute to {company}'s continued success.

Sincerely,
{personal_info.get('full_name', 'Your Name')}
"""
    
    return letter


def generate_opening_paragraph(profile, job):
    """Generate compelling opening that hooks the reader."""
    personal_info = profile.get('personal_info', {})
    work_exp = profile.get('work_experience', [])
    
    company = job.get('company', 'your company')
    title = job.get('title', 'this position')
    source = job.get('source', 'Tech Jobs for Good')
    
    # Calculate years of experience
    total_years = len(work_exp) * 1.5  # Rough estimate
    years_str = f"{int(total_years)}+" if total_years > 0 else "several"
    
    # Get headline or current role
    headline = personal_info.get('professional_headline', 'Software Engineer')
    
    # Opening hook variations
    openings = [
        f"I am excited to apply for the {title} position at {company}, as advertised on {source}. As a {headline} with {years_str} years of experience building scalable, user-focused applications, I am drawn to {company}'s mission to drive meaningful impact through technology.",
        
        f"When I discovered the {title} opening at {company} on {source}, I knew I had to apply. With {years_str} years of experience as a {headline}, I have consistently delivered high-impact solutions, and I am excited about the opportunity to bring this expertise to {company}.",
        
        f"I am writing to express my strong interest in the {title} role at {company}. As a {headline} with {years_str} years of hands-on experience, I am passionate about leveraging technology to solve complex problems—a value I see reflected in {company}'s work."
    ]
    
    # Choose first one for now (in production, AI would craft unique opening)
    return openings[0]


def generate_experience_paragraph(profile, job):
    """Highlight relevant experience with specific achievements."""
    work_exp = profile.get('work_experience', [])
    
    # Handle skills (can be list or dict)
    skills_data = profile.get('skills', [])
    if isinstance(skills_data, dict):
        skills = skills_data.get('technical', [])
    else:
        skills = skills_data
    
    if not work_exp:
        return "I bring strong technical skills and a proven ability to deliver results in fast-paced environments."
    
    most_recent = work_exp[0]
    company = most_recent.get('company', 'my current company')
    title = most_recent.get('title', 'Software Engineer')
    
    # Get achievements
    achievements = most_recent.get('achievements', [])
    top_achievement = achievements[0] if achievements else "delivered high-impact projects"
    
    # Get relevant technologies
    technologies = most_recent.get('technologies', [])
    tech_str = ", ".join(technologies[:5]) if technologies else "modern technologies"
    
    # Craft experience paragraph
    paragraphs = [
        f"In my current role as {title} at {company}, I have {top_achievement.lower()} This experience has honed my ability to work with {tech_str} while maintaining a strong focus on code quality and team collaboration. I have consistently demonstrated the ability to translate complex requirements into elegant, scalable solutions that drive business value.",
        
        f"Throughout my tenure as {title} at {company}, I have specialized in building robust applications using {tech_str}. Notably, I {top_achievement.lower()} This hands-on experience has equipped me with both the technical depth and leadership mindset needed to excel in the {job.get('title', 'this role')}.",
        
        f"As {title} at {company}, I have been instrumental in {top_achievement.lower()} Working extensively with {tech_str}, I have developed a comprehensive understanding of modern software development practices and a track record of delivering results under pressure."
    ]
    
    return paragraphs[0]


def generate_why_company_paragraph(profile, job):
    """Explain why you're interested in THIS company specifically."""
    company = job.get('company', 'your company')
    title = job.get('title', 'this position')
    
    # In production, AI would research the company and craft specific reasons
    # For now, use intelligent templates based on company name/industry
    
    # Detect industry/mission from company name (simple heuristic)
    company_lower = company.lower()
    
    if any(word in company_lower for word in ['energy', 'climate', 'solar', 'green']):
        reason = f"I am particularly drawn to {company} because of its commitment to addressing climate change through innovative technology. The opportunity to contribute to clean energy solutions aligns perfectly with my personal values and professional goals."
    
    elif any(word in company_lower for word in ['health', 'medical', 'care', 'wellness']):
        reason = f"What excites me most about {company} is the opportunity to make a tangible difference in people's health and well-being through technology. I am inspired by organizations that leverage software to improve quality of life at scale."
    
    elif any(word in company_lower for word in ['education', 'learn', 'school', 'academy']):
        reason = f"I am passionate about democratizing access to education, and {company}'s mission to empower learners resonates deeply with me. The chance to build tools that enable knowledge-sharing excites me both personally and professionally."
    
    elif any(word in company_lower for word in ['library', 'public', 'civic', 'government']):
        reason = f"I am drawn to {company}'s commitment to public service and civic engagement. The opportunity to work on technology that serves the broader community, rather than purely commercial interests, aligns with my desire to create meaningful impact."
    
    elif any(word in company_lower for word in ['open', 'science', 'research']):
        reason = f"As someone who values transparency and collaboration, I am excited about {company}'s dedication to open science and research. The prospect of contributing to tools that advance human knowledge is incredibly motivating."
    
    else:
        reason = f"I am impressed by {company}'s reputation for innovation and technical excellence. The {title} role represents an exciting opportunity to work on challenging problems with a talented team, and I am eager to contribute to {company}'s continued growth."
    
    return reason


def generate_closing_paragraph(profile, job):
    """Strong, confident closing."""
    company = job.get('company', 'your company')
    title = job.get('title', 'this position')
    
    closings = [
        f"I am confident that my technical expertise, combined with my passion for building impactful solutions, makes me a strong fit for the {title} role. I am excited about the possibility of joining {company} and contributing to your team's success.",
        
        f"I believe my background in delivering scalable, user-centric applications positions me well to make immediate contributions to {company}. I am enthusiastic about the opportunity to bring my skills to the {title} role and help drive your mission forward.",
        
        f"With a proven track record of technical excellence and a genuine enthusiasm for {company}'s work, I am eager to discuss how I can add value to your team. Thank you for considering my application for the {title} position."
    ]
    
    return closings[0]


def save_cover_letter(letter, company_name):
    """Save cover letter to text file."""
    # Create company folder
    app_dir = Path(__file__).parent.parent / ".tmp" / "applications" / company_name.replace(' ', '_').replace('/', '_')
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as text
    txt_path = app_dir / "cover_letter.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(letter)
    
    return txt_path


# Setup logging
log_path = Path(__file__).parent.parent / ".tmp" / "generate_cover_letter.log"
def log(msg):
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except:
        pass # Fallback if file write fails

def main():
    parser = argparse.ArgumentParser(description='Generate cover letters')
    parser.add_argument('--company', type=str, help='Generate for specific company only')
    args = parser.parse_args()
    
    log("AI-Powered Cover Letter Generator\n")
    
    # Load data
    try:
        profile = load_profile()
        jobs = load_jobs()
    except Exception as e:
        log(f"Error loading data: {e}")
        return

    if not jobs:
        log("No filtered jobs found. Run filtering first.")
        sys.exit(1)
    
    # Filter by company if specified
    if args.company:
        jobs = [j for j in jobs if args.company.lower() in j.get('company', '').lower()]
        if not jobs:
            log(f"No jobs found for company: {args.company}")
            sys.exit(1)
    
    log(f"Generating cover letters for {len(jobs)} jobs\n")
    
    # Generate cover letters
    for i, job in enumerate(jobs, 1):
        company = job.get('company', 'Unknown Company')
        title = job.get('title', 'Position')
        
        log(f"{i}. {title} at {company}")
        
        # Generate letter
        try:
            letter = generate_cover_letter(profile, job)
            
            # Save
            letter_path = save_cover_letter(letter, company)
            log(f"   Saved: {letter_path}\n")
        except Exception as e:
            log(f"   Error generating letter for {company}: {e}")
    
    log(f"\nGenerated {len(jobs)} cover letters!")
    log(f"Location: .tmp/applications/")
    log(f"\nNext steps:")
    log(f"   1. Review generated cover letters")
    log(f"   2. Customize if needed (add specific company research)")
    log(f"   3. Ready for application submission!")
    
    log(f"\nTips:")
    log(f"   - Letters use intelligent templates")
    log(f"   - For dream jobs: add company-specific details")
    log(f"   - Future: AI will auto-research companies")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Error: {e}")
        import traceback
        with open(log_path, "a", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        sys.exit(1)
