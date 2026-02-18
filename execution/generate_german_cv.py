import json
import os
from pathlib import Path
from datetime import datetime

# Config
BASE_DIR = Path(__file__).parent.parent
PROFILE_FILE = BASE_DIR / ".tmp" / "user_profile.json"
OUTPUT_FILE = BASE_DIR / ".tmp" / "generated_cv_german.md"

def load_profile():
    if not PROFILE_FILE.exists():
        print(f"❌ Profile file not found at {PROFILE_FILE}")
        return None
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def format_date_german(date_str):
    """Converts various date formats to MM.YYYY (German standard)"""
    if not date_str:
        return "Heute"
    try:
        # Try YYYY-MM-DD format first
        if len(date_str) == 10:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            # Try YYYY-MM format
            dt = datetime.strptime(date_str, "%Y-%m")
        return dt.strftime("%m.%Y")
    except ValueError:
        return date_str

def generate_german_cv():
    profile = load_profile()
    if not profile:
        return

    print("🇩🇪 Generiere Lebenslauf (Generating German CV)...")

    # Extract data from both possible schema formats
    personal = profile.get('personal_info', {})
    name = personal.get('full_name') or profile.get('name', 'Max Mustermann')
    email = personal.get('email') or profile.get('email', 'max@beispiel.de')
    phone = personal.get('phone') or profile.get('phone', '+49 123 456789')
    
    location = personal.get('location', {})
    if isinstance(location, dict):
        address = f"{location.get('city', 'Berlin')}, {location.get('country', 'Germany')}"
    else:
        address = profile.get('address', 'Berlin, Germany')

    # Header
    markdown = f"# LEBENSLAUF\n\n"
    
    # 1. Persönliche Daten (Personal Details) - Critical for Germany
    markdown += "## PERSÖNLICHE DATEN\n\n"
    markdown += f"**Name:** {name}\n\n"
    markdown += f"**Adresse:** {address}\n\n"
    markdown += f"**Telefon:** {phone}\n\n"
    markdown += f"**E-Mail:** {email}\n\n"
    
    # Optional German specific fields
    if profile.get('birthdate'):
        markdown += f"**Geburtsdatum:** {profile.get('birthdate')}\n\n"
    if profile.get('marital_status'):
        markdown += f"**Familienstand:** {profile.get('marital_status')}\n\n"
    
    # LinkedIn/GitHub if present
    if personal.get('linkedin'):
        markdown += f"**LinkedIn:** {personal.get('linkedin')}\n\n"
    if personal.get('github'):
        markdown += f"**GitHub:** {personal.get('github')}\n\n"
    
    # Professional headline
    if personal.get('professional_headline'):
        markdown += f"**Position:** {personal.get('professional_headline')}\n\n"
    
    # Photo Placeholder
    markdown += "> ![Bewerbungsfoto](path/to/photo.jpg)\n"
    markdown += "> *Hinweis: Ein professionelles Foto wird in Deutschland oft noch erwartet.*\n\n"

    # 2. Beruflicher Werdegang (Experience)
    markdown += "## BERUFLICHER WERDEGANG\n\n"
    experience_list = profile.get('work_experience') or profile.get('experience', [])
    for job in experience_list:
        start = format_date_german(job.get('start_date'))
        end = format_date_german(job.get('end_date'))
        title = job.get('title', 'Position')
        company = job.get('company', 'Unternehmen')
        location_job = job.get('location', '')
        
        markdown += f"### {start} – {end}\n"
        markdown += f"**{title}** bei *{company}*"
        if location_job:
            markdown += f" ({location_job})"
        markdown += "\n\n"
        
        # Description
        if job.get('description'):
            markdown += f"{job.get('description')}\n\n"
        
        # Achievements as bullet points
        achievements = job.get('achievements', [])
        if achievements:
            markdown += "**Erfolge:**\n"
            for achievement in achievements:
                markdown += f"- {achievement}\n"
            markdown += "\n"
        
        # Technologies used
        technologies = job.get('technologies', [])
        if technologies:
            markdown += f"**Technologien:** {', '.join(technologies)}\n\n"

    # 3. Ausbildung (Education)
    markdown += "## AUSBILDUNG\n\n"
    for edu in profile.get('education', []):
        start = format_date_german(edu.get('start_date'))
        end = format_date_german(edu.get('end_date'))
        
        # Handle both schema formats
        degree = edu.get('degree', '')
        field = edu.get('field_of_study', '')
        if field:
            degree = f"{degree} in {field}"
        
        institution = edu.get('institution') or edu.get('university', 'Universität')
        
        markdown += f"### {start} – {end}\n"
        markdown += f"**{degree}**\n"
        markdown += f"*{institution}*\n\n"
        
        # GPA if present
        if edu.get('gpa'):
            markdown += f"Note: {edu.get('gpa')}\n\n"
        
        # Honors
        honors = edu.get('honors', [])
        if honors:
            markdown += f"Auszeichnungen: {', '.join(honors)}\n\n"

    # 4. Kenntnisse & Fähigkeiten (Skills)
    markdown += "## KENNTNISSE & FÄHIGKEITEN\n\n"
    
    skills = profile.get('skills', [])
    if isinstance(skills, list):
        # Simple list of skills
        markdown += "**Technische Fähigkeiten:**\n"
        markdown += ", ".join(skills) + "\n\n"
    elif isinstance(skills, dict):
        # Categorized skills
        for category, items in skills.items():
            if isinstance(items, list):
                markdown += f"**{category}:** {', '.join(items)}\n\n"
            else:
                markdown += f"**{category}:** {items}\n\n"
    
    # Languages from preferences if available
    if profile.get('preferences', {}).get('required_languages'):
        markdown += "**Sprachen:**\n"
        for lang in profile.get('preferences', {}).get('required_languages', []):
            markdown += f"- {lang}\n"
        markdown += "\n"

    # 5. Preferences Summary (for German cover letter context)
    prefs = profile.get('preferences', {})
    if prefs:
        markdown += "## WUNSCHPROFIL (Für Anschreiben-Referenz)\n\n"
        if prefs.get('desired_roles'):
            markdown += f"**Gewünschte Positionen:** {', '.join(prefs.get('desired_roles', []))}\n\n"
        if prefs.get('remote_preference'):
            remote_map = {
                'remote-only': 'Nur Remote',
                'hybrid': 'Hybrid',
                'on-site': 'Vor Ort'
            }
            markdown += f"**Arbeitsmodell:** {remote_map.get(prefs.get('remote_preference'), prefs.get('remote_preference'))}\n\n"

    # Footer (Signature place)
    markdown += "---\n\n"
    markdown += f"{datetime.now().strftime('%d.%m.%Y')}, {address.split(',')[0] if ',' in address else address}\n\n\n"
    markdown += "(Unterschrift)\n"

    # Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    print(f"✅ Lebenslauf generated: {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    generate_german_cv()
