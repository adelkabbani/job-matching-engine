"""
Profile Ingestion System

Parses uploaded documents (CV, certificates, LinkedIn exports) and extracts
structured professional data conforming to profile_schema.json.

Usage:
    python execution/ingest_profile.py path/to/cv.pdf
    python execution/ingest_profile.py path/to/linkedin_export.zip
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import re

try:
    import pdfplumber
    import docx
    from jsonschema import validate
except ImportError:
    print("Installing required dependencies...")
    os.system("pip install pdfplumber python-docx jsonschema")
    import pdfplumber
    import docx
    from jsonschema import validate


def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text


def extract_text_from_docx(docx_path):
    """Extract all text from a DOCX file."""
    doc = docx.Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


def extract_text_from_file(file_path):
    """Automatically detect file type and extract text."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.suffix.lower() == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_path.suffix.lower() in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    elif file_path.suffix.lower() == '.txt':
        return file_path.read_text(encoding='utf-8')
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")


def parse_profile_basic(text, file_path):
    """
    Basic regex-based parsing. 
    In production, this will be replaced with AI-powered extraction.
    """
    profile = {
        "personal_info": {},
        "work_experience": [],
        "education": [],
        "skills": {
            "technical": [],
            "soft_skills": [],
            "languages": []
        },
        "certifications": [],
        "projects": [],
        "achievements": [],
        "preferences": {},
        "metadata": {
            "profile_version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "source_documents": [str(file_path)],
            "ai_confidence_score": 0.5  # Low confidence for regex parsing
        }
    }
    
    # Extract email (basic regex)
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        profile["personal_info"]["email"] = email_match.group(0)
    
    # Extract phone (basic regex for US/international format)
    phone_match = re.search(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,5}[-\s\.]?[0-9]{1,5}', text)
    if phone_match:
        profile["personal_info"]["phone"] = phone_match.group(0)
    
    # Extract name (assume first non-empty line is name)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        profile["personal_info"]["full_name"] = lines[0]
    
    # Extract LinkedIn
    linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text, re.IGNORECASE)
    if linkedin_match:
        profile["personal_info"]["linkedin"] = f"https://{linkedin_match.group(0)}"
    
    # Extract GitHub
    github_match = re.search(r'github\.com/[\w-]+', text, re.IGNORECASE)
    if github_match:
        profile["personal_info"]["github"] = f"https://{github_match.group(0)}"
    
    # Placeholder for skills extraction
    # This is where AI will shine - identifying skills from context
    common_skills = [
        'Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 
        'Kubernetes', 'SQL', 'MongoDB', 'Git', 'Java', 'C++', 'TypeScript',
        'Vue', 'Angular', 'Django', 'Flask', 'FastAPI', 'PostgreSQL', 'Redis'
    ]
    
    for skill in common_skills:
        if re.search(rf'\b{skill}\b', text, re.IGNORECASE):
            profile["skills"]["technical"].append({
                "name": skill,
                "proficiency": "intermediate",  # Conservative default
                "years_of_experience": 0
            })
    
    return profile


def validate_profile(profile):
    """Validate profile against schema."""
    schema_path = Path(__file__).parent.parent / "schemas" / "profile_schema.json"
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    try:
        validate(instance=profile, schema=schema)
        return True, None
    except Exception as e:
        return False, str(e)


def save_profile(profile, output_path=None):
    """Save profile to JSON file."""
    if output_path is None:
        output_dir = Path(__file__).parent.parent / ".tmp"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "user_profile.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    
    return output_path


def process_file(file_path):
    """
    Main entry point for processing a file (CV, etc.)
    Returns the parsed profile dictionary.
    """
    print(f"📄 Reading file: {file_path}")
    text = extract_text_from_file(file_path)
    
    print(f"📊 Extracting structured data...")
    profile = parse_profile_basic(text, file_path)
    
    print(f"✅ Validating profile...")
    is_valid, error = validate_profile(profile)
    
    if not is_valid:
        print(f"⚠️  Warning: Profile validation failed: {error}")
    
    output_path = save_profile(profile)
    return profile



def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_profile.py <path_to_cv_or_document>")
        print("\nSupported formats: PDF, DOCX, TXT")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        print(f"📄 Reading file: {input_file}")
        text = extract_text_from_file(input_file)
        
        print(f"📊 Extracting structured data...")
        profile = parse_profile_basic(text, input_file)
        
        print(f"✅ Validating profile...")
        is_valid, error = validate_profile(profile)
        
        if not is_valid:
            print(f"⚠️  Warning: Profile validation failed: {error}")
            print("Saving anyway for manual review...")
        
        output_path = save_profile(profile)
        print(f"✅ Profile saved to: {output_path}")
        
        # Print summary
        print("\n📋 Profile Summary:")
        print(f"  Name: {profile['personal_info'].get('full_name', 'Not found')}")
        print(f"  Email: {profile['personal_info'].get('email', 'Not found')}")
        print(f"  Phone: {profile['personal_info'].get('phone', 'Not found')}")
        print(f"  Technical Skills: {len(profile['skills']['technical'])} detected")
        
        if profile['skills']['technical']:
            print(f"  Top skills: {', '.join([s['name'] for s in profile['skills']['technical'][:5]])}")
        
        print(f"\n💡 Next steps:")
        print(f"  1. Review and edit: {output_path}")
        print(f"  2. Add work experience, education, and projects manually (or upload more documents)")
        print(f"  3. Run job matching: python execution/match_jobs.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
