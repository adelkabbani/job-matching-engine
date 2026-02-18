"""
Certificate deduplication utilities.
Provides fingerprinting and dedup logic for certificates.
"""
import hashlib


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    Converts to lowercase and strips whitespace.
    """
    if not text:
        return ""
    return text.lower().strip()


def generate_certificate_fingerprint(cert_data: dict) -> str:
    """
    Generate stable fingerprint for certificate deduplication.
    
    Based on: normalized title + issuer + completion_date
    
    Args:
        cert_data: Dictionary with certificate fields (title, issuer, completion_date)
    
    Returns:
        16-character hex fingerprint
    
    Example:
        >>> cert = {"title": "Python Basics", "issuer": "Coursera", "completion_date": "2024-01-15"}
        >>> fingerprint = generate_certificate_fingerprint(cert)
        >>> len(fingerprint)
        16
    """
    title = normalize_text(cert_data.get("title", ""))
    issuer = normalize_text(cert_data.get("issuer", ""))
    date = normalize_text(cert_data.get("completion_date", ""))
    
    # Create stable string representation
    fingerprint_str = f"{title}|{issuer}|{date}"
    
    # Hash for storage efficiency (SHA-256, truncated to 16 chars)
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]


def deduplicate_skills(skills_list: list[str]) -> list[str]:
    """
    Deduplicate skills list with filtering and synonym normalization.
    
    - Removes blacklisted noisy skills
    - Applies synonym mapping (e.g., "ML" -> "Machine Learning")
    - Case-insensitive deduplication
    - Trimming whitespace
    
    Args:
        skills_list: List of skill strings
    
    Returns:
        Sorted list of unique, cleaned skills
    
    Example:
        >>> deduplicate_skills(["Python", "python", "ML", "Grade Conversion"])
        ['Machine Learning', 'Python']
    """
    if not skills_list:
        return []
    
    # Load filter config
    import json
    import os
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "config" / "skills_filter.json"
    
    blacklist = set()
    synonyms = {}
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                blacklist = set(s.lower() for s in config.get("blacklist", []))
                synonyms = {k: v for k, v in config.get("synonyms", {}).items()}
    except Exception as e:
        print(f"Warning: Could not load skills filter config: {e}")
    
    # Process skills
    unique_skills_map = {}
    
    for skill in skills_list:
        if not skill:
            continue
        
        skill_stripped = skill.strip()
        if not skill_stripped:
            continue
        
        # Check blacklist (case-insensitive)
        if skill_stripped.lower() in blacklist:
            continue
        
        # Apply synonym mapping (exact match, case-sensitive for keys)
        normalized_skill = synonyms.get(skill_stripped, skill_stripped)
        
        # Deduplicate (case-insensitive key)
        key = normalized_skill.lower()
        if key not in unique_skills_map:
            unique_skills_map[key] = normalized_skill
    
    # Return sorted list
    return sorted(unique_skills_map.values())
